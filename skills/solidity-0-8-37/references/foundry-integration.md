# Foundry Integration — testing hygiene and fork conventions

> Sources, all read 2026-10-06: https://www.getfoundry.sh/best-practices (page modified 2026-09-29),
> https://www.getfoundry.sh/forge/testing (2026-09-29), https://www.getfoundry.sh/guides/fork-testing (2026-10-05),
> https://www.getfoundry.sh/reference/cheatcodes/overview and .../create-fork (2026-07-20).
> Foundry's docs moved to getfoundry.sh; `book.getfoundry.sh` redirects there. Flags and cheatcode signatures
> move between releases — when a result depends on one, confirm with `forge --version` and `forge test --help`
> rather than trusting this snapshot.

A passing unit test proves only what the test asserts. Fork tests against real addresses at a pinned block are
what turn "this should work against the live protocol" into evidence. This file covers both halves: the test
conventions Foundry itself documents, and how to fork reproducibly.

## Contents
1. foundry.toml baseline
2. Test file conventions and naming
3. Assertions: reverts, events, access control
4. Fuzz, invariant, table, brutalized, mutation, symbolic
5. Fork testing: flag vs cheatcodes, pinning, caching, multi-fork
6. Isolation, gas and traces
7. Scripts and key hygiene
8. Pre-ship gate
9. What a fork test does and does not prove

---

## 1. foundry.toml baseline

```toml
[profile.default]
solc = "0.8.37"
evm_version = "osaka"          # 0.8.37's default; set it explicitly so the pin is visible in the repo
via_ir = true
optimizer = true
optimizer_runs = 1_000_000
src = "src"; test = "test"; script = "script"

[fmt]
line_length = 120              # matches the Solidity style guide
tab_width = 4
bracket_spacing = true

[lint]
severity = "warning"

[fuzz]
runs = 1000
max_test_rejects = 65536

[rpc_endpoints]                # aliases; URLs come from env, never committed literals
arbitrum = "${ARBITRUM_RPC_URL}"
mainnet  = "${MAINNET_RPC_URL}"

[profile.ci.fuzz]
runs = 10_000
```

Inspect what actually resolved with `forge config --json` instead of assuming defaults. On "stack too deep",
restructure first — group locals into structs, split the function, add block scoping — and treat `via_ir` as a
compiler setting you chose, not a workaround you reached for.

## 2. Test file conventions and naming

Tests live in `test/`, end in `.t.sol`, inherit `forge-std/Test.sol`, and mirror `src/`
(`src/Vault.sol` → `test/Vault.t.sol`; `src/governance/Governor.sol` → `test/governance/Governor.t.sol`).

| Pattern | Use |
|---|---|
| `test_Description` | standard test (`test_TransferUpdatesBalances`) |
| `testFuzz_Description` | fuzz test (`testFuzz_TransferAnyAmount`) |
| `test_RevertWhen_Condition` / `test_RevertIf_Condition` | expected revert (`test_RevertWhen_InsufficientBalance`) |
| `testFork_Description` | runs against a forked network |
| `invariant_Property` | stateful invariant |
| `check_*` / `prove_*` | symbolic (only discovered with `--symbolic`) |
| `table*Test` + `fixture*` | table test and its dataset |

- `setUp()` runs before every test; state does not leak between tests.
- Group related tests into separate contracts in one file (`TokenTransferTest`, `TokenApprovalTest`) so
  `--match-contract` is useful.
- Expose internals through a harness in `test/harnesses/` (`exposed_mint`) rather than widening visibility in
  production code. A `public` function that exists only for tests is a defect in the contract.
- Named imports only: `import {Test} from "forge-std/Test.sol";`.
- `makeAddr("alice")` for labelled actors, `vm.label(addr, "USDC")` for readable traces, `vm.deal` for ETH,
  `deal(token, who, amt)` for ERC-20 balances (`deal(..., true)` also adjusts `totalSupply`).
- Prefer `bound(x, lo, hi)` to `vm.assume(...)`: `assume` discards runs and can exhaust `max_test_rejects`,
  `bound` reshapes them. Bound independent parameters first, then dependent ones.

## 3. Assertions

```solidity
// custom error, no args — assert the selector, not a string
vm.expectRevert(Vault.ZeroAmount.selector);
vault.withdraw(0);

// custom error with args — checks the full revert data
vm.expectRevert(abi.encodeWithSelector(Vault.InsufficientBalance.selector, 5 ether, 1 ether));
vault.withdraw(5 ether);

// panic from checked arithmetic
vm.expectRevert(stdError.arithmeticError);

// events: set the expectation immediately before the emitting call
vm.expectEmit(true, true, true, true);   // topic1, topic2, topic3, data
emit Vault.Deposited(alice, 1 ether);
vault.deposit{value: 1 ether}();
```

