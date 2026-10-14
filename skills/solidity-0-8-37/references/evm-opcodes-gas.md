# EVM Opcode Gas Costs Reference

## Storage Opcodes
| Opcode | Gas (Cold) | Gas (Warm) | Description |
|--------|-----------|-----------|-------------|
| `SLOAD` | 2100 | 100 | Read persistent storage |
| `SSTORE` (0→non-0) | 20000 | — | Write to fresh slot |
| `SSTORE` (non-0→non-0) | 2900 | — | Update existing slot |
| `SSTORE` (non-0→0) | 2900 + 4800 refund | — | Clear slot (refund) |
| `TLOAD` | 100 | 100 | Read transient storage (EIP-1153) |
| `TSTORE` | 100 | 100 | Write transient storage (EIP-1153) |

## Memory Opcodes
| Opcode | Gas | Description |
|--------|-----|-------------|
| `MLOAD` | 3 | Read 32 bytes from memory |
| `MSTORE` | 3 | Write 32 bytes to memory |
| `MSTORE8` | 3 | Write 1 byte to memory |
| `MCOPY` | 3 + 3/word | Copy memory (EIP-5656, Cancun) |
| `MSIZE` | 2 | Current memory size |

Memory expansion cost: `3 * words + words^2 / 512` (quadratic growth)

## Call Opcodes
| Opcode | Gas (Cold) | Gas (Warm) | Description |
|--------|-----------|-----------|-------------|
| `CALL` | 2600 | 100 | External call with value |
| `STATICCALL` | 2600 | 100 | Read-only external call |
| `DELEGATECALL` | 2600 | 100 | Call in caller's context |
| `CALLCODE` | 2600 | 100 | Deprecated — use DELEGATECALL |
| `CREATE` | 32000 | — | Deploy contract |
| `CREATE2` | 32000 | — | Deterministic deploy |

Additional CALL costs:
- Value transfer (non-zero): +9000 gas
- New account creation: +25000 gas
- Minimum 2300 gas stipend for value transfer

## Calldata Opcodes
| Opcode | Gas | Description |
|--------|-----|-------------|
| `CALLDATALOAD` | 3 | Read 32 bytes from calldata |
| `CALLDATASIZE` | 2 | Calldata length |
| `CALLDATACOPY` | 3 + 3/word | Copy calldata to memory |

## Return Data Opcodes
| Opcode | Gas | Description |
|--------|-----|-------------|
| `RETURNDATASIZE` | 2 | Size of last return data |
| `RETURNDATACOPY` | 3 + 3/word | Copy return data to memory |

## Hash & Crypto Opcodes
| Opcode | Gas | Description |
|--------|-----|-------------|
| `KECCAK256` | 30 + 6/word | Keccak-256 hash |
| `SHA3` | 30 + 6/word | Alias for KECCAK256 |

Precompiles (via CALL to address):
| Address | Gas | Description |
|---------|-----|-------------|
| `0x01` | 3000 | ecrecover |
| `0x02` | 60 + 12/word | SHA-256 |
| `0x03` | 600 + 120/word | RIPEMD-160 |
| `0x04` | 15 + 3/word | identity (memcpy) |
| `0x05` | complex | modexp |
| `0x06` | 150 | ecAdd (alt_bn128) |
| `0x07` | 6000 | ecMul (alt_bn128) |
| `0x08` | 45000/pairing | ecPairing (alt_bn128) |
| `0x09` | 1000 | blake2f |
| `0x0a` | 3450 + 4/byte | point evaluation (EIP-4844) |

## Comparison & Logic Opcodes
| Opcode | Gas | Description |
|--------|-----|-------------|
| `LT`, `GT`, `SLT`, `SGT` | 3 | Comparisons |
| `EQ` | 3 | Equality |
| `ISZERO` | 3 | Boolean not |
| `AND`, `OR`, `XOR`, `NOT` | 3 | Bitwise operations |
| `BYTE` | 3 | Extract byte from word |
| `SHL`, `SHR`, `SAR` | 3 | Bit shifts |

## Arithmetic Opcodes
| Opcode | Gas | Description |
|--------|-----|-------------|
| `ADD`, `SUB`, `MUL`, `DIV`, `SDIV` | 3-5 | Basic math |
| `MOD`, `SMOD` | 5 | Modulo |
| `ADDMOD`, `MULMOD` | 8 | Modular arithmetic |
| `EXP` | 10 + 50/byte | Exponentiation |
| `SIGNEXTEND` | 5 | Sign extension |

## Block & Environment
| Opcode | Gas | Description |
|--------|-----|-------------|
| `BLOCKHASH` | 20 | Hash of block (last 256) |
| `COINBASE` | 2 | Block producer address |
| `TIMESTAMP` | 2 | Block timestamp |
| `NUMBER` | 2 | Block number |
| `PREVRANDAO` | 2 | Beacon randomness (replaces DIFFICULTY) |
| `GASLIMIT` | 2 | Block gas limit |
| `CHAINID` | 2 | Chain ID |
| `SELFBALANCE` | 5 | This contract's ETH balance |
| `BASEFEE` | 2 | Block base fee |
| `BLOBHASH` | 3 | Blob version hash (EIP-4844) |
| `BLOBBASEFEE` | 2 | Blob base fee (EIP-7516) |
| `BALANCE` | 2600 (cold) / 100 (warm) | Address ETH balance |
| `EXTCODESIZE` | 2600 (cold) / 100 (warm) | Contract code size |
| `EXTCODEHASH` | 2600 (cold) / 100 (warm) | Contract code hash |
| `EXTCODECOPY` | 2600 (cold) + 3/word | Copy contract code |

## Stack & Flow
| Opcode | Gas | Description |
|--------|-----|-------------|
| `POP` | 2 | Remove top of stack |
| `PUSH0` | 2 | Push zero (EIP-3855, Shanghai) |
| `PUSH1`-`PUSH32` | 3 | Push N bytes |
| `DUP1`-`DUP16` | 3 | Duplicate stack item |
| `SWAP1`-`SWAP16` | 3 | Swap stack items |
| `JUMP`, `JUMPI` | 8, 10 | Control flow |
| `JUMPDEST` | 1 | Jump target marker |
| `RETURN` | 0 | Return data from memory |
| `REVERT` | 0 | Revert with data |
| `STOP` | 0 | Halt execution |
| `INVALID` | all remaining | Consume all gas |

## EIP-1153 Transient Storage (Cancun+)
```
TLOAD:  100 gas — read from transient storage
TSTORE: 100 gas — write to transient storage

Properties:
- Auto-cleared after transaction (no explicit cleanup needed)
- No cold/warm distinction (always 100 gas)
- Same slot addressing as regular storage
- Cannot be read by other transactions
- Perfect for per-transaction state (locks, deltas, flags)

MEV-KERNEL usage:
- EntryExitGuard reentrancy lock
- Per-tx order dedup bitmap
- Asset delta tracking
- Domain separator cache
```

## EIP-4844 Blob Opcodes (Cancun+)
```
BLOBHASH(index): 3 gas — get versioned hash of blob at index
BLOBBASEFEE:     2 gas — current blob base fee

Used for: rollup data posting cost estimation
```

## Source
- [soliditylang.org](https://www.soliditylang.org)
- [docs.soliditylang.org](https://docs.soliditylang.org/en/latest/)
- [evm.codes](https://www.evm.codes) (gas costs)
