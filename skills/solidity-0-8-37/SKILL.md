---
name: solidity-0-8-37
description: Canonical Solidity 0.8.37 rules, style guide and NatSpec from the bundled official docs, with a static checker and compile gate. Use for any .sol file, Foundry test or script, EVM, storage, assembly or ABI question, or a Solidity review or audit.
metadata:
  version: "0.1.0"
  categories: "development, security"
  topics: "solidity, foundry, smart-contracts, evm, security-audit"
  upstream: "solc@0.8.37, foundry@1.8.3"
  openclaw:
    homepage: https://github.com/tenequm/skills/tree/main/skills/solidity-0-8-37
    emoji: "📜"
    requires:
      anyBins:
        - solc
        - forge
    install:
      - kind: brew
        formula: foundry
        bins:
          - forge
          - cast
          - anvil
---

# Solidity 0.8.37 — Canonical Language Rules

This skill makes Solidity output conform to the actual 0.8.37 language rules rather than to habits
learned from older code. Three things make that work: the official docs are bundled verbatim under
`references/` so a rule can be looked up instead of guessed; `references/quick-rules.md` distils the rules
that apply to nearly every file; and two scripts gate the result (a style/NatSpec/deprecation checker and a
real compile). The docs snapshot is release `0.8.37-develop` (Sep 10, 2026). Where the snapshot and a live
compiler disagree, the compiler wins — say so rather than papering over it.

Why this matters: 0.8.37 is not "0.8.x". `transfer`/`send`, `selfdestruct`, `virtual` modifiers, constructor
visibility, `abicoder v1` and the `memory-safe-assembly` comment are all deprecated; `osaka` is the default
EVM target; `require(cond, CustomError())`, `transient` state variables, `layout at`, `erc7201()`,
`block.slotnum` and `clz` exist. Code written from memory of 0.8.20 compiles with warnings or not at all,
and a warning is a defect, not noise.

## Workflow

### 1. Establish the target before writing a line

- Read `foundry.toml` / `hardhat.config.*` / `remappings.txt` if present: `solc` version, `evm_version`,
  `via_ir`, optimizer, remappings. If none exist, assume `0.8.37`, `osaka`, `via_ir = true` and say so.
- Decide the profile. Generic rules always apply. Additionally apply `references/repo-profile.md` when the
  repository's own contract files (`CLAUDE.md`, `AGENTS.md`, guardrails) call for exact pins, named custom
  errors only, Solady/forge-std pins, or when the user asks for the production/repo
  profile. `@uniswap/v4-core` is allowed. The profile tightens; it never relaxes a docs rule.
- Read `references/quick-rules.md` in full. It is short and it is the rule set you will be checked against.

### 2. Consult the verbatim reference for anything non-trivial

Open the relevant file whenever the construct is version-sensitive, you are about to rely on a detail
(packing, selector, conversion rule, panic code, override rule), or the quick rules are not specific enough.
Each file starts with a table of contents keyed by the docs' section numbers, so jump by heading.

