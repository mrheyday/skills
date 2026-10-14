# Foundry workflow supplement

Adapted from the supplied foundry-solidity skill. This supplement focuses on safe workflow and
project-specific configuration; its examples do not replace the pinned compiler language rules.

## Configuration

Before using Foundry, inspect the project foundry.toml, remappings, and lockfiles. Use the
configured compiler, EVM target, optimizer, and profiles rather than copying sample values. Keep
RPC endpoints environment-interpolated and credentials in approved local secret storage.

## Build and tests

- forge build compiles with the project configuration.
- forge test runs the suite; use --match-test or --match-contract to narrow a run.
- forge test -vvvv provides detailed traces for a failing test.
- Use unit, fuzz, invariant, and fork tests as appropriate. Bound fuzz inputs instead of relying
  on assumptions where possible; match expected custom-error selectors precisely.
- Pin fork blocks when results depend on chain state. A mocked test does not establish behavior
  against a deployed protocol.

Run only the checks required by the task and repository workflow. A passing build or test proves
only the behavior it exercised.

## Local debugging and inspection

Use Anvil for local execution and fork debugging. Use cast call and storage inspection for
read-only queries. Review decoded transaction data and chain context before any state-changing
operation.

## Deployment

A deployment script should make its target chain, deployer, and resulting addresses reviewable.
Dry-run and inspect the exact transaction before broadcast. Never treat a sample broadcast,
cast send, or private-key command as permission to execute it. Do not place private keys, seed
phrases, or credential-bearing RPC URLs in source, logs, or tool output.

## Version boundary

The supplied Foundry skill examples target Solidity 0.8.30 and a particular Foundry release.
For projects pinned to another version, use the checked-in project configuration and matching
compiler references. Solidity 0.8.37-specific syntax and semantics are governed by this bundle.
