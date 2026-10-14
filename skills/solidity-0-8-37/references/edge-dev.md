# Edge development: EVM innovations in flight (Ethereum Magicians index)

> **Provenance (read 2026-10-10).**
> - Thread discovery: Exa search over ethereum-magicians.org.
> - Statuses, created dates and discussion links: read from each EIP's own page at
>   `https://eips.ethereum.org/EIPS/eip-<n>` (its JSON-LD `headline`/`dateCreated`/`discussionUrl` and the status
>   badge). Never from a forum post or a search snippet.
> - Fork scope: read from the hardfork meta EIPs, [7607](https://eips.ethereum.org/EIPS/eip-7607) (Fusaka, "Included
>   EIPs") and [7773](https://eips.ethereum.org/EIPS/eip-7773) (Glamsterdam, "Scheduled for Inclusion"; that meta EIP
>   itself is in Review).
> - Compiler exposure: from this skill's `compiler-evm-versions-and-imports.md`.
> - "Repo implication" lines are **analysis, not fact**. Statuses move; re-read the EIP page before relying on any
>   non-Final entry.

Companion to `eip-register.md`. That file lists the settled standards to build on. This file lists what is
**changing**: proposals still in Draft, Review or Last Call, and Final EIPs whose activation is recent or pending. Each
one changes how contracts should be written, priced or deployed.

## How to use this file

1. **Status is not activation.** A Final core EIP is live only on chains whose fork activated it. **L2s activate on
   their own schedule.** Arbitrum ships EVM changes through ArbOS upgrades. Example: CLZ (EIP-7939) is live on Arbitrum
   One via ArbOS 51 "Dia" (2026-01-08), per the repo record, which was probed on-chain. **Probe the target chain**
   (`eth_call` a tiny contract that uses the opcode) before relying on any opcode or precompile there.
2. **Compiler target gates the code.** solc 0.8.37 defaults to `osaka`. `amsterdam` and `@future` are **experimental**
   EVM versions. Glamsterdam features such as `block.slotnum` / `slotnum()` (EIP-7843) compile only against them.
   **Under the repo profile, never change `evm_version` without the owner's explicit OK** (CLAUDE.md §2).
3. **Draft or Review ERCs are moving targets.** Build against one only when asked. Pin the exact text (commit or PR
   head) and say so in the NatSpec and the PR. The repo precedent is ERC-8211, pinned at PR ethereum/ERCs#1638 head
   `1f6ea652` in `docs/evidence/2026-10-05-flash-loan-specs/erc-8211.md`.
4. **The Magicians thread is where the edge cases live.** The spec says what MUST happen. The thread is where
   security, gas and composability objections get raised. Skim the thread before implementing a non-Final standard.

## A. Final and activated on Ethereum. Probe each L2.

