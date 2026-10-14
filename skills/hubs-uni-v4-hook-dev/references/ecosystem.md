# Ecosystem Map

Curated from [awesome-uniswap-hooks](https://github.com/fewwwww/awesome-uniswap-hooks) plus the current official docs. Links were checked on 2026-10-14; dead ones from the awesome list were dropped. Older community repos target pre-1.0 v4 APIs, so read them for ideas and port the code to the patterns in `SKILL.md`.

## Contents

- [Primary references (start here)](#primary-references-start-here)
- [Edge-case references](#edge-case-references)
- [Libraries and tooling](#libraries-and-tooling)
- [Templates](#templates)
- [Production hooks](#production-hooks)
- [Uniswap example hooks](#uniswap-example-hooks)
- [Community hooks worth reading](#community-hooks-worth-reading)
- [Tutorials and courses](#tutorials-and-courses)
- [Research and ideas](#research-and-ideas)

## Primary references (start here)

| Resource | Use it for |
|---|---|
| [Hooks concepts](https://developers.uniswap.org/docs/protocols/v4/concepts/hooks) | Lifecycle callbacks, pool attachment, permission flags |
| [Getting started](https://developers.uniswap.org/docs/protocols/v4/guides/hooks/getting-started) | Foundry setup, local testing, minimal Counter hook |
| [Building your first hook](https://developers.uniswap.org/docs/protocols/v4/guides/hooks/your-first-hook) | End-to-end points hook with tests |
| [uniswapfoundation/v4-template](https://github.com/uniswapfoundation/v4-template) | The canonical Foundry project (OZ uniswap-hooks + hookmate) |
| [`IHooks.sol`](https://github.com/Uniswap/v4-core/blob/main/src/interfaces/IHooks.sol) | Callback signatures, arguments, return semantics |
| [`Hooks.sol`](https://github.com/Uniswap/v4-core/blob/main/src/libraries/Hooks.sol) | Address-bit permissions, validation, delta handling |
| [OpenZeppelin Uniswap Hooks docs](https://docs.openzeppelin.com/uniswap-hooks) / [repo](https://github.com/OpenZeppelin/uniswap-hooks) | Audited bases: custom accounting/curves, async swaps, fees, oracles |

## Edge-case references

| Resource | Use it for |
|---|---|
| [Hook deployment](https://developers.uniswap.org/docs/protocols/v4/guides/hooks/hook-deployment) | CREATE2 mining; matching address bits to permissions |
| [Accessing the original sender](https://developers.uniswap.org/docs/protocols/v4/guides/hooks/accessing-msg.sender) | `msg.sender` is the PoolManager and `sender` is the router; trusted-router patterns |
| [Custom accounting](https://developers.uniswap.org/docs/protocols/v4/guides/custom-accounting) | Return deltas, hook fees, custom swap accounting |
| [Unlock callback and deltas](https://developers.uniswap.org/docs/protocols/v4/guides/unlock-callback-and-deltas) | Flash accounting, the zero-delta invariant, rounding/slippage pitfalls |
| [Dynamic fees](https://developers.uniswap.org/docs/protocols/v4/concepts/dynamic-fees) | Persistent `updateDynamicLPFee` vs per-swap override |
| [AsyncSwap hooks](https://developers.uniswap.org/docs/protocols/v4/guides/hooks/async-swap) | Replacing swap execution; user-facing risk |
| [Hook security framework](https://developers.uniswap.org/docs/protocols/v4/security) | Risk-scoring worksheet, audit and monitoring guidance |
| [Uniswap/v4-hooks-public](https://github.com/Uniswap/v4-hooks-public) | Production-oriented hook contracts from Uniswap Labs |
| [Routing API hook allowlist](https://github.com/Uniswap/routing-api/blob/main/lib/util/hooksAddressesAllowlist.ts) | Which hooks the Uniswap router will route through, per chain |

## Libraries and tooling

- [hookmate](https://github.com/akshatmittal/hookmate) (formerly `saucepoint/hookmate`): canonical v4 artifacts, `AddressConstants`, `DeployHelper`, the `IUniswapV4Router04` interface, and TypeScript ABIs (`pnpm add hookmate`). Its stateless swap router is [hookmate/v4-router](https://github.com/hookmate/v4-router).
- [OpenZeppelin uniswap-hooks](https://github.com/OpenZeppelin/uniswap-hooks): hook bases and `CurrencySettler`. The OZ Contracts Wizard MCP can scaffold from these; see the `v4-hook-generator` skill.
- [Solady](https://github.com/Vectorized/solady): auth, math, transient guards; see `solady-composition.md` and the `solady-reference` skill.
- HookMiner (`@uniswap/v4-periphery/src/utils/HookMiner.sol`) for in-Solidity salt mining. Offline mining: [v4hookaddressminer.xyz](https://v4hookaddressminer.xyz/) and [HookMineAndSinker](https://github.com/devtooligan/HookMineAndSinker).
- [Scaffold Hook](https://github.com/uniswapfoundation/scaffold-hook): hook development stack with testnet deployment and UI.
- [v4 by Example](https://www.v4-by-example.org/): short Solidity snippets for v4 integration.
- Data and analytics: [HookRank](https://hookrank.io/), [v4.xyz](https://www.v4.xyz/).
- Uniswap's own AI plugin for hooks: [uniswap-ai / uniswap-hooks](https://github.com/Uniswap/uniswap-ai/tree/main/packages/plugins/uniswap-hooks) (the source of the `v4-security-foundations` and `v4-hook-generator` skills).

## Templates

- [uniswapfoundation/v4-template](https://github.com/uniswapfoundation/v4-template): recommended.
- [OpenZeppelin uniswap-hooks](https://github.com/OpenZeppelin/uniswap-hooks): a library, but its `src/mocks/` and `test/` are complete, runnable examples of every base.
- [Cyfrin defi-uniswap-v4](https://github.com/Cyfrin/defi-uniswap-v4): course exercises with solutions (flash loans, routers, hooks, PositionManager, UniversalRouter); see the `cyfrin-defi-uniswap-v4` skill.
- Older and community templates from the awesome list: SolidityLabs custom-pool, Arrakis playground, Quantum3 Scaffold-UniswapV4, Gnome101 Hardhat template. They are useful for UI or Hardhat setups but behind current APIs.

## Production hooks

| Project | What the hook does |
|---|---|
| Angstrom | Only staked validators can execute swaps; batch auctions defend LPs |
| Bunni | Rehypothecates idle liquidity into lending vaults; shape-shifting liquidity |
| EulerSwap | AMM backed by Euler lending vaults |
| Flaunch / UniDerp / Clanker / Zora / Ohara | Launchpads: fair launch, fee routing to creators, buybacks, MEV modules |
| Super DCA | TWAMM-style DCA plus dynamic fees and gauge-weighted rewards |
| USDL (Paxos) | Compliance-gated stablecoin pools (AML/jurisdiction checks via Predicate) |
| Unimon | NFT game minted and managed inside a hook |
| Pubhouse | Prediction-token markets |

## Uniswap example hooks

Legacy `example-contracts` branch, pre-1.0 API: [Full Range](https://github.com/Uniswap/v4-periphery/tree/example-contracts/contracts/hooks/examples/FullRange.sol), [Geomean Oracle](https://github.com/Uniswap/v4-periphery/tree/example-contracts/contracts/hooks/examples/GeomeanOracle.sol), [Limit Order](https://github.com/Uniswap/v4-periphery/tree/example-contracts/contracts/hooks/examples/LimitOrder.sol), [TWAMM](https://github.com/Uniswap/v4-periphery/tree/example-contracts/contracts/hooks/examples/TWAMM.sol), [Volatility Oracle](https://github.com/Uniswap/v4-periphery/tree/example-contracts/contracts/hooks/examples/VolatilityOracle.sol), [Truncated Oracle](https://github.com/Uniswap/v4-periphery/blob/trunc-oracle/contracts/hooks/TruncGeoOracle.sol). For current code, prefer [v4-hooks-public](https://github.com/Uniswap/v4-hooks-public) and the OZ bases.

## Community hooks worth reading

Grouped by archetype; `hook-archetypes.md` explains each pattern.

- **Fees:** [Ref Fee Hook](https://github.com/mergd/ref-fee-hook), [Slippage Fee Hook](https://github.com/dennnis0204/slippage-fee-hook), [Super DCA Gauge](https://github.com/Super-DCA-Tech/super-dca-gauge).
- **Orders:** [Stop Loss](https://github.com/saucepoint/v4-stoploss), [Take Profit](https://github.com/LearnWeb3DAO/uniswap-v4-take-profits-hook), [Encrypted iceberg orders (Fhenix)](https://github.com/marronjo/iceberg-cofhe), [FWB TWAMM](https://github.com/akshatmittal/v4-twamm-hook).
- **Curves / NoOp:** [Constant-sum](https://github.com/saucepoint/v4-constant-sum), [v2 on v4](https://github.com/hensha256/v2-on-v4), [Orbital spherical AMM](https://github.com/Dhruv-2003/ethglobal-buenos-aires-25).
- **Oracles:** [BackGeoOracle](https://github.com/RigoBlock/back-geo-oracle/blob/main/src/BackGeoOracle.sol).
- **Gating / compliance:** [Civic](https://github.com/civicteam/uniswap-v4-hook), [World ID KYC](https://github.com/Shivamycodee/WID-KYC-Hook), [Whitelist](https://github.com/atj3097/whitelist-hook), [NFT owners only](https://github.com/wagmiwiz/nft-owners-only-uniswap-hook), [NY trading hours](https://github.com/horsefacts/trading-days), [PureFi verifier](https://github.com/purefiprotocol/purefi-verifier-hook).
- **Liquidity / MEV:** [Minimize LVR PoC](https://github.com/ArrakisFinance/minimize-lvr-hook-poc), [Detox (MEV → LPs)](https://ethglobal.com/showcase/detox-hook-mppeg), [Liquidity locking](https://github.com/BrokkrFinance/hooks-poc/blob/main/src/LiquidityLocking.sol), [veLP](https://github.com/kadenzipfel/veLP), [Bungi](https://github.com/saucepoint/bungi), [Automated buyback](https://github.com/atj3097/buyback-hook).
- **Launch:** [Uni LBP](https://github.com/kadenzipfel/uni-lbp), [Torres token sale](https://github.com/jamesbachini/Uniswap-V4-Torres-Token-Sale).

## Tutorials and courses

- [Captain Hook tutorial hooks](https://github.com/umbrellaresearch/uni-v4-hooks-tutorial) (roles, dynamic fees), with the Umbrella Research deep-dive posts.
- [LearnWeb3 take-profit hook lesson](https://learnweb3.io/lessons/uniswap-v4-hooks-create-a-fully-on-chain-take-profit-orders-hook-on-uniswap-v4/).
- Cyfrin Updraft "DeFi Uniswap V4" course (exercises: [Cyfrin/defi-uniswap-v4](https://github.com/Cyfrin/defi-uniswap-v4)).
- [Atrium Uniswap Hook Incubator](https://atrium.academy/uniswap): an 8-week program for advanced hook builders.

## Research and ideas

- Security research: Composable Security on [re-initialization](https://composable-security.com/blog/uniswap-v-4-re-initialization-leading-to-funds-locked/), [hook-fee liquidity theft](https://composable-security.com/blog/uniswap-v-4-liquidity-theft-via-hook-fee/), [malicious-owner oracle](https://composable-security.com/blog/uniswap-v-4-oracle-hook-with-malicious-owner/) and [integration threat model](https://composable-security.com/blog/uniswap-v-4-threat-modeling-for-secure-integration/); Phalcon on [risky interactions](https://phalcon.xyz/blog/lethal-integration-vulnerabilities-in-hooks-due-to-risky-interactions) and [hook threat models](https://phalcon.xyz/blog/thorns-in-the-rose-exploring-security-risks-in-uniswap-v4-s-novel-hook-mechanism); [Certora's v4 threat model](https://www.certora.com/blog/protecting-uniswap-v4-against-unknown-attacks-part-one-a-threat-model); [0x on quote-vs-settle spoofing](https://x.com/0xProject/status/2099578032960995502).
- Design ideas from the awesome list:
  - [LVR minimization](https://ethresear.ch/t/lvr-minimization-in-uniswap-v4/15900), [oracleless lending on v4](https://blog.instadapp.io/oracleless-lending-protocol-on-uniswap-v4/), the auction-managed AMM, a sandwich-resistant hook (Umbra Research), Doppler (liquidity bootstrapping), and the "null fee" indicator for dynamic-fee design.
  - Aggregator-friendliness tips for custom pools, and value-accrual and fork risk of hook fees.
- [Establishing hook data standards](https://uniswapfoundation.mirror.xyz/KGKMZ2Gbc_I8IqySVUMrEenZxPnVnH9-Qe4BlN1qn0g): event conventions so indexers and analysts can read your hook. Emit OZ `IHookEvents`-style events.
- [Optimization Arena AMM challenge](https://www.optimizationarena.com/amm): compete with v4-style dynamic-fee hooks against a 30 bps benchmark.
