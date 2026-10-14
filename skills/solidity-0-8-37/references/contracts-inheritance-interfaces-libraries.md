# Contracts: inheritance, abstract contracts, interfaces, libraries, using for (3.9.11–3.9.15)

> Source: Solidity documentation, release 0.8.37-develop (Sep 10, 2026), https://docs.soliditylang.org/ — text reproduced from the official docs; code indentation was flattened by the export and is not normative.

## Contents

  - 3.9.11 Inheritance
  - 3.9.12 Abstract Contracts
  - 3.9.13 Interfaces
  - 3.9.14 Libraries
  - 3.9.15 Using For

---

## 3.9.11 Inheritance

Solidity supports multiple inheritance including polymorphism.

Polymorphism means that a function call (internal and external) always executes the function of the same name (and parameter types) in the most derived contract in the inheritance hierarchy. This has to be explicitly enabled on each function in the hierarchy using the virtual and override keywords. See Function Overriding for more details.

It is possible to call functions further up in the inheritance hierarchy internally by explicitly specifying the contract using ContractName.functionName() or using super.functionName() if you want to call the function one level higher up in the flattened inheritance hierarchy (see below).

When a contract inherits from other contracts, only a single contract is created on the blockchain, and the code from all the base contracts is compiled into the created contract. This means that all internal calls to functions of base contracts also just use internal function calls (super.f(..) will use JUMP and not a message call).

State variable shadowing is considered as an error. A derived contract can only declare a state variable x, if there is no visible state variable with the same name in any of its bases.

The general inheritance system is very similar to Python’s, especially concerning multiple inheritance, but there are also some differences.

Details are given in the following example.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.0 <0.9.0;
contract Owned {
address payable owner;
constructor() { owner = payable(msg.sender); }
}
// Use `is` to derive from another contract. Derived
// contracts can access all non-private members including
// internal functions and state variables. These cannot be
// accessed externally via `this`, though.
contract Emittable is Owned {
event Emitted();
// The keyword `virtual` means that the function can change
// its behavior in derived classes ("overriding").
function emitEvent() virtual public {
if (msg.sender == owner)
emit Emitted();
}
}
// These abstract contracts are only provided to make the
// interface known to the compiler. Note the function
// without body. If a contract does not implement all
// functions it can only be used as an interface.
abstract contract Config {
function lookup(uint id) public virtual returns (address adr);
}
abstract contract NameReg {
function register(bytes32 name) public virtual;
function unregister() public virtual;
}
// Multiple inheritance is possible. Note that `Owned` is
// also a base class of `Emittable`, yet there is only a single
// instance of `Owned` (as for virtual inheritance in C++).
contract Named is Owned, Emittable {
constructor(bytes32 name) {
Config config = Config(0xD5f9D8D94886E70b06E474c3fB14Fd43E2f23970);
NameReg(config.lookup(1)).register(name);
}
// Functions can be overridden by another function with the same name and
// the same number/types of inputs. If the overriding function has different
// types of output parameters, that causes an error.
// Both local and message-based function calls take these overrides
// into account.
// If you want the function to override, you need to use the
// `override` keyword. You need to specify the `virtual` keyword again
// if you want this function to be overridden again.
function emitEvent() public virtual override {
if (msg.sender == owner) {
Config config = Config(0xD5f9D8D94886E70b06E474c3fB14Fd43E2f23970);
NameReg(config.lookup(1)).unregister();
// It is still possible to call a specific
// overridden function.
Emittable.emitEvent();
}
}
}
// If a constructor takes an argument, it needs to be
// provided in the header or modifier-invocation-style at
// the constructor of the derived contract (see below).
contract PriceFeed is Owned, Emittable, Named("GoldFeed") {
uint info;
function updateInfo(uint newInfo) public {
if (msg.sender == owner) info = newInfo;
}
// Here, we only specify `override` and not `virtual`.
// This means that contracts deriving from `PriceFeed`
// cannot change the behavior of `emitEvent` anymore.
function emitEvent() public override(Emittable, Named) { Named.emitEvent(); }
function get() public view returns(uint r) { return info; }
}
```

Note that above, we call Emittable.emitEvent() to “forward” the emit event request. The way this is done is problematic, as seen in the following example:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.0 <0.9.0;
contract Owned {
address payable owner;
constructor() { owner = payable(msg.sender); }
}
contract Emittable is Owned {
event Emitted();
function emitEvent() virtual public {
if (msg.sender == owner) {
emit Emitted();
}
}
}
contract Base1 is Emittable {
event Base1Emitted();
function emitEvent() public virtual override {
/* Here, we emit an event to simulate some Base1 logic */
emit Base1Emitted();
Emittable.emitEvent();
}
}
contract Base2 is Emittable {
event Base2Emitted();
function emitEvent() public virtual override {
/* Here, we emit an event to simulate some Base2 logic */
emit Base2Emitted();
Emittable.emitEvent();
}
}
contract Final is Base1, Base2 {
event FinalEmitted();
function emitEvent() public override(Base1, Base2) {
/* Here, we emit an event to simulate some Final logic */
emit FinalEmitted();
Base2.emitEvent();
}
}
```

