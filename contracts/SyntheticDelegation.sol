// SPDX-License-Identifier: unlicensed
pragma solidity ^0.8.0;

import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {ERC20PresetMinterPauser} from "@openzeppelin/contracts/token/ERC20/presets/ERC20PresetMinterPauser.sol";
import {ReentrancyGuard} from '@openzeppelin/contracts/security/ReentrancyGuard.sol';
import {SafeERC20} from '@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol';
import {IERC20} from '@openzeppelin/contracts/token/ERC20/IERC20.sol';


/// @title Synthetic Delegation Contract
/// @notice User comes and wants to stake LX tokens to get LXP tokens to gain discounts and/or guaranteed allocations
///   to IDO’s and passive yield, in the form of tokens or cash. Yield is in LX tokens.
/// @notice When tokens are staked, they immediately get locked and user gets synthetic LXP tokens,
///   however, tokens are not given access to yield until next two-week cycle.
contract SyntheticDelegation is Ownable, ReentrancyGuard {  //todo remove ownable
    using SafeERC20 for IERC20;
    uint256 constant FIRST_MONDAY = 24 * 3600 * 4;  // 01.01.1970 was a Thursday
    uint256 constant WINDOW = 2 * 3600 * 24 * 7;   // 2 weeks
    uint256 constant ACTION_WINDOW = 1 * 3600;  // 1 hour to stake/unstake

    uint256 internal _rewardPerLXP;
    mapping (address => uint256) internal _userClaimed;

    address public LX;
    address public LXP;

    event RewardShared(address user, uint256 amount);
    event Stake(address user, uint256 amount);
    event Unstake(address user, uint256 amount);
    event Claim(address user, uint256 amount);

    constructor(address _LX) {
        LX = _LX;
        LXP = address(new ERC20PresetMinterPauser("LXP", "LXP"));  //todo discuss symbol
    }

    function timeFromPeriodStart() view public returns(uint256) {
        return (block.timestamp - FIRST_MONDAY) % WINDOW;
    }


    /// @notice Tokens are added every two weeks.
    ///   Users must wait until beginning of a new two-week period for tokens to stake.
    function stake(uint256 amount) external nonReentrant {
        require(timeFromPeriodStart() < ACTION_WINDOW, "TOO_LATE");
        _userClaimed[msg.sender] += amount * _rewardPerLXP;  // make it seems like user already claimed all prev reward
        emit Stake(msg.sender, amount);
        IERC20(LX).safeTransferFrom(msg.sender, address(this), amount);
        ERC20PresetMinterPauser(LXP).mint(msg.sender, amount);
    }

    /// @notice The contract needs to keep track of users’ running balance from delegation cycle to
    ///   delegation cycle and users need to be able to withdraw from just this yield balance without
    ///   removing themselves from the delegation.
    ///   They also need to be able to read this balance(UI showing balance on staking page)
    function claimableAmountOfUser(address user) view public returns(uint256) {
        uint256 balance = IERC20(LXP).balanceOf(user);
        return balance * _rewardPerLXP - _userClaimed[user];
    }

    function claim() public {  //todo nonReentrant ??
        require(timeFromPeriodStart() < ACTION_WINDOW, "TOO_LATE");
        uint256 amount = claimableAmountOfUser(msg.sender);
        if (amount > 0) {
            _userClaimed[msg.sender] += amount;
            emit Claim(msg.sender, amount);
            IERC20(LX).safeTransfer(msg.sender, amount);
        }
    }

    /// @notice When user decides to withdraw, they do not receive tokens until end of two-week delegation cycle,
    ///   but they still need synthetic tokens in wallet to burn to contract.
    function unstake(uint256 amount) external nonReentrant {
        require(timeFromPeriodStart() < ACTION_WINDOW, "TOO_LATE");  //todo resolve double require
        require(amount <= IERC20(LXP).balanceOf(msg.sender), "NOT_ENOUGH_LXP");
        claim();  //todo discuss
        _userClaimed[msg.sender] -= amount * _rewardPerLXP;  //todo avoid double calculations
        emit Stake(msg.sender, amount);
        IERC20(LX).safeTransferFrom(msg.sender, address(this), amount);
        ERC20PresetMinterPauser(LXP).burnFrom(msg.sender, amount);
    }

    /// @dev Contract also needs ability to receive yield and claim that yield based on share of contract.
    function shareReward(uint256 amount) external nonReentrant {
        IERC20(LX).safeTransferFrom(msg.sender, address(this), amount);
        _rewardPerLXP += amount / IERC20(LXP).totalSupply();
        emit RewardShared(msg.sender, amount);
    }
}