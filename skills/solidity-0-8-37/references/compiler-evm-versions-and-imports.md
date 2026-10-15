# Using the Compiler, EVM versions, Standard JSON, Experimental mode, Analysing output, Import path resolution (3.13, 3.14, 3.33)

> Source: Solidity documentation, release 0.8.37-develop (Sep 10, 2026), https://docs.soliditylang.org/ — text reproduced from the official docs; code indentation was flattened by the export and is not normative.

## Contents

- 3.13 Using the Compiler
  - 3.13.1 Using the Commandline Compiler
  - 3.13.2 Setting the EVM Version to Target
  - 3.13.3 Compiler Input and Output JSON Description
  - 3.13.4 Experimental Mode
- 3.14 Analysing the Compiler Output
- 3.33 Import Path Resolution
  - 3.33.1 Virtual Filesystem
  - 3.33.2 Imports
  - 3.33.3 Base Path and Include Paths
  - 3.33.4 Allowed Paths
  - 3.33.5 Import Remapping
  - 3.33.6 Using URLs in imports

---

# 3.13 Using the Compiler

## 3.13.1 Using the Commandline Compiler

**Note:**

This section does not apply to solcjs, not even if it is used in commandline mode.

### Basic Usage

One of the build targets of the Solidity repository is solc, the Solidity commandline compiler. Using solc --help provides you with an explanation of all options. The compiler can produce various outputs, ranging from simple binaries and assembly over an abstract syntax tree (parse tree) to estimations of gas usage. If you only want to compile a single file, you run it as solc --bin sourceFile.sol and it will print the binary. If you want to get some of the more advanced output variants of solc, it is probably better to tell it to output everything to separate files using solc -o outputDirectory --bin --ast-compact-json --asm sourceFile.sol.

### Optimizer Options

Before you deploy your contract, activate the optimizer when compiling using solc --optimize --bin sourceFile.sol. By default, the optimizer will optimize the contract assuming it is called 200 times across its lifetime (more specifically, it assumes each opcode is executed around 200 times). If you want the initial contract deployment to be cheaper and the later function executions to be more expensive, set it to --optimize-runs=1. If you expect many transactions and do not care for higher deployment cost and output size, set --optimize-runs to a high number. This parameter has effects on the following (this might change in the future):

- the size of the binary search in the function dispatch routine

- the way constants like large numbers or strings are stored

### Base Path and Import Remapping

The commandline compiler will automatically read imported files from the filesystem, but it is also possible to provide path redirects using prefix=path in the following way:

solc github.com/ethereum/dapp-bin/=/usr/local/lib/dapp-bin/ file.sol

This essentially instructs the compiler to search for anything starting with github.com/ethereum/dapp-bin/ under

/usr/local/lib/dapp-bin.

When accessing the filesystem to search for imports, paths that do not start with ./ or ../ are treated as relative to the directories specified using --base-path and --include-path options (or the current working directory if base path is not specified). Furthermore, the part of the path added via these options will not appear in the contract metadata.

For security reasons the compiler has restrictions on what directories it can access. Directories of source files specified on the command-line and target paths of remappings are automatically allowed to be accessed by the file reader, but everything else is rejected by default. Additional paths (and their subdirectories) can be allowed via the --allow-paths /sample/path,/another/sample/path switch. Everything inside the path specified via --base-path is always allowed.

The above is only a simplification of how the compiler handles import paths. For a detailed explanation with examples and discussion of corner cases please refer to the section on path resolution.

### Library Linking

If your contracts use libraries, you will notice that the bytecode contains substrings of the form

**\$53aea86b7d70b31448b230b20ae141a537\$** (format was different <v0.5.0). These are placeholders for the actual library addresses. The placeholder is a 34 character prefix of the hex encoding of the keccak256 hash of the fully qualified library name. The bytecode file will also contain lines of the form // <placeholder> -> <fq library name> at the end to help identify which libraries the placeholders represent. Note that the fully qualified library name is the path of its source file and the library name separated by :. You can use solc as a linker meaning that it will insert the library addresses for you at those points: (https://docs.soliditylang.org/en/v0.4.26/contracts.html#libraries)

Either add --libraries "file.sol:Math=0x1234567890123456789012345678901234567890 file.

sol:Heap=0xabCD567890123456789012345678901234567890" to your command to provide an address for each library (use commas or spaces as separators) or store the string in a file (one library per line) and run solc using --libraries fileName.

**Note:**

Starting Solidity 0.8.1 accepts = as separator between library and address, and

: as a separator is deprecated.

--libraries "file.sol:Math:0x1234567890123456789012345678901234567890 file. sol:Heap:0xabCD567890123456789012345678901234567890" will work too.

If solc is called with the option --standard-json, it will expect a JSON input (as explained below) on the standard input, and return a JSON output on the standard output. This is the recommended interface for more complex and especially automated uses. The process will always terminate in a “success” state and report any errors via the JSON output. The option --base-path is also processed in standard-json mode.

If solc is called with the option --link, all input files are interpreted to be unlinked binaries (hex-encoded) in the

**\$53aea86b7d70b31448b230b20ae141a537\$**-format given above and are linked in-place (if the input is read from stdin, it is written to stdout). All options except --libraries are ignored (including -o) in this case.

It will be removed in the future.

Currently

**Warning:**

Manually linking libraries on the generated bytecode is discouraged because it does not update contract metadata.

Since metadata contains a list of libraries specified at the time of compilation and bytecode contains a metadata hash, you will get different binaries, depending on when linking is performed.

You should ask the compiler to link the libraries at the time a contract is compiled by either using the --libraries option of solc or the libraries key if you use the standard-JSON interface to the compiler.

**Note:**

The library placeholder used to be the fully qualified name of the library itself instead of the hash of it. This format is still supported by solc --link but the compiler will no longer output it. This change was made to reduce the likelihood of a collision between libraries, since only the first 36 characters of the fully qualified library name could be used.

## 3.13.2 Setting the EVM Version to Target

When you compile your contract code you can specify the Ethereum virtual machine version to compile for to avoid particular features or behaviors.

**Warning:**

Compiling for the wrong EVM version can result in wrong, strange and failing behavior. Please ensure, especially if running a private chain, that you use matching EVM versions.

On the command-line, you can select the EVM version as follows:

solc --evm-version <VERSION> contract.sol

In the standard JSON interface, use the "evmVersion" key in the "settings" field:

```
{
"sources": {/* ... */},
"settings": {
"optimizer": {/* ... */},
"evmVersion": "<VERSION>"
}
}
```

### Target Options

Below is a list of target EVM versions and the compiler-relevant changes introduced at each version. Backward compatibility is not guaranteed between each version.

- homestead (support deprecated)

- (oldest version)

- tangerineWhistle (support deprecated)

- Gas cost for access to other accounts increased, relevant for gas estimation and the optimizer.

- All gas sent by default for external calls, previously a certain amount had to be retained.

- spuriousDragon (support deprecated)

- Gas cost for the exp opcode increased, relevant for gas estimation and the optimizer.

- byzantium (support deprecated)

- Opcodes returndatacopy, returndatasize and staticcall are available in assembly.

- The staticcall opcode is used when calling non-library view or pure functions, which prevents the functions from modifying state at the EVM level, i.e., even applies when you use invalid type conversions.

- It is possible to access dynamic data returned from function calls.

- revert opcode introduced, which means that revert() will not waste gas.

