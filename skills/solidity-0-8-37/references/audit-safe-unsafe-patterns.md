# Safe vs Unsafe Patterns (audit false-positive filter)

> **Provenance:** adapted from the local "hashlock-style-audit" skill (`common-patterns.md`, read in full 2026-10-10;
> no licence file present). Every SAFE example is **rewritten** to this skill's 0.8.37 rules:
> - named custom errors, never string `require`;
> - Solady before OpenZeppelin;
> - no `.transfer`/`.send`;
> - no raw slot-0 transient lock, and no bare `revert(0,0)`;
> - Chainlink checks without the deprecated `answeredInRound`.
>
> The SAFE snippets are compiled as one file under solc 0.8.37 / osaka / via-IR against Solady `2afba69`. That file is
> `examples/AuditSafePatterns.sol`, alongside this skill's `scripts/`.
>
> Purpose: decide whether code that *looks* vulnerable actually is. Flag the UNSAFE shape only when its path is
> really reachable.

## Reentrancy

UNSAFE: external call before the state update.
```solidity
function withdraw(uint256 amount) external {
    if (balances[msg.sender] < amount) revert Insufficient(amount, balances[msg.sender]);
    (bool ok, ) = msg.sender.call{value: amount}("");   // interaction first
    if (!ok) revert TransferFailed(msg.sender, amount);
    balances[msg.sender] -= amount;                     // effect after: reentrancy
}
```

SAFE: checks-effects-interactions.
```solidity
function withdraw(uint256 amount) external {
    uint256 bal = balances[msg.sender];
    if (amount > bal) revert Insufficient(amount, bal);
    balances[msg.sender] = bal - amount;                // effect first
    (bool ok, ) = msg.sender.call{value: amount}("");   // interaction last
    if (!ok) revert TransferFailed(msg.sender, amount);
}
```

SAFE: Solady transient guard. Inherit `ReentrancyGuardTransient` and mark entry points `nonReentrant`. It reverts
with `Reentrancy()` (`0xab143c06`). On L2s, override `_useTransientReentrancyGuardOnlyOnMainnet()` to return `false`
so it uses TSTORE everywhere. **Do not hand-roll `tload(0)` / `tstore(0, 1)`**: slot 0 can collide, and a bare revert
is a §0D defect. If you must, use a namespaced slot through Solady `LibTransient` (non-`Compat`) and a named error.

## Access control

UNSAFE: no gate on a sensitive function.
```solidity
function mint(address to, uint256 amount) external { _mint(to, amount); }   // anyone
```

SAFE: an explicit owner gate. With Solady `Ownable`, pass the owner as a **constructor argument**, never
`msg.sender`: under CREATE3 that is the factory.
```solidity
function mint(address to, uint256 amount) external onlyOwner { _mint(to, amount); }
```

UNSAFE: `tx.origin` auth. It is phishable, and since EIP-7702 it no longer proves an EOA.
```solidity
if (tx.origin != owner) revert NotOwner(tx.origin);
```
SAFE: `if (msg.sender != owner) revert NotOwner(msg.sender);`

## Integer safety

UNSAFE: `unchecked { balances[msg.sender] += amount; }` with an amount the user controls.

SAFE: `unchecked { ++i; }` in `for (uint256 i; i < n; )`. The proof is `i < n ≤ type(uint256).max`; state it in a
comment.

UNSAFE: `share = (amount / totalSupply) * totalShares;` truncates early.

SAFE: `share = FixedPointMathLib.fullMulDiv(amount, totalShares, totalSupply);` multiplies first with no phantom
overflow, and a zero `totalSupply` is a named check.

## Oracles

UNSAFE: spot price from reserves. Flash-loan manipulable.
```solidity
(uint112 r0, uint112 r1, ) = pair.getReserves();
uint256 price = uint256(r0) * 1e18 / r1;
```

UNSAFE: no validation.
```solidity
(, int256 answer, , , ) = feed.latestRoundData();
return uint256(answer);
```

SAFE: proxy feed, with every check named. `answeredInRound` is deprecated (docs.chain.link API reference), so it is
not used.
```solidity
(, int256 answer, , uint256 updatedAt, ) = feed.latestRoundData();      // `feed` = the PROXY, not an aggregator
if (answer <= 0) revert BadAnswer(answer);
if (updatedAt == 0) revert FeedUninitialized();
if (updatedAt > block.timestamp) revert FeedFromFuture(updatedAt, block.timestamp);
if (block.timestamp - updatedAt > maxAge) revert StaleFeed(updatedAt, maxAge);   // maxAge: immutable/config
```
On an L2, check the sequencer-uptime feed first: down, `startedAt == 0`, inside the grace period, or a future
`startedAt` each reverts with a named error.

## Token transfers

UNSAFE: `token.transfer(to, amount);`. Some tokens return `false` or nothing.

SAFE: Solady.
```solidity
using SafeTransferLib for address;
token.safeTransfer(to, amount);   // reverts TransferFailed() on false or no code
```

UNSAFE: credits `amount` with a fee-on-transfer token.
```solidity
token.safeTransferFrom(msg.sender, address(this), amount);
balances[msg.sender] += amount;
```

SAFE: credit the measured delta.
```solidity
uint256 before = SafeTransferLib.balanceOf(token, address(this));
token.safeTransferFrom(msg.sender, address(this), amount);
uint256 received = SafeTransferLib.balanceOf(token, address(this)) - before;
balances[msg.sender] += received;
```
Note: Solady `balanceOf` reads **0 for a codeless token**. Gate on `token.code.length != 0` where a silent zero
would mislead.

## Proxies and initialisation

UNSAFE: `function initialize(address admin) public { _admin = admin; }`. Anyone can call it first. Under CREATE3, a
split deploy-then-init is a real takeover window, and has been fork-proven in this repo.

SAFE, preferred: **no initializer.** Set owners and endpoints as constructor-set `immutable`s, or deploy and
initialise atomically (CreateX `deployCreate3AndInit`).

SAFE, initializer pattern: Solady `Initializable`. Mark `initialize` with `initializer`, call `_disableInitializers()`
in the implementation constructor, and reject a zero admin with a named error. Caveat: its modifiers are `virtual`,
which gives 8429 warnings under 0.8.37 unless you patch the copy.

## Front-running

UNSAFE: `amountOutMin = 0`, `deadline = block.timestamp`, or a v3/v4 `sqrtPriceLimitX96 = 0` (full-range sentinel).

SAFE: caller-supplied `minOut > 0`, a real `deadline`, and a non-zero price limit. Reject the sentinels with named
errors.

## Signatures

UNSAFE: raw `ecrecover` without a zero check. It returns `address(0)` on failure.

SAFE: Solady.
```solidity
address signer = ECDSA.recover(digest, signature);   // reverts InvalidSignature() on failure
if (signer != expected) revert WrongSigner(signer, expected);
```
**Malleability:** Solady's `ECDSA` does **not** check non-malleability (its header). So never key replay protection
on the signature bytes: put a nonce and a deadline in the EIP-712 digest, or use `ECDSA.canonicalHash`. For contract
signers use `SignatureCheckerLib.isValidSignatureNow`, which makes a STATICCALL for ERC-1271.

## Denial of service

UNSAFE: a push loop over a growable array with `.transfer`. That is deprecated, and one failure blocks every user.

SAFE: pull pattern.
```solidity
function claim() external {
    uint256 r = pending[msg.sender];
    if (r == 0) revert NothingToClaim();
    pending[msg.sender] = 0;
    (bool ok, ) = msg.sender.call{value: r}("");
    if (!ok) revert TransferFailed(msg.sender, r);
}
```