| You are working on… | Open |
|---|---|
| File header, pragmas, imports, SPDX, contract skeleton | `source-layout-and-contract-structure.md` |
| Integer/bytes/address/enum/UDVT/function types, data locations, arrays, mappings, structs, conversions, operators | `types.md` |
| `block.*`, `msg.*`, `abi.*`, `keccak256`, `ecrecover`, `erc7201`, `type(X)`, units, reserved words | `units-and-globals.md` |
| `require`/`revert`/`assert`, custom errors, `try/catch`, `unchecked`, `new`, calls with `{value, gas}`, scoping | `expressions-control-structures-and-errors.md` |
| Visibility, getters, modifiers, `receive`/`fallback`, `constant`/`immutable`, `transient`, `layout at`, functions, events | `contracts-core.md` |
| Inheritance, `virtual`/`override`, abstract, interfaces, libraries, `using for`, operators on UDVTs | `contracts-inheritance-interfaces-libraries.md` |
| `assembly { }`, memory-safe rules, Yul grammar, opcode availability by EVM version | `inline-assembly-and-yul.md` |
| Operator precedence, member cheat lists, the formal grammar | `cheatsheet-and-grammar.md` |
| `solc` flags, EVM version list, standard JSON, experimental mode, import resolution/remappings | `compiler-evm-versions-and-imports.md` |
| Behaviour differences under `via_ir`, optimizer steps | `ir-codegen-and-optimizer.md` |
| Storage/transient slot packing, mapping/array slots, memory layout, calldata, dirty bits | `data-layout.md` |
| Function/event/error selectors, ABI encoding, metadata hash | `abi-and-metadata.md` |
| Re-entrancy, gas limits, delegatecall, randomness, `tx.origin`, pitfalls checklist | `security-considerations.md`, `common-patterns.md` |
| "Is this compiler version affected by a known bug?" | `known-bugs.md` (search by `introduced`/`fixed`) |
| Reading or migrating pre-0.8 code | `breaking-changes.md` |
| Doc comments | `natspec.md` |
| Naming, ordering, indentation, line length, formatting | `style-guide.md` |
| Formal verification / SMTChecker flags | `smtchecker.md` |
| Want a canonical worked example (auction, purchase, payment channel, modular contracts) | `examples.md` |
| Foundry tests, `forge test --fork-url`, forking cheatcodes, fuzz/invariant/brutalize, test naming, key hygiene | `foundry-integration.md` |
| Anvil/cast/chisel, interactive debugger, forge-std APIs, invariant handlers, `forge install`/Soldeer, extra `foundry.toml` keys, GitHub Actions, `forge script` deploy + verify | `foundry-tooling.md` |
| Which ERC/EIP applies, its number, title and current status (tokens, proxies, signatures, EVM opcodes) | `eip-register.md` |
| Edge development: EIPs/ERCs still in flight and recent forks (Fusaka live, Glamsterdam scheduled: 64 KB code size, SLOTNUM, SWAPN/DUPN, state-gas repricing, CREATE2 predeploy), Draft ERCs (7399, 8211, 7579, 7739, 7821, 7683, 7930…), with Ethereum Magicians threads, plus Arbitrum ArbOS activations (Dia, Elara), OP Stack Jovian, EntryPoint v0.9, Core Solidity roadmap, v4-hook security and MEV research | `edge-dev.md` (non-docs; verified 2026-10-10, re-check statuses) |
| Running a security audit: likelihood×impact severity, overall rating | `audit-severity-matrix.md` |
| Audit category checklist (reentrancy … L2 specifics, repo-profile doctrine) | `audit-vulnerability-checklist.md` |
| Writing the audit report / finding format (CONFIRMED vs HYPOTHESIS) | `audit-report-template.md` |
| Is this code *really* vulnerable? Safe-vs-unsafe pattern pairs, 0.8.37 + Solady style (compile-checked in `examples/AuditSafePatterns.sol`) | `audit-safe-unsafe-patterns.md` |
| Pitfalls the docs only touch indirectly: rounding order, SLOAD/SSTORE gas habits, force-fed Ether, reentrancy-guard tooling, proxy/initializer/storage-collision traps, string comparison, oracle/token/signature/access-control pitfalls, pre-audit checklist | `practitioner-checklist.md` (non-docs; docs win on conflict) |

Do not invent a rule, a global, an opcode's availability, a panic code or a selector. If the reference does
not settle it, say "could not confirm in the 0.8.37 docs" and, when a compiler is available, test it.

### 3. Write to the canonical structure

Every file follows the Style Guide order; every ABI-visible item is NatSpec'd; every failure is a named
custom error with useful values. Skeleton:

```solidity
// SPDX-License-Identifier: <id>
pragma solidity 0.8.37;            // exact pin in projects; a range only for libraries meant to be reused

import {Thing} from "./Thing.sol"; // named imports

/// @notice Thrown when `amount` is zero.
error ZeroAmount();
/// @notice Thrown when `requested` exceeds `available`.
error InsufficientBalance(uint256 requested, uint256 available);

/// @title Vault
/// @notice One-line purpose for end users.
/// @dev Design notes for developers.
contract Vault is Base {
    // 1. type declarations (struct, enum, type ... is, using for)
    // 2. state variables: constants (UPPER_CASE), immutables, storage, transient
    // 3. events   4. errors (contract-scoped)   5. modifiers
    // 6. functions: constructor, receive, fallback, external, public, internal, private
    //    (view then pure last inside each visibility group)

    /// @notice Withdraws `amount` wei to the caller.
    /// @param amount wei to withdraw
    /// @return newBalance the caller's balance after withdrawal
    function withdraw(uint256 amount) external returns (uint256 newBalance) {
        // checks
        if (amount == 0) revert ZeroAmount();
        uint256 bal = _balances[msg.sender];
        if (amount > bal) revert InsufficientBalance(amount, bal);
        // effects
        newBalance = bal - amount;
        _balances[msg.sender] = newBalance;
        // interactions
        (bool ok, ) = msg.sender.call{value: amount}("");
        if (!ok) revert TransferFailed(msg.sender, amount);
    }
}
```

