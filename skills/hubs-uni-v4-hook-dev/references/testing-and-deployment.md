# Testing and Deployment

Everything here runs on Foundry 1.8.3 with the remappings in `SKILL.md`. For general Forge usage (cheatcodes, `bound`, invariant config, `forge script` flags) load `foundry-solidity`.

## Contents

- [The hookmate test harness](#the-hookmate-test-harness)
- [Placing a hook at a flagged address in tests](#placing-a-hook-at-a-flagged-address-in-tests)
- [Asserting hook reverts (WrappedError)](#asserting-hook-reverts-wrappederror)
- [Fuzz and invariant tests](#fuzz-and-invariant-tests)
- [Fork tests against canonical deployments](#fork-tests-against-canonical-deployments)
- [Deploying: mining, CREATE2, verification](#deploying-mining-create2-verification)
- [Canonical addresses](#canonical-addresses)
- [Debugging checklist](#debugging-checklist)

## The hookmate test harness

[hookmate](https://github.com/akshatmittal/hookmate) (v0.6.0; formerly `saucepoint/hookmate`) ships canonical **creation bytecode** for `PoolManager`, `PositionManager`, `Permit2` and its stateless [V4 router](https://github.com/hookmate/v4-router). It also ships `AddressConstants` for every chain Uniswap v4 is deployed on, and `DeployHelper` (CREATE2 with revert bubbling).

`uniswapfoundation/v4-template` builds two small test contracts on top. Copy them as they are into `test/utils/`:

- `Deployers.sol` (abstract, no forge-std dependency, so scripts can reuse it):
  - `deployArtifacts()` → `deployPermit2()` (etched at the canonical `0x000000000022D473030F116dDEE9F6B43aC78BA3`), `deployPoolManager()`, `deployPositionManager()`, `deployRouter()`.
  - On chainid 31337 it deploys fresh instances. On any other chain (a fork) it binds to `AddressConstants.get*Address(block.chainid)`.
  - `deployCurrencyPair()` sorts tokens, mints 10M to the test, and approves Permit2 → PositionManager/PoolManager plus the router.
- `BaseTest.sol` = `Test` + `Deployers`, with labels and `_etch` → `vm.etch`.
- `libraries/EasyPosm.sol`: one-call `positionManager.mint(...)`, `increaseLiquidity`, `decreaseLiquidity`, `collect`, `burn` wrappers over `modifyLiquidities` action encoding.

Swaps go through `IUniswapV4Router04`:

| Call | Meaning |
|---|---|
| `swapExactTokensForTokens(amountIn, amountOutMin, zeroForOne, poolKey, hookData, receiver, deadline)` | single pool, exact in |
| `swapTokensForExactTokens(amountOut, amountInMax, zeroForOne, poolKey, hookData, receiver, deadline)` | single pool, exact out |
| `swapExactTokensForTokens(amountIn, amountOutMin, startCurrency, PathKey[] path, receiver, deadline)` | multi-hop |
| `swap(int256 amountSpecified, uint256 amountLimit, startCurrency, path, receiver, deadline)` | generic (negative = exact in) |

All return the swapper's `BalanceDelta`: negative amounts were paid, positive were received.

Why not v4-core's own `test/utils/Deployers.sol`? It compiles `PoolManager.sol` from source, which pins `pragma solidity 0.8.26` and forces your whole project onto that compiler. It also uses v4-core's test routers (`PoolSwapTest`, `PoolModifyLiquidityTest`), which behave differently from the production routers your users hit.

### Full example: `test/CappedDynamicFeeHook.t.sol`

The complete suite for the `SKILL.md` reference hook (4 tests, all passing): fee effect, cap, auth, and second-pool rejection.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IHooks} from "@uniswap/v4-core/src/interfaces/IHooks.sol";
import {Hooks} from "@uniswap/v4-core/src/libraries/Hooks.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {LPFeeLibrary} from "@uniswap/v4-core/src/libraries/LPFeeLibrary.sol";
import {CustomRevert} from "@uniswap/v4-core/src/libraries/CustomRevert.sol";
import {PoolKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import {BalanceDelta} from "@uniswap/v4-core/src/types/BalanceDelta.sol";
import {Currency} from "@uniswap/v4-core/src/types/Currency.sol";
import {IPositionManager} from "@uniswap/v4-periphery/src/interfaces/IPositionManager.sol";
import {LiquidityAmounts} from "@uniswap/v4-core/test/utils/LiquidityAmounts.sol";
import {Constants} from "@uniswap/v4-core/test/utils/Constants.sol";
import {Ownable} from "solady/auth/Ownable.sol";

import {EasyPosm} from "./utils/libraries/EasyPosm.sol";
import {BaseTest} from "./utils/BaseTest.sol";
import {CappedDynamicFeeHook} from "../src/CappedDynamicFeeHook.sol";

contract CappedDynamicFeeHookTest is BaseTest {
    using EasyPosm for IPositionManager;

    Currency currency0;
    Currency currency1;
    PoolKey poolKey;
    CappedDynamicFeeHook hook;
    address owner = makeAddr("owner");

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

    function test_RevertWhen_FeeAboveCap() public {
        vm.prank(owner);
        vm.expectRevert(CappedDynamicFeeHook.FeeAboveCap.selector);
        hook.setFee(10_001);
    }

    function test_RevertWhen_NotOwner() public {
        vm.expectRevert(Ownable.Unauthorized.selector);
        hook.setFee(1);
    }

    function test_RevertWhen_SecondPoolUsesHook() public {
        PoolKey memory other = PoolKey(currency0, currency1, LPFeeLibrary.DYNAMIC_FEE_FLAG, 10, IHooks(hook));
        // PoolManager wraps hook reverts: WrappedError(hook, selector, reason, details).
        vm.expectRevert(
            abi.encodeWithSelector(
                CustomRevert.WrappedError.selector,
                address(hook),
                IHooks.beforeInitialize.selector,
                abi.encodeWithSelector(CappedDynamicFeeHook.PoolAlreadyBound.selector),
                abi.encodeWithSelector(Hooks.HookCallFailed.selector)
            )
        );
        poolManager.initialize(other, Constants.SQRT_PRICE_1_1);
    }
}
```

## Placing a hook at a flagged address in tests

```solidity
address flags = address(uint160(Hooks.BEFORE_INITIALIZE_FLAG | Hooks.BEFORE_SWAP_FLAG) ^ (0x4444 << 144));
deployCodeTo(
    "CappedDynamicFeeHook.sol:CappedDynamicFeeHook",
    abi.encode(poolManager, owner, uint24(10_000), uint24(3000)),
    flags
);
hook = CappedDynamicFeeHook(flags);
```

- `deployCodeTo` runs the real constructor at that address, so `BaseHook`'s permission check runs too.
- `^ (0x4444 << 144)` sets high bytes so test hooks don't land on precompiles or collide with each other. Only the low 14 bits matter to the PoolManager.
- Immutables are set correctly, unlike `vm.etch` of runtime code.
- Use a distinct namespace per hook when a test deploys several.

Decode an address's permission bits from the shell (the last 14 binary digits, bit 13 → bit 0):

```bash
cast to-base 0x4444000000000000000000000000000000002888 bin
# ...10100010001000 → bits 13, 11, 7, 3 = beforeInitialize, beforeAddLiquidity, beforeSwap, beforeSwapReturnDelta
```

## Asserting hook reverts (WrappedError)

The PoolManager catches hook reverts and re-raises them as `CustomRevert.WrappedError(address target, bytes4 selector, bytes reason, bytes details)`. Import `CustomRevert` from `@uniswap/v4-core/src/libraries/CustomRevert.sol`:

```solidity
function test_RevertWhen_SecondPoolUsesHook() public {
    PoolKey memory other = PoolKey(currency0, currency1, LPFeeLibrary.DYNAMIC_FEE_FLAG, 10, IHooks(hook));
    // PoolManager wraps hook reverts: WrappedError(hook, selector, reason, details).
    vm.expectRevert(
        abi.encodeWithSelector(
            CustomRevert.WrappedError.selector,
            address(hook),
            IHooks.beforeInitialize.selector,
            abi.encodeWithSelector(CappedDynamicFeeHook.PoolAlreadyBound.selector),
            abi.encodeWithSelector(Hooks.HookCallFailed.selector)
        )
    );
    poolManager.initialize(other, Constants.SQRT_PRICE_1_1);
}
```

The `details` error is `Hooks.HookCallFailed()`, selector `0xa9e35b2f`. The official troubleshooting page (and a comment in `Hooks.sol`) still use the pre-1.0 name `FailedHookCall` (`0x36bc48c5`), which no longer exists. Decode traces with the current name.

Calls that go **directly to the hook** (admin functions, your own `addLiquidity`) are not wrapped. `vm.expectRevert(Ownable.Unauthorized.selector)` works for those. Routers may wrap again. When in doubt, run the call with `-vvvv` and copy the revert data from the trace.

## Fuzz and invariant tests

Fuzz the properties a hook promises, across **both directions and both signs** of `amountSpecified`:

```solidity
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
```

Invariant tests target a **handler** that bounds inputs and calls the real router. Hook-owned value is the thing to protect. Verified against `ConstantSumHook` (256 runs × 500 calls):

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {Test} from "forge-std/Test.sol";
import {IHooks} from "@uniswap/v4-core/src/interfaces/IHooks.sol";
import {IPoolManager} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import {Hooks} from "@uniswap/v4-core/src/libraries/Hooks.sol";
import {PoolKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import {Currency} from "@uniswap/v4-core/src/types/Currency.sol";
import {Constants} from "@uniswap/v4-core/test/utils/Constants.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";
import {IUniswapV4Router04} from "hookmate/interfaces/router/IUniswapV4Router04.sol";

import {BaseTest} from "./utils/BaseTest.sol";
import {ConstantSumHook} from "../src/ConstantSumHook.sol";

/// @dev The fuzzer calls only this handler; it bounds inputs and swaps through the real router.
contract SwapHandler is Test {
    IUniswapV4Router04 immutable router;
    PoolKey key;

    constructor(IUniswapV4Router04 _router, PoolKey memory _key) {
        router = _router;
        key = _key;
    }

    function swap(uint256 amount, bool zeroForOne, bool exactIn) external {
        amount = bound(amount, 1, 100e18);
        if (exactIn) {
            router.swapExactTokensForTokens(amount, 0, zeroForOne, key, "", address(this), block.timestamp + 1);
        } else {
            router.swapTokensForExactTokens(
                amount, type(uint256).max, zeroForOne, key, "", address(this), block.timestamp + 1
            );
        }
    }
}

contract ConstantSumHookInvariantTest is BaseTest {
    ConstantSumHook hook;
    Currency currency0;
    Currency currency1;
    SwapHandler handler;

    function setUp() public {
        deployArtifactsAndLabel();
        (currency0, currency1) = deployCurrencyPair();

        address flags = address(
            uint160(Hooks.BEFORE_ADD_LIQUIDITY_FLAG | Hooks.BEFORE_SWAP_FLAG | Hooks.BEFORE_SWAP_RETURNS_DELTA_FLAG)
                ^ (0x4444 << 144)
        );
        deployCodeTo("ConstantSumHook.sol:ConstantSumHook", abi.encode(poolManager), flags);
        hook = ConstantSumHook(flags);

        PoolKey memory key = PoolKey(currency0, currency1, 0, 60, IHooks(hook));
        poolManager.initialize(key, Constants.SQRT_PRICE_1_1);
        IERC20(Currency.unwrap(currency0)).approve(address(hook), type(uint256).max);
        IERC20(Currency.unwrap(currency1)).approve(address(hook), type(uint256).max);
        hook.addLiquidity(key, 1000e18);

        handler = new SwapHandler(swapRouter, key);
        // Fund the handler and let the router pull from it.
        for (uint256 i; i < 2; i++) {
            IERC20 token = IERC20(Currency.unwrap(i == 0 ? currency0 : currency1));
            token.transfer(address(handler), 1_000_000e18);
            vm.prank(address(handler));
            token.approve(address(swapRouter), type(uint256).max);
        }
        targetContract(address(handler));
    }

    /// Constant sum: total claims never change, whatever the swap sequence.
    function invariant_ClaimsSumIsConstant() public view {
        uint256 c0 = poolManager.balanceOf(address(hook), currency0.toId());
        uint256 c1 = poolManager.balanceOf(address(hook), currency1.toId());
        assertEq(c0 + c1, 2000e18);
    }

    /// The PoolManager always holds at least what it owes the hook in claims.
    function invariant_ManagerSolvent() public view {
        assertGe(
            IERC20(Currency.unwrap(currency0)).balanceOf(address(poolManager)),
            poolManager.balanceOf(address(hook), currency0.toId())
        );
    }
}
```

hookmate's router pulls tokens with a plain `transferFrom` from the caller, so the handler holds the tokens and approves the **router** directly. That differs from the PositionManager, which pulls via Permit2.

Useful invariants by archetype:
- Custom accounting: `sum(shares) ↔ hook claims`, and no LP can withdraw more than they deposited plus fees.
- Fee hooks: accrued fee ≤ cap × volume, and LP output is monotonic in fee.
- Order hooks: filled + open + cancelled = placed, per bucket.
- Every hook: `poolManager` holds ≥ the sum of ERC-6909 claims, and swaps with `hookData = ""` never revert because of the hook unless you designed it to.

## Fork tests against canonical deployments

The same suite runs on a fork. `Deployers` switches to the canonical PoolManager, PositionManager and router through `AddressConstants`:

```bash
forge test --fork-url $RPC_URL -vvv                         # latest block
forge test --fork-url $RPC_URL --fork-block-number 30000000 # pinned, reproducible
```

Fork tests catch:
- opcode support (TSTORE/MCOPY/PUSH0 on the target L2)
- real-token behaviour (fee-on-transfer, blocklists, USDT's non-standard `approve`)
- gas against real pool state

hookmate's router has its own canonical address per chain, and on a fork the harness uses it. Check that the chain exists in `AddressConstants`; unknown chains revert `UnsupportedChainId()`.

## Deploying: mining, CREATE2, verification

1. **Mine** with `HookMiner.find(deployer, flags, creationCode, constructorArgs)` from `@uniswap/v4-periphery/src/utils/HookMiner.sol`. It loops salts until `address & ALL_HOOK_MASK == flags`, up to 160,444 iterations.
   - Use `CREATE2_FACTORY` (forge-std's `0x4e59b44847b379578588920cA78FbF26c0B4956C`) when you deploy with `new Hook{salt: salt}(...)` inside `vm.startBroadcast()`.
   - Use your own factory's address if a factory deploys the hook.
   - Offline mining options: [v4hookaddressminer.xyz](https://v4hookaddressminer.xyz/) and [HookMineAndSinker](https://github.com/devtooligan/HookMineAndSinker).
2. **Deploy.** The script in `SKILL.md` was broadcast to a local anvil and printed a matching address:

   ```bash
   anvil &   # 31337 → the script deploys hookmate's PoolManager first
   forge script script/DeployHook.s.sol --rpc-url http://127.0.0.1:8545 \
     --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80 --broadcast
   # Real chains: use an encrypted keystore, not a raw key
   cast wallet import deployer --interactive
   forge script script/DeployHook.s.sol --rpc-url $RPC_URL --account deployer --broadcast --verify
   ```

3. **Verify** after the fact:

   ```bash
   forge verify-contract $HOOK src/CappedDynamicFeeHook.sol:CappedDynamicFeeHook \
     --chain base --constructor-args $(cast abi-encode "f(address,address,uint24,uint24)" $PM $OWNER 10000 3000)
   ```

4. **Initialize the pool** (fee `0x800000` for dynamic pools), then add liquidity through PositionManager. v4-template's `script/01_CreatePoolAndAddLiquidity.s.sol` does both in one `multicall`.
5. **Get routed.** The Uniswap routing API only routes through hooks on its per-chain [allowlist](https://github.com/Uniswap/routing-api/blob/main/lib/util/hooksAddressesAllowlist.ts). Aggregators apply their own safety screens (see `security.md`, "Quote equals settle").

Pitfalls:
- **A different `msg.sender` changes the address.** If the constructor reads `msg.sender` (for example `_initializeOwner(msg.sender)`), then in a broadcast `msg.sender` is the CREATE2 factory, not your EOA. Pass the owner explicitly, as the example does.
- **Changing the args changes the address.** Constructor args are part of the init-code hash: changing any argument means re-mining.
- **The address must stay where it was mined.** Don't put the hook behind a proxy that you deploy separately. The **proxy** address carries the flags, and the implementation's code runs via delegatecall. Upgradeable hooks raise the trust bar sharply (see `security.md`).

## Canonical addresses

From `hookmate/src/constants/AddressConstants.sol` (v0.6.0). Permit2 is `0x000000000022D473030F116dDEE9F6B43aC78BA3` on every chain.

| Chain (id) | PoolManager | PositionManager |
|---|---|---|
| Ethereum (1) | `0x000000000004444c5dc75cB358380D2e3dE08A90` | `0xbD216513d74C8cf14cf4747E6AaA6420FF64ee9e` |
| Unichain (130) | `0x1F98400000000000000000000000000000000004` | `0x4529A01c7A0410167c5740C487A8DE60232617bf` |
| Base (8453) | `0x498581fF718922c3f8e6A244956aF099B2652b2b` | `0x7C5f5A4bBd8fD63184577525326123B519429bDc` |
| Arbitrum One (42161) | `0x360E68faCcca8cA495c1B759Fd9EEe466db9FB32` | `0xd88F38F930b7952f2DB2432Cb002E7abbF3dD869` |
| Optimism (10) | `0x9a13F98Cb987694C9F086b1F5eB990EeA8264Ec3` | `0x3C3Ea4B57a46241e54610e5f022E5c45859A1017` |
| Polygon (137) | `0x67366782805870060151383F4BbFF9daB53e5cD6` | `0x1Ec2eBf4F37E7363FDfe3551602425af0B3ceef9` |
| BNB Chain (56) | `0x28e2Ea090877bF75740558f6BFB36A5ffeE9e9dF` | `0x7A4a5c919aE2541AeD11041A1AEeE68f1287f95b` |
| Sepolia (11155111) | `0xE03A1074c86CFeDd5C142C4F04F1a1536e203543` | `0x429ba70129df741B2Ca2a85BC3A2a3328e5c09b4` |
| Base Sepolia (84532) | `0x05E73354cFDd6745C338b50BcFDfA3Aa6fA03408` | `0x4B2C77d209D3405F41a037Ec6c77F7F5b8e2ca80` |
| Unichain Sepolia (1301) | `0x00B036B58a818B1BC34d502D3fE730Db729e62AC` | `0xf969Aee60879C54bAAed9F3eD26147Db216Fd664` |

`AddressConstants` also covers Blast, Zora, World Chain, Ink, Soneium, Avalanche, Celo, Monad and Arbitrum Sepolia. In code, call `AddressConstants.getPoolManagerAddress(block.chainid)` rather than copying addresses.

## Debugging checklist

| Symptom | Likely cause |
|---|---|
| Deploy reverts `HookAddressNotValid(address)` | Address bits ≠ `getHookPermissions()`: wrong salt, args changed after mining, or the wrong deployer passed to `HookMiner` |
| `initialize` reverts `HookAddressNotValid` | A `*_RETURNS_DELTA` bit is set without its base bit, or the hook address has zero flags and a static fee |
| Swap reverts `CurrencyNotSettled` | A hook or callback path leaves a non-zero delta: missing `take`/`settle`, or a wrong sign in `BeforeSwapDelta` |
| `HookNotImplemented()` | The flag is set but the internal `_callback` isn't overridden |
| A callback never runs | The flag is missing from the address, or the hook itself is the caller (self-calls skip callbacks) |
| Override fee has no effect | The pool isn't `DYNAMIC_FEE_FLAG`, or `OVERRIDE_FEE_FLAG` wasn't OR-ed in |
| `UnauthorizedDynamicLPFeeUpdate` | `updateDynamicLPFee` called by anything other than the pool's hook |
| `ManagerLocked()` | A PoolManager state change outside `unlock` (call it from `unlockCallback`) |
| `Source ".../src/src/..." not found` | Two copies of v4-core and auto-remappings: pin `v4-core/` and `v4-periphery/` explicitly |
