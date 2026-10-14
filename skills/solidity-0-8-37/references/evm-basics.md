# The Ethereum Virtual Machine (3.1.3)

> Source: Solidity documentation, release 0.8.37-develop (Sep 10, 2026), https://docs.soliditylang.org/ — text reproduced from the official docs; code indentation was flattened by the export and is not normative.

## Contents

  - 3.1.3 The Ethereum Virtual Machine

---

## 3.1.3 The Ethereum Virtual Machine

### Overview

The Ethereum Virtual Machine or EVM is the runtime environment for smart contracts in Ethereum. It is not only sandboxed but actually completely isolated, which means that code running inside the EVM has no access to network, filesystem or other processes. Smart contracts even have limited access to other smart contracts.

### Accounts

There are two kinds of accounts in Ethereum which share the same address space: Externally-owned accounts that are controlled by public-private key pairs (i.e. humans) and contract accounts which are controlled by the code stored together with the account.

The address of an externally-owned account is determined from the public key while the address of a contract is determined at the time the contract is created (it is derived from the creator address and the number of transactions sent from that address, the so-called “nonce”).

Regardless of whether or not the account stores code, the two types are treated equally by the EVM.

Every account has a persistent key-value store mapping 256-bit words to 256-bit words called storage.

Furthermore, every account has a balance in Ether (in “Wei” to be exact, 1 ether is 10**18 wei) which can be modified by sending transactions that include Ether.

### Transactions

A transaction is a message that is sent from one account to another account (which might be the same or empty, see below). It can include binary data (which is called “payload”) and Ether.

If the target account contains code, that code is executed and the payload is provided as input data.

If the target account is not set (the transaction does not have a recipient or the recipient is set to null), the transaction creates a new contract. As already mentioned, the address of that contract is not the zero address but an address derived from the sender and its number of transactions sent (the “nonce”). The payload of such a contract creation transaction is taken to be EVM bytecode and executed. The output data of this execution is permanently stored as the code of the contract. This means that in order to create a contract, you do not send the actual code of the contract, but in fact code that returns that code when executed.

**Note:**

While a contract is being created, its code is still empty. Because of that, you should not call back into the contract under construction until its constructor has finished executing.

### Gas

Upon creation, each transaction is charged with a certain amount of gas that has to be paid for by the originator of the transaction (tx.origin). While the EVM executes the transaction, the gas is gradually depleted according to specific rules. If the gas is used up at any point (i.e. it would be negative), an out-of-gas exception is triggered, which ends execution and reverts all modifications made to the state in the current call frame.

This mechanism incentivizes economical use ofEVM execution time and also compensates EVM executors (i.e. miners / stakers) for their work. Since each block has a maximum amount of gas, it also limits the amount of work needed to validate a block.

The gas price is a value set by the originator of the transaction, who has to pay gas_price * gas up front to the EVM executor. If some gas is left after execution, it is refunded to the transaction originator. In case of an exception that reverts changes, already used up gas is not refunded.

Since EVM executors can choose to include a transaction or not, transaction senders cannot abuse the system by setting a low gas price.

### Storage, Transient Storage, Memory and the Stack

The Ethereum Virtual Machine has different areas where it can store data with the most prominent being storage, transient storage, memory and the stack.

Each account has a data area called storage, which is persistent between function calls and transactions. Storage is a key-value store that maps 256-bit words to 256-bit words. It is not possible to enumerate storage from within a contract, it is comparatively costly to read, and even more to initialise and modify storage. Because of this cost, you should minimize what you store in persistent storage to what the contract needs to run. Store data like derived calculations, caching, and aggregates outside of the contract. A contract can neither read nor write to any storage apart from its own.

Similar to storage, there is another data area called transient storage, where the main difference is that it is reset at the end of each transaction. The values stored in this data location persist only across function calls originating from the first call of the transaction. When the transaction ends, the transient storage is reset and the values stored there become unavailable to calls in subsequent transactions. Despite this, the cost of reading and writing to transient storage is significantly lower than for storage.

The third data area is called memory, of which a contract obtains a freshly cleared instance for each message call. Memory is linear and can be addressed at byte level, but reads are limited to a width of 256 bits, while writes can be either 8 bits or 256 bits wide. Memory is expanded by a word (256-bit), when accessing (either reading or writing) a previously untouched memory word (i.e. any offset within a word). At the time of expansion, the cost in gas must be paid. Memory is more costly the larger it grows (it scales quadratically).

The EVM is not a register machine but a stack machine, so all computations are performed on a data area called the stack. It has a maximum size of 1024 elements and contains words of 256 bits. Access to the stack is limited to the top end in the following way: It is possible to copy one of the topmost 16 elements to the top of the stack or swap the topmost element with one of the 16 elements below it. All other operations take the topmost two (or one, or more, depending on the operation) elements from the stack and push the result onto the stack. Of course it is possible to move stack elements to storage or memory in order to get deeper access to the stack, but it is not possible to just access arbitrary elements deeper in the stack without first removing the top of the stack.

### Calldata, Returndata and Code

There are also other data areas which are not as apparent as those discussed previously. However, they are routinely used during the execution of smart contract transactions.

The calldata region is the data sent to a transaction as part of a smart contract transaction. For example, when creating a contract, calldata would be the constructor code of the new contract. The parameters of external functions are always initially stored in calldata in an ABI-encoded form and only then decoded into the location specified in their declaration. If declared as memory, the compiler will eagerly decode them into memory at the beginning of the function, while marking them as calldata means that this will be done lazily, only when accessed. Value types and storage pointers are decoded directly onto the stack.

