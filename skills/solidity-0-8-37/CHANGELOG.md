# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-10-15

### Added

- Solidity 0.8.37 language skill: the official docs snapshot (`0.8.37-develop`, 2026-09-10) bundled verbatim under `references/` with a table of contents per file, `quick-rules.md` distilling the rules that apply to nearly every file, and a repo-profile overlay for projects that pin exact versions and named custom errors.
- `scripts/solcheck.py`: style, ordering, naming, NatSpec-coverage and 0.8.37-deprecation checker, parsing with solc's own AST when a `solc` binary is available and falling back to regex otherwise; `scripts/test_solcheck.py` verifies the checker.
- `scripts/compile_check.sh`: compile gate that runs `forge build` inside a Foundry project or `solc --via-ir --evm-version osaka` otherwise, with distinct exit codes for clean, warnings, errors and no compiler; `scripts/test_compile_check.sh` covers all four.
- `scripts/fix_memory_safe.py`: rewrites the deprecated `/// @solidity memory-safe-assembly` comment to `assembly ("memory-safe")`, proven bytecode-neutral on 1,547 blocks of Solady; 13 unit tests.
- Audit mode: severity matrix, category checklist, report template and compile-checked safe-vs-unsafe pattern pairs (`examples/AuditSafePatterns.sol`).
- Non-docs references, dated and marked as such: `edge-dev.md` (in-flight EIPs, Fusaka/Glamsterdam, ArbOS, OP Stack, EntryPoint v0.9), `evm-opcodes-gas.md`, `practitioner-checklist.md`, `eip-register.md`, and the Foundry integration and tooling guides.
- `evals/evals.json`: four evals (write-and-gate a contract, deprecated-construct review, memory-safe conversion, version-gated construct lookup).

Verified against: solc@0.8.37, foundry@1.8.3
