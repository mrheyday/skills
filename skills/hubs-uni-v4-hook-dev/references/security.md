# Hook Security

Hooks hold or steer user funds and sit on the swap path of every trade in their pools. Start from the official [Hook security framework](https://developers.uniswap.org/docs/protocols/v4/security) (risk-scoring worksheet, audit and monitoring guidance), then apply the hook-specific rules below.

## Contents

- [Threat model](#threat-model)
- [Permission risk matrix](#permission-risk-matrix)
- [Incident classes](#incident-classes)
- [Identity: sender, routers and hookData](#identity-sender-routers-and-hookdata)
- [Delta and settlement bugs](#delta-and-settlement-bugs)
- [Tokens and native ETH](#tokens-and-native-eth)
- [Gas and liveness](#gas-and-liveness)
- [Risk scoring and audit tiers](#risk-scoring-and-audit-tiers)
- [Pre-deployment checklist](#pre-deployment-checklist)
- [Reviewing someone else's hook](#reviewing-someone-elses-hook)

## Threat model

| Actor | Can do | Defence |
|---|---|---|
| Anyone | Initialize **any** pool whose `PoolKey.hooks` is your hook, with any tokens, fee or tick spacing | Validate/bind in `beforeInitialize`; key state by `PoolId` |
| Anyone | Call your hook's external functions directly | OZ `BaseHook` guards the callbacks; guard `unlockCallback` (`onlyPoolManager`) and admin functions yourself |
| Swapper / LP | Choose router, `hookData`, direction, exact-in/out, amounts down to 1 wei | Fuzz all of these; never trust `hookData` without a signature or a trusted router |
| Searcher | Sandwich or JIT around hook-triggered state changes; manipulate in-pool prices that the hook reads | Use previous-block observations; bound per-block movement |
| Hook owner | Change fees, curves, oracles, allowlists; upgrade code | Immutable caps, timelocks, no upgradeability unless audited and disclosed |
| Hook itself (if malicious) | Take input via `beforeSwapReturnDelta`, block exits, quote ≠ settle | Users and aggregators: audit before routing; prefer allowlisted hooks |

## Permission risk matrix

Bit positions are from `Hooks.sol` in v4-core 1.0.2. Some older guides say `beforeSwapReturnDelta` is bit 10: that number is its field index in the `Permissions` struct, not its address bit.

| Permission | Bit | Risk | Why |
|---|---|---|---|
| `beforeInitialize` / `afterInitialize` | 13 / 12 | Low | Pool creation only; use them to validate keys |
| `beforeAddLiquidity` | 11 | Medium | Can block or tax LP entry |
| `afterAddLiquidity` | 10 | Low | Tracking/rewards |
| `beforeRemoveLiquidity` | 9 | **High** | Can trap LP funds by reverting |
| `afterRemoveLiquidity` | 8 | Low | Tracking |
| `beforeSwap` | 7 | **High** | Runs before pricing; can revert, re-price (fee override) or move liquidity |
| `afterSwap` | 6 | Medium | Sees the final state; anything it does moves price for the next trader |
| `beforeDonate` / `afterDonate` | 5 / 4 | Low | Access control, tracking |
| `beforeSwapReturnDelta` | 3 | **Critical** | Hook can claim the entire input and return nothing (NoOp rug) |
| `afterSwapReturnDelta` | 2 | High | Can skim output of every swap |
| `afterAddLiquidityReturnDelta` | 1 | High | Can over-charge LP deposits |
| `afterRemoveLiquidityReturnDelta` | 0 | High | Can skim LP withdrawals |

Legitimate users of the critical and high flags include custom curves, JIT, RFQ/PMM, async/intents, hook fees and JIT penalties. Each one needs fuzzing on every path plus an invariant that bounds the extracted value.

## Incident classes

These are documented patterns from audits and research linked in awesome-uniswap-hooks.

1. **Re-initialization / foreign pools → funds locked.** A hook with one global state (a single price, a single position) is attached to a second pool by an attacker, which corrupts the first pool's accounting or locks withdrawals. Fix: bind in `beforeInitialize` (see `CappedDynamicFeeHook`) or key everything by `PoolId`. [Composable Security write-up](https://composable-security.com/blog/uniswap-v-4-re-initialization-leading-to-funds-locked/).
2. **Liquidity theft via hook fee.** An owner-mutable withdrawal/swap fee (through a return delta or a dynamic fee) is raised to ~100% just before LPs exit. Fix: immutable maximums, timelocked changes, and no fee on `afterRemoveLiquidity` unless disclosed. [Write-up](https://composable-security.com/blog/uniswap-v-4-liquidity-theft-via-hook-fee/).
3. **Oracle hook with malicious owner.** An admin path rewrites observations or swaps the price source, so every integrator reading the oracle is exploitable. Fix: no admin write path to observations; make the source immutable. [Write-up](https://composable-security.com/blog/uniswap-v-4-oracle-hook-with-malicious-owner/).
4. **Quote ≠ settle (aggregator spoofing).** A hook behaves differently when simulated (quoter, `eth_call`, origin checks, gas-based branches, block-dependent state) than when executed, so aggregators route volume into a worse fill. 0x's analysis of 84,163 deployed hooks classified only 19.4% as safe ([thread](https://x.com/0xProject/status/2099578032960995502)). Fix: outcomes must be a deterministic function of the pool state and swap inputs. Never branch on `tx.origin`, `gasleft()` or `msg.sender` codesize.
5. **Risky external interactions.** Hooks calling untrusted tokens, vaults or oracles open reentrancy and DoS paths ([Phalcon: Lethal Integration](https://phalcon.xyz/blog/lethal-integration-vulnerabilities-in-hooks-due-to-risky-interactions), [Thorns in the Rose](https://phalcon.xyz/blog/thorns-in-the-rose-exploring-security-risks-in-uniswap-v4-s-novel-hook-mechanism)). Fix: minimise external calls in callbacks, use transient reentrancy guards, and let exits work when the external dependency fails.
6. **Protocol-level threat model:** Certora's [Protecting Uniswap v4 Against Unknown Attacks](https://www.certora.com/blog/protecting-uniswap-v4-against-unknown-attacks-part-one-a-threat-model) and Composable Security's [threat modeling for secure integration](https://composable-security.com/blog/uniswap-v-4-threat-modeling-for-secure-integration/).

## Identity: sender, routers and hookData

- Inside a callback, `msg.sender` is always the PoolManager. The `sender` argument is whoever called `poolManager.swap/modifyLiquidity`, which is a router or PositionManager, not the user.
- Getting the user: allowlist routers you trust, then read `IMsgSender(sender).msgSender()` (`@uniswap/v4-periphery/src/interfaces/IMsgSender.sol`). v4-periphery's PositionManager and V4Router-based routers implement it. Official guide: [Accessing the original sender](https://developers.uniswap.org/docs/protocols/v4/guides/hooks/accessing-msg.sender).
- `hookData` is attacker-controlled bytes. Treat a user address in it as a claim, not a fact, unless it is signed (EIP-712 with nonce + deadline) or the router is trusted to set it.
- `tx.origin` gating breaks smart-contract wallets and ERC-4337 bundles, and it is spoofable by any relaying contract the user is tricked into calling.

## Delta and settlement bugs

- **Signs.** `amountSpecified < 0` means exact-in. `BalanceDelta` is from the caller's view: negative means the caller pays. `BeforeSwapDelta` and the `int128` returned from `afterSwap` are from the **hook's** view: positive means the hook is owed. Mixing these perspectives is the most common NoOp/fee bug.
- **Specified vs unspecified.** "Specified" is the currency named by `amountSpecified` (input for exact-in, output for exact-out). It is not "currency0".
- **ERC-20 settlement order** is `sync(currency)` → transfer → `settle()`. `settle()` has no argument: it settles whatever currency `sync` recorded, and treats an un-synced call as native ETH. For ETH, call `settle{value: x}()` with no `sync`.
- **Every path must net to zero.** That includes exact-in and exact-out, both directions, zero amounts and partial fills. `unlock` reverts `CurrencyNotSettled` otherwise. A path that passes in tests but leaves a dust delta in production is a liveness bug.
- **Rounding.** Round in the pool's favour: the user pays rounded up and receives rounded down. Solady `FixedPointMathLib` has explicit `*Up` variants.
- **Claims vs tokens.** `take(..., claims=true)` mints ERC-6909 instead of transferring. Your invariant must cover both what the hook owns as claims and what the PoolManager holds.

## Tokens and native ETH

| Token behaviour | Hazard in hooks | Mitigation |
|---|---|---|
| Fee-on-transfer | `settle` credits less than you transferred → `CurrencyNotSettled` | Measure actual deltas; don't support them, or handle explicitly |
| Rebasing | Stored balances drift | Store shares or claims, not raw balances |
| ERC-777 / callback tokens | Reentrancy during transfer | Transient reentrancy guard; settle last |
| Pausable / blocklist (USDC, USDT) | A transfer to or from the hook reverts → swaps or exits brick | Keep exits independent of hook transfers; fork-test real tokens |
| Native ETH (`address(0)`) | No `sync`; `settle{value}`; refunds | Handle `msg.value` exactly; never use `transfer()` for ETH |
| Low decimals | Precision loss in fee math | Scale with `mulDiv`; test 6 and 8 decimals |

## Gas and liveness

| Callback | Target | Ceiling |
|---|---|---|
| `beforeSwap` | < 50k | 150k |
| `afterSwap` | < 30k | 100k |
| liquidity callbacks | < 50k | 200k |
| callbacks with external calls | < 100k | 300k |

- Have no unbounded loops over orders, positions or ticks. Cap the work per call and leave the remainder for a keeper.
- Use transient storage (`LibTransient`, transient guards) for data that dies with the transaction. A new SSTORE slot costs about 20k.
- A reverting hook bricks its pool. Decide whether a failure should revert the swap or degrade gracefully (skip the order fill, keep the old fee).
- Measure with `forge snapshot` and `forge test --gas-report`. Treat a gas regression in `beforeSwap` as a bug.

## Risk scoring and audit tiers

Score each dimension and sum (0–34):

| Dimension | Points |
|---|---|
| Permissions (sum over the matrix: low 0, medium 1, high 2, critical 3; all 14 enabled = 2×1 + 5×2 + 1×3) | 0–15 |
| External calls (count/trust) | 0–5 |
| State complexity | 0–5 |
| Upgradeability / admin power | 0–5 |
| Non-standard token support | 0–4 |

| Score | Tier | Minimum |
|---|---|---|
| 0–5 | Low | Self-review, peer review, full test matrix |
| 6–12 | Medium | Professional audit recommended |
| 13–20 | High | Professional audit required, plus a bug bounty |
| 21–34 | Critical | Multiple audits, formal verification of the delta invariants, monitoring |

## Pre-deployment checklist

- [ ] Every enabled flag is needed. Each `*ReturnDelta` has a written justification and an invariant.
- [ ] Callbacks are PoolManager-only; `unlockCallback` and admin functions are guarded.
- [ ] Unknown pools are rejected, or all state is keyed by `PoolId`.
- [ ] Identity comes from allowlisted routers, `msgSender()` or signed `hookData`, never `msg.sender` or `tx.origin`.
- [ ] Deltas net to zero on every path. Fuzz covers ±`amountSpecified` × both directions × edge amounts.
- [ ] Admin powers are bounded (immutable caps, timelocks); upgradeability is absent or disclosed and audited.
- [ ] LP exits can't be blocked by the owner, the hook's own failures, or an external dependency.
- [ ] Quote equals settle: no branches on `tx.origin`, `gasleft`, codesize or simulation context.
- [ ] Gas is within budget; there are no unbounded loops.
- [ ] Fork tests pass on the target chain against real tokens; Slither is clean or triaged.
- [ ] An audit tier matching the risk score is complete; monitoring and alerting is in place for production.

## Reviewing someone else's hook

Before routing funds through an unknown hook:

1. Decode its permissions from the address. The last 14 bits are the flags; see `testing-and-deployment.md`. Any `*ReturnDelta` flag calls for a full code review.
2. Check whether the source is verified, whether it is upgradeable (proxy pattern, `delegatecall`, `selfdestruct` + CREATE2 redeploy), and who the owner is (EOA vs timelock vs none).
3. Check whether it is on the Uniswap routing [allowlist](https://github.com/Uniswap/routing-api/blob/main/lib/util/hooksAddressesAllowlist.ts) and whether it has published audits.
4. Simulate the exact trade and compare against a direct `eth_call` from a different origin. Divergence is a red flag.
5. Start with small size.

The `v4-security-foundations` skill has a longer vulnerability catalog. Where it disagrees with this file on flag bits or the `settle` signature, this file matches v4-core 1.0.2.