A call to Final.emitEvent() will call Base2.emitEvent because we specify it explicitly in the final override, but this function will bypass Base1.emitEvent, resulting in the following sequence of events: FinalEmitted -> Base2Emitted -> Emitted, instead of the expected sequence: FinalEmitted -> Base2Emitted -> Base1Emitted -> Emitted. The way around this is to use super:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.0 <0.9.0;
contract Owned {
address payable owner;
constructor() { owner = payable(msg.sender); }
}
contract Emittable is Owned {
event Emitted();
function emitEvent() virtual public {
if (msg.sender == owner) {
emit Emitted();
}
}
}
contract Base1 is Emittable {
event Base1Emitted();
function emitEvent() public virtual override {
/* Here, we emit an event to simulate some Base1 logic */
emit Base1Emitted();
super.emitEvent();
}
}
contract Base2 is Emittable {
event Base2Emitted();
function emitEvent() public virtual override {
/* Here, we emit an event to simulate some Base2 logic */
emit Base2Emitted();
super.emitEvent();
}
}
contract Final is Base1, Base2 {
event FinalEmitted();
function emitEvent() public override(Base1, Base2) {
/* Here, we emit an event to simulate some Final logic */
emit FinalEmitted();
super.emitEvent();
}
}
```

If Final calls a function of super, it does not simply call this function on one of its base contracts. Rather, it calls this function on the next base contract in the final inheritance graph, so it will call Base1.emitEvent() (note that the final inheritance sequence is – starting with the most derived contract: Final, Base2, Base1, Emittable, Owned). The actual function that is called when using super is not known in the context of the class where it is used, although its type is known. This is similar for ordinary virtual method lookup.

### Function Overriding

Base functions can be overridden by inheriting contracts to change their behavior if they are marked as virtual. The overriding function must then use the override keyword in the function header. The overriding function may only change the visibility of the overridden function from external to public. The mutability may be changed to a more strict one following the order: nonpayable can be overridden by view and pure. view can be overridden by pure. payable is an exception and cannot be changed to any other mutability.

The following example demonstrates changing mutability and visibility:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.0 <0.9.0;
contract Base
{
function foo() virtual external view {}
}
contract Middle is Base {}
contract Inherited is Middle
{
function foo() override public pure {}
}
```

For multiple inheritance, the most derived base contracts that define the same function must be specified explicitly after the override keyword. In other words, you have to specify all base contracts that define the same function and have not yet been overridden by another base contract (on some path through the inheritance graph). Additionally, if a contract inherits the same function from multiple (unrelated) bases, it has to explicitly override it:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.6.0 <0.9.0;
contract Base1
{
function foo() virtual public {}
}
contract Base2
{
function foo() virtual public {}
}
contract Inherited is Base1, Base2
{
// Derives from multiple bases defining foo(), so we must explicitly
// override it
function foo() public override(Base1, Base2) {}
}
```

An explicit override specifier is not required if the function is defined in a common base contract or if there is a unique function in a common base contract that already overrides all other functions.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.6.0 <0.9.0;
contract A { function f() public pure{} }
contract B is A {}
contract C is A {}
// No explicit override required
contract D is B, C {}
```