`vm.expectRevert` applies to the **next** call only. Matching a string passes for any path sharing that
message; matching a selector does not — which is the point of the 0.8.37 custom-error style. Always test
access control (`vm.prank(attacker)` + expected revert) and edge values (zero, `type(uint256).max`, empty
arrays, self-as-counterparty).

The cheatcode address is `0x7109709ECfa91a80626fF3989D68f67F5b1DD12D`; exclude it from fuzzed addresses.

## 4. Beyond unit tests

- **Fuzz** — any parameterised test is fuzzed (256 runs default). Assert relationships, not magic numbers.
- **Invariant** — `invariant_*` plus handler contracts modelling allowed actions; write these for anything
  holding value ("total shares always equals the sum of balances").
- **Table** (v1.3+) — `tableSumsTest(TestCase memory sums)` driven by `fixtureSums()`. The parameter name must
  match the fixture name or the run fails with `Table test should have fixtures defined`.
- **Brutalized** (`--brutalize`) — recompiles `src/` with dirty upper bits on narrow casts, dirtied scratch
  space (`0x00`–`0x3f`) and a misaligned free-memory pointer. Mandatory for anything using inline assembly,
  narrow `uint`/`bytesN`/`address` casts, or manual memory: a pass under `forge test` and a fail under
  `--brutalize` means the code assumes cleanliness the EVM does not guarantee. Cannot be combined with `--mutate`.
- **Mutation** (`--mutate`) — measures whether the suite would catch a small code change. A surviving mutant is
  untested behaviour, not noise.
- **Symbolic** (`--symbolic`, `check_*`/`prove_*`, needs `z3`) — MVP. `PASS` is scoped to the modeled semantics
  and configured bounds; `Incomplete` means "not established" and must never be reported as proof.
- **Gas** — `forge test --gas-report`; `forge snapshot` for regressions.

## 5. Fork testing

Two mechanisms, and they are not interchangeable.

### Whole-run fork — the `--fork-url` flag

```bash
forge test --fork-url "$ARBITRUM_RPC_URL"                                 # latest block — NOT reproducible
forge test --fork-url "$ARBITRUM_RPC_URL" --fork-block-number 250000000   # pinned — do this
forge test --fork-url "$RPC" --fork-block-number N --fork-state-by-number # RPC can't serve state by hash
forge test --fork-url "$RPC" --fork-retry-backoff 1000                    # initial retry delay, ms
forge test --fork-url "$RPC" --etherscan-api-key "$KEY"                   # decode traces via Etherscan
```

