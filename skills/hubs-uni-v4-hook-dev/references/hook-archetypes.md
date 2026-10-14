# Hook Archetypes

This is a pattern catalog distilled from [awesome-uniswap-hooks](https://github.com/fewwwww/awesome-uniswap-hooks), mapped to permissions, OpenZeppelin `uniswap-hooks` bases (master `b5f1057`, package 1.3.0 pre-release), and the failure modes that matter. Community repos are learning material: most are hackathon-grade and target pre-1.0 v4 APIs (`IPoolManager.SwapParams`, external `beforeSwap` overrides, `settle(currency)`), so port the idea rather than the code.

## Contents

- [Choosing a base](#choosing-a-base)
- [Gating and compliance](#gating-and-compliance)
- [Fees](#fees)
- [Orders: limit, stop-loss, take-profit, TWAMM](#orders)
- [Oracles](#oracles)
- [Custom curves and NoOp (verified example)](#custom-curves-and-noop)
- [Async, intents, batch auctions](#async-intents-batch-auctions)
- [MEV, LVR and JIT](#mev-lvr-and-jit)
- [Liquidity management and rehypothecation](#liquidity-management-and-rehypothecation)
- [Launchpads, LBPs and token mechanics](#launchpads-lbps-and-token-mechanics)

## Choosing a base

| OZ base (`@openzeppelin/uniswap-hooks/src/...`) | What it gives you | You implement |
|---|---|---|
| `base/BaseHook.sol` | `onlyPoolManager` externals → internal `_beforeX` overrides, `onlyValidPools`, address validation | `getHookPermissions`, the `_callbacks` |
| `base/BaseCustomAccounting.sol` | Hook-owned liquidity, `addLiquidity`/`removeLiquidity` entrypoints, unlock plumbing | share mint/burn, `_getAddLiquidity`/`_getRemoveLiquidity` |
| `base/BaseCustomCurve.sol` | NoOp swap path on top of custom accounting | `_getUnspecifiedAmount` (your curve) |
| `base/BaseAsyncSwap.sol` | Takes exact-input swaps as ERC-6909 claims, no AMM execution | later fulfilment logic |
| `fee/BaseDynamicFee.sol` | Sets the fee in `afterInitialize`; internal `_poke(key)` → `updateDynamicLPFee` | `_getFee(key)`, an access-controlled external wrapper around `_poke` |
| `fee/BaseOverrideFee.sol` | Per-swap override from `beforeSwap` | `_getFee(sender, key, params, hookData)` |
| `fee/BaseDynamicAfterFee.sol` | Fee on output computed after the swap | target / fee logic |
| `fee/BaseHookFee.sol` | Hook-side fee via `afterSwapReturnDelta`, accrued as claims | `_getHookFee`, `handleHookFees(currencies)` (withdrawal) |
| `general/LimitOrderHook.sol` | Full tick-bucket limit orders | - (use or extend) |
| `general/AntiSandwichHook.sol` | Price-checkpoint sandwich resistance | - |
| `general/LiquidityPenaltyHook.sol` | Penalises JIT add→remove within N blocks | `blockNumberOffset` |
| `general/ReHypothecationHook.sol` | Idle liquidity in ERC-4626 vaults | vault wiring |
| `oracles/panoptic/BaseOracleHook.sol`, `OracleHookWithV3Adapters.sol` | Truncated TWAP oracle, optional v3 `IUniswapV3Pool`-style adapter | - |

Rule: use `BaseHook` unless a specialised base already solves the delta accounting you would otherwise hand-roll. Every `*ReturnDelta` you write yourself is audit surface.

## Gating and compliance

Examples: [Identity with Civic](https://github.com/civicteam/uniswap-v4-hook), [WID KYC](https://github.com/Shivamycodee/WID-KYC-Hook), [Whitelist](https://github.com/atj3097/whitelist-hook), [NFT Owners Only](https://github.com/wagmiwiz/nft-owners-only-uniswap-hook), [New York Trading Hours](https://github.com/horsefacts/trading-days), USDL (Paxos + Predicate compliance), [PureFi Verifier](https://github.com/purefiprotocol/purefi-verifier-hook).

- Permissions: `beforeSwap` and usually `beforeAddLiquidity`/`beforeRemoveLiquidity`.
- **Identity.** The `sender` argument is the router (PositionManager, UniversalRouter, hookmate V4Router, or any contract), never the EOA. Gate on `sender` against an allowlist of routers you trust. Then read the user via the router's `msgSender()` (v4-periphery routers expose it) or a signed attestation in `hookData`. Gating on `tx.origin` breaks smart wallets and is spoofable through relays.
- **Removal.** Don't gate `beforeRemoveLiquidity` in a way that can trap LPs (for example, after a KYC revocation). Gating exits is how a compliance hook becomes a fund lock.
- Time-based gates (`block.timestamp`) are fine for coarse windows. Add the timezone and holiday logic off-chain to a config with an owner and a cap.

## Fees

Examples: [Captain Hook tutorial hooks (dynamic fees, roles)](https://github.com/umbrellaresearch/uni-v4-hooks-tutorial), [Ref Fee Hook](https://github.com/mergd/ref-fee-hook), [Slippage Fee Hook](https://github.com/dennnis0204/slippage-fee-hook), [Super DCA Gauge Hook](https://github.com/Super-DCA-Tech/super-dca-gauge), Zora / Clanker / Flaunch fee routing.

- **LP fee, persistent:** pool `fee = DYNAMIC_FEE_FLAG`, and the hook calls `poolManager.updateDynamicLPFee(key, fee)` (only the pool's hook may call it, otherwise `UnauthorizedDynamicLPFeeUpdate`). Do it in `afterInitialize` and from a keeper-callable wrapper around OZ's internal `_poke`.
- **LP fee, per swap:** return `fee | OVERRIDE_FEE_FLAG` from `beforeSwap`. This is silently ignored on static-fee pools. `SKILL.md` has a verified example.
- **Hook fee (revenue to the hook, not the LPs):** use `afterSwap` + `afterSwapReturnDelta`. Take the cut from the unspecified currency and return it as a positive `int128`. Then `take`/`mint` it inside the same callback, or the delta won't net.
- Cap every fee with an immutable maximum. A mutable uncapped fee is the "liquidity theft via hook fee" pattern (`security.md`).
- Volatility estimators that read the pool's own price can be pushed by the same trader within one block. Use previous-block observations or an external oracle.

## Orders

Examples: Uniswap [Limit Order](https://github.com/Uniswap/v4-periphery/tree/example-contracts/contracts/hooks/examples/LimitOrder.sol), [Stop Loss Order](https://github.com/saucepoint/v4-stoploss), [On-Chain Take Profit Order](https://github.com/LearnWeb3DAO/uniswap-v4-take-profits-hook), [Encrypted Limit Order Hook](https://github.com/marronjo/iceberg-cofhe), Uniswap [TWAMM](https://github.com/Uniswap/v4-periphery/tree/example-contracts/contracts/hooks/examples/TWAMM.sol), [FWB v4-twamm-hook](https://github.com/akshatmittal/v4-twamm-hook).

- Limit orders are single-tick liquidity positions owned by the hook. `afterSwap` compares the tick before and after the swap and withdraws the crossed buckets. Start from OZ `LimitOrderHook`.
- Store the last processed tick per pool (`afterInitialize` seeds it). Bucket orders by `(tickLower, zeroForOne)` with an epoch counter so partially-claimed buckets don't mix.
- **Bound the work per swap.** Crossing 1,000 ticks with orders must not iterate 1,000 buckets in a single `afterSwap`. Cap the fills per swap and leave the rest for a keeper.
- Executing orders swaps inside `afterSwap`. Self-calls don't re-enter your callbacks, but they do move price: account for the price impact your fills have on the user's swap.
- TWAMM: virtual orders execute in `beforeSwap`/`beforeAddLiquidity`. Every pool action pays for elapsed intervals, so cap the intervals processed per call.

## Oracles

Examples: Uniswap [Geomean Oracle](https://github.com/Uniswap/v4-periphery/tree/example-contracts/contracts/hooks/examples/GeomeanOracle.sol), [Truncated Oracle](https://github.com/Uniswap/v4-periphery/blob/trunc-oracle/contracts/hooks/TruncGeoOracle.sol), [Volatility Oracle](https://github.com/Uniswap/v4-periphery/tree/example-contracts/contracts/hooks/examples/VolatilityOracle.sol), [Backrunning Oracle](https://github.com/RigoBlock/back-geo-oracle/blob/main/src/BackGeoOracle.sol), OZ `BaseOracleHook` / `OracleHookWithV3Adapters`.

- Write the observation in `beforeSwap`, before the price moves, so the stored value reflects the last block's closing price.
- Truncation (cap the tick move per observation) limits single-block manipulation. OZ's Panoptic-derived oracle exposes `maxAbsTickDelta`.
- Full-range-only or locked-liquidity designs make manipulation costlier. A thin hook-oracle pool is cheap to move.
- An owner who can rewrite observations or swap the oracle source is a backdoor ("Oracle hook with malicious owner").

## Custom curves and NoOp

Examples: [Constant-sum Swap](https://github.com/saucepoint/v4-constant-sum), [v2 on v4](https://github.com/hensha256/v2-on-v4), [Orbital Hook](https://github.com/Dhruv-2003/ethglobal-buenos-aires-25) (spherical stable curve), EulerSwap (lending-backed AMM).

The hook returns a `BeforeSwapDelta` that fully satisfies `amountSpecified`, so the v4 concentrated-liquidity math is skipped ("NoOp"). It requires `beforeSwap` + `beforeSwapReturnDelta`, and normally `beforeAddLiquidity` that reverts so nobody adds unreachable v4-curve liquidity.

`BeforeSwapDelta` packs `(int128 specified, int128 unspecified)` from the **hook's** perspective:
- `specified = -amountSpecified` cancels the swapper's request. Exact-in: the hook takes the input; exact-out: the hook supplies the output.
- `unspecified` is the hook's delta on the other currency: negative = the hook pays it, positive = the hook receives it.
- The hook must then actually move the value in the same callback (`take`/`mint` for what it receives, `settle`/`burn` for what it pays), or the swap reverts with `CurrencyNotSettled`.

Verified implementation (v4-core 1.0.2, OZ uniswap-hooks `b5f1057`, Solady 0.1.26). Liquidity is held as ERC-6909 claims inside the PoolManager, so swaps never transfer ERC-20s:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {BaseHook} from "@openzeppelin/uniswap-hooks/src/base/BaseHook.sol";
import {CurrencySettler} from "@openzeppelin/uniswap-hooks/src/utils/CurrencySettler.sol";
import {Hooks} from "@uniswap/v4-core/src/libraries/Hooks.sol";
import {IPoolManager, SwapParams, ModifyLiquidityParams} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import {IUnlockCallback} from "@uniswap/v4-core/src/interfaces/callback/IUnlockCallback.sol";
import {PoolKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import {Currency} from "@uniswap/v4-core/src/types/Currency.sol";
import {BeforeSwapDelta, toBeforeSwapDelta} from "@uniswap/v4-core/src/types/BeforeSwapDelta.sol";
import {SafeCastLib} from "solady/utils/SafeCastLib.sol";
import {ReentrancyGuardTransient} from "solady/utils/ReentrancyGuardTransient.sol";

/// @notice x + y = k: every swap fills 1:1 from hook-owned ERC-6909 claims; the v4 curve is never used.
contract ConstantSumHook is BaseHook, IUnlockCallback, ReentrancyGuardTransient {
    using CurrencySettler for Currency;
    using SafeCastLib for int256;

    error AddLiquidityThroughHook();

    struct CallbackData {
        address payer;
        Currency currency0;
        Currency currency1;
        uint256 amountEach;
    }

    constructor(IPoolManager _poolManager) BaseHook(_poolManager) {}

    function getHookPermissions() public pure override returns (Hooks.Permissions memory) {
        return Hooks.Permissions({
            beforeInitialize: false,
            afterInitialize: false,
            beforeAddLiquidity: true, // block v4-curve liquidity
            afterAddLiquidity: false,
            beforeRemoveLiquidity: false,
            afterRemoveLiquidity: false,
            beforeSwap: true,
            afterSwap: false,
            beforeDonate: false,
            afterDonate: false,
            beforeSwapReturnDelta: true, // NoOp: the hook prices the whole swap
            afterSwapReturnDelta: false,
            afterAddLiquidityReturnDelta: false,
            afterRemoveLiquidityReturnDelta: false
        });
    }

    /// @dev Use TSTORE on every chain (Solady defaults to SSTORE off mainnet). Needs Cancun+.
    function _useTransientReentrancyGuardOnlyOnMainnet() internal pure override returns (bool) {
        return false;
    }

    /// @notice Deposit `amountEach` of both currencies; the hook keeps them as PoolManager claims.
    /// @dev Demo only: deposits are not tracked per LP and cannot be withdrawn.
    function addLiquidity(PoolKey calldata key, uint256 amountEach) external nonReentrant onlyValidPools(key.hooks) {
        poolManager.unlock(abi.encode(CallbackData(msg.sender, key.currency0, key.currency1, amountEach)));
    }

    function unlockCallback(bytes calldata rawData) external onlyPoolManager returns (bytes memory) {
        CallbackData memory data = abi.decode(rawData, (CallbackData));
        // Pay ERC-20s in (debt), then mint claims to the hook (credit): net delta is zero.
        data.currency0.settle(poolManager, data.payer, data.amountEach, false);
        data.currency1.settle(poolManager, data.payer, data.amountEach, false);
        data.currency0.take(poolManager, address(this), data.amountEach, true);
        data.currency1.take(poolManager, address(this), data.amountEach, true);
        return "";
    }

    function _beforeAddLiquidity(address, PoolKey calldata, ModifyLiquidityParams calldata, bytes calldata)
        internal
        pure
        override
        returns (bytes4)
    {
        revert AddLiquidityThroughHook();
    }

    function _beforeSwap(address, PoolKey calldata key, SwapParams calldata params, bytes calldata)
        internal
        override
        returns (bytes4, BeforeSwapDelta, uint24)
    {
        // Constant sum: |input| == |output|, so exact-in and exact-out share one code path.
        uint256 amount = params.amountSpecified < 0 ? uint256(-params.amountSpecified) : uint256(params.amountSpecified);
        (Currency input, Currency output) =
            params.zeroForOne ? (key.currency0, key.currency1) : (key.currency1, key.currency0);

        // Hook takes the input as claims and burns output claims to pay the swapper.
        input.take(poolManager, address(this), amount, true);
        output.settle(poolManager, address(this), amount, true);

        // Specified delta cancels the swapper's amountSpecified; unspecified is the opposite side.
        int128 specified = (-params.amountSpecified).toInt128();
        return (BaseHook.beforeSwap.selector, toBeforeSwapDelta(specified, -specified), 0);
    }
}
```

Its tests (setup and the fuzzed 1:1 property; runs under the hookmate harness from `testing-and-deployment.md`):

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IHooks} from "@uniswap/v4-core/src/interfaces/IHooks.sol";
import {Hooks} from "@uniswap/v4-core/src/libraries/Hooks.sol";
import {PoolKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import {BalanceDelta} from "@uniswap/v4-core/src/types/BalanceDelta.sol";
import {Currency} from "@uniswap/v4-core/src/types/Currency.sol";
import {Constants} from "@uniswap/v4-core/test/utils/Constants.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";

import {BaseTest} from "./utils/BaseTest.sol";
import {ConstantSumHook} from "../src/ConstantSumHook.sol";

contract ConstantSumHookTest is BaseTest {
    Currency currency0;
    Currency currency1;
    PoolKey poolKey;
    ConstantSumHook hook;

    function setUp() public {
        deployArtifactsAndLabel();
        (currency0, currency1) = deployCurrencyPair();

        address flags = address(
            uint160(Hooks.BEFORE_ADD_LIQUIDITY_FLAG | Hooks.BEFORE_SWAP_FLAG | Hooks.BEFORE_SWAP_RETURNS_DELTA_FLAG)
                ^ (0x4444 << 144)
        );
        deployCodeTo("ConstantSumHook.sol:ConstantSumHook", abi.encode(poolManager), flags);
        hook = ConstantSumHook(flags);

        poolKey = PoolKey(currency0, currency1, 0, 60, IHooks(hook));
        poolManager.initialize(poolKey, Constants.SQRT_PRICE_1_1);

        IERC20(Currency.unwrap(currency0)).approve(address(hook), type(uint256).max);
        IERC20(Currency.unwrap(currency1)).approve(address(hook), type(uint256).max);
        hook.addLiquidity(poolKey, 1000e18);
    }

    function test_ClaimsBackLiquidity() public view {
        assertEq(poolManager.balanceOf(address(hook), currency0.toId()), 1000e18);
        assertEq(poolManager.balanceOf(address(hook), currency1.toId()), 1000e18);
    }

    function testFuzz_ExactInIsOneToOne(uint256 amountIn, bool zeroForOne) public {
        amountIn = bound(amountIn, 1, 1000e18);
        BalanceDelta d = swapRouter.swapExactTokensForTokens({
            amountIn: amountIn,
            amountOutMin: amountIn,
            zeroForOne: zeroForOne,
            poolKey: poolKey,
            hookData: Constants.ZERO_BYTES,
            receiver: address(this),
            deadline: block.timestamp + 1
        });
        (int128 paid, int128 got) = zeroForOne ? (d.amount0(), d.amount1()) : (d.amount1(), d.amount0());
        assertEq(-int256(paid), int256(amountIn));
        assertEq(int256(got), int256(amountIn));
    }

    function test_ExactOutIsOneToOne() public {
        BalanceDelta d = swapRouter.swapTokensForExactTokens({
            amountOut: 5e18,
            amountInMax: 5e18,
            zeroForOne: false,
            poolKey: poolKey,
            hookData: Constants.ZERO_BYTES,
            receiver: address(this),
            deadline: block.timestamp + 1
        });
        assertEq(d.amount1(), -5e18);
        assertEq(d.amount0(), 5e18);
    }

    function test_RevertWhen_SwapExceedsClaims() public {
        vm.expectRevert(); // burning more ERC-6909 claims than the hook holds underflows
        swapRouter.swapExactTokensForTokens({
            amountIn: 1001e18,
            amountOutMin: 0,
            zeroForOne: true,
            poolKey: poolKey,
            hookData: Constants.ZERO_BYTES,
            receiver: address(this),
            deadline: block.timestamp + 1
        });
    }
}
```

Production gaps, which are deliberate in the demo: no LP share accounting or withdrawal (use `BaseCustomAccounting`/`BaseCustomCurve`, which mint shares), no fee, and a 1:1 price that is only sane for hard-pegged pairs. A NoOp hook with an upgradeable or owner-mutable curve can steal every input. Users and aggregators must audit it before routing (`security.md`).

## Async, intents, batch auctions

Examples: Angstrom (validator-signed batches, only staked nodes can swap), CoW-style batch auctions, UniBrain Dutch-auction triggers.

- `BaseAsyncSwap` takes exact-input amounts as ERC-6909 claims in `beforeSwap` and returns a delta that zeroes the AMM swap. The user gets the output later, from a solver or order book.
- Users receive nothing at swap time. Front-ends and aggregators must know this, or users read it as a loss. Document it and emit events (`IHookEvents`).
- Restricting swaps to signed batches means gating `sender`/`hookData`. Keep removal of liquidity permissionless.

## MEV, LVR and JIT

Examples: [Minimize LVR Hook](https://github.com/ArrakisFinance/minimize-lvr-hook-poc), [Detox Hook](https://ethglobal.com/showcase/detox-hook-mppeg) (Pyth-based arbitrage capture to LPs), the sandwich-resistant design (Umbra Research), auction-managed AMM, OZ `AntiSandwichHook` and `LiquidityPenaltyHook`.

- Anti-sandwich: checkpoint the pool state at the first swap of the block, then price same-direction follow-up swaps no better than the checkpoint. It costs gas on the first swap per block.
- LVR / MEV capture: charge a dynamic fee or run a block-level auction for the first swap right. The oracle comparison needs a fresh external price, so plan for stale-feed handling.
- JIT penalty: donate a share of fees earned by liquidity added and removed within N blocks back to the pool (`LiquidityPenaltyHook`). That requires `afterAdd/RemoveLiquidityReturnDelta`.

## Liquidity management and rehypothecation

Examples: Uniswap [Full Range](https://github.com/Uniswap/v4-periphery/tree/example-contracts/contracts/hooks/examples/FullRange.sol), Bunni (rehypothecation into lending vaults), [Locking Liquidity Hook](https://github.com/BrokkrFinance/hooks-poc/blob/main/src/LiquidityLocking.sol), [Curve Style Voting Escrow - veLP](https://github.com/kadenzipfel/veLP), [Bungi](https://github.com/saucepoint/bungi), [Automated Buyback](https://github.com/atj3097/buyback-hook).

- A hook that owns the liquidity issues its own shares (ERC-20/6909). Guard the first deposit against share inflation, using virtual shares or a dead-share mint. Solady `ERC4626` has `_useVirtualShares`/`_decimalsOffset`; see `solady-composition.md`.
- Rehypothecation moves funds to external vaults. Every swap or withdrawal path must handle a vault that is paused, illiquid, or charges withdrawal fees. Don't make LP exits depend on a third party being solvent without a fallback.
- Locks (`beforeRemoveLiquidity` reverts until T) are legitimate only when disclosed and time-bounded. An owner-extendable lock is a rug.

## Launchpads, LBPs and token mechanics

Examples: Flaunch, Doppler, [Uni LBP](https://github.com/kadenzipfel/uni-lbp), Zora, Clanker, UniDerp, Pubhouse, Ohara, Unimon (mint an NFT on swap), [Torres Token Sale](https://github.com/jamesbachini/Uniswap-V4-Torres-Token-Sale).

- An LBP moves the price curve over time by repositioning hook-owned liquidity in `beforeSwap`. Bound the per-call repositioning and handle the first swap after a long gap.
- Fee-to-creator and buyback flows: collect with `afterSwapReturnDelta`, then convert in a separate keeper transaction. Swapping inside `afterSwap` changes the price the user's swap just paid for.
- Launch tokens built on Solady `ERC20` grant **Permit2 an infinite allowance by default**. Decide deliberately and override `_givePermit2InfiniteAllowance` if unwanted.
- Anti-snipe and anti-whale rules (cooldowns, max tx) belong in `beforeSwap`. Gate on the router-reported user, not on `sender`, or every user of a router shares one cooldown.
