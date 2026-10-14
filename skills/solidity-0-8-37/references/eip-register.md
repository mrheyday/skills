# EIP / ERC Register (verified index)

> Numbers, titles and statuses below were read from the official indexes at https://eips.ethereum.org/all and
> https://eips.ethereum.org/erc on 2026-10-06. Status moves: re-check at https://eips.ethereum.org/EIPS/eip-<n>
> (ERCs also mirror to https://ercs.ethereum.org/ERCS/erc-<n>) before relying on a non-Final entry.
> The one-line notes are implementation guidance, not quotations from the specs.

Status meanings (EIP-1): **Final** = settled standard; **Last Call** = final review window; **Review**/**Draft** = still
changing; **Stagnant** = inactive for 6+ months; **Withdrawn** = abandoned. Build against Final unless the user
explicitly wants a draft, and say so when you do.

## Token standards

| # | Title | Status | Why it matters when writing Solidity |
|---|---|---|---|
| [20](https://eips.ethereum.org/EIPS/eip-20) | Token Standard | Final | The ERC-20 interface; `transfer`/`approve` return `bool` — check it. Non-standard tokens (USDT) omit the return value: use a safe-transfer wrapper. |
| [721](https://eips.ethereum.org/EIPS/eip-721) | Non-Fungible Token Standard | Final | NFTs; `safeTransferFrom` calls `onERC721Received` on contracts — a re-entrancy surface in mint/transfer flows. |
| [1155](https://eips.ethereum.org/EIPS/eip-1155) | Multi Token Standard | Final | Multi-token; batch transfers call `onERC1155BatchReceived`. Same re-entrancy caveat as 721. |
| [6909](https://eips.ethereum.org/EIPS/eip-6909) | Minimal Multi-Token Interface | Final | Lean multi-token alternative to 1155 with no callbacks — fewer re-entrancy surfaces. |
| [777](https://eips.ethereum.org/EIPS/eip-777) | Token Standard | Final | Legacy token with `tokensReceived` hooks via ERC-1820; the hook has caused real re-entrancy incidents. Avoid for new work. |
| [4626](https://eips.ethereum.org/EIPS/eip-4626) | Tokenized Vaults | Final | Tokenized vault accounting; `convertTo*` vs `preview*` differ (fees). Rounding must favour the vault. |
| [7540](https://eips.ethereum.org/EIPS/eip-7540) | Asynchronous ERC-4626 Tokenized Vaults | Final | Async (request/claim) extension of 4626 for vaults that cannot settle synchronously. |
| [3156](https://eips.ethereum.org/EIPS/eip-3156) | Flash Loans | Final | Flash-loan interface; the borrower callback must return the magic value. |
| [2981](https://eips.ethereum.org/EIPS/eip-2981) | NFT Royalty Standard | Final | Royalty lookup (`royaltyInfo`); informational to marketplaces, not enforced on-chain. |

## Signatures and approvals

| # | Title | Status | Why it matters when writing Solidity |
|---|---|---|---|
| [191](https://eips.ethereum.org/EIPS/eip-191) | Signed Data Standard | Final | Prefixed signed-data; the `\x19` prefix scheme 712 builds on. |
| [712](https://eips.ethereum.org/EIPS/eip-712) | Typed structured data hashing and signing | Final | Typed structured data. Bind the domain separator to `block.chainid` at use time, or recompute on fork; include a nonce and deadline. |
| [2612](https://eips.ethereum.org/EIPS/eip-2612) | Permit Extension for EIP-20 Signed Approvals | Final | `permit` for gasless approvals on ERC-20. Front-runnable by design — never assume exclusivity. |
| [1271](https://eips.ethereum.org/EIPS/eip-1271) | Standard Signature Validation Method for Contracts | Final | `isValidSignature` for contract (smart-account) signers. `ecrecover` alone rejects them. |
| [5267](https://eips.ethereum.org/EIPS/eip-5267) | Retrieval of EIP-712 domain | Final | `eip712Domain()` so off-chain tooling can discover your domain without hardcoding. |
| [7739](https://eips.ethereum.org/EIPS/eip-7739) | Readable Typed Signatures for Smart Accounts | Draft | Readable nested typed signatures for smart accounts (not Final; check status before relying on it). |

## Interfaces, errors, conventions

| # | Title | Status | Why it matters when writing Solidity |
|---|---|---|---|
| [165](https://eips.ethereum.org/EIPS/eip-165) | Standard Interface Detection | Final | `supportsInterface`; `type(I).interfaceId` in Solidity gives the XOR of the interface's own selectors. |
| [6093](https://eips.ethereum.org/EIPS/eip-6093) | Custom errors for commonly-used tokens | Final | Canonical custom errors for ERC-20/721/1155 — reuse these names instead of inventing your own. |
| [7528](https://eips.ethereum.org/EIPS/eip-7528) | ETH (Native Asset) Address Convention | Final | `0xEeee...EEeE` as the pseudo-address for native ETH in token-agnostic interfaces. |
| [55](https://eips.ethereum.org/EIPS/eip-55) | Mixed-case checksum address encoding | Final | Mixed-case checksummed addresses — what tooling displays and validates. |

## Proxies, storage layout, upgrades

| # | Title | Status | Why it matters when writing Solidity |
|---|---|---|---|
| [1167](https://eips.ethereum.org/EIPS/eip-1167) | Minimal Proxy Contract | Final | Minimal proxy (clone) bytecode; immutable implementation, cheap deploys. |
| [1967](https://eips.ethereum.org/EIPS/eip-1967) | Proxy Storage Slots | Final | Standard slots for implementation/admin/beacon so explorers can resolve a proxy. |
| [7201](https://eips.ethereum.org/EIPS/eip-7201) | Namespaced Storage Layout | Final | Namespaced storage (`erc7201(id)` is a Solidity built-in since 0.8.x) — avoids collisions in upgradeable and modular contracts. |
| [2535](https://eips.ethereum.org/EIPS/eip-2535) | Diamonds, Multi-Facet Proxy | Final | Diamond multi-facet proxy with per-selector routing. |
| [5202](https://eips.ethereum.org/EIPS/eip-5202) | Blueprint contract format | Final | Blueprint (initcode-container) contract format for factory deploys. |

## Accounts and abstraction

| # | Title | Status | Why it matters when writing Solidity |
|---|---|---|---|
| [4337](https://eips.ethereum.org/EIPS/eip-4337) | Account Abstraction Using Alt Mempool | Final | EntryPoint/UserOperation account abstraction via an alt mempool; validation is storage-restricted. |
| [7702](https://eips.ethereum.org/EIPS/eip-7702) | Set Code for EOAs | Final | EOAs can set code — `msg.sender` may now be an EOA *with* code. `tx.origin == msg.sender` and `code.length == 0` are no longer EOA tests. |
| [5792](https://eips.ethereum.org/EIPS/eip-5792) | Wallet Call API | Final | Wallet batched-call API (`wallet_sendCalls`). |
| [7579](https://eips.ethereum.org/EIPS/eip-7579) | Minimal Modular Smart Accounts | Draft | Modular smart-account interface (Draft — verify status). |
| [6900](https://eips.ethereum.org/EIPS/eip-6900) | Modular Smart Contract Accounts | Draft | Modular account plugin interface (Draft — verify status). |

## EVM features the compiler gates on

| # | Title | Status | Why it matters when writing Solidity |
|---|---|---|---|
| [1153](https://eips.ethereum.org/EIPS/eip-1153) | Transient storage opcodes | Final | `TSTORE`/`TLOAD` — Solidity `transient` state variables; available from the cancun target onward. |
| [5656](https://eips.ethereum.org/EIPS/eip-5656) | MCOPY - Memory copying instruction | Final | `MCOPY`; cancun onward. |
| [3855](https://eips.ethereum.org/EIPS/eip-3855) | PUSH0 instruction | Final | `PUSH0`; shanghai onward — smaller code. |
| [7939](https://eips.ethereum.org/EIPS/eip-7939) | Count leading zeros (CLZ) opcode | Final | `CLZ` builtin in Yul; **osaka** onward, the 0.8.37 default target. |
| [7843](https://eips.ethereum.org/EIPS/eip-7843) | SLOTNUM opcode | Review | `SLOTNUM` / `block.slotnum`; amsterdam (experimental) only — not Final, do not rely on it. |
| [4844](https://eips.ethereum.org/EIPS/eip-4844) | Shard Blob Transactions | Final | Blob transactions; `blobhash(i)` and `block.blobbasefee`. |
| [7516](https://eips.ethereum.org/EIPS/eip-7516) | BLOBBASEFEE instruction | Final | `BLOBBASEFEE` opcode behind `block.blobbasefee`. |
| [3198](https://eips.ethereum.org/EIPS/eip-3198) | BASEFEE opcode | Final | `BASEFEE` behind `block.basefee`; london onward. |
| [4399](https://eips.ethereum.org/EIPS/eip-4399) | Supplant DIFFICULTY opcode with PREVRANDAO | Final | `PREVRANDAO` replaces `DIFFICULTY`; `block.difficulty` is a deprecated alias from paris. |
| [6049](https://eips.ethereum.org/EIPS/eip-6049) | Deprecate SELFDESTRUCT | Final | Deprecates `SELFDESTRUCT` — the reason Solidity warns on it since 0.8.18. |
| [170](https://eips.ethereum.org/EIPS/eip-170) | Contract code size limit | Final | 24,576-byte deployed-code limit; the cause of most 'contract too large' failures. |
| [2929](https://eips.ethereum.org/EIPS/eip-2929) | Gas cost increases for state access opcodes | Final | Cold/warm state-access gas — why repeated SLOADs differ and why Foundry's call isolation changes gas. |
| [2930](https://eips.ethereum.org/EIPS/eip-2930) | Optional access lists | Final | Access lists to pre-warm slots/addresses. |
| [1559](https://eips.ethereum.org/EIPS/eip-1559) | Fee market change for ETH 1.0 chain | Final | Base fee + priority fee; `tx.gasprice` is the effective price. |
| [7623](https://eips.ethereum.org/EIPS/eip-7623) | Increase calldata cost | Final | Raised calldata cost — affects calldata-heavy designs. |
| [7825](https://eips.ethereum.org/EIPS/eip-7825) | Transaction Gas Limit Cap | Final | Per-transaction gas-limit cap — bounds what a single tx can do. |

## Other primitives worth knowing

| # | Title | Status | Why it matters when writing Solidity |
|---|---|---|---|
| [7951](https://eips.ethereum.org/EIPS/eip-7951) | Precompile for secp256r1 Curve Support | Final | secp256r1 (P-256) precompile — passkey/WebAuthn signers on-chain. |
| [2718](https://eips.ethereum.org/EIPS/eip-2718) | Typed Transaction Envelope | Final | Typed transaction envelope; all newer tx types build on it. |
| [137](https://eips.ethereum.org/EIPS/eip-137) | Ethereum Domain Name Service - Specification | Final | ENS resolution. |
| [1820](https://eips.ethereum.org/EIPS/eip-1820) | Pseudo-introspection Registry Contract | Final | Pseudo-introspection registry used by ERC-777. |

## Using this register

- Cite the number *and* the status when you recommend a standard: "ERC-4626 (Final)".
- Prefer an audited implementation (Solady, OpenZeppelin) over hand-rolling a standard; if the repo profile pins
  Solady, use it and record provenance.
- When a standard defines errors (ERC-6093) or interface ids (ERC-165), reuse the canonical names rather than
  inventing parallel ones — integrators decode against the published selectors.
- A status here is a snapshot. If the answer depends on whether something is Final, re-fetch the EIP page.
