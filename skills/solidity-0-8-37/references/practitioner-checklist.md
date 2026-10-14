# Practitioner Checklist (NOT from the 0.8.37 docs bundle)

Hands-on pitfalls that the official docs only touch indirectly or not at all. Where an item has a docs
anchor it is cited; where it does not, treat it as practitioner guidance to verify, not as a docs rule.
§7–§8 and the gas additions in §2 are condensed and corrected from `tenequm/foundry-solidity` v0.2.5 (Apache-2.0, modified; see
`foundry-tooling.md` for the full credit line).
**If this file and a verbatim reference disagree, the verbatim reference wins.** Gas figures are EVM
schedule facts, chain-dependent (L2s such as Arbitrum add their own cost model) — measure with
`forge snapshot` / `forge test --gas-report` on the target chain's fork instead of trusting a number here.

## Contents
1. Integer maths and rounding
2. Gas habits
3. Ether accounting
4. Reentrancy tooling
5. Upgradeable contracts and proxies
6. Strings and small traps
7. Integration and audit-level pitfalls (oracles, tokens, signatures, access control)
8. Pre-audit checklist

## 1. Integer maths and rounding
- Division truncates toward zero (`5 / 2 == 2`, `-5 / 2 == -2`); there are no decimals (types.md §3.6).
- Multiply before dividing (`a * b / c`, not `a / c * b`) to keep precision, and decide the rounding
  direction on purpose: round **against** the caller in value-moving code (shares minted down, assets owed
  up). `mulDiv`-style helpers (Solady `FixedPointMathLib`, OZ `Math.mulDiv`) avoid the 256-bit intermediate
  overflow of `a * b`.
- `unchecked` removes the overflow revert for that block only (quick-rules §3). Narrowing casts
  (`uint128(x)`) truncate silently even in 0.8+; use a checked cast helper (SafeCast / Solady `SafeCastLib`).
- Use `type(uint256).max` / `type(T).min` rather than hardcoded large literals (units-and-globals.md §3.7).

## 2. Gas habits
- Storage is the expensive resource: a zero→non-zero `SSTORE` is ~20k gas (plus cold-slot access) while
  memory/calldata are a few gas per word. Prefer `calldata` for external read-only reference params.
- Cache a storage variable in a local before a loop and write back once; every `SLOAD` in the loop body is
  paid per iteration. Cache `array.length` too.
- Clearing storage (`delete`, writing zero) earns a refund, but the refund is capped per transaction since
  London (EIP-3529) — never design around it.
- Loops over user-growable arrays need a cap or pagination (quick-rules §10; security-considerations.md
  "Gas Limit and Loops").
- Packing: value types smaller than 32 bytes share a slot only when adjacent in declaration order (struct and array
  elements start a new slot) — reorder fields, then confirm with `forge inspect <C> storageLayout`. Never reorder
  an already-deployed layout (§5). Packing saves SSTOREs only if the packed fields are written together.
- `constant` is inlined at compile time and `immutable` is inlined in the deployed bytecode: no `SLOAD` for either.
- Data that only off-chain readers need (history, receipts) belongs in events, not storage; contracts cannot read logs.
- Raising `optimizer_runs` trades larger bytecode for cheaper runtime. Where the size limit binds (the Diamond
  facets), re-run `forge build --sizes` after any change to `optimizer_runs` or `via_ir`.
- Recent compilers elide the overflow check on simple bounded `for` counters; confirm with `forge snapshot` before
  hand-writing `unchecked { ++i; }`, and never use `unchecked` on value arithmetic to save gas.
- `this.f()` turns an internal call into an external message call — costly, and it changes `msg.sender`.
  `external` functions cannot be called internally; use `public` or an `internal` helper that both call.

## 3. Ether accounting
- A contract cannot refuse all Ether: it can be force-fed via `selfdestruct(x)` or by being the coinbase /
  pre-funded address (security-considerations.md "Sending and Receiving Ether"). Never base invariants on
  `address(this).balance == expected` — track deposits in your own storage variable.
- A `receive`/`fallback` that works only under the 2300 gas stipend is fragile; `call{value: x}("")` forwards
  all gas, so apply CEI and check the returned `bool` (quick-rules §3, §5).
- `payable` is required to accept Ether; a non-payable function reverts on `msg.value > 0`.

## 4. Reentrancy tooling
- CEI is the primary defence (quick-rules §10). Add a guard where a function both moves value and calls out:
  the docs show a hand-rolled `nonReentrant` modifier (contracts-core.md §3.9.4); in practice use a vetted
  one (OZ `ReentrancyGuard` / `ReentrancyGuardTransient`, Solady `ReentrancyGuard`) and check the exact
  pinned version in the repo.
- A transient-storage guard (`transient` flag) is cheap but persists for the whole transaction, so it also
  blocks legitimate re-entry from the same transaction's other calls — reason about composability
  (quick-rules §6).
- A guard does not cover read-only reentrancy: a `view` function read mid-update by another protocol can
  return a stale value. Finish state updates before any external call.

