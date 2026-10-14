# Cheatsheet (3.11) & Language Grammar (3.12)

> Source: Solidity documentation, release 0.8.37-develop (Sep 10, 2026), https://docs.soliditylang.org/ — text reproduced from the official docs; code indentation was flattened by the export and is not normative.

## Contents

- 3.11 Cheatsheet
  - 3.11.1 Order of Precedence of Operators
  - 3.11.2 ABI Encoding and Decoding Functions
  - 3.11.3 Members of bytes and string
  - 3.11.4 Members of address
  - 3.11.5 Block and Transaction Properties
  - 3.11.6 Validations and Assertions
  - 3.11.7 Mathematical and Cryptographic Functions
  - 3.11.8 Contract-related
  - 3.11.9 Type Information
  - 3.11.10 Function Visibility Specifiers
  - 3.11.11 Modifiers
- 3.12 Language Grammar

---

# 3.11 Cheatsheet

## 3.11.1 Order of Precedence of Operators

The following is the order of precedence for operators, listed in order of evaluation.

| Precedence Description |                                     | Operator                               |
| ---------------------- | ----------------------------------- | -------------------------------------- |
| 1                      | Postfix increment and decrement     | ++, --                                 |
|                        | New expression                      | new <typename>                         |
|                        | Array subscripting                  | <array>[<index>]                       |
|                        | Member access                       | <object>.<member>                      |
|                        | Function-like call                  | <func>(<args...>)                      |
|                        | Parentheses                         | (<statement>)                          |
| 2                      | Prefix increment and decrement      | ++, --                                 |
|                        | Unary minus                         | -                                      |
|                        | Unary operations                    | delete                                 |
|                        | Logical NOT                         | !                                      |
|                        | Bitwise NOT                         | ~                                      |
| 3                      | Exponentiation                      | **                                     |
| 4                      | Multiplication, division and modulo | *, /, %                                |
| 5                      | Addition and subtraction            | +, -                                   |
| 6                      | Bitwise shift operators             | <<, >>                                 |
| 7                      | Bitwise AND                         | &                                      |
| 8                      | Bitwise XOR                         | ^                                      |
| 9                      | Bitwise OR                          |                                        |                                         |
| 10                     | Inequality operators                | <, >, <=, >=                           |
| 11                     | Equality operators                  | ==, !=                                 |
| 12                     | Logical AND                         | &&                                     |
| 13                     | Logical OR                          |                                        |                                         |     |
| 14                     | Ternary operator                    | <conditional> ? <if-true> : <if-false> |
|                        | Assignment operators                | =,                                     | =, ^=, &=, <<=, >>=, +=, -=, *=, /=, %= |
| 15                     | Comma operator                      | ,                                      |

## 3.11.2 ABI Encoding and Decoding Functions

- abi.decode(bytes memory encodedData, (...)) returns (...): ABI-decodes the provided data. The types are given in parentheses as second argument. Example: (uint a, uint[2] memory b, bytes memory c) = abi.decode(data, (uint, uint[2], bytes))

- abi.encode(...) returns (bytes memory): ABI-encodes the given arguments

- abi.encodePacked(...) returns (bytes memory): Performs packed encoding of the given arguments. Note that this encoding can be ambiguous!

- abi.encodeWithSelector(bytes4 selector, ...) returns (bytes memory): ABI-encodes the given arguments starting from the second and prepends the given four-byte selector

- abi.encodeCall(function functionPointer, (...)) returns (bytes memory): ABI-encodes a call to functionPointer with the arguments found in the tuple. Performs a full type-check, ensuring the types match the function signature. Result equals abi.encodeWithSelector(functionPointer.selector, .. .)

- abi.encodeWithSignature(string memory signature, ...) returns (bytes memory): Equivalent to abi.encodeWithSelector(bytes4(keccak256(bytes(signature))), ...)

## 3.11.3 Members of bytes and string

- bytes.concat(...) returns (bytes memory): Concatenates variable number of arguments to one byte array

- string.concat(...) returns (string memory): Concatenates variable number of arguments to one string array

## 3.11.4 Members of address

- <address>.balance (uint256): balance of the Address in Wei

- <address>.code (bytes memory): code at the Address (can be empty)

- <address>.codehash (bytes32): the codehash of the Address

- <address>.call(bytes memory) returns (bool, bytes memory): issue low-level CALL with the given payload, returns success condition and return data

- <address>.delegatecall(bytes memory) returns (bool, bytes memory): DELEGATECALL with the given payload, returns success condition and return data issue low-level

