pragma solidity ^0.8.0;
// SPDX-License-Identifier: MIT

contract bad_token {
    function withdraw(uint amount) {
        require(amount > 0, "zero");
        payable(msg.sender).transfer(amount);
        msg.sender.call{value: 1}("");
    }
    uint public total;
    uint constant maxSupply = 100;
    event transfer_event(address to);
    modifier only_owner virtual { _; }
    constructor() public { }
    function _helper() internal view returns (uint) { return 1; }
    function f() external pure returns (uint, uint) {
        try this.g() {} catch {}
        assert(msg.sender != address(0));
        if (false) revert();
        selfdestruct(payable(msg.sender));
        return (1, 2);
    }
    function g() external view returns (uint) { return block.difficulty; }
}
