# Repo Profile (optional, stricter) — apply when the repository contract asks for it

Use this profile only when the working repository's `CLAUDE.md` / `AGENTS.md` / `agents/guardrails.md`
declares these constraints, or the user explicitly asks for "repo profile" / "production profile".
It tightens, never loosens, the generic rules in `quick-rules.md`. Verify each stack value against the live
`foundry.toml`, `remappings.txt` and lockfiles before relying on it — the profile records expectations, the
checkout is the truth.

## Toolchain pins (verify in `foundry.toml`)
- `solc = "0.8.37"`, `evm_version = "osaka"`, `via_ir = true`. Pragma in every source file is the exact
  `pragma solidity 0.8.37;`, or a floor range `>=0.8.3[4-7] <0.9.0;` when the repo contract adopts one (no
  caret). A range lets an alternative compiler with an older front end, such as solx on solc 0.8.34, build the
  file, while `solc_version` still decides the compiler that ships. Pick the floor from what the file uses:
  `erc7201()` needs 0.8.35 (solc Changelog), so such a file cannot claim 0.8.34. Building below 0.8.37 exposes
  the three bugs fixed in 0.8.37 (`known-bugs.md`), so a range is not authority to deploy that bytecode.
- Foundry is the only test harness. Behavioural claims need `--fork-url` tests against real mainnet addresses;
  mocks alone do not establish behaviour. Label every fork/testnet explicitly; the production target is
  Arbitrum One.
- Dependencies are pinned to exact versions with raw-GitHub provenance recorded. Default imports are
  `@solady/...` and `@forge-std/...`; `SafeCastLib` means Solady's implementation, never an inline cast
  suppression. `@uniswap/v4-core` is allowed (no import ban). Check the SPDX header on each v4-core file
  before adding a new import; the checkout contract names the approved MIT surface.
- Alloy (Rust side) uses `provider-ws` / `provider-ipc` features with exact pins — not bare `ws` / `ipc`.

## Target-chain EVM facts (Arbitrum One; sources and refresh steps in `edge-dev.md` §E1)
- **ArbOS history** (activation, from docs.arbitrum.foundation/network-upgrades, read 2026-10-10):
  - ArbOS 40 Callisto: 2025-06-17;
  - ArbOS 51 Dia: 2026-01-08. Fusaka execution-layer parity: CLZ, secp256r1 (EIP-7951), MODEXP bounds and
    repricing, BLS12-381 enabled;
  - **ArbOS 61 Elara: 2026-08-20.**
- **Contract size: Solidity is 24,576 B runtime and 49,152 B initcode.** Elara's 96 KB limit applies to Stylus
  (WASM/Rust) contracts only. EIP-7954's 64 KB is an Ethereum Glamsterdam item, and it does not apply on Arbitrum
  until an ArbOS release adopts it. Size every deployable against 24,576 B.
- **Per-tx gas cap (EIP-7825): 32M L2 gas on Arbitrum**, not Ethereum's 16M. Split deploys and batches to fit.
- **Elara's `BaseFeeManager`:** the minimum L2 base fee is adjustable within 0.01–0.10 gwei by Offchain Labs for
  2 years. Read the base fee live and never hardcode it. Dynamic Pricing (multidimensional gas) is present but
  disabled.
- **Ordering:** PGA on-chain since block 508,190,474 (repo proof PR-20260925-01). Priority-fee collection sits behind
  an `ArbOwner.setCollectTips` toggle. A "Fast Feed" AIP was voted together with PGA; its latency terms were not
  read.
- **Never change `evm_version`** (for example to the experimental `amsterdam`) without the owner's explicit OK.
  Glamsterdam opcodes (SLOTNUM, SWAPN/DUPN) are not available on Arbitrum yet.

## Failure safety (stricter than the docs)
- Every revert uses a **named custom error** carrying the offending values when useful. No bare `revert()`,
  no `revert("string")`, no `require(cond, "string")`, no `assert` for input validation, no `revert(0,0)`
  in assembly.
- Reject zero / unset / stale / uninitialised state explicitly (`if (x == 0) revert ZeroValue();`), never treat
  it as valid or default-on-error.
- No empty `catch`, no swallowed low-level call result, no default-on-error path, no no-op failure branch.
- An intentionally unimplemented entrypoint reverts with a named error (e.g. `NotImplemented(bytes4 selector)`)
  and has a tracked ledger task; never a `TODO`/`FIXME`/filler return.
- Economic and latency thresholds are sourced live (config, oracle, constructor/immutable from deployment
  input) — never hard-coded literals in logic.

## Lint and warnings
- Zero warnings, fixed in code — not suppressed. Only a justified, narrow
  `// forge-lint: disable-next-line(<id>)` is acceptable, never blanket config ignores.
- Deprecated patterns (`transfer`/`send`, `selfdestruct`, `virtual` modifiers, constructor visibility,
  `memory-safe-assembly` comment) are defects even if they compile.

## Naming and reuse
- One concept has one canonical name across Solidity, Rust and docs. Re-home reused code under
  repository-owned modules with provenance preserved (see the repo's naming-and-reuse conventions file).

## Evidence
- A compile or passing unit test proves only itself. Behavioural completion claims cite a proof record
  (on-chain tx, fork test against real addresses, or REVM simulation) per the repo's proof-ledger doctrine.
- Report in this order: what changed; what was verified (proof IDs, URLs, `file:line`); what remains
  unproven; open tasks/blockers; discrepancies corrected. Never declare a lane executable — the owner does.

## Never
- Read, print, or write secrets (keys, seeds, mnemonics, RPC URLs with embedded keys) anywhere.
- Work on `main`, use `git add -A` blindly, or expand beyond the declared file set.
