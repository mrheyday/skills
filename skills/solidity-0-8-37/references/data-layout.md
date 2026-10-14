# Layout in Storage/Transient Storage, Memory, Calldata; Cleaning up Variables; Source Mappings (3.16–3.20)

> Source: Solidity documentation, release 0.8.37-develop (Sep 10, 2026), https://docs.soliditylang.org/ — text reproduced from the official docs; code indentation was flattened by the export and is not normative.

## Contents

- 3.16 Layout of State Variables in Storage and Transient Storage
  - 3.16.1 Mappings and Dynamic Arrays
  - 3.16.2 JSON Output
- 3.17 Layout in Memory
  - 3.17.1 Differences to Layout in Storage
- 3.18 Layout of Call Data
- 3.19 Cleaning Up Variables
- 3.20 Source Mappings

---

# 3.16 Layout of State Variables in Storage and Transient Storage

**Note:**

The rules described in this section apply for both storage and transient storage data locations. The layouts are completely independent and don’t interfere with each other’s variable locations. Thus storage and transient storage state variables can be safely interleaved without any side effects. Only value types are supported for transient storage.

State variables of contracts are stored in storage in a compact way such that multiple values sometimes use the same storage slot. Except for dynamically-sized arrays and mappings (see below), data is stored contiguously item after item starting with the first state variable, which is stored in slot 0. For each variable, a size in bytes is determined according to its type. Multiple, contiguous items that need less than 32 bytes are packed into a single storage slot if possible, according to the following rules:

- The first item in a storage slot is stored lower-order aligned.

- Value types use only as many bytes as are necessary to store them.

- If a value type does not fit the remaining part of a storage slot, it is stored in the next storage slot.

- Structs and array data always start a new slot and their items are packed tightly according to these rules.

- Items following struct or array data always start a new storage slot.

For contracts that use inheritance, the ordering of state variables is determined by the C3-linearized order of contracts starting with the most base-ward contract. If allowed by the above rules, state variables from different contracts do share the same storage slot.

The elements of structs and arrays are stored after each other, just as if they were given as individual values.

If a contract specifies a custom storage layout, the slots assigned to static storage variables are shifted according the value defined as the layout base. Locations of dynamic arrays and mappings are also indirectly affected by this due to shifting of the static slots they are based on. The custom layout is specified in the most derived contract and, following the order explained above, starting from the most base-ward contract’s variables, all storage slots are adjusted.

