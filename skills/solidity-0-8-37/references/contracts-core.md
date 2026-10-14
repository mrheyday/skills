# Contracts: creation, visibility, modifiers, transient storage, constant/immutable, custom layout, functions, events, custom errors (3.9.1–3.9.10)

> Source: Solidity documentation, release 0.8.37-develop (Sep 10, 2026), https://docs.soliditylang.org/ — text reproduced from the official docs; code indentation was flattened by the export and is not normative.

## Contents

- 3.9 Contracts
  - 3.9.1 Creating Contracts
  - 3.9.2 Visibility and Getters
  - 3.9.3 Function Modifiers
  - 3.9.4 Transient Storage
  - 3.9.5 Composability of Smart Contracts and the Caveats of Transient Storage
  - 3.9.6 Constant and Immutable State Variables
  - 3.9.7 Custom Storage Layout
  - 3.9.8 Functions
  - 3.9.9 Events
  - 3.9.10 Custom Errors

---

# 3.9 Contracts

Contracts in Solidity are similar to classes in object-oriented languages. They contain persistent data in state variables, and functions that can modify these variables. Calling a function on a different contract (instance) will performan EVM function call and thus switch the context such that state variables in the calling contract are inaccessible. A contract and its functions need to be called for anything to happen. There is no “cron” concept in Ethereum to call a function at a particular event automatically.

## 3.9.1 Creating Contracts

Contracts can be created “from outside” via Ethereum transactions or from within Solidity contracts.