- <address>.staticcall(bytes memory) returns (bool, bytes memory): STATICCALL with the given payload, returns success condition and return data issue low-level

- <address payable>.send(uint256 amount) returns (bool): send given amount of Wei to Address, returns false on failure (deprecated)

- <address payable>.transfer(uint256 amount): (deprecated) send given amount ofWei to Address, throws on failure

## 3.11.5 Block and Transaction Properties

- blockhash(uint blockNumber) returns (bytes32): hash of the given block - only works for 256 most recent blocks

- blobhash(uint index) returns (bytes32): versioned hash of the index-th blob associated with the current transaction. A versioned hash consists of a single byte representing the version (currently 0x01), followed by the last 31 bytes of the SHA256 hash of the KZG commitment (EIP-4844). Returns zero if no blob with the given index exists.

- block.basefee (uint): current block’s base fee (EIP-3198 and EIP-1559) (https://eips.ethereum.org/EIPS/eip-3198)

- block.blobbasefee (uint): current block’s blob base fee (EIP-7516 and EIP-4844) (https://eips.ethereum.org/EIPS/eip-7516)

- block.chainid (uint): current chain id

- block.coinbase (address payable): current block miner’s address

- block.difficulty (uint): current block difficulty (EVM < Paris). For other EVM versions it behaves as a deprecated alias for block.prevrandao that will be removed in the next breaking release

- block.gaslimit (uint): current block gaslimit

- block.number (uint): current block number

- block.prevrandao (uint): random number provided by the beacon chain (EVM >= Paris) (see EIP-4399 ) (https://eips.ethereum.org/EIPS/eip-4399)

- block.slotnum (uint64): current beacon chain slot number (EVM >= Amsterdam) (see EIP-7843 )

- block.timestamp (uint): current block timestamp in seconds since Unix epoch

- gasleft() returns (uint256): remaining gas

- msg.data (bytes): complete calldata

- msg.sender (address): sender of the message (current call)

- msg.sig (bytes4): first four bytes of the calldata (i.e. function identifier)

- msg.value (uint): number of wei sent with the message

- tx.gasprice (uint): gas price of the transaction

- tx.origin (address): sender of the transaction (full call chain)

## 3.11.6 Validations and Assertions

- assert(bool condition): abort execution and revert state changes if condition is false (use for internal error)

- require(bool condition): abort execution and revert state changes if condition is false (use for malformed input or error in external component)

- require(bool condition, string memory message): abort execution and revert state changes if condition is false (use for malformed input or error in external component). Also provide error message.

- revert(): abort execution and revert state changes

- revert(string memory message): abort execution and revert state changes providing an explanatory string

## 3.11.7 Mathematical and Cryptographic Functions

- keccak256(bytes memory) returns (bytes32): compute the Keccak-256 hash of the input

- sha256(bytes memory) returns (bytes32): compute the SHA-256 hash of the input

- ripemd160(bytes memory) returns (bytes20): compute the RIPEMD-160 hash of the input

- ecrecover(bytes32 hash, uint8 v, bytes32 r, bytes32 s) returns (address): recover address associated with the public key from elliptic curve signature, return zero on error

- addmod(uint x, uint y, uint k) returns (uint): compute (x + y) % k where the addition is performed with arbitrary precision and does not wrap around at 2**256. Assert that k != 0 starting from version 0.5.0.

- mulmod(uint x, uint y, uint k) returns (uint): compute (x * y) % k where the multiplication is performed with arbitrary precision and does not wrap around at 2**256. Assert that k != 0 starting from version 0.5.0.

- erc7201(string memory id) returns (uint): compute the base slot of an erc7201 storage namespace. Can be used in compile time context.

## 3.11.8 Contract-related

- this (current contract’s type): the current contract, explicitly convertible to address or address payable

- super: a contract one level higher in the inheritance hierarchy

- selfdestruct(address payable recipient): send all funds to the given address and (only on EVMs before Cancun or when invoked within the transaction creating the contract) destroy the contract.

## 3.11.9 Type Information

- type(C).name (string): the name of the contract

- type(C).creationCode (bytes memory): creation bytecode of the given contract, see Type Information.

- type(C).runtimeCode (bytes memory): runtime bytecode of the given contract, see Type Information.

- type(I).interfaceId (bytes4): value containing the EIP-165 interface identifier of the given interface, see Type Information.

- type(T).min (T): the minimum value representable by the integer type T, see Type Information.

- type(T).max (T): the maximum value representable by the integer type T, see Type Information.

## 3.11.10 Function Visibility Specifiers

```
function myFunction() <visibility specifier> returns (bool) {
return true;
}
```

- public: visible externally and internally (creates a getter function for storage/state variables)

- private: only visible in the current contract

- external: only visible externally (only for functions) - i.e. can only be message-called (via this.func)

- internal: only visible internally

## 3.11.11 Modifiers

- pure for functions: Disallows modification or access of state.

- view for functions: Disallows modification of state.

- payable for functions: Allows them to receive Ether together with a call.

- constant for state variables: Disallows assignment (except initialization), does not occupy storage slot.

- immutable for state variables: Allows assignment at construction time and is constant when deployed. Is stored in code.

- anonymous for events: Does not store event signature as topic.

- indexed for event parameters: Stores the parameter as topic.

- virtual for functions and modifiers: Allows the function’s or modifier’s behavior to be changed in derived contracts.

- override: States that this function, modifier or public state variable changes the behavior of a function or modifier in a base contract.

# 3.12 Language Grammar

### grammar SolidityParser

Solidity is a statically typed, contract-oriented, high-level language for implementing smart contracts on the

Ethereum platform.

### source-unit

On top level, Solidity allows pragmas, import directives, and definitions of contracts, interfaces, libraries, structs, enums and constants.

### import-directive

Import directives import identifiers from different files.

### path

_Path of a file to be imported._

### symbol-aliases

List of aliases for symbols to be imported.

### contract-definition

Top-level definition of a contract.

### interface-definition

_Top-level definition of an interface._

### library-definition

_Top-level definition of a library._

### inheritance-specifier

Inheritance specifier for contracts and interfaces. Can optionally supply base constructor arguments.

### contract-body-element

Declarations that can be used in contracts, interfaces and libraries.

Note that interfaces and libraries may not contain constructors, interfaces may not contain state variables and libraries may not contain fallback, receive functions nor non-constant state variables.

### call-argument-list

Arguments when calling a function or a similar callable object. The arguments are either given as comma separated list or as map of named arguments.

### identifier-path

Qualified name.

### modifier-invocation

Call to a modifier. If the modifier takes no arguments, the argument list can be skipped entirely (including opening and closing parentheses).

### visibility

Visibility for functions and function types.

### parameter-list

A list of parameters, such as function arguments or return values.

### constructor-definition

Definition of a constructor. Must always supply an implementation. Note that specifying internal or public visibility is deprecated.

### state-mutability

State mutability for function types. The default mutability ‘non-payable’ is assumed if no mutability is specified.

### override-specifier

An override specifier used for functions, modifiers or state variables. In cases where there are ambiguous declarations in several base contracts being overridden, a complete list of base contracts has to be given.

### function-definition

The definition of contract, library, interface or free functions. Depending on the context in which the function is defined, further restrictions may apply, e.g. functions in interfaces have to be unimplemented, i.e. may not contain a body block.

### modifier-definition

The definition of a modifier. Note that within the body block of a modifier, the underscore cannot be used as identifier, but is used as placeholder statement for the body of a function to which the modifier is applied.

### fallback-function-definition

Definition of the special fallback function.

### receive-function-definition

Definition of the special receive function.

### struct-definition

Definition of a struct. Can occur at top-level within a source unit or within a contract, library or interface.

### struct-member

The declaration of a named struct member.

### enum-definition

Definition of an enum. Can occur at top-level within a source unit or within a contract, library or interface.

### user-defined-value-type-definition

Definition of a user defined value type. Can occur at top-level within a source unit or within a contract, library or interface.

### state-variable-declaration

The declaration of a state variable.

### constant-variable-declaration

event-parameter

_Parameter of an event._

event-definition

Definition of an event. Can occur in contracts, libraries or interfaces.

### error-definition

Definition of an error.

### user-definable-operator

Operators that users are allowed to implement for some types with using for.

### using-directive

Using directive to attach library functions and free functions to types. Can occur within contracts and libraries and at the file level.

### using-aliases

### type-name

A type name can be an elementary type, a function type, a mapping type, a user-defined type (e.g. a contract or struct) or an array type.

### data-location

### expression

Complex expression. Can be an index access, an index range access, a member access, a function call (with optional function call options), a type conversion, an unary or binary expression, a comparison or assignment, a ternary expression, a new-expression (i.e. a contract creation or the allocation of a dynamic memory array), a tuple, an inline array or a primary expression (i.e. an identifier, literal or type name).

### tuple-expression

### inline-array-expression

An inline array expression denotes a statically sized array of the common type of the contained expressions.

### identifier

Besides regular non-keyword Identifiers, some keywords like ‘from’ and ‘error’ can also be used as iden-

tifiers.

_literal_

_literal-with-sub-denomination_

### string-literal

A full string literal consists of either one or several consecutive quoted strings.

### hex-string-literal

A full hex string literal that consists of either one or several consecutive hex strings.

### unicode-string-literal

A full unicode string literal that consists of either one or several consecutive unicode strings.

### number-literal

Number literals can be decimal or hexadecimal numbers with an optional unit.

### block

A curly-braced block of statements. Opens its own scope.

### if-statement

If statement with optional else part.

### for-statement

For statement with optional init, condition and post-loop part.

_do-while-statement_

### continue-statement

A continue statement. Only allowed inside for, while or do-while loops.

### break-statement

A break statement. Only allowed inside for, while or do-while loops.

### try-statement

A try statement. The contained expression needs to be an external function call or a contract creation.

### catch-clause

_The catch clause of a try statement._

_return-statement_

### emit-statement

_An emit statement. The contained expression needs to refer to an event._

### revert-statement

_A revert statement. The contained expression needs to refer to an error._

### assembly-statement

An inline assembly block. The contents of an inline assembly block use a separate scanner/lexer, i.e. the set of keywords and allowed identifiers is different inside an inline assembly block.

### assembly-flags

Assembly flags. Comma-separated list of double-quoted strings as flags.

### variable-declaration-tuple

A tuple of variable names to be used in variable declarations. May contain empty fields.

### variable-declaration-statement

A variable declaration statement. A single variable may be declared without initial value, whereas a tuple of variables can only be declared with initial value.

### mapping-key-type

Only elementary types or user defined types are viable as mapping keys.

### yul-statement

A Yul statement within an inline assembly block. continue and break statements are only valid within for loops. leave statements are only valid within function bodies.

_yul-block_

### yul-variable-declaration

The declaration of one or more Yul variables with optional initial value. If multiple variables are declared, only a function call is a valid initial value.

### yul-assignment

Any expression can be assigned to a single Yul variable, whereas multi-assignments require a function call on the right-hand side.

### yul-switch-statement

A Yul switch statement can consist of only a default-case (deprecated) or one or more non-default cases optionally followed by a default-case.

_yul-function-definition_

### yul-path

While only identifiers without dots can be declared within inline assembly, paths containing dots can refer to declarations outside the inline assembly block.

### yul-function-call

A call to a function with return values can only occur as right-hand side of an assignment or a variable declaration.

_grammar SolidityLexer_

### fixed-bytes

Bytes types of fixed length.

### sub-denomination

Unit denomination for numbers.

_signed-integer-type_

Sized signed integer types. int is an alias of int256.

### unsigned-integer-type

Sized unsigned integer types. uint is an alias of uint256.

### non-empty-string-literal

A non-empty quoted string literal restricted to printable characters.

### empty-string-literal

_An empty string literal_

### single-quoted-printable

Any printable character except single quote or back slash.

### double-quoted-printable

Any printable character except double quote or back slash.

### escape-sequence

Escape sequence. Apart from common single character escape sequences, line breaks can be escaped as well as four hex digit unicode escapes \uXXXX and two digit hex escape sequences \xXX are allowed.

### unicode-string-literal

A single quoted string literal allowing arbitrary unicode characters.

### hex-string

Hex strings need to consist of an even number of hex digits that may be grouped using underscores.

### hex-number

Hex numbers consist of a prefix and an arbitrary number of hex digits that may be delimited by underscores.

### decimal-number

A decimal number literal consists of decimal digits that may be delimited by underscores and an optional positive or negative exponent. If the digits contain a decimal point, the literal has fixed point type.

### identifier

An identifier in solidity has to start with a letter, a dollar-sign or an underscore and may additionally contain numbers after the first symbol.

### yul-evm-builtin

Builtin functions in the EVM Yul dialect.

### yul-identifier

Yul identifiers consist of letters, dollar signs, underscores and numbers, but may not start with a number.

In inline assembly there cannot be dots in user-defined identifiers. Instead see yulPath for expressions consisting of identifiers with dots.

### yul-hex-number

Hex literals in Yul consist of a prefix and one or more hexadecimal digits.

### yul-decimal-number

Decimal literals in Yul may be zero or any sequence of decimal digits without leading zeroes.

### yul-string-literal

String literals in Yul consist of one or more double-quoted or single-quoted strings that may contain escape sequences and printable characters except unescaped line breaks or unescaped double-quotes or single-quotes, respectively.

### pragma-token

Pragma token. Can contain any kind of symbol except a semicolon. Note that currently the solidity parser only allows a subset of this.
