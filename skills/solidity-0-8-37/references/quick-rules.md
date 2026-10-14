# Solidity 0.8.37 — Quick Rules

Distilled from the official 0.8.37-develop documentation (Sep 10, 2026). Each rule names the
verbatim reference file (and doc section) it comes from. When a rule here is not detailed enough
to decide a case, open that file; the verbatim text wins over this summary.

## 1. File layout (source-layout-and-contract-structure.md §3.4; style-guide.md §3.34.3)

- First line: `// SPDX-License-Identifier: <id>` (use `UNLICENSED` if closed-source; not `UNLICENSE`).
- Then `pragma solidity ...;`. Pragmas are file-local: every file carries its own.
  The default EVM target for 0.8.37 is `osaka` (compiler-evm-versions-and-imports.md §3.13.2).
- `pragma abicoder v2` is the default since 0.8.0; `abicoder v1` is deprecated and scheduled for removal.
- `pragma experimental SMTChecker;` is deprecated — select the engine from the compiler instead.
- File-level order: pragmas → imports → events → errors → interfaces → libraries → contracts.
- Inside a contract/library/interface: type declarations → state variables → events → errors →
  modifiers → functions.
- Function order: constructor → receive → fallback → external → public → internal → private;
  within each group, `view` then `pure` last.
- Contract/library name matches the file name (`Congress.sol` ↔ `contract Congress`).
- 4-space indentation, no tabs; max line length 120.

## 2. Naming (style-guide.md §3.34.4)

- CapWords: contracts, libraries, interfaces, structs, enums, events.
- mixedCase: functions, function arguments, modifiers, local and state variables.
- UPPER_CASE_WITH_UNDERSCORES: constants.
- `_singleLeadingUnderscore` for internal/private functions and state variables;
  `singleTrailingUnderscore_` to avoid collisions with reserved names.
- Never single-letter `l`, `O`, `I`. Initialisms stay capitalised (`HTTPServerError`, `xmlHTTPRequest`).
- Library functions on a custom struct: the struct is the first argument and is named `self`.
- Do not use reserved future keywords as identifiers (units-and-globals.md §3.7.4): `after, alias, apply,
  auto, byte, case, copyof, default, define, final, implements, in, inline, let, macro, match, mutable,
  null, of, partial, promise, reference, relocatable, sealed, sizeof, static, supports, switch, typedef,
  typeof, var`.

## 3. Types (types.md §3.6)

- Every value has a static type; there is no `undefined`/`null`. Default values are the zero state of the type.
- Integers: `int8..int256`, `uint8..uint256` in steps of 8; `int`/`uint` alias the 256-bit forms.
  Checked arithmetic reverts with `Panic(0x11)` on overflow/underflow; division/modulo by zero is `Panic(0x12)`.
  `unchecked { ... }` opts into wrapping for arithmetic *inside the block only* (not for calls made from it,
  not for division by zero, not for shifts/exponent bases that are otherwise checked)
  (expressions-control-structures-and-errors.md §3.8.7).
- `address` vs `address payable`: only `address payable` has `.transfer`/`.send`; `address` → `address payable`
  requires `payable(addr)`; a contract type converts to `address payable` only if it has a `receive` or payable
  `fallback`.
- `.transfer()` and `.send()` are **deprecated and scheduled for removal**. Send Ether with
  `(bool ok, ) = addr.call{value: amount}("")` and check `ok` explicitly.
- `.call/.delegatecall/.staticcall` return `(bool, bytes memory)`; they succeed when the target has no code —
  check `extcodesize`/use a high-level call when code presence matters.
- Fixed-size bytes `bytes1..bytes32`; `bytes` and `string` are dynamic reference types; `bytes.concat` and
  `string.concat` exist. `byte` (the old alias) is not a type.
- Enums: converting an out-of-range integer to an enum is `Panic(0x21)`. Enums need ≥1 and ≤256 members.
- User-defined value types: `type T is <value type>;` with `T.wrap`/`T.unwrap`. No implicit conversions.
- Function types: `function (params) {internal|external} [pure|view|payable] [returns (...)]`.
  Calling a zero-initialised internal function-type variable is `Panic(0x51)`.
- Reference types require an explicit data location: `memory`, `storage`, or `calldata` (parameters of
  external functions may be `calldata`; it is read-only and cheapest). Assignment semantics:
  storage↔memory and memory→storage copy; storage→local storage pointer references; memory→memory references.
- Arrays: `.push()`/`.pop()` only on storage dynamic arrays; `.pop()` on empty is `Panic(0x31)`;
  out-of-bounds index is `Panic(0x32)`. Memory arrays are fixed once allocated (`new T[](n)`).
  Array slices `x[start:end]` exist only for `calldata` arrays.