In the following example, contract C inherits from contracts A and B and also specifies a custom storage base slot. The result is that all storage variable slots of the inheritance tree are adjusted according to the value specified by C.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.29;
struct S {
int32 x;
bool y;
}
contract A {
uint a;
uint128 transient b;
uint constant c = 10;
uint immutable d = 12;
}
contract B {
uint8[] e;
mapping(uint => S) f;
uint16 g;
uint16 h;
bytes16 transient i;
S s;
int8 k;
}
contract C is A, B layout at 42 {
bytes21 l;
uint8[10] m;
bytes5[8] n;
bytes5 o;
}
```

In the example, the storage layout starts with the inherited state variable a stored directly inside the base slot (slot 42). Transient, constant and immutable variables are stored in separate locations, and thus, b, i, c and d have no effect on the storage layout. Then we get to the dynamic array e and mapping f. They both reserve a whole slot whose address will be used to calculate the location where their data is actually stored. The slot cannot be shared with any other variable, because the resulting addresses must be unique. The next two variables, g and h, need 2 bytes each and can be packed together into slot 45, at offsets 0 and 2 respectively. Since s is a struct, its two members are packed contiguously, each taking up 5 bytes. Even though they both would still fit in slot 45, structs and arrays always start a new slot. Therefore, s is placed in slot 46 and the next variable, k, in slot 47. Base contracts, on the other hand, can share slots with derived ones, so l does not require an new one. Then variable m, which is an array of 10 items, gets into slot 48 and takes up 10 bytes. n is an array as well, but due to the size of its items, cannot fill its first slot perfectly and spills over to the next one. Finally, variable o ends up in slot 51, even though it is of the same type as items of n. As explained before, variables after structs and arrays always start a new slot.

Putting it all together, the storage and transient storage layouts of contract C can be illustrated as follows:

- Storage:

```
42 [aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa]
43 [eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee]
44 [ffffffffffffffffffffffffffffffff]
45 [ hhgg]
46 [ yxxxx]
47 [ lllllllllllllllllllllk]
48 [ mmmmmmmmmm]
49 [ nnnnnnnnnnnnnnnnnnnnnnnnnnnnnn]
50 [ nnnnnnnnnn]
51 [ ooooo]
```

- Transient storage:

00 [iiiiiiiiiiiiiiiibbbbbbbbbbbbbbbb]

Note that the storage specifier affects A and B only as a part of C’s inheritance hierarchy. When deployed independently, their storage starts at 0:

- Storage layout of A:

```
00 [aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa]
```

- Storage layout of B:

```
00 [eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee]
01 [ffffffffffffffffffffffffffffffff]
02 [ hhgg]
03 [ yxxxx]
04 [ k]
```

**Warning:**

When using elements that are smaller than 32 bytes, your contract’s gas usage may be higher. This is because the EVM operates on 32 bytes at a time. Therefore, if the element is smaller than that, the EVM must use more operations in order to reduce the size of the element from 32 bytes to the desired size.

It might be beneficial to use reduced-size types if you are dealing with storage values because the compiler will pack multiple elements into one storage slot, and thus, combine multiple reads or writes into a single operation. If you are not reading or writing all the values in a slot at the same time, this can have the opposite effect, though: When one value is written to a multi-value storage slot, the storage slot has to be read first and then combined with the new value such that other data in the same slot is not destroyed.

When dealing with function arguments or memory values, there is no inherent benefit because the compiler does not pack these values.

Finally, in order to allow the EVM to optimize for this, ensure that you try to order your storage variables and struct members such that they can be packed tightly. For example, declaring your storage variables in the order of uint128, uint128, uint256 instead of uint128, uint256, uint128, as the former will only take up two slots of storage whereas the latter will take up three.

**Note:**

The layout of state variables in storage is considered to be part of the external interface of Solidity due to the fact that storage pointers can be passed to libraries. This means that any change to the rules outlined in this section is considered a breaking change of the language and due to its critical nature should be considered very carefully before being executed. In the event of such a breaking change, we would want to release a compatibility mode in which the compiler would generate bytecode supporting the old layout.

## 3.16.1 Mappings and Dynamic Arrays

Due to their unpredictable size, mappings and dynamically-sized array types cannot be stored “in between” the state variables preceding and following them. Instead, they are considered to occupy only 32 bytes with regards to the rules above and the elements they contain are stored starting at a different storage slot that is computed using a Keccak-256 hash.

Assume the storage location of the mapping or array ends up being a slot p after applying the storage layout rules. For dynamic arrays, this slot stores the number of elements in the array (byte arrays and strings are an exception, see below). For mappings, the slot stays empty, but it is still needed to ensure that even if there are two mappings next to each other, their content ends up at different storage locations.

Array data is located starting at keccak256(p) and it is laid out in the same way as statically-sized array data would: One element after the other, potentially sharing storage slots if the elements are not longer than 16 bytes. Dynamic arrays of dynamic arrays apply this rule recursively. The location of element x[i][j], where the type of x is uint24[][], is computed as follows (again, assuming x itself is stored at slot p): The slot is keccak256(keccak256(p) + i) + floor(j / floor(256 / 24)) and the element can be obtained from the slot data v using (v >> ((j % floor(256 / 24)) * 24)) & type(uint24).max.

The value corresponding to a mapping key k is located at keccak256(h(k) . p) where . is concatenation and h is a function that is applied to the key depending on its type:

- for value types, h pads the value to 32 bytes in the same way as when storing the value in memory.

- for strings and byte arrays, h(k) is just the unpadded data.

If the mapping value is a non-value type, the computed slot marks the start of the data. If the value is of struct type, for example, you have to add an offset corresponding to the struct member to reach the member.

As an example, consider the following contract:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.0 <0.9.0;
contract C {
struct S { uint16 a; uint16 b; uint256 c; }
uint x;
mapping(uint => mapping(uint => S)) data;
}
```