More formally, it is not required to override a function (directly or indirectly) inherited from multiple bases if there is a base contract that is part of all override paths for the signature, and (1) that base implements the function and no paths from the current contract to the base mentions a function with that signature or (2) that base does not implement the function and there is at most one mention of the function in all paths from the current contract to that base.

In this sense, an override path for a signature is a path through the inheritance graph that starts at the contract under consideration and ends at a contract mentioning a function with that signature that does not override.

If you do not mark a function that overrides as virtual, derived contracts can no longer change the behavior of that function.

ò Note

Functions with the private visibility cannot be virtual.

ò Note

Functions without implementation have to be marked virtual outside of interfaces. In interfaces, all functions are automatically considered virtual.

ò Note

Starting from Solidity 0.8.8, the override keyword is not required when overriding an interface function, except for the case where the function is defined in multiple bases.

Public state variables can override external functions if the parameter and return types of the function matches the getter function of the variable:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.6.0 <0.9.0;
contract A
{
function f() external view virtual returns(uint) { return 5; }
}
contract B is A
{
uint public override f;
}
```

While public state variables can override external functions, they themselves cannot be overridden.

### Modifier Overriding (deprecated)

Function modifiers can override each other. This works in the same way as function overriding (except that there is no overloading for modifiers). The virtual keyword must be used on the overridden modifier and the override keyword must be used in the overriding modifier:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.6.0 <0.9.0;
contract Base
{
// This will report a warning (deprecation)
modifier foo() virtual {_;}
}
contract Inherited is Base
{
modifier foo() override {_;}
}
```

In case of multiple inheritance, all direct base contracts must be specified explicitly:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.6.0 <0.9.0;
contract Base1
{
// This will report a warning (deprecation)
modifier foo() virtual {_;}
}
contract Base2
{
// This will report a warning (deprecation)
modifier foo() virtual {_;}
}
contract Inherited is Base1, Base2
{
modifier foo() override(Base1, Base2) {_;}
}
```

**Warning:**

virtual modifiers are deprecated and scheduled for removal.

### Constructors

A constructor is an optional function declared with the constructor keyword which is executed upon contract creation, and where you can run contract initialization code.

Before the constructor code is executed, state variables are initialised to their specified value if you initialise them inline, or their default value if you do not.

After the constructor has run, the final code of the contract is deployed to the blockchain. The deployment of the code costs additional gas linear to the length of the code. This code includes all functions that are part of the public interface and all functions that are reachable from there through function calls. It does not include the constructor code or internal functions that are only called from the constructor.

If there is no constructor, the contract will assume the default constructor, which is equivalent to constructor() {}. For example:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.0 <0.9.0;
abstract contract A {
uint public a;
constructor(uint a_) {
a = a_;
}
}
contract B is A(1) {
constructor() {}
}
```

You can use internal parameters in a constructor (for example storage pointers). In this case, the contract has to be marked abstract, because these parameters cannot be assigned valid values from outside but only through the constructors of derived contracts.

**Warning:**

Prior to version 0.4.22, constructors were defined as functions with the same name as the contract. This syntax was deprecated and is not allowed anymore in version 0.5.0.

**Warning:**

Prior to version 0.7.0, you had to specify the visibility of constructors as either internal or public.

### Arguments for Base Constructors

