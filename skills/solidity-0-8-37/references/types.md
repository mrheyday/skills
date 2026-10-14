# Types (3.6)

> Source: Solidity documentation, release 0.8.37-develop (Sep 10, 2026), https://docs.soliditylang.org/ — text reproduced from the official docs; code indentation was flattened by the export and is not normative.

## Contents

- 3.6 Types
  - 3.6.1 Value Types
  - 3.6.2 Reference Types
  - 3.6.3 Mapping Types
  - 3.6.4 Operators
  - 3.6.5 Conversions between Elementary Types
  - 3.6.6 Conversions between Literals and Elementary Types

---

# 3.6 Types

Solidity is a statically typed language, which means that the type of each variable (state and local) needs to be specified. Solidity provides several elementary types which can be combined to form complex types.

In addition, types can interact with each other in expressions containing operators. For a quick reference of the various operators, see Order ofPrecedence ofOperators.

The concept of “undefined” or “null” values does not exist in Solidity, but newly declared variables always have a default value dependent on its type. To handle any unexpected values, you should use the revert function to revert the whole transaction, or return a tuple with a second bool value denoting success.

## 3.6.1 Value Types

The following are called value types because their variables will always be passed by value, i.e. they are always copied when they are used as function arguments or in assignments.

Unlike reference types, value type declarations do not specify a data location since they are small enough to be stored on the stack. The only exception is state variables. Those are by default located in storage, but can also be marked as transient, constant or immutable.

### Booleans

bool:

Operators:

- ! (logical negation)

- && (logical conjunction, “and”)

- || (logical disjunction, “or”)

- == (equality)

- != (inequality)

The operators || and && apply the common short-circuiting rules. This means that in the expression f(x) || g(y), if f(x) evaluates to true, g(y) will not be evaluated even if it may have side-effects.

The possible values are constants true and false.

### Integers

int / uint: Signed and unsigned integers of various sizes. Keywords uint8 to uint256 in steps of 8 (unsigned of 8 up to 256 bits) and int8 to int256. uint and int are aliases for uint256 and int256, respectively.

Operators:

- Comparisons: <=, <, ==, !=, >=, > (evaluate to bool)

- Bit operators: &, |, ^ (bitwise exclusive or), ~ (bitwise negation)

- Shift operators: << (left shift), >> (right shift)

- Arithmetic operators: +, -, unary - (only for signed integers), *, /, % (modulo), ** (exponentiation)

For an integer type X, you can use type(X).min and type(X).max to access the minimum and maximum value representable by the type.

**Warning:**

Integers in Solidity are restricted to a certain range. For example, with uint32, this is 0 up to 2**32 - 1. There are two modes in which arithmetic is performed on these types: The “wrapping” or “unchecked” mode and the “checked” mode. By default, arithmetic is always “checked”, meaning that if an operation’s result falls outside the value range of the type, the call is reverted through a failing assertion. You can switch to “unchecked” mode using unchecked { ... }. More details can be found in the section about unchecked.

### Comparisons

The value of a comparison is the one obtained by comparing the integer value.

### Bit operations

Bit operations are performed on the two’s complement representation of the number. This means that, for example ~int256(0) == int256(-1).

### Shifts

The result of a shift operation has the type of the left operand, truncating the result to match the type. The right operand must be of unsigned type, trying to shift by a signed type will produce a compilation error.

Shifts can be “simulated” using multiplication by powers of two in the following way. Note that the truncation to the type of the left operand is always performed at the end, but not mentioned explicitly.

- x << y is equivalent to the mathematical expression x * 2**y.

- x >> y is equivalent to the mathematical expression x / 2**y, rounded towards negative infinity.

**Warning:**

Before version 0.5.0 a right shift x >> y for negative x was equivalent to the mathematical expression x / 2**y rounded towards zero, i.e., right shifts used rounding up (towards zero) instead of rounding down (towards negative infinity).

**Note:**

Overflow checks are never performed for shift operations as they are done for arithmetic operations. Instead, the result is always truncated.

### Addition, Subtraction and Multiplication

Addition, subtraction and multiplication have the usual semantics, with two different modes in regard to over- and underflow:

By default, all arithmetic is checked for under- or overflow, but this can be disabled using the unchecked block, resulting in wrapping arithmetic. More details can be found in that section.

The expression -x is equivalent to (T(0) - x) where T is the type of x. It can only be applied to signed types. The value of -x can be positive if x is negative. There is another caveat also resulting from two’s complement representation:

If you have int x = type(int).min;, then -x does not fit the positive range. This means that unchecked { assert(-x == x); } works, and the expression -x when used in checked mode will result in a failing assertion.

### Division

Since the type ofthe result ofan operation is always the type ofone ofthe operands, division on integers always results in an integer. In Solidity, division rounds towards zero. This means that int256(-5) / int256(2) == int256(-2).

Note that in contrast, division on literals results in fractional values of arbitrary precision.

ò Note

Division by zero causes a Panic error. This check can not be disabled through unchecked { ... }.

**Note:**

The expression type(int).min / (-1) is the only case where division causes an overflow. In checked arithmetic mode, this will cause a failing assertion, while in wrapping mode, the value will be type(int).min.

### Modulo

The modulo operation a % n yields the remainder r after the division of the operand a by the operand n, where q = int(a / n) and r = a - (n * q). This means that modulo results in the same sign as its left operand (or zero) and a % n == -(-a % n) holds for negative a:

- int256(5) % int256(2) == int256(1)

- int256(5) % int256(-2) == int256(1)

- int256(-5) % int256(2) == int256(-1)

- int256(-5) % int256(-2) == int256(-1)

**Note:**

Modulo with zero causes a Panic error. This check can not be disabled through unchecked { ... }.

### Exponentiation

Exponentiation is only available for unsigned types in the exponent. The resulting type of an exponentiation is always equal to the type of the base. Please take care that it is large enough to hold the result and prepare for potential assertion failures or wrapping behavior.

**Note:**

In checked mode, exponentiation only uses the comparatively cheap exp opcode for small bases. For the cases of x**3, the expression x*x*x might be cheaper. In any case, gas cost tests and the use of the optimizer are advisable.

**Note:**

Note that 0**0 is defined by the EVM as 1.

### Fixed Point Numbers

**Warning:**

Fixed point numbers are not fully supported by Solidity yet. They can be declared, but cannot be assigned to or from.

fixed / ufixed: Signed and unsigned fixed point number of various sizes. Keywords ufixedMxN and fixedMxN, where M represents the number of bits taken by the type and N represents how many decimal points are available. M must be divisible by 8 and goes from 8 to 256 bits. N must be between 0 and 80, inclusive. ufixed and fixed are aliases for ufixed128x18 and fixed128x18, respectively.

Operators:

- Comparisons: <=, <, ==, !=, >=, > (evaluate to bool)

- Arithmetic operators: +, -, unary -, *, /, % (modulo)

**Note:**

The main difference between floating point (float and double in many languages, more precisely IEEE 754 numbers) and fixed point numbers is that the number of bits used for the integer and the fractional part (the part after the decimal dot) is flexible in the former, while it is strictly defined in the latter. Generally, in floating point almost the entire space is used to represent the number, while only a small number of bits define where the decimal point is.

### Address

The address type comes in two largely identical flavors:

- address: Holds a 20 byte value (size of an Ethereum address).

- address payable: Same as address, but with the additional members transfer and send.

The idea behind this distinction is that address payable is an address you can send Ether to, while you are not supposed to send Ether to a plain address, for example because it might be a smart contract that was not built to accept Ether.

Type conversions:

Implicit conversions from address payable to address are allowed, whereas conversions from address to address payable must be explicit via payable(<address>).

Explicit conversions to and from address are allowed for uint160, integer literals, bytes20 and contract types.

Only expressions of type address and contract type can be converted to the type address payable via the explicit conversion payable(...). For contract-type, this conversion is only allowed if the contract can receive Ether, i.e., the contract either has a receive or a payable fallback function. Note that payable(0) is valid and is an exception to this rule.

**Note:**

If you need a variable of type address and plan to send Ether to it, then declare its type as address payable to make this requirement visible. Also, try to make this distinction or conversion as early as possible.

The distinction between address and address payable was introduced in version 0.5.0. Also starting from that version, contracts are not implicitly convertible to the address type, but can still be explicitly converted to address or to address payable, if they have a receive or payable fallback function.

### Operators:

- <=, <, ==, !=, >= and >

**Warning:**

If you convert a type that uses a larger byte size to an address, for example bytes32, then the address is truncated. To reduce conversion ambiguity, starting with version 0.4.24, the compiler will force you to make the truncation explicit in the conversion. Take for example the 32-byte value 0x111122223333444455556666777788889999AAAABBBBCCCCDDDDEEEEFFFFCCCC.

You can use address(bytes20(b)), which results in 0x111122223333444455556666777788889999aAaa, or you can use address(uint160(uint256(b))), which results in

0x777788889999AaAAbBbbCcccddDdeeeEfFFfCcCc.

**Note:**

Mixed-case hexadecimal numbers conforming to See Address Literals.