- constantinople (support deprecated)

- Opcodes create2, extcodehash, shl, shr and sar are available in assembly.

- Shifting operators use shifting opcodes and thus need less gas.

- petersburg (support deprecated)

- The compiler behaves the same way as with constantinople.

- istanbul (support deprecated)

- Opcodes chainid and selfbalance are available in assembly.

- berlin (support deprecated)

- Gas costs for SLOAD, _CALL, BALANCE, EXT_ and SELFDESTRUCT increased. The compiler assumes cold gas costs for such operations. This is relevant for gas estimation and the optimizer.

- london

- The block’s base fee (EIP-3198 and EIP-1559) can be accessed via the global block.basefee or basefee() in inline assembly. (https://eips.ethereum.org/EIPS/eip-3198)

- paris

- Introduces prevrandao() and block.prevrandao, and changes the semantics ofthe nowdeprecated block.difficulty, disallowing difficulty() in inline assembly (see EIP-4399). (https://eips.ethereum.org/EIPS/eip-4399)

- shanghai

- Smaller code size and gas savings due to the introduction of push0 (see EIP-3855). (https://eips.ethereum.org/EIPS/eip-3855)

- cancun

- The block’s blob base fee (EIP-7516 and EIP-4844) can be accessed via the global block. blobbasefee or blobbasefee() in inline assembly. (https://eips.ethereum.org/EIPS/eip-4844)

- Introduces blobhash() in inline assembly and a corresponding global function to retrieve versioned hashes of blobs associated with the transaction (see EIP-4844). (https://eips.ethereum.org/EIPS/eip-4844)

- Opcode mcopy is available in assembly (see EIP-5656). (https://eips.ethereum.org/EIPS/eip-5656)

- Opcodes tstore and tload are available in assembly (see EIP-1153). (https://eips.ethereum.org/EIPS/eip-1153)

- prague

- osaka (default)

- clz builtin function is available in inline assembly. (EIP-7939) (https://eips.ethereum.org/EIPS/eip-7939)

- amsterdam (experimental)

- The beacon chain slot number (EIP-7843) can be accessed via the global block.slotnum or slotnum() in inline assembly. (https://eips.ethereum.org/EIPS/eip-7843)

## 3.13.3 Compiler Input and Output JSON Description

The recommended way to interface with the Solidity compiler especially for more complex and automated setups is the so-called JSON-input-output interface. The same interface is provided by all distributions of the compiler.

The fields are generally subject to change, some are optional (as noted), but we try to only make backwards compatible changes.

The compiler API expects a JSON formatted input and outputs the compilation result in a JSON formatted output. The standard error output is not used and the process will always terminate in a “success” state, even if there were errors. Errors are always reported as part of the JSON output.

The following subsections describe the format through an example. Comments are of course not permitted and used here only for explanatory purposes.

### Input Description

```
{
// Required: Source code language. Currently supported are "Solidity", "Yul", "SolidityAST" (experimental), "EVMAssembly" (experimental).
"language": "Solidity",
// Required
"sources":
{
// The keys here are the "global" names of the source files,
// imports can use other files via remappings (see below).
"myFile.sol":
{
// Optional: keccak256 hash of the source file
// It is used to verify the retrieved content if imported via URLs.
"keccak256": "0x123...",
// Required (unless "content" is used, see below): URL(s) to the source file.
// URL(s) should be imported in this order and the result checked against the
// keccak256 hash (if available). If the hash doesn't match or none of the
// URL(s) result in success, an error should be raised.
// Using the commandline interface only filesystem paths are supported.
// With the JavaScript interface the URL will be passed to the user-supplied
// read callback, so any URL supported by the callback can be used.
"urls":
[
"bzzr://56ab...",
"ipfs://Qma...",
"/tmp/path/to/file.sol"
// If files are used, their directories should be added to the command-line via
// `--allow-paths <path>`.
]
},
"settable":
{
// Optional: keccak256 hash of the source file
"keccak256": "0x234...",
// Required (unless "urls" is used): literal contents of the source file
"content": "contract settable is owned { uint256 private x = 0; function set(uint256 _x) public { if (msg.sender == owner) x = _x; } }"
},
"myFile.sol_json.ast":
{
// If language is set to "SolidityAST", an AST needs to be supplied under the "ast" key
// and there can be only one source file present.
// The format is the same as used by the `ast` output.
// Note that importing ASTs is experimental and in particular that:
// - importing invalid ASTs can produce undefined results and
// - no proper error reporting is available on invalid ASTs.
// Furthermore, note that the AST import only consumes the fields of the AST as
// produced by the compiler in "stopAfter": "parsing" mode and then re-performs
// analysis, so any analysis-based annotations of the AST are ignored upon import.
"ast": { ... }
},
"myFile_evm.json":
{
// If language is set to "EVMAssembly", an EVM Assembly JSON object needs to be supplied
// under the "assemblyJson" key and there can be only one source file present.
// The format is the same as used by the `evm.legacyAssembly` output or `--asm-json`
// output on the command line.
// Note that importing EVM assembly is experimental.
"assemblyJson":
{
".code": [ ... ],
".data": { ... }, // optional
"sourceList": [ ... ] // optional (if no `source` node was defined in any `.code` object)
}
}
},
// Optional
"settings":
{
// Optional: Stop compilation after the given stage. Currently only "parsing" is valid here
"stopAfter": "parsing",
// Optional: List of remappings
"remappings": [ ":g=/dir" ],
// Optional: Experimental mode toggle (Default: false)
// Makes it possible to use experimental features (but does not enable any such feature by itself).
// The use of this mode is recorded in contract metadata.
"experimental": true,
// Optional: Optimizer settings
"optimizer": {
// Turn on the optimizer. Optional. Default: false.
// NOTE: The state of the optimizer is fully determined by the 'details' dict and this setting
// only affects its defaults - when enabled, all components default to being enabled.
// The opposite is not true - there are several components that always default to being
// enabled an can only be explicitly disabled via 'details'.
// WARNING: Before version 0.8.6 omitting this setting was not equivalent to setting
// it to false and would result in all components being disabled instead.
// WARNING: Enabling optimizations for EVMAssembly input is allowed but not necessary under normal
// circumstances. It forces the opcode-based optimizer to run again and can produce bytecode that
// is not reproducible from metadata.
"enabled": true,
// Optimize for how many times you intend to run the code. Optional. Default: 200.
// Lower values will optimize more for initial deployment cost, higher
// values will optimize more for high-frequency usage.
"runs": 200,
// State of all optimizer components. Optional.
// Default values are determined by whether the optimizer is enabled or not.
// Note that the 'enabled' setting only affects the defaults here and has no effect when
// all values are provided explicitly.
"details": {
// Peephole optimizer (opcode-based). Optional. Default: true.
// Default for EVMAssembly input: false when optimization is not enabled.
// NOTE: Always runs (even with optimization disabled) except for EVMAssembly input or when explicitly turned off here.
"peephole": true,
// Inliner (opcode-based). Optional. Default: true when optimization is enabled.
"inliner": false,
// Unused JUMPDEST remover (opcode-based). Optional. Default: true.
// Default for EVMAssembly input: false when optimization is not enabled.
// NOTE: Always runs (even with optimization disabled) except for EVMAssembly input or when explicitly turned off here.
"jumpdestRemover": true,
// Literal reordering (codegen-based). Optional. Default: true when optimization is enabled.
// Moves literals to the right of commutative binary operators during code generation, helping exploit associativity.
"orderLiterals": false,
// Block deduplicator (opcode-based). Optional. Default: true when optimization is enabled.
// Unifies assembly code blocks that share content.
"deduplicate": false,
// Common subexpression elimination (opcode-based). Optional. Default: true when optimization is enabled.
// This is the most complicated step but can also provide the largest gain.
"cse": false,
// Constant optimizer (opcode-based). Optional. Default: true when optimization is enabled.
// Tries to find better representations of literal numbers and strings, that satisfy the
// size/cost trade-off determined by the 'runs' setting.
"constantOptimizer": false,
// Unchecked loop increment (codegen-based). Optional. Default: true.
// Use unchecked arithmetic when incrementing the counter of 'for' loops under certain circumstances.
// NOTE: Always runs (even with optimization disabled) unless explicitly turnedoff here.
"simpleCounterForLoopUncheckedIncrement": true,
// Yul optimizer. Optional. Default: true when optimization is enabled.
// Used to optimize the IR produced by the Yul IR-based pipeline as well as inline assembly
// and utility Yul code generated by the compiler.
// NOTE: Before Solidity 0.6.0 the default was false.
"yul": false,
// Tuning options for the Yul optimizer. Optional.
"yulDetails": {
// Improve allocation of stack slots for variables, can free up stack slots early.
// Optional. Default: true if Yul optimizer is enabled.
"stackAllocation": true,
// Optimization step sequence.
// The general form of the value is "<main sequence>:<cleanup sequence>".
// The setting is optional and when omitted, default values are used for both sequences.
// If the value does not contain the ':' delimiter, it is interpreted as the main
// sequence and the default is used for the cleanup sequence.
// To make one of the sequences empty, the delimiter must be present at the first or last position.
// In particular if the whole value consists only of the delimiter, both
```

``` sequences are empty.
// Note that there are several hard-coded steps that always run, even when both sequences are empty.
// For more information see "The Optimizer > Selecting Optimizations".
"optimizerSteps": "dfDvulfnTUtnIf..."
}
}
},
// Version of the EVM to compile for (optional).
// Affects type checking and code generation. Can be homestead,
// tangerineWhistle, spuriousDragon, byzantium, constantinople,
// petersburg, istanbul, berlin, london, paris, shanghai, cancun,
// prague, osaka (default), amsterdam (experimental), or @future (experimental).
"evmVersion": "osaka",
// Optional: Change compilation pipeline to go through the Yul intermediate representation.
// This is false by default.
"viaIR": true,
// Optional: Turn on SSA CFG-based code generation via the IR (experimental).
// Implies viaIR: true. This is false by default.
"viaSSACFG": false,
// Optional: Debugging settings
"debug": {
// How to treat revert (and require) reason strings. Settings are
// "default", "strip", "debug" and "verboseDebug".
// "default" does not inject compiler-generated revert strings and keeps user- supplied ones.
// "strip" removes all revert strings (if possible, i.e. if literals are used) keeping side-effects.
// NOTE: "strip" does not remove custom errors.
// "debug" injects strings for compiler-generated internal reverts, implemented for ABI encoders V1 and V2 for now.
// "verboseDebug" even appends further information to user-supplied revert strings (not yet implemented)
"revertStrings": "default",
// Optional: How much extra debug information to include in comments in the produced EVM
// assembly and Yul code. Available components are:
// - `location`: Annotations of the form `@src <index>:<start>:<end>` indicating the
// location of the corresponding element in the original Solidity file, where:
// - `<index>` is the file index matching the `@use-src` annotation,
// - `<start>` is the index of the first byte at that location,
// - `<end>` is the index of the first byte after that location.
// - `snippet`: A single-line code snippet from the location indicated by `@src`.
// The snippet is quoted and follows the corresponding `@src` annotation.
// - `ast-id`: Annotations of the form `@ast-id <id>` over elements that can be mapped back to a definition in the original Solidity file.
// `<id>` is a node ID in the Solidity AST ('ast' output).
// - `ethdebug`: Ethdebug annotations (experimental). Automatically enabled when any ethdebug output is requested.
// - `*`: Wildcard value that can be used to request all non-experimental components.
"debugInfo": ["location", "snippet", "ast-id", "ethdebug"]
},
// Metadata settings (optional)
"metadata": {
// The CBOR metadata is appended at the end of the bytecode by default.
// Setting this to false omits the metadata from the runtime and deploy time code.
"appendCBOR": true,
// Use only literal content and not URLs (false by default)
"useLiteralContent": true,
// Use the given hash method for the metadata hash that is appended to the bytecode.
// The metadata hash can be removed from the bytecode via option "none".
// The other options are "ipfs" and "bzzr1".
// If the option is omitted, "ipfs" is used by default.
"bytecodeHash": "ipfs"
},
// Addresses of the libraries. If not all libraries are given here,
// it can result in unlinked objects whose output data is different.
"libraries": {
// The top level key is the name of the source file where the library is used.
// If remappings are used, this source file should match the global path
// after remappings were applied.
// If this key is an empty string, that refers to a global level.
"myFile.sol": {
"MyLib": "0x123123..."
}
},
// The following can be used to select desired outputs based
// on file and contract names.
// If this field is omitted, then the compiler loads and does type checking,
// but will not generate any outputs apart from errors.
// The first level key is the file name and the second level key is the contract name.
// An empty contract name is used for outputs that are not tied to a contract
// but to the whole source file like the AST.
// A star as contract name refers to all contracts in the file.
// Similarly, a star as a file name matches all files.
// To select all outputs the compiler can possibly generate, with the exclusion of
// Yul intermediate representation outputs, use
// "outputSelection: { "*": { "*": [ "*" ], "": [ "*" ] } }"
// but note that this might slow down the compilation process needlessly.
//
// The available output types are as follows:
//
// File level (needs empty string as contract name):
// ast - AST of all source files
//
// Contract level (needs the contract name or "*"):
// abi - ABI
// devdoc - Developer documentation (natspec)
// userdoc - User documentation (natspec)
// metadata - Metadata
// ir - Yul intermediate representation of the code before optimization
// irAst - AST of Yul intermediate representation of the code before optimization (experimental)
// irOptimized - Intermediate representation after optimization
// irOptimizedAst - AST of intermediate representation after optimization (experimental)
// storageLayout - Slots, offsets and types of the contract's state variables in storage
// transientStorageLayout - Slots, offsets and types of the contract's state variables in transient storage
// evm.assembly - New assembly format
// evm.legacyAssembly - Old-style assembly format in JSON
// evm.bytecode.ethdebug - Debug information in ethdebug format (ethdebug/format/program schema for creation bytecode). Can only be requested when compiling via IR. (experimental)
// evm.deployedBytecode.ethdebug - Debug information in ethdebug format (ethdebug/format/program schema for deployed bytecode). Can only be requested when compiling via IR. (experimental)
// evm.bytecode.functionDebugData - Debugging information at function level
// evm.bytecode.object - Bytecode object
// evm.bytecode.opcodes - Opcodes list
// evm.bytecode.sourceMap - Source mapping (useful for debugging)
// evm.bytecode.linkReferences - Link references (if unlinked object)
// evm.bytecode.generatedSources - Sources generated by the compiler
// evm.deployedBytecode* - Deployed bytecode (has all the options that evm. bytecode has)
// evm.deployedBytecode.immutableReferences - Map from AST ids to bytecode ranges that reference immutables
// evm.methodIdentifiers - The list of function hashes
// evm.gasEstimates - Function gas estimates
// yulCFGJson - Control Flow Graph (CFG) of the Single Static Assignment (SSA) form of the contract (experimental)
//
// Global level (needs "*" as file name and "*" as contract name):
// ethdebug.resources - Global ethdebug output (ethdebug/format/info/resources schema) containing source list and compiler info (experimental)
// ethdebug.compilation - Global ethdebug compilation output (the 'compilation' key from ethdebug/format/info/resources schema) (experimental)
//
// Note that using `evm`, `evm.bytecode`, etc. will select every
// target part of that output. Additionally, `*` can be used as a wildcard to request everything.
//
"outputSelection": {
"*": {
"*": [
"metadata", "evm.bytecode" // Enable the metadata and bytecode outputs of every single contract.
, "evm.bytecode.sourceMap" // Enable the source map output of every single contract.
],
"": [
"ast" // Enable the AST output of every single file.
]
},
// Enable the abi and opcodes output of MyContract defined in file def.
"def": {
"MyContract": [ "abi", "evm.bytecode.opcodes" ]
}
},
// The modelChecker object is experimental and subject to changes.
"modelChecker":
{
// Chose which contracts should be analyzed as the deployed one.
"contracts":
{
"source1.sol": ["contract1"],
"source2.sol": ["contract2", "contract3"]
},
// Choose how division and modulo operations should be encoded.
// When using `false` they are replaced by multiplication with slack
// variables. This is the default.
// Using `true` here is recommended if you are using the CHC engine
// and not using Spacer as the Horn solver (using Eldarica, for example).
// See the Formal Verification section for a more detailed explanation of this option.
"divModNoSlacks": false,
// Choose which model checker engine to use: all (default), bmc, chc, none.
"engine": "chc",
// Choose whether external calls should be considered trusted in case the
// code of the called function is available at compile-time.
// For details see the SMTChecker section.
"extCalls": "trusted",
// Choose which types of invariants should be reported to the user: contract, reentrancy.
"invariants": ["contract", "reentrancy"],
// Choose whether to output all proved targets. The default is `false`.
"showProvedSafe": true,
// Choose whether to output all unproved targets. The default is `false`.
"showUnproved": true,
// Choose whether to output all unsupported language features. The default is`false`.
"showUnsupported": true,
// Choose which solvers should be used, if available.
// See the Formal Verification section for the solvers description.
"solvers": ["cvc5", "smtlib2", "z3"],
// Choose which targets should be checked: constantCondition,
// underflow, overflow, divByZero, balance, assert, popEmptyArray, outOfBounds.
// If the option is not given all targets are checked by default,
// except underflow/overflow for Solidity >=0.8.7.
// See the Formal Verification section for the targets description.
"targets": ["underflow", "overflow", "assert"],
// Timeout for each SMT query in milliseconds.
// If this option is not given, the SMTChecker will use a deterministic
// resource limit by default.
// A given timeout of 0 means no resource/time restrictions for any query.
"timeout": 20000
}
}
}
```

### Output Description

```
{
// Optional: not present if no errors/warnings/infos were encountered
"errors": [
{
// Optional: Location within the source file.
"sourceLocation": {
"file": "sourceFile.sol",
"start": 0,
"end": 100
},
// Optional: Further locations (e.g. places of conflicting declarations)
"secondarySourceLocations": [
{
"file": "sourceFile.sol",
"start": 64,
"end": 92,
"message": "Other declaration is here:"
}
],
// Mandatory: Error type, such as "TypeError", "InternalCompilerError", "Exception ", etc.
// See below for complete list of types.
"type": "TypeError",
// Mandatory: Component where the error originated, such as "general" etc.
"component": "general",
// Mandatory ("error", "warning" or "info", but please note that this may be extended in the future)
"severity": "error",
// Optional: unique code for the cause of the error
"errorCode": "3141",
// Mandatory
"message": "Invalid keyword",
// Optional: the message formatted with source location
"formattedMessage": "sourceFile.sol:100: Invalid keyword"
}
],
// This contains the file-level outputs.
// It can be limited/filtered by the outputSelection settings.
"sources": {
"sourceFile.sol": {
// Identifier of the source (used in source maps)
"id": 1,
// The AST object
"ast": {}
}
},
// This contains the contract-level outputs.
// It can be limited/filtered by the outputSelection settings.
"contracts": {
"sourceFile.sol": {
// If the language used has no contract names, this field should equal to an empty string.
"ContractName": {
// The Ethereum Contract ABI. If empty, it is represented as an empty array.
// See https://docs.soliditylang.org/en/develop/abi-spec.html
"abi": [],
// See the Metadata Output documentation (serialised JSON string)
"metadata": "{/* ... */}",
// User documentation (natspec)
"userdoc": {},
// Developer documentation (natspec)
"devdoc": {},
// Intermediate representation before optimization (string)
"ir": "",
// AST of intermediate representation before optimization
"irAst": {/* ... */},
// Intermediate representation after optimization (string)
"irOptimized": "",
// AST of intermediate representation after optimization
"irOptimizedAst": {/* ... */},
// See the Storage Layout documentation.
"storageLayout": {"storage": [/* ... */], "types": {/* ... */} },
// See the Storage Layout documentation.
"transientStorageLayout": {"storage": [/* ... */], "types": {/* ... */} },
// EVM-related outputs
"evm": {
// Assembly (string)
"assembly": "",
// Old-style assembly (object)
"legacyAssembly": {},
// Bytecode and related details.
"bytecode": {
// Ethdebug output (experimental)
"ethdebug": {/* ... */},
// Debugging data at the level of functions.
"functionDebugData": {
// Now follows a set of functions including compiler-internal and
// user-defined function. The set does not have to be complete.
"@mint_13": { // Internal name of the function
"entryPoint": 128, // Byte offset into the bytecode where the function starts (optional)
"id": 13, // AST ID of the function definition or null for compiler- internal functions (optional)
"parameterSlots": 2, // Number of EVM stack slots for the function
```

```parameters (optional)
"returnSlots": 1 // Number of EVM stack slots for the return values (optional)
}
},
// The bytecode as a hex string.
"object": "00fe",
// Opcodes list (string)
"opcodes": "",
// The source mapping as a string. See the source mapping definition.
"sourceMap": "",
// Array of sources generated by the compiler. Currently only
// contains a single Yul file.
"generatedSources": [{
// Yul AST
"ast": {/* ... */},
// Source file in its text form (may contain comments)
"contents":"{ function abi_decode(start, end) -> data { data := calldataload(start) } }",
// Source file ID, used for source references, same "namespace" as the Solidity source files
"id": 2,
"language": "Yul",
"name": "#utility.yul"
}],
// If given, this is an unlinked object.
"linkReferences": {
"libraryFile.sol": {
// Byte offsets into the bytecode.
// Linking replaces the 20 bytes located there.
"Library1": [
{ "start": 0, "length": 20 },
{ "start": 200, "length": 20 }
]
}
}
},
"deployedBytecode": {
// Ethdebug output (experimental)
"ethdebug": {/* ... */},
/* ..., */ // The same layout as above.
"immutableReferences": {
// There are two references to the immutable with AST ID 3, both 32 byteslong. One is
// at bytecode offset 42, the other at bytecode offset 80.
"3": [{ "start": 42, "length": 32 }, { "start": 80, "length": 32 }]
}
},
// The list of function hashes
"methodIdentifiers": {
"delegate(address)": "5c19a95c"
},
// Function gas estimates
"gasEstimates": {
"creation": {
"codeDepositCost": "420000",
"executionCost": "infinite",
"totalCost": "infinite"
},
"external": {
"delegate(address)": "25000"
},
"internal": {
"heavyLifting()": "infinite"
}
},
// Yul CFG representation of the SSA form (experimental)
"yulCFGJson": {/* ... */}
}
}
}
},
// Global Ethdebug output (experimental)
"ethdebug": {
// Requested via ethdebug.resources output selection
"resources": {/* ... */},
// Requested via ethdebug.compilation output selection
"compilation": {/* ... */}
}
}
```

### Error Types

- 1. JSONError: JSON input doesn’t conform to the required format, e.g. input is not a JSON object, the language is not supported, etc.

- 2. IOError: IO and import processing errors, such as unresolvable URL or hash mismatch in supplied sources.

- 3. ParserError: Source code doesn’t conform to the language rules.

- 4. DocstringParsingError: The NatSpec tags in the comment block cannot be parsed.

- 5. SyntaxError: Syntactical error, such as continue is used outside of a for loop.

- 6. DeclarationError: Invalid, unresolvable or clashing identifier names. e.g. Identifier not found

- 7. TypeError: Error within the type system, such as invalid type conversions, invalid assignments, etc.

- 8. UnimplementedFeatureError: Feature is not supported by the compiler, but is expected to be supported in future versions.

- 9. InternalCompilerError: Internal bug triggered in the compiler - this should be reported as an issue.

- 10. Exception: Unknown failure during compilation - this should be reported as an issue.

- 11. CompilerError: Invalid use of the compiler stack - this should be reported as an issue.

- 12. FatalError: Fatal error not processed correctly - this should be reported as an issue.

- 13. YulException: Error during Yul code generation - this should be reported as an issue.

- 14. Warning: A warning, which didn’t stop the compilation, but should be addressed if possible.

- 15. Info: Information that the compiler thinks the user might find useful, but is not dangerous and does not necessarily need to be addressed.

## 3.13.4 Experimental Mode

Some language and compiler features included in stable releases are not themselves considered stable. They are sparsely documented, if at all, often not adequately tested, and thus not yet intended for production use. In many cases it is possible to develop a big feature incrementally, with each iteration being already stable. Sometimes, however, it is preferable to start with a prototype and stabilize it over multiple releases, while receiving feedback from users. To prevent accidental use, such features can be only accessed by enabling the experimental mode.

There are no backwards compatibility guarantees for experimental features. They are subject to change in breaking ways in non-breaking releases of the compiler. Only major changes affecting them are recorded in the changelog.

To enable the experimental mode, use the --experimental flag on the command line, or the analogous settings. experimental boolean setting in the Standard JSON input.

Note that the use of this mode is recorded in the metadata:

- experimental flag in CBOR metadata is set to true,

- settings.experimental in JSON metadata is set to true,

**Note:**

Prior to version 0.8.35, most of the experimental features were usable without any extra safeguards. Some were gated behind pragma experimental, but this was not done consistently. The information about them was also only recorded in CBOR metadata and even then not always. The main goal of the experimental mode is to systematize this and make users fully aware when relying on features which are unfinished or not production-ready.

The table below details all currently available experimental features.

| Feature    | ID               | Affects | Flag/pragma                                     |
| ---------- | ---------------- | ------- | ----------------------------------------------- |
|            |                  | byte-   |                                                 |
|            |                  | code    |                                                 |
| AST import | ast-importyes    |         | --import-ast                                    |
| EVM As-    | evmasm-importyes |         | --import-asm-json                               |
| sembly     |                  |         |                                                 |
| import     |                  |         |                                                 |
| IR AST     | ir-ast           | no      | --ir-ast-json, --ir-optimized-ast-json          |
| Non-       | evm              | yes     | --evm-version <version name>                    |
| mainnet    |                  |         |                                                 |
| EVMs       |                  |         |                                                 |
| Ethdebug   | ethdebug         | no      | --ethdebug-resources, --ethdebug-compilation,   |
|            |                  |         | --ethdebug-program, --ethdebug-program-runtime, |
|            |                  |         | --debug-info ethdebug                           |
| SSA CFG    | ssa-cfg          | no      | --yul-cfg-json                                  |
|            |                  | yes     | --via-ssa-cfg                                   |

# 3.14 Analysing the Compiler Output

It is often useful to look at the assembly code generated by the compiler. The generated binary, i.e., the output of solc --bin contract.sol, is generally difficult to read. It is recommended to use the flag --asm to analyse the assembly output. Even for large contracts, looking at a visual diff of the assembly before and after a change is often very enlightening.

Consider the following contract (named, say contract.sol):

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.5.0 <0.9.0;
contract C {
function one() public pure returns (uint) {
return 1;
}
}
```

The following would be the output of solc --asm contract.sol

```
======= contract.sol:C =======
EVM assembly:
/* "contract.sol":0:86 contract C {... */
mstore(0x40, 0x80)
callvalue
dup1
iszero
tag_1
jumpi
0x00
dup1
revert
tag_1:
pop
dataSize(sub_0)
dup1
dataOffset(sub_0)
0x00
codecopy
0x00
return
stop
sub_0: assembly {
/* "contract.sol":0:86 contract C {... */
mstore(0x40, 0x80)
callvalue
dup1
iszero
tag_1
jumpi
0x00
dup1
revert
tag_1:
pop
jumpi(tag_2, lt(calldatasize, 0x04))
shr(0xe0, calldataload(0x00))
dup1
0x901717d1
eq
tag_3
jumpi
tag_2:
0x00
dup1
revert
/* "contract.sol":17:84 function one() public pure returns (uint) {... */
tag_3:
tag_4
tag_5
jump // in
tag_4:
mload(0x40)
tag_6
swap2
swap1
tag_7
jump // in
tag_6:
mload(0x40)
dup1
swap2
sub
swap1
return
tag_5:
/* "contract.sol":53:57 uint */
0x00
/* "contract.sol":76:77 1 */
0x01
/* "contract.sol":69:77 return 1 */
swap1
pop
/* "contract.sol":17:84 function one() public pure returns (uint) {... */
swap1
jump // out
/* "#utility.yul":7:125 */
tag_10:
/* "#utility.yul":94:118 */
tag_12
/* "#utility.yul":112:117 */
dup2
/* "#utility.yul":94:118 */
tag_13
jump // in
tag_12:
/* "#utility.yul":89:92 */
dup3
/* "#utility.yul":82:119 */
mstore
/* "#utility.yul":72:125 */
pop
pop
jump // out
/* "#utility.yul":131:353 */
tag_7:
0x00
/* "#utility.yul":262:264 */
0x20
/* "#utility.yul":251:260 */
dup3
/* "#utility.yul":247:265 */
add
/* "#utility.yul":239:265 */
swap1
pop
/* "#utility.yul":275:346 */
tag_15
/* "#utility.yul":343:344 */
0x00
/* "#utility.yul":332:341 */
dup4
/* "#utility.yul":328:345 */
add
/* "#utility.yul":319:325 */
dup5
/* "#utility.yul":275:346 */
tag_10
jump // in
tag_15:
/* "#utility.yul":229:353 */
swap3
swap2
pop
pop
jump // out
/* "#utility.yul":359:436 */
tag_13:
0x00
/* "#utility.yul":425:430 */
dup2
/* "#utility.yul":414:430 */
swap1
pop
/* "#utility.yul":404:436 */
swap2
swap1
pop
```

jump // out auxdata: 0xa2646970667358221220a5874f19737ddd4c5d77ace1619e5160c67b3d4bedac75fce908fed32d98899864736f6c63782730

}

Alternatively, the above output can also be obtained from Remix, under the option “Compilation Details” after com- (https://remix.ethereum.org/)

piling a contract.

Notice that the asm output starts with the creation / constructor code. The deploy code is provided as part of the sub object (in the above example, it is part of the sub-object sub_0). The auxdata field corresponds to the contract metadata. The comments in the assembly output point to the source location. Note that #utility.yul is an internally generated file of utility functions that can be obtained using the flags --combined-json generated-sources, generated-sources-runtime.

Similarly, the optimized assembly can be obtained with the command: solc --optimize --asm contract.sol.

Often times, it is interesting to see if two different sources in Solidity result in the same optimized code. For example, to see if the expressions (a * b) / c, a * b / c generates the same bytecode. This can be easily done by taking a diff of the corresponding assembly output, after potentially stripping comments that reference the source locations.

**Note:**

The --asm output is not designed to be machine readable. Therefore, there may be breaking changes on the output between minor versions of solc.


# 3.33 Import Path Resolution

In order to be able to support reproducible builds on all platforms, the Solidity compiler has to abstract away the details of the filesystem where source files are stored. Paths used in imports must work the same way everywhere while the command-line interface must be able to work with platform-specific paths to provide good user experience. This section aims to explain in detail how Solidity reconciles these requirements.

## 3.33.1 Virtual Filesystem

The compiler maintains an internal database (virtual filesystem or VFS for short) where each source unit is assigned a unique source unit name which is an opaque and unstructured identifier. When you use the import statement, you specify an import path that references a source unit name.

### Import Callback

The VFS is initially populated only with files the compiler has received as input. Additional files can be loaded during compilation using an import callback, which is different depending on the type of compiler you use (see below). If the compiler does not find any source unit name matching the import path in the VFS, it invokes the callback, which is responsible for obtaining the source code to be placed under that name. An import callback is free to interpret source unit names in an arbitrary way, not just as paths. If there is no callback available when one is needed or if it fails to locate the source code, compilation fails.

By default, the command-line compiler provides the Host Filesystem Loader - a rudimentary callback that interprets a source unit name as a path in the local filesystem. This callback can be disabled using the --no-import-callback command-line option. The JavaScript interface does not provide any by default, but one can be provided by the user. This mechanism can be used to obtain source code from locations other than the local filesystem (which may not even be accessible, e.g. when the compiler is running in a browser). For example the Remix IDE provides a versatile callback that lets you import files from HTTP, IPFS and Swarm URLs or refer directly to packages in NPM registry. (https://remix-ide.readthedocs.io/en/latest/import.html)

**Note:**

Host Filesystem Loader’s file lookup is platform-dependent. For example backslashes in a source unit name can be interpreted as directory separators or not and the lookup can be case-sensitive or not, depending on the underlying platform.

For portability it is recommended to avoid using import paths that will work correctly only with a specific import callback or only on one platform. For example you should always use forward slashes since they work as path separators also on platforms that support backslashes.

### Initial Content of the Virtual Filesystem

The initial content of the VFS depends on how you invoke the compiler:

### 1. solc / command-line interface

When you compile a file using the command-line interface of the compiler, you provide one or more paths to files containing Solidity code:

solc contract.sol /usr/local/dapp-bin/token.sol

The source unit name of a file loaded this way is constructed by converting its path to a canonical form and, if possible, making it relative to either the base path or one of the include paths. See CLI Path Normalization and Stripping for a detailed description of this process.

### 2. Standard JSON

When using the StandardJSON API (via either the JavaScript interface or the --standard-json command-line option) you provide input in JSON format, containing, among other things, the content of all your source files: (https://github.com/argotorg/solc-js)

```
{
"language": "Solidity",
"sources": {
"contract.sol": {
"content": "import \"./util.sol\";\ncontract C {}"
},
"util.sol": {
"content": "library Util {}"
},
"/usr/local/dapp-bin/token.sol": {
"content": "contract Token {}"
}
},
"settings": {"outputSelection": {"*": { "*": ["metadata", "evm.bytecode"]}}}
}
```

The sources dictionary becomes the initial content of the virtual filesystem and its keys are used as source unit names.

### 3. Standard JSON (via import callback)

With Standard JSON it is also possible to tell the compiler to use the import callback to obtain the source code:

```
{
"language": "Solidity",
"sources": {
"/usr/local/dapp-bin/token.sol": {
"urls": [
"/projects/mytoken.sol",
"https://example.com/projects/mytoken.sol"
]
}
},
"settings": {"outputSelection": {"*": { "*": ["metadata", "evm.bytecode"]}}}
}
```

If an import callback is available, the compiler will give it the strings specified in urls one by one, until one is loaded successfully or the end of the list is reached.

The source unit names are determined the same way as when using content - they are keys of the sources dictionary and the content of urls does not affect them in any way.

### 4. Standard input

On the command-line it is also possible to provide the source by sending it to compiler’s standard input:

```
echo 'import "./util.sol"; contract C {}' | solc -
```

\- used as one of the arguments instructs the compiler to place the content of the standard input in the virtual filesystem under a special source unit name: <stdin>.

Once the VFS is initialized, additional files can still be added to it only through the import callback.

## 3.33.2 Imports

The import statement specifies an import path. Based on how the import path is specified, we can divide imports into two categories:

- Direct imports, where you specify the full source unit name directly.

- Relative imports, where you specify a path starting with ./ or ../ to be combined with the source unit name of the importing file.

_Listing 1: contracts/contract.sol_

```
import "./math/math.sol";
import "contracts/tokens/token.sol";
```

In the above ./math/math.sol and contracts/tokens/token.sol are import paths while the source unit names they translate to are contracts/math/math.sol and contracts/tokens/token.sol respectively.

### Direct Imports

An import that does not start with ./ or ../ is a direct import.

```
import "/project/lib/util.sol"; // source unit name: /project/lib/util.sol
import "lib/util.sol"; // source unit name: lib/util.sol
import "@openzeppelin/address.sol"; // source unit name: @openzeppelin/address.sol
import "https://example.com/token.sol"; // source unit name: https://example.com/token. sol
```

After applying any import remappings the import path simply becomes the source unit name.

**Note:**

A source unit name is just an identifier and even if its value happens to look like a path, it is not subject to the normalization rules you would typically expect in a shell. Any /./ or /../ segments or sequences of multiple slashes remain a part of it. When the source is provided via Standard JSON interface it is entirely possible to associate different content with source unit names that would refer to the same file on disk.

When the source is not available in the virtual filesystem, the compiler passes the source unit name to the import callback. The Host Filesystem Loader will attempt to use it as a path and look up the file on disk. At this point the platform-specific normalization rules kick in and names that were considered different in the VFS may actually result in the same file being loaded. For example /project/lib/math.sol and /project/lib/../lib///math.sol are considered completely different in the VFS even though they refer to the same file on disk.

**Note:**

Even if an import callback ends up loading source code for two different source unit names from the same file on disk, the compiler will still see them as separate source units. It is the source unit name that matters, not the physical location of the code.

### Relative Imports

An import starting with ./ or ../ is a relative import. Such imports specify a path relative to the source unit name of the importing source unit:

_Listing 2: /project/lib/math.sol_

```
import "./util.sol" as util; // source unit name: /project/lib/util.sol
import "../token.sol" as token; // source unit name: /project/token.sol
```

_Listing 3: lib/math.sol_

```
import "./util.sol" as util; // source unit name: lib/util.sol
import "../token.sol" as token; // source unit name: token.sol
```

**Note:**

Relative imports always start with ./ or ../ so import "util.sol", unlike import "./util.sol", is a direct import. While both paths would be considered relative in the host filesystem, util.sol is actually absolute in the VFS.

Let us define a path segment as any non-empty part of the path that does not contain a separator and is bounded by two path separators. A separator is a forward slash or the beginning/end of the string. For example in ./abc/..// there are three path segments: ., abc and ...

The compiler resolves the import into a source unit name based on the import path, in the following way:

- 1. We start with the source unit name of the importing source unit.

- 2. The last path segment with preceding slashes is removed from the resolved name.

- 3. Then, for every segment in the import path, starting from the leftmost one:

- If the segment is ., it is skipped.

- If the segment is .., the last path segment with preceding slashes is removed from the resolved name.

- Otherwise, the segment (preceded by a single slash if the resolved name is not empty), is appended to the resolved name.

The removal of the last path segment with preceding slashes is understood to work as follows:

- 1. Everything past the last slash is removed (i.e. a/b//c.sol becomes a/b//).

- 2. All trailing slashes are removed (i.e. a/b// becomes a/b).

Note that the process normalizes the part of the resolved source unit name that comes from the import path according to the usual rules for UNIX paths, i.e. all . and .. are removed and multiple slashes are squashed into a single one. On the other hand, the part that comes from the source unit name of the importing module remains unnormalized. This ensures that the protocol:// part does not turn into protocol:/ if the importing file is identified with a URL.

If your import paths are already normalized, you can expect the above algorithm to produce very intuitive results. Here are some examples of what you can expect if they are not:

_Listing 4: lib/src/../contract.sol_

```
import "./util/./util.sol"; // source unit name: lib/src/../util/util.sol
import "./util//util.sol"; // source unit name: lib/src/../util/util.sol
import "../util/../array/util.sol"; // source unit name: lib/src/array/util.sol
import "../.././../util.sol"; // source unit name: util.sol
import "../../.././../util.sol"; // source unit name: util.sol
```

**Note:**

The use of relative imports containing leading .. segments is not recommended. The same effect can be achieved in a more reliable way by using direct imports with base path and include paths.

## 3.33.3 Base Path and Include Paths

The base path and include paths represent directories that the Host Filesystem Loader will load files from. When a source unit name is passed to the loader, it prepends the base path to it and performs a filesystem lookup. If the lookup does not succeed, the same is done with all directories on the include path list.

It is recommended to set the base path to the root directory of your project and use include paths to specify additional locations that may contain libraries your project depends on. This lets you import from these libraries in a uniform way, no matter where they are located in the filesystem relative to your project. For example, if you use npm to install packages and your contract imports @openzeppelin/contracts/utils/Strings.sol, you can use these options to tell the compiler that the library can be found in one of the npm package directories:

```
solc contract.sol \
--base-path . \
--include-path node_modules/ \
--include-path /usr/local/lib/node_modules/
```

Your contract will compile (with the same exact metadata) no matter whether you install the library in the local or global package directory or even directly under your project root.

By default the base path is empty, which leaves the source unit name unchanged. When the source unit name is a relative path, this results in the file being looked up in the directory the compiler has been invoked from. It is also the only value that results in absolute paths in source unit names being actually interpreted as absolute paths on disk. If the base path itself is relative, it is interpreted as relative to the current working directory of the compiler.

**Note:**

Include paths cannot have empty values and must be used together with a non-empty base path.

**Note:**

Include paths and base path can overlap as long as it does not make import resolution ambiguous. For example, you can specify a directory inside base path as an include directory or have an include directory that is a subdirectory of another include directory. The compiler will only issue an error if the source unit name passed to the Host Filesystem Loader represents an existing path when combined with multiple include paths or an include path and base path.

### CLI Path Normalization and Stripping

On the command-line the compiler behaves just as you would expect from any other program: it accepts paths in a format native to the platform and relative paths are relative to the current working directory. The source unit names assigned to files whose paths are specified on the command-line, however, should not change just because the project is being compiled on a different platform or because the compiler happens to have been invoked from a different directory. To achieve this, paths to source files coming from the command-line must be converted to a canonical form, and, if possible, made relative to the base path or one of the include paths.

The normalization rules are as follows:

- If a path is relative, it is made absolute by prepending the current working directory to it.

- Internal . and .. segments are collapsed.

- Platform-specific path separators are replaced with forward slashes.

- Sequences ofmultiple consecutive path separators are squashed into a single separator (unless they are the leading slashes of an UNC path).

- If the path includes a root name (e.g. a drive letter onWindows) and the root is the same as the root of the current working directory, the root is replaced with /.

- Symbolic links in the path are not resolved.

- The only exception is the path to the current working directory prepended to relative paths in the process of making them absolute. On some platforms the working directory is reported always with symbolic links resolved so for consistency the compiler resolves them everywhere.

- The original case of the path is preserved even if the filesystem is case-insensitive but case-preserving and the actual case on disk is different. (https://en.wikipedia.org/wiki/Case_preservation)

**Note:**

There are situations where paths cannot be made platform-independent. For example onWindows the compiler can avoid using drive letters by referring to the root directory of the current drive as / but drive letters are still necessary for paths leading to other drives. You can avoid such situations by ensuring that all the files are available within a single directory tree on the same drive.

After normalization the compiler attempts to make the source file path relative. It tries the base path first and then the include paths in the order they were given. If the base path is empty or not specified, it is treated as if it was equal to the path to the current working directory (with all symbolic links resolved). The result is accepted only if the normalized directory path is the exact prefix of the normalized file path. Otherwise the file path remains absolute. This makes the conversion unambiguous and ensures that the relative path does not start with ../. The resulting file path becomes the source unit name.

**Note:**

The relative path produced by stripping must remain unique within the base path and include paths. For example the compiler will issue an error for the following command if both /project/contract.sol and /lib/contract. sol exist:

solc /project/contract.sol --base-path /project --include-path /lib

**Note:**

Prior to version 0.8.8, CLI path stripping was not performed and the only normalization applied was the conversion of path separators. When working with older versions of the compiler it is recommended to invoke the compiler from the base path and to only use relative paths on the command-line.

## 3.33.4 Allowed Paths

As a security measure, the Host Filesystem Loader will refuse to load files from outside of a few locations that are considered safe by default:

- Outside of Standard JSON mode:

- The directories containing input files listed on the command-line.

- The directories used as remapping targets. If the target is not a directory (i.e does not end with /, /. or /..) the directory containing the target is used instead.

- Base path and include paths.

- In Standard JSON mode:

- Base path and include paths.

Additional directories can be whitelisted using the --allow-paths option. The option accepts a comma-separated list of paths:

```
cd /home/user/project/
solc token/contract.sol \
lib/util.sol=libs/util.sol \
--base-path=token/ \
--include-path=/lib/ \
--allow-paths=../utils/,/tmp/libraries
```

When the compiler is invoked with the command shown above, the Host Filesystem Loader will allow importing files from the following directories:

- /home/user/project/token/ (because token/ contains the input file and also because it is the base path),

- /lib/ (because /lib/ is one of the include paths),

- /home/user/project/libs/ (because libs/ is a directory containing a remapping target),

- /home/user/utils/ (because of ../utils/ passed to --allow-paths),

- /tmp/libraries/ (because of /tmp/libraries passed to --allow-paths),

**Note:**

The working directory of the compiler is one of the paths allowed by default only if it happens to be the base path (or the base path is not specified or has an empty value).

**Note:**

The compiler does not check if allowed paths actually exist and whether they are directories. Non-existent or empty paths are simply ignored. If an allowed path matches a file rather than a directory, the file is considered whitelisted, too.

**Note:**

Allowed paths are case-sensitive even if the filesystem is not. The case must exactly match the one used in your imports. For example --allow-paths tokens will not match import "Tokens/IERC20.sol".

**Warning:**

Files and directories only reachable through symbolic links from allowed directories are not automatically whitelisted. For example if token/contract.sol in the example above was actually a symlink pointing at / etc/passwd the compiler would refuse to load it unless /etc/ was one of the allowed paths too.

## 3.33.5 Import Remapping

Import remapping allows you to redirect imports to a different location in the virtual filesystem. The mechanism works by changing the translation between import paths and source unit names. For example you can set up a remapping so that any import from the virtual directory github.com/ethereum/dapp-bin/library/ would be seen as an import from dapp-bin/library/ instead.

You can limit the scope of a remapping by specifying a context. This allows creating remappings that apply only to imports located in a specific library or a specific file. Without a context a remapping is applied to every matching import in all the files in the virtual filesystem.

Import remappings have the form of context:prefix=target:

- context must match the beginning of the source unit name of the file containing the import.

- prefix must match the beginning of the source unit name resulting from the import.

- target is the value the prefix is replaced with.

For example, if you clone https://github.com/ethereum/dapp-bin/ locally to /project/dapp-bin and run the compiler (https://github.com/ethereum/dapp-bin/)

with:

solc github.com/ethereum/dapp-bin/=dapp-bin/ --base-path /project source.sol you can use the following in your source file:

import "github.com/ethereum/dapp-bin/library/math.sol"; // source unit name: dapp-bin/  library/math.sol

The compiler will look for the file in the VFS under dapp-bin/library/math.sol. If the file is not available there, the source unit name will be passed to the Host Filesystem Loader, which will then look in /project/dapp-bin/ library/math.sol.

**Warning:**

Information about remappings is stored in contract metadata. Since the binary produced by the compiler has a hash of the metadata embedded in it, any modification to the remappings will result in different bytecode.

For this reason you should be careful not to include any local information in remapping targets. For example if your library is located in /home/user/packages/mymath/math.sol, a remapping like @math/=/home/user/ packages/mymath/ would result in your home directory being included in the metadata. To be able to reproduce the same bytecode with such a remapping on a different machine, you would need to recreate parts of your local directory structure in the VFS and (if you rely on Host Filesystem Loader) also in the host filesystem.

To avoid having your local directory structure embedded in the metadata, it is recommended to designate the direc-

tories containing libraries as include paths instead. For example, in the example above --include-path /home/ user/packages/ would let you use imports starting with mymath/. Unlike remapping, the option on its own will not make mymath appear as @math but this can be achieved by creating a symbolic link or renaming the package subdirectory.

As a more complex example, suppose you rely on a module that uses an old version of dapp-bin that you checked out to /project/dapp-bin_old, then you can run:

```
solc module1:github.com/ethereum/dapp-bin/=dapp-bin/ \
module2:github.com/ethereum/dapp-bin/=dapp-bin_old/ \
--base-path /project \
source.sol
```

This means that all imports in module2 point to the old version but imports in module1 point to the new version.

Here are the detailed rules governing the behavior of remappings:

- 1. Remappings only affect the translation between import paths and source unit names.

Source unit names added to the VFS in any other way cannot be remapped. For example the paths you specify on the command-line and the ones in sources.urls in Standard JSON are not affected.

```
solc /project/=/contracts/ /project/contract.sol # source unit name: /project/ contract.sol
```

In the example above the compiler will load the source code from /project/contract.sol and place it under that exact source unit name in the VFS, not under /contract/contract.sol.

- 2. Context and prefix must match source unit names, not import paths.

- This means that you cannot remap ./ or ../ directly since they are replaced during the translation to source unit name but you can remap the part of the name they are replaced with:

```
solc ./=a/ /project/=b/ /project/contract.sol # source unit name: /project/ contract.sol
```

_Listing 5: /project/contract.sol_

```
import "./util.sol" as util; // source unit name: b/util.sol
```

- You cannot remap base path or any other part of the path that is only added internally by an import callback:

```
solc /project/=/contracts/ /project/contract.sol --base-path /project # source unit name: contract.sol
```

_Listing 6: /project/contract.sol_

```
import "util.sol" as util; // source unit name: util.sol
```

- 3. Target is inserted directly into the source unit name and does not necessarily have to be a valid path.

- It can be anything as long as the import callback can handle it. In case of the Host Filesystem Loader this includes also relative paths. When using the JavaScript interface you can even use URLs and abstract identifiers if your callback can handle them.

- Remapping happens after relative imports have already been resolved into source unit names. This means that targets starting with ./ and ../ have no special meaning and are relative to the base path rather than to the location of the source file.

- Remapping targets are not normalized so @root/=./a/b// will remap @root/contract.sol to ./a/b/ /contract.sol and not a/b/contract.sol.

- If the target does not end with a slash, the compiler will not add one automatically:

```
solc /project/=/contracts /project/contract.sol # source unit name: /project/ contract.sol
```

_Listing 7: /project/contract.sol_

import

"/project/util.sol" as util;

// source unit name: /contractsutil.sol

- 4. Context and prefix are patterns and matches must be exact.

- a//b=c will not match a/b.

- source unit names are not normalized so a/b=c will not match a//b either.

- Parts of file and directory names can match as well. /newProject/con:/new=old will match / newProject/contract.sol and remap it to oldProject/contract.sol.

- 5. At most one remapping is applied to a single import.

- If multiple remappings match the same source unit name, the one with the longest matching context is chosen.

- If contexts are identical, the one with the longest matching prefix is chosen.

- If contexts and prefixes are identical, the one specified last wins.

- Remappings do not work on other remappings. For example a=b b=c c=d will not result in a being remapped to d.

- 6. Prefix cannot be empty but context and target are optional.

- If target is the empty string, prefix is simply removed from import paths.

- Empty context means that the remapping applies to all imports in all source units.

## 3.33.6 Using URLs in imports

Most URL prefixes such as https:// or data:// have no special meaning in import paths. The only exception is file:// which is stripped from source unit names by the Host Filesystem Loader.

When compiling locally you can use import remapping to replace the protocol and domain part with a local path:

Note the leading :, which is necessary when the remapping context is empty. Otherwise the https: part would be interpreted by the compiler as the context.