- Mappings live only in storage (state variables, storage pointers, library params); not iterable,
  no `.length`; keys can be any value type, `bytes`, `string`, contract, or enum — not mappings/structs/arrays.
- Structs cannot contain themselves directly (only via mapping/array indirection).
- `delete x` resets to the type's zero value; on a struct it recurses, on a mapping it does nothing
  (mapping members of deleted structs are untouched).
- Conversions: implicit only when safe (e.g. `uint8`→`uint16`, `int128`→`int256`); explicit conversions
  between integers of different size truncate/extend, between integer and `bytesN` of different size are
  disallowed in one step; literals convert only if they fit.

## 4. Globals and units (units-and-globals.md §3.7)

- Units: `wei`, `gwei`, `ether`; `seconds`, `minutes`, `hours`, `days`, `weeks` (no `years`).
- Block/tx: `block.basefee`, `block.blobbasefee`, `block.chainid`, `block.coinbase`, `block.gaslimit`,
  `block.number`, `block.prevrandao`, `block.timestamp`, `block.slotnum` (EVM ≥ amsterdam only),
  `blockhash(n)` (only the 256 most recent blocks, excluding current), `blobhash(i)`,
  `msg.sender`, `msg.value`, `msg.data`, `msg.sig`, `tx.origin`, `tx.gasprice`, `gasleft()`.
- `block.difficulty` is a deprecated alias of `block.prevrandao` on EVM ≥ paris; `now` was removed in 0.7.0.
- Do not use `block.timestamp`/`blockhash` as randomness sources and do not rely on `tx.origin` for auth.
- ABI: `abi.encode`, `abi.encodePacked` (ambiguous for dynamic types — do not hash it for signatures with
  more than one dynamic argument), `abi.encodeWithSelector`, `abi.encodeWithSignature`,
  `abi.encodeCall(fnPtr, (args))` (type-checked — prefer it), `abi.decode(data, (types))`.
- Crypto: `keccak256(bytes)`, `sha256(bytes)`, `ripemd160(bytes)`, `ecrecover(hash, v, r, s)` (returns
  `address(0)` on failure — check it), `addmod`, `mulmod`.
- `erc7201(string memory id) returns (uint)` computes an ERC-7201 namespace base slot (usable at compile time).
- `type(C).name/creationCode/runtimeCode`, `type(I).interfaceId`, `type(T).min/max`.
- `selfdestruct` is deprecated (since 0.8.18). On a chain at Cancun or later it only transfers the balance and
  does not remove code unless called in the creating transaction; this depends on the chain's fork, not on
  `--evm-version` (evm-basics.md §3.1.3). Do not use it in new code; deactivate via a state flag instead.

## 5. Control flow, calls and errors (expressions-control-structures-and-errors.md §3.8)

- `if/else`, `while`, `do..while`, `for`, `break`, `continue`, `return`, `try/catch`. No `switch`/`goto`.
  Parentheses are required around conditions; non-boolean values are not auto-converted to `bool`.
- Internal calls are jumps; external calls (`this.f()`, `c.f()`) create message calls and can be given
  `{value: ..., gas: ...}`. Named arguments `f({a: 1, b: 2})` are allowed; omitted names in declarations are OK.
- `new C{value: v, salt: s}(args)` deploys; with `salt` the address is `create2`-deterministic.
- Evaluation order of expression operands is unspecified except that statements execute in order.
- Destructuring: `(uint a, , uint c) = f();` leaves gaps with blank entries.
- Variables are scoped C99-style (block scope; visible from declaration to end of block).
- Error handling:
  - `require(cond)`, `require(cond, "msg")`, `require(cond, CustomError(args))` (custom-error form since 0.8.26).
    All `require` arguments are evaluated unconditionally — never put side effects in the error expression.
  - `revert CustomError(args);` / `revert()` / `revert("msg")`. Custom errors are cheaper and ABI-decodable;
    prefer them. Define with `error Name(type arg, ...);` at file or contract level.
  - `assert(cond)` is for invariants only; failure is `Panic(0x01)`. Do not use `assert` for input validation.
  - `try f() returns (T v) { } catch Error(string memory r) { } catch Panic(uint code) { } catch (bytes memory d) { }`
    only works on external calls and `new`; a failing call inside the `catch` block itself still reverts.
    Never leave a `catch` block empty — handle or re-revert.
- Exceptions bubble up through internal calls and `transfer`; low-level `call/delegatecall/staticcall` return
  `false` instead of bubbling — always check the result.

## 6. Contracts (contracts-core.md §3.9.1–3.9.10)

