# Contract Metadata (3.22) & Contract ABI Specification (3.23)

> Source: Solidity documentation, release 0.8.37-develop (Sep 10, 2026), https://docs.soliditylang.org/ — text reproduced from the official docs; code indentation was flattened by the export and is not normative.

## Contents

- 3.22 Contract Metadata
  - 3.22.1 Encoding of the Metadata Hash in the Bytecode
  - 3.22.2 Usage for Automatic Interface Generation and NatSpec
  - 3.22.3 Usage for Source Code Verification
- 3.23 Contract ABI Specification
  - 3.23.1 Basic Design
  - 3.23.2 Function Selector
  - 3.23.3 Argument Encoding
  - 3.23.4 Types
  - 3.23.5 Design Criteria for the Encoding
  - 3.23.6 Formal Specification of the Encoding
  - 3.23.7 Function Selector and Argument Encoding
  - 3.23.8 Examples
  - 3.23.9 Use of Dynamic Types
  - 3.23.10 Events
  - 3.23.11 Errors
  - 3.23.12 JSON
  - 3.23.13 Strict Encoding Mode
  - 3.23.14 Non-standard Packed Mode
  - 3.23.15 Encoding of Indexed Event Parameters

---

# 3.22 Contract Metadata

The Solidity compiler automatically generates a JSON file. The file contains two kinds of information about the compiled contract:

- How to interact with the contract: ABI, and NatSpec documentation.

- How to reproduce the compilation and verify a deployed contract: compiler version, compiler settings, and source files used.

The compiler appends by default the IPFS hash of the metadata file to the end of the runtime bytecode (not necessarily the creation bytecode) of each contract, so that, if published, you can retrieve the file in an authenticated way without having to resort to a centralized data provider. The other available options are the Swarm hash and not appending the metadata hash to the bytecode. These can be configured via the Standard JSON Interface.

You have to publish the metadata file to IPFS, Swarm, or another service so that others can access it. You create the file by using the solc --metadata command together with the --output-dir parameter. Without the parameter, the metadata will be written to standard output. The metadata contains IPFS and Swarm references to the source code, so you have to upload all source files in addition to the metadata file. For IPFS, the hash contained in the CID returned by ipfs add (not the direct sha2-256 hash of the file) shall match with the one contained in the bytecode.

The metadata file has the following format. The example below is presented in a human-readable way. Properly formatted metadata should use quotes correctly, reduce whitespace to a minimum, and sort the keys of all objects in alphabetical order to arrive at a canonical formatting. Comments are not permitted and are used here only for explanatory purposes.

```
{
// Required: Details about the compiler, contents are specific
// to the language.
"compiler": {
// Optional: Hash of the compiler binary which produced this output
"keccak256": "0x123...",
// Required for Solidity: Version of the compiler
"version": "0.8.2+commit.661d1103"
},
// Required: Source code language, basically selects a "sub-version"
// of the specification
"language": "Solidity",
// Required: Generated information about the contract.
"output": {
// Required: ABI definition of the contract. See "Contract ABI Specification"
"abi": [/* ... */],
// Required: NatSpec developer documentation of the contract. See https://docs. soliditylang.org/en/latest/natspec-format.html for details.
"devdoc": {
// Contents of the @author NatSpec field of the contract
"author": "John Doe",
// Contents of the @dev NatSpec field of the contract
"details": "Interface of the ERC20 standard as defined in the EIP. See https:// eips.ethereum.org/EIPS/eip-20 for details",
"errors": {
"MintToZeroAddress()" : {
"details": "Cannot mint to zero address"
}
},
"events": {
"Transfer(address,address,uint256)": {
"details": "Emitted when `value` tokens are moved from one account (`from`) toanother (`to`).",
"params": {
"from": "The sender address",
"to": "The receiver address",
"value": "The token amount"
}
}
},
"kind": "dev",
"methods": {
"transfer(address,uint256)": {
// Contents of the @dev NatSpec field of the method
"details": "Returns a boolean value indicating whether the operation succeeded. Must be called by the token holder address",
// Contents of the @param NatSpec fields of the method
"params": {
"_value": "The amount tokens to be transferred",
"_to": "The receiver address"
},
// Contents of the @return NatSpec field.
"returns": {
// Return var name (here "success") if exists. "_0" as key if return var is unnamed
"success": "a boolean value indicating whether the operation succeeded"
}
}
},
"stateVariables": {
"owner": {
// Contents of the @dev NatSpec field of the state variable
"details": "Must be set during contract creation. Can then only be changed by the owner"
}
},
// Contents of the @title NatSpec field of the contract
"title": "MyERC20: an example ERC20",
"version": 1 // NatSpec version
},
// Required: NatSpec user documentation of the contract. See "NatSpec Format"
"userdoc": {
"errors": {
"ApprovalCallerNotOwnerNorApproved()": [
{
"notice": "The caller must own the token or be an approved operator."
}
]
},
"events": {
"Transfer(address,address,uint256)": {
"notice": "`_value` tokens have been moved from `from` to `to`"
}
},
"kind": "user",
"methods": {
"transfer(address,uint256)": {
"notice": "Transfers `_value` tokens to address `_to`"
}
},
"version": 1 // NatSpec version
}
},
// Required: Compiler settings.
// Reflects the settings in the JSON input during compilation, except:
// - Different format: "libraries" field
// - Added field in metadata.settings: "compilationTarget"
// - Not in metadata.settings: "stopAfter", "debug.debugInfo", "outputSelection"
// See the standard JSON input's "settings" field docs for the rest.
"settings": {
// Required for Solidity: File path and the name of the contract or library this
// metadata is created for. This field is not present in the standard JSON input settings.
"compilationTarget": {
"myDirectory/myFile.sol": "MyContract"
},
// Optional (false if omitted): Indicates whether experimental mode has been enabled.
// Always matches the value of the `experimental` flag in CBOR metadata.
// Note that experimental mode being enabled does not necessarily mean that any
// experimental features were actually used, or if they were, that those features
// affected the bytecode.
"experimental": true,
// Required for Solidity: Addresses for libraries used.
// Note that metadata has a different format for "libraries" field than the standard JSON input.
// metadata format = { "MyLib.sol:MyLib": "0x123123..." }
// standard JSON input format = { "MyLib.sol": { "MyLib": "0x123123..." } }
"libraries": {
"MyLib.sol:MyLib": "0x123123..."
},
// ...
// ...
// ...
// The rest of the fields and their defaults same as in std JSON input.
},
// Required: Compilation source files/source units, keys are file paths
"sources": {
"settable": {
// Required (unless "url" is used): literal contents of the source file
"content": "contract settable is owned { uint256 private x = 0; function set(uint256 _x) public { if (msg.sender == owner) x = _x; } }",
// Required: keccak256 hash of the source file
"keccak256": "0x234..."
},
"myDirectory/myFile.sol": {
// Required: keccak256 hash of the source file
"keccak256": "0x123...",
// Optional: SPDX license identifier as given in the source file
"license": "MIT",
// Required (unless "content" is used, see above): Sorted URL(s)
// to the source file, protocol is more or less arbitrary, but an
// IPFS URL is recommended
"urls": [ "bzz-raw://7d7a...", "dweb:/ipfs/QmN..." ]
}
},
// Required: The version of the metadata format
"version": 1
}
```