Let us compute the storage location of data[4][9].c. The position of the mapping itself is 1

(the variable x with 32 bytes precedes it). This means data[4] is stored at keccak256(uint256(4) . uint256(1)). The type of data[4] is again a mapping and the data for data[4][9] starts at slot keccak256(uint256(9) . keccak256(uint256(4) . uint256(1))). The slot offset of the member c inside the struct S is 1 because a and b are packed in a single slot. This means the slot for data[4][9].c is keccak256(uint256(9) . keccak256(uint256(4) . uint256(1))) + 1. The type of the value is uint256, so it uses a single slot.

### bytes and string

bytes and string are encoded identically. In general, the encoding is similar to bytes1[], in the sense that there is a slot for the array itself and a data area that is computed using a keccak256 hash of that slot’s position. However, for short values (shorter than 32 bytes) the array elements are stored together with the length in the same slot.

In particular: if the data is at most 31 bytes long, the elements are stored in the higher-order bytes (left aligned) and the lowest-order byte stores the value length * 2. For byte arrays that store data which is 32 or more bytes long, the main slot p stores length * 2 + 1 and the data is stored as usual in keccak256(p). This means that you can distinguish a short array from a long array by checking if the lowest bit is set: short (not set) and long (set).

**Note:**

Handling invalidly encoded slots is currently not supported but may be added in the future. If you are compiling via IR, reading an invalidly encoded slot results in a Panic(0x22) error.

## 3.16.2 JSON Output

The storage (or transient storage) layout of a contract can be requested via the standard JSON interface. The output is a JSON object containing two keys, storage and types. The storage object is an array where each element has the following form:

```
{
"astId": 2,
"contract": "fileA:A",
"label": "x",
"offset": 0,
"slot": "0",
"type": "t_uint256"
}
```

The example above is the storage layout of contract A { uint x; } from source unit fileA and

- astId is the id of the AST node of the state variable’s declaration

- contract is the name of the contract including its path as prefix

- label is the name of the state variable

- offset is the offset in bytes within the storage slot according to the encoding

- slot is the storage slot where the state variable resides or starts. This number may be very large and therefore its JSON value is represented as a string.

- type is an identifier used as key to the variable’s type information (described in the following)

The given type, in this case t_uint256 represents an element in types, which has the form:

```
{
"encoding": "inplace",
"label": "uint256",
"numberOfBytes": "32",
}
```

where

- encoding how the data is encoded in storage, where the possible values are:

- inplace: data is laid out contiguously in storage (see above).

- mapping: Keccak-256 hash-based method (see above).

- dynamic_array: Keccak-256 hash-based method (see above).

- bytes: single slot or Keccak-256 hash-based depending on the data size (see above).

- label is the canonical type name.

- numberOfBytes is the number of used bytes (as a decimal string). Note that if numberOfBytes > 32 this means that more than one slot is used.

Some types have extra information besides the four above. Mappings contain its key and value types (again referencing an entry in this mapping of types), arrays have its base type, and structs list their members in the same format as the top-level storage (see above).

**Note:**

The JSON output format of a contract’s storage layout is still considered experimental and is subject to change in non-breaking releases of Solidity.