- Visibility is mandatory on functions: `external`, `public`, `internal`, `private`. State variables default to
  `internal`; `public` state variables get an auto-generated getter (arrays/mappings take index args; structs omit
  nested mappings/arrays). Nothing is hidden from other observers — `private` only limits access from code.
- `constructor` has no visibility specifier (declaring `internal`/`public` is deprecated). A contract with no
  constructor gets an implicit empty one. Base constructor args are given in the inheritance list or via
  modifier-style invocation in the derived constructor — not both.
- `receive() external payable { }` for empty-calldata Ether; `fallback() external [payable]` or
  `fallback(bytes calldata) external [payable] returns (bytes memory)` for everything else. Keep both minimal
  (2300-gas callers will fail otherwise).
- State mutability: `pure` (no read/write of state), `view` (read only), default (read/write), `payable`
  (may receive Ether). Non-payable functions reject `msg.value > 0`. `view` is enforced with `staticcall`
  at the EVM level for external calls.
- Modifiers: `modifier m(args) { ...; _; ... }`; `_` may appear multiple times; modifier-local variables
  are not visible to the function. `virtual` modifiers are **deprecated and scheduled for removal**.
- `constant`: value fixed at compile time (only literals, pure built-ins like `keccak256`, and
  compile-time expressions); `immutable`: assigned at construction (anywhere not reachable after deployment —
  constructor or inline initialiser, since 0.8.21 also readable in the constructor after assignment), stored in
  code. Both allowed for value types and `string`/`bytes` (constant only for reference types).
- `transient` storage (`uint256 transient x;`): value-type **state variables only** (no reference types,
  no locals/params), reset at end of transaction, cheaper than storage. Not usable through library/delegatecall
  references — libraries can only touch it via inline assembly. Beware composability: a transient flag set in
  one call survives into later calls of the same transaction.
- Custom storage layout: `contract C layout at <compile-time uint256 literal expr> { ... }` (may use
  `erc7201(...)`); at most one specifier, placed before or after the inheritance list, only on the most
  derived contract being compiled.
- Functions: parameters/returns can be named; `returns (uint a, uint b)` lets you assign to names or `return`.
  Function overloading resolves on argument types; ambiguous external overloads are errors.
  Free functions (file level) are implicitly `internal` and cannot touch state they aren't given.
- Events: `event E(type indexed a, type b)`; up to 3 `indexed` params (4 if `anonymous`); indexed reference
  types store the keccak hash as the topic; `emit E(...)`. Events are not readable from contracts.
- Custom errors: `error E(type a);` at file or contract scope; selector = first 4 bytes of
  `keccak256("E(type)")`; use `revert E(a)` or `require(cond, E(a))`. Errors cannot be overloaded with the
  same name in the same scope. Include offending values in parameters for debuggability.

## 7. Inheritance, interfaces, libraries (contracts-inheritance-interfaces-libraries.md §3.9.11–3.9.15)

- `contract D is A, B` — list bases from "most base-like" to "most derived"; C3 linearization applies and
  an impossible order is a compile error. `super.f()` follows the linearization, not a single parent.
- A function that may be overridden must be `virtual`; the overriding one must say `override`
  (`override(A, B)` when it overrides several bases). Public state variables can `override` external
  functions of the same getter signature (not the reverse).
- Overriding may only tighten mutability (`nonpayable`→`view`→`pure`; `payable` cannot change) and
  may make visibility `external`→`public` only.
- Interfaces: all functions `external`; no implemented functions, no constructor, no state variables,
  no modifiers; may declare events, errors, structs, enums; may inherit only interfaces. `type(I).interfaceId`
  is the XOR of the function selectors (excluding inherited ones).
- Abstract contracts: `abstract contract X` — required when any function lacks an implementation
  (unimplemented functions must be `virtual`).
- Libraries: `library L { ... }`; no state variables, no Ether, no inheritance, cannot be destroyed.
  `internal` library functions are inlined; `external`/`public` ones run via `delegatecall` and require
  linking. Libraries may take `storage` reference arguments to mutate caller state.
- `using L for T;` / `using {f, g as +} for T [global];` — attaches functions as members (first param is
  the receiver) or defines operators on user-defined value types (operator functions must be pure, free
  functions; `global` only at file level for a type defined in the same file).
- Shadowing of state variables by derived declarations is disallowed; function/local shadowing warns.

## 8. Inline assembly (inline-assembly-and-yul.md §3.10, §3.32)

- `assembly { ... }` uses Yul; variables of value type are accessible by name; storage variables need
  `.slot` and `.offset`; `calldata` arrays/`bytes` need `.offset`/`.length`; memory references give the
  pointer. You cannot access `storage` locals directly except through `.slot`.