## 5. Upgradeable contracts and proxies
- Constructors do not run in the proxy's context: use an `initialize()` guarded by an `initializer`-style
  modifier, and lock the implementation (OZ `_disableInitializers()` in its constructor).
  `immutable` values live in implementation bytecode, so they are shared by every proxy — not per-proxy state.
- `delegatecall` runs implementation code against the **proxy's** storage: the implementation's layout must
  match the proxy's. Never reorder, retype or remove existing storage variables across versions; append only,
  or use namespaced storage (`layout at` / `erc7201()` — contracts-core.md, units-and-globals.md; ERC-7201,
  ERC-1967 in eip-register.md) so the proxy's admin/implementation slots cannot collide with logic state.
- Changing storage layout needs a migration plan and a layout diff in CI (`forge inspect <C> storageLayout`).
- `selfdestruct` in an implementation: since Cancun (EIP-6780) it no longer removes code unless called in the
  creating transaction (evm-basics.md §3.1.3), but it is deprecated and must not appear in new code
  regardless; guard `delegatecall` targets so user input can never select one.
- Internal function-pointer variables are unsafe across upgrades (security-considerations.md "Internal
  Function Pointers in Upgradeable Contracts").

## 6. Strings and small traps
- `==` is not defined on `string`/`bytes`. Compare with `keccak256(bytes(a)) == keccak256(bytes(b))`
  (or `bytes.concat`/length-then-hash). Avoid `abi.encodePacked` for this unless exactly one dynamic arg
  (quick-rules §4).
- `block.timestamp` is validator-adjustable within chain limits: fine for coarse deadlines, never for
  randomness or tight ordering. On L2s it can be set by the sequencer; verify per chain.
- `private` does not hide data: every storage slot is readable off-chain (quick-rules §6, §10).
- State variables default to `internal`, so derived contracts see them — make intent explicit.
- Index up to three event params you will filter on (contracts-core.md events).

## 7. Integration and audit-level pitfalls
- **Oracles.** A spot price read from a pool is flash-loan-manipulable within one transaction; use a TWAP or a
  push oracle, and size the manipulation cost against the value at risk. For Chainlink-style feeds check
  `answer > 0`, `updatedAt` against the feed's documented heartbeat (not an invented constant), and — on L2s such as
  Arbitrum — the sequencer-uptime feed plus a grace period after it comes back. `answeredInRound` is deprecated in
  Chainlink's docs; do not rely on it.
- **Token quirks.** Some tokens return no value from `transfer`/`approve` (USDT-style): `require(token.transfer(..))`
  reverts on them, so use `SafeERC20` / Solady `SafeTransferLib`. Fee-on-transfer and rebasing tokens break
  `amount in == amount credited`: credit the measured balance delta, or reject such tokens explicitly. Allowance
  race and zero-approve-first tokens need `forceApprove`-style helpers.
- **Signatures.** Bind every signed message to its purpose: EIP-712 domain (chainId + verifyingContract), a per-signer
  nonce or unique id, and a deadline. Use a library `ECDSA.recover` (rejects malleable high-`s` and zero address)
  instead of raw `ecrecover`; for contract wallets use ERC-1271. A `permit` can be front-run, so wrap it in
  `try/catch` and fall back to the existing allowance.
- **Access control.** Prefer a two-step ownership transfer (`Ownable2Step`-style: propose, then accept), a role
  per privilege, and a timelock on parameter changes that move funds. Single-owner `transferOwnership(newOwner)`
  to a wrong address is unrecoverable.
- **Push vs pull.** Paying many recipients in a loop lets one reverting recipient block everyone. Record
  `pendingWithdrawals[account]` and let each account pull (quick-rules §10; Check-Effects-Interactions).
- **Ordering and MEV.** Anything revealed in a pending transaction can be copied or reordered on chains with a public
  mempool; on Arbitrum ordering is set by the sequencer, and its rules have changed over time — confirm the current
  model in Arbitrum's docs before reasoning about front-running. Commit–reveal, slippage bounds and deadlines
  are still required in contract code regardless of the chain's ordering rules.
- **Symbolic checks.** `halmos` proves properties written as `check_*` tests over all inputs within bounds (for example
  "transfer preserves total supply"); use it alongside fuzz/invariant tests for small, arithmetic-heavy functions.
  A passing run under loop/size bounds is evidence, not a proof beyond those bounds.

## 8. Pre-audit checklist
- NatSpec on every external function; no `console.log` or debug code; no open TODO/FIXME.
- CEI everywhere value moves; guards only where a call-out and a state change coexist; no `tx.origin` auth.
- Every privileged function has an explicit access check and a test that an unauthorised caller reverts.
- Token transfers go through safe-transfer helpers; balance-delta accounting where fee-on-transfer is possible.
- Unit, fuzz (`bound` every input) and invariant tests for solvency/accounting; fork tests pinned to a block.
- Static analysis (Slither or equivalent) clean at HIGH/MEDIUM, with every suppression justified in a comment.
- Storage-layout diff checked in CI for upgradeable code; `forge build --sizes` within limits.
- Written threat model: assumptions about oracles, admins, tokens and sequencer behaviour; known limitations listed.