Habits the docs actually require (see quick-rules for the sections):

- Explicit visibility on every function; explicit data location on every reference-type parameter/local.
- Checks-Effects-Interactions; check every low-level call result; never `transfer`/`send`.
- `require(cond, CustomError(args))` or `revert CustomError(args)`; `assert` only for invariants.
- `unchecked` only around arithmetic you have proven cannot wrap, with the proof in a comment.
- `assembly ("memory-safe") { ... }` only when the block honours the memory model; otherwise no annotation.
- Up to three `indexed` event params; `calldata` for external read-only reference params; `immutable` for
  constructor-set values; `constant` for compile-time values; `transient` only for value-type state that
  must reset per transaction (and only if you have reasoned about composability).
- Value-moving or upgradeable code: also read `references/practitioner-checklist.md` (rounding direction,
  cached storage reads, no `address(this).balance` invariants, initializer/implementation locking, append-only
  storage). It is practitioner guidance, not docs text — cite it as such.
- Interfaces: `external` functions only, no state, no constructor, no modifiers.
- Implementing a standard (token, vault, proxy, signature scheme): check `references/eip-register.md` for the
  number and its status, reuse the canonical errors (ERC-6093) and interface ids (ERC-165), and prefer an
  audited implementation over hand-rolling. Say which EIP and status you built against.

### 3b. Tests are part of the deliverable

Contract code without tests is half an answer. When the request implies a working contract (not a snippet or a
syntax question), write the Foundry tests alongside it following `references/foundry-integration.md`: the
documented naming (`test_`, `testFuzz_`, `test_RevertWhen_`, `testFork_`), `bound()` over `vm.assume()`,
selector-matched `expectRevert`, access-control and edge-value cases. If the contract integrates with a
deployed protocol, the test that matters is a fork test at a pinned block against verified addresses — and
every hardcoded address is a factual claim to check, not to recall.
Tooling, deployment and CI mechanics are in `references/foundry-tooling.md`.

### 4. Gate the result — and never claim what did not run

Run both scripts from this skill's directory on every file you wrote or changed:

```bash
python3 scripts/solcheck.py path/to/File.sol            # add --profile repo when the repo profile applies
bash   scripts/compile_check.sh path/to/File.sol        # or no args inside a Foundry project → forge build
python3 scripts/fix_memory_safe.py --check path/        # deprecated `/// @solidity memory-safe-assembly` → exit 1
```

`fix_memory_safe.py --write <paths>` rewrites the deprecated comment (docs §3.10.5) to `assembly ("memory-safe") { }`.
It keeps any dialect flag, including a single-quoted one, and reports anything it cannot convert by `file:line`; it never skips one silently.
The marker is read from comment text, so a string literal that contains the words is left alone. `--write` converts the whole batch in memory and writes only if every file converts. A path that is not `.sol` is an error.
Its tests are in `scripts/test_fix_memory_safe.py`.
- **Proof it is behaviour-neutral (2026-10-10):** on the full Solady `2afba69` tree, 1,547 blocks in 107 files were
  converted. Under solc 0.8.37 / osaka / via-IR, all 89 artifacts with code are byte-identical with the metadata
  trailer stripped. The one exception is the zksync `ERC1967Factory`, which is identical once its three embedded child
  metadata hashes are masked. The conversion also cleared the build's `4591` diagnostic-cap overflow.
- **Before converting a vendored tree you do not own**, check the project's rules: under the repo profile, vendored edits
  need the owner's OK.

- `solcheck.py` enforces: SPDX + pragma, file/member/function ordering, naming, 120-column limit, tabs,
  NatSpec coverage of the ABI (`@notice`, one `@param` per parameter, one `@return` per return) on
  functions, events, errors (including file-level), and public getters, the
  0.8.37 deprecations, bare/string reverts (including when the call is wrapped across lines), empty `catch`,
  unchecked low-level calls judged over the whole statement, `tx.origin`, `selfdestruct`, and `block.difficulty`.
  `now` is a legal 0.8 identifier and is left to the compiler. `__gap` is an allowed non-constant state name.
  Non-constant `UPPER_CASE` state is rejected. In repo profile the exact pragma is required and warnings fail the exit.
  Structure comes from solc's own parser (`--ast-compact-json --stop-after parsing`) when a `solc` binary is
  available, with a regex fallback otherwise; the summary line names the backend that ran (`backend=ast|regex`).
  Two parse-stage gaps are covered from the source text: solc attaches no NatSpec node to state variables, and
  it fills in `public` for a function written without visibility. It is a rule gate, not a type checker or a
  security analyser: an unexpected hit is a prompt to read the cited section, and a clean pass is necessary,
  not sufficient. `python3 scripts/test_solcheck.py` re-verifies the checker itself.
- `compile_check.sh` runs `forge build` when given no files inside a Foundry project, otherwise
  `solc --via-ir --evm-version osaka`. It does not call `solc-select` and does not change the selected
  compiler. Remappings come from `forge remappings` when `foundry.toml` and `forge` are available, otherwise
  from `remappings.txt`. Exit 0 = clean, 2 = warnings or usage (the `RESULT` line says which), 1 = errors,
  3 = no compiler → report "compilation not verified". A `// forge-lint: disable-next-line(<id>)` is acceptable
  only when narrow and justified. `bash scripts/test_compile_check.sh` checks exits 0, 1, 2, and 3.