Every test in the run executes on that fork, so unit tests burn RPC calls, offline runs fail, and the fork
target is invisible from the source. Good for ad-hoc investigation; a poor foundation for a suite. The older
Foundry Book best-practices page stated this as a rule ("When writing fork tests, do not use the `--fork-url`
flag… define `[rpc_endpoints]` and use the forking cheatcodes"); the current consolidated best-practices page
no longer carries that line, and the fork-testing guide documents the flag as the basic approach. Both agree on
what actually matters: **pin the block**. Prefer in-test cheatcodes for anything that lives in the repo.

`fork_block_number` and `eth_rpc_url` can also be set per profile in `foundry.toml`.

### In-test forks — cheatcodes

```solidity
uint256 forkId = vm.createFork("arbitrum");                 // alias from [rpc_endpoints], or a URL
uint256 pinned = vm.createFork("arbitrum", 250_000_000);    // pinned to a block
uint256 atTx   = vm.createFork("arbitrum", txHash);         // replays txs preceding txHash in its block
vm.selectFork(forkId);                                      // createFork does NOT select
uint256 active = vm.activeFork();
vm.rollFork(250_100_000);                                   // move the active fork's block
vm.makePersistent(address(helper));                         // carry an address across fork switches
```

`vm.createSelectFork(...)` does create + select in one call — but it creates a **new** fork every time it is
called, each from clean state. To switch back and forth while keeping state, call `createFork` once per chain,
keep the ids, and `selectFork` between them. Each fork is a standalone EVM with independent storage; the test
contract itself is persistent across switches, other contracts you deployed are not unless made persistent.

A fork test that carries its own context:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity 0.8.37;

import {Test} from "forge-std/Test.sol";
import {IERC20} from "forge-std/interfaces/IERC20.sol";

/// @notice Fork: Arbitrum One (42161), block pinned for reproducibility and RPC caching.
contract UsdcForkTest is Test {
    uint256 internal constant ARBITRUM_ONE = 42161;
    uint256 internal constant FORK_BLOCK = 250_000_000;
    /// @dev Verify this address against the issuer's published deployment before trusting any result.
    IERC20 internal constant USDC = IERC20(0xaf88d065e77c8cC2239327C5EDb3A432268e5831);

    function setUp() public {
        vm.createSelectFork(vm.rpcUrl("arbitrum"), FORK_BLOCK);
        assertEq(block.chainid, ARBITRUM_ONE, "wrong chain: check the RPC alias");
        assertEq(block.number, FORK_BLOCK, "fork not pinned");
        vm.label(address(USDC), "USDC");
    }

    function testFork_UsdcHasSixDecimals() public view {
        assertEq(USDC.decimals(), 6);
    }
}
```

Conventions that make a fork test worth citing:

- **Pin the block.** Pinning makes the run deterministic and lets Foundry cache RPC responses under
  `~/.foundry/cache/rpc/<chain>/<block>/` — the first run is slow, later runs are fast. An unpinned fork
  re-runs against whatever the chain looks like today: a pass proves nothing repeatable.
- **Assert the chain id in `setUp`.** It turns "wrong RPC in the environment" into a test failure instead of a
  confidently wrong proof.
- **Treat every hardcoded address as a factual claim.** Check it (`cast code` non-empty, `cast call` returns the
  expected `symbol()`/`decimals()`) or cite the protocol's published deployment list, and record where it came
  from. A fork test pointed at the wrong address proves nothing while looking authoritative.
- **Use aliases, not URLs in source.** `[rpc_endpoints]` + `vm.rpcUrl("arbitrum")` keeps keys out of the repo.
- **Name them `testFork_*` or keep them in `test/fork/`** so offline and fast-CI runs can skip them:
  `forge test --no-match-test testFork` or `--no-match-path "test/fork/**"`.
- **Fuzz on a fork burns RPC.** Bound tightly, lower `runs`, never fuzz against `latest`.
- **Prefer forks to mocks for deployed code.** A mock encodes your assumption about the protocol; the fork runs
  the protocol. The `foundry-toolchain` GitHub Action caches RPC responses in CI by default.
- **Stale cache after an upgrade:** `forge clean`, or remove `~/.foundry/cache/rpc`.

Note `--fork-state-by-number` has weaker reorg protection and skips the disk state cache; transaction replay
still requires hash-based reads.

## 6. Isolation, gas and traces

Forge runs with **call isolation on by default**: each top-level external call in a test executes as its own
transaction in its own context. Gas is accounted per call and accounts/slots can be charged cold again on
repeated calls, so a test function is not equivalent to one real transaction. If a test deliberately asserts
warm-slot behaviour across repeated calls, use `--no-isolate` / `isolate = false` and say in the test why.

Verbosity: `-vv` logs, `-vvv` traces for failures (start here — the backtrace names the revert site),
`-vvvv` traces for everything, `-vvvvv` adds storage changes. Filter with `--match-test` / `--match-contract` /
`--match-path` and their `--no-match-*` inverses.

## 7. Scripts and key hygiene

One concern per script, orchestrated from `Deploy.s.sol`. Read config with `vm.envAddress` / `vm.envOr`; never
hardcode addresses or keys. Wrap state changes in `vm.startBroadcast()` / `vm.stopBroadcast()` and log the
deployed address, `block.chainid` and `msg.sender`.

Keys: encrypted keystore (`cast wallet import deployer --interactive`, then `--account deployer`) for testnets;
hardware wallet (`--ledger`) for mainnet; Anvil's published default keys only against local Anvil, never a
public network. `.env` and `.env.*` stay out of version control; `.env.example` documents variable names only.

## 8. Pre-ship gate

```bash
forge fmt --check
forge lint
forge build                       # zero warnings — fixed in code, not suppressed
forge test -vvvv                  # at least once, with full traces
forge test --brutalize            # if assembly, narrow casts or manual memory are involved
forge test --match-test testFork  # with RPC env set, blocks pinned
forge snapshot                    # gas regression baseline
```

Foundry's own list adds: verify deployments with the exact compiler settings used to build them. The only
acceptable suppression is a narrow, justified `// forge-lint: disable-next-line(<rule-id>)`.

## 9. What a fork test does and does not prove

- **Proves:** the integration behaves this way against that chain's state **at that block**, under Foundry's EVM,
  for the addresses actually exercised.
- **Does not prove:** behaviour at head, after a protocol upgrade, under different liquidity, under adversarial
  ordering or MEV, or anything about code paths the test did not touch.
- **So report:** chain id, pinned block, addresses, test names, commit, and the exact command. Under
  `references/repo-profile.md` that record *is* the proof artifact; "tests pass" without it is not evidence, and
  a mock-only unit test never establishes a behavioural claim about deployed code.