IDEs, such as Remix, make the creation process seamless using UI elements. (https://remix.ethereum.org/)

One way to create contracts programmatically on Ethereum is via the JavaScript API web3.js. It has a function called (https://github.com/web3/web3.js)

web3.eth.Contract to facilitate contract creation. (https://web3js.readthedocs.io/en/1.0/web3-eth-contract.html#new-contract)

When a contract is created, its constructor (a function declared with the constructor keyword) is executed once.

A constructor is optional. Only one constructor is allowed, which means overloading is not supported.

After the constructor has executed, the final code of the contract is stored on the blockchain. This code includes all public and external functions and all functions that are reachable from there through function calls. The deployed code does not include the constructor code or internal functions only called from the constructor.

Internally, constructor arguments are passed ABI encoded after the code of the contract itself, but you do not have to care about this if you use web3.js.

If a contract wants to create another contract, the source code (and the binary) of the created contract has to be known to the creator. This means that cyclic creation dependencies are impossible.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.22 <0.9.0;
contract OwnedToken {
// `TokenCreator` is a contract type that is defined below.
// It is fine to reference it as long as it is not used
// to create a new contract.
TokenCreator creator;
address owner;
bytes32 name;
// This is the constructor which registers the
// creator and the assigned name.
constructor(bytes32 name_) {
// State variables are accessed via their name
// and not via e.g. `this.owner`. Functions can
// be accessed directly or through `this.f`,
// but the latter provides an external view
// to the function. Especially in the constructor,
// you should not access functions externally,
// because the function does not exist yet.
// See the next section for details.
owner = msg.sender;
// We perform an explicit type conversion from `address`
// to `TokenCreator` and assume that the type of
// the calling contract is `TokenCreator`, there is
// no real way to verify that.
// This does not create a new contract.
creator = TokenCreator(msg.sender);
name = name_;
}
function changeName(bytes32 newName) public {
// Only the creator can alter the name.
// We compare the contract based on its
// address which can be retrieved by
// explicit conversion to address.
if (msg.sender == address(creator))
name = newName;
}
function transfer(address newOwner) public {
// Only the current owner can transfer the token.
if (msg.sender != owner) return;
// We ask the creator contract if the transfer
// should proceed by using a function of the
// `TokenCreator` contract defined below. If
// the call fails (e.g. due to out-of-gas),
// the execution also fails here.
if (creator.isTokenTransferOK(owner, newOwner))
owner = newOwner;
}
}
contract TokenCreator {
function createToken(bytes32 name)
public
returns (OwnedToken tokenAddress)
{
// Create a new `Token` contract and return its address.
// From the JavaScript side, the return type
// of this function is `address`, as this is
// the closest type available in the ABI.
return new OwnedToken(name);
}
function changeName(OwnedToken tokenAddress, bytes32 name) public {
// Again, the external type of `tokenAddress` is
// simply `address`.
tokenAddress.changeName(name);
}
// Perform checks to determine if transferring a token to the
// `OwnedToken` contract should proceed
function isTokenTransferOK(address currentOwner, address newOwner)
public
pure
returns (bool ok)
{
// Check an arbitrary condition to see if transfer should proceed
return keccak256(abi.encodePacked(currentOwner, newOwner))[0] == 0x7f;
}
}
```

## 3.9.2 Visibility and Getters

### State Variable Visibility

Public state variables differ from internal ones only in that the compiler automatically generates getter functions for them, which allows other contracts to read their values. When used within the same contract, the external access (e.g. this.x) invokes the getter while internal access (e.g. x) gets the variable value directly from storage. Setter functions are not generated so other contracts cannot directly modify their values.

Internal state variables can only be accessed from within the contract they are defined in and in derived contracts. They cannot be accessed externally. This is the default visibility level for state variables.

Private state variables are like internal ones but they are not visible in derived contracts.

### public

### internal

### private

**Warning:**

Making something private or internal only prevents other contracts from reading or modifying the information, but it will still be visible to the whole world outside of the blockchain.

### Function Visibility

Solidity knows two kinds of function calls: external ones that do create an actual EVM message call and internal ones that do not. Furthermore, internal functions can be made inaccessible to derived contracts. This gives rise to four types of visibility for functions.

External functions are part of the contract interface, which means they can be called from other contracts and via transactions. An external function f cannot be called internally (i.e. f() does not work, but this.f() works).

Public functions are part of the contract interface and can be either called internally or via message calls.

Internal functions can only be accessed from within the current contract or contracts deriving from it. They cannot be accessed externally. Since they are not exposed to the outside through the contract’s ABI, they can take parameters of internal types like mappings or storage references.

Private functions are like internal ones but they are not visible in derived contracts.

### external

### public

### internal

### private

**Warning:**

Making something private or internal only prevents other contracts from reading or modifying the information, but it will still be visible to the whole world outside of the blockchain.

The visibility specifier is given after the type for state variables and between parameter list and return parameter list for functions.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.16 <0.9.0;
contract C {
function f(uint a) private pure returns (uint b) { return a + 1; }
function setData(uint a) internal { data = a; }
uint public data;
}
```

In the following example, D, can call c.getData() to retrieve the value of data in state storage, but is not able to call f. Contract E is derived from C and, thus, can call compute.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.16 <0.9.0;
contract C {
uint private data;
function f(uint a) private pure returns(uint b) { return a + 1; }
function setData(uint a) public { data = a; }
function getData() public view returns(uint) { return data; }
function compute(uint a, uint b) internal pure returns (uint) { return a + b; }
}
// This will not compile
contract D {
function readData() public {
C c = new C();
uint local = c.f(7); // error: member `f` is not visible
c.setData(3);
local = c.getData();
local = c.compute(3, 5); // error: member `compute` is not visible
}
}
contract E is C {
function g() public {
C c = new C();
uint val = compute(3, 5); // access to internal member (from derived to parent contract)
}
}
```

### Getter Functions

The compiler automatically creates getter functions for all public state variables. For the contract given below, the compiler will generate a function called data that does not take any arguments and returns a uint, the value of the state variable data. State variables can be initialized when they are declared.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.16 <0.9.0;
contract C {
uint public data = 42;
}
contract Caller {
C c = new C();
function f() public view returns (uint) {
return c.data();
}
}
```

The getter functions have external visibility. If the symbol is accessed internally (i.e. without this.), it evaluates to a state variable. If it is accessed externally (i.e. with this.), it evaluates to a function.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.0 <0.9.0;
contract C {
uint public data;
function x() public returns (uint) {
data = 3; // internal access
return this.data(); // external access
}
}
```

Ifyou have a public state variable ofarray type, then you can only retrieve single elements ofthe array via the generated getter function. This mechanism exists to avoid high gas costs when returning an entire array. You can use arguments to specify which individual element to return, for example myArray(0). If you want to return an entire array in one call, then you need to write a function, for example:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.16 <0.9.0;
contract arrayExample {
// public state variable
uint[] public myArray;
// Getter function generated by the compiler
/*
function myArray(uint i) public view returns (uint) {
return myArray[i];
}
*/
// function that returns entire array
function getArray() public view returns (uint[] memory) {
return myArray;
}
}
```

Now you can use getArray() to retrieve the entire array, instead of myArray(i), which returns a single element per call.

The next example is more complex:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.0 <0.9.0;
contract Complex {
struct Data {
uint a;
bytes3 b;
mapping(uint => uint) map;
uint[3] c;
uint[] d;
bytes e;
}
mapping(uint => mapping(bool => Data[])) public data;
}
```

It generates a function of the following form. The mapping and arrays (with the exception of byte arrays) in the struct are omitted because there is no good way to select individual struct members or provide a key for the mapping:

```
function data(uint arg1, bool arg2, uint arg3)
public
returns (uint a, bytes3 b, bytes memory e)
{
a = data[arg1][arg2][arg3].a;
b = data[arg1][arg2][arg3].b;
e = data[arg1][arg2][arg3].e;
}
```

## 3.9.3 Function Modifiers

Modifiers can be used to change the behavior of functions in a declarative way. For example, you can use a modifier to automatically check a condition prior to executing the function.

Modifiers are inheritable properties of contracts and may be overridden by derived contracts, but only if they are marked virtual. For details, please see Modifier Overriding.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.1 <0.9.0;
contract owned {
constructor() { owner = payable(msg.sender); }
address payable owner;
// This contract only defines a modifier but does not use
// it: it will be used in derived contracts.
// The function body is inserted where the special symbol
// `_;` in the definition of a modifier appears.
// This means that if the owner calls this function, the
// function is executed and otherwise, an exception is
// thrown.
modifier onlyOwner {
require(
msg.sender == owner,
"Only owner can call this function."
);
_;
}
}
contract priced {
// Modifiers can receive arguments:
modifier costs(uint price) {
if (msg.value >= price) {
_;
}
}
}
contract Register is priced, owned {
mapping(address => bool) registeredAddresses;
uint price;
constructor(uint initialPrice) { price = initialPrice; }
// It is important to also provide the
// `payable` keyword here, otherwise the function will
// automatically reject all Ether sent to it.
function register() public payable costs(price) {
registeredAddresses[msg.sender] = true;
}
// This contract inherits the `onlyOwner` modifier from
// the `owned` contract. As a result, calls to `changePrice` will
// only take effect if they are made by the stored owner.
function changePrice(uint price_) public onlyOwner {
price = price_;
}
}
contract Mutex {
bool locked;
modifier noReentrancy() {
require(
!locked,
"Reentrant call."
);
locked = true;
_;
locked = false;
}
/// This function is protected by a mutex, which means that
/// reentrant calls from within `msg.sender.call` cannot call `f` again.
/// The `return 7` statement assigns 7 to the return value but still
/// executes the statement `locked = false` in the modifier.
function f() public noReentrancy returns (uint) {
(bool success,) = msg.sender.call("");
require(success);
return 7;
}
}
```

If you want to access a modifier m defined in a contract C, you can use C.m to reference it without virtual lookup. It is only possible to use modifiers defined in the current contract or its base contracts. Modifiers can also be defined in libraries but their use is limited to functions of the same library.

Multiple modifiers are applied to a function by specifying them in a whitespace-separated list and are evaluated in the order presented.

Modifiers cannot implicitly access or change the arguments and return values of functions they modify. Their values can only be passed to them explicitly at the point of invocation.

In function modifiers, it is necessary to specify when you want the function to which the modifier is applied to be run. The placeholder statement (denoted by a single underscore character _) is used to denote where the body of the function being modified should be inserted. Note that the placeholder operator is different from using underscores as leading or trailing characters in variable names, which is a stylistic choice.

Explicit returns from a modifier or function body only leave the current modifier or function body. Return variables are assigned and control flow continues after the _ in the preceding modifier.

```
. Warning
In an earlier version of Solidity, return statements in functions having modifiers behaved differently.
```

An explicit return from a modifier with return; does not affect the values returned by the function. The modifier can, however, choose not to execute the function body at all and in that case the return variables are set to their default values just as if the function had an empty body.

The _ symbol can appear in the modifier multiple times. Each occurrence is replaced with the function body, and the function returns the return value of the final occurrence.

Arbitrary expressions are allowed for modifier arguments and in this context, all symbols visible from the function are visible in the modifier. Symbols introduced in the modifier are not visible in the function (as they might change by overriding).

## 3.9.4 Transient Storage

Transient storage is another data location besides memory, storage, calldata (and return-data and code) which was introduced alongside its respective opcodes TSTORE and TLOAD by EIP-1153. This new data location behaves as a key-value store similar to storage with the main difference being that data in transient storage is not permanent, but is scoped to the current transaction only, after which it will be reset to zero. Since the content of transient storage has very limited lifetime and size, it does not need to be stored permanently as a part of state and the associated gas costs are much lower than in case of storage. EVM version cancun or newer is required for transient storage to be available. (https://eips.ethereum.org/EIPS/eip-1153)

Transient storage variables cannot be initialized in place, i.e., they cannot be assigned to upon declaration, since the value would be cleared at the end of the creation transaction, rendering the initialization ineffective. Transient variables will be default value initialized depending on their underlying type. constant and immutable variables conflict with transient storage, since their values are either inlined or directly stored in code.

Transient storage variables have completely independent address space from storage, so that the order of transient state variables does not affect the layout of storage state variables and vice-versa. They do need distinct names though because all state variables share the same namespace. It is also important to note that the values in transient storage are packed in the same fashion as those in persistent storage. See Storage Layout for more information.

Besides that, transient variables can have visibility as well and public ones will have a getter function generated automatically as usual.

Note that, currently, such use of transient as a data location is only allowed for value type state variable declarations. Reference types, such as arrays, mappings and structs, as well as local or parameter variables are not yet supported.

An expected canonical use case for transient storage is cheaper reentrancy locks, which can be readily implemented with the opcodes as showcased next.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.28;
contract Generosity {
mapping(address => bool) sentGifts;
bool transient locked;
modifier nonReentrant {
require(!locked, "Reentrancy attempt");
locked = true;
_;
// Unlocks the guard, making the pattern composable.
// After the function exits, it can be called again, even in the same transaction.
locked = false;
}
function claimGift() nonReentrant public {
require(address(this).balance >= 1 ether);
require(!sentGifts[msg.sender]);
(bool success, ) = msg.sender.call{value: 1 ether}("");
require(success);
// In a reentrant function, doing this last would open up the vulnerability
sentGifts[msg.sender] = true;
}
}
```

Transient storage is private to the contract that owns it, in the same way as persistent storage. Only owning contract frames may access their transient storage, and when they do, all the frames access the same transient store.

Transient storage is part of the EVM state and is subject to the same mutability enforcements as persistent storage. As such, any read access to it is not pure and writing access is not view.

If the TSTORE opcode is called within the context of a STATICCALL, it will result in an exception instead of performing the modification. TLOAD is allowed within the context of a STATICCALL.

When transient storage is used in the context of DELEGATECALL or CALLCODE, then the owning contract of the transient storage is the contract that issued DELEGATECALL or CALLCODE instruction (the caller) as with persistent storage. When transient storage is used in the context of CALL or STATICCALL, then the owning contract of the transient storage is the contract that is the target of the CALL or STATICCALL instruction (the callee).

**Note:**

In the case of DELEGATECALL, since references to transient storage variables are currently not supported, it is not possible to pass those into library calls. In libraries, access to transient storage is only possible using inline assembly.

If a frame reverts, all writes to transient storage that took place between entry to the frame and the return are reverted, including those that took place in inner calls. The caller of an external call may employ a try ... catch block to prevent reverts bubbling up from the inner calls.

## 3.9.5 Composability of Smart Contracts and the Caveats of Transient Storage

Given the caveats mentioned in the specification of EIP-1153, in order to preserve the composability of your smart contract, utmost care is recommended for more advanced use cases of transient storage.

For smart contracts, composability is a very important design principle to achieve self-contained behaviour, such that multiple calls into individual smart contracts can be composed to more complex applications. So far the EVM largely guaranteed composable behaviour, since multiple calls into a smart contract within a complex transaction are virtually indistinguishable from multiple calls to the contract stretched over several transactions. However, transient storage allows a violation of this principle, and incorrect use may lead to complex bugs that only surface when used across several calls.

Let’s illustrate the problem with a simple example:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.28;
contract MulService {
uint transient multiplier;
function setMultiplier(uint mul) external {
multiplier = mul;
}
function multiply(uint value) external view returns (uint) {
return value * multiplier;
}
}
```

and a sequence of external calls:

```
setMultiplier(42);
multiply(1);
multiply(2);
```

If the example used memory or storage to store the multiplier, it would be fully composable. It would not matter whether you split the sequence into separate transactions or grouped them in some way. You would always get the same result: after multiplier is set to 42, the subsequent calls would return 42 and 84 respectively. This enables use cases such as batching calls from multiple transactions together to reduce gas costs. Transient storage potentially breaks such use cases since composability can no longer be taken for granted. In the example, if the calls are not executed in the same transaction, then multiplier is reset and the next calls to function multiply would always return 0.

As another example, since transient storage is constructed as a relatively cheap key-value store, a smart contract author may be tempted to use transient storage as a replacement for in-memory mappings without keeping track of the modified keys in the mapping and thereby without clearing the mapping at the end of the call. This, however, can easily lead to unexpected behaviour in complex transactions, in which values set by a previous call into the contract within the same transaction remain.

The use of transient storage for reentrancy locks that are cleared at the end of the call frame into the contract, is safe. However, be sure to resist the temptation to save the 100 gas used for resetting the reentrancy lock, since failing to do so, will restrict your contract to only one call within a transaction, preventing its use in complex composed transactions, which have been a cornerstone for complex applications on chain.

It is recommend to generally always clear transient storage completely at the end of a call into your smart contract to avoid these kinds of issues and to simplify the analysis of the behaviour of your contract within complex transactions. Check the Security Considerations section of EIP-1153 for further details. (https://eips.ethereum.org/EIPS/eip-1153#security-considerations)

## 3.9.6 Constant and Immutable State Variables

State variables can be declared as constant or immutable. In both cases, the variables cannot be modified after the contract has been constructed. For constant variables, the value has to be fixed at compile-time, while for immutable, it can still be assigned at construction time.

It is also possible to define constant variables at the file level.

Every occurrence of such a variable in the source is replaced by its underlying value and the compiler does not reserve a storage slot for it. It cannot be assigned a slot in transient storage using the transient keyword either.

Compared to regular state variables, the gas costs of constant and immutable variables are much lower. For a constant variable, the expression assigned to it is copied to all the places where it is accessed and also re-evaluated each time.

This allows for local optimizations. Immutable variables are evaluated once at construction time and their value is copied to all the places in the code where they are accessed. For these values, 32 bytes are reserved, even if they would fit in fewer bytes. Due to this, constant values can sometimes be cheaper than immutable values.

Not all types for constants and immutables are implemented at this time. The only supported types are strings (only for constants) and value types.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.21;
uint constant X = 32**22 + 8;
contract C {
string constant TEXT = "abc";
bytes32 constant MY_HASH = keccak256("abc");
uint immutable decimals = 18;
uint immutable maxBalance;
address immutable owner = msg.sender;
constructor(uint decimals_, address ref) {
if (decimals_ != 0)
// Immutables are only immutable when deployed.
// At construction time they can be assigned to any number of times.
decimals = decimals_;
// Assignments to immutables can even access the environment.
maxBalance = ref.balance;
}
function isBalanceTooHigh(address other) public view returns (bool) {
return other.balance > maxBalance;
}
}
```

### Constant

For constant variables, the value has to be a constant at compile time and it has to be assigned where the variable is declared. Any expression that accesses storage, blockchain data (e.g. block.timestamp, address(this).balance or block.number) or execution data (msg.value or gasleft()) or makes calls to external contracts is disallowed. Expressions that might have a side-effect on memory allocation are allowed, but those that might have a side-effect on other memory objects are not. The built-in functions keccak256, sha256, ripemd160, ecrecover, addmod and mulmod are allowed (even though, with the exception of keccak256, they do call external contracts).

The reason behind allowing side-effects on the memory allocator is that it should be possible to construct complex objects like e.g. lookup-tables. This feature is not yet fully usable.

### Immutable

Variables declared as immutable are a bit less restricted than those declared as constant: Immutable variables can be assigned a value at construction time. The value can be changed at any time before deployment and then it becomes permanent.

One additional restriction is that immutables can only be assigned to inside expressions for which there is no possibility of being executed after creation. This excludes all modifier definitions and functions other than constructors.

There are no restrictions on reading immutable variables. The read is even allowed to happen before the variable is written to for the first time because variables in Solidity always have a well-defined initial value. For this reason it is also allowed to never explicitly assign a value to an immutable.

**Warning:**

When accessing immutables at construction time, please keep the initialization order in mind. Even if you provide an explicit initializer, some expressions may end up being evaluated before that initializer, especially when they are at a different level in inheritance hierarchy.

**Note:**

Before Solidity 0.8.21 initialization ofimmutable variables was more restrictive. Such variables had to be initialized exactly once at construction time and could not be read before then.

The contract creation code generated by the compiler will modify the contract’s runtime code before it is returned by replacing all references to immutables with the values assigned to them. This is important if you are comparing the runtime code generated by the compiler with the one actually stored in the blockchain. The compiler outputs where these immutables are located in the deployed bytecode in the immutableReferences field of the compiler JSON standard output.

## 3.9.7 Custom Storage Layout

A contract can define an arbitrary location for its storage using the layout specifier. The contract’s state variables, including those inherited from base contracts, start from the specified base slot instead of the default slot zero.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.29;
contract C layout at 0xAAAA + 0x11 {
uint[3] x; // Occupies slots 0xAABB..0xAABD
}
```

As the above example shows, the specifier uses the layout at <base-slot-expression> syntax and is located in the header of a contract definition.

The layout specifier can be placed either before or after the inheritance specifier, and can appear at most once. The base-slot-expression must be an integer literal expression that can be evaluated at compilation time and yields a value in the range of uint256. The use of constants initialized using such expressions and the built-in function erc7201 is also allowed.

A custom layout cannot make contract’s storage “wrap around”. If the selected base slot would push the static variables past the end of storage, the compiler will issue an error. Note that the data areas of dynamic arrays and mappings are not affected by this check because their layout is not linear. Regardless of the base slot used, their locations are calculated in a way that always puts them within the range of uint256 and their sizes are not known at compilation time.

While there are no other limits placed on the base slot, it is recommended to avoid locations that are too close to the end of the address space. Leaving too little space may complicate contract upgrades or cause problems for contracts that store additional values past their allocated space using inline assembly.

The storage layout can only be specified for the topmost contract of an inheritance tree, and affects locations of all the storage variables in all the contracts in that tree. Variables are laid out according to the order of their definitions and the positions of their contracts in the linearized inheritance hierarchy and a custom base slot preserves their relative positions, shifting them all by the same amount.

The storage layout cannot be specified for abstract contracts, interfaces and libraries. Also, it is important to note that it does not affect transient state variables.

For details about storage layout and the effect of the layout specifier on it see layout ofstorage variables.

**Warning:**

The identifiers layout and at are not yet reserved as keywords in the language. It is strongly recommended to avoid using them since they will become reserved in a future breaking release.

## 3.9.8 Functions

Functions can be defined inside and outside of contracts.

Functions outside of a contract, also called “free functions”, always have implicit internal visibility. Their code is included in all contracts that call them, similar to internal library functions.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.1 <0.9.0;
function sum(uint[] memory arr) pure returns (uint s) {
for (uint i = 0; i < arr.length; i++)
s += arr[i];
}
contract ArrayExample {
bool found;
function f(uint[] memory arr) public {
// This calls the free function internally.
// The compiler will add its code to the contract.
uint s = sum(arr);
require(s >= 10);
found = true;
}
}
```

**Note:**

Functions defined outside a contract are still always executed in the context of a contract. They still can call other contracts, send them Ether and destroy the contract that called them, among other things. The main difference to functions defined inside a contract is that free functions do not have direct access to the variable this, storage variables and functions not in their scope.

### Function Parameters and Return Variables

Functions take typed parameters as input and may, unlike in many other languages, also return an arbitrary number of values as output.

### Function Parameters

Function parameters are declared the same way as variables, and the name of unused parameters can be omitted.

For example, if you want your contract to accept one kind of external call with two integers, you would use something like the following:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.16 <0.9.0;
contract Simple {
uint sum;
function taker(uint a, uint b) public {
sum = a + b;
}
}
```

Function parameters can be used as any other local variable and they can also be assigned to.

### Return Variables

Function return variables are declared with the same syntax after the returns keyword.

For example, suppose you want to return two results: the sum and the product of two integers passed as function parameters, then you use something like:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.16 <0.9.0;
contract Simple {
function arithmetic(uint a, uint b)
public
pure
returns (uint sum, uint product)
{
sum = a + b;
product = a * b;
}
}
```

The names of return variables can be omitted. Return variables can be used as any other local variable and they are initialized with their default value and have that value until they are (re-)assigned.

You can either explicitly assign to return variables and then leave the function as above, or you can provide return values (either a single or multiple ones) directly with the return statement:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.16 <0.9.0;
contract Simple {
function arithmetic(uint a, uint b)
public
pure
returns (uint sum, uint product)
{
return (a + b, a * b);
}
}
```

If you use an early return to leave a function that has return variables, you must provide return values together with the return statement.

**Note:**

You cannot return some types from non-internal functions. This includes the types listed below and any composite types that recursively contain them:

- mappings,

- internal function types,

- reference types with location set to storage,

- multi-dimensional arrays (applies only to ABI coder v1),

- structs (applies only to ABI coder v1).

This restriction does not apply to library functions because of their different internal ABI.

### Returning Multiple Values

When a function has multiple return types, the statement return (v0, v1, ..., vn) can be used to return multiple values. The number of components must be the same as the number of return variables and their types have to match, potentially after an implicit conversion.

### State Mutability

### View Functions

Functions can be declared view in which case they promise not to modify the state.

**Note:**

If the compiler’s EVM target is Byzantium or newer (default) the opcode STATICCALL is used when view functions are called, which enforces the state to stay unmodified as part of the EVM execution. For library view functions DELEGATECALL is used, because there is no combined DELEGATECALL and STATICCALL. This means library view functions do not have run-time checks that prevent state modifications. This should not impact security negatively because library code is usually known at compile-time and the static checker performs compile-time checks.

The following statements are considered modifying the state:

- 1. Writing to state variables (storage and transient storage).

- 2. Emitting events.

- 3. Creating other contracts.

- 4. Using selfdestruct.

- 5. Sending Ether via calls.

- 6. Calling any function not marked view or pure.

- 7. Using low-level calls.

- 8. Using inline assembly that contains certain opcodes.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.5.0 <0.9.0;
contract C {
function f(uint a, uint b) public view returns (uint) {
return a * (b + 42) + block.timestamp;
}
}
```

ò Note constant on functions used to be an alias to view, but this was dropped in version 0.5.0.

ò Note

Getter methods are automatically marked view.

**Note:**

Prior to version 0.5.0, the compiler did not use the STATICCALL opcode for view functions. This enabled state modifications in view functions through the use of invalid explicit type conversions. By using STATICCALL for view functions, modifications to the state are prevented on the level of the EVM.

### Pure Functions

Functions can be declared pure in which case they promise not to read from or modify the state. In particular, it should be possible to evaluate a pure function at compile-time given only its inputs and msg.data, but without any knowledge of the current blockchain state. This means that reading from immutable variables can be a non-pure operation.

**Note:**

If the compiler’s EVM target is Byzantium or newer (default) the opcode STATICCALL is used, which does not guarantee that the state is not read, but at least that it is not modified.

In addition to the list of state modifying statements explained above, the following are considered reading from the state:

- 1. Reading from state variables (storage and transient storage).

- 2. Accessing address(this).balance or <address>.balance.

- 3. Accessing any of the members of block, tx, msg (with the exception of msg.sig and msg.data).

- 4. Calling any function not marked pure.

- 5. Using inline assembly that contains certain opcodes.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.5.0 <0.9.0;
contract C {
function f(uint a, uint b) public pure returns (uint) {
return a * (b + 42);
}
}
```

Pure functions are able to use the revert() and require() functions to revert potential state changes when an error occurs.

Reverting a state change is not considered a “state modification”, as only changes to the state made previously in code that did not have the view or pure restriction are reverted and that code has the option to catch the revert and not pass it on.

This behavior is also in line with the STATICCALL opcode.

**Warning:**

It is not possible to prevent functions from reading the state at the level of the EVM, it is only possible to prevent them from writing to the state (i.e. only view can be enforced at the EVM level, pure can not).

**Note:**

Prior to version 0.5.0, the compiler did not use the STATICCALL opcode for pure functions. This enabled state modifications in pure functions through the use of invalid explicit type conversions. By using STATICCALL for pure functions, modifications to the state are prevented on the level of the EVM.

**Note:**

Prior to version 0.4.17 the compiler did not enforce that pure is not reading the state. It is a compile-time type check, which can be circumvented by doing invalid explicit conversions between contract types, because the compiler can verify that the type of the contract does not do state-changing operations, but it cannot check that the contract that will be called at runtime is actually of that type.

### Special Functions

### Receive Ether Function

A contract can have at most one receive function, declared using receive() external payable { ... }

out the function keyword). This function cannot have arguments, cannot return anything and must have external visibility and payable state mutability. It can be virtual, can override and can have modifiers.

The receive function is executed on a call to the contract with empty calldata. This is the function that is executed on plain Ether transfers (e.g. via .send() or .transfer()). If no such function exists, but a payable fallback function exists, the fallback function will be called on a plain Ether transfer. If neither a receive Ether nor a payable fallback function is present, the contract cannot receive Ether through a transaction that does not represent a payable function call and throws an exception.

In the worst case, the receive function can only rely on 2300 gas being available (for example when send or transfer is used), leaving little room to perform other operations except basic logging. The following operations will consume (with-

more gas than the 2300 gas stipend:

- Writing to storage

- Creating a contract

- Calling an external function which consumes a large amount of gas

- Sending Ether

**Warning:**

send() and transfer() are deprecated and scheduled for removal. See the section on send and transfer for more information.

**Warning:**

When Ether is sent directly to a contract (without a function call, i.e. sender uses send or transfer) but the receiving contract does not define a receive Ether function or a payable fallback function, an exception will be thrown, sending back the Ether (this was different before Solidity v0.4.0). If you want your contract to receive Ether, you have to implement a receive Ether function (using payable fallback functions for receiving Ether is not recommended, since the fallback is invoked and would not fail for interface confusions on the part of the sender).

**Warning:**

A contract without a receive Ether function can receive Ether as a recipient of a coinbase transaction (aka miner block reward) or as a destination of a selfdestruct.

A contract cannot react to such Ether transfers and thus also cannot reject them. This is a design choice of the EVM and Solidity cannot work around it.

It also means that address(this).balance can be higher than the sum of some manual accounting implemented in a contract (i.e. having a counter updated in the receive Ether function).

Below you can see an example of a Sink contract that uses function receive.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.6.0 <0.9.0;
// This contract keeps all Ether sent to it with no way
// to get it back.
contract Sink {
event Received(address, uint);
receive() external payable {
emit Received(msg.sender, msg.value);
}
}
```

### Fallback Function

A contract can have at most one fallback function, declared using either fallback () external [payable] or fallback (bytes calldata input) external [payable] returns (bytes memory output) (both without the function keyword). This function must have external visibility. A fallback function can be virtual, can override and can have modifiers.

The fallback function is executed on a call to the contract if none of the other functions match the given function signature, or if no data was supplied at all and there is no receive Ether function. The fallback function always receives data, but in order to also receive Ether it must be marked payable.

If the version with parameters is used, input will contain the full data sent to the contract (equal to msg.data) and can return data in output. The returned data will not be ABI-encoded. Instead it will be returned without modifications (not even padding).

In the worst case, if a payable fallback function is also used in place of a receive function, it can only rely on 2300 gas being available (see receive Ether function for a brief description of the implications of this).

Like any function, the fallback function can execute complex operations as long as there is enough gas passed on to it.

**Warning:**

A payable fallback function is also executed for plain Ether transfers, if no receive Ether function is present. It is recommended to always define a receive Ether function as well, if you define a payable fallback function to distinguish Ether transfers from interface confusions.

**Note:**

If you want to decode the input data, you can check the first four bytes for the function selector and then you can use abi.decode together with the array slice syntax to decode ABI-encoded data: (c, d) = abi. decode(input[4:], (uint256, uint256)); Note that this should only be used as a last resort and proper functions should be used instead.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.6.2 <0.9.0;
contract Test {
uint x;
// This function is called for all messages sent to
// this contract (there is no other function).
// Sending Ether to this contract will cause an exception,
// because the fallback function does not have the `payable`
// modifier.
fallback() external { x = 1; }
}
contract TestPayable {
uint x;
uint y;
// This function is called for all messages sent to
// this contract, except plain Ether transfers
// (there is no other function except the receive function).
// Any call with non-empty calldata to this contract will execute
// the fallback function (even if Ether is sent along with the call).
fallback() external payable { x = 1; y = msg.value; }
// This function is called for plain Ether transfers, i.e.
// for every call with empty calldata.
receive() external payable { x = 2; y = msg.value; }
}
contract Caller {
function callTest(Test test) public returns (bool) {
(bool success,) = address(test).call(abi.encodeWithSignature( "nonExistingFunction()"));
require(success);
// results in test.x becoming == 1.
// address(test) will not allow to call ``send`` directly, since ``test`` has no payable
// fallback function.
// It has to be converted to the ``address payable`` type to even allow calling ``send`` on it.
address payable testPayable = payable(address(test));
// If someone sends Ether to that contract,
// the transfer will fail, i.e. this returns false here.
// This will report a warning (deprecation)
return testPayable.send(2 ether);
}
function callTestPayable(TestPayable test) public returns (bool) {
(bool success,) = address(test).call(abi.encodeWithSignature( "nonExistingFunction()"));
require(success);
// results in test.x becoming == 1 and test.y becoming 0.
(success,) = address(test).call{value: 1}(abi.encodeWithSignature( "nonExistingFunction()"));
require(success);
// results in test.x becoming == 1 and test.y becoming 1.
// If someone sends Ether to that contract, the receive function in TestPayable will be called.
// Since that function writes to storage, it takes more gas than is availablewith a
// simple ``send`` or ``transfer``. Because of that, we have to use a low-level call.
(success,) = address(test).call{value: 2 ether}("");
require(success);
// results in test.x becoming == 2 and test.y becoming 2 ether.
return true;
}
}
```

### Function Overloading

A contract can have multiple functions of the same name but with different parameter types. This process is called “overloading” and also applies to inherited functions. The following example shows overloading of the function f in the scope of contract A.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.16 <0.9.0;
contract A {
function f(uint value) public pure returns (uint out) {
out = value;
}
function f(uint value, bool really) public pure returns (uint out) {
if (really)
out = value;
}
}
```

Overloaded functions are also present in the external interface. It is an error if two externally visible functions differ by their Solidity types but not by their external types.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.16 <0.9.0;
// This will not compile
contract A {
function f(B value) public pure returns (B out) {
out = value;
}
function f(address value) public pure returns (address out) {
out = value;
}
}
contract B {
}
```

Both f function overloads above end up accepting the address type for the ABI although they are considered different inside Solidity.

### Overload resolution and Argument matching

Overloaded functions are selected by matching the function declarations in the current scope to the arguments supplied in the function call. Functions are selected as overload candidates if all arguments can be implicitly converted to the expected types. If there is not exactly one candidate, resolution fails.

ò Note

Return parameters are not taken into account for overload resolution.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.16 <0.9.0;
contract A {
function f(uint8 val) public pure returns (uint8 out) {
out = val;
}
function f(uint256 val) public pure returns (uint256 out) {
out = val;
}
}
```

Calling f(50) would create a type error since 50 can be implicitly converted both to uint8 and uint256 types. On another hand f(256) would resolve to f(uint256) overload as 256 cannot be implicitly converted to uint8.

## 3.9.9 Events

Solidity events give an abstraction on top of the EVM’s logging functionality. Applications can subscribe and listen to these events through the RPC interface of an Ethereum client.

Events can be defined at file level or as inheritable members of contracts (including interfaces and libraries). When you call them, they cause the arguments to be stored in the transaction’s log - a special data structure in the blockchain. These logs are associated with the address of the contract that emitted them, are incorporated into the blockchain, and stay there as long as a block is accessible (forever as of now, but this might change in the future). The Log and its event data are not accessible from within contracts (not even from the contract that created them).

It is possible to request a Merkle proof for logs, so if an external entity supplies a contract with such a proof, it can check that the log actually exists inside the blockchain. You have to supply block headers because the contract can only see the last 256 block hashes.

You can add the attribute indexed to up to three parameters which adds them to a special data structure known as “topics” instead of the data part of the log. A topic can only hold a single word (32 bytes) so if you use a reference type for an indexed argument, the Keccak-256 hash of the value is stored as a topic instead.

All parameters without the indexed attribute are ABI-encoded into the data part of the log.

Topics allow you to search for events, for example when filtering a sequence of blocks for certain events. You can also filter events by the address of the contract that emitted the event.

For example, the code below uses the web3.js subscribe("logs") method to filter logs that match a topic with a certain address value: (https://web3js.readthedocs.io/en/1.0/web3-eth-subscribe.html#subscribe-logs)

```
var options = {
fromBlock: 0,
address: web3.eth.defaultAccount,
topics: ["0x0000000000000000000000000000000000000000000000000000000000000000", null,null]
};
web3.eth.subscribe('logs', options, function (error, result) {
if (!error)
console.log(result);
})
.on("data", function (log) {
console.log(log);
})
.on("changed", function (log) {
});
```

The hash of the signature of the event is one of the topics, except if you declared the event with the anonymous specifier. This means that it is not possible to filter for specific anonymous events by name, you can only filter by the contract address. The advantage of anonymous events is that they are cheaper to deploy and call. It also allows you to declare four indexed arguments rather than three.

**Note:**

Since the transaction log only stores the event data and not the type, you have to know the type of the event, including which parameter is indexed and if the event is anonymous in order to correctly interpret the data. In particular, it is possible to “fake” the signature of another event using an anonymous event.

### Members of Events

- event.selector: For non-anonymous events, this is a bytes32 value containing the keccak256 hash of the event signature, as used in the default topic.

### Example

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.21 <0.9.0;
contract ClientReceipt {
event Deposit(
address indexed from,
bytes32 indexed id,
uint value
);
function deposit(bytes32 id) public payable {
// Events are emitted using `emit`, followed by
// the name of the event and the arguments
// (if any) in parentheses. Any such invocation
// (even deeply nested) can be detected from
// the JavaScript API by filtering for `Deposit`.
emit Deposit(msg.sender, id, msg.value);
}
}
```

The use in the JavaScript API is as follows:

```
var abi = /* abi as generated by the compiler */;
var ClientReceipt = web3.eth.contract(abi);
var clientReceipt = ClientReceipt.at("0x1234...ab67" /* address */);
var depositEvent = clientReceipt.Deposit();
// watch for changes
depositEvent.watch(function(error, result){
// result contains non-indexed arguments and topics
// given to the `Deposit` call.
if (!error)
console.log(result);
});
// Or pass a callback to start watching immediately
var depositEvent = clientReceipt.Deposit(function(error, result) {
if (!error)
console.log(result);
});
```

The output of the above looks like the following (trimmed):

```
{
"returnValues": {
"from": "0x1111...FFFFCCCC",
"id": "0x50...sd5adb20",
"value": "0x420042"
},
"raw": {
"data": "0x7f...91385",
"topics": ["0xfd4...b4ead7", "0x7f...1a91385"]
}
}
```

### Additional Resources for Understanding Events

- [• JavaScript documentation](https://github.com/web3/web3.js/blob/1.x/docs/web3-eth-contract.rst#events)

- [• Example usage of events](https://github.com/ethchange/smart-exchange/blob/master/lib/contracts/SmartExchange.sol)

- [• How to access them in js](https://github.com/ethchange/smart-exchange/blob/master/lib/exchange_transactions.js)

## 3.9.10 Custom Errors

Errors in Solidity provide a convenient and gas-efficient way to explain to the user why an operation failed. They can be defined inside and outside of contracts (including interfaces and libraries).

They have to be used together with the revert statement or the require function. In the case of revert statements, or require calls where the condition is evaluated to be false, all changes in the current call are reverted, and the error data passed back to the caller.

The example below shows custom error usage with the revert statement in function transferWithRevertError, as well as the newer approach with require in function transferWithRequireError.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.27;
/// Insufficient balance for transfer. Needed `required` but only
/// `available` available.
/// @param available balance available.
/// @param required requested amount to transfer.
error InsufficientBalance(uint256 available, uint256 required);
contract TestToken {
mapping(address => uint) balance;
function transferWithRevertError(address to, uint256 amount) public {
if (amount > balance[msg.sender])
revert InsufficientBalance({
available: balance[msg.sender],
required: amount
});
balance[msg.sender] -= amount;
balance[to] += amount;
}
function transferWithRequireError(address to, uint256 amount) public {
require(amount <= balance[msg.sender], InsufficientBalance(balance[msg.sender], amount));
balance[msg.sender] -= amount;
balance[to] += amount;
}
// ...
}
```

Another important detail to mention when it comes to using require with custom errors, is that memory allocation for the error-based revert reason will only happen in the reverting case, which, along with optimization of constants and string literals makes this about as gas-efficient as the if (!condition) revert CustomError(args) pattern.

Errors cannot be overloaded or overridden but are inherited. The same error can be defined in multiple places as long as the scopes are distinct. Instances of errors can only be created using revert statements, or as the second argument to require functions.

The error creates data that is then passed to the caller with the revert operation to either return to the off-chain component or catch it in a try/catch statement. Note that an error can only be caught when coming from an external call, reverts happening in internal calls or inside the same function cannot be caught.

If you do not provide any parameters, the error only needs four bytes of data and you can use NatSpec as above to further explain the reasons behind the error, which is not stored on chain. This makes this a very cheap and convenient error-reporting feature at the same time.

More specifically, an error instance is ABI-encoded in the same way as a function call to a function of the same name and types would be and then used as the return data in the revert opcode. This means that the data consists of a 4-byte selector followed by ABI-encoded data. The selector consists of the first four bytes of the keccak256-hash of the signature of the error type.

ò Note

It is possible for a contract to revert with different errors of the same name or even with errors defined in different places that are indistinguishable by the caller. For the outside, i.e. the ABI, only the name of the error is relevant, not the contract or file where it is defined.

The statement require(condition, "description"); would be equivalent to if (!condition) revert Error("description") if you could define error Error(string). Note, however, that Error is a built-in type and cannot be defined in user-supplied code.

Similarly, a failing assert or similar conditions will revert with an error of the built-in type Panic(uint256).

ò Note

Error data should only be used to give an indication of failure, but not as a means for control-flow. The reason is that the revert data of inner calls is propagated back through the chain of external calls by default. This means that an inner call can “forge” revert data that looks like it could have come from the contract that called it.

### Members of Errors

- error.selector: A bytes4 value containing the error selector.
