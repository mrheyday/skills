---
name: hubs-uni-v4-hook-dev
description: Build Uniswap v4 hooks with Foundry, OpenZeppelin uniswap-hooks, hookmate and Solady - permission bits, address mining, deltas, dynamic fees, NoOp curves, tests, deploys, security. Use for v4 hooks, PoolManager, beforeSwap, HookMiner.
metadata:
  version: "0.1.0"
  categories: "development, finance, security"
  topics: "uniswap-v4, hooks, solidity, foundry, defi"
  upstream: "@uniswap/v4-core@1.0.2, @uniswap/v4-periphery@1.0.3, @openzeppelin/uniswap-hooks@b5f1057, hookmate@0.6.0, solady@0.1.26, foundry@1.8.3"
  openclaw:
    homepage: https://github.com/tenequm/skills/tree/main/skills/hubs-uni-v4-hook-dev
    emoji: "🪝"
    primaryEnv: RPC_URL
    requires:
      anyBins:
        - forge
    install:
      - kind: brew
        formula: foundry
        bins:
          - forge
          - cast
          - anvil
    envVars:
      - name: RPC_URL
        required: false
        description: RPC endpoint for fork tests and deployment (Base, Unichain, Sepolia, ...).
      - name: ETHERSCAN_API_KEY
        required: false
        description: Explorer key for forge verify-contract.
---

# Uniswap v4 Hook Development

End-to-end hook engineering on the stack `uniswapfoundation/v4-template` ships today: **Foundry** for build/test/deploy, **OpenZeppelin `uniswap-hooks`** for audited bases, **hookmate** for canonical v4 artifacts and addresses, and **Solady** for gas-lean auth/math/guards. Every Solidity block below compiled and passed `forge test` against the pinned versions in `metadata.upstream` (solc 0.8.30, `evm_version = "cancun"`).

Companion skills (this one shows how they fit):