The following example shows a contract and both its storage and transient storage layout, containing value and reference types, types that are encoded packed, and nested types.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.28;
contract A {
struct S {
uint128 a;
uint128 b;
uint[2] staticArray;
uint[] dynArray;
}
uint x;
uint transient y;
uint w;
uint transient z;
S s;
address addr;
address transient taddr;
mapping(uint => mapping(address => bool)) map;
uint[] array;
string s1;
bytes b1;
}
```

### Storage Layout

```
{
"storage": [
{
"astId": 15,
"contract": "fileA:A",
"label": "x",
"offset": 0,
"slot": "0",
"type": "t_uint256"
},
{
"astId": 19,
"contract": "fileA:A",
"label": "w",
"offset": 0,
"slot": "1",
"type": "t_uint256"
},
{
"astId": 24,
"contract": "fileA:A",
"label": "s",
"offset": 0,
"slot": "2",
"type": "t_struct(S)13_storage"
},
{
"astId": 26,
"contract": "fileA:A",
"label": "addr",
"offset": 0,
"slot": "6",
"type": "t_address"
},
{
"astId": 34,
"contract": "fileA:A",
"label": "map",
"offset": 0,
"slot": "7",
"type": "t_mapping(t_uint256,t_mapping(t_address,t_bool))"
},
{
"astId": 37,
"contract": "fileA:A",
"label": "array",
"offset": 0,
"slot": "8",
"type": "t_array(t_uint256)dyn_storage"
},
{
"astId": 39,
"contract": "fileA:A",
"label": "s1",
"offset": 0,
"slot": "9",
"type": "t_string_storage"
},
{
"astId": 41,
"contract": "fileA:A",
"label": "b1",
"offset": 0,
"slot": "10",
"type": "t_bytes_storage"
}
],
"types": {
"t_address": {
"encoding": "inplace",
"label": "address",
"numberOfBytes": "20"
},
"t_array(t_uint256)2_storage": {
"base": "t_uint256",
"encoding": "inplace",
"label": "uint256[2]",
"numberOfBytes": "64"
},
"t_array(t_uint256)dyn_storage": {
"base": "t_uint256",
"encoding": "dynamic_array",
"label": "uint256[]",
"numberOfBytes": "32"
},
"t_bool": {
"encoding": "inplace",
"label": "bool",
"numberOfBytes": "1"
},
"t_bytes_storage": {
"encoding": "bytes",
"label": "bytes",
"numberOfBytes": "32"
},
"t_mapping(t_address,t_bool)": {
"encoding": "mapping",
"key": "t_address",
"label": "mapping(address => bool)",
"numberOfBytes": "32",
"value": "t_bool"
},
"t_mapping(t_uint256,t_mapping(t_address,t_bool))": {
"encoding": "mapping",
"key": "t_uint256",
"label": "mapping(uint256 => mapping(address => bool))",
"numberOfBytes": "32",
"value": "t_mapping(t_address,t_bool)"
},
"t_string_storage": {
"encoding": "bytes",
"label": "string",
"numberOfBytes": "32"
},
"t_struct(S)13_storage": {
"encoding": "inplace",
"label": "struct A.S",
"members": [
{
"astId": 3,
"contract": "fileA:A",
"label": "a",
"offset": 0,
"slot": "0",
"type": "t_uint128"
},
{
"astId": 5,
"contract": "fileA:A",
"label": "b",
"offset": 16,
"slot": "0",
"type": "t_uint128"
},
{
"astId": 9,
"contract": "fileA:A",
"label": "staticArray",
"offset": 0,
"slot": "1",
"type": "t_array(t_uint256)2_storage"
},
{
"astId": 12,
"contract": "fileA:A",
"label": "dynArray",
"offset": 0,
"slot": "3",
"type": "t_array(t_uint256)dyn_storage"
}
],
"numberOfBytes": "128"
},
"t_uint128": {
"encoding": "inplace",
"label": "uint128",
"numberOfBytes": "16"
},
"t_uint256": {
"encoding": "inplace",
"label": "uint256",
"numberOfBytes": "32"
}
}
}
```

### Transient Storage Layout

```
{
"storage": [
{
"astId": 17,
"contract": "fileA:A",
"label": "y",
"offset": 0,
"slot": "0",
"type": "t_uint256"
},
{
"astId": 21,
"contract": "fileA:A",
"label": "z",
"offset": 0,
"slot": "1",
"type": "t_uint256"
},
{
"astId": 28,
"contract": "fileA:A",
"label": "taddr",
"offset": 0,
"slot": "2",
"type": "t_address"
}
],
"types": {
"t_address": {
"encoding": "inplace",
"label": "address",
"numberOfBytes": "20"
},
"t_uint256": {
"encoding": "inplace",
"label": "uint256",
"numberOfBytes": "32"
}
}
}
```

# 3.17 Layout in Memory

Solidity reserves four 32-byte slots, with specific byte ranges (inclusive of endpoints) being used as follows:

- 0x00 - 0x3f (64 bytes): scratch space for hashing methods

- 0x40 - 0x5f (32 bytes): currently allocated memory size (aka. free memory pointer)

- 0x60 - 0x7f (32 bytes): zero slot

Scratch space can be used between statements (i.e. within inline assembly). The zero slot is used as initial value for dynamic memory arrays and should never be written to (the free memory pointer points to 0x80 initially).

Solidity always places new objects at the free memory pointer and memory is never freed (this might change in the future).

Elements in memory arrays in Solidity always occupy multiples of 32 bytes (this is even true for bytes1[], but not for bytes and string). Multi-dimensional memory arrays are pointers to memory arrays. The length of a dynamic array is stored at the first slot of the array and followed by the array elements.

**Warning:**

There are some operations in Solidity that need a temporary memory area larger than 64 bytes and therefore will not fit into the scratch space. They will be placed where the free memory points to, but given their short lifetime, the pointer is not updated. The memory may or may not be zeroed out. Because of this, one should not expect the free memory to point to zeroed out memory.

While it may seem like a good idea to use msize to arrive at a definitely zeroed out memory area, using such a pointer non-temporarily without updating the free memory pointer can have unexpected results.

## 3.17.1 Differences to Layout in Storage

As described above the layout in memory is different from the layout in storage. Below there are some examples.

### Example for Difference in Arrays

The following array occupies 32 bytes (1 slot) in storage, but 128 bytes (4 items with 32 bytes each) in memory.

```
uint8[4] a;
```

### Example for Difference in Struct Layout

The following struct occupies 96 bytes (3 slots of 32 bytes) in storage, but 128 bytes (4 items with 32 bytes each) in memory.

```
struct S {
uint a;
uint b;
uint8 c;
uint8 d;
}
```

# 3.18 Layout of Call Data

The input data for a function call is assumed to be in the format defined by the ABI specification. Among others, the

ABI specification requires arguments to be padded to multiples of 32 bytes. The internal function calls use a different convention.

Arguments for the constructor ofa contract are directly appended at the end of the contract’s code, also in ABI encoding.

The constructor will access them through a hard-coded offset, and not by using the codesize opcode, since this of course changes when appending data to the code.

# 3.19 Cleaning Up Variables

Ultimately, all values in the EVM are stored in 256 bit words. Thus, in some cases, when the type of a value has less than 256 bits, it is necessary to clean the remaining bits. The Solidity compiler is designed to do such cleaning before any operations that might be adversely affected by the potential garbage in the remaining bits. For example, before writing a value to memory, the remaining bits need to be cleared because the memory contents can be used for computing hashes or sent as the data of a message call. Similarly, before storing a value in the storage, the remaining bits need to be cleaned because otherwise the garbled value can be observed.

Note that access via inline assembly is not considered such an operation: If you use inline assembly to access Solidity variables shorter than 256 bits, the compiler does not guarantee that the value is properly cleaned up.

Moreover, we do not clean the bits if the immediately following operation is not affected. For instance, since any non-

zero value is considered true by JUMPI instruction, we do not clean the boolean values before they are used as the condition for JUMPI.

In addition to the design principle above, the Solidity compiler cleans input data when it is loaded onto the stack.

The following table describes the cleaning rules applied to different types, where higher bits refers to the remaining bits in case the type has less than 256 bits.

| Type         | Valid Values                                                                                            | Cleanup of Invalid Values                                                            |
| ------------ | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| enum of n    | 0 until n - 1                                                                                           | throws exception                                                                     |
| members      |                                                                                                         |                                                                                      |
| bool         | 0 or 1                                                                                                  | results in 1                                                                         |
| signed inte- | higher bits set to                                                                                      | currently silently signextends to a valid value, i.e. all higher bits are set to the |
| gers         | the sign bit                                                                                            | sign bit; may throw an exception in the future                                       |
| unsigned in- | higher bits zeroed currently silently masks to a valid value, i.e. all higher bits are set to zero; may |                                                                                      |
| tegers       |                                                                                                         | throw an exception in the future                                                     |

Note that valid and invalid values are dependent on their type size. Consider uint8, the unsigned 8-bit type, which has the following valid values:

```
0000...0000 0000 0000
0000...0000 0000 0001
0000...0000 0000 0010
....
0000...0000 1111 1111
```

Any invalid value will have the higher bits set to zero:

| 0101...1101 0010 1010 invalid value |
| ----------------------------------- |
| 0000...0000 0010 1010 cleaned value |

For int8, the signed 8-bit type, the valid values are:

Negative

```
1111...1111 1111 1111
1111...1111 1111 1110
....
1111...1111 1000 0000
```

### Positive

```
0000...0000 0000 0000
0000...0000 0000 0001
0000...0000 0000 0010
....
0000...0000 0111 1111
```

The compiler will signextend the sign bit, which is 1 for negative and 0 for positive values, overwriting the higher bits:

Negative

| 0010...1010 1111 1111 invalid value |
| ----------------------------------- |
| 1111...1111 1111 1111 cleaned value |

### Positive

1101...0101 0000 0100 invalid value

0000...0000 0000 0100 cleaned value

# 3.20 Source Mappings

As part of the AST output, the compiler provides the range of the source code that is represented by the respective node in the AST. This can be used for various purposes ranging from static analysis tools that report errors based on the AST and debugging tools that highlight local variables and their uses.

Furthermore, the compiler can also generate a mapping from the bytecode to the range in the source code that generated the instruction. This is again important for static analysis tools that operate on bytecode level and for displaying the current position in the source code inside a debugger or for breakpoint handling. This mapping also contains other information, like the jump type and the modifier depth (see below).

Both kinds of source mappings use integer identifiers to refer to source files. The identifier of a source file is stored in output['sources'][sourceName]['id'] where output is the output of the standard-json compiler interface parsed as JSON. For some utility routines, the compiler generates “internal” source files that are not part of the original input but are referenced from the source mappings. These source files together with their identifiers can be obtained via output['contracts'][sourceName][contractName]['evm']['bytecode']['generatedSources'].

**Note:**

In the case of instructions that are not associated with any particular source file, the source mapping assigns an integer identifier of -1. This may happen for bytecode sections stemming from compiler-generated inline assembly statements.

The source mappings inside the AST use the following notation:

s:l:f

Where s is the byte-offset to the start of the range in the source file, l is the length of the source range in bytes and f is the source index mentioned above.

The encoding in the source mapping for the bytecode is more complicated: It is a list of s:l:f:j:m separated by ;.

Each of these elements corresponds to an instruction, i.e. you cannot use the byte offset but have to use the instruction offset (push instructions are longer than a single byte). The fields s, l and f are as above. j can be either i, o or - signifying whether a jump instruction goes into a function, returns from a function or is a regular jump as part of e.g. a loop. The last field, m, is an integer that denotes the “modifier depth”. This depth is increased whenever the placeholder statement (_) is entered in a modifier and decreased when it is left again. This allows debuggers to track tricky cases like the same modifier being used twice or multiple placeholder statements being used in a single modifier.

In order to compress these source mappings especially for bytecode, the following rules are used:

- If a field is empty, the value of the preceding element is used.

- If a : is missing, all following fields are considered empty.

This means the following source mappings represent the same information:

1:2:1;1:9:1;2:1:2;2:1:2;2:1:2

1:2:1;:9;2:1:2;;

Important to note is that when the verbatim builtin is used, the source mappings will be invalid: The builtin is considered
