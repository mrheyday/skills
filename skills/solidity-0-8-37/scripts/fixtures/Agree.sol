// SPDX-License-Identifier: MIT
pragma solidity 0.8.37;

/// @notice Bad name and undocumented parameter on purpose.
error zero_amount(uint256 BAD);

/// @title Agree
/// @notice Fixture that both solcheck backends must judge the same way.
contract Agree {
    uint256[50] private __gap;

    /// @notice Deploy.
    constructor()
        public
    { }

    /// @notice Takes a callback.
    function take(function(uint256) external cb) external {
        cb(1);
    }

    /// @notice Captured low-level call.
    /// @param to recipient
    function captured(address to) external {
        (bool ok,) = to.call{value: 1}("");
        if (!ok) revert zero_amount(0);
    }

    /// @notice Unchecked low-level call.
    /// @param to recipient
    function uncheckedCall(address to) external {
        uint256 x = 1;
        to.call{value: x}("");
    }

    /// @notice Replaced memory-safe-assembly with the flag form.
    function note() external { }

    /// @notice Parameter named now.
    /// @param now a timestamp value
    /// @return stamp the same value
    function stamp(uint256 now) external pure returns (uint256) {
        return now;
    }

    /// @notice Wrapped string require.
    /// @param amount candidate
    function badRequire(uint256 amount) external pure {
        require(
            amount > 0,
            "zero"
        );
    }
}