- Annotate blocks that respect Solidity's memory model with `assembly ("memory-safe") { ... }`. The old
  `/// @solidity memory-safe-assembly` comment is deprecated and scheduled for removal. Memory-safe blocks
  may only touch: memory you allocated via the free-memory pointer at `0x40`, scratch space `0x00–0x3f`,
  and memory past the free-memory pointer that you don't leave allocated. Violating this with the annotation
  present is undefined behaviour under `via_ir`.
- Available opcodes depend on `evm_version`: `tload/tstore/mcopy/blobhash/blobbasefee` need ≥ cancun;
  `clz` needs ≥ osaka; `slotnum` needs ≥ amsterdam (experimental). `difficulty()` is disallowed ≥ paris.
- Don't rely on the layout of memory beyond what the docs guarantee; never write to slots `0x40`–`0x5f`
  except to update the free-memory pointer; `0x60` is the zero slot (never write to it).

## 9. Data layout (data-layout.md §3.16–3.19)

- Storage packs consecutive variables < 32 bytes into one slot, in declaration order, lower-order aligned;
  structs and arrays always start a new slot and occupy whole slots. Order small types together to save slots.
- Dynamic array data is at `keccak256(slot)` + index; mapping values at `keccak256(h(k) . slot)`.
  `bytes`/`string` ≤ 31 bytes are stored in-slot with `length*2` in the low byte; longer ones use
  `keccak256(slot)` and store `length*2+1`.
- Transient storage uses the same layout rules but a separate address space.
- Memory: fixed slots `0x00–0x3f` scratch, `0x40` free pointer, `0x60` zero slot; memory is never freed;
  elements are always 32-byte padded (except `bytes`/`string` payload).
- Calldata arrays follow ABI encoding (abi-and-metadata.md §3.23); use `calldata` params to avoid copies.
- Values narrower than 256 bits may contain dirty higher-order bits until the compiler "cleans" them before
  use that depends on them; never assume clean bits in assembly for values you did not clean yourself.

## 10. Security baseline (security-considerations.md §3.24; known-bugs.md §3.25)

- Checks-Effects-Interactions: validate → update state → call out. Re-entrancy is possible on any external
  call that forwards gas, including through `receive`/`fallback` of the callee.
- Pull over push for payments (common-patterns.md §3.35.1 withdrawal pattern).
- Never trust `tx.origin` for authorisation; never use block fields for randomness.
- Gas limits: unbounded loops over user-growable arrays can brick a function; cap iteration or paginate.
- `delegatecall`/libraries execute in the caller's storage context — only call code you control, and keep
  storage layouts identical for proxies.
- Mark that `private`/`internal` does not hide data on-chain.
- Reduce surface: minimise code in `receive`/`fallback`, prefer explicit casts, prefer `abi.encodeCall`.
- Check the known-bugs list for the compiler version in use before shipping (entries include `introduced`
  and `fixed` versions; several fixed in 0.8.32–0.8.37).

## 11. NatSpec (natspec.md §3.30)

- Use `///` or `/** */` directly above the item. Tags: `@title`, `@author`, `@notice`, `@dev`, `@param name`,
  `@return`, `@inheritdoc Contract`, `@custom:...` (lowercase letters/hyphens).
- A `///` comment with no tag is treated as `@notice`.
- Document every public/external function, every public state variable, event and error: `@notice` plus one
  `@param` per parameter (by name) and one `@return` per return value (in order). Multiple returns get
  multiple `@return` lines.
- Overrides without NatSpec inherit the base docs unless param names differ, there are multiple bases, or you
  use `@inheritdoc` explicitly.
- Dynamic expressions in `@notice` (e.g. `` `a` ``) are rendered by clients — use backticks for identifiers.

## 12. Compiler usage (compiler-evm-versions-and-imports.md §3.13, §3.33)

- EVM targets: `homestead…berlin` (deprecated), `london`, `paris`, `shanghai`, `cancun`, `prague`,
  `osaka` (default), `amsterdam` (experimental). Compiling for the wrong target yields wrong/failing bytecode.
- `via_ir` / `--via-ir` routes through Yul; semantics differ from legacy codegen in documented ways
  (ir-codegen-and-optimizer.md §3.15): e.g. modifier/state-variable initialisation order, cleanup of
  dirty bytes, `.selector`/`.address` access on function types, memory layout for returned values.
- Imports: `import "./x.sol";`, `import {A, B as C} from "./x.sol";`, `import * as X from "./x.sol";`.
  Use remappings (`prefix=target`) in `foundry.toml`/`remappings.txt`; `allowed_paths` restricts reads.
- Experimental mode (`pragma experimental ...`, since 0.8.35 systematised) is opt-in and non-production.
