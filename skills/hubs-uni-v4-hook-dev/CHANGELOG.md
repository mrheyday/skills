# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-10-14

### Added

- Uniswap v4 hook development skill composing Foundry, OpenZeppelin `uniswap-hooks`, hookmate and Solady, with companion-skill routing to `foundry-solidity`, `solady-reference`, `v4-hook-generator`, `v4-sdk-integration` and `cyfrin-defi-uniswap-v4`.
- Verified examples: `CappedDynamicFeeHook` (single-pool binding, capped per-swap fee override, Solady `Ownable`), `ConstantSumHook` (NoOp `BeforeSwapDelta` over ERC-6909 claims, Solady transient reentrancy guard), `SkimFeeHook` (capped `afterSwapReturnDelta` fee, Solady `OwnableRoles` + `FixedPointMathLib`), the hookmate test harness, fuzz and invariant suites, and a HookMiner + CREATE2 deploy script broadcast to anvil.
- `BalanceDelta` reference: packing and operators, sign and perspective rules, swap/modifyLiquidity/donate returns, hook-delta mapping (specified/unspecified to amount0/1), settlement table, and a verified `DeltaSwapper` router with a fuzz test proving that the delta equals the balance change.
- References: hook archetypes from awesome-uniswap-hooks, testing and deployment, security (incident classes and risk scoring), Solady composition, and an ecosystem map including the current developers.uniswap.org guides.

### Fixed

- Corrected two facts that older v4 skills get wrong: `BEFORE_SWAP_RETURNS_DELTA` is address bit 3, and `IPoolManager.settle()` takes no arguments.

Verified against: @uniswap/v4-core@1.0.2, @uniswap/v4-periphery@1.0.3, @openzeppelin/uniswap-hooks@b5f1057, hookmate@0.6.0, solady@0.1.26, foundry@1.8.3