Fix every error and warning in the source, rerun, and only then move on. If no compiler exists in the
environment, say exactly that in the final answer; do not describe code as compiling.

### 5. Report with evidence

End with: what was written/changed; which docs sections governed any non-obvious choice (e.g. "packing per
§3.16", "custom-error require per §3.8.8"); the `solcheck` and compile results verbatim (counts and exit
codes); anything that could not be confirmed and what would confirm it (a fork test, a compiler run, a live
docs check). Keep facts, hypotheses and open tasks separate.


## Foundry workflow

For Foundry projects, use the repository configuration as the source of truth for the compiler,
EVM target, optimizer, remappings, and test profiles. Do not copy version pins or config values
from generic examples. Read foundry.toml and applicable repository instructions first.

Use the relevant bundled references for test design, configuration, deployment, debugging, and
tooling. Typical local checks include forge build, targeted forge test runs, forge test -vvvv
for traces, Anvil for local execution, and cast call for read-only contract queries. Fork tests
should pin the fork block when behavior depends on chain state, and should use configured RPC
aliases without printing or exposing credentials.

Deployment and state-changing cast send commands can move assets or change live contracts.
Prepare and review the exact script, chain, target, and transaction first; do not broadcast or
sign unless the user explicitly requested that action. Keep deployer keys out of source, logs,
and command output. Treat example commands in the bundled references as illustrative, not
authorization to execute them.

Foundry examples from other skills may target older Solidity or Foundry releases. The pinned
project compiler and this skill's 0.8.37 references take precedence for syntax and compiler behavior.

## Review / audit mode

When asked to review existing Solidity rather than write it: run `solcheck.py` first for the mechanical
layer, then read the code against `security-considerations.md` (pitfalls), `quick-rules.md` §10 and `practitioner-checklist.md`, map any
compiler-version-specific concern to `known-bugs.md` by `introduced`/`fixed`, and for pre-0.8 code consult
`breaking-changes.md`. For a full audit, work `audit-vulnerability-checklist.md` category by category, grade with
`audit-severity-matrix.md`, filter false positives with `audit-safe-unsafe-patterns.md`, and write the report from
`audit-report-template.md` (every finding CONFIRMED or HYPOTHESIS). Report findings as `file:line → rule (docs §) → fix`, ordered by severity; do not
soften a finding because the code compiles, and do not escalate a style nit to a security finding.

## Version boundary

The references describe 0.8.37-develop. For a different pinned version, the rules still largely hold, but
check `known-bugs.md` for that version and prefer `solc --version` plus the live docs
(https://docs.soliditylang.org/en/<version>/) for anything the snapshot calls "scheduled for removal",
"experimental" or gates behind an EVM version — those move between releases.
