// SPDX-License-Identifier: unlicensed
pragma solidity 0.8.4;

import {Ownable} from "./Ownable.sol";
import {ReentrancyGuard} from './ReentrancyGuard.sol';
import {SafeERC20} from './SafeERC20.sol';
import {IERC20} from './IERC20.sol';
import {Initializable} from './Initializable.sol';


/// @title Synthetic Delegation Contract
/// @notice User comes and wants to stake LX tokens to get LXP tokens to gain discounts and/or guaranteed allocations
///   to IDO’s and passive yield, in the form of tokens or cash. Yield is in LX tokens.
/// @notice When tokens are staked, they immediately get locked and user gets synthetic LXP tokens,
///   however, tokens are not given access to yield until next two-week cycle.
contract SyntheticDelegation is ReentrancyGuard, Initializable {
    using SafeERC20 for IERC20;
    uint256 constant FIRST_MONDAY = 24 * 3600 * 4;  // 01.01.1970 was a Thursday, so 24 * 3600 * 4 is the first Monday python: datetime.datetime.fromtimestamp(24 * 3600 * 4).weekday()
    uint256 constant WINDOW = 14 * 24 * 3600;   // 2 weeks
    uint256 constant ACTION_WINDOW = 1 * 3600;  // 1 hour to stake/unstake

    uint256 internal _totalCurrentCycleStakeAmount;
    uint256 internal _totalNextCycleStakeAmount;
    uint256 internal _globalCacheCycle;
    mapping (uint256 => uint256) internal _cycleTotalReward;
    mapping (uint256 => uint256) internal _cycleTotalStaked;
    struct UserProfile {
        uint256 currentCycleStake;
        uint256 nextCycleStake;
        uint256 currentCycleAvailableUnstake;
        uint256 nextCycleAvailableUnstake;
        uint256 cacheCycle;
    }

    function getTotalCurrentCycleStakeAmount() external view returns(uint256){
        uint256 current = getCurrentCycle();
        if (_globalCacheCycle < current) {
            return _totalNextCycleStakeAmount;
        } else {
            return _totalCurrentCycleStakeAmount;
        }
    }

    function getTotalNextCycleStakeAmount() external view returns(uint256){
        return _totalNextCycleStakeAmount;
    }

    mapping (address => UserProfile) internal _userProfile;

    address public LX;
    address public LXP;

    event RewardShared(address user, uint256 amount);
    event Stake(address user, uint256 amount);
    event Unstake(address user, uint256 amount);
    event Claim(address user, uint256 amount);
    event GlobalCacheUpdated(address indexed caller, uint256 indexed previousCycle, uint256 indexed currentCycle);
    event UserCacheUpdated(address indexed caller, address indexed user, uint256 previousCycle, uint256 indexed currentCycle);
    event UserCyclePayout(address indexed caller, address indexed user, uint256 indexed cycle, uint256 payout);

    function getUserTotalStake(address user) requireUpdatedGlobalCache requireUpdatedUserCache(user) external view returns(uint256) {
        return _userProfile[user].nextCycleStake;
    }

    function getUserCurrentCycleAvailableUnstake(address user) requireUpdatedUserCache(user) requireUpdatedGlobalCache external view returns(uint256) {
        return _userProfile[user].currentCycleAvailableUnstake;
    }

    function getUserCacheCycle(address user) external view returns(uint256) {
        return _userProfile[user].cacheCycle;
    }

    function getGlobalCacheCycle() external view returns(uint256) {
        return _globalCacheCycle;
    }

    function cycleRewardsOfUser(uint256 cycle, address user) requireUpdatedUserCache(user) external view returns(uint256){
        uint256 current = getCurrentCycle();
        UserProfile storage profile = _userProfile[user];
        if (profile.cacheCycle == 0) {
            return 0;
        }
        if (cycle == current) {
            return _cycleTotalReward[cycle] * profile.currentCycleStake / _cycleTotalStaked[cycle];
        } else if (cycle > current) {
            return _cycleTotalReward[cycle] * profile.nextCycleStake / _totalNextCycleStakeAmount;
        } else {
            assert(cycle < current);
            revert("SC does not remember past user stake");
        }
    }

    function cycleTotalRewards(uint256 cycle) external view returns(uint256) {
        return _cycleTotalReward[cycle];
    }

    function getProfile(address user) external view returns(UserProfile memory){
        return _userProfile[user];
    }

    function getClaimableRewardOfUserForNow(address user) requireUpdatedGlobalCache external view returns(uint256){  //todo tests
        uint256 current = getCurrentCycle();
        UserProfile storage profile = _userProfile[user];
        if (profile.cacheCycle == 0) {
            return 0;
        }
        uint256 reward = 0;
        if (current > profile.cacheCycle) {
            for (uint256 i = profile.cacheCycle; i < current; i++) {
                uint256 cycleStake = (i == profile.cacheCycle) ? profile.currentCycleStake : profile.nextCycleStake;
                if (_cycleTotalStaked[i] > 0) {
                    reward += _cycleTotalReward[i] * cycleStake / _cycleTotalStaked[i];
                }
            }
        }
        return reward;
    }

    function initialize(address _LX, address _LXP) external initializer {
        LX = _LX;
        LXP = _LXP;
    }

    function getCurrentCycle() view public returns(uint256) {
        return (block.timestamp - FIRST_MONDAY) / WINDOW;
    }

    function timeFromCycleStart() view public returns(uint256) {
        return (block.timestamp - FIRST_MONDAY) % WINDOW;
    }

    modifier requireUpdatedGlobalCache() {
        require(getCurrentCycle() == _globalCacheCycle, "update global cache");
        _;
    }

    modifier requireUpdatedUserCache(address user) {
        require(getCurrentCycle() == _userProfile[user].cacheCycle, "update user cache");
        _;
    }

    function updateGlobalCache() public {
        uint256 current = getCurrentCycle();
        if (_globalCacheCycle == 0) {
            emit GlobalCacheUpdated(msg.sender, _globalCacheCycle, current);
            _globalCacheCycle = current;
            return;
        }
        if (current > _globalCacheCycle) {
            emit GlobalCacheUpdated(msg.sender, _globalCacheCycle, current);
            for (uint256 i = _globalCacheCycle+1; i <= current; i++) {
                _cycleTotalStaked[i] = _totalNextCycleStakeAmount;
            }
            _globalCacheCycle = current;
            _totalCurrentCycleStakeAmount = _totalNextCycleStakeAmount;
        }
    }

    // todo
//    function updateGlobalCacheCycleLimited(uint256 maxIterations) public {
//        uint256 current = getCurrentCycle();
//        if (current > _globalCacheCycle) {
//            emit GlobalCacheUpdated(msg.sender, _globalCacheCycle, current);
//            for (uint256 i = _globalCacheCycle+1; i < current; i++) {
//                _cycleTotalStaked[i] = _totalNextCycleStakeAmount;
//            }
//            _globalCacheCycle = current;
//            _totalCurrentCycleStakeAmount = _totalNextCycleStakeAmount;
//        }
//    }

    function updateUserCache(address user) public {
        uint256 current = getCurrentCycle();
        UserProfile storage profile = _userProfile[user];
        if (profile.cacheCycle == 0) {
            emit UserCacheUpdated(msg.sender, user, profile.cacheCycle, current);
            profile.cacheCycle = current;
            return;
        }
        if (current > profile.cacheCycle) {
            emit UserCacheUpdated(msg.sender, user, profile.cacheCycle, current);
            uint256 reward;
            for (uint256 i = profile.cacheCycle; i < current; i++) {
                if (_cycleTotalStaked[i] > 0) {
                    uint256 cycleStaked = (i == profile.cacheCycle) ? profile.currentCycleStake : profile.nextCycleStake;
                    uint256 iReward = _cycleTotalReward[i] * cycleStaked / _cycleTotalStaked[i];
                    if (iReward > 0) {
                        reward += iReward;
                        emit UserCyclePayout(msg.sender, user, i, iReward);
                    }
                }  
            }
            profile.cacheCycle = current;
            profile.currentCycleStake = profile.nextCycleStake;
            profile.currentCycleAvailableUnstake = profile.nextCycleAvailableUnstake;
            if (reward > 0) {
                IERC20(LX).safeTransfer(user, reward);
            }
        }
    }

    function claimReward() external nonReentrant {
        updateGlobalCache();  // todo limit for loop here
        updateUserCache(msg.sender);
    }

    /// @notice Tokens are added every two weeks.
    ///   Users must wait until beginning of a new two-week cycle for tokens to stake.
    function stake(uint256 amount) external nonReentrant {
        require(IERC20(LXP).balanceOf(address(this)) >= amount, "not enough LXP on the contract address");
        updateGlobalCache();
        updateUserCache(msg.sender);
        UserProfile storage profile = _userProfile[msg.sender];
        profile.nextCycleStake += amount;
        _totalNextCycleStakeAmount += amount;
        emit Stake(msg.sender, amount);
        IERC20(LX).safeTransferFrom(msg.sender, address(this), amount);
        IERC20(LXP).safeTransfer(msg.sender, amount);
    }

    function getUserNextCycleStake(address user) requireUpdatedUserCache(user) external view returns(uint256) {
        return _userProfile[user].nextCycleStake;
    }

    function getUserNextCycleAvailableUnstake(address user) requireUpdatedUserCache(user) external view returns(uint256) {
        return _userProfile[user].nextCycleAvailableUnstake;
    }

    /// @notice A user can't request and unstake more than staked from their address by transferring LXP tokens.
    function requestToUnstakeInTheNextCycle(uint256 amount) external nonReentrant {
        require(amount <= IERC20(LXP).balanceOf(msg.sender), "NOT_ENOUGH_LXP");
        updateGlobalCache();
        updateUserCache(msg.sender);
        uint256 possibleUnstakeAmount = _userProfile[msg.sender].nextCycleStake;
        require(amount <= possibleUnstakeAmount, "NOT_ENOUGH_STAKED");
        if (possibleUnstakeAmount > 0) {
            _totalNextCycleStakeAmount -= amount;
            _userProfile[msg.sender].nextCycleAvailableUnstake += amount;
            _userProfile[msg.sender].nextCycleStake -= amount;
            emit Claim(msg.sender, amount);
            IERC20(LXP).safeTransferFrom(msg.sender, address(this), amount);
        }
    }

    function availableUnstake(address user) external view returns(uint256){
        return _userProfile[user].currentCycleAvailableUnstake;
    }

    function pendingUnstakeRequests(address user) external view returns(uint256 pendingUnstake){
        pendingUnstake = _userProfile[user].currentCycleAvailableUnstake -
            _userProfile[user].nextCycleAvailableUnstake;
    }

    /// @notice When user decides to withdraw, they do not receive tokens until end of two-week delegation cycle,
    ///   but they still need synthetic tokens in wallet to burn to contract.
    function unstake(uint256 amount) external nonReentrant {
        updateGlobalCache();
        updateUserCache(msg.sender);
        require(_userProfile[msg.sender].currentCycleAvailableUnstake >= amount, "not enough unfrozen LXP in current cycle");
        // note that always nextCycleAvailableUnstake >= currentCycleAvailableUnstake, so more require not need
        _userProfile[msg.sender].currentCycleAvailableUnstake -= amount;
        _userProfile[msg.sender].nextCycleAvailableUnstake -= amount;
        emit Unstake(msg.sender, amount);
        IERC20(LX).safeTransfer(msg.sender, amount);
    }

    /// @dev Contract also needs ability to receive yield and claim that yield based on share of contract.
    function shareReward(uint256 amount, uint256 cycle) external nonReentrant {  //todo discuss
        updateGlobalCache();
        require(cycle > getCurrentCycle(), "require: cycle > getCurrentCycle()");  // todo: discuss == current
        IERC20(LX).safeTransferFrom(msg.sender, address(this), amount);
        _cycleTotalReward[cycle] += amount;
    }

    function getRevision() pure public returns(uint256) {
        return 2;
    }
}