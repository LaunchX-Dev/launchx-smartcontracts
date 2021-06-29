// SPDX-License-Identifier: unlicensed
pragma solidity ^0.8.0;

import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {SafeERC20} from '@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol';
import {IERC20} from '@openzeppelin/contracts/token/ERC20/IERC20.sol';

library Errors {
    string public constant ZERO_ADDRESS = 'ZERO_ADDRESS';
    string public constant LOCK_END_BEFORE_START = 'LOCK_END_BEFORE_START';
    string public constant DEPOSIT_BEFORE_START = 'DEPOSIT_BEFORE_START';
    string public constant DEPOSIT_AFTER_END = 'DEPOSIT_AFTER_END';
    string public constant WITHDRAW_BEFORE_END = 'WITHDRAW_BEFORE_END';
    string public constant TOKEN_MUST_BE_LNX_OR_LNXP = 'TOKEN_MUST_BE_LNX_OR_LNXP';
}

// this contract will basically be the main contract that implements the fucntionality for "guarantee pool"
// and "lottery pool" based on the specification given by Mathew over the conference.
contract Staking is Ownable {
    using SafeERC20 for IERC20;

    address public lnx_address;
    address public lnxp_address;
    uint256 public lock_start;  // todo use uint40
    uint256 public lock_end;

    mapping(address => mapping(address => uint256)) public userTokenDeposit;  // todo instead of mapping use struct with 2 tokens balances

    event Deposit(
        address indexed user,
        address indexed token,
        uint256 amount
    );
    event Withdraw(
        address indexed user,
        address indexed token,
        uint256 amount
    );
    event EmergencyWithdraw(
        address indexed user,
        address indexed token,
        uint256 amount
    );

    /*
    lnx_address - address of the Lunch X token contract
    lnxp_address - address of the Lunch X power token contract
    lock_start - start time of the lock
    lock_end - end of the lock period
    */
    constructor (address _lnx_address, address _lnxp_address, uint256 _lock_start, uint256 _lock_end) {
        require(_lnx_address != address(0), Errors.ZERO_ADDRESS);
        require(_lnxp_address != address(0), Errors.ZERO_ADDRESS);
        require(_lock_start < _lock_end, Errors.LOCK_END_BEFORE_START);
        // todo restrictions on lock start and end
        lnx_address = _lnx_address;
        lnxp_address = _lnxp_address;
        lock_start = _lock_start;
        lock_end = _lock_end;
    }

    // If there is a problem with the contract, it should be possible to return tokens (to the specified address) parameters - token address, recipient address and quantity
    function emergencyWithdrawal(address token, address recipient, uint256 quantity) external onlyOwner {
        require(recipient != address(0), Errors.ZERO_ADDRESS);
        require(token == lnx_address || token == lnxp_address, Errors.TOKEN_MUST_BE_LNX_OR_LNXP);
        emit EmergencyWithdraw(recipient, token, quantity);
        IERC20(token).safeTransfer(recipient, quantity);
    }

    /*
    Transfers tokens on behalf of msg.sender to this contract,

    if the transfer occurs within the specified period (lock_start, lock_end),
    and the transferred tokens are either launcx or laynchx power - then the transfer ends with success,
    if not, an error is issued corresponding to the problem.

    If the transfer is successful,
    it adds to the counter of transferred tokens with this address the amount of transferred tokens (report from zero)
    */
    function depositToken(address token, uint256 amount) external {
        require(block.timestamp >= lock_start, Errors.DEPOSIT_BEFORE_START);
        require(block.timestamp <= lock_start, Errors.DEPOSIT_AFTER_END);
        require(token == lnx_address || token == lnxp_address, Errors.TOKEN_MUST_BE_LNX_OR_LNXP);
        userTokenDeposit[_msgSender()][token] += amount;
        emit Deposit(_msgSender(), token, amount);
        IERC20(token).safeTransferFrom(_msgSender(), address(this), amount);  // todo deflationary token
    }

    /*
    When a function is called, all tokens of the specified type previously translated by the called address
    are transferred back to the calling address.
    If the transfer is initiated between lock_start and lock_end, - an error
    If tokens have already been transferred in whole or in part - also an error.
    */
    function withdrawToken(address token, uint256 amount) external {
        require(block.timestamp > lock_end, Errors.WITHDRAW_BEFORE_END);
        require(token == lnx_address || token == lnxp_address, Errors.TOKEN_MUST_BE_LNX_OR_LNXP);
        userTokenDeposit[_msgSender()][token] -= amount;  // warn: underflow check happens here because solidity 0.8.0
        emit Withdraw(_msgSender(), token, amount);
        IERC20(token).safeTransfer(_msgSender(), amount);  // todo deflationary token
    }

    /*
    This readonly function simply returns the number of tokens of the specified type that were
    locked with the specified address. That is, the sum of all successful deposits of tokens of
    the specified type with the specified address.
    */
    function getTokensStaked(address user, address token) external view returns(uint256) {
        require(token == lnx_address || token == lnxp_address, Errors.TOKEN_MUST_BE_LNX_OR_LNXP);
        return userTokenDeposit[user][token];
    }

    /*
    This function returns the current balance of the specified address in the specified tokens.
    The balance can be greater than zero and at the same time less than the sum of the withdrawn tokens,
    since there is an emergencyWithdrawal function
    */
    function getTokenBalance(address token) external view returns(uint256)  {
        require(token == lnx_address || token == lnxp_address, Errors.TOKEN_MUST_BE_LNX_OR_LNXP);
        return IERC20(token).balanceOf(address(this)); // todo discuss external call is more safe but expensive
    }

    // Also, the contract must have standard functions for changing and adding or removing owners
    // done inside Ownable
}