The returndata is the way a smart contract can return a value after a call. In general, external Solidity functions use the return keyword to ABI-encode values into the returndata area.

The code is the region where the EVM instructions of a smart contract are stored. Code is the bytes read, interpreted, and executed by the EVM during smart contract execution. Instruction data stored in the code is persistent as part of a contract account state field. Immutable and constant variables are stored in the code region. All references to immutables are replaced with the values assigned to them. A similar process is performed for constants which have their expressions inlined in the places where they are referenced in the smart contract code.

### Instruction Set

The instruction set of the EVM is kept minimal in order to avoid incorrect or inconsistent implementations which could cause consensus problems. All instructions operate on the basic data type, 256-bit words or on slices of memory (or other byte arrays). The usual arithmetic, bit, logical and comparison operations are present. Conditional and unconditional jumps are possible. Furthermore, contracts can access relevant properties of the current block like its number and timestamp.

For a complete list, please see the list ofopcodes as part of the inline assembly documentation.

### Message Calls

Contracts can call other contracts or send Ether to non-contract accounts by the means of message calls. Message calls are similar to transactions, in that they have a source, a target, data payload, Ether, gas and return data. In fact, every transaction consists of a top-level message call which in turn can create further message calls.

A contract can decide how much of its remaining gas should be sent with the inner message call and how much it wants to retain. If an out-of-gas exception happens in the inner call (or any other exception), this will be signaled by an error value put onto the stack. In this case, only the gas sent together with the call is used up. In Solidity, the calling contract causes a manual exception by default in such situations, so that exceptions “bubble up” the call stack.

As already said, the called contract (which can be the same as the caller) will receive a freshly cleared instance of memory and has access to the call payload - which will be provided in a separate area called the calldata. After it has finished execution, it can return data which will be stored at a location in the caller’s memory preallocated by the caller. All such calls are fully synchronous.

Calls are limited to a depth of 1024, which means that for more complex operations, loops should be preferred over recursive calls. Furthermore, only 63/64th of the gas can be forwarded in a message call, which causes a depth limit of a little less than 1000 in practice.

### Delegatecall and Libraries

There exists a special variant of a message call, named delegatecall which is identical to a message call apart from the fact that the code at the target address is executed in the context (i.e. at the address) of the calling contract and msg.sender and msg.value do not change their values.

This means that a contract can dynamically load code from a different address at runtime. Storage, current address and balance still refer to the calling contract, only the code is taken from the called address.

This makes it possible to implement the “library” feature in Solidity: Reusable library code that can be applied to a contract’s storage, e.g. in order to implement a complex data structure.

### Logs

It is possible to store data in a specially indexed data structure that maps all the way up to the block level. This feature called logs is used by Solidity in order to implement events. Contracts cannot access log data after it has been created, but they can be efficiently accessed from outside the blockchain. Since some part of the log data is stored in bloom filters, it is possible to search for this data in an efficient and cryptographically secure way, so network peers that do not download the whole blockchain (so-called “light clients”) can still find these logs.

### Create

Contracts can even create other contracts using a special opcode (i.e. they do not simply call the zero address as a transaction would). The only difference between these create calls and normal message calls is that the payload data is executed and the result stored as code and the caller / creator receives the address of the new contract on the stack.

### Deactivate and Self-destruct

The only way to remove code from the blockchain is when a contract at that address performs the selfdestruct operation. The remaining Ether stored at that address is sent to a designated target and then the storage and code is removed from the state. Removing the contract in theory sounds like a good idea, but it is potentially dangerous, as if someone sends Ether to removed contracts, the Ether is forever lost.

**Warning:**

From EVM >= Cancun onwards, selfdestruct will only send all Ether in the account to the given recipient and not destroy the contract. However, when selfdestruct is called in the same transaction that creates the contract calling it, the behaviour of selfdestruct before Cancun hardfork (i.e., EVM <= Shanghai) is preserved and will destroy the current contract, deleting any data, including storage keys, code and the account itself. See EIP-6780 for more details. (https://eips.ethereum.org/EIPS/eip-6780)

The new behaviour is the result of a network-wide change that affects all contracts present on the Ethereum mainnet and testnets. It is important to note that this change is dependent on the EVM version of the chain on which the contract is deployed. The --evm-version setting used when compiling the contract has no bearing on it.

Also, note that the selfdestruct opcode has been deprecated in Solidity version 0.8.18, as recommended by EIP-6049. The deprecation is still in effect and the compiler will still emit warnings on its use. Any use in newly deployed contracts is strongly discouraged even if the new behavior is taken into account. Future changes to the EVM might further reduce the functionality of the opcode. (https://eips.ethereum.org/EIPS/eip-6049)

**Warning:**

Even if a contract is removed by selfdestruct, it is still part of the history of the blockchain and probably retained by most Ethereum nodes. So using selfdestruct is not the same as deleting data from a hard disk.

**Note:**

Even if a contract’s code does not contain a call to selfdestruct, it can still perform that operation using delegatecall or callcode.

If you want to deactivate your contracts, you should instead disable them by changing some internal state which causes all functions to revert. This makes it impossible to use the contract, as it returns Ether immediately.

### Precompiled Contracts

There is a small set of contract addresses that are special: The address range between 1 and (including) 0x0a contains “precompiled contracts” that can be called as any other contract but their behavior (and their gas consumption) is not defined by EVM code stored at that address (they do not contain code) but instead is implemented in the EVM execution environment itself.

Different EVM-compatible chains might use a different set of precompiled contracts. It might also be possible that new precompiled contracts are added to the Ethereum main chain in the future, but you can reasonably expect them to always be in the range between 1 and 0xffff (inclusive).