The constructors of all the base contracts will be called following the linearization rules explained below. If the base constructors have arguments, derived contracts need to specify all of them. This can be done in two ways:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.0 <0.9.0;
contract Base {
uint x;
constructor(uint x_) { x = x_; }
}
// Either directly specify in the inheritance list...
contract Derived1 is Base(7) {
constructor() {}
}
// or through a "modifier" of the derived constructor...
contract Derived2 is Base {
constructor(uint y) Base(y * y) {}
}
// or declare abstract...
abstract contract Derived3 is Base {
}
// and have the next concrete derived contract initialize it.
contract DerivedFromDerived is Derived3 {
constructor() Base(10 + 10) {}
}
```

One way is directly in the inheritance list (is Base(7)). The other is in the way a modifier is invoked as part of the derived constructor (Base(y * y)). The first way to do it is more convenient if the constructor argument is a constant and defines the behavior of the contract or describes it. The second way has to be used if the constructor arguments of the base depend on those of the derived contract. Arguments have to be given either in the inheritance list or in modifier-style in the derived constructor. Specifying arguments in both places is an error.

If a derived contract does not specify the arguments to all of its base contracts’ constructors, it must be declared abstract. In that case, when another contract derives from it, that other contract’s inheritance list or constructor must provide the necessary parameters for all base classes that haven’t had their parameters specified (otherwise, that other contract must be declared abstract as well). For example, in the above code snippet, see Derived3 and DerivedFromDerived.

### Multiple Inheritance and Linearization

Languages that allow multiple inheritance have to deal with several problems. One is the Diamond Problem. Solidity is similar to Python in that it uses C3 Linearization to force a specific order in the directed acyclic graph (DAG) of base classes. This results in the desirable property of monotonicity but disallows some inheritance graphs. Especially, the order in which the base classes are given in the is directive is important: You have to list the direct base contracts in the order from “most base-like” to “most derived”. Note that this order is the reverse of the one used in Python. (https://en.wikipedia.org/wiki/Multiple_inheritance#The_diamond_problem)

Another simplifying way to explain this is that when a function is called that is defined multiple times in different contracts, the given bases are searched from right to left (left to right in Python) in a depth-first manner, stopping at the first match. If a base contract has already been searched, it is skipped.

In the following code, Solidity will give the error “Linearization of inheritance graph impossible”.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.4.0 <0.9.0;
contract X {}
contract A is X {}
// This will not compile
contract C is A, X {}
```

The reason for this is that C requests X to override A (by specifying A, X in this order), but A itself requests to override X, which is a contradiction that cannot be resolved.

Due to the fact that you have to explicitly override a function that is inherited from multiple bases without a unique override, C3 linearization is not too important in practice.

One area where inheritance linearization is especially important and perhaps not as clear is when there are multiple constructors in the inheritance hierarchy. The constructors will always be executed in the linearized order, regardless of the order in which their arguments are provided in the inheriting contract’s constructor. For example:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.0 <0.9.0;
contract Base1 {
constructor() {}
}
contract Base2 {
constructor() {}
}
// Constructors are executed in the following order:
// 1 - Base1
// 2 - Base2
// 3 - Derived1
contract Derived1 is Base1, Base2 {
constructor() Base1() Base2() {}
}
// Constructors are executed in the following order:
// 1 - Base2
// 2 - Base1
// 3 - Derived2
contract Derived2 is Base2, Base1 {
constructor() Base2() Base1() {}
}
// Constructors are still executed in the following order:
// 1 - Base2
// 2 - Base1
// 3 - Derived3
contract Derived3 is Base2, Base1 {
constructor() Base1() Base2() {}
}
```

### Inheriting Different Kinds of Members of the Same Name

The only situations where, due to inheritance, a contract may contain multiple definitions sharing the same name are:

- Overloading of functions.

- Overriding of virtual functions.

- Overriding of external virtual functions by state variable getters.

- Overriding of virtual modifiers.

- Overloading of events.

## 3.9.12 Abstract Contracts

Contracts must be marked as abstract when at least one of their functions is not implemented or when they do not provide arguments for all of their base contract constructors. Even if this is not the case, a contract may still be marked abstract, such as when you do not intend for the contract to be created directly. Abstract contracts are similar to Interfaces but an interface is more limited in what it can declare.

An abstract contract is declared using the abstract keyword as shown in the following example. Note that this contract needs to be defined as abstract, because the function utterance() is declared, but no implementation was provided (no implementation body { } was given).

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.6.0 <0.9.0;
abstract contract Feline {
function utterance() public virtual returns (bytes32);
}
```