| Need | Skill |
|---|---|
| forge/cast/anvil, cheatcodes, foundry.toml, fuzz/invariant | `foundry-solidity` |
| Exact Solady signatures, reverts, chain variants | `solady-reference` if installed; otherwise the [Solady v0.1.26 source](https://github.com/Vectorized/solady/tree/v0.1.26/src) |
| Generating a scaffold from OZ Contracts Wizard (MCP) | `v4-hook-generator` |
| Calling hooks from apps (v4 SDK, PositionManager, Permit2) | `v4-sdk-integration` |
| Course-style PoolManager integration (flash, routers, UniversalRouter) | `cyfrin-defi-uniswap-v4` |

Two facts in older skills are wrong for v4-core 1.0.2 - trust this skill and `Hooks.sol`: `BEFORE_SWAP_RETURNS_DELTA` is **bit 3** (not 10), and `IPoolManager.settle()` takes **no arguments** (it is `payable` and settles the currency last passed to `sync`).

## Quick Start

```bash
# Recommended: the official template (OZ uniswap-hooks + hookmate already wired)
git clone https://github.com/uniswapfoundation/v4-template my-hook && cd my-hook
git submodule update --init --recursive
forge test

# Add Solady alongside
forge install Vectorized/solady@v0.1.26
echo 'solady/=lib/solady/src/' >> remappings.txt
```

Manual setup (existing repo) - install, then pin remappings explicitly:

```bash
forge install OpenZeppelin/uniswap-hooks@b5f1057 akshatmittal/hookmate@v0.6.0 Vectorized/solady@v0.1.26
```

`b5f1057` is the uniswap-hooks `master` commit (package 1.3.0, nesting v4-core 1.0.2 / v4-periphery 1.0.3) the examples were verified against. 1.3.0 is not a stable release yet (only `v1.3.0-rc.0`; the latest stable tag is v1.2.1), so pin the commit, not a version.

```text
forge-std/=lib/forge-std/src/
@uniswap/v4-core/=lib/uniswap-hooks/lib/v4-core/
@uniswap/v4-periphery/=lib/uniswap-hooks/lib/v4-periphery/
@openzeppelin/uniswap-hooks/=lib/uniswap-hooks/
@openzeppelin/contracts/=lib/uniswap-hooks/lib/v4-core/lib/openzeppelin-contracts/contracts/
hookmate/=lib/hookmate/src/
permit2/=lib/uniswap-hooks/lib/v4-periphery/lib/permit2/
solmate/=lib/uniswap-hooks/lib/v4-core/lib/solmate/
solady/=lib/solady/src/
v4-core/=lib/uniswap-hooks/lib/v4-core/
v4-periphery/=lib/uniswap-hooks/lib/v4-periphery/
```

```toml
[profile.default]
src = "src"
out = "out"
libs = ["lib"]
solc_version = "0.8.30"
evm_version = "cancun"     # TSTORE/TLOAD: flash accounting + transient guards
optimizer = true
optimizer_runs = 200
bytecode_hash = "none"
ffi = true
fs_permissions = [{ access = "read-write", path = ".forge-snapshots/" }]
```

Setup gotchas:
- **One copy of v4-core**, the one nested in `uniswap-hooks`. A second top-level `v4-periphery` install makes forge's auto-remappings fail with `Source ".../src/src/types/PoolKey.sol" not found`. Keep the explicit `v4-core/` and `v4-periphery/` lines.
- **hookmate artifacts, not core sources.** `PoolManager.sol` pins `pragma 0.8.26` exactly, and hookmate deploys canonical bytecode, so any solc ≥0.8.26 works. Importing `PoolManager.sol` or v4-core's `test/utils/Deployers.sol` forces 0.8.26.
- **hookmate moved** from `saucepoint/hookmate` (404) to `akshatmittal/hookmate`. Remap `hookmate/=lib/hookmate/src/`; its README's `lib/hookmate/` is wrong.

## Mental Model

One `PoolManager` singleton holds every pool. A pool is identified by `PoolKey{currency0, currency1, fee, tickSpacing, hooks}` (`currency0 < currency1`, native ETH = `address(0)`). The `hooks` address is fixed at `initialize` and the PoolManager calls it at up to 10 lifecycle points:

| Action | Callbacks | Can return a delta? |
|---|---|---|
| `initialize` | `beforeInitialize`, `afterInitialize` | no |
| `modifyLiquidity` (add) | `beforeAddLiquidity`, `afterAddLiquidity` | after: `afterAddLiquidityReturnDelta` |
| `modifyLiquidity` (remove) | `beforeRemoveLiquidity`, `afterRemoveLiquidity` | after: `afterRemoveLiquidityReturnDelta` |
| `swap` | `beforeSwap`, `afterSwap` | before: `BeforeSwapDelta` (NoOp); after: `int128` on the unspecified currency |
| `donate` | `beforeDonate`, `afterDonate` | no |

### Permissions live in the address

The PoolManager never asks the hook what it implements. It reads the **low 14 bits of the hook address** (`Hooks.ALL_HOOK_MASK = (1 << 14) - 1`). A bit set without the function implemented makes calls revert. A function implemented without the bit is silently never called.

| Bit | Flag constant (`Hooks.sol`) | Bit | Flag constant |
|---|---|---|---|
| 13 | `BEFORE_INITIALIZE_FLAG` | 6 | `AFTER_SWAP_FLAG` |
| 12 | `AFTER_INITIALIZE_FLAG` | 5 | `BEFORE_DONATE_FLAG` |
| 11 | `BEFORE_ADD_LIQUIDITY_FLAG` | 4 | `AFTER_DONATE_FLAG` |
| 10 | `AFTER_ADD_LIQUIDITY_FLAG` | 3 | `BEFORE_SWAP_RETURNS_DELTA_FLAG` |
| 9 | `BEFORE_REMOVE_LIQUIDITY_FLAG` | 2 | `AFTER_SWAP_RETURNS_DELTA_FLAG` |
| 8 | `AFTER_REMOVE_LIQUIDITY_FLAG` | 1 | `AFTER_ADD_LIQUIDITY_RETURNS_DELTA_FLAG` |
| 7 | `BEFORE_SWAP_FLAG` | 0 | `AFTER_REMOVE_LIQUIDITY_RETURNS_DELTA_FLAG` |

A `*_RETURNS_DELTA` flag requires its base flag too (for example, bit 3 requires bit 7), otherwise `initialize` reverts `HookAddressNotValid`. The PoolManager skips a hook's callbacks when the hook itself is the caller, so a hook can swap or modify liquidity on its own pool without recursing. `getHookPermissions()` must match the address exactly. OZ `BaseHook`'s constructor calls `Hooks.validateHookPermissions`, so a wrong address reverts at deploy. Tests use `deployCodeTo` at a crafted address. Production mines a CREATE2 salt with `HookMiner`.

### Flash accounting (unlock → deltas → settle/take)

All state changes happen inside `poolManager.unlock(data)` → your `unlockCallback(data)`. Each operation adds signed **deltas** per `(address, currency)` in transient storage, and `unlock` reverts with `CurrencyNotSettled` unless every delta is zero at the end.

- **You owe the pool (negative delta):** for ERC-20, call `sync(currency)`, then transfer, then `settle()`. For ETH, call `settle{value: amount}()`. Or burn ERC-6909 claims with `burn(...)`.
- **The pool owes you (positive delta):** call `take(currency, to, amount)`, or mint ERC-6909 claims with `mint(to, currency.toId(), amount)`. Claims are the cheap way for a hook to hold inventory inside the PoolManager.
- OZ `CurrencySettler` wraps all four: `currency.settle(manager, payer, amount, burnClaims)` and `currency.take(manager, recipient, amount, mintClaims)`.
### BalanceDelta

`amountSpecified < 0` means exact-in, `> 0` means exact-out. `BalanceDelta` packs `int128 amount0` (upper 128 bits) and `amount1` (lower 128 bits) into one `int256`.
- **Reading it.** Use only `.amount0()` / `.amount1()`; `+`/`-` revert on int128 overflow.
- **Perspective.** It is from the view of the address it is booked to: negative means owe, positive means owed.
- **Returns.** `swap` returns the caller's delta, already net of hook deltas (`ammDelta - hookDelta`). `modifyLiquidity` returns `(callerDelta, feesAccrued)`, with the fees already inside `callerDelta`.
- **Hook deltas.** They are keyed by specified/unspecified: specified is currency0 iff `(amountSpecified < 0) == zeroForOne`. The hook must clear its own delta in the same callback.

Rules, settlement, verified swap and liquidity routers, and pitfalls: `references/balance-delta.md`.

### Fees

- **Static:** `key.fee` in hundredths of a bip (`3000` = 0.30%, max `LPFeeLibrary.MAX_LP_FEE = 1_000_000`).
- **Dynamic:** `key.fee = LPFeeLibrary.DYNAMIC_FEE_FLAG` (`0x800000`). There are two ways to set it:
  - `poolManager.updateDynamicLPFee(key, fee)`, callable only by the hook. It is persistent and fits periodic updates.
  - Return `fee | LPFeeLibrary.OVERRIDE_FEE_FLAG` (`0x400000`) from `beforeSwap`. It applies to that swap only and is **silently ignored on static-fee pools**, so check `key.fee` in `beforeInitialize`.
- **Hook fees:** charge via the `afterSwapReturnDelta` / `beforeSwapReturnDelta` / `afterAdd|RemoveLiquidityReturnDelta` deltas. See OZ `BaseHookFee` and `BaseDynamicAfterFee`.

## Reference Hook: single-pool, owner-tuned, capped dynamic fee

OZ `BaseHook` exposes the external callbacks with `onlyPoolManager` already applied and dispatches to `internal` `_beforeSwap`/`_afterSwap`/… overrides. Override the internal ones and return `BaseHook.<callback>.selector`. `SwapParams`/`ModifyLiquidityParams` live in `types/PoolOperation.sol` and are re-exported by `IPoolManager.sol`.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {BaseHook} from "@openzeppelin/uniswap-hooks/src/base/BaseHook.sol";
import {Hooks} from "@uniswap/v4-core/src/libraries/Hooks.sol";
import {IPoolManager, SwapParams} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import {PoolKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import {PoolId, PoolIdLibrary} from "@uniswap/v4-core/src/types/PoolId.sol";
import {LPFeeLibrary} from "@uniswap/v4-core/src/libraries/LPFeeLibrary.sol";
import {BeforeSwapDelta, BeforeSwapDeltaLibrary} from "@uniswap/v4-core/src/types/BeforeSwapDelta.sol";
import {Ownable} from "solady/auth/Ownable.sol";

/// @notice Owner-tuned swap fee for exactly one dynamic-fee pool, bounded by an immutable cap.
contract CappedDynamicFeeHook is BaseHook, Ownable {
    using PoolIdLibrary for PoolKey;

    error NotDynamicFee();
    error PoolAlreadyBound();
    error FeeAboveCap();

    event FeeUpdated(uint24 fee);

    uint24 public immutable maxFee; // hundredths of a bip: 10_000 = 1%
    PoolId public boundPool;
    bool public bound;
    uint24 public fee;

    constructor(IPoolManager _poolManager, address _owner, uint24 _maxFee, uint24 _initialFee) BaseHook(_poolManager) {
        if (_maxFee > LPFeeLibrary.MAX_LP_FEE || _initialFee > _maxFee) revert FeeAboveCap();
        _initializeOwner(_owner);
        maxFee = _maxFee;
        fee = _initialFee;
    }

    function getHookPermissions() public pure override returns (Hooks.Permissions memory) {
        return Hooks.Permissions({
            beforeInitialize: true,
            afterInitialize: false,
            beforeAddLiquidity: false,
            afterAddLiquidity: false,
            beforeRemoveLiquidity: false,
            afterRemoveLiquidity: false,
            beforeSwap: true,
            afterSwap: false,
            beforeDonate: false,
            afterDonate: false,
            beforeSwapReturnDelta: false,
            afterSwapReturnDelta: false,
            afterAddLiquidityReturnDelta: false,
            afterRemoveLiquidityReturnDelta: false
        });
    }

    function setFee(uint24 newFee) external onlyOwner {
        if (newFee > maxFee) revert FeeAboveCap();
        fee = newFee;
        emit FeeUpdated(newFee);
    }

    /// @dev Anyone can initialize a pool that points at this hook; bind the first one and reject the rest.
    function _beforeInitialize(address, PoolKey calldata key, uint160) internal override returns (bytes4) {
        if (!LPFeeLibrary.isDynamicFee(key.fee)) revert NotDynamicFee();
        if (bound) revert PoolAlreadyBound();
        bound = true;
        boundPool = key.toId();
        return BaseHook.beforeInitialize.selector;
    }

    function _beforeSwap(address, PoolKey calldata, SwapParams calldata, bytes calldata)
        internal
        view
        override
        returns (bytes4, BeforeSwapDelta, uint24)
    {
        // OVERRIDE_FEE_FLAG makes the PoolManager use this fee for this swap only.
        return (BaseHook.beforeSwap.selector, BeforeSwapDeltaLibrary.ZERO_DELTA, fee | LPFeeLibrary.OVERRIDE_FEE_FLAG);
    }
}
```

Design choices worth copying:
- **Pool binding in `beforeInitialize`.** Any address can initialize any `PoolKey` that names your hook. OZ's `onlyValidPools` only checks `key.hooks == this`. Hooks with per-pool or global state must reject unknown pools themselves.
- **An immutable cap on owner power.** "Liquidity theft via hook fee" and "malicious-owner oracle" are documented incident classes (see `references/security.md`). Bounding admin knobs at construction removes the rug path.
- **Solady `Ownable` needs `_initializeOwner`.** Without it the owner is `address(0)` and `onlyOwner` reverts `Unauthorized()` forever.

## Test It (hookmate harness)

Copy `test/utils/{Deployers,BaseTest}.sol` and `test/utils/libraries/EasyPosm.sol` from v4-template. `deployArtifactsAndLabel()` deploys Permit2, PoolManager, PositionManager and hookmate's `IUniswapV4Router04` locally (chainid 31337). On a fork it reads the canonical addresses from `AddressConstants`, so the same test runs with `--fork-url`.

Core of `test/CappedDynamicFeeHook.t.sol` (`contract CappedDynamicFeeHookTest is BaseTest`, `using EasyPosm for IPositionManager`). The full file, with imports and all four tests, is in `references/testing-and-deployment.md`:

```solidity
function setUp() public {
    deployArtifactsAndLabel(); // hookmate: Permit2, PoolManager, PositionManager, V4Router
    (currency0, currency1) = deployCurrencyPair();

    // Low 14 bits = permissions; the 0x4444 namespace keeps test hooks from colliding.
    address flags = address(uint160(Hooks.BEFORE_INITIALIZE_FLAG | Hooks.BEFORE_SWAP_FLAG) ^ (0x4444 << 144));
    deployCodeTo(
        "CappedDynamicFeeHook.sol:CappedDynamicFeeHook",
        abi.encode(poolManager, owner, uint24(10_000), uint24(3000)),
        flags
    );
    hook = CappedDynamicFeeHook(flags);

    poolKey = PoolKey(currency0, currency1, LPFeeLibrary.DYNAMIC_FEE_FLAG, 60, IHooks(hook));
    poolManager.initialize(poolKey, Constants.SQRT_PRICE_1_1);

    int24 lower = TickMath.minUsableTick(60);
    int24 upper = TickMath.maxUsableTick(60);
    uint128 liquidity = 100e18;
    (uint256 a0, uint256 a1) = LiquidityAmounts.getAmountsForLiquidity(
        Constants.SQRT_PRICE_1_1, TickMath.getSqrtPriceAtTick(lower), TickMath.getSqrtPriceAtTick(upper), liquidity
    );
    positionManager.mint(
        poolKey, lower, upper, liquidity, a0 + 1, a1 + 1, address(this), block.timestamp, Constants.ZERO_BYTES
    );
}

function _swap(uint256 amountIn) internal returns (uint256 out) {
    BalanceDelta d = swapRouter.swapExactTokensForTokens({
        amountIn: amountIn,
        amountOutMin: 0,
        zeroForOne: true,
        poolKey: poolKey,
        hookData: Constants.ZERO_BYTES,
        receiver: address(this),
        deadline: block.timestamp + 1
    });
    out = uint256(int256(d.amount1()));
}

function test_HigherFeeGivesLessOutput() public {
    uint256 snap = vm.snapshotState();
    uint256 outLowFee = _swap(1e18);
    vm.revertToState(snap);

    vm.prank(owner);
    hook.setFee(10_000);
    assertLt(_swap(1e18), outLowFee);
}
```

Hook reverts arrive **wrapped**: the PoolManager re-raises them as `CustomRevert.WrappedError(hook, callbackSelector, innerRevertData, Hooks.HookCallFailed.selector)`. `vm.expectRevert(MyHook.MyError.selector)` alone will not match. The exact encoding, plus fuzz/invariant/fork recipes, are in `references/testing-and-deployment.md`.

```bash
forge test -vvv                                   # local, hookmate artifacts
forge test --fork-url $RPC_URL -vvv               # same tests against canonical v4 deployment
forge snapshot --match-contract CappedDynamicFee  # track callback gas per change
```

## Deploy (HookMiner + CREATE2)

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Script, console} from "forge-std/Script.sol";
import {Hooks} from "@uniswap/v4-core/src/libraries/Hooks.sol";
import {IPoolManager} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import {HookMiner} from "@uniswap/v4-periphery/src/utils/HookMiner.sol";
import {AddressConstants} from "hookmate/constants/AddressConstants.sol";
import {V4PoolManagerDeployer} from "hookmate/artifacts/V4PoolManager.sol";

import {CappedDynamicFeeHook} from "../src/CappedDynamicFeeHook.sol";

/// forge script script/DeployHook.s.sol --rpc-url $RPC_URL --account deployer --broadcast
contract DeployHook is Script {
    function run() external returns (CappedDynamicFeeHook hook) {
        vm.startBroadcast();
        // Local anvil has no PoolManager: deploy hookmate's canonical artifact. Elsewhere use the real one.
        IPoolManager poolManager = block.chainid == 31337
            ? IPoolManager(V4PoolManagerDeployer.deploy(msg.sender))
            : IPoolManager(AddressConstants.getPoolManagerAddress(block.chainid));
        vm.stopBroadcast();

        uint160 flags = uint160(Hooks.BEFORE_INITIALIZE_FLAG | Hooks.BEFORE_SWAP_FLAG);
        bytes memory args = abi.encode(poolManager, msg.sender, uint24(10_000), uint24(3000));
        // `new X{salt: s}` in a broadcast goes through forge-std's CREATE2_FACTORY (0x4e59...956C).
        (address predicted, bytes32 salt) =
            HookMiner.find(CREATE2_FACTORY, flags, type(CappedDynamicFeeHook).creationCode, args);

        vm.startBroadcast();
        hook = new CappedDynamicFeeHook{salt: salt}(poolManager, msg.sender, 10_000, 3000);
        vm.stopBroadcast();

        require(address(hook) == predicted, "hook address mismatch");
        console.log("hook", address(hook));
    }
}
```

- Mine with the **same constructor args you deploy with**. Any change alters the init-code hash, and the address no longer carries the flags.
- `HookMiner.find` must use the deployer that actually runs CREATE2. In a broadcast that is `CREATE2_FACTORY`; a custom factory needs its own address.
- Before routing volume, check whether the Uniswap routing API's per-chain hook allowlist (`hooksAddressesAllowlist.ts`) includes your hook. Unlisted hooks do not get routed by the Uniswap interface.

## Hook Archetypes (from awesome-uniswap-hooks)

Start from an OZ base when one fits. It is audited and already handles the delta plumbing.

| Goal | Permissions | Start from | Reference implementations |
|---|---|---|---|
| Gated pools (KYC, allowlist, NFT holders, trading hours) | `beforeSwap`, `beforeAddLiquidity` | `BaseHook` | Civic, World ID KYC, NFT-owners-only, trading-days |
| Dynamic / volatility fee | `beforeSwap` (+`afterInitialize`) | `BaseDynamicFee`, `BaseOverrideFee` | Captain Hook dynamic fees, Slippage Fee Hook, Super DCA |
| Hook fee / referral fee | `afterSwap`+`afterSwapReturnDelta` | `BaseHookFee`, `BaseDynamicAfterFee` | Ref Fee Hook, Zora, Clanker |
| Limit / stop-loss / take-profit orders | `afterInitialize`, `afterSwap` | `LimitOrderHook` | v4-stoploss, LearnWeb3 take-profit |
| TWAMM / DCA | `beforeSwap`, `beforeAddLiquidity`, `afterInitialize` | `BaseHook` | Uniswap TWAMM, v4-twamm-hook, Super DCA |
| Oracle (geomean, truncated, backrun-resistant) | `afterInitialize`, `beforeSwap` | `BaseOracleHook`, `OracleHookWithV3Adapters` | Geomean/Truncated oracle, BackGeoOracle |
| Custom curve / NoOp (constant-sum, v2-on-v4, PMM) | `beforeSwap`+`beforeSwapReturnDelta`, `beforeAddLiquidity` | `BaseCustomCurve`, `BaseCustomAccounting` | v4-constant-sum, v2-on-v4, EulerSwap |
| Async / intent / batch execution | `beforeSwap`+`beforeSwapReturnDelta` | `BaseAsyncSwap` | Angstrom-style auctions |
| MEV / sandwich resistance, LVR to LPs | `beforeSwap`, `afterSwap` | `AntiSandwichHook` | Detox, minimize-LVR PoC |
| JIT liquidity penalty | `afterAddLiquidity`, `afterRemoveLiquidity` (+deltas) | `LiquidityPenaltyHook` | - |
| Rehypothecation (idle liquidity → lending) | custom accounting | `ReHypothecationHook` | Bunni |
| Launchpads / LBP / fair launch | `beforeSwap`, `beforeAddLiquidity`, fee deltas | `BaseHook` + fee bases | Flaunch, Doppler, uni-lbp |

The full catalog with per-archetype pitfalls and links, plus a verified NoOp constant-sum hook (ERC-6909 claims, `BeforeSwapDelta`, fuzzed 1:1) is in `references/hook-archetypes.md`.

## Solady in Hooks

| Need inside a hook | Solady (v0.1.26) | Notes |
|---|---|---|
| Admin / roles | `auth/Ownable.sol`, `auth/OwnableRoles.sol` | Call `_initializeOwner(owner)` in the constructor |
| Narrowing casts for deltas | `utils/SafeCastLib.sol` `toInt128`, `toUint128`, `toUint24` | `using SafeCastLib for int256;` - the `using` type must match |
| Reentrancy on hook entrypoints | `utils/ReentrancyGuardTransient.sol` | Defaults to **SSTORE off mainnet**; override `_useTransientReentrancyGuardOnlyOnMainnet()` → `false` on Cancun L2s |
| Fee / price math | `utils/FixedPointMathLib.sol` `mulDiv`, `fullMulDiv`, `mulWad`, `sqrt` | Check rounding direction per call |
| Token moves outside the PoolManager | `utils/SafeTransferLib.sol` | Inside `unlock`, use `CurrencySettler` instead |
| Per-tx scratch state between callbacks | `utils/LibTransient.sol` | Cleared at tx end; never persist cross-tx facts here |
| Tick / order bitmaps, sets | `utils/LibBitmap.sol`, `utils/EnumerableSetLib.sol` | Bound iteration to keep swaps under gas budget |

Look every signature up before writing it, with `solady-reference` if installed or in the pinned Solady source. `references/solady-composition.md` has the hook-specific caveats, including Solady ERC20's default Permit2 infinite allowance for launchpad tokens.

## Security Checklist (minimum before any deploy)

1. **Least privilege.** Enable only needed flags. Any `*ReturnDelta` flag is high or critical risk: `beforeSwapReturnDelta` lets the hook take the entire input (the "NoOp rug").
2. **Callbacks are PoolManager-only** (OZ `BaseHook` does this). Your own `unlockCallback` and admin functions need explicit guards too.
3. **`sender` is the router, not the user.** `msg.sender` is always the PoolManager. User identity requires a trusted router allowlist plus `hookData` or `msgSender()` from that router.
4. **Bind or validate pools.** Reject unexpected `PoolKey`s in `beforeInitialize`. Key all state by `PoolId`.
5. **Deltas net to zero on every path,** including reverts, partial fills, exact-in vs exact-out, and both swap directions.
6. **Bound admin power.** Use immutable caps on fees, timelock any parameter that moves value, and avoid upgradeable hooks unless audited.
7. **Quote equals settle.** Aggregators simulate swaps. A hook whose behaviour depends on `tx.origin`, `block.*` or private state can quote one price and settle another. Make outcomes deterministic from swap inputs.
8. **Gas.** `beforeSwap` runs on every swap. Keep it under ~50k gas, with no unbounded loops.
9. **Test matrix.** Run unit, fuzz (both directions, both signs), invariant ("sum of claims ≤ hook balance"), and fork tests against the canonical PoolManager, then Slither. Get an audit when the risk score calls for it (`references/security.md`).

## References

- `references/balance-delta.md`: the `BalanceDelta` type, sign and perspective rules, swap/liquidity/donate returns, how hook deltas combine, settlement, verified swap and `SafeCallback` liquidity routers (the official guide, corrected), pitfalls.
- `references/hook-archetypes.md`: every awesome-uniswap-hooks archetype with permissions, OZ base, pitfalls and links, plus the verified `ConstantSumHook`.
- `references/testing-and-deployment.md`: the hookmate harness internals, wrapped-revert assertions, fuzz/invariant/fork recipes, anvil deploy, verification, and the canonical addresses.
- `references/security.md`: threat model, permission risk matrix, incident classes (re-init lock, hook-fee theft, malicious owner, quote spoofing), audit checklist.
- `references/solady-composition.md`: Solady patterns and gotchas specific to hooks.
- `references/ecosystem.md`: docs, production hooks, tools, templates, tutorials, research.
