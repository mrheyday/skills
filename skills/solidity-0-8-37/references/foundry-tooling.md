# Foundry Tooling — Anvil, cast, chisel, debugger, deps, CI, deployment

> Source: condensed, corrected and re-organised (modified) from `tenequm/foundry-solidity` v0.2.5
> (https://github.com/tenequm/skills/tree/main/skills/foundry-solidity), licensed Apache-2.0 per that skill folder's
> `LICENSE.txt` (the repo-root `LICENSE` is MIT, (c) 2025 Mykhaylo Kolesnik; ClawHub lists MIT-0). Written against
> Foundry 1.5.0 / Solidity 0.8.30 (Nov 2025). Test conventions, fork pinning, call isolation and the pre-ship gate
> live in `foundry-integration.md` and are not repeated here. **Nothing below was run**: no Foundry binary was
> available when this was merged. Flags move between releases — confirm with `forge --version` and `<cmd> --help`
> before relying on one. Where this file and `foundry-integration.md` / `repo-profile.md` disagree, those win.

## Contents
1. Anvil (local node, forks, state control)
2. cast (decode, encode, inspect, replay)
3. chisel (REPL)
4. Debugger and traces
5. forge-std APIs worth knowing
6. Invariant handlers
7. Dependencies (submodules, Soldeer)
8. Config keys beyond the baseline
9. CI (GitHub Actions)
10. Deployment scripts and verification
11. Deliberately not imported

## 1. Anvil

```bash
anvil --fork-url "$RPC" --fork-block-number N        # pinned fork; unpinned is not reproducible
anvil --block-time 12 | --no-mining                  # interval / manual mining
anvil --auto-impersonate                             # send from any address with --unlocked
anvil --dump-state s.json ; anvil --load-state s.json
```

State control by JSON-RPC (`cast rpc <method> <args>`): `anvil_impersonateAccount` / `anvil_stopImpersonatingAccount`,
`anvil_setBalance` (hex wei), `anvil_setCode`, `anvil_setStorageAt`, `anvil_setNonce`, `anvil_mine`, `evm_mine`,
`evm_setAutomine`, `evm_setIntervalMining`, `evm_snapshot` / `evm_revert`, `evm_setNextBlockTimestamp`,
`evm_increaseTime`, `anvil_reset`. In Solidity tests the equivalents are `vm.deal`, `vm.etch`, `vm.store`,
`vm.setNonce`, `vm.warp`, `vm.roll`, `vm.snapshot`/`vm.revertTo`, `vm.prank`.

- Anvil's default accounts and mnemonic are public: use them only against local Anvil, never a public network.
- Anvil runs a standard EVM. On an Arbitrum fork, do not assume ArbOS precompiles (e.g. ArbSys) or L1/L2 gas
  accounting are modelled — check what your Foundry version supports; otherwise gas and precompile-dependent
  results are unproven (see `foundry-integration.md` §9).
- Impersonation of a real holder ("whale") is a fact claim about that address at that block: verify the
  balance with `cast call` at the pinned block and record the source.

## 2. cast

```bash
cast sig "transfer(address,uint256)"          # selector from signature
cast 4byte 0xa9059cbb                         # signature from selector (public database — treat as a hint)
cast calldata "f(uint256)" 1                  # encode a call
cast calldata-decode "f(uint256)" 0x...       # decode calldata
cast abi-encode "constructor(string,uint256)" "T" 1   # encode args (add --packed for packed)
cast abi-decode "balanceOf(address)(uint256)" 0x...   # decode return data
cast storage $ADDR <slot> --rpc-url $RPC      # raw slot (proxy impl slot: ERC-1967, see eip-register.md)
cast index address $KEY 0                     # mapping slot for key at base slot 0
cast call $C "f()(uint256)" --block N         # historical read
cast tx $HASH ; cast receipt $HASH ; cast block N --field timestamp ; cast logs --from-block A --to-block B --address $C
cast run $HASH                                # replay a mined tx locally with a trace (add --debug)
cast estimate $C "f()" ; cast compute-address $DEPLOYER --nonce N ; cast create2 --starts-with 0x1234 --init-code 0x...
cast to-wei 1 ether ; cast from-wei ... ; cast to-dec 0x64 ; cast to-hex 100
cast wallet new ; cast wallet import NAME --interactive ; cast send ... --account NAME
```

`cast send`, `forge script --broadcast` and `forge create --broadcast` move real funds on a live RPC. Rehearse on
Anvil or a labelled fork first. Prefer `--account`/`--ledger` over `--private-key` (keys in shell history).

## 3. chisel

`chisel` is a Solidity REPL (`--fork-url`/`--fork-block-number` supported; reads `foundry.toml`). Use it for a
quick integer-rounding check, `keccak256`/`abi.encode` output, or a single `eth_call`-style read on a fork.
Session commands: `!help`, `!source`, `!clear`, `!save <name>`, `!export`; `chisel list` / `chisel load <name>`.
It is a scratchpad, not evidence — put anything that matters in a test.

## 4. Debugger and traces

```bash
forge test --debug --match-test test_X        # interactive debugger
forge script script/X.s.sol --debug
cast run --debug $HASH
```

`vm.breakpoint("a")` in a test, then `'a` in the debugger to jump. Keys: `j`/`k` step, `c`/`C` next/previous
CALL, `g`/`G` start/end, `t` stack labels, `m` memory as UTF-8, `h` help, `q` quit. Verbosity levels are in
`foundry-integration.md` §6. Workflow: `-vvv` on the failing test → find the red (reverting) frame → `--debug` or
a targeted `console.log` only if the trace is not enough. `forge test -vvvv > trace.txt` for a saved trace.
Trace failure names: `OOG` (out of gas), `Revert`, `InvalidFEOpcode`, `NotActivated` (opcode not enabled for the
configured `evm_version`).

## 5. forge-std APIs worth knowing

Not exhaustive; `foundry-integration.md` §2–3 covers the common ones.

- Storage without knowing the slot: `using stdStorage for StdStorage;` then
  `stdstore.target(addr).sig("balanceOf(address)").with_key(user).checked_write(amt)` (`checked_write_int` for
  signed; `.depth(n)` for struct fields). Prefer `deal(token, who, amt)` where it works.
- Cheats: `hoax(sender, give)` / `startHoax`, `skip(s)` / `rewind(s)`, `deployCodeTo("X.sol", args, addr)`,
  `deployCode(...)`, `makeAddrAndKey`, `makeAccount`, `noGasMetering` modifier,
  `skipWhenForking` / `skipWhenNotForking`, `isFork()`.
- Fuzz hygiene: `assumeNotZeroAddress`, `assumeNotPrecompile`, `assumeNotForgeAddress`, `assumePayable` /
  `assumeNotPayable`, `assumeNotBlacklisted(token, addr)`, `boundPrivateKey`.
- Reverts and calls: `vm.expectPartialRevert(selector)` (selector match, ignores args), `vm.expectCall(...)`,
  `vm.recordLogs()` + `vm.getRecordedLogs()`; `stdError.arithmeticError`, `divisionError`, `indexOOBError`, …
- Gas sections: `vm.startSnapshotGas("name")` … `vm.stopSnapshotGas()`; `vm.lastCallGas()`.
- Addresses: `computeCreateAddress`, `computeCreate2Address(salt, initCodeHash[, deployer])`, `hashInitCode`.
  Constants: `DEFAULT_SENDER`, `CREATE2_FACTORY` (0x4e59…956C), `MULTICALL3_ADDRESS` (0xcA11…CA11) — confirm
  with `cast code` on the target chain.
- Data: `stdJson` / `stdToml` (`readUint`, `readAddress`, `readUintArray`, `keyExists`, `parseRaw`,
  `serialize`/`write`); `getChain("arbitrum")` / `setChain` via StdChains.
- Multi-fork: see `foundry-integration.md` §5; `makePersistent` for helper contracts.
- Assertions: `assertApproxEqAbs(a, b, maxDelta)` / `assertApproxEqRel(a, b, maxPercentDelta)` (1e18 = 100%), the `*Decimal`
  variants (print with decimals), `assertEqCall(target, calldataA, calldataB)` for differential checks, `assertNotEq`,
  array `assertEq`.
- Token setup: `deal(token, to, amt[, adjustTotalSupply])`, `dealERC721`, `dealERC1155`; batch balances with
  `getTokenBalances(token, addrs)` (Multicall3, so it needs that contract on the fork).
- `Script` inherits `StdCheatsSafe` only (no `deal`/`hoax`); test-only cheats belong in `Test`.
- Fixtures: an array or function named `fixture<ParamName>` supplies fixed values for that fuzz parameter.
- Invariant targeting: `targetContract/Sender/Selector/Artifact` and the matching `exclude*`; selector targeting uses
  `FuzzSelector{addr, selectors}`.
- Math: `stdMath.abs/delta/percentDelta`; `console2` has the same API as `console` with less bytecode overhead.

## 6. Invariant handlers

Fuzz a **handler**, not the target: bound every input, keep actors in an array, track ghost variables, and
assert against the real contract.

```solidity
contract VaultHandler is Test {
    Vault internal vault;
    address[] internal actors;
    uint256 public ghostDeposited;

    function deposit(uint256 actorSeed, uint256 amount) external {
        address actor = actors[bound(actorSeed, 0, actors.length - 1)];
        amount = bound(amount, 1, 1e24);
        deal(address(vault.asset()), actor, amount);
        vm.startPrank(actor);
        vault.asset().approve(address(vault), amount);
        vault.deposit(amount, actor);
        vm.stopPrank();
        ghostDeposited += amount;
    }
}
// in the invariant test's setUp: targetContract(address(handler));
// optional: targetSelector(FuzzSelector({addr: address(handler), selectors: sels})); excludeSender(address(0));
```

Config: `[invariant] runs`, `depth`, `fail_on_revert` (false lets reverting calls through; true makes every handler
revert a failure), `shrink_run_limit`. Start with one simple invariant, then raise depth/runs. Money-moving
code should have solvency and accounting invariants (profit-in-integer-domain checks belong here too).

## 7. Dependencies

```bash
forge install vectorized/solady@v0.0.265     # tag or full commit hash, never a moving branch for release code
forge update lib/solady ; forge remove solady ; forge remappings > remappings.txt
git submodule update --init --recursive      # after a fresh clone
```

Pin every dependency to a tag or commit and record provenance (repo-profile). `--no-commit` was a flag on older
`forge install`; check `forge install --help` for what your version does about commits. Conflicting versions of
one library: remapping contexts (`lib/a/:@openzeppelin/=lib/a/node_modules/@openzeppelin/`).

Soldeer (npm-style registry): `forge soldeer init`, `forge soldeer install <name>~<version>`,
`forge soldeer update`, `forge soldeer uninstall <name>`; deps live in `dependencies/` and `[dependencies]` in
`foundry.toml`, with `[soldeer]` options for generated remappings. Trade-off: semantic versions and a shared
registry vs submodules' commit-hash pinning and full private-repo support. Registry content is third-party
code — pin the version and review it like any other dependency.

## 8. Config keys beyond the baseline

```toml
[profile.default]
extra_output = ["storageLayout"]   # then: forge inspect <Contract> storageLayout — diff it in CI for upgrades/diamonds
bytecode_hash = "none"             # + cbor_metadata = false: smaller, reproducible bytecode when metadata isn't needed
gas_reports = ["*"]
fuzz.seed = "0x1234"               # deterministic CI runs; fuzz.dictionary_weight tunes discovered-value reuse
invariant.depth = 50
rpc_storage_caching = { chains = "all", endpoints = "all" }

[etherscan]                        # per-chain explorer keys from env, e.g. arbitrum = { key = "${ARBISCAN_API_KEY}" }
```

Override any key per run with `FOUNDRY_<KEY>` (e.g. `FOUNDRY_PROFILE=ci`, `FOUNDRY_FUZZ_RUNS=10000`).
Profiles: `ci` (high fuzz/invariant runs, `verbosity = 3`), `production`, `fast` (optimizer off, fewer runs,
`no_match_test = "testFork_"`). Keep the optimizer/`via_ir` settings of the profile you ship identical to the one
you verify with.

## 9. CI (GitHub Actions)

- Install with `foundry-rs/foundry-toolchain@v1`; set `FOUNDRY_PROFILE: ci`. **Pin third-party actions to a full
  commit SHA for release pipelines**; a floating tag can change under you.
- Jobs worth separating: `forge fmt --check` + `forge lint` + `forge build --sizes` (the bytecode-size gate —
  confirm how your version reports/exits when a contract exceeds the limit); `forge test` (offline);
  `forge test --match-test testFork` with the RPC URL from an encrypted secret and a pinned block;
  `forge coverage --report lcov`; `forge snapshot --check --tolerance <pct>` for gas regressions.
- Cache `lib`/`cache`/`out` keyed on `foundry.toml` + lockfile hashes; RPC response caching comes from the
  toolchain action and pinned fork blocks.
- Secrets: RPC URLs and explorer keys as repository/environment secrets only. **Do not put a deployer private
  key in CI** for mainnet; deploy from a hardware wallet or a keystore-backed signer with a protected
  environment and manual approval, per `foundry-integration.md` §7.
- Matrix over solc versions only for libraries meant to be reused; an application pins one (`repo-profile.md`).

## 10. Deployment scripts and verification

```bash
forge script script/Deploy.s.sol:Deploy --rpc-url $RPC                    # simulation only
forge script script/Deploy.s.sol:Deploy --rpc-url $RPC --account deployer --broadcast --verify
forge script ... --resume                                                 # continue a partly-broadcast run
forge script script/Multi.s.sol --multi --slow --broadcast --verify       # multi-chain, one tx at a time
```

Phases: local simulation → on-chain simulation (with `--rpc-url`) → broadcast (`--broadcast`) → verification
(`--verify`). Output lands in `broadcast/<Script>/<chainId>/run-latest.json` (plus timestamped runs and
receipts); read it with `vm.readFile` + `vm.parseJson*`, or commit the relevant record as the deployment proof.

- **Pre-flight inside the script:** assert `block.chainid`, the deployer's balance and every address/config input
  (zero/unset → named custom error, per `repo-profile.md`) *before* `vm.startBroadcast`.
- **Deterministic (CREATE2):** `new C{salt: salt}(args)` under broadcast deploys through the standard
  deterministic-deployment proxy (`0x4e59…956C`); predict with `computeCreate2Address(salt, hashInitCode(
  type(C).creationCode, abi.encode(args)))` and skip if `predicted.code.length > 0`. Confirm the proxy exists on
  the target chain (`cast code`) — it is common, not universal.
- **Manual verification:** `forge verify-contract --chain <id|name> --compiler-version <v> --num-of-optimizations
  <n> --constructor-args $(cast abi-encode "constructor(...)" ...) <addr> src/X.sol:X`; `forge verify-check
  --chain <id> <guid>`; linked libraries via `--libraries path:Lib:0xAddr`. Use the same compiler version,
  optimizer runs, `via_ir` and EVM version as the build.
- **Proxies:** deploy implementation → proxy with `abi.encodeCall(Impl.initialize, (...))` init data in the same
  transaction (no uninitialized window). OZ `TransparentUpgradeableProxy` / `ERC1967Proxy` (UUPS) are the
  vetted choices; details in `practitioner-checklist.md` §5.
- **Script tests:** a `Test` that calls `script.run()` against Anvil/fork catches broken wiring before broadcast.

## 11. Deliberately not imported

From the source skill, left out because they conflict with this skill's rules or are unreliable:

- Its gas tables: the two files disagree (SSTORE non-zero→non-zero is 5,000 in one and 2,900 in the other;
  refund 15,000 vs 4,800). Measure with `forge snapshot` on the target chain instead.
- `transfer()`/`send()` payout loops, string-reason `require`, `assert`-style validation, and a hand-rolled
  `tload(0)` guard — deprecated or contrary to `quick-rules.md` and the repo profile.
- Deploy and CI examples that read `PRIVATE_KEY` from the environment.
- Its Solidity 0.8.30 version table, "latest EVM" claims, and `resources.md` (links and version context dated
  Nov 2025). For current versions use `compiler-evm-versions-and-imports.md` and `foundry-integration.md`.
