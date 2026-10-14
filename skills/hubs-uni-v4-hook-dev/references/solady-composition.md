# Composing Solady with v4 Hooks

Solady v0.1.26 (`forge install Vectorized/solady@v0.1.26`, remap `solady/=lib/solady/src/`) works alongside OZ `uniswap-hooks`. OZ supplies the hook bases and `CurrencySettler`; Solady supplies auth, math, casts, guards and tokens with lower gas. For any Solady signature, revert or rounding mode not shown here, use the `solady-reference` skill (`scripts/lookup.sh <symbol>`) instead of memory.

## Contents

- [Which library for which hook need](#which-library-for-which-hook-need)
- [Verified example: capped skim fee with roles](#verified-example-capped-skim-fee-with-roles)
- [Gotchas specific to hooks](#gotchas-specific-to-hooks)
- [Solady vs OpenZeppelin inside one hook](#solady-vs-openzeppelin-inside-one-hook)

## Which library for which hook need

| Hook need | Solady | Key API (v0.1.26) |
|---|---|---|
| Single admin | `auth/Ownable.sol` | `_initializeOwner(addr)`, `onlyOwner`, `transferOwnership`, two-step `requestOwnershipHandover`/`completeOwnershipHandover`; reverts `Unauthorized()` |
| Keepers / fee setters | `auth/OwnableRoles.sol` | `_ROLE_0`…`_ROLE_255`, `grantRoles`, `onlyRoles`, `onlyOwnerOrRoles` |
| Fee and price math | `utils/FixedPointMathLib.sol` | `mulDiv`/`mulDivUp` (revert on overflow), `fullMulDiv`/`fullMulDivUp` (512-bit intermediate), `mulWad`, `sqrt` |
| Delta narrowing | `utils/SafeCastLib.sol` | `toInt128(int256)`, `toInt128(uint256)`, `toUint128`, `toUint24`; the `using` type must match the argument type |
| Reentrancy | `utils/ReentrancyGuardTransient.sol` | `nonReentrant`; override `_useTransientReentrancyGuardOnlyOnMainnet()` |
| Scratch state across callbacks in one tx | `utils/LibTransient.sol` | `LibTransient.tUint256(slot).set/get/inc/clear` (Cancun+) |
| Orders by tick / bitmaps | `utils/LibBitmap.sol` | `get`, `set`, `unset`, `findLastSet` |
| Allowlists | `utils/EnumerableSetLib.sol` | `AddressSet`, `add`, `remove`, `contains`, `length` |
| Token moves outside `unlock` | `utils/SafeTransferLib.sol` | `safeTransfer`, `safeTransferFrom`, `safeTransferETH`; inside `unlock` use `CurrencySettler` |
| Signed hookData | `utils/EIP712.sol`, `utils/SignatureCheckerLib.sol` | `_hashTypedData`, `isValidSignatureNow` (EOA + ERC-1271) |
| Launch / share tokens | `tokens/ERC20.sol`, `tokens/ERC4626.sol`, `tokens/ERC6909.sol` | see gotchas |
| Deterministic deploys / clones | `utils/LibClone.sol`, `utils/CREATE3.sol` | only for non-hook helpers; a hook's address must come from CREATE2 + mined salt |

## Verified example: capped skim fee with roles

This hook skims a fee from the unspecified side of each swap through `afterSwapReturnDelta`, held as ERC-6909 claims. Admin is Solady `OwnableRoles`, the math is `FixedPointMathLib.mulDivUp` (rounded in the pool's favour), and the narrowing uses `SafeCastLib`. It compiles against v4-core 1.0.2, OZ uniswap-hooks `b5f1057` and Solady 0.1.26, and the tests below pass, including a 256-run fuzz.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {BaseHook} from "@openzeppelin/uniswap-hooks/src/base/BaseHook.sol";
import {CurrencySettler} from "@openzeppelin/uniswap-hooks/src/utils/CurrencySettler.sol";
import {Hooks} from "@uniswap/v4-core/src/libraries/Hooks.sol";
import {IPoolManager, SwapParams} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import {PoolKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import {Currency} from "@uniswap/v4-core/src/types/Currency.sol";
import {BalanceDelta} from "@uniswap/v4-core/src/types/BalanceDelta.sol";
import {OwnableRoles} from "solady/auth/OwnableRoles.sol";
import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";
import {SafeCastLib} from "solady/utils/SafeCastLib.sol";

/// @notice Skims a capped hook fee from the unspecified side of every swap, held as ERC-6909 claims.
contract SkimFeeHook is BaseHook, OwnableRoles {
    using CurrencySettler for Currency;
    using SafeCastLib for uint256;

    error FeeAboveCap();

    uint256 public constant FEE_SETTER_ROLE = _ROLE_0;
    uint256 public constant FEE_DENOMINATOR = 1_000_000;
    uint24 public constant MAX_HOOK_FEE = 10_000; // 1%, immutable bound on admin power
    uint24 public hookFee;

    constructor(IPoolManager _poolManager, address _owner, uint24 _hookFee) BaseHook(_poolManager) {
        if (_hookFee > MAX_HOOK_FEE) revert FeeAboveCap();
        _initializeOwner(_owner);
        hookFee = _hookFee;
    }

    function getHookPermissions() public pure override returns (Hooks.Permissions memory) {
        return Hooks.Permissions({
            beforeInitialize: false,
            afterInitialize: false,
            beforeAddLiquidity: false,
            afterAddLiquidity: false,
            beforeRemoveLiquidity: false,
            afterRemoveLiquidity: false,
            beforeSwap: false,
            afterSwap: true,
            beforeDonate: false,
            afterDonate: false,
            beforeSwapReturnDelta: false,
            afterSwapReturnDelta: true,
            afterAddLiquidityReturnDelta: false,
            afterRemoveLiquidityReturnDelta: false
        });
    }

    function setHookFee(uint24 newFee) external onlyOwnerOrRoles(FEE_SETTER_ROLE) {
        if (newFee > MAX_HOOK_FEE) revert FeeAboveCap();
        hookFee = newFee;
    }

    function _afterSwap(address, PoolKey calldata key, SwapParams calldata params, BalanceDelta delta, bytes calldata)
        internal
        override
        returns (bytes4, int128)
    {
        // Unspecified side: output for exact-in, input for exact-out.
        bool exactIn = params.amountSpecified < 0;
        (Currency unspecified, int128 amount) =
            exactIn == params.zeroForOne ? (key.currency1, delta.amount1()) : (key.currency0, delta.amount0());
        uint256 abs = amount < 0 ? uint256(-int256(amount)) : uint256(int256(amount));

        // Round the fee up: the pool side never loses to rounding.
        uint256 fee = FixedPointMathLib.mulDivUp(abs, hookFee, FEE_DENOMINATOR);
        if (fee == 0) return (BaseHook.afterSwap.selector, 0);

        // Hook mints itself claims (debit), and the returned delta credits it the same amount.
        unspecified.take(poolManager, address(this), fee, true);
        return (BaseHook.afterSwap.selector, fee.toInt128());
    }
}
```

Why the signs work:
- `delta` is the swapper's `BalanceDelta` before the hook acts.
- Returning `+fee` as the `int128` means the hook is owed `fee` of the unspecified currency, and the PoolManager takes it from the swapper: less output on exact-in, more input on exact-out.
- `take(..., claims=true)` mints that `fee` to the hook as ERC-6909, which creates a matching debt, so the hook nets to zero.
- If you forget the `take`, the swap reverts `CurrencyNotSettled`. If you take without returning the delta, LPs pay the fee instead of the swapper.

The tests, under the hookmate harness from `testing-and-deployment.md` (hook at `AFTER_SWAP_FLAG | AFTER_SWAP_RETURNS_DELTA_FLAG`, a 0.30% static-fee pool, 100e18 full-range liquidity, hook fee 5000 = 0.5%):

```solidity
function testFuzz_ExactInFeeOnOutput(uint256 amountIn) public {
    amountIn = bound(amountIn, 1e6, 10e18);
    BalanceDelta d =
        swapRouter.swapExactTokensForTokens(amountIn, 0, true, poolKey, "", address(this), block.timestamp + 1);
    uint256 received = uint256(int256(d.amount1()));
    uint256 fee = poolManager.balanceOf(address(hook), currency1.toId());
    // The swapper got gross output minus the hook fee, rounded in the pool's favour.
    assertEq(fee, FixedPointMathLib.mulDivUp(received + fee, 5000, 1_000_000));
}

function test_ExactOutFeeOnInput() public {
    BalanceDelta d = swapRouter.swapTokensForExactTokens(
        1e18, type(uint256).max, true, poolKey, "", address(this), block.timestamp + 1
    );
    assertEq(d.amount1(), 1e18); // exact output delivered
    uint256 paid = uint256(-int256(d.amount0()));
    uint256 fee = poolManager.balanceOf(address(hook), currency0.toId());
    assertEq(fee, FixedPointMathLib.mulDivUp(paid - fee, 5000, 1_000_000));
}

function test_RoleCanSetFee() public {
    uint256 role = hook.FEE_SETTER_ROLE();
    vm.prank(owner);
    hook.grantRoles(keeper, role);
    vm.prank(keeper);
    hook.setHookFee(100);
    assertEq(hook.hookFee(), 100);

    vm.prank(makeAddr("rando"));
    vm.expectRevert(Ownable.Unauthorized.selector);
    hook.setHookFee(1);
}
```

Production additions: a way to withdraw the accrued claims (owner `unlock` → `burn` claims → `take` tokens, or OZ `BaseHookFee.handleHookFees`) and events for indexers (`IHookEvents`).

## Gotchas specific to hooks

1. **`ReentrancyGuardTransient` is not transient on L2s by default.** `_useTransientReentrancyGuardOnlyOnMainnet()` returns `true`, so on Base, Unichain, Arbitrum and others it uses SSTORE (~20k gas per guarded call). On Cancun-capable chains, override it to `false`:

   ```solidity
   function _useTransientReentrancyGuardOnlyOnMainnet() internal pure override returns (bool) {
       return false;
   }
   ```

2. **`Ownable` has no owner until you call `_initializeOwner`.** Pass the owner as a constructor argument. Don't use `msg.sender`: under a CREATE2 broadcast it is the factory (`0x4e59…956C`), and the hook would be permanently ownerless.
3. **`OwnableRoles` already is `Ownable`.** Listing both is redundant. `onlyOwnerOrRoles` lets the owner through regardless of roles, so a compromised owner key bypasses every role split.
4. **The `SafeCastLib` `using` type must match.** `using SafeCastLib for uint256;` doesn't attach `toInt128(int256)`; casting `-params.amountSpecified` needs `using SafeCastLib for int256;`.
5. **Rounding direction is your job.** `mulDiv` rounds down and `mulDivUp` rounds up. Fees owed to the hook or LPs round up, and amounts paid out round down. `mulDiv` reverts on 256-bit overflow of `x*y`; `fullMulDiv` doesn't.
6. **Solady `ERC20` gives Permit2 infinite allowance by default.** This matters for launchpad hooks that deploy tokens. Override `_givePermit2InfiniteAllowance()` → `false` unless that is intended. Solady `ERC20` also allows mint/transfer to `address(0)` and zero-amount transfers; add checks if your accounting assumes otherwise.
7. **Share tokens for hook-owned liquidity.** Solady `ERC4626` has `_useVirtualShares()` (default `true`) and `_decimalsOffset()` to blunt first-depositor inflation. Keep them on for hook-owned vault shares. Solady `ERC6909` is a fit for per-pool LP shares (id = `uint256(PoolId.unwrap(id))`).
8. **`LibTransient` is per-transaction, not per-call.** Values survive across the PoolManager's nested callbacks within one transaction (useful for passing `beforeSwap` → `afterSwap` data) and across multiple swaps in the same transaction (dangerous). Key by `PoolId` or clear in the second callback.
9. **The chain needs Cancun or later for TSTORE.** Every v4 deployment does, because the PoolManager requires transient storage. If you also deploy helpers elsewhere, use Solady's `*Compat` functions or the non-transient variants (see `solady-reference` variants).

## Solady vs OpenZeppelin inside one hook

- The OZ hook bases are required: `BaseHook`, the fee bases, and `CurrencySettler`. OZ's own access-control mixins inside `uniswap-hooks` are optional.
- Use Solady for auth, math and guards where gas matters (`beforeSwap` runs on every trade). Use OZ when a reviewer or audit firm requires OZ primitives.
- Don't mix two `Ownable`s in one inheritance tree. OZ `Ownable` and Solady `Ownable` both define `owner()`, `transferOwnership` and `onlyOwner`, so the compiler demands overrides and the two storage layouts coexist confusingly.
- Both libraries compile with solc 0.8.30 in the same project. The remappings are disjoint (`@openzeppelin/contracts/` and `solady/`).
