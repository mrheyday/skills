// SPDX-License-Identifier: MIT
pragma solidity 0.8.37;

import {ReentrancyGuardTransient} from "solady/utils/ReentrancyGuardTransient.sol";
import {SafeTransferLib} from "solady/utils/SafeTransferLib.sol";
import {FixedPointMathLib} from "solady/utils/FixedPointMathLib.sol";
import {ECDSA} from "solady/utils/ECDSA.sol";
import {SafeCastLib} from "solady/utils/SafeCastLib.sol";

/// @notice Minimal Chainlink proxy surface used by the oracle example.
interface IAggregatorProxy {
    /// @notice Latest round data from the feed proxy.
    /// @return roundId The round id.
    /// @return answer The reported answer.
    /// @return startedAt When the round started.
    /// @return updatedAt When the round was last updated.
    /// @return answeredInRound Deprecated by Chainlink; ignored.
    function latestRoundData()
        external
        view
        returns (uint80 roundId, int256 answer, uint256 startedAt, uint256 updatedAt, uint80 answeredInRound);
}

/// @title AuditSafePatterns
/// @notice Compile-checked SAFE examples for `references/audit-safe-unsafe-patterns.md` (illustration only).
/// @dev Every failure is a named error; Solady first; no `transfer`/`send`; transient guard via Solady.
contract AuditSafePatterns is ReentrancyGuardTransient {
    using SafeTransferLib for address;

    /// @notice Owner, set at construction (never `msg.sender` under a CREATE3 factory).
    /// @return owner the owner address
    address public immutable owner;
    /// @notice Chainlink feed PROXY.
    /// @return feed the feed proxy
    IAggregatorProxy public immutable feed;
    /// @notice Maximum accepted feed age in seconds (deploy-time config, never a literal in logic).
    /// @return maxAge the maximum age in seconds
    uint256 public immutable maxAge;

    /// @notice ETH balances for the CEI example.
    /// @param account the account
    /// @return amount wei credited
    mapping(address account => uint256 amount) public balances;
    /// @notice Claimable rewards for the pull-pattern example.
    /// @param account the account
    /// @return amount wei claimable
    mapping(address account => uint256 amount) public pending;

    /// @notice A zero address was supplied.
    error ZeroAddress();
    /// @notice `amount` exceeds `available`.
    /// @param amount Requested amount.
    /// @param available Available balance.
    error Insufficient(uint256 amount, uint256 available);
    /// @notice An ETH transfer failed.
    /// @param to Recipient.
    /// @param amount Amount sent.
    error TransferFailed(address to, uint256 amount);
    /// @notice Caller is not the owner.
    /// @param caller The caller.
    error NotOwner(address caller);
    /// @notice The feed answer is not positive.
    /// @param answer The answer.
    error BadAnswer(int256 answer);
    /// @notice The feed has never been updated.
    error FeedUninitialized();
    /// @notice The feed reports an update in the future.
    /// @param updatedAt Reported update time.
    /// @param nowTs Current block timestamp.
    error FeedFromFuture(uint256 updatedAt, uint256 nowTs);
    /// @notice The feed is older than `maxAge`.
    /// @param updatedAt Reported update time.
    /// @param maxAge_ Maximum accepted age.
    error StaleFeed(uint256 updatedAt, uint256 maxAge_);
    /// @notice The divisor is zero.
    error ZeroSupply();
    /// @notice The recovered signer is not the expected one.
    /// @param signer Recovered signer.
    /// @param expected Expected signer.
    error WrongSigner(address signer, address expected);
    /// @notice Nothing to claim.
    error NothingToClaim();

    /// @dev Owner gate with a named error.
    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner(msg.sender);
        _;
    }

    /// @notice Deploy with explicit owner, feed proxy and max age.
    /// @param owner_ Owner address.
    /// @param feed_ Chainlink feed proxy.
    /// @param maxAge_ Maximum accepted feed age in seconds.
    constructor(address owner_, IAggregatorProxy feed_, uint256 maxAge_) {
        if (owner_ == address(0) || address(feed_) == address(0)) revert ZeroAddress();
        owner = owner_;
        feed = feed_;
        maxAge = maxAge_;
    }

    /// @notice Withdraw ETH following checks-effects-interactions, guarded.
    /// @param amount Wei to withdraw.
    function withdraw(uint256 amount) external nonReentrant {
        uint256 bal = balances[msg.sender];
        if (amount > bal) revert Insufficient(amount, bal);
        balances[msg.sender] = bal - amount;
        (bool ok,) = msg.sender.call{value: amount}("");
        if (!ok) revert TransferFailed(msg.sender, amount);
    }

    /// @notice Pull-pattern claim.
    function claim() external nonReentrant {
        uint256 r = pending[msg.sender];
        if (r == 0) revert NothingToClaim();
        pending[msg.sender] = 0;
        (bool ok,) = msg.sender.call{value: r}("");
        if (!ok) revert TransferFailed(msg.sender, r);
    }

    /// @notice Pull `amount` of `token` and return what actually arrived (fee-on-transfer safe).
    /// @param token ERC-20 token.
    /// @param amount Requested amount.
    /// @return received The measured balance delta.
    function pull(address token, uint256 amount) external onlyOwner returns (uint256 received) {
        uint256 before = SafeTransferLib.balanceOf(token, address(this));
        token.safeTransferFrom(msg.sender, address(this), amount);
        received = SafeTransferLib.balanceOf(token, address(this)) - before;
    }

    /// @notice Read the feed proxy with every check named (no deprecated `answeredInRound`).
    /// @return price The validated positive answer.
    function price() external view returns (uint256) {
        // forge-lint: disable-next-line(unused-return) -- only answer + updatedAt used (answeredInRound deprecated)
        (, int256 answer,, uint256 updatedAt,) = feed.latestRoundData();
        if (answer <= 0) revert BadAnswer(answer);
        if (updatedAt == 0) revert FeedUninitialized();
        // forge-lint: disable-next-line(block-timestamp) -- a staleness check is inherently a wall-clock comparison
        if (updatedAt > block.timestamp) revert FeedFromFuture(updatedAt, block.timestamp);
        // forge-lint: disable-next-line(block-timestamp) -- a staleness check is inherently a wall-clock comparison
        if (block.timestamp - updatedAt > maxAge) revert StaleFeed(updatedAt, maxAge);
        return SafeCastLib.toUint256(answer);
    }

    /// @notice Verify `signature` over `digest` came from `expected` (digest must carry nonce + deadline).
    /// @param digest EIP-712 digest including a nonce and a deadline.
    /// @param signature 65-byte or EIP-2098 signature.
    /// @param expected Expected signer.
    function verify(bytes32 digest, bytes calldata signature, address expected) external view {
        address signer = ECDSA.recover(digest, signature);
        if (signer != expected) revert WrongSigner(signer, expected);
    }

    /// @notice Share calculation: multiply before divide, no phantom overflow, named zero check.
    /// @param amount Asset amount.
    /// @param totalShares Total shares.
    /// @param totalSupply Total supply (divisor).
    /// @return share The computed share, rounded down.
    function share(uint256 amount, uint256 totalShares, uint256 totalSupply) external pure returns (uint256) {
        if (totalSupply == 0) revert ZeroSupply();
        return FixedPointMathLib.fullMulDiv(amount, totalShares, totalSupply);
    }

    /// @dev Use TSTORE on every chain (L2s included), not only mainnet.
    /// @return Always false.
    function _useTransientReentrancyGuardOnlyOnMainnet() internal pure override returns (bool) {
        return false;
    }
}