Such abstract contracts can not be instantiated directly. This is also true, if an abstract contract itself does implement all defined functions. The usage of an abstract contract as a base class is shown in the following example:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.6.0 <0.9.0;
abstract contract Feline {
function utterance() public pure virtual returns (bytes32);
}
contract Cat is Feline {
function utterance() public pure override returns (bytes32) { return "miaow"; }
}
```

If a contract inherits from an abstract contract and does not implement all non-implemented functions by overriding, it needs to be marked as abstract as well.

Note that a function without implementation is different from a Function Type even though their syntax looks very similar.

Example of function without implementation (a function declaration):

```
function foo(address) external returns (address);
```

Example of a declaration of a variable whose type is a function type:

```
function(address) external returns (address) foo;
```

Abstract contracts decouple the definition of a contract from its implementation providing better extensibility and self-documentation and facilitating patterns like the Template method and removing code duplication. Abstract contracts are useful in the same way that defining methods in an interface is useful. It is a way for the designer of the abstract contract to say “any child of mine must implement this method”. (https://en.wikipedia.org/wiki/Template_method_pattern)

ò Note

Abstract contracts cannot override an implemented virtual function with an unimplemented one.

## 3.9.13 Interfaces

Interfaces are similar to abstract contracts, but they cannot have any functions implemented. There are further restrictions:

- They cannot inherit from other contracts, but they can inherit from other interfaces.

- All declared functions must be external in the interface, even if they are public in the contract.

- They cannot declare a constructor.

- They cannot declare state variables.

- They cannot declare modifiers.

Some of these restrictions might be lifted in the future.

Interfaces are basically limited to what the Contract ABI can represent, and the conversion between the ABI and an interface should be possible without any information loss.

Interfaces are denoted by their own keyword:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.6.2 <0.9.0;
interface Token {
enum TokenType { Fungible, NonFungible }
struct Coin { string obverse; string reverse; }
function transfer(address recipient, uint amount) external;
}
```

Contracts can inherit interfaces as they would inherit other contracts.

All functions declared in interfaces are implicitly virtual and any functions that override them do not need the override keyword. This does not automatically mean that an overriding function can be overridden again - this is only possible if the overriding function is marked virtual.

Interfaces can inherit from other interfaces. This has the same rules as normal inheritance.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.6.2 <0.9.0;
interface ParentA {
function test() external returns (uint256);
}
interface ParentB {
function test() external returns (uint256);
}
interface SubInterface is ParentA, ParentB {
// Must redefine test in order to assert that the parent
// meanings are compatible.
function test() external override(ParentA, ParentB) returns (uint256);
}
```

Types defined inside interfaces and other contract-like structures can be accessed from other contracts: Token. TokenType or Token.Coin.

**Warning:**

Interfaces have supported enum types since Solidity version 0.5.0, make sure the pragma version specifies this version as a minimum.

## 3.9.14 Libraries

Libraries are similar to contracts, but their purpose is that they are deployed only once at a specific address and their code is reused using the DELEGATECALL (CALLCODE until Homestead) feature of the EVM. This means that if library functions are called, their code is executed in the context of the calling contract, i.e. this points to the calling contract, and especially the storage from the calling contract can be accessed. As a library is an isolated piece of source code, it can only access state variables of the calling contract if they are explicitly supplied (it would have no way to name them, otherwise). Library functions can only be called directly (i.e. without the use of DELEGATECALL) if they do not modify the state (i.e. if they are view or pure functions), because libraries are assumed to be stateless. In particular, it is not possible to destroy a library.

**Note:**

Until version 0.4.20, it was possible to destroy libraries by circumventing Solidity’s type system. Starting from that version, libraries contain a mechanism that disallows state-modifying functions to be called directly (i.e. without DELEGATECALL).

Libraries can be seen as implicit base contracts of the contracts that use them. They will not be explicitly visible in the inheritance hierarchy, but calls to library functions look just like calls to functions of explicit base contracts (using qualified access like L.f()). Ofcourse, calls to internal functions use the internal calling convention, which means that all internal types can be passed and types stored in memory will be passed by reference and not copied. To realize this in the EVM, the code of internal library functions that are called from a contract and all functions called from therein will at compile time be included in the calling contract, and a regular JUMP call will be used instead of a DELEGATECALL.

**Note:**

The inheritance analogy breaks down when it comes to public functions. Calling a public library function with L.f() results in an external call (DELEGATECALL to be precise). In contrast, A.f() is an internal call when A is a base contract of the current contract.

The following example illustrates how to use libraries (but using a manual method, be sure to check out using for for a more advanced example to implement a set).

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.6.0 <0.9.0;
// We define a new struct datatype that will be used to
// hold its data in the calling contract.
struct Data {
mapping(uint => bool) flags;
}
library Set {
// Note that the first parameter is of type "storage
// reference" and thus only its storage address and not
// its contents is passed as part of the call. This is a
// special feature of library functions. It is idiomatic
// to call the first parameter `self`, if the function can
// be seen as a method of that object.
function insert(Data storage self, uint value)
public
returns (bool)
{
if (self.flags[value])
return false; // already there
self.flags[value] = true;
return true;
}
function remove(Data storage self, uint value)
public
returns (bool)
{
if (!self.flags[value])
return false; // not there
self.flags[value] = false;
return true;
}
function contains(Data storage self, uint value)
public
view
returns (bool)
{
return self.flags[value];
}
}
contract C {
Data knownValues;
function register(uint value) public {
// The library functions can be called without a
// specific instance of the library, since the
// "instance" will be the current contract.
require(Set.insert(knownValues, value));
}
// In this contract, we can also directly access knownValues.flags, if we want.
}
```

Of course, you do not have to follow this way to use libraries: they can also be used without defining struct data types. Functions also work without any storage reference parameters, and they can have multiple storage reference parameters and in any position.

The calls to Set.contains, Set.insert and Set.remove are all compiled as calls (DELEGATECALL) to an external contract/library. If you use libraries, be aware that an actual external function call is performed. msg.sender, msg. value and this will retain their values in this call, though (prior to Homestead, because of the use of CALLCODE, msg.sender and msg.value changed, though).

The following example shows how to use types stored in memory and internal functions in libraries in order to implement custom types without the overhead of external function calls:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.0;
struct bigint {
uint[] limbs;
}
library BigInt {
function fromUint(uint x) internal pure returns (bigint memory r) {
r.limbs = new uint[](1);
r.limbs[0] = x;
}
function add(bigint memory a, bigint memory b) internal pure returns (bigint memoryr) {
r.limbs = new uint[](max(a.limbs.length, b.limbs.length));
uint carry = 0;
for (uint i = 0; i < r.limbs.length; ++i) {
uint limbA = limb(a, i);
uint limbB = limb(b, i);
unchecked {
r.limbs[i] = limbA + limbB + carry;
if (limbA + limbB < limbA || (limbA + limbB == type(uint).max && carry >0))
carry = 1;
else
carry = 0;
}
}
if (carry > 0) {
// too bad, we have to add a limb
uint[] memory newLimbs = new uint[](r.limbs.length + 1);
uint i;
for (i = 0; i < r.limbs.length; ++i)
newLimbs[i] = r.limbs[i];
newLimbs[i] = carry;
r.limbs = newLimbs;
}
}
function limb(bigint memory a, uint index) internal pure returns (uint) {
return index < a.limbs.length ? a.limbs[index] : 0;
}
function max(uint a, uint b) private pure returns (uint) {
return a > b ? a : b;
}
}
contract C {
using BigInt for bigint;
function f() public pure {
bigint memory x = BigInt.fromUint(7);
bigint memory y = BigInt.fromUint(type(uint).max);
bigint memory z = x.add(y);
assert(z.limb(1) > 0);
}
}
```

It is possible to obtain the address of a library by converting the library type to the address type, i.e. using address(LibraryName).

As the compiler does not know the address where the library will be deployed, the compiled hex code will contain placeholders of the form **\$30bbc0abd4d6364515865950d3e0d10953\$** (format was different <v0.5.0). The placeholder is a 34 character prefix of the hex encoding of the keccak256 hash of the fully qualified library name, which would be for example libraries/bigint.sol:BigInt if the library was stored in a file called bigint.sol in a libraries/ directory. Such bytecode is incomplete and should not be deployed. Placeholders need to be replaced with actual addresses. You can do that by either passing them to the compiler when the library is being compiled or by using the linker to update an already compiled binary. See Library Linking for information on how to use the commandline compiler for linking. (https://docs.soliditylang.org/en/v0.4.26/contracts.html#libraries)

In comparison to contracts, libraries are restricted in the following ways:

- they cannot have state variables

- they cannot inherit nor be inherited

- they cannot receive Ether

- they cannot be destroyed

(These might be lifted at a later point.)

### Function Signatures and Selectors in Libraries

While external calls to public or external library functions are possible, the calling convention for such calls is considered to be internal to Solidity and not the same as specified for the regular contract ABI. External library functions support more argument types than external contract functions, for example recursive structs and storage pointers. For that reason, the function signatures used to compute the 4-byte selector are computed following an internal naming schema and arguments of types not supported in the contract ABI use an internal encoding.

The following identifiers are used for the types in the signatures:

- Value types, non-storage string and non-storage bytes use the same identifiers as in the contract ABI.

- Non-storage array types follow the same convention as in the contract ABI, i.e. <type>[] for dynamic arrays and <type>[M] for fixed-size arrays of M elements.

- Non-storage structs are referred to by their fully qualified name, i.e. C.S for contract C { struct S { ... } }.

- Storage pointer mappings use mapping(<keyType> => <valueType>) storage where <keyType> and <valueType> are the identifiers for the key and value types of the mapping, respectively.

- Other storage pointer types use the type identifier of their corresponding non-storage type, but append a single space followed by storage to it.

The argument encoding is the same as for the regular contract ABI, except for storage pointers, which are encoded as a uint256 value referring to the storage slot to which they point.

Similarly to the contract ABI, the selector consists of the first four bytes of the Keccak256-hash of the signature. Its value can be obtained from Solidity using the .selector member as follows:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.5.14 <0.9.0;
library L {
function f(uint256) external {}
}
contract C {
function g() public pure returns (bytes4) {
return L.f.selector;
}
}
```

### Call Protection For Libraries

As mentioned in the introduction, if a library’s code is executed using a CALL instead of a DELEGATECALL or CALLCODE, it will revert unless a view or pure function is called.

The EVM does not provide a direct way for a contract to detect whether it was called using CALL or not, but a contract can use the ADDRESS opcode to find out “where” it is currently running. The generated code compares this address to the address used at construction time to determine the mode of calling.

More specifically, the runtime code of a library always starts with a push instruction, which is a zero of 20 bytes at compilation time. When the deploy code runs, this constant is replaced in memory by the current address and this modified code is stored in the contract. At runtime, this causes the deploy time address to be the first constant to be pushed onto the stack and the dispatcher code compares the current address against this constant for any non-view and non-pure function.

This means that the actual code stored on chain for a library is different from the code reported by the compiler as deployedBytecode.

## 3.9.15 Using For

The directive using A for B can be used to attach functions (A) as operators to user-defined value types or as member functions to any type (B). The member functions receive the object they are called on as their first parameter (like the self variable in Python). The operator functions receive operands as parameters.

It is valid either at file level or inside a contract, at contract level.

The first part, A, can be one of:

- A list of functions, optionally with an operator name assigned (e.g. using {f, g as +, h, L.t} for uint). If no operator is specified, the function can be either a library function or a free function and is attached to the type as a member function. Otherwise it must be a free function and it becomes the definition of that operator on the type.

- The name of a library (e.g. using L for uint) - all non-private functions of the library are attached to the type as member functions

At file level, the second part, B, has to be an explicit type (without data location specifier). Inside contracts, you can also use * in place of the type (e.g. using L for *;), which has the effect that all functions of the library L are attached to all types.

If you specify a library, all non-private functions in the library get attached, even those where the type of the first parameter does not match the type of the object. The type is checked at the point the function is called and function overload resolution is performed.

If you use a list of functions (e.g. using {f, g, h, L.t} for uint), then the type (uint) has to be implicitly convertible to the first parameter of each of these functions. This check is performed even if none of these functions are called. Note that private library functions can only be specified when using for is inside a library.

If you define an operator (e.g. using {f as +} for T), then the type (T) must be a user-defined value type and the definition must be a pure function. Operator definitions must be global. The following operators can be defined this way:

