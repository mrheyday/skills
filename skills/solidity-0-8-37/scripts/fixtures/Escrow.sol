// SPDX-License-Identifier: MIT
pragma solidity 0.8.37;

/// @notice Thrown when `msg.value` is zero on deposit.
error ZeroDeposit();
/// @notice Thrown when `seller` is the zero address or equals the buyer.
/// @param seller the rejected seller address
error InvalidSeller(address seller);
/// @notice Thrown when the escrow is not in the state required by the call.
/// @param current the current state
/// @param required the state the call requires
error InvalidState(Escrow.State current, Escrow.State required);
/// @notice Thrown when the caller is neither the buyer nor the seller, or not the required party.
/// @param caller the unauthorised caller
error Unauthorized(address caller);
/// @notice Thrown when an Ether transfer fails.
/// @param to the recipient
/// @param amount wei attempted
error TransferFailed(address to, uint256 amount);
/// @notice Thrown on a reentrant call.
error Reentrancy();

/// @title Escrow
/// @notice Holds a buyer's Ether for a seller until the buyer confirms delivery; either party can cancel
///         before confirmation, refunding the buyer.
/// @dev Single-use: one deposit, one outcome. Funds leave only via `call` after state is finalised
///      (checks-effects-interactions). The reentrancy lock uses transient storage (EIP-1153), which is
///      reset at the end of every transaction, so the guard costs no persistent SSTORE.
contract Escrow {
    /// @notice Lifecycle of the escrow.
    enum State {
        AwaitingDeposit,
        Funded,
        Released,
        Cancelled
    }

    /// @notice The party that funds the escrow and confirms delivery.
    /// @return buyer the buyer address
    address public immutable buyer;
    /// @notice The party paid on confirmation.
    /// @return seller the seller address
    address public immutable seller;
    /// @notice Current lifecycle state.
    /// @return state the current state
    State public state;
    /// @notice Wei held for the seller while `state == Funded`.
    /// @return amount wei held
    uint256 public amount;
    uint256 private transient _locked;

    /// @notice Emitted when the buyer funds the escrow.
    /// @param amount wei deposited
    event Deposited(uint256 amount);
    /// @notice Emitted when funds are released to the seller.
    /// @param amount wei paid
    event Released(uint256 amount);
    /// @notice Emitted when the escrow is cancelled and the buyer refunded.
    /// @param by the party that cancelled
    /// @param amount wei refunded
    event Cancelled(address indexed by, uint256 amount);

    modifier nonReentrant() {
        if (_locked != 0) revert Reentrancy();
        _locked = 1;
        _;
        _locked = 0;
    }

    modifier inState(State required) {
        if (state != required) revert InvalidState(state, required);
        _;
    }

    /// @notice Creates an escrow between the deployer (buyer) and `seller_`.
    /// @param seller_ the seller to be paid on confirmation
    constructor(address seller_) {
        if (seller_ == address(0) || seller_ == msg.sender) revert InvalidSeller(seller_);
        buyer = msg.sender;
        seller = seller_;
    }

    /// @notice Buyer funds the escrow. Callable once.
    function deposit() external payable inState(State.AwaitingDeposit) {
        if (msg.sender != buyer) revert Unauthorized(msg.sender);
        if (msg.value == 0) revert ZeroDeposit();
        amount = msg.value;
        state = State.Funded;
        emit Deposited(msg.value);
    }

    /// @notice Buyer confirms delivery; the held amount is paid to the seller.
    function confirmDelivery() external nonReentrant inState(State.Funded) {
        if (msg.sender != buyer) revert Unauthorized(msg.sender);
        uint256 payout = amount;
        state = State.Released;
        emit Released(payout);
        _pay(seller, payout);
    }

    /// @notice Either party cancels before confirmation; the buyer is refunded in full.
    function cancel() external nonReentrant inState(State.Funded) {
        if (msg.sender != buyer && msg.sender != seller) revert Unauthorized(msg.sender);
        uint256 refund = amount;
        state = State.Cancelled;
        emit Cancelled(msg.sender, refund);
        _pay(buyer, refund);
    }

    /// @dev Sends `value` wei to `to` and reverts with the offending values on failure.
    function _pay(address to, uint256 value) private {
        (bool ok, ) = to.call{value: value}("");
        if (!ok) revert TransferFailed(to, value);
    }
}
