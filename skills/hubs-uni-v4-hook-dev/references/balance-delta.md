# BalanceDelta and Flash Accounting

`BalanceDelta` is the value every PoolManager action hands back, and most hook bugs come down to misreading it. Everything here comes from v4-core 1.0.2 (`src/types/BalanceDelta.sol`, `src/PoolManager.sol`, `src/libraries/Hooks.sol`). The code blocks come from a passing Forge suite. Official companion guides: [Unlock callback and deltas](https://developers.uniswap.org/docs/protocols/v4/guides/unlock-callback-and-deltas) and [Custom accounting](https://developers.uniswap.org/docs/protocols/v4/guides/custom-accounting).

## Contents

- [The type](#the-type)
- [Whose perspective: the sign rule](#whose-perspective-the-sign-rule)
- [What each action returns](#what-each-action-returns)
- [How hook deltas combine with the caller's](#how-hook-deltas-combine-with-the-callers)
- [From BalanceDelta to settlement](#from-balancedelta-to-settlement)
- [Verified example: settle a swap's BalanceDelta](#verified-example-settle-a-swaps-balancedelta)
- [Modifying liquidity: the official guide, corrected](#modifying-liquidity-the-official-guide-corrected)
- [Pitfalls](#pitfalls)

## The type

`type BalanceDelta is int256` packs two `int128`s: **`amount0` in the upper 128 bits, `amount1` in the lower 128 bits**.

| Operation | Behaviour |
|---|---|
| `toBalanceDelta(int128 a0, int128 a1)` | Free function; `or(shl(128, a0), and((1<<128)-1, a1))` |
| `d.amount0()` | `sar(128, d)`: arithmetic shift, so the sign is preserved |
| `d.amount1()` | `signextend(15, d)`: the low 16 bytes, sign-extended |
| `a + b`, `a - b` | Component-wise in 256-bit, then `SafeCast.toInt128` on each, so it **reverts `SafeCastOverflow`** if a component leaves the int128 range |
| `a == b`, `a != b` | Raw `int256` comparison |
| `BalanceDeltaLibrary.ZERO_DELTA` | `BalanceDelta.wrap(0)` |

Imports: `import {BalanceDelta, BalanceDeltaLibrary, toBalanceDelta} from "@uniswap/v4-core/src/types/BalanceDelta.sol";`. The operators and `amount0`/`amount1` are attached `global`ly, so no `using` is needed.

```solidity
function test_PackingAndAccessors() public pure {
    BalanceDelta d = toBalanceDelta(-5, 7);
    assertEq(d.amount0(), -5); // upper 128 bits, arithmetic shift keeps the sign
    assertEq(d.amount1(), 7); // lower 128 bits, sign-extended
    assertEq(BalanceDelta.unwrap(d) >> 128, -5);
    assertTrue(d - toBalanceDelta(-5, 7) == BalanceDeltaLibrary.ZERO_DELTA);
}

function addExternal(BalanceDelta a, BalanceDelta b) external pure returns (BalanceDelta) {
    return a + b;
}

function test_RevertWhen_AddOverflowsInt128() public {
    BalanceDelta max0 = toBalanceDelta(type(int128).max, 0);
    vm.expectRevert(SafeCast.SafeCastOverflow.selector);
    this.addExternal(max0, toBalanceDelta(1, 0));
}
```

Never cast `BalanceDelta.unwrap(d)` to `uint256`, or slice it by hand with `int128(int256(...))`. Truncation keeps the low half, which is `amount1`, not `amount0`. Use the accessors.

## Whose perspective: the sign rule

A `BalanceDelta` is always written **from the point of view of the address it is booked to**:

| Sign | Meaning for that address |
|---|---|
| negative | it **owes** the PoolManager (must `settle` / `burn`) |
| positive | it is **owed** by the PoolManager (may `take` / `mint`) |

For the caller of `swap`/`modifyLiquidity`/`donate`, that is the caller (router, PositionManager, your contract). For `hookDelta`, it is the hook. The same rule applies to the `int128` an `afterSwap` hook returns and to `BeforeSwapDelta`: positive means the hook is owed.

## What each action returns

| Call | Returns | Notes |
|---|---|---|
| `swap(key, params, hookData)` | `swapDelta` | Already net of hook deltas (`swapDelta = ammDelta - hookDelta`). This is exactly what the caller must settle. |
| `modifyLiquidity(key, params, hookData)` | `(callerDelta, feesAccrued)` | `callerDelta = principalDelta + feesAccrued - hookDelta`. `feesAccrued` is **informational**: fees are already folded into `callerDelta`. Any modification of a position collects its fees, including `liquidityDelta = 0` on a non-empty position (an empty one reverts `CannotUpdateEmptyPosition`). |
| `donate(key, amount0, amount1, hookData)` | `delta` | Negative in both currencies: the donor owes what it donated. |

Swap signs by mode. "In" is the input currency (currency0 when `zeroForOne`):

| Mode | `amountSpecified` | Input currency delta | Output currency delta |
|---|---|---|---|
| exact-in | negative (`-amountIn`) | `== amountSpecified` (unless a hook changes it) | positive, the computed output |
| exact-out | positive (`+amountOut`) | negative, the computed input | `== amountSpecified` |

Liquidity: adding liquidity gives negative principal (you deposit). Removing gives positive principal (you withdraw). Fees are always ≥ 0 and are added on top.

## How hook deltas combine with the caller's

From `Hooks.beforeSwap` / `Hooks.afterSwap` / `Hooks.afterModifyLiquidity`:

1. **`beforeSwap` → `BeforeSwapDelta(specified, unspecified)`.** This is a *different* type: it is keyed by **specified/unspecified**, not by currency0/1. The **specified** currency is the one named by `amountSpecified` (the input for exact-in, the output for exact-out).
   - The PoolManager runs the AMM on `amountToSwap = amountSpecified + specified`. If the hook's delta would flip exact-in into exact-out (or the reverse), it reverts `HookDeltaExceedsSwapAmount`.
   - A NoOp hook returns `specified = -amountSpecified`, so `amountToSwap = 0`.
2. **`afterSwap`** receives the **AMM delta before any hook adjustment** and may return an `int128` that is added to the **unspecified** delta (requires `AFTER_SWAP_RETURNS_DELTA`).
3. The PoolManager maps (specified, unspecified) onto (amount0, amount1). If `(amountSpecified < 0) == zeroForOne`, specified is currency0; otherwise specified is currency1. That gives `hookDelta`.
4. `swapDelta = ammDelta - hookDelta`. `hookDelta` is booked to the hook and `swapDelta` to the caller. What the hook is owed, the caller pays, and the reverse.
5. Liquidity follows the same shape. `afterAddLiquidity`/`afterRemoveLiquidity` receive `(delta = callerDelta incl. fees, feesAccrued)` and may return a `BalanceDelta` (with the `*_RETURNS_DELTA` flag), then `callerDelta = callerDelta - hookDelta`.

A hook that returns a non-zero delta has created a debt or credit for **itself**, and must clear it inside the same callback: `take`/`mint` what it is owed, `settle`/`burn` what it owes. Otherwise the outer `unlock` reverts `CurrencyNotSettled`. `ConstantSumHook` (`hook-archetypes.md`) and `SkimFeeHook` (`solady-composition.md`) show both sides.

When the hook itself is the caller, none of this runs. `Hooks.*` returns early when `msg.sender == address(hook)`, so a hook's own swaps book only the AMM delta.

## From BalanceDelta to settlement

`_accountPoolBalanceDelta` splits a `BalanceDelta` into two **currency deltas**, keyed by `(target, currency)` in transient storage:

- Each currency delta that goes from 0 to non-zero increments `NonzeroDeltaCount`, and returning to 0 decrements it.
- `unlock` reverts `CurrencyNotSettled()` if `NonzeroDeltaCount != 0` when your callback returns.

| To move a currency delta | Call | Effect on your currency delta |
|---|---|---|
| Pay ERC-20 in | `sync(c)`, transfer to the PoolManager, then `settle()` | `+paid` |
| Pay native ETH | `settle{value: x}()` (no `sync`) | `+x` |
| Pay for someone else | `settleFor(recipient)` | credits `recipient` |
| Withdraw tokens | `take(c, to, amount)` | `-amount` |
| Hold as ERC-6909 claims | `mint(to, c.toId(), amount)` / `burn(from, c.toId(), amount)` | `-amount` / `+amount` |
| Forfeit dust you are owed | `clear(c, amount)` | must equal your exact positive delta, else `MustClearExactPositiveDelta` |

Reading deltas mid-callback: `TransientStateLibrary.currencyDelta(manager, target, currency)` returns the live `int256` (via `exttload`). `getNonzeroDeltaCount(manager)` tells you what is still open.

## Verified example: settle a swap's BalanceDelta

A minimal router. It swaps inside `unlock`, then settles each component of the returned `BalanceDelta` by sign. OZ `CurrencySettler` does `sync` → `transferFrom(payer)` → `settle` for debts and `take` for credits.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {IPoolManager, SwapParams} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import {IUnlockCallback} from "@uniswap/v4-core/src/interfaces/callback/IUnlockCallback.sol";
import {PoolKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import {Currency} from "@uniswap/v4-core/src/types/Currency.sol";
import {BalanceDelta} from "@uniswap/v4-core/src/types/BalanceDelta.sol";
import {TickMath} from "@uniswap/v4-core/src/libraries/TickMath.sol";
import {CurrencySettler} from "@openzeppelin/uniswap-hooks/src/utils/CurrencySettler.sol";

/// @notice Minimal router: swap inside unlock, then settle the returned BalanceDelta per currency.
contract DeltaSwapper is IUnlockCallback {
    using CurrencySettler for Currency;

    error NotPoolManager();

    IPoolManager public immutable poolManager;

    constructor(IPoolManager _poolManager) {
        poolManager = _poolManager;
    }

    /// @param amountSpecified negative = exact input, positive = exact output
    function swap(PoolKey calldata key, bool zeroForOne, int256 amountSpecified) external returns (BalanceDelta delta) {
        bytes memory result = poolManager.unlock(abi.encode(msg.sender, key, zeroForOne, amountSpecified));
        delta = abi.decode(result, (BalanceDelta));
    }

    function unlockCallback(bytes calldata data) external returns (bytes memory) {
        if (msg.sender != address(poolManager)) revert NotPoolManager();
        (address payer, PoolKey memory key, bool zeroForOne, int256 amountSpecified) =
            abi.decode(data, (address, PoolKey, bool, int256));

        BalanceDelta delta = poolManager.swap(
            key,
            SwapParams({
                zeroForOne: zeroForOne,
                amountSpecified: amountSpecified,
                sqrtPriceLimitX96: zeroForOne ? TickMath.MIN_SQRT_PRICE + 1 : TickMath.MAX_SQRT_PRICE - 1
            }),
            ""
        );

        // Caller's perspective: negative = we owe the pool, positive = the pool owes us.
        _settleOrTake(key.currency0, delta.amount0(), payer);
        _settleOrTake(key.currency1, delta.amount1(), payer);
        return abi.encode(delta);
    }

    function _settleOrTake(Currency currency, int128 amount, address payer) internal {
        if (amount < 0) {
            currency.settle(poolManager, payer, uint256(-int256(amount)), false); // sync + transferFrom + settle
        } else if (amount > 0) {
            currency.take(poolManager, payer, uint256(int256(amount)), false);
        }
    }
}
```

The property worth testing in any router or hook: **the settled delta equals the caller's real balance change**, for both directions and both modes.

```solidity
function testFuzz_DeltaMatchesBalances(uint256 amount, bool zeroForOne, bool exactIn) public {
    amount = bound(amount, 1e6, 10e18);
    uint256 b0 = currency0.balanceOf(address(this));
    uint256 b1 = currency1.balanceOf(address(this));
    BalanceDelta d = swapper.swap(poolKey, zeroForOne, exactIn ? -int256(amount) : int256(amount));
    // The settled delta is exactly the caller's balance change, per currency.
    assertEq(int256(currency0.balanceOf(address(this))) - int256(b0), int256(d.amount0()));
    assertEq(int256(currency1.balanceOf(address(this))) - int256(b1), int256(d.amount1()));
}
```

This router is a teaching example: it has no slippage limit (`MIN/MAX_SQRT_PRICE ± 1`), no deadline and no native-ETH path. Production code must check the output against a user minimum, because the delta alone doesn't protect against price impact.

## Modifying liquidity: the official guide, corrected

The official [Unlock callback and deltas](https://developers.uniswap.org/docs/protocols/v4/guides/unlock-callback-and-deltas) guide splits PoolManager calls into two groups:

| Group | Operations | Effect on deltas |
|---|---|---|
| Liquidity-accessing | `modifyLiquidity`, `swap`, `donate` | create deltas and move pool state |
| Delta-resolving | `sync`, `settle`, `take`, `mint`, `burn`, `clear` | move deltas toward zero (`take` can also be a free flash loan: a negative delta you repay before `unlock` returns) |

That makes 9 operations. The guide names 8; `sync` is the ninth.

It recommends inheriting v4-periphery's `SafeCallback` (`@uniswap/v4-periphery/src/base/SafeCallback.sol`). That puts `onlyPoolManager` on `unlockCallback` and forwards to your `internal _unlockCallback`.

Two rules from the guide that every router and hook needs:
- **`LiquidityAmounts.getAmountsForLiquidity()` is an estimate, not the delta.** The real amounts come from `modifyLiquidity` at execution time: a different price, tick crossings, Q128 rounding. Underestimating leaves `CurrencyNotSettled`, overestimating leaves dust, and both need a slippage check.
- **Check slippage on the actual delta, after execution,** then settle from that delta.

The guide's own settle snippet has two bugs; don't copy it:
- It calls `settle` for **both** signs using the absolute value. A positive delta (from removing liquidity) must be resolved with `take`, otherwise you pay instead of being paid.
- It passes `_data.key.hookAddress`, but `PoolKey` has no such field (the fields are `currency0, currency1, fee, tickSpacing, hooks`), and the payer should be the user anyway.

Corrected and verified:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.26;

import {SafeCallback} from "@uniswap/v4-periphery/src/base/SafeCallback.sol";
import {IPoolManager, ModifyLiquidityParams} from "@uniswap/v4-core/src/interfaces/IPoolManager.sol";
import {PoolKey} from "@uniswap/v4-core/src/types/PoolKey.sol";
import {Currency} from "@uniswap/v4-core/src/types/Currency.sol";
import {BalanceDelta} from "@uniswap/v4-core/src/types/BalanceDelta.sol";
import {CurrencySettler} from "@openzeppelin/uniswap-hooks/src/utils/CurrencySettler.sol";

/// @notice Modify liquidity, enforce slippage on the ACTUAL delta, then settle each currency by sign.
contract DeltaLiquidity is SafeCallback {
    using CurrencySettler for Currency;

    error SlippageExceeded(int128 amount, int256 limit);

    struct CallbackData {
        address user;
        PoolKey key;
        ModifyLiquidityParams params;
        int256 limit0; // minimum signed delta accepted for currency0
        int256 limit1;
    }

    constructor(IPoolManager _poolManager) SafeCallback(_poolManager) {}

    /// @param limit0 For adds, -maxAmount0In; for removes, +minAmount0Out.
    function modify(PoolKey calldata key, ModifyLiquidityParams calldata params, int256 limit0, int256 limit1)
        external
        returns (BalanceDelta delta)
    {
        bytes memory result = poolManager.unlock(abi.encode(CallbackData(msg.sender, key, params, limit0, limit1)));
        delta = abi.decode(result, (BalanceDelta));
    }

    function _unlockCallback(bytes calldata raw) internal override returns (bytes memory) {
        CallbackData memory data = abi.decode(raw, (CallbackData));
        (BalanceDelta delta,) = poolManager.modifyLiquidity(data.key, data.params, "");

        // Slippage is checked on what the pool actually computed, not on LiquidityAmounts estimates.
        if (delta.amount0() < data.limit0) revert SlippageExceeded(delta.amount0(), data.limit0);
        if (delta.amount1() < data.limit1) revert SlippageExceeded(delta.amount1(), data.limit1);

        _resolve(data.key.currency0, delta.amount0(), data.user);
        _resolve(data.key.currency1, delta.amount1(), data.user);
        return abi.encode(delta);
    }

    function _resolve(Currency currency, int128 amount, address user) internal {
        if (amount < 0) currency.settle(poolManager, user, uint256(uint128(-amount)), false); // owe: pay in
        else if (amount > 0) currency.take(poolManager, user, uint256(uint128(amount)), false); // owed: pay out
    }
}
```

The test, using the real `LiquidityAmounts` estimate as the slippage bound:

```solidity
function test_AddThenRemove() public {
    (uint256 est0, uint256 est1) = LiquidityAmounts.getAmountsForLiquidity(
        Constants.SQRT_PRICE_1_1, TickMath.getSqrtPriceAtTick(lower), TickMath.getSqrtPriceAtTick(upper), 1e18
    );
    // Add: we owe the pool -> negative deltas, bounded by the estimate plus 1 wei of rounding.
    BalanceDelta added = router.modify(poolKey, _params(1e18), -int256(est0 + 1), -int256(est1 + 1));
    assertLt(added.amount0(), 0);
    assertLt(added.amount1(), 0);

    // Remove: the pool owes us -> positive deltas, at least the estimate minus 1 wei.
    BalanceDelta removed = router.modify(poolKey, _params(-1e18), int256(est0) - 1, int256(est1) - 1);
    assertGt(removed.amount0(), 0);
    assertGt(removed.amount1(), 0);
    // Rounding always favours the pool: you get back at most what you put in.
    assertLe(removed.amount0(), -added.amount0());
}
```

Signed limits keep a single check correct for both directions: adding passes `-maxIn` (the delta must not be more negative), removing passes `+minOut`. The delta must reach the limit or the call reverts with `SlippageExceeded`. `unlock` doesn't wrap callback reverts, so `vm.expectPartialRevert(DeltaLiquidity.SlippageExceeded.selector)` catches it directly. Hook reverts, by contrast, arrive wrapped.

What a liquidity hook sees: `afterAddLiquidity`/`afterRemoveLiquidity` receive `delta` = principal + fees **before** the hook's own returned delta is subtracted (`Hooks.afterModifyLiquidity`: `callerDelta = callerDelta - hookDelta` after the call). `feesAccrued` has been passed to these hooks since [v4-core PR #853](https://github.com/Uniswap/v4-core/pull/853).

## Pitfalls

| Bug | Symptom | Fix |
|---|---|---|
| Reading `amount0` as "input" | Wrong token paid in `zeroForOne = false` swaps | Pick the currency by `zeroForOne`, or settle both components by sign as above |
| Mixing perspectives (caller vs hook) | A hook fee charged to the LPs, or double-charged | Hook return values are from the **hook's** view (positive = hook owed); `swapDelta` is from the **caller's** |
| Specified ≠ currency0 | NoOp/fee hooks broken for exact-out or `oneForZero` | Map with `(amountSpecified < 0) == zeroForOne` → specified is currency0 |
| Forgetting the hook's own delta | `CurrencyNotSettled` on every swap | `take`/`mint` or `settle`/`burn` inside the same callback |
| `uint256(int256(x))` on a negative component | Huge transfer and revert, or underflow | Branch on the sign; negate before casting (`uint256(-int256(amount))`) |
| Using `feesAccrued` as extra credit | Paying LP fees twice | `callerDelta` already includes the fees |
| ERC-20 `settle` without `sync` (or `sync` too early) | Credits the wrong amount, or a previous currency | `sync(c)` immediately before the transfer, then `settle()`; `CurrencySettler` does this |
| Fee-on-transfer tokens | `settle` credits less than intended, leaving a residual debt | Measure what `settle()` returns; unsupported by default |
| Exact-in shortfall | Partial fill at `sqrtPriceLimitX96`: the input delta is smaller than `amountSpecified` | Never assume `delta.amount0() == amountSpecified`; read the delta |
| Porting pre-March-2024 hook code | Every sign is inverted: before [v4-core PR #481](https://github.com/Uniswap/v4-core/pull/481) (merged 2024-03-13), positive meant "owed to the PoolManager" | Re-derive signs for any code older than that (several awesome-list hooks, e.g. v4-stoploss) |
| Settling `LiquidityAmounts` estimates | `CurrencyNotSettled` or dust left behind | Settle the delta `modifyLiquidity` returned; slippage-check that delta |
| `settle` on a positive delta (the guide's snippet) | Pays instead of receiving; the debt grows | `take` positives, `settle` negatives |
| Overflow in delta math | `SafeCastOverflow` revert inside the hook | Bound amounts to int128, and use `SafeCastLib.toInt128` before building deltas |