| Category   | Operator Possible signatures |                                     |
| ---------- | ---------------------------- | ----------------------------------- |
| Bitwise    | &                            | function (T, T) pure returns (T)    |
|            |                              |                                     | function (T, T) pure returns (T) |
|            | ^                            | function (T, T) pure returns (T)    |
|            | ~                            | function (T) pure returns (T)       |
| Arithmetic | +                            | function (T, T) pure returns (T)    |
|            | -                            | function (T, T) pure returns (T)    |
|            |                              | function (T) pure returns (T)       |
|            | *                            | function (T, T) pure returns (T)    |
|            | /                            | function (T, T) pure returns (T)    |
|            | %                            | function (T, T) pure returns (T)    |
| Comparison | ==                           | function (T, T) pure returns (bool) |
|            | !=                           | function (T, T) pure returns (bool) |
|            | <                            | function (T, T) pure returns (bool) |
|            | <=                           | function (T, T) pure returns (bool) |
|            | >                            | function (T, T) pure returns (bool) |
|            | >=                           | function (T, T) pure returns (bool) |

Note that unary and binary - need separate definitions. The compiler will choose the right definition based on how the operator is invoked.

The using A for B; directive is active only within the current scope (either the contract or the current module/source unit), including within all of its functions, and has no effect outside of the contract or module in which it is used.

When the directive is used at file level and applied to a user-defined type which was defined at file level in the same file, the word global can be added at the end. This will have the effect that the functions and operators are attached to the type everywhere the type is available (including other files), not only in the scope of the using statement.

Let us rewrite the set example from the Libraries section in this way, using file-level functions instead of library functions.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.13;
struct Data { mapping(uint => bool) flags; }
// Now we attach functions to the type.
// The attached functions can be used throughout the rest of the module.
// If you import the module, you have to
// repeat the using directive there, for example as
// import "flags.sol" as Flags;
// using {Flags.insert, Flags.remove, Flags.contains}
// for Flags.Data;
using {insert, remove, contains} for Data;
function insert(Data storage self, uint value)
returns (bool)
{
if (self.flags[value])
return false; // already there
self.flags[value] = true;
return true;
}
function remove(Data storage self, uint value)
returns (bool)
{
if (!self.flags[value])
return false; // not there
self.flags[value] = false;
return true;
}
function contains(Data storage self, uint value)
view
returns (bool)
{
return self.flags[value];
}
contract C {
Data knownValues;
function register(uint value) public {
// Here, all variables of type Data have
// corresponding member functions.
// The following function call is identical to
// `Set.insert(knownValues, value)`
require(knownValues.insert(value));
}
}
```

It is also possible to extend built-in types in that way. In this example, we will use a library.

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.13;
library Search {
function indexOf(uint[] storage self, uint value)
public
view
returns (uint)
{
for (uint i = 0; i < self.length; i++)
if (self[i] == value) return i;
return type(uint).max;
}
}
using Search for uint[];
contract C {
uint[] data;
function append(uint value) public {
data.push(value);
}
function replace(uint from, uint to) public {
// This performs the library function call
uint index = data.indexOf(from);
if (index == type(uint).max)
data.push(to);
else
data[index] = to;
}
}
```

Note that all external library calls are actual EVM function calls. This means that if you pass memory or value types, a copy will be performed, even in case of the self variable. The only situation where no copy will be performed is when storage reference variables are used or when internal library functions are called.

Another example shows how to define a custom operator for a user-defined type:

```
// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.19;
type UFixed16x2 is uint16;
using {
add as +,
div as /
} for UFixed16x2 global;
uint32 constant SCALE = 100;
function add(UFixed16x2 a, UFixed16x2 b) pure returns (UFixed16x2) {
return UFixed16x2.wrap(UFixed16x2.unwrap(a) + UFixed16x2.unwrap(b));
}
function div(UFixed16x2 a, UFixed16x2 b) pure returns (UFixed16x2) {
uint32 a32 = UFixed16x2.unwrap(a);
uint32 b32 = UFixed16x2.unwrap(b);
uint32 result32 = a32 * SCALE / b32;
require(result32 <= type(uint16).max, "Divide overflow");
return UFixed16x2.wrap(uint16(a32 * SCALE / b32));
}
contract Math {
function avg(UFixed16x2 a, UFixed16x2 b) public pure returns (UFixed16x2) {
return (a + b) / UFixed16x2.wrap(200);
}
}
```