| EIP | Title | Status | Ethereum fork | Discussion | Writing-code note |
|---|---|---|---|---|---|
| [1153](https://eips.ethereum.org/EIPS/eip-1153) | Transient storage opcodes | Final | Cancun | [thread](https://ethereum-magicians.org/t/eip-transient-storage-opcodes/553) | `TSTORE`/`TLOAD` are cleared at transaction end, not call end. A lock or flag shared by several operations in one tx can read stale values. Clear explicitly when an operation ends. |
| [7702](https://eips.ethereum.org/EIPS/eip-7702) | Set Code for EOAs | Final | Pectra | [thread](https://ethereum-magicians.org/t/eip-set-eoa-account-code-for-one-transaction/19923) | `tx.origin == msg.sender` no longer proves "EOA, no code". `extcodesize > 0` can be a delegated EOA. Never gate on either. |
| [2935](https://eips.ethereum.org/EIPS/eip-2935) | Serve historical block hashes from state | Final | Pectra | [thread](https://ethereum-magicians.org/t/eip-2935-save-historical-block-hashes-in-state/4565) | Hashes older than 256 blocks are readable from the history contract. Still not a randomness source. |
| [7623](https://eips.ethereum.org/EIPS/eip-7623) | Increase calldata cost | Final | Pectra | [thread](https://ethereum-magicians.org/t/eip-7623-increase-calldata-cost/18647) | A calldata floor price applies to data-heavy transactions. Compressing calldata matters less on L1 where execution dominates. On Arbitrum the L1 data fee is a separate formula (repo §2). |
| [7825](https://eips.ethereum.org/EIPS/eip-7825) | Transaction Gas Limit Cap | Final | Fusaka | [thread](https://ethereum-magicians.org/t/eip-7825-transaction-gas-limit-cap/21848) | Every transaction has a hard gas cap. A batch or deploy script that relied on one huge transaction must split it. |
| [7939](https://eips.ethereum.org/EIPS/eip-7939) | Count leading zeros (CLZ) opcode | Final | Fusaka | [thread](https://ethereum-magicians.org/t/create-a-new-opcode-for-counting-leading-zeros-clz/10805) | `clz` is a builtin in inline assembly (osaka). Solady's `@solady/utils/clz/` uses it. Halmos 0.3.3 cannot execute 0x1e (repo §2), so cover it with fuzz tests. |
| [7951](https://eips.ethereum.org/EIPS/eip-7951) | Precompile for secp256r1 Curve Support | Final | Fusaka | [thread](https://ethereum-magicians.org/t/eip-7951-precompile-for-secp256r1-curve-support/24360) | Passkey/P-256 verification becomes a precompile call. Check the precompile exists on the target chain before deleting a Solidity fallback verifier. |
| [7201](https://eips.ethereum.org/EIPS/eip-7201) | Namespaced Storage Layout | Final | (ERC) | [thread](https://ethereum-magicians.org/t/eip-7201-namespaced-storage-layout/14796) | `erc7201("ns")` is a compiler builtin in 0.8.37. Use it for every persistent namespace in upgradeable code. |
| [7528](https://eips.ethereum.org/EIPS/eip-7528) | ETH (Native Asset) Address Convention | Final | (ERC) | [thread](https://ethereum-magicians.org/t/eip-7808-eth-native-asset-address-convention/15989) | `0xEeee…EEeE` names native ETH in ERC-20 address fields. A wrapped token (WETH) MUST use its own address. |
| [7913](https://eips.ethereum.org/EIPS/eip-7913) | Signature Verifiers | Final | (ERC) | [thread](https://ethereum-magicians.org/t/erc-7913-key-verifiers/23262) | Verifier contracts for keys that are not addresses (P-256, RSA…), complementing ERC-1271. |
| [7786](https://eips.ethereum.org/EIPS/eip-7786) | Cross-Chain Messaging Gateway | Final | (ERC) | [thread](https://ethereum-magicians.org/t/erc-7786-cross-chain-messaging-gateway/21374) | A transport-agnostic send/receive gateway. Pair it with an ERC-7930 address on the receive side. |
| [4337](https://eips.ethereum.org/EIPS/eip-4337) | Account Abstraction Using Alt Mempool | Final | (ERC) | [thread](https://ethereum-magicians.org/t/erc-4337-account-abstraction-via-entry-point-contract-specification/7160) | EntryPoint versions are not interchangeable. A paymaster built for v0.7 fails v0.9's ERC-165 check. Pin the EntryPoint address per version. |

## B. Scheduled for Glamsterdam (EIP-7773 "Scheduled for Inclusion"). Execution-layer items that affect contract code.

Each EIP below is in **Last Call** (read from its page on 2026-10-10). It is not live until the fork activates, and
not on an L2 until that L2 adopts it. In solc these compile only against the experimental `amsterdam` target.

| EIP | Title | Discussion | What changes for contract authors |
|---|---|---|---|
| [7954](https://eips.ethereum.org/EIPS/eip-7954) | Increase Maximum Contract Size | [thread](https://ethereum-magicians.org/t/increase-maximum-contract-size-to-48kb/24509) | Runtime limit goes from 24,576 to **65,536 B**; initcode limit from 49,152 to **131,072 B** (spec abstract). The thread slug still says "48kb", but the spec is the source. **Repo implication:** this would relax the 24 KB pressure behind the linked-library splits, but only once the deploy chain (Arbitrum) adopts it. Do not plan around it before then. |
| [7843](https://eips.ethereum.org/EIPS/eip-7843) | SLOTNUM opcode | [thread](https://ethereum-magicians.org/t/eip-7843-slotnum-opcode/22234) | `SLOTNUM` (0x4b) returns the beacon slot. Exposed as `block.slotnum` / `slotnum()` under `amsterdam`. It is meaningless on an L2 that has no beacon slots, so do not use it as a timing source there. |
| [8024](https://eips.ethereum.org/EIPS/eip-8024) | Backward compatible SWAPN, DUPN, EXCHANGE | [thread](https://ethereum-magicians.org/t/eip-8024-backward-compatible-swapn-dupn-exchange/25486) | Lifts the 16-deep stack limit for codegen. Expected to relieve "stack too deep". Hypothesis until a solc release documents using it. Do not restructure code around it yet. |
| [8037](https://eips.ethereum.org/EIPS/eip-8037) | State Creation Gas Cost Increase | [thread](https://ethereum-magicians.org/t/eip-8037-state-creation-gas-cost-increase/25694) | Creating state (new storage slots, new accounts, code bytes) costs more. Its "Deterministic deployment factories" section matters for CREATE2/CREATE3 deploy budgets. **Repo implication:** this reinforces the transient-plus-immutable design over persistent storage. |
| [8038](https://eips.ethereum.org/EIPS/eip-8038) | State-access gas cost update | [thread](https://ethereum-magicians.org/t/eip-8038-state-access-gas-cost-update/25693) | Re-prices SLOAD/SSTORE/account access into access + write + state components, with a special case for EXTCODESIZE/EXTCODECOPY. Hard-coded gas stipends and gas-bounded sub-calls must be re-measured after the fork. |
| [7778](https://eips.ethereum.org/EIPS/eip-7778) | Block Gas Accounting without Refunds | [thread](https://ethereum-magicians.org/t/eip-7778-prevent-block-gas-smuggling/21234) | SSTORE-to-zero refunds still reduce what the transaction pays, but no longer reduce gas counted toward the block limit. Refund tricks no longer pack more into a block. |
| [8246](https://eips.ethereum.org/EIPS/eip-8246) | Remove SELFDESTRUCT Burn | [thread](https://ethereum-magicians.org/t/eip-8246-remove-selfdestruct-burn/28416) | Remaining balance is preserved instead of burned. `selfdestruct` stays deprecated in Solidity; do not use it. |
| [7708](https://eips.ethereum.org/EIPS/eip-7708) | ETH transfers emit a log | [thread](https://ethereum-magicians.org/t/eip-7708-eth-transfers-emit-a-log/20034) | Every ETH transfer emits a protocol log, so indexers no longer need traces for contract ETH movements. Custom "ETH sent" events become redundant for tracking, but are still useful for semantics. |
| [7997](https://eips.ethereum.org/EIPS/eip-7997) | Deterministic Factory Contract | [thread](https://ethereum-magicians.org/t/eip-7997-deterministic-factory-predeploy/24998) | Makes the CREATE2 factory `0x4e59b44847b379578588920cA78FbF26c0B4956C` a required predeploy. The spec has a "Frontrunnable deployments" section: unguarded salts can be front-run. the repo profile deploys through CreateX with guarded salts (§2), which is unaffected. |
| [7976](https://eips.ethereum.org/EIPS/eip-7976) | Increase Calldata Floor Cost | [thread](https://ethereum-magicians.org/t/eip-7976-further-increase-calldata-cost/24597) | A further calldata floor increase, after 7623. |
| [7981](https://eips.ethereum.org/EIPS/eip-7981) | Increase Access List Cost | [thread](https://ethereum-magicians.org/t/eip-7981-increase-access-list-cost/24680) | Access lists are charged for their data, which closes a way around the 7623 floor. |
| [2780](https://eips.ethereum.org/EIPS/eip-2780) | Resource-based intrinsic transaction gas | [thread](https://ethereum-magicians.org/t/eip-2780-reduce-intrinsic-cost-of-transactions/4413) | The flat 21,000 intrinsic cost is broken into components. Off-chain gas estimators must use the new formula. |
| [7928](https://eips.ethereum.org/EIPS/eip-7928) | Block-Level Access Lists | [thread](https://ethereum-magicians.org/t/eip-7928-block-level-access-lists/23337) | Blocks commit to every account and slot touched, which enables parallel execution. Mostly a client and builder concern. **MEV implication (analysis):** a block's touched-state footprint becomes explicit. |
| [7732](https://eips.ethereum.org/EIPS/eip-7732) | Enshrined Proposer-Builder Separation | [thread](https://ethereum-magicians.org/t/eip-7732-enshrined-proposer-builder-separation-epbs/19634) | PBS moves into the protocol, changing Ethereum L1 block-building and MEV supply-chain timing. No direct effect on Arbitrum, where ordering is the sequencer's PGA. |

## C. Draft or Review standards relevant to the repo profile (moving targets)

| # | Title | Status | Discussion | Why it is on the repo profile's edge |
|---|---|---|---|---|
| [7399](https://eips.ethereum.org/EIPS/eip-7399) | ⚡ Flash Loans ⚡ | Review | [thread](https://ethereum-magicians.org/t/erc7400-flash-loans/15211) | Successor to ERC-3156: arbitrary callback selector, and fee payment to a separate receiver. A lender kind in `impl/flash` and `impl/hooks`. Wrappers are admitted only with a full Sourcify match (repo ruling). |
| 8211 | Smart Batching | Draft (no EIPs-site page yet; PR text) | [thread](https://ethereum-magicians.org/t/erc-8211-smart-batching/28135) | Parameters resolved at execution time, with inline constraints. Implemented by `impl/flash` `LegRunner` against the pinned spec text. Requires ERC-7964. |
| [7579](https://eips.ethereum.org/EIPS/eip-7579) | Minimal Modular Smart Accounts | Draft | [thread](https://ethereum-magicians.org/t/erc-7579-minimal-modular-smart-accounts/17336) | Module types 1–4 and `isModuleInstalled`, used by the account unit. Draft, so the interface ids can still change. |
| [7821](https://eips.ethereum.org/EIPS/eip-7821) | Minimal Batch Executor Interface | Draft | [thread](https://ethereum-magicians.org/t/erc-7821-minimal-batch-executor-interface/21776) | A single `execute(mode, data)` batching shape, common in 7702 delegate code. |
| [7739](https://eips.ethereum.org/EIPS/eip-7739) | Readable Typed Signatures for Smart Accounts | Draft | [thread](https://ethereum-magicians.org/t/erc-7739-readable-typed-signatures-for-smart-accounts/20513) | Nested EIP-712 signatures that stop one signature being replayed across accounts owned by the same key. The account unit's guard uses it. |
| [7710](https://eips.ethereum.org/EIPS/eip-7710) | Smart Contract Delegation | Draft | [thread](https://ethereum-magicians.org/t/towards-more-conversational-wallet-connections-a-proposal-for-the-redeemdelegation-interface/16690) | On-chain delegation redemption. Relevant to scoped session or bot keys. |
| [7715](https://eips.ethereum.org/EIPS/eip-7715) | Request Permissions from Wallets | Draft | [thread](https://ethereum-magicians.org/t/erc-7715-grant-permissions-from-wallets/20100) | Wallet RPC for granting scoped permissions. The off-chain counterpart of 7710. |
| [7683](https://eips.ethereum.org/EIPS/eip-7683) | Cross Chain Intents | Draft | [thread](https://ethereum-magicians.org/t/erc-cross-chain-intents-standard/19619) | Order and settlement structs for cross-chain intents. Relevant to the decision-0017 intents path. |
| [7930](https://eips.ethereum.org/EIPS/eip-7930) | Interoperable Addresses | Review | [thread](https://ethereum-magicians.org/t/erc-7930-interoperable-addresses/23365) | Chain-qualified address encoding. Never treat a bare 20-byte address as chain-agnostic. |
| [7965](https://eips.ethereum.org/EIPS/eip-7965) | Proof-based Broadcast in ERC-7786 Gateways | Draft | [thread](https://ethereum-magicians.org/t/erc-7965-storage-proof-broadcasting-for-cross-chain-messaging-gateways/24477) | Storage-proof broadcast over 7786. Relevant to read-only cross-chain ingest (decision 0015). |
| [7955](https://eips.ethereum.org/EIPS/eip-7955) | Permissionless CREATE2 Factory | Draft | [thread](https://ethereum-magicians.org/t/multi-chain-deployment-process-for-a-permissionless-contract-factory/24318) | A multi-chain factory deployment process. Compare with 7997's predeploy and with CreateX. |
| [8004](https://eips.ethereum.org/EIPS/eip-8004) | Trustless Agents | Draft | [thread](https://ethereum-magicians.org/t/erc-8004-trustless-agents/25098) | On-chain agent identity, reputation and validation registries. |
| [8141](https://eips.ethereum.org/EIPS/eip-8141) | Frame Transaction | Draft (core) | [thread](https://ethereum-magicians.org/t/frame-transaction/27617) | A new transaction type with multiple execution frames, a native account-abstraction direction. Not scheduled. |
| [7907](https://eips.ethereum.org/EIPS/eip-7907) | Meter Contract Code Size | Draft | [thread](https://ethereum-magicians.org/t/eip-remove-contract-size-limit/23156) | Gas-metered code size. The limit increase itself moved to EIP-7954 (its spec says so). |
| [5920](https://eips.ethereum.org/EIPS/eip-5920) | PAY opcode | Draft | [thread](https://ethereum-magicians.org/t/eip-5920-pay-opcode/11717) | Send ETH without executing the recipient's code, which removes the reentrancy surface of `call{value:}`. Not scheduled. |
| [7692](https://eips.ethereum.org/EIPS/eip-7692) | EVM Object Format (EOFv1) Meta | **Stagnant** | [thread](https://ethereum-magicians.org/t/eip-7692-evm-object-format-eof-meta/19686) | EOF is not in Fusaka's included list or Glamsterdam's schedule. Do not target it. Stack-depth relief is coming via 8024 instead. |

## D. Searched, but no Magicians thread found by Exa on 2026-10-10

Topics: ERC-6909, EIP-7825 (later found through its EIP page), ERC-8004 (likewise), ERC-7739 (likewise), EIP-2935
(likewise) and ERC-4337. Their discussion links above come from each EIP page's `discussions-to` field, not from
search. Uniswap v4 hook ERCs: only [ERC-8090](https://ethereum-magicians.org/t/erc-8090-gasless-minting-swap-standards-in-uniswap-v4/26711)
turned up. It has no EIPs-site page and its status is unverified, so it is listed here for awareness only.

## E. Beyond Magicians: chain, compiler and research forums (read 2026-10-10)

Discovered by Exa and then read from each primary page: Discourse threads via their `/t/<id>.json` endpoint, docs
pages and GitHub releases directly. Each statement below cites its source. The rest is labelled analysis.

### E1. Arbitrum, the repo profile's deploy chain: what the EVM actually is there

**ArbOS activation table** (source: [docs.arbitrum.foundation/network-upgrades](https://docs.arbitrum.foundation/network-upgrades)):

| ArbOS | Arbitrum One activation (UTC) | What matters for contract code |
|---|---|---|
| 40 Callisto | 2025-06-17 22:56:23 | Base for Dia. Its BLS12-381 precompile was not properly enabled until Dia. |
| 51 Dia | 2026-01-08 17:00:02 | Ethereum Fusaka EL parity: EIP-7951 secp256r1, EIP-7939 CLZ, EIP-7823 MODEXP bounds, EIP-7883 MODEXP repricing, EIP-2537 BLS12-381 enabled. **EIP-7825 cap is 32M L2 gas per tx on Arbitrum (Ethereum: 16M).** The last tx in a block may use `MaxTxGasLimit` beyond the block limit. Minimum L2 base fee went to 0.02 gwei. Sources: [AIP ArbOS 50/51 Dia](https://forum.arbitrum.foundation/t/constitutional-aip-arbos-version-50-dia/29835), [ArbOS 51 release notes](https://docs.arbitrum.io/run-a-node/arbos-releases/arbos51). |
| 61 Elara | 2026-08-20 17:08:23 | Stylus (WASM/Rust) contracts get a **96 KB** limit, split into ≤24 KB fragments by the Stylus SDK. **Solidity stays at 24 KB.** Elara calls 96 KB "4x greater than the smart contract size limit for Solidity contracts on the EVM". New `BaseFeeManager`: Offchain Labs may set the minimum L2 base fee within 0.01–0.10 gwei for 2 years. Dynamic Pricing (multidimensional gas) is included but **disabled** on One and Nova. ArbOS 60 was never activated on One: a refund-logic bug moved it to 61. Source: [AIP ArbOS 61 Elara](https://forum.arbitrum.foundation/t/constitutional-aip-arbos-61-elara/30601). |

**Contract size on Arbitrum.** A community request to adopt EIP-7954 ahead of Glamsterdam
([thread](https://forum.arbitrum.foundation/t/implement-an-enhanced-version-of-eip-7954-on-arbitrum-to-raise-contract-the-size-limit-to-at-least-64kb/30428))
got this answer from Offchain Labs (2026-02-02): stay compatible with Ethereum's forks, and raise the limit for
**Stylus only**. That thread still describes EIP-7954 as 32 KB. The current EIP-7954 page says 65,536 B, and the EIP
page is the source. **Rule:** plan Solidity on Arbitrum at **24,576 B** until a future ArbOS adopts EIP-7954. Read the
ArbOS release notes, not the Ethereum fork, for the date.

**Ordering, which matters to MEV.** The [PGA ordering AIP](https://forum.arbitrum.foundation/t/constitutional-aip-transition-arbitrum-one-ordering-policy-to-priority-gas-auctions-pga/30942)
was consolidated with a separate "Fast Feed" AIP into one constitutional vote (update of 2026-08-17). Priority-fee
collection sits behind an on-chain toggle (`ArbOwner.setCollectTips`) that is enabled together with the sequencer's
PGA mode. The repo records PGA as live on-chain since block 508,190,474 (proof PR-20260925-01). The Fast Feed details
were **not read here**: read that AIP before relying on feed latency.

**Glamsterdam on Arbitrum (analysis).** None of section B is live on Arbitrum until an ArbOS release ships it. Elara's
own text expects Ethereum's multidimensional gas (EIP-8037) to shape Arbitrum's later implementation.

### E2. OP Stack chains (Base, Unichain), in the scaffold but not wired

- **Jovian** execution-engine changes ([spec](https://specs.optimism.io/protocol/jovian/exec-engine.html)):
  - a configurable **minimum base fee**, "to reduce the duration of priority-fee auctions";
  - a DA-footprint block limit;
  - an operator-fee formula update;
  - **precompile input size restrictions**.

  Activation dates per chain were **not read**: check each chain's upgrade notice.
- **Unichain**: the first L2 with Rollup-Boost and TEE block building on mainnet
  ([Flashbots, 2025-05-02](https://collective.flashbots.net/t/the-first-l2-tee-block-builder-is-live-on-unichain-mainnet/4917)).
  Block building is external and runs in a TEE, so ordering assumptions differ from Arbitrum's sequencer PGA.

### E3. The Solidity compiler's direction

- "[The Road to Core Solidity](https://www.soliditylang.org/blog/2025/10/21/the-road-to-core-solidity/)"
  (2025-10-21), discussed in the
  [roadmap feedback thread](https://forum.soliditylang.org/t/call-for-feedback-the-long-term-solidity-roadmap/3530).
  The long-term trajectory is toward **1.0** and a new "Core Solidity", with IR-pipeline backend work and **planned
  breaking changes** during the transition.
  - The team holds a public language-design call every Wednesday, 15:00 CET/CEST.
  - The post is a direction, not a release: no 0.9.0 date was found.
- **Repo link:** Solady deferred removing `virtual` from its modifiers until "Solidity 0.9.0 is released" (Solady
  issue #1519, recorded in CLAUDE.md §2). Re-check both when 0.9.0 ships.

### E4. Account abstraction

- **EntryPoint v0.9.0** ([release, 2025-11-16](https://github.com/eth-infinitism/account-abstraction/releases/tag/v0.9.0)):
  - addresses: `0x433709009B8330FDa32311DF1C2AFA402eD8D009`, with SenderCreator `0x0A630a99Df908A81115A3022927Be82f9299987e`;
  - **ABI-compatible with v0.7 and v0.8**;
  - a new `paymasterSignature` field, which lets a paymaster sign after the wallet;
  - UserOp validity ranges can be expressed in **block numbers**.

  Its own warning: verify the address **and code hash** against the audit report before switching. Interface
  compatibility is not ERC-165 compatibility: a v0.7-built paymaster that checks the v0.7 interface id fails against
  v0.9 (repo finding, T-208).

### E5. Uniswap v4 hooks

[Trail of Bits, "Building secure Uniswap v4 hooks" (2026-07-30)](https://blog.trailofbits.com/2026/07/30/building-secure-uniswap-v4-hooks/)
lists seven failure classes:
1. anyone can call your hook;
2. treating any pool as legitimate;
3. custom accounting leaks value;
4. right logic, wrong hook;
5. **address bits are part of the API**;
6. hook failures can block pool actions;
7. state can change during a callback sequence.

Pair it with the `v4-security-foundations` skill's catalogue.

### E6. MEV and block-building research (context, not build targets)

- **FOCIL**, [EIP-7805](https://eips.ethereum.org/EIPS/eip-7805): fork-choice enforced inclusion lists. **Draft**, not
  in Glamsterdam's schedule ([research](https://ethresear.ch/t/fork-choice-enforced-inclusion-lists-focil-a-simple-committee-based-inclusion-list-proposal/19870)).
- **Arbitrage origin attribution** ([ethresear.ch](https://ethresear.ch/t/the-origins-of-mev-systematic-attribution-of-arbitrage-opportunity-creation-at-scale/25124))
  attributes arbitrage opportunities to the transactions that created them. It is relevant to backrun-only lane design.
- **Cross-chain arbitrage detection** ([Flashbots, 2025-07-22](https://collective.flashbots.net/t/detecting-cross-chain-arbitrages-in-the-wild/5107)),
  covering nine chains. Its methodology is reproducible. Relevant to decision 0015's read-only cross-chain ingest.

### E7. Searched but not resolved on 2026-10-10

- Forkcast (`forkcast.org/upgrade/glamsterdam`) renders client-side, so no content was read. Use EIP-7773 instead.
- No usable hit for: gov.optimism.io interop, Base Flashblocks, gov.uniswap.org hook design, a Solidity 0.9.0 thread,
  OpenZeppelin 6.0 roadmap, Solady discussions, Robinhood chain docs, Stylus–Solidity interop.
- HyperEVM: the official "Interacting with HyperCore" page was fetched but **not analysed**. Read it before any
  HyperEVM work.

## Refresh procedure

1. For each number, open `https://eips.ethereum.org/EIPS/eip-<n>` and read the status badge and the `discussionUrl`
   in the page's JSON-LD.
2. Re-read the meta EIPs: 7773 for Glamsterdam, and the next fork's meta EIP when it exists.
3. For each target L2, read its upgrade source and probe on-chain.
   - Arbitrum: the activation table at docs.arbitrum.foundation/network-upgrades, plus the ArbOS release notes.
   - OP Stack chains: each chain's upgrade notice.
   - Then probe the opcodes and precompiles on-chain, and record the block and the result.
4. Update the date in the provenance block. Never carry a status forward without re-reading it.