[EIP-55](https://github.com/ethereum/EIPs/blob/master/EIPS/eip-55.md)

are automatically treated as literals of the address type.

### Members of Addresses

For a quick reference of all members of address, see Members ofAddress Types.

### • balance and transfer

It is possible to query the balance of an address using the property balance and to send Ether (in units of wei) to a payable address using the transfer function:

```
address payable x = payable(0x123);
address myAddress = address(this);
if (x.balance < 10 && myAddress.balance >= 10) x.transfer(10);
```

The transfer function fails if the balance of the current contract is not large enough or if the Ether transfer is rejected by the receiving account. The transfer function reverts on failure.

**Note:**

If x is a contract address, its code (more specifically: its Receive Ether Function, if present, or otherwise its Fallback Function, if present) will be executed together with the transfer call (this is a feature of the EVM and cannot be prevented). If that execution runs out of gas or fails in any way, the Ether transfer will be reverted and the current contract will stop with an exception.

**Warning:**

transfer is deprecated and scheduled for removal. Simple ether transfers can still be performed using the call function with with an optionally provided maximum amount of gas and empty payload, i.e., call{value: <amount>}(""). By default this forwards all the remaining gas, subject to additional limits imposed by some EVM versions (such as the 63/64th rule introduced by tangerineWhistle). As with any external call, the gas call option can be used to set a lower limit.

While it is possible to recreate the functionality by explicitly setting the limit to the value of the stipend (2300 gas), this value no longer holds its original meaning due to changing opcode costs. It is recommended to use different means to protect against reentrancy.

### • send

send is the low-level counterpart of transfer. If the execution fails, the current contract will not stop with an exception, but send will return false.

**Warning:**

There are some dangers in using send: The transfer fails if the call stack depth is at 1024 (this can always be forced by the caller) and it also fails if the recipient runs out of gas. So in order to make safe Ether transfers, always check the return value of send, use transfer or even better: use a pattern where the recipient withdraws the Ether.

**Warning:**

send is deprecated and scheduled for removal. Simple ether transfers can still be performed using the call function with with an optionally provided maximum amount of gas and empty payload, i.e., call{value: <amount>}(""). By default this forwards all the remaining gas, subject to additional limits imposed by some EVM versions (such as the 63/64th rule introduced by tangerineWhistle). As with any external call, the gas call option can be used to set a lower limit.

While it is possible to recreate the functionality by explicitly setting the limit to the value of the stipend (2300 gas), this value no longer holds its original meaning due to changing opcode costs. It is recommended to use different means to protect against reentrancy.

### • call, delegatecall and staticcall

In order to interface with contracts that do not adhere to the ABI, or to get more direct control over the encoding, the functions call, delegatecall and staticcall are provided. They all take a single bytes memory parameter and return the success condition (as a bool) and the returned data (bytes memory). The functions abi.encode, abi.encodePacked, abi.encodeWithSelector and abi.encodeWithSignature can be used to encode structured data.

Example:

```
bytes memory payload = abi.encodeWithSignature("register(string)", "MyName ");
(bool success, bytes memory returnData) = address(nameReg).call(payload);
require(success);
```

**Warning:**

All these functions are low-level functions and should be used with care. Specifically, any unknown contract might be malicious and if you call it, you hand over control to that contract which could in turn call back into your contract, so be prepared for changes to your state variables when the call returns. The regular way to interact with other contracts is to call a function on a contract object (x.f()).

**Note:**

Previous versions of Solidity allowed these functions to receive arbitrary arguments and would also handle a first argument of type bytes4 differently. These edge cases were removed in version 0.5.0.

It is possible to adjust the supplied gas with the gas modifier:

```
address(nameReg).call{gas: 1000000}(abi.encodeWithSignature( "register(string)", "MyName"));
```

Similarly, the supplied Ether value can be controlled too:

```
address(nameReg).call{value: 1 ether}(abi.encodeWithSignature( "register(string)", "MyName"));
```

Lastly, these modifiers can be combined. Their order does not matter:

```
address(nameReg).call{gas: 1000000, value: 1 ether}(abi.encodeWithSignature( "register(string)", "MyName"));
```

In a similar way, the function delegatecall can be used: the difference is that only the code of the given address is used, all other aspects (storage, balance, . . . ) are taken from the current contract. The purpose of delegatecall is to use library code which is stored in another contract. The user has to ensure that the layout of storage in both contracts is suitable for delegatecall to be used.

**Note:**

Prior to homestead, only a limited variant called callcode was available that did not provide access to the original msg.sender and msg.value values. This function was removed in version 0.5.0.

Since byzantium staticcall can be used as well. This is basically the same as call, but will revert if the called function modifies the state in any way.

All three functions call, delegatecall and staticcall are very low-level functions and should only be used as a last resort as they break the type-safety of Solidity.

The gas option is available on all three methods, while the value option is only available on call.

**Note:**

It is best to avoid relying on hardcoded gas values in your smart contract code, regardless of whether state is read from or written to, as this can have many pitfalls. Also, access to gas might change in the future.

- code and codehash

You can query the deployed code for any smart contract. Use .code to get the EVM bytecode as a bytes memory, which might be empty. Use .codehash to get the Keccak-256 hash of that code (as a bytes32). Note that addr.codehash is cheaper than using keccak256(addr.code).

**Warning:**

The output of addr.codehash may be 0 if the account associated with addr is empty or non-existent (i.e., it has no code, zero balance, and zero nonce as defined by EIP- 161). If the account has no code but a non-zero balance or nonce, then addr.codehash will output the Keccak-256 hash of empty data (i.e., keccak256("") which is equal to c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470), as defined by EIP-1052. (https://eips.ethereum.org/EIPS/eip-1052)

**Note:**

All contracts can be converted to address type, so it is possible to query the balance of the current contract using address(this).balance.

### Contract Types

Every contract defines its own type. You can implicitly convert contracts to contracts they inherit from. Contracts can be explicitly converted to and from the address type.

Explicit conversion to and from the address payable type is only possible if the contract type has a receive or payable fallback function. The conversion is still performed using address(x). If the contract type does not have a receive or payable fallback function, the conversion to address payable can be done using payable(address(x)). You can find more information in the section about the address type.

**Note:**

Before version 0.5.0, contracts directly derived from the address type and there was no distinction between address and address payable.

If you declare a local variable of contract type (MyContract c), you can call functions on that contract. Take care to assign it from somewhere that is the same contract type.

You can also instantiate contracts (which means they are newly created). You can find more details in the ‘Contracts via new’ section.

The data representation of a contract is identical to that of the address type and this type is also used in the ABI.

Contracts do not support any operators.

The members ofcontract types are the external functions ofthe contract including any state variables marked as public.

For a contract C you can use type(C) to access type information about the contract.

### Fixed-size byte arrays

The value types bytes1, bytes2, bytes3, . . . , bytes32 hold a sequence of bytes from one to up to 32.

Operators:

- Comparisons: <=, <, ==, !=, >=, > (evaluate to bool)

- Bit operators: &, |, ^ (bitwise exclusive or), ~ (bitwise negation)

- Shift operators: << (left shift), >> (right shift)

- Index access: If x is of type bytesI, then x[k] for 0 <= k < I returns the k th byte (read-only).

The shifting operator works with unsigned integer type as right operand (but returns the type of the left operand), which denotes the number of bits to shift by. Shifting by a signed type will produce a compilation error.

Members:

- .length yields the fixed length of the byte array (read-only).

**Note:**

The type bytes1[] is an array of bytes, but due to padding rules, it wastes 31 bytes of space for each element (except in storage). It is better to use the bytes type instead.

**Note:**

Prior to version 0.8.0, byte used to be an alias for bytes1.

### Address Literals

Hexadecimal literals that pass the address checksum test, for example 0xdCad3a6d3569DF655070DEd06cb7A1b2Ccd1D3AF are of address type. Hexadecimal literals that are between 39 and 41 digits long and do not pass the checksum test produce an error. You can prepend (for integer types) or append (for bytesNN types) zeros to remove the error.

**Note:**

The mixed-case address checksum format is defined in EIP-55. (https://github.com/ethereum/EIPs/blob/master/EIPS/eip-55.md)

### Rational and Integer Literals

Integer literals are formed from a sequence of digits in the range 0-9. They are interpreted as decimals. For example, 69 means sixty nine. Octal literals do not exist in Solidity and leading zeros are invalid.

Decimal fractional literals are formed by a . with at least one number after the decimal point. Examples include .1 and 1.3 (but not 1.).

Scientific notation in the form of 2e10 is also supported, where the mantissa can be fractional but the exponent has to be an integer. The literal MeE is equivalent to M * 10**E. Examples include 2e10, -2e10, 2e-10, 2.5e1.

Underscores can be used to separate the digits of a numeric literal to aid readability. For example, decimal 123_000, hexadecimal 0x2eff_abde, scientific decimal notation 1_2e345_678 are all valid. Underscores are only allowed between two digits and only one consecutive underscore is allowed. There is no additional semantic meaning added to a number literal containing underscores, the underscores are ignored.

Number literal expressions retain arbitrary precision until they are converted to a non-literal type (i.e. by using them together with anything other than a number literal expression (like boolean literals) or by explicit conversion). This means that computations do not overflow and divisions do not truncate in number literal expressions.

For example, (2**800 + 1) - 2**800 results in the constant 1 (of type uint8) although intermediate results would not even fit the machine word size. Furthermore, .5 * 8 results in the integer 4 (although non-integers were used in between).

**Warning:**

While most operators produce a literal expression when applied to literals, there are certain operators that do not follow this pattern:

- Ternary operator (... ? ... : ...),

- Array subscript (<array>[<index>]).

You might expect expressions like 255 + (true ? 1 : 0) or 255 + [1, 2, 3][0] to be equivalent to using the literal 256 directly, but in fact they are computed within the type uint8 and can overflow.

Any operator that can be applied to integers can also be applied to number literal expressions as long as the operands are integers. If any of the two is fractional, bit operations are disallowed and exponentiation is disallowed if the exponent is fractional (because that might result in a non-rational number).

Shifts and exponentiation with literal numbers as left (or base) operand and integer types as the right (exponent) operand are always performed in the uint256 (for non-negative literals) or int256 (for a negative literals) type, regardless of the type of the right (exponent) operand.

**Warning:**

Division on integer literals used to truncate in Solidity prior to version 0.4.0, but it now converts into a rational number, i.e. 5 / 2 is not equal to 2, but to 2.5.

**Note:**

Solidity has a number literal type for each rational number. Integer literals and rational number literals belong to number literal types. Moreover, all number literal expressions (i.e. the expressions that contain only number literals and operators) belong to number literal types. So the number literal expressions 1 + 2 and 2 + 1 both belong to the same number literal type for the rational number three.

**Note:**

Number literal expressions are converted into a non-literal type as soon as they are used with non-literal expressions. Disregarding types, the value of the expression assigned to b below evaluates to an integer. Because a is of type uint128, the expression 2.5 + a has to have a proper type, though. Since there is no common type for the type of 2.5 and uint128, the Solidity compiler does not accept this code.

```
uint128 a = 1;
uint128 b = 2.5 + a + 0.5;
```

### String Literals and Types

String literals are written with either double or single-quotes ("foo" or 'bar'), and they can also be split into multiple consecutive parts ("foo" "bar" is equivalent to "foobar") which can be helpful when dealing with long strings. They do not imply trailing zeroes as in C; "foo" represents three bytes, not four. As with integer literals, their type can vary, but they are implicitly convertible to bytes1, . . . , bytes32, if they fit, to bytes and to string.

For example, with bytes32 samevar = "stringliteral" the string literal is interpreted in its raw byte form when assigned to a bytes32 type.

String literals can only contain printable ASCII characters, which means the characters between and including 0x20 .. 0x7E.

Additionally, string literals also support the following escape characters:

- \<newline> (escapes an actual newline)

- \\ (backslash)

- \' (single quote)

- \" (double quote)

- \n (newline)

- \r (carriage return)

- \t (tab)

- \xNN (hex escape, see below)

- \uNNNN (unicode escape, see below)

\xNN takes a hex value and inserts the appropriate byte, while \uNNNN takes a Unicode codepoint and inserts an UTF-8 sequence.

**Note:**

Until version 0.8.0 there were three additional escape sequences: \b, \f and \v. They are commonly available in other languages but rarely needed in practice. If you do need them, they can still be inserted via hexadecimal escapes, i.e. \x08, \x0c and \x0b, respectively, just as any other ASCII character.

The string in the following example has a length of ten bytes. It starts with a newline byte, followed by a double quote, a single quote a backslash character and then (without separator) the character sequence abcdef.

Any Unicode line terminator which is not a newline (i.e. LF, VF, FF, CR, NEL, LS, PS) is considered to terminate the string literal. Newline only terminates the string literal if it is not preceded by a \.

### Unicode Literals

While regular string literals can only contain ASCII, Unicode literals – prefixed with the keyword unicode – can contain any valid UTF-8 sequence. They also support the very same escape sequences as regular string literals.

string memory a = unicode"Hello ";

### Hexadecimal Literals

Hexadecimal literals are prefixed with the keyword hex and are enclosed in double or single-quotes (hex"001122FF", hex'0011_22_FF'). Their content must be hexadecimal digits which can optionally use a single underscore as separator between byte boundaries. The value of the literal will be the binary representation of the hexadecimal sequence.

Multiple hexadecimal literals separated by whitespace are concatenated into a single literal: hex"00112233" hex"44556677" is equivalent to hex"0011223344556677"

Hexadecimal literals in some ways behave like string literals but are not implicitly convertible to the string type.

### Enums

Enums are one way to create a user-defined type in Solidity. They are explicitly convertible to and from all integer types but implicit conversion is not allowed. The explicit conversion from integer checks at runtime that the value lies inside the range of the enum and causes a Panic error otherwise. Enums require at least one member, and its default value when declared is the first member. Enums cannot have more than 256 members.

The data representation is the same as for enums in C: The options are represented by subsequent unsigned integer values starting from 0.

Using type(NameOfEnum).min and type(NameOfEnum).max you can get the smallest and respectively largest value of the given enum.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.8;
contract test {
enum ActionChoices { GoLeft, GoRight, GoStraight, SitStill }
ActionChoices choice;
ActionChoices constant defaultChoice = ActionChoices.GoStraight;
function setGoStraight() public {
choice = ActionChoices.GoStraight;
}
// Since enum types are not part of the ABI, the signature of "getChoice"
// will automatically be changed to "getChoice() returns (uint8)"
// for all matters external to Solidity.
function getChoice() public view returns (ActionChoices) {
return choice;
}
function getDefaultChoice() public pure returns (uint) {
return uint(defaultChoice);
}
function getLargestValue() public pure returns (ActionChoices) {
return type(ActionChoices).max;
}
function getSmallestValue() public pure returns (ActionChoices) {
return type(ActionChoices).min;
}
}
```

ò Note

Enums can also be declared on the file level, outside of contract or library definitions.

### User-defined Value Types

A user-defined value type allows creating a zero cost abstraction over an elementary value type. This is similar to an alias, but with stricter type requirements.

A user-defined value type is defined using type C is V, where C is the name of the newly introduced type and V has to be a built-in value type (the “underlying type”). The function C.wrap is used to convert from the underlying type to the custom type. Similarly, the function C.unwrap is used to convert from the custom type to the underlying type.

The type C does not have any operators or attached member functions. In particular, even the operator == is not defined. Explicit and implicit conversions to and from other types are disallowed.

The data-representation of values of such types are inherited from the underlying type and the underlying type is also used in the ABI.

The following example illustrates a custom type UFixed256x18 representing a decimal fixed point type with 18 decimals and a minimal library to do arithmetic operations on the type.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.8;
// Represent a 18 decimal, 256 bit wide fixed point type using a user-defined value type.
type UFixed256x18 is uint256;
/// A minimal library to do fixed point operations on UFixed256x18.
library FixedMath {
uint constant multiplier = 10**18;
/// Adds two UFixed256x18 numbers. Reverts on overflow, relying on checked
/// arithmetic on uint256.
function add(UFixed256x18 a, UFixed256x18 b) internal pure returns (UFixed256x18) {
return UFixed256x18.wrap(UFixed256x18.unwrap(a) + UFixed256x18.unwrap(b));
}
/// Multiplies UFixed256x18 and uint256. Reverts on overflow, relying on checked
/// arithmetic on uint256.
function mul(UFixed256x18 a, uint256 b) internal pure returns (UFixed256x18) {
return UFixed256x18.wrap(UFixed256x18.unwrap(a) * b);
}
/// Take the floor of a UFixed256x18 number.
/// @return the largest integer that does not exceed `a`.
function floor(UFixed256x18 a) internal pure returns (uint256) {
return UFixed256x18.unwrap(a) / multiplier;
}
/// Turns a uint256 into a UFixed256x18 of the same value.
/// Reverts if the integer is too large.
function toUFixed256x18(uint256 a) internal pure returns (UFixed256x18) {
return UFixed256x18.wrap(a * multiplier);
}
}
```

Notice how UFixed256x18.wrap and FixedMath.toUFixed256x18 have the same signature but perform two very different operations: The UFixed256x18.wrap function returns a UFixed256x18 that has the same data representation as the input, whereas toUFixed256x18 returns a UFixed256x18 that has the same numerical value.

### Function Types

Function types are the types of functions. Variables of a function type can be assigned from functions and function parameters of function type can be used to pass functions to and return functions from function calls. Function types come in two flavours - internal and external functions:

Internal functions can only be called inside the current contract (more specifically, inside the current code unit, which also includes internal library functions and inherited functions) because they cannot be executed outside of the context of the current contract. Calling an internal function is realized by jumping to its entry label, just like when calling a function of the current contract internally.

External functions consist of an address and a function signature and they can be passed via and returned from external function calls.

Note that public functions of the current contract can be used both as an internal and as an external function. To use f as an internal function, just use f, if you want to use its external form, use this.f.

If a function type variable is not initialised, calling it results in a Panic error. The same happens if you call a function after using delete on it.

**Note:**

Lambda or inline functions are planned but not yet supported.

### Declaration syntax

Function types are notated as follows:

function (<parameter types>) {internal|external} [pure|view|payable] [returns (<return   types>)]

In contrast to the parameter types, the return types cannot be empty - if the function type should not return anything, the whole returns (<return types>) part has to be omitted.

By default, function types are internal, so the internal keyword can be omitted. Note that this only applies to function types. Visibility has to be specified explicitly for functions defined in contracts, they do not have a default.

### Conversions

A function type A is implicitly convertible to a function type B if and only if their parameter types are identical, their return types are identical, their internal/external property is identical and the state mutability of A is more restrictive than the state mutability of B. In particular:

- pure functions can be converted to view and non-payable functions

- view functions can be converted to non-payable functions

- payable functions can be converted to non-payable functions

No other conversions between function types are possible.

The rule about payable and non-payable might be a little confusing, but in essence, if a function is payable, this means that it also accepts a payment of zero Ether, so it also is non-payable. On the other hand, a non-payable function will reject Ether sent to it, so non-payable functions cannot be converted to payable functions. To clarify, rejecting ether is more restrictive than not rejecting ether. This means you can override a payable function with a non-payable but not the other way around.

Additionally, When you define a non-payable function pointer, the compiler does not enforce that the pointed function will actually reject ether. Instead, it enforces that the function pointer is never used to send ether. Which makes it possible to assign a payable function pointer to a non-payable function pointer ensuring both types behave the same way, i.e, both cannot be used to send ether.

If external function types are used outside of the context of Solidity, they are treated as the function type, which encodes the address followed by the function identifier together in a single bytes24 type.

A function of an internal type can be assigned to a variable of an internal function type regardless of where it is defined. This includes private, internal and public functions of both contracts and libraries as well as free functions. External function types, on the other hand, are only compatible with public and external contract functions.

**Note:**

External functions with calldata parameters are incompatible with external function types with calldata parameters. They are compatible with the corresponding types with memory parameters instead. For example, there is no function that can be pointed at by a value of type (string memory) external can point at both function f(string memory) external {} and function g(string calldata) external {}. This is because for both locations the arguments are passed to the function in the same way. The caller cannot pass its calldata directly to an external function and always ABI-encodes the arguments into memory. Marking the parameters as calldata only affects the implementation of the external function and is meaningless in a function pointer on the caller’s side.

function (string calldata) external while function

**Warning:**

Comparison of internal function pointers can have unexpected results in the legacy pipeline with the optimizer enabled, as it can collapse identical functions into one, which will then lead to said function pointers comparing as equal instead of not. Such comparisons are not advised, and will lead to the compiler issuing a warning, until the next breaking release (0.9.0), when the warning will be upgraded to an error, thereby making such comparisons disallowed.

Libraries are excluded because they require a delegatecall and use a different ABI convention for their selectors. Functions declared in interfaces do not have definitions so pointing at them does not make sense either.

### Members

External (or public) functions have the following members:

- .address returns the address of the contract of the function.

- .selector returns the ABI function selector

**Note:**

External (or public) functions used to have the additional members .gas(uint) and .value(uint). These were deprecated in Solidity 0.6.2 and removed in Solidity 0.7.0. Instead use {gas: ...} and {value: ...} to specify the amount of gas or the amount of wei sent to a function, respectively. See External Function Calls for more information.

### Value stability across contract updates

An important aspect to consider when using values of function types is whether the value will remain valid if the underlying code changes.

The state of the blockchain is not completely immutable and there are multiple ways to place different code under the same address:

- Directly deploying different code using salted contract creation.

- Delegating to a different contract via DELEGATECALL (upgradeable code behind a proxy contract is a common example of this).

- Account abstraction as defined by EIP-7702. (https://eips.ethereum.org/EIPS/eip-7702)

External function types can be considered as stable as contract’s ABI, which makes them very portable. Their ABI representation always consists of a contract address and a function selector and it is perfectly safe to store them long-term or pass them between contracts. While it is possible for the referenced function to change or disappear, a direct external call would be affected the same way, so there is no additional risk in such use.

In case of internal functions, however, the value is an identifier that is strongly tied to contract’s bytecode. The actual representation of the identifier is an implementation detail and may change between compiler versions or even between different backends. Values assigned under a given representation are deterministic (i.e. guaranteed to remain the same as long as the source code is the same) but are easily affected by changes such as adding, removing or reordering of functions. The compiler is also free to remove internal functions that are never used, which may affect other identifiers. Some representations, e.g. one where identifiers are simply jump targets, may be affected by virtually any change, even one completely unrelated to internal functions.

To counter this, the language limits the use of internal function types outside of the context in which they are valid. This is why internal function types cannot be used as parameters of external functions (or in any other way that is exposed in contract’s ABI). However, there are still situations where it is up to the user to decide whether their use is safe or not. For example long-term storage of such values in state variables is discouraged, but may be safe if the contract code is never going to be updated. It is also always possible to side-step any safeguards by using inline assembly. Such use always needs careful consideration.

**Note:**

The removal of unused internal functions only takes into account explicit references to such functions by name. Implicit references, such as assigning a new value to a function type variable in inline assembly may still lead to the removal of the function if it is not also referenced explicitly elsewhere in the source.

### Examples

Example that shows how to use the members:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.6.4 <0.9.0;
contract Example {
function f() public payable returns (bytes4) {
assert(this.f.address == address(this));
return this.f.selector;
}
function g() public {
this.f{gas: 10, value: 800}();
}
}
```

Example that shows how to use internal function types:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.16 <0.9.0;
library ArrayUtils {
// internal functions can be used in internal library functions because
// they will be part of the same code context
function map(uint[] memory self, function (uint) pure returns (uint) f)
internal
pure
returns (uint[] memory r)
{
r = new uint[](self.length);
for (uint i = 0; i < self.length; i++) {
r[i] = f(self[i]);
}
}
function reduce(
uint[] memory self,
function (uint, uint) pure returns (uint) f
)
internal
pure
returns (uint r)
{
r = self[0];
for (uint i = 1; i < self.length; i++) {
r = f(r, self[i]);
}
}
function range(uint length) internal pure returns (uint[] memory r) {
r = new uint[](length);
for (uint i = 0; i < r.length; i++) {
r[i] = i;
}
}
}
contract Pyramid {
using ArrayUtils for *;
function pyramid(uint l) public pure returns (uint) {
return ArrayUtils.range(l).map(square).reduce(sum);
}
function square(uint x) internal pure returns (uint) {
return x * x;
}
function sum(uint x, uint y) internal pure returns (uint) {
return x + y;
}
}
```

Another example that uses external function types:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.22 <0.9.0;
contract Oracle {
struct Request {
bytes data;
function(uint) external callback;
}
Request[] private requests;
event NewRequest(uint);
function query(bytes memory data, function(uint) external callback) public {
requests.push(Request(data, callback));
emit NewRequest(requests.length - 1);
}
function reply(uint requestID, uint response) public {
// Here goes the check that the reply comes from a trusted source
requests[requestID].callback(response);
}
}
contract OracleUser {
Oracle constant private ORACLE_CONST = Oracle(address(0x00000000219ab540356cBB839Cbe05303d7705Fa)); // known contract
uint private exchangeRate;
function buySomething() public {
ORACLE_CONST.query("USD", this.oracleResponse);
}
function oracleResponse(uint response) public {
require(
msg.sender == address(ORACLE_CONST),
"Only oracle can call this."
);
exchangeRate = response;
}
```

}

## 3.6.2 Reference Types

Values of reference type can be modified through multiple different names. Contrast this with value types where you get an independent copy whenever a variable ofvalue type is used. Because of that, reference types have to be handled more carefully than value types. Currently, reference types comprise structs, arrays and mappings. If you use a reference type, you always have to explicitly provide the data area where the type is stored: memory (whose lifetime is limited to an external function call), storage (the location where the state variables are stored, where the lifetime is limited to the lifetime of a contract) or calldata (special data location that contains the function arguments).

An assignment or type conversion that changes the data location will always incur an automatic copy operation, while assignments inside the same data location only copy in some cases for storage types.

### Data location

Every reference type has an additional annotation, the “data location”, about where it is stored. There are three data locations: memory, storage and calldata. Calldata is a non-modifiable, non-persistent area where function arguments are stored, and behaves mostly like memory.

**Note:**

transient is not yet supported as a data location for reference types.

**Note:**

If you can, try to use calldata as data location because it will avoid copies and also makes sure that the data cannot be modified. Arrays and structs with calldata data location can also be returned from functions, but it is not possible to allocate such types.

**Note:**

Arrays and structs with calldata location declared in a function body or as its return parameters must be assigned before being used or returned. There are certain cases in which non-trivial control flow is used and the compiler can’t properly detect the initialization. A common workaround in such cases is to assign the affected variable to itself before the correct initialization takes place.

**Note:**

Prior to version 0.6.9 data location for reference-type arguments was limited to calldata in external functions, memory in public functions and either memory or storage in internal and private ones. Nowmemory and calldata are allowed in all functions regardless of their visibility.

**Note:**

Constructor parameters cannot use calldata as their data location.

**Note:**

Prior to version 0.5.0 the data location could be omitted, and would default to different locations depending on the kind of variable, function type, etc., but all complex types must now give an explicit data location.

### Data location and assignment behavior

Data locations are not only relevant for persistency of data, but also for the semantics of assignments:

- Assignments between storage and memory (or from calldata) always create an independent copy.

- Assignments from memory to memory only create references. This means that changes to one memory variable are also visible in all other memory variables that refer to the same data.

- Assignments from storage to a local storage variable also only assign a reference.

- All other assignments to storage always copy. Examples for this case are assignments to state variables or to members of local variables of storage struct type, even if the local variable itself is just a reference.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.5.0 <0.9.0;
contract C {
// The data location of x is storage.
// This is the only place where the
// data location can be omitted.
uint[] x;
// The data location of memoryArray is memory.
function f(uint[] memory memoryArray) public {
x = memoryArray; // works, copies the whole array to storage
uint[] storage y = x; // works, assigns a pointer, data location of y is storage
y[7]; // fine, returns the 8th element
y.pop(); // fine, modifies x through y
delete x; // fine, clears the array, also modifies y
// The following does not work; it would need to create a new temporary /
// unnamed array in storage, but storage is "statically" allocated:
// y = memoryArray;
// Similarly, "delete y" is not valid, as assignments to local variables
// referencing storage objects can only be made from existing storage objects.
// It would "reset" the pointer, but there is no sensible location it could point to.
// For more details see the documentation of the "delete" operator.
// delete y;
g(x); // calls g, handing over a reference to x
h(x); // calls h and creates an independent, temporary copy in memory
}
function g(uint[] storage) internal pure {}
function h(uint[] memory) public pure {}
}
```

### Arrays

Arrays can have a compile-time fixed size, or they can have a dynamic size.

The type of an array of fixed size k and element type T is written as T[k], and an array of dynamic size as T[].

For example, an array of 5 dynamic arrays of uint is written as uint[][5]. The notation is reversed compared to some other languages. In Solidity, X[3] is always an array containing three elements of type X, even if X is itself an array. This is not the case in other languages such as C.

Indices are zero-based, and access is in the opposite direction of the declaration.

For example, if you have a variable uint[][5] memory x, you access the seventh uint in the third dynamic array using x[2][6], and to access the third dynamic array, use x[2]. Again, if you have an array T[5] a for a type T that can also be an array, then a[2] always has type T.

Array elements can be of any type, including mapping or struct. The general restrictions for types apply, in that mappings can only be stored in the storage data location and publicly-visible functions need parameters that are ABI types.

It is possible to mark state variable arrays public and have Solidity create a getter. The numeric index becomes a required parameter for the getter.

Accessing an array past its end causes a failing assertion. Methods .push() and .push(value) can be used to append a new element at the end of a dynamically-sized array, where .push() appends a zero-initialized element and returns a reference to it.

**Note:**

Dynamically-sized arrays can only be resized in storage. In memory, such arrays can be of arbitrary size but the size cannot be changed once an array is allocated.

### bytes and string as Arrays

Variables of type bytes and string are special arrays. The bytes type is similar to bytes1[], but it is packed tightly in calldata and memory. string is equal to bytes but does not allow length or index access.

Solidity does not have string manipulation functions, but there are third-party string libraries. You can also compare two strings by their keccak256-hash using keccak256(abi.encodePacked(s1)) == keccak256(abi. encodePacked(s2)) and concatenate two strings using string.concat(s1, s2).

You should use bytes over bytes1[] because it is cheaper, since using bytes1[] in memory adds 31 padding bytes between the elements. Note that in storage, the padding is absent due to tight packing, see bytes and string.

general rule, use bytes for arbitrary-length raw byte data and string for arbitrary-length string (UTF-8) data. If you can limit the length to a certain number of bytes, always use one of the value types bytes1 to bytes32 because they are much cheaper.

As a

**Note:**

If you want to access the byte-representation of a string s, use bytes(s).length / bytes(s)[7] = 'x';. Keep in mind that you are accessing the low-level bytes of the UTF-8 representation, and not the individual characters.

### The functions bytes.concat and string.concat

You can concatenate an arbitrary number of string values using string.concat. The function returns a single string memory array that contains the contents of the arguments without padding. If you want to use parameters of other types that are not implicitly convertible to string, you need to convert them to string first.

Analogously, the bytes.concat function can concatenate an arbitrary number of bytes or bytes1 ... bytes32 values. The function returns a single bytes memory array that contains the contents of the arguments without padding. If you want to use string parameters or other types that are not implicitly convertible to bytes, you need to convert them to bytes or bytes1/. . . /bytes32 first.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.12;
contract C {
string s = "Storage";
function f(bytes calldata bc, string memory sm, bytes16 b) public view {
string memory concatString = string.concat(s, string(bc), "Literal", sm);
assert((bytes(s).length + bc.length + 7 + bytes(sm).length) == bytes(concatString).length);
bytes memory concatBytes = bytes.concat(bytes(s), bc, bc[:2], "Literal", bytes(sm), b);
assert((bytes(s).length + bc.length + 2 + 7 + bytes(sm).length + b.length) == concatBytes.length);
}
}
```

If you call string.concat or bytes.concat without arguments they return an empty array.

### Allocating Memory Arrays

Memory arrays with dynamic length can be created using the new operator. As opposed to storage arrays, it is not possible to resize memory arrays (e.g. the .push member functions are not available). You either have to calculate the required size in advance or create a new memory array and copy every element.

As all variables in Solidity, the elements of newly allocated arrays are always initialized with the default value.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.16 <0.9.0;
contract C {
function f(uint len) public pure {
uint[] memory a = new uint[](7);
bytes memory b = new bytes(len);
assert(a.length == 7);
assert(b.length == len);
a[6] = 8;
}
}
```

### Array Literals

An array literal is a comma-separated list of one or more expressions, enclosed in square brackets ([...]). For example [1, a, f(3)]. The type of the array literal is determined as follows:

It is always a statically-sized memory array whose length is the number of expressions.

The base type of the array is the type of the first expression on the list such that all other expressions can be implicitly converted to it. It is a type error if this is not possible.

It is not enough that there is a type all the elements can be converted to. One of the elements has to be of that type.

In the example below, the type of [1, 2, 3] is uint8[3] memory, because the type of each of these constants is uint8. If you want the result to be a uint[3] memory type, you need to convert the first element to uint.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.16 <0.9.0;
contract C {
function f() public pure {
g([uint(1), 2, 3]);
}
function g(uint[3] memory) public pure {
// ...
}
}
```

The array literal [1, -1] is invalid because the type of the first expression is uint8 while the type of the second is int8 and they cannot be implicitly converted to each other. To make it work, you can use [int8(1), -1], for example.

Since fixed-size memory arrays of different type cannot be converted into each other (even if the base types can), you always have to specify a common base type explicitly if you want to use two-dimensional array literals:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.16 <0.9.0;
contract C {
function f() public pure returns (uint24[2][4] memory) {
uint24[2][4] memory x = [[uint24(0x1), 1], [0xffffff, 2], [uint24(0xff), 3], [uint24(0xffff), 4]];
// The following does not work, because some of the inner arrays are not of the right type.
// uint[2][4] memory x = [[0x1, 1], [0xffffff, 2], [0xff, 3], [0xffff, 4]];
return x;
}
}
```

Fixed size memory arrays cannot be assigned to dynamically-sized memory arrays, i.e. the following is not possible:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.0 <0.9.0;
// This will not compile.
contract C {
function f() public {
// The next line creates a type error because uint[3] memory
// cannot be converted to uint[] memory.
uint[] memory x = [uint(1), 3, 4];
}
}
```

It is planned to remove this restriction in the future, but it creates some complications because of how arrays are passed in the ABI.

If you want to initialize dynamically-sized arrays, you have to assign the individual elements:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.16 <0.9.0;
contract C {
function f() public pure {
uint[] memory x = new uint[](3);
x[0] = 1;
x[1] = 3;
x[2] = 4;
}
}
```

### Array Members

Arrays have a length member that contains their number of elements. The length of memory arrays is fixed (but dynamic, i.e. it can depend on runtime parameters) once they are created.

Dynamic storage arrays and bytes (not string) have a member function called push() that you can use to append a zero-initialised element at the end of the array. It returns a reference to the element, so that it can be used like x.push().t = 2 or x.push() = b.

Dynamic storage arrays and bytes (not string) have a member function called push(x) that you can use to append a given element at the end of the array. The function returns nothing.

Dynamic storage arrays and bytes (not string) have a member function called pop() that you can use to remove an element from the end of the array. This also implicitly calls delete on the removed element. The function returns nothing.

ò Note

Increasing the length of a storage array by calling push() has constant gas costs because storage is zero-initialised, while decreasing the length by calling pop() has a cost that depends on the “size” of the element being removed. If that element is an array, it can be very costly, because it includes explicitly clearing the removed elements similar to calling delete on them.

ò Note

### length:

### push():

### push(x):

### pop():

To use arrays of arrays in external (instead of public) functions, you need to activate ABI coder v2.

ò Note

In EVM versions before Byzantium, it was not possible to access dynamic arrays returned from function calls. If you call functions that return dynamic arrays, make sure to use an EVM that is set to Byzantium mode.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.6.0 <0.9.0;
contract ArrayContract {
uint[2**20] aLotOfIntegers;
// Note that the following is not a pair of dynamic arrays but a
// dynamic array of pairs (i.e. of fixed size arrays of length two).
// In Solidity, T[k] and T[] are always arrays with elements of type T,
// even if T itself is an array.
// Because of that, bool[2][] is a dynamic array of elements
// that are bool[2]. This is different from other languages, like C.
// Data location for all state variables is storage.
bool[2][] pairsOfFlags;
// newPairs is stored in memory
function setAllFlagPairs(bool[2][] memory newPairs) public {
// assignment to a storage array performs a copy of ``newPairs`` and
// replaces the complete array ``pairsOfFlags``.
pairsOfFlags = newPairs;
}
struct StructType {
uint[] contents;
uint moreInfo;
}
StructType s;
function f(uint[] memory c) public {
// stores a reference to ``s`` in ``g``
StructType storage g = s;
// also changes ``s.moreInfo``.
g.moreInfo = 2;
// assigns a copy because ``g.contents``
// is not a local variable, but a member of
// a local variable.
g.contents = c;
}
function setFlagPair(uint index, bool flagA, bool flagB) public {
// access to a non-existing index will throw an exception
pairsOfFlags[index][0] = flagA;
pairsOfFlags[index][1] = flagB;
}
function changeFlagArraySize(uint newSize) public {
// using push and pop is the only way to change the
// length of an array
if (newSize < pairsOfFlags.length) {
while (pairsOfFlags.length > newSize)
pairsOfFlags.pop();
} else if (newSize > pairsOfFlags.length) {
while (pairsOfFlags.length < newSize)
pairsOfFlags.push();
}
}
function clear() public {
// these clear the arrays completely
delete pairsOfFlags;
delete aLotOfIntegers;
// identical effect here
pairsOfFlags = new bool[2][](0);
}
bytes byteData;
function byteArrays(bytes memory data) public {
// byte arrays ("bytes") are different as they are stored without padding,
// but can be treated identical to "uint8[]"
byteData = data;
for (uint i = 0; i < 7; i++)
byteData.push();
byteData[3] = 0x08;
delete byteData[2];
}
function addFlag(bool[2] memory flag) public returns (uint) {
pairsOfFlags.push(flag);
return pairsOfFlags.length;
}
function createMemoryArray(uint size) public pure returns (bytes memory) {
// Dynamic memory arrays are created using `new`:
uint[2][] memory arrayOfPairs = new uint[2][](size);
// Inline arrays are always statically-sized and if you only
// use literals, you have to provide at least one type.
arrayOfPairs[0] = [uint(1), 2];
// Create a dynamic byte array:
bytes memory b = new bytes(200);
for (uint i = 0; i < b.length; i++)
b[i] = bytes1(uint8(i));
return b;
}
}
```

### Dangling References to Storage Array Elements

When working with storage arrays, you need to take care to avoid dangling references. A dangling reference is a reference that points to something that no longer exists or has been moved without updating the reference. A dangling reference can for example occur, if you store a reference to an array element in a local variable and then .pop() from the containing array:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.8.0 <0.9.0;
contract C {
uint[][] s;
function f() public {
// Stores a pointer to the last array element of s.
uint[] storage ptr = s[s.length - 1];
// Removes the last array element of s.
s.pop();
// Writes to the array element that is no longer within the array.
ptr.push(0x42);
// Adding a new element to ``s`` now will not add an empty array, but
// will result in an array of length 1 with ``0x42`` as element.
s.push();
assert(s[s.length - 1][0] == 0x42);
}
}
```

The write in ptr.push(0x42) will not revert, despite the fact that ptr no longer refers to a valid element of s. Since the compiler assumes that unused storage is always zeroed, a subsequent s.push() will not explicitly write zeroes to storage, so the last element of s after that push() will have length 1 and contain 0x42 as its first element.

Note that Solidity does not allow to declare references to value types in storage. These kinds of explicit dangling references are restricted to nested reference types. However, dangling references can also occur temporarily when using complex expressions in tuple assignments:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.8.0 <0.9.0;
contract C {
uint[] s;
uint[] t;
constructor() {
// Push some initial values to the storage arrays.
s.push(0x07);
t.push(0x03);
}
function g() internal returns (uint[] storage) {
s.pop();
return t;
}
function f() public returns (uint[] memory) {
// The following will first evaluate ``s.push()`` to a reference to a new element
// at index 1. Afterwards, the call to ``g`` pops this new element, resulting in
// the left-most tuple element to become a dangling reference. The assignment still
// takes place and will write outside the data area of ``s``.
(s.push(), g()[0]) = (0x42, 0x17);
// A subsequent push to ``s`` will reveal the value written by the previous
// statement, i.e. the last element of ``s`` at the end of this function will have
// the value ``0x42``.
s.push();
return s;
}
}
```

It is always safer to only assign to storage once per statement and to avoid complex expressions on the left-hand-side of an assignment.

You need to take particular care when dealing with references to elements of bytes arrays, since a .push() on a bytes array may switch from short to long layout in storage.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.8.0 <0.9.0;
// This will report a warning
contract C {
bytes x = "012345678901234567890123456789";
function test() external returns(uint) {
(x.push(), x.push()) = (0x01, 0x02);
return x.length;
}
}
```

Here, when the first x.push() is evaluated, x is still stored in short layout, thereby x.push() returns a reference to an element in the first storage slot of x. However, the second x.push() switches the bytes array to large layout. Now the element that x.push() referred to is in the data area of the array while the reference still points at its original location, which is now a part of the length field and the assignment will effectively garble the length of x. To be safe, only enlarge bytes arrays by at most one element during a single assignment and do not simultaneously index-access the array in the same statement.

While the above describes the behavior of dangling storage references in the current version of the compiler, any code with dangling references should be considered to have undefined behavior. In particular, this means that any future version of the compiler may change the behavior of code that involves dangling references.

Be sure to avoid dangling references in your code!

### Array Slices

Array slices are a view on a contiguous portion of an array. They are written as x[start:end], where start and end are expressions resulting in a uint256 type (or implicitly convertible to it). The first element of the slice is x[start] and the last element is x[end - 1].

If start is greater than end or if end is greater than the length of the array, an exception is thrown.

Both start and end are optional: start defaults to 0 and end defaults to the length of the array.

Array slices do not have any members. They are implicitly convertible to arrays of their underlying type and support index access. Index access is not absolute in the underlying array, but relative to the start of the slice.

Array slices do not have a type name which means no variable can have an array slices as type, they only exist in intermediate expressions.

ò Note

As of now, array slices are only implemented for calldata arrays.

Array slices are useful to ABI-decode secondary data passed in function parameters:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.8.5 <0.9.0;
contract Proxy {
/// @dev Address of the client contract managed by proxy i.e., this contract
address client;
constructor(address client_) {
client = client_;
}
/// Forward call to "setOwner(address)" that is implemented by client
/// after doing basic validation on the address argument.
function forward(bytes calldata payload) external {
bytes4 sig = bytes4(payload[:4]);
// Due to truncating behavior, bytes4(payload) performs identically.
// bytes4 sig = bytes4(payload);
if (sig == bytes4(keccak256("setOwner(address)"))) {
address owner = abi.decode(payload[4:], (address));
require(owner != address(0), "Address of owner cannot be zero.");
}
(bool status,) = client.delegatecall(payload);
require(status, "Forwarded call failed.");
}
}
```

### Structs

Solidity provides a way to define new types in the form of structs, which is shown in the following example:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.6.2 <0.9.0;
// Defines a new type with two fields.
// Declaring a struct outside of a contract allows
// it to be shared by multiple contracts.
// Here, this is not really needed.
struct Funder {
address addr;
uint amount;
}
contract CrowdFunding {
// Structs can also be defined inside contracts, which makes them
// visible only there and in derived contracts.
struct Campaign {
address payable beneficiary;
uint fundingGoal;
uint numFunders;
uint amount;
mapping(uint => Funder) funders;
}
uint numCampaigns;
mapping(uint => Campaign) campaigns;
function newCampaign(address payable beneficiary, uint goal) public returns (uint campaignID) {
campaignID = numCampaigns++; // campaignID is return variable
// We cannot use "campaigns[campaignID] = Campaign(beneficiary, goal, 0, 0)"
// because the right hand side creates a memory-struct "Campaign" that containsa mapping.
Campaign storage c = campaigns[campaignID];
c.beneficiary = beneficiary;
c.fundingGoal = goal;
}
function contribute(uint campaignID) public payable {
Campaign storage c = campaigns[campaignID];
// Creates a new temporary memory struct, initialised with the given values
// and copies it over to storage.
// Note that you can also use Funder(msg.sender, msg.value) to initialise.
c.funders[c.numFunders++] = Funder({addr: msg.sender, amount: msg.value});
c.amount += msg.value;
}
function checkGoalReached(uint campaignID) public returns (bool reached) {
Campaign storage c = campaigns[campaignID];
if (c.amount < c.fundingGoal)
return false;
uint amount = c.amount;
c.amount = 0;
(bool success, ) = c.beneficiary.call{value: amount}("");
return success;
}
}
```

The contract does not provide the full functionality of a crowdfunding contract, but it contains the basic concepts necessary to understand structs. Struct types can be used inside mappings and arrays and they can themselves contain mappings and arrays.

It is not possible for a struct to contain a member of its own type, although the struct itself can be the value type of a mapping member or it can contain a dynamically-sized array of its type. This restriction is necessary, as the size of the struct has to be finite.

Note how in all the functions, a struct type is assigned to a local variable with data location storage. This does not copy the struct but only stores a reference so that assignments to members of the local variable actually write to the state.

Of course, you can also directly access the members of the struct without assigning it to a local variable, as in campaigns[campaignID].amount = 0.

ò Note

Until Solidity 0.7.0, memory-structs containing members of storage-only types (e.g. mappings) were allowed and assignments like campaigns[campaignID] = Campaign(beneficiary, goal, 0, 0) in the example above would work and just silently skip those members.

## 3.6.3 Mapping Types

Mapping types use the syntax mapping(KeyType KeyName? => ValueType ValueName?) and variables of mapping type are declared using the syntax mapping(KeyType KeyName? => ValueType ValueName?) VariableName. The KeyType can be any built-in value type, bytes, string, or any contract or enum type. Other user-defined or complex types, such as mappings, structs or array types are not allowed. ValueType can be any type, including mappings, arrays and structs. KeyName and ValueName are optional (so mapping(KeyType => ValueType) works as well) and can be any valid identifier that is not a type.

You can think of mappings as hash tables, which are virtually initialised such that every possible key exists and is mapped to a value whose byte-representation is all zeros, a type’s default value. The similarity ends there, the key data is not stored in a mapping, only its keccak256 hash is used to look up the value.

Because of this, mappings do not have a length or a concept of a key or value being set, and therefore cannot be erased without extra information regarding the assigned keys (see Clearing Mappings).

Mappings can only have a data location of storage and thus are allowed for state variables, as storage reference types in functions, or as parameters for library functions. They cannot be used as parameters or return parameters of contract functions that are publicly visible. These restrictions are also true for arrays and structs that contain mappings.

You can mark state variables of mapping type as public and Solidity creates a getter for you. The KeyType becomes a parameter with name KeyName (if specified) for the getter. If ValueType is a value type or a struct, the getter returns ValueType with name ValueName (if specified). If ValueType is an array or a mapping, the getter has one parameter for each KeyType, recursively.

In the example below, the MappingExample contract defines a public balances mapping, with the key type an address, and a value type a uint, mapping an Ethereum address to an unsigned integer value. As uint is a value type, the getter returns a value that matches the type, which you can see in the MappingUser contract that returns the value at the specified address.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.0 <0.9.0;
contract MappingExample {
mapping(address => uint) public balances;
function update(uint newBalance) public {
balances[msg.sender] = newBalance;
}
}
contract MappingUser {
function f() public returns (uint) {
MappingExample m = new MappingExample();
m.update(100);
return m.balances(address(this));
}
}
```

The example below is a simplified version of an ERC20 token. _allowances is an example of a mapping type inside another mapping type. (https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/token/ERC20/ERC20.sol)

In the example below, the optional KeyName and ValueName are provided for the mapping. It does not affect any contract functionality or bytecode, it only sets the name field for the inputs and outputs in the ABI for the mapping’s getter.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.18;
contract MappingExampleWithNames {
mapping(address user => uint balance) public balances;
function update(uint newBalance) public {
balances[msg.sender] = newBalance;
}
}
```

The example below uses _allowances to record the amount someone else is allowed to withdraw from your account.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.22 <0.9.0;
contract MappingExample {
mapping(address => uint256) private _balances;
mapping(address => mapping(address => uint256)) private _allowances;
event Transfer(address indexed from, address indexed to, uint256 value);
event Approval(address indexed owner, address indexed spender, uint256 value);
function allowance(address owner, address spender) public view returns (uint256) {
return _allowances[owner][spender];
}
function transferFrom(address sender, address recipient, uint256 amount) public returns (bool) {
require(_allowances[sender][msg.sender] >= amount, "ERC20: Allowance not highenough.");
_allowances[sender][msg.sender] -= amount;
_transfer(sender, recipient, amount);
return true;
}
function approve(address spender, uint256 amount) public returns (bool) {
require(spender != address(0), "ERC20: approve to the zero address");
_allowances[msg.sender][spender] = amount;
emit Approval(msg.sender, spender, amount);
return true;
}
function _transfer(address sender, address recipient, uint256 amount) internal {
require(sender != address(0), "ERC20: transfer from the zero address");
require(recipient != address(0), "ERC20: transfer to the zero address");
require(_balances[sender] >= amount, "ERC20: Not enough funds.");
_balances[sender] -= amount;
_balances[recipient] += amount;
emit Transfer(sender, recipient, amount);
}
}
```

### Iterable Mappings

You cannot iterate over mappings, i.e. you cannot enumerate their keys. It is possible, though, to implement a data structure on top of them and iterate over that. For example, the code below implements an IterableMapping library that the User contract then adds data to, and the sum function iterates over to sum all the values.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.8;
struct IndexValue { uint keyIndex; uint value; }
struct KeyFlag { uint key; bool deleted; }
struct itmap {
mapping(uint => IndexValue) data;
KeyFlag[] keys;
uint size;
}
type Iterator is uint;
library IterableMapping {
function insert(itmap storage self, uint key, uint value) internal returns (bool replaced) {
uint keyIndex = self.data[key].keyIndex;
self.data[key].value = value;
if (keyIndex > 0)
return true;
else {
keyIndex = self.keys.length;
self.keys.push();
self.data[key].keyIndex = keyIndex + 1;
self.keys[keyIndex].key = key;
self.size++;
return false;
}
}
function remove(itmap storage self, uint key) internal returns (bool success) {
uint keyIndex = self.data[key].keyIndex;
if (keyIndex == 0)
return false;
delete self.data[key];
self.keys[keyIndex - 1].deleted = true;
self.size --;
}
function contains(itmap storage self, uint key) internal view returns (bool) {
return self.data[key].keyIndex > 0;
}
function iterateStart(itmap storage self) internal view returns (Iterator) {
return iteratorSkipDeleted(self, 0);
}
function iterateValid(itmap storage self, Iterator iterator) internal view returns(bool) {
return Iterator.unwrap(iterator) < self.keys.length;
}
function iterateNext(itmap storage self, Iterator iterator) internal view returns (Iterator) {
return iteratorSkipDeleted(self, Iterator.unwrap(iterator) + 1);
}
function iterateGet(itmap storage self, Iterator iterator) internal view returns (uint key, uint value) {
uint keyIndex = Iterator.unwrap(iterator);
key = self.keys[keyIndex].key;
value = self.data[key].value;
}
function iteratorSkipDeleted(itmap storage self, uint keyIndex) private view returns (Iterator) {
while (keyIndex < self.keys.length && self.keys[keyIndex].deleted)
keyIndex++;
return Iterator.wrap(keyIndex);
}
}
// How to use it
contract User {
// Just a struct holding our data.
itmap data;
// Apply library functions to the data type.
using IterableMapping for itmap;
// Insert something
function insert(uint k, uint v) public returns (uint size) {
// This calls IterableMapping.insert(data, k, v)
data.insert(k, v);
// We can still access members of the struct,
// but we should take care not to mess with them.
return data.size;
}
// Computes the sum of all stored data.
function sum() public view returns (uint s) {
for (
Iterator i = data.iterateStart();
data.iterateValid(i);
i = data.iterateNext(i)
) {
(, uint value) = data.iterateGet(i);
s += value;
}
}
}
```

## 3.6.4 Operators

Arithmetic and bit operators can be applied even if the two operands do not have the same type. For example, you can compute y = x + z, where x is a uint8 and z has the type uint32. In these cases, the following mechanism will be used to determine the type in which the operation is computed (this is important in case of overflow) and the type of the operator’s result:

- 1. If the type of the right operand can be implicitly converted to the type of the left operand, use the type of the left operand,

- 2. if the type of the left operand can be implicitly converted to the type of the right operand, use the type of the right operand,

- 3. otherwise, the operation is not allowed.

In case one of the operands is a literal number it is first converted to its “mobile type”, which is the smallest type that can hold the value (unsigned types of the same bit-width are considered “smaller” than the signed types). If both are literal numbers, the operation is computed with effectively unlimited precision in that the expression is evaluated to whatever precision is necessary so that none is lost when the result is used with a non-literal type.

The operator’s result type is the same as the type the operation is performed in, except for comparison operators where the result is always bool.

The operators ** (exponentiation), << and >> use the type of the left operand for the operation and the result.

### Ternary Operator

The ternary operator is used in expressions of the form <expression> ? <trueExpression> : <falseExpression>. It evaluates one of the latter two given expressions depending upon the result of the evaluation of the main <expression>. If <expression> evaluates to true, then <trueExpression> will be evaluated, otherwise <falseExpression> is evaluated.

The result of the ternary operator does not have a rational number type, even if all of its operands are rational number literals. The result type is determined from the types of the two operands in the same way as above, converting to their mobile type first if required.

As a consequence, 255 + (true ? 1 : 0) will revert due to arithmetic overflow. The reason is that (true ? 1 : 0) is of uint8 type, which forces the addition to be performed in uint8 as well, and 256 exceeds the range allowed for this type.

Another consequence is that an expression like 1.5 + 1.5 is valid but 1.5 + (true ? 1.5 : 2.5) is not. This is because the former is a rational expression evaluated in unlimited precision and only its final value matters. The latter involves a conversion of a fractional rational number to an integer, which is currently disallowed.

### Compound and Increment/Decrement Operators

If a is an LValue (i.e. a variable or something that can be assigned to), the following operators are available as shorthands:

a += e is equivalent to a = a + e. The operators -=, *=, /=, %=, |=, &=, ^=, <<= and >>= are defined accordingly. a++ and a-- are equivalent to a += 1 / a -= 1 but the expression itself still has the previous value of a. In contrast, --a and ++a have the same effect on a but return the value after the change.

### delete

delete a assigns the initial value for the type to a. I.e. for integers it is equivalent to a = 0, but it can also be used on arrays, where it assigns a dynamic array of length zero or a static array of the same length with all elements set to their initial value. delete a[x] deletes the item at index x of the array and leaves all other elements and the length of the array untouched. This especially means that it leaves a gap in the array. If you plan to remove items, a mapping is probably a better choice.

For structs, it assigns a struct with all members reset. In other words, the value of a after delete a is the same as if a would be declared without assignment, with the following caveat:

delete you delete a struct, it will reset all members that are not mappings and also recurse into the members unless they are mappings. However, individual keys and what they map to can be deleted: If a is a mapping, then delete a[x] will delete the value stored at x.

It is important to note that delete a really behaves like an assignment to a, i.e. it stores a new object in a. This distinction is visible when a is reference variable: It will only reset a itself, not the value it referred to previously.

has no effect on mappings (as the keys of mappings may be arbitrary and are generally unknown). So if

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.0 <0.9.0;
contract DeleteExample {
uint data;
uint[] dataArray;
function f() public {
uint x = data;
delete x; // sets x to 0, does not affect data
delete data; // sets data to 0, does not affect x
uint[] storage y = dataArray;
delete dataArray; // this sets dataArray.length to zero, but as uint[] is a complex object, also
// y is affected which is an alias to the storage object
// On the other hand: "delete y" is not valid, as assignments to local variables
// referencing storage objects can only be made from existing storage objects.
assert(y.length == 0);
}
}
```

### Order of Precedence of Operators

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

## 3.6.5 Conversions between Elementary Types

### Implicit Conversions

An implicit type conversion is automatically applied by the compiler in some cases during assignments, when passing arguments to functions and when applying operators. In general, an implicit conversion between value-types is possible if it makes sense semantically and no information is lost.

For example, uint8 is convertible to uint16 and int128 to int256, but int8 is not convertible to uint256, because uint256 cannot hold values such as -1.

If an operator is applied to different types, the compiler tries to implicitly convert one of the operands to the type of the other (the same is true for assignments). This means that operations are always performed in the type of one of the operands.

For more details about which implicit conversions are possible, please consult the sections about the types themselves.

In the example below, y and z, the operands of the addition, do not have the same type, but uint8 can be implicitly converted to uint16 and not vice-versa. Because of that, y is converted to the type of z before the addition is performed in the uint16 type. The resulting type of the expression y + z is uint16. Because it is assigned to a variable of type uint32 another implicit conversion is performed after the addition.

```
uint8 y;
uint16 z;
uint32 x = y + z;
```

### Explicit Conversions

If the compiler does not allow implicit conversion but you are confident a conversion will work, an explicit type conversion is sometimes possible. This may result in unexpected behavior and allows you to bypass some security features of the compiler, so be sure to test that the result is what you want and expect!

Take the following example that converts a negative int to a uint:

```
int y = -3;
uint x = uint(y);
```

At the end of this code snippet, x will have the value 0xfffff..fd (64 hex characters), which is -3 in the two’s complement representation of 256 bits.

If an integer is explicitly converted to a smaller type, higher-order bits are cut off:

```
uint32 a = 0x12345678;
uint16 b = uint16(a); // b will be 0x5678 now
```

If an integer is explicitly converted to a larger type, it is padded on the left (i.e., at the higher order end). The result of the conversion will compare equal to the original integer:

```
uint16 a = 0x1234;
uint32 b = uint32(a); // b will be 0x00001234 now
assert(a == b);
```

Fixed-size bytes types behave differently during conversions. They can be thought of as sequences of individual bytes and converting to a smaller type will cut off the sequence:

```
bytes2 a = 0x1234;
bytes1 b = bytes1(a); // b will be 0x12
```

If a fixed-size bytes type is explicitly converted to a larger type, it is padded on the right. Accessing the byte at a fixed index will result in the same value before and after the conversion (if the index is still in range):

```
bytes2 a = 0x1234;
bytes4 b = bytes4(a); // b will be 0x12340000
assert(a[0] == b[0]);
assert(a[1] == b[1]);
```

Since integers and fixed-size byte arrays behave differently when truncating or padding, explicit conversions between integers and fixed-size byte arrays are only allowed, if both have the same size. If you want to convert between integers and fixed-size byte arrays of different size, you have to use intermediate conversions that make the desired truncation and padding rules explicit:

```
bytes2 a = 0x1234;
uint32 b = uint16(a); // b will be 0x00001234
uint32 c = uint32(bytes4(a)); // c will be 0x12340000
uint8 d = uint8(uint16(a)); // d will be 0x34
uint8 e = uint8(bytes1(a)); // e will be 0x12
```

bytes arrays and bytes calldata slices can be converted explicitly to fixed bytes types (bytes1/. . . /bytes32). In case the array is longer than the target fixed bytes type, truncation at the end will happen. If the array is shorter than the target type, it will be padded with zeros at the end.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.5;
contract C {
bytes s = "abcdefgh";
function f(bytes calldata c, bytes memory m) public view returns (bytes16, bytes3) {
require(c.length == 16, "");
bytes16 b = bytes16(m); // if length of m is greater than 16, truncation will happen
b = bytes16(s); // padded on the right, so result is "abcdefgh\0\0\0\0\0\0\0\0"
bytes3 b1 = bytes3(s); // truncated, b1 equals to "abc"
b = bytes16(c[:8]); // also padded with zeros
return (b, b1);
}
}
```

## 3.6.6 Conversions between Literals and Elementary Types

### Integer Types

Decimal and hexadecimal number literals can be implicitly converted to any integer type that is large enough to represent it without truncation:

```
uint8 a = 12; // fine
uint32 b = 1234; // fine
uint16 c = 0x123456; // fails, since it would have to truncate to 0x3456
```

**Note:**

Prior to version 0.8.0, any decimal or hexadecimal number literals could be explicitly converted to an integer type. From 0.8.0, such explicit conversions are as strict as implicit conversions, i.e., they are only allowed if the literal fits in the resulting range.

### Fixed-Size Byte Arrays

Decimal number literals cannot be implicitly converted to fixed-size byte arrays. Hexadecimal number literals can be, but only if the number of hex digits exactly fits the size of the bytes type. As an exception both decimal and hexadecimal literals which have a value of zero can be converted to any fixed-size bytes type:

```
bytes2 a = 54321; // not allowed
bytes2 b = 0x12; // not allowed
bytes2 c = 0x123; // not allowed
bytes2 d = 0x1234; // fine
bytes2 e = 0x0012; // fine
bytes4 f = 0; // fine
bytes4 g = 0x0; // fine
```

String literals and hex string literals can be implicitly converted to fixed-size byte arrays, if their number of characters is less than or equal to the size of the bytes type:

```
bytes2 a = hex"1234"; // fine
bytes2 b = "xy"; // fine
bytes2 c = hex"12"; // fine
bytes2 e = "x"; // fine
bytes2 f = "xyz"; // not allowed
```

### Addresses

As described in Address Literals, hex literals of the correct size that pass the checksum test are of address type. No other literals can be implicitly converted to the address type.

Explicit conversions to address are allowed only from bytes20 and uint160.

An address a can be converted explicitly to address payable via payable(a).

ò Note

Prior to version 0.8.0, it was possible to explicitly convert from any integer type (of any size, signed or unsigned) to address or address payable. Starting with 0.8.0 only conversion from uint160 is allowed.