**Warning:**

Since the bytecode of the resulting contract contains the metadata hash by default, any change to the metadata might result in a change of the bytecode. This includes changes to a filename or path, and since the metadata includes a hash of all the sources used, a single whitespace change results in different metadata, and different bytecode.

**Note:**

The ABI definition above has no fixed order. It can change with compiler versions. Starting from Solidity version 0.5.12, though, the array maintains a certain order.

## 3.22.1 Encoding of the Metadata Hash in the Bytecode

The compiler currently by default appends the IPFS hash (in CID v0) of the canonical metadata file and the compiler (https://docs.ipfs.tech/concepts/content-addressing/#version-0-v0)

version to the end of the bytecode. Optionally, a Swarm hash instead of the IPFS, or an experimental flag is used. Below are all the possible fields: (https://docs.ipfs.tech/concepts/content-addressing/#version-0-v0)

```
{
// Present if "bytecodeHash" was "ipfs" in compiler settings
"ipfs": "<metadata hash>",
// Present if "bytecodeHash" was "bzzr1" in compiler settings
"bzzr1": "<metadata hash>",
// Previous versions were using "bzzr0" instead of "bzzr1"
"bzzr0": "<metadata hash>",
// Present if experimental mode has been enabled either via "--experimental" flag or
// "settings.experimental" option in Standard JSON
"experimental": true,
"solc": "<compiler version>"
}
```

Because we might support other ways to retrieve the metadata file in the future, this information is stored CBOR- (https://tools.ietf.org/html/rfc7049)

encoded. The last two bytes in the bytecode indicate the length of the CBOR encoded information. By looking at this length, the relevant part of the bytecode can be decoded with a CBOR decoder. (https://tools.ietf.org/html/rfc7049)

Check the Metadata Playground to see it in action. (https://playground.sourcify.dev/)

Whereas release builds of solc use a 3 byte encoding of the version as shown above (one byte each for major, minor and patch version number), pre-release builds will instead use a complete version string including commit hash and build date.

The commandline flag --no-cbor-metadata can be used to skip metadata from getting appended at the end of the deployed bytecode. Equivalently, the boolean field settings.metadata.appendCBOR in Standard JSON input can be set to false.

**Note:**

The CBOR mapping can also contain other keys, so it is better to fully decode the data by looking at the end of the bytecode for the CBOR length, and to use a proper CBOR parser. Do not rely on it starting with 0xa264 or 0x64 'i' 'p' 'f' 's'.

0xa2

## 3.22.2 Usage for Automatic Interface Generation and NatSpec

The metadata is used in the following way: A component that wants to interact with a contract (e.g. a wallet) retrieves the code of the contract. It decodes the CBOR encoded section containing the IPFS/Swarm hash of the metadata file. With that hash, the metadata file is retrieved. That file is JSON-decoded into a structure like above.

The component can then use the ABI to automatically generate a rudimentary user interface for the contract.

Furthermore, the wallet can use the NatSpec user documentation to display a human-readable confirmation message to the user whenever they interact with the contract, together with requesting authorization for the transaction signature.

For additional information, read Ethereum Natural Language Specification (NatSpec) format.

## 3.22.3 Usage for Source Code Verification

If pinned/published, it is possible to retrieve the metadata of the contract from IPFS/Swarm. The metadata file also contains the URLs or the IPFS hashes of the source files, as well as the compilation settings, i.e. everything needed to reproduce a compilation.

With this information it is then possible to verify the source code of a contract by reproducing the compilation, and comparing the bytecode from the compilation with the bytecode of the deployed contract.

This automatically verifies the metadata since its hash is part of the bytecode, as well as the source codes, because their hashes are part of the metadata. Any change in the files or settings would result in a different metadata hash. The metadata here serves as a fingerprint of the whole compilation.

Sourcify makes use of this feature for “full/perfect verification”, as well as pinning the files publicly on IPFS to be (https://sourcify.dev)

accessed with the metadata hash. (https://sourcify.dev)

# 3.23 Contract ABI Specification

## 3.23.1 Basic Design

The Contract Application Binary Interface (ABI) is the standard way to interact with contracts in the Ethereum ecosys-

tem, both from outside the blockchain and for contract-to-contract interaction. Data is encoded according to its type, as described in this specification. The encoding is not self describing and thus requires a schema in order to decode.

We assume that the interface functions of a contract are strongly typed, known at compilation time and static. We assume that all contracts will have the interface definitions of any contracts they call available at compile-time.

This specification does not address contracts whose interface is dynamic or otherwise known only at run-time. Also, the ABI specification for libraries is slightly different.

## 3.23.2 Function Selector

The first four bytes of the call data for a function call specifies the function to be called. It is the first (left, high-order in big-endian) four bytes of the Keccak-256 hash of the signature of the function. The signature is defined as the canonical expression of the basic prototype without data location specifier, i.e. the function name with the parenthesised list of parameter types. Parameter types are split by a single comma — no spaces are used.

**Note:**

The return type of a function is not part of this signature. In Solidity’s function overloading return types are not considered. The reason is to keep function call resolution context-independent. The JSON description of the ABI however contains both inputs and outputs.

## 3.23.3 Argument Encoding

Starting from the fifth byte, the encoded arguments follow. This encoding is also used in other places, e.g. the return values and also event arguments are encoded in the same way, without the four bytes specifying the function.

## 3.23.4 Types

Note that the library ABIs can take types different than below e.g. for non-storage structs. See library selectors for details.

The following elementary types exist:

- uint<M>: unsigned integer type of M bits, 0 < M <= 256, M % 8 == 0. e.g. uint32, uint8, uint256.

- int<M>: two’s complement signed integer type of M bits, 0 < M <= 256, M % 8 == 0.

- address: equivalent to uint160, except for the assumed interpretation and language typing. For computing the function selector, address is used.

- uint, int: synonyms for uint256, int256 respectively. For computing the function selector, uint256 and int256 have to be used.

- bool: equivalent to uint8 restricted to the values 0 and 1. For computing the function selector, bool is used.

- fixed<M>x<N>: signed fixed-point decimal number of M bits, 8 <= M <= 256, M % 8 == 0, and 0 < N <= 80, which denotes the value v as v / (10 ** N).

- ufixed<M>x<N>: unsigned variant of fixed<M>x<N>.

- fixed, ufixed: synonyms for fixed128x18, ufixed128x18 respectively. For computing the function selector, fixed128x18 and ufixed128x18 have to be used.

- bytes<M>: binary type of M bytes, 0 < M <= 32.

- function: an address (20 bytes) followed by a function selector (4 bytes). Encoded identical to bytes24.

The following (fixed-size) array type exists:

- <type>[M]: a fixed-length array of M elements, M >= 0, of the given type.

**Note:**

While this ABI specification can express fixed-length arrays with zero elements, they’re not supported by the compiler.

The following non-fixed-size types exist:

- bytes: dynamic sized byte sequence.

- string: dynamic sized unicode string assumed to be UTF-8 encoded.

- <type>[]: a variable-length array of elements of the given type.

Types can be combined to a tuple by enclosing them inside parentheses, separated by commas:

- (T1,T2,...,Tn): tuple consisting of the types T1, . . . , Tn, n >= 0

It is possible to form tuples of tuples, arrays of tuples and so on. It is also possible to form zero-tuples (where n ==

0).

### Mapping Solidity to ABI types

Solidity supports all the types presented above with the same names with the exception of tuples. On the other hand, some Solidity types are not supported by the ABI. The following table shows on the left column Solidity types that are not part of the ABI, and on the right column the ABI types that represent them.

| Solidity                 | ABI                       |
| ------------------------ | ------------------------- |
| address payable          | address                   |
| contract                 | address                   |
| enum                     | uint8                     |
| user defined value types | its underlying value type |
| struct                   | tuple                     |

**Warning:**

Before version 0.8.0 enums could have more than 256 members and were represented by the smallest integer type just big enough to hold the value of any member.

## 3.23.5 Design Criteria for the Encoding

The encoding is designed to have the following properties, which are especially useful if some arguments are nested arrays:

- 1. The number of reads necessary to access a value is at most the depth of the value inside the argument array structure, i.e. four reads are needed to retrieve a_i[k][l][r]. In a previous version of the ABI, the number of reads scaled linearly with the total number of dynamic parameters in the worst case.

- 2. The data of a variable or an array element is not interleaved with other data and it is relocatable, i.e. it only uses relative “addresses”.

## 3.23.6 Formal Specification of the Encoding

We distinguish static and dynamic types. Static types are encoded in-place and dynamic types are encoded at a sepa-

rately allocated location after the current block.

Definition: The following types are called “dynamic”:

- bytes

- string

- T[] for any T

- T[k] for any dynamic T and any k >= 0

- (T1,...,Tk) if Ti is dynamic for some 1 <= i <= k

All other types are called “static”.

Definition: len(a) is the number of bytes in a binary string a. The type of len(a) is assumed to be uint256.

We define enc, the actual encoding, as a mapping of values of the ABI types to binary strings such that len(enc(X))

depends on the value of X if and only if the type of X is dynamic.

Definition: For any ABI value X, we recursively define enc(X), depending on the type of X being

- (T1,...,Tk) for k >= 0 and any types T1, . . . , Tk

enc(X) = head(X(1)) ... head(X(k)) tail(X(1)) ... tail(X(k))

where X = (X(1), ..., X(k)) and head and tail are defined for Ti as follows:

if Ti is static:

head(X(i)) = enc(X(i)) and tail(X(i)) = "" (the empty string)

otherwise, i.e. if Ti is dynamic:

Note that in the dynamic case, head(X(i)) is well-defined since the lengths of the head parts only depend on the types and not the values. The value of head(X(i)) is the offset of the beginning of tail(X(i)) relative to the start of enc(X).

- T[k] for any T and k:

enc(X) = enc((X[0], ..., X[k-1]))

i.e. it is encoded as if it were a tuple with k elements of the same type.

- T[] where X has k elements (k is assumed to be of type uint256):

i.e. it is encoded as if it were a tuple with k elements of the same type (resp. an array of static size k), prefixed with the number of elements.

- bytes, of length k (which is assumed to be of type uint256):

enc(X) = enc(k) pad_right(X), i.e. the number of bytes is encoded as a uint256 followed by the actual value of X as a byte sequence, followed by the minimum number of zero-bytes such that len(enc(X)) is a multiple of 32.

- string:

enc(X) = enc(enc_utf8(X)), i.e. X is UTF-8 encoded and this value is interpreted as of bytes type and encoded further. Note that the length used in this subsequent encoding is the number of bytes of the UTF-8 encoded string, not its number of characters.

- uint<M>: enc(X) is the big-endian encoding of X, padded on the higher-order (left) side with zero-bytes such that the length is 32 bytes.

- address: as in the uint160 case

- int<M>: enc(X) is the big-endian two’s complement encoding of X, padded on the higher-order (left) side with 0xff bytes for negative X and with zero-bytes for non-negative X such that the length is 32 bytes.

- bool: as in the uint8 case, where 1 is used for true and 0 for false

- fixed<M>x<N>: enc(X) is enc(X * 10**N) where X * 10**N is interpreted as a int256.

- fixed: as in the fixed128x18 case

- ufixed<M>x<N>: enc(X) is enc(X * 10**N) where X * 10**N is interpreted as a uint256.

- ufixed: as in the ufixed128x18 case

- bytes<M>: enc(X) is the sequence of bytes in X padded with trailing zero-bytes to a length of 32 bytes.

Note that for any X, len(enc(X)) is a multiple of 32.

## 3.23.7 Function Selector and Argument Encoding

All in all, a call to the function f with parameters a_1, ..., a_n is encoded as function_selector(f) enc((a_1, ..., a_n))

and the return values v_1, ..., v_k of f are encoded as i.e. the values are combined into a tuple and encoded.

## 3.23.8 Examples

Given the contract:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.16 <0.9.0;
contract Foo {
function bar(bytes3[2] memory) public pure {}
function baz(uint32 x, bool y) public pure returns (bool r) { r = x > 32 || y; }
function sam(bytes memory, bool, uint[] memory) public pure {}
}
```

Thus, for our Foo example, if we wanted to call bar with the argument ["abc", "def"], we would pass 68 bytes total, broken down into:

- 0xfce353f6: the Method ID. This is derived from the signature bar(bytes3[2]).

- 0x6162630000000000000000000000000000000000000000000000000000000000: the first part of the first parameter, a bytes3 value "abc" (left-aligned).

- 0x6465660000000000000000000000000000000000000000000000000000000000: the second part of the first parameter, a bytes3 value "def" (left-aligned).

### In total:

```
0xfce353f66162630000000000000000000000000000000000000000000000000000000000646566000000000000000000000000
```

If we wanted to call baz with the parameters 69 and true, we would pass 68 bytes total, which can be broken down into:

- 0xcdcd77c0: the Method ID. This is derived as the first 4 bytes of the Keccak hash of the ASCII form of the signature baz(uint32,bool).

- 0x0000000000000000000000000000000000000000000000000000000000000045: the first parameter, a uint32 value 69 padded to 32 bytes

- 0x0000000000000000000000000000000000000000000000000000000000000001: the second parameter - boolean true, padded to 32 bytes

In total:

```
0xcdcd77c00000000000000000000000000000000000000000000000000000000000000045000000000000000000000000000000
```

It returns a single bool. If, for example, it were to return false, its output would be the single byte array 0x0000000000000000000000000000000000000000000000000000000000000000, a single bool.

If we wanted to call sam with the arguments "dave", true and [1,2,3], we would pass 292 bytes total, broken down into:

- 0xa5643bf2: the Method ID. This is derived from the signature sam(bytes,bool,uint256[]). Note that uint is replaced with its canonical representation uint256.

- 0x0000000000000000000000000000000000000000000000000000000000000060: the location of the data part of the first parameter (dynamic type), measured in bytes from the start of the arguments block. In this case, 0x60.

- 0x0000000000000000000000000000000000000000000000000000000000000001: the second parameter: boolean true.

- 0x00000000000000000000000000000000000000000000000000000000000000a0: the location of the data part of the third parameter (dynamic type), measured in bytes. In this case, 0xa0.

- 0x0000000000000000000000000000000000000000000000000000000000000004: the data part of the first argument, it starts with the length of the byte array in elements, in this case, 4.

- 0x6461766500000000000000000000000000000000000000000000000000000000: the contents of the first argument: the UTF-8 (equal to ASCII in this case) encoding of "dave", padded on the right to 32 bytes.

- 0x0000000000000000000000000000000000000000000000000000000000000003: the data part ofthe third argument, it starts with the length of the array in elements, in this case, 3.

- 0x0000000000000000000000000000000000000000000000000000000000000001: the first entry of the third parameter.

- 0x0000000000000000000000000000000000000000000000000000000000000002: the second entry of the third parameter.

- 0x0000000000000000000000000000000000000000000000000000000000000003: the third entry of the third parameter.

In total:

0xa5643bf20000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000

## 3.23.9 Use of Dynamic Types

A call to a function with the signature f(uint256,uint32[],bytes10,bytes) with values (0x123, [0x456,

0x789], "1234567890", "Hello, world!") is encoded in the following way:

We take the first four bytes of keccak("f(uint256,uint32[],bytes10,bytes)"), i.e. 0x8be65246. Then we encode the head parts of all four arguments. For the static types uint256 and bytes10, these are directly the values we want to pass, whereas for the dynamic types uint32[] and bytes, we use the offset in bytes to the start of their data area, measured from the start of the value encoding (i.e. not counting the first four bytes containing the hash of the function signature). These are:

- 0x0000000000000000000000000000000000000000000000000000000000000123 (0x123 padded to 32 bytes)

- 0x0000000000000000000000000000000000000000000000000000000000000080 (offset to start of data part of second parameter, 4*32 bytes, exactly the size of the head part)

- 0x3132333435363738393000000000000000000000000000000000000000000000 padded to 32 bytes on the right) ("1234567890"

- 0x00000000000000000000000000000000000000000000000000000000000000e0 (offset to start of data part of fourth parameter = offset to start of data part of first dynamic parameter + size of data part of first dynamic parameter = 4*32 + 3*32 (see below))

After this, the data part of the first dynamic argument, [0x456, 0x789] follows:

- 0x0000000000000000000000000000000000000000000000000000000000000002 (number of elements of the array, 2)

- 0x0000000000000000000000000000000000000000000000000000000000000456 (first element)

- 0x0000000000000000000000000000000000000000000000000000000000000789 (second element)

Finally, we encode the data part of the second dynamic argument, "Hello, world!":

- 0x000000000000000000000000000000000000000000000000000000000000000d (number of elements (bytes in this case): 13)

- 0x48656c6c6f2c20776f726c642100000000000000000000000000000000000000 ("Hello, world!" padded to 32 bytes on the right)

All together, the encoding is (newline after function selector and each 32-bytes for clarity):

### 0x8be65246

```
0000000000000000000000000000000000000000000000000000000000000123
0000000000000000000000000000000000000000000000000000000000000080
3132333435363738393000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000e0
0000000000000000000000000000000000000000000000000000000000000002
0000000000000000000000000000000000000000000000000000000000000456
0000000000000000000000000000000000000000000000000000000000000789
000000000000000000000000000000000000000000000000000000000000000d
48656c6c6f2c20776f726c642100000000000000000000000000000000000000
```

Let us apply the same principle to encode the data for a function with a signature g(uint256[][],string[]) with values ([[1, 2], [3]], ["one", "two", "three"]) but start from the most atomic parts of the encoding:

First we encode the length and data of the first embedded dynamic array [1, 2] of the first root array [[1, 2], [3]]:

- 0x0000000000000000000000000000000000000000000000000000000000000002 (number of elements in the first array, 2; the elements themselves are 1 and 2)

- 0x0000000000000000000000000000000000000000000000000000000000000001 (first element)

- 0x0000000000000000000000000000000000000000000000000000000000000002 (second element)

Then we encode the length and data of the second embedded dynamic array [3] of the first root array [[1, 2], [3]]:

- 0x0000000000000000000000000000000000000000000000000000000000000001 (number of elements in the second array, 1; the element is 3)

- 0x0000000000000000000000000000000000000000000000000000000000000003 (first element)

Then we need to find the offsets a and b for their respective dynamic arrays [1, 2] and [3]. To calculate the offsets we can take a look at the encoded data of the first root array [[1, 2], [3]] enumerating each line in the encoding:

0 - a

\- offset of [1, 2]

1 - b

\- offset of [3]

- 2 - 0000000000000000000000000000000000000000000000000000000000000002 - count for [1, 2]

- 3 - 0000000000000000000000000000000000000000000000000000000000000001 - encoding of 1

- 4 - 0000000000000000000000000000000000000000000000000000000000000002 - encoding of 2

- 5 - 0000000000000000000000000000000000000000000000000000000000000001 - count for [3]

- 6 - 0000000000000000000000000000000000000000000000000000000000000003 - encoding of 3

Offset a points to the start of the content of the array [1, 2] which is line 2 (64 bytes); thus a = 0x0000000000000000000000000000000000000000000000000000000000000040.

Offset b points to the start of the content of the array [3] which is line 5 (160 bytes); thus b = 0x00000000000000000000000000000000000000000000000000000000000000a0.

Then we encode the embedded strings of the second root array:

- 0x0000000000000000000000000000000000000000000000000000000000000003 (number of characters in word "one")

- 0x6f6e650000000000000000000000000000000000000000000000000000000000 (utf8 representation of word "one")

- 0x0000000000000000000000000000000000000000000000000000000000000003 (number of characters in word "two")

- 0x74776f0000000000000000000000000000000000000000000000000000000000 (utf8 representation of word "two")

- 0x0000000000000000000000000000000000000000000000000000000000000005 (number of characters in word "three")

- 0x7468726565000000000000000000000000000000000000000000000000000000 (utf8 representation of word "three")

In parallel to the first root array, since strings are dynamic elements we need to find their offsets c, d and e:

```
0 - c - offset for "one"
1 - d - offset for "two"
2 - e - offset for "three"
3 - 0000000000000000000000000000000000000000000000000000000000000003 - count for "one"
4 - 6f6e650000000000000000000000000000000000000000000000000000000000 - encoding of "one"
5 - 0000000000000000000000000000000000000000000000000000000000000003 - count for "two"
6 - 74776f0000000000000000000000000000000000000000000000000000000000 - encoding of "two"
7 - 0000000000000000000000000000000000000000000000000000000000000005 - count for "three"
8 - 7468726565000000000000000000000000000000000000000000000000000000 - encoding of "three "
```

Offset c points to the start of the content of the string "one" which is line 3 (96 bytes); thus c = 0x0000000000000000000000000000000000000000000000000000000000000060.

Offset d points to the start of the content of the string "two" which is line 5 (160 bytes); thus d = 0x00000000000000000000000000000000000000000000000000000000000000a0.

Offset e points to the start of the content of the string "three" which is line 7 (224 bytes); thus e = 0x00000000000000000000000000000000000000000000000000000000000000e0.

Note that the encodings of the embedded elements of the root arrays are not dependent on each other and have the same encodings for a function with a signature g(string[],uint256[][]).

Then we encode the length of the first root array:

- 0x0000000000000000000000000000000000000000000000000000000000000002 (number of elements in the first root array, 2; the elements themselves are [1, 2] and [3])

Then we encode the length of the second root array:

- 0x0000000000000000000000000000000000000000000000000000000000000003 (number of strings in the second root array, 3; the strings themselves are "one", "two" and "three")

Finally we find the offsets f and g for their respective root dynamic arrays [[1, 2], [3]] and ["one", "two", "three"], and assemble parts in the correct order:

```
0x2289b18c - function signature
0 - f - offset of [[1,2], [3]]
1 - g - offset of ["one", "two", "three"]
2 - 0000000000000000000000000000000000000000000000000000000000000002 - count for [[1,2], [3]]
3 - 0000000000000000000000000000000000000000000000000000000000000040 - offset of [1, 2]
4 - 00000000000000000000000000000000000000000000000000000000000000a0 - offset of [3]
5 - 0000000000000000000000000000000000000000000000000000000000000002 - count for [1, 2]
6 - 0000000000000000000000000000000000000000000000000000000000000001 - encoding of 1
7 - 0000000000000000000000000000000000000000000000000000000000000002 - encoding of 2
8 - 0000000000000000000000000000000000000000000000000000000000000001 - count for [3]
9 - 0000000000000000000000000000000000000000000000000000000000000003 - encoding of 3
10 - 0000000000000000000000000000000000000000000000000000000000000003 - count for ["one", "two", "three"]
11 - 0000000000000000000000000000000000000000000000000000000000000060 - offset for "one"
12 - 00000000000000000000000000000000000000000000000000000000000000a0 - offset for "two"
13 - 00000000000000000000000000000000000000000000000000000000000000e0 - offset for "three "
14 - 0000000000000000000000000000000000000000000000000000000000000003 - count for "one"
15 - 6f6e650000000000000000000000000000000000000000000000000000000000 - encoding of "one"
16 - 0000000000000000000000000000000000000000000000000000000000000003 - count for "two"
17 - 74776f0000000000000000000000000000000000000000000000000000000000 - encoding of "two"
18 - 0000000000000000000000000000000000000000000000000000000000000005 - count for "three"
19 - 7468726565000000000000000000000000000000000000000000000000000000 - encoding of "three"
```

Offset f points to the start of the content of the array [[1, 2], [3]] which is line 2 (64 bytes); thus f = 0x0000000000000000000000000000000000000000000000000000000000000040.

Offset g points to the start of the content of the array ["one", "two", "three"] which is line 10 (320 bytes); thus g = 0x0000000000000000000000000000000000000000000000000000000000000140.

## 3.23.10 Events

Events are an abstraction of the Ethereum logging/event-watching protocol. Log entries provide the contract’s address, a series of up to four topics and some arbitrary length binary data. Events leverage the existing function ABI in order to interpret this (together with an interface spec) as a properly typed structure.

Given an event name and series of event parameters, we split them into two sub-series: those which are indexed and those which are not. Those which are indexed, which may number up to 3 (for non-anonymous events) or 4 (for anonymous ones), are used alongside the Keccak hash of the event signature to form the topics of the log entry. Those which are not indexed form the byte array of the event.

In effect, a log entry using this ABI is described as:

- address: the address of the contract (intrinsically provided by Ethereum);

- topics[0]: (canonical_type_of is a function that simply returns the canonical type of a given argument, e.g. for uint indexed foo, it would return uint256). This value is only present in topics[0] if the event is not declared as anonymous; keccak(EVENT_NAME+"("+EVENT_ARGS.map(canonical_type_of).join(",")+")")

- topics[n]: abi_encode(EVENT_INDEXED_ARGS[n - 1]) if the event is not declared as anonymous or abi_encode(EVENT_INDEXED_ARGS[n]) if it is (EVENT_INDEXED_ARGS is the series of EVENT_ARGS that are indexed);

- data: ABI encoding of EVENT_NON_INDEXED_ARGS (EVENT_NON_INDEXED_ARGS is the series of EVENT_ARGS that are not indexed, abi_encode is the ABI encoding function used for returning a series of typed values from a function, as described above).

For all types of length at most 32 bytes, the EVENT_INDEXED_ARGS array contains the value directly, padded or sign-

extended (for signed integers) to 32 bytes, just as for regular ABI encoding. However, for all “complex” types or types of dynamic length, including all arrays, string, bytes and structs, EVENT_INDEXED_ARGS will contain the Keccak hash of a special in-place encoded value (see Encoding ofIndexed Event Parameters), rather than the encoded value directly. This allows applications to efficiently query for values of dynamic-length types (by setting the hash of the encoded value as the topic), but leaves applications unable to decode indexed values they have not queried for. For dynamic-length types, application developers face a trade-off between fast search for predetermined values (if the argument is indexed) and legibility of arbitrary values (which requires that the arguments not be indexed). Developers may overcome this tradeoff and achieve both efficient search and arbitrary legibility by defining events with two arguments—one indexed, one not — intended to hold the same value.

## 3.23.11 Errors

In case of a failure inside a contract, the contract can use a special opcode to abort execution and revert all state changes. In addition to these effects, descriptive data can be returned to the caller. This descriptive data is the encoding of an error and its arguments in the same way as data for a function call.

As an example, let us consider the following contract whose transfer function always reverts with a custom error of “insufficient balance”:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.4;
contract TestToken {
error InsufficientBalance(uint256 available, uint256 required);
function transfer(address /*to*/, uint amount) public pure {
revert InsufficientBalance(0, amount);
}
}
```

The return data would be encoded in the same way as the function call InsufficientBalance(0, amount) to the function InsufficientBalance(uint256,uint256), i.e. 0xcf479181, uint256(0), uint256(amount).

The error selectors 0x00000000 and 0xffffffff are reserved for future use.

**Warning:**

Never trust error data. The error data by default bubbles up through the chain of external calls, which means that a contract may receive an error not defined in any of the contracts it calls directly. Furthermore, any contract can fake any error by returning data that matches an error signature, even if the error is not defined anywhere.

## 3.23.12 JSON

The JSON format for a contract’s interface is given by an array of function, event and error descriptions. A function description is a JSON object with the fields:

- type: "function", "constructor", "receive" (the “receive Ether” function) or "fallback" (the “default” function);

- name: the name of the function;

- inputs: an array of objects, each of which contains:

- name: the name of the parameter.

- type: the canonical type of the parameter (more below).

- components: used for tuple types (more below).

- outputs: an array of objects similar to inputs.

- stateMutability: a string with one of the following values: pure (specified to not read blockchain state), view (specified to not modify the blockchain state), nonpayable (function does not accept Ether - the default) and payable (function accepts Ether).

Constructor, receive, and fallback never have name or outputs. Receive and fallback do not have inputs either.

ò Note

Sending non-zero Ether to non-payable function will revert the transaction.

**Note:**

The state mutability nonpayable is reflected in Solidity by not specifying a state mutability modifier at all.

An event description is a JSON object with fairly similar fields:

- type: always "event"

- name: the name of the event.

- inputs: an array of objects, each of which contains:

- name: the name of the parameter.

- type: the canonical type of the parameter (more below).

- components: used for tuple types (more below).

- indexed: true if the field is part of the log’s topics, false if it is one of the log’s data segments.

- anonymous: true if the event was declared as anonymous.

Errors look as follows:

- type: always "error"

- name: the name of the error.

- inputs: an array of objects, each of which contains:

- name: the name of the parameter.

- type: the canonical type of the parameter (more below).

- components: used for tuple types (more below).

**Note:**

There can be multiple errors with the same name and even with identical signature in the JSON array; for example, if the errors originate from different files in the smart contract or are referenced from another smart contract. For the ABI, only the name of the error itself is relevant and not where it is defined.

For example,

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.4;
contract Test {
constructor() { b = hex"12345678901234567890123456789012"; }
event Event(uint indexed a, bytes32 b);
event Event2(uint indexed a, bytes32 b);
error InsufficientBalance(uint256 available, uint256 required);
function foo(uint a) public { emit Event(a, b); }
bytes32 b;
}
```

would result in the JSON:

```
[{
"type":"error",
"inputs": [{"name":"available","type":"uint256"},{"name":"required","type":"uint256"}],
"name":"InsufficientBalance"
}, {
"type":"event",
"inputs": [{"name":"a","type":"uint256","indexed":true},{"name":"b","type":"bytes32", "indexed":false}],
"name":"Event"
}, {
"type":"event",
"inputs": [{"name":"a","type":"uint256","indexed":true},{"name":"b","type":"bytes32", "indexed":false}],
"name":"Event2"
}, {
"type":"function",
"inputs": [{"name":"a","type":"uint256"}],
"name":"foo",
"outputs": []
}]
```

### Handling tuple types

Despite the fact that names are intentionally not part of the ABI encoding, they do make a lot of sense to be included in the JSON to enable displaying it to the end user. The structure is nested in the following way:

An object with members name, type and potentially components describes a typed variable. The canonical type is determined until a tuple type is reached and the string description up to that point is stored in type prefix with the word tuple, i.e. it will be tuple followed by a sequence of [] and [k] with integers k. The components of the tuple are then stored in the member components, which is of an array type and has the same structure as the top-level object except that indexed is not allowed there.

As an example, the code

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.5 <0.9.0;
pragma abicoder v2;
contract Test {
struct S { uint a; uint[] b; T[] c; }
struct T { uint x; uint y; }
function f(S memory, T memory, uint) public pure {}
function g() public pure returns (S memory, T memory, uint) {}
}
```

would result in the JSON:

```
[
{
"name": "f",
"type": "function",
"inputs": [
{
"name": "s",
"type": "tuple",
"components": [
{
"name": "a",
"type": "uint256"
},
{
"name": "b",
"type": "uint256[]"
},
{
"name": "c",
"type": "tuple[]",
"components": [
{
"name": "x",
"type": "uint256"
},
{
"name": "y",
"type": "uint256"
}
]
}
]
},
{
"name": "t",
"type": "tuple",
"components": [
{
"name": "x",
"type": "uint256"
},
{
"name": "y",
"type": "uint256"
}
]
},
{
"name": "a",
"type": "uint256"
}
],
"outputs": []
}
]
```

## 3.23.13 Strict Encoding Mode

Strict encoding mode is the mode that leads to exactly the same encoding as defined in the formal specification above.

This means that offsets have to be as small as possible while still not creating overlaps in the data areas, and thus no gaps are allowed.

Usually, ABI decoders are written in a straightforward way by just following offset pointers, but some decoders might enforce strict mode. The Solidity ABI decoder currently does not enforce strict mode, but the encoder always creates data in strict mode.

## 3.23.14 Non-standard Packed Mode

Through abi.encodePacked(), Solidity supports a non-standard packed mode where:

- types shorter than 32 bytes are concatenated directly, without padding or sign extension

- dynamic types are encoded in-place and without the length.

- array elements are padded, but still encoded in-place

Furthermore, structs as well as nested arrays are not supported.

As an example, the encoding of int16(-1), bytes1(0x42), uint16(0x03), string("Hello, world!") results in:

```
0xffff42000348656c6c6f2c20776f726c6421
^^^^ int16(-1)
^^ bytes1(0x42)
^^^^ uint16(0x03)
^^^^^^^^^^^^^^^^^^^^^^^^^^ string("Hello, world!") without a length field
```

More specifically:

- During the encoding, everything is encoded in-place. This means that there is no distinction between head and tail, as in the ABI encoding, and the length of an array is not encoded.

- The direct arguments of abi.encodePacked are encoded without padding, as long as they are not arrays (or string or bytes).

- The encoding of an array is the concatenation of the encoding of its elements with padding.

- Dynamically-sized types like string, bytes or uint[] are encoded without their length field.

- The encoding of string or bytes does not apply padding at the end, unless it is part of an array or struct (then it is padded to a multiple of 32 bytes).

In general, the encoding is ambiguous as soon as there are two dynamically-sized elements, because of the missing length field.

If padding is needed, explicit type conversions can be used: abi.encodePacked(uint16(0x12)) == hex"0012".

Since packed encoding is not used when calling functions, there is no special support for prepending a function selector.

Since the encoding is ambiguous, there is no decoding function.

**Warning:**

If you use sions in the hash value by moving parts of a into b and vice-versa. More specifically,

"bc") == abi.encodePacked("ab", "c"). If you use abi.encodePacked for signatures, authentication or data integrity, make sure to always use the same types and check that at most one of them is dynamic. Unless there is a compelling reason, abi.encode should be preferred.

keccak256(abi.encodePacked(a, b)) and both a and b are dynamic types, it is easy to craft colli-

abi.encodePacked("a",

## 3.23.15 Encoding of Indexed Event Parameters

Indexed event parameters that are not value types, i.e. arrays and structs are not stored directly but instead a Keccak-256

hash of an encoding is stored. This encoding is defined as follows:

- the encoding of a bytes and string value is just the string contents without any padding or length prefix.

- the encoding of a struct is the concatenation of the encoding of its members, always padded to a multiple of 32 bytes (even bytes and string).

- the encoding of an array (both dynamically- and statically-sized) is the concatenation of the encoding of its elements, always padded to a multiple of 32 bytes (even bytes and string) and without any length prefix

In the above, as usual, a negative number is padded by sign extension and not zero padded. bytesNN types are padded on the right while uintNN / intNN are padded on the left.

**Warning:**

The encoding of a struct is ambiguous if it contains more than one dynamically-sized array. Because of that, always re-check the event data and do not rely on the search result based on the indexed parameters alone.
