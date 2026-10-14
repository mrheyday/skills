// SPDX-License-Identifier: MIT
pragma solidity 0.8.37;

/// @notice Thrown when a zero amount is supplied.
error ZeroAmount();
/// @notice Thrown when the caller's balance is insufficient.
/// @param requested amount requested
/// @param available amount available
error InsufficientBalance(uint256 requested, uint256 available);
/// @notice Thrown when an Ether transfer fails.
/// @param to recipient
/// @param amount wei attempted
error TransferFailed(address to, uint256 amount);

/// @title Vault
/// @notice Minimal Ether vault with pull-based withdrawals.
contract Vault {
    /// @notice Balance per depositor.
    /// @return balance wei held for the account
    mapping(address => uint256) public balances;

    /// @notice Emitted on deposit.
    /// @param from depositor
    /// @param amount wei deposited
    event Deposited(address indexed from, uint256 amount);

    /// @notice Deposit Ether.
    function deposit() external payable {
        if (msg.value == 0) revert ZeroAmount();
        balances[msg.sender] += msg.value;
        emit Deposited(msg.sender, msg.value);
    }

    /// @notice Withdraw Ether.
    /// @param amount wei to withdraw
    function withdraw(uint256 amount) external {
        uint256 bal = balances[msg.sender];
        if (amount == 0) revert ZeroAmount();
        if (amount > bal) revert InsufficientBalance(amount, bal);
        balances[msg.sender] = bal - amount;
        (bool ok, ) = msg.sender.call{value: amount}("");
        if (!ok) revert TransferFailed(msg.sender, amount);
    }

    /// @notice Balance of an account.
    /// @param account the account
    /// @return balance wei held
    function balanceOf(address account) external view returns (uint256 balance) {
        return balances[account];
    }
}
