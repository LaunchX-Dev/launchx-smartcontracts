// SPDX-License-Identifier: unlicensed
pragma solidity ^0.8.0;

/*
The delegation staking smart contract.
The principle of the Synthetic Delegation Contract is quite simple.
User is able to stake the LNCHX tokens in the smart contract in exchange for the LNCHXP tokens.
The user will then be rewarded yields in bi-weekly cycles in LNCHX tokens,
deposited in the smart contract by a centralised authority.

The smart contract shall have a constructor that specifies the addresses of both lnchx and lnchxp token smart contracts.
The smart contract shall be upgradable through Proxy,
so the owner of the smart contract has an option to upgrade it in order to fix possible issues.

The contract will own the totalSupply of the LNCHXP tokens, they will be exchanged for LNCHX at 1:1 ratio at staking,
and received back by the contract on unstaking. So prior to making any staking transaction a transfer
the of totalSupply of the LNCHXP tokens to the synthetic contract shall be made.

In order to stake into smart contract the user will first call the “approve” method of the LNCHX token smart contract,
and then this method of the Synthetic Delegation Contract:

function stake(amount)

The previous “approve” call transaction should have been confirmed by now and should have been called for
the same amount of tokens.

As stake is called and LNCHX is transferred from the caller’s address the same amount of LNCHXP tokens
are transferred to the caller’s address from the synthetic delegation contract.

As the stake is performed the smart contract remembers the total amount staked by user and
the starting cycle (next biweekly cycle) the yield should be rewarded from.
No new stakes can be added by the same address until all yields from previous cycles are claimed by the staker.

The stakes receives no yields from current 2 week cycle. Even if he posts the stake in the first day of the cycle.
The yields will start next cycle for him.

Anybody may deposit the bi-weekly Rewards and assign a cycle this reward should be applied to.
The reward may be assigned to current bi-weekly cycle too.

The following method shall be called when the rewards are deposited into the contract:
function shareReward(amount, cycle).
The “amount” is specified in LNCHX tokens, and the “cycle” shall be the cycle’s
index number that identifies the cycle this reward should be assigned to.
Prior to depositing the LNCHX tokens the operator who makes the reward deposit shall call the approve method of the
LNCHX token contract, allowing the smart contract to withdraw the same amount of from the operator’s wallet.
There should be ability to call this method more than once for the same cycle, so the rewards are added up.

The user may claim pending rewards for past cycles where she participated.
todo: ??? In order to save gas costs, the contract is designed to avoid large for loops.
One solution that was accepted by the team was that a new staking deposit can not be made
until all claimable rewards for the previous cycles have all been claimed.

The claiming of the rewards are done by calling this smart contract method:
function claim().

If there are rewards claimable by the user rewards for all previous cycles will be claimed in one call.
They will be transferred to the user in the same transaction.
The rewards for current cycle can not be claimed,
the user will need to wait for the end of the current cycle to be able to claim the reward.

todo: ??? when to allow reward for cycle index

The rewards claimable for an address can be retrieved via:
todo: claimableAmountOfUser(address)
The contract is also to have other view methods:
todo: totalTokensStaked()
Also a method to get current cycle index:
todo: getCurrentCycle()
And a method that returns rewards for a cycle.
todo: cycleTotalRewards(cycle)
todo: cycleRewardsOfUser(cycle, address)
On to the unstaking.
The unsticking is done in 2 transactions method calls:
todo: requestUnstake(amount)
This method will require the same amount of LNCHXP previously unlocked (approved)
for the contract to transfer from the caller’s address.
Once called, the LNCHXP tokens are transferred back to the Synthetic contract,
and the same amount of LNCHX tokens is reserved for withdrawal at the end of the current staking cycle.

Once the request is submitted, the user will not be awarded any yields beyond the current cycle.
She will need to complete the unstake, and then stake again to be able to get new rewards.
At any time after the cycle end the user can complete the Unstaking Request.
This step should be done by one method call without parameters:

unstake()
This method shall fail if there are any pending reward claims by address. (claimableAmountOfUser(address) > 0)
The frontend must know of any pending withdrawals by calling this method:
pendingUnstakeRequests(address)
*/

import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {ReentrancyGuard} from '@openzeppelin/contracts/security/ReentrancyGuard.sol';
import {SafeERC20} from '@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol';
import {IERC20} from '@openzeppelin/contracts/token/ERC20/IERC20.sol';
import {Initializable} from './Initializable.sol';


/// @title Synthetic Delegation Contract
/// @notice User comes and wants to stake LX tokens to get LXP tokens to gain discounts and/or guaranteed allocations
///   to IDO’s and passive yield, in the form of tokens or cash. Yield is in LX tokens.
/// @notice When tokens are staked, they immediately get locked and user gets synthetic LXP tokens,
///   however, tokens are not given access to yield until next two-week cycle.
contract SyntheticDelegation is ReentrancyGuard, Initializable {  // todo: ownable?
    using SafeERC20 for IERC20;
    uint256 constant FIRST_MONDAY = 24 * 3600 * 4;  // 01.01.1970 was a Thursday, so 24 * 3600 * 4 is the first Monday python: datetime.datetime.fromtimestamp(24 * 3600 * 4).weekday()
    uint256 constant WINDOW = 14 * 24 * 3600;   // 2 weeks
    uint256 constant ACTION_WINDOW = 1 * 3600;  // 1 hour to stake/unstake

//    struct WithdrawOrder {
//        uint256 amount;
//        uint256 lockedTill;
//    }
//    mapping (address => mapping(uint256 => WithdrawOrder)) internal _userWithdrawOrder;

    uint256 public totalCurrentCycleStakeAmount;
    uint256 public totalNextCycleStakeAmount;
    uint256 public globalCacheCycle;
    mapping (uint256 => uint256) public cycleTotalReward;
    mapping (uint256 => uint256) public cycleTotalStaked;
    struct UserProfile {
        uint256 currentCycleStake;
        uint256 nextCycleStake;
        uint256 currentCycleAvailableUnstake;
        uint256 nextCycleAvailableUnstake;
        uint256 cacheCycle;
        uint256 currentCycleClaimed;
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

    function getTotalTokensStaked() view external returns(uint256){
        return totalNextCycleStakeAmount;
    }

    function getUserTotalStake(address user) external view returns(uint256) {
        require(getCurrentCycle() == _userProfile[user].cacheCycle, "update cache please");
        require(getCurrentCycle() == globalCacheCycle, "update cache please");
        return _userProfile[user].nextCycleStake;
    }

    function getUserCurrentCycleAvailableUnstake(address user) external view returns(uint256) {
        require(getCurrentCycle() == _userProfile[user].cacheCycle, "update cache please");
        require(getCurrentCycle() == globalCacheCycle, "update cache please");
        return _userProfile[user].currentCycleAvailableUnstake;
    }

    function getUserCacheCycle(address user) external view returns(uint256) {
        return _userProfile[user].cacheCycle;
    }

    function getGlobalCacheCycle() external view returns(uint256) {
        return globalCacheCycle;
    }

    function cycleRewardsOfUser(uint256 cycle, address user) external view returns(uint256){
        uint256 current = getCurrentCycle();
        UserProfile storage profile = _userProfile[user];
        if (profile.cacheCycle == 0) {
            return 0;
        }
        if (cycle == current) {
            require(profile.cacheCycle == cycle, "update cache please");
            return cycleTotalReward[cycle] * profile.currentCycleStake / cycleTotalStaked[cycle];
        } else if (cycle > current) {
            require(profile.cacheCycle == cycle, "update cache please");
            return cycleTotalReward[cycle] * profile.nextCycleStake / totalNextCycleStakeAmount;
        } else {
            assert(cycle < current);
            revert("SC does not remember past user stake");
        }
    }

    function cycleTotalRewards(uint256 cycle) external view returns(uint256) {
        return cycleTotalReward[cycle];
    }

    function getClaimableRewardOfUser(address user) external view returns(uint256){  //todo tests
        uint256 current = getCurrentCycle();
        UserProfile storage profile = _userProfile[user];
        if (profile.cacheCycle == 0) {
            return 0;
        }
        uint256 reward = 0;
        if (current > profile.cacheCycle) {
            uint256 currentCycleStake = profile.currentCycleStake;
            uint256 nextCycleStake = profile.nextCycleStake;
            uint256 currentCycleClaimed = profile.currentCycleClaimed;
            for (uint256 i = profile.cacheCycle; i < current; i++) {
                if (cycleTotalStaked[i] > 0) {
                    uint256 iReward = (cycleTotalReward[i] * currentCycleStake / cycleTotalStaked[i]
                        - currentCycleClaimed);
                    currentCycleClaimed += iReward;
                    if (iReward > 0) {
                        reward += iReward;
                    }
                }
                currentCycleStake = nextCycleStake;
                currentCycleClaimed = 0;
            }
        }
        return reward;
    }


    // todo cycleTotalRewards(cycle, address)

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

    function updateGlobalCacheCycle() public {
        uint256 current = getCurrentCycle();
        if (globalCacheCycle == 0) {
            emit GlobalCacheUpdated(msg.sender, globalCacheCycle, current);
            globalCacheCycle = current;
            return;
        }
        if (current > globalCacheCycle) {
            emit GlobalCacheUpdated(msg.sender, globalCacheCycle, current);
            for (uint256 i = globalCacheCycle+1; i <= current; i++) {
                cycleTotalStaked[i] = totalNextCycleStakeAmount;
            }
            globalCacheCycle = current;
            totalCurrentCycleStakeAmount = totalNextCycleStakeAmount;
        }
    }

    // todo
//    function updateGlobalCacheCycleLimited(uint256 maxIterations) public {
//        uint256 current = getCurrentCycle();
//        if (current > globalCacheCycle) {
//            emit GlobalCacheUpdated(msg.sender, globalCacheCycle, current);
//            for (uint256 i = globalCacheCycle+1; i < current; i++) {
//                cycleTotalStaked[i] = totalNextCycleStakeAmount;
//            }
//            globalCacheCycle = current;
//            totalCurrentCycleStakeAmount = totalNextCycleStakeAmount;
//        }
//    }

    function updateUserCacheCycle(address user) public {
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
                if (cycleTotalStaked[i] > 0) {
                    uint256 iReward = (cycleTotalReward[i] * profile.currentCycleStake / cycleTotalStaked[i]
                        - profile.currentCycleClaimed);
                    profile.currentCycleClaimed += iReward;
                    if (iReward > 0) {
                        reward += iReward;
                        emit UserCyclePayout(msg.sender, user, i, iReward);
                    }
                }
                profile.cacheCycle = i+1;
                profile.currentCycleStake = profile.nextCycleStake;
                profile.currentCycleAvailableUnstake = profile.nextCycleAvailableUnstake;
                profile.currentCycleClaimed = 0;
            }
            if (reward > 0) {
                IERC20(LX).safeTransfer(user, reward);
            }
        }
    }

    function claimReward() external nonReentrant {
        updateGlobalCacheCycle();  // todo limit for loop here
        updateUserCacheCycle(msg.sender);
    }

    /// @notice Tokens are added every two weeks.
    ///   Users must wait until beginning of a new two-week cycle for tokens to stake.
    function stake(uint256 amount) external nonReentrant {
        require(IERC20(LXP).balanceOf(address(this)) >= amount, "not enough LXP on the contract address");
        updateGlobalCacheCycle();
        updateUserCacheCycle(msg.sender);
        UserProfile storage profile = _userProfile[msg.sender];
        profile.nextCycleStake += amount;
        emit Stake(msg.sender, amount);
        IERC20(LX).safeTransferFrom(msg.sender, address(this), amount);
        IERC20(LXP).safeTransfer(msg.sender, amount);
    }

    function getUserNextCycleStake(address user) external view returns(uint256) {
        uint256 current = getCurrentCycle();
        require(_userProfile[user].cacheCycle == current, "update user cache please");
        return _userProfile[user].nextCycleStake;
    }

    function getUserNextCycleAvailableUnstake(address user) external view returns(uint256) {
        uint256 current = getCurrentCycle();
        require(_userProfile[user].cacheCycle == current, "update user cache please");
        return _userProfile[user].nextCycleAvailableUnstake;
    }

    function requestToUnstakeInTheNextCycle(uint256 amount) external nonReentrant {
        require(amount <= IERC20(LXP).balanceOf(msg.sender), "NOT_ENOUGH_LXP");
        updateGlobalCacheCycle();
        updateUserCacheCycle(msg.sender);
        uint256 possibleUnstakeAmount = _userProfile[msg.sender].nextCycleStake;
        if (possibleUnstakeAmount > 0) {
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
        updateGlobalCacheCycle();
        updateUserCacheCycle(msg.sender);
        require(_userProfile[msg.sender].currentCycleAvailableUnstake >= amount, "not enough unfrozen LXP in current cycle");
        // note that always nextCycleAvailableUnstake >= currentCycleAvailableUnstake, so more require not need
        _userProfile[msg.sender].currentCycleAvailableUnstake -= amount;
        _userProfile[msg.sender].nextCycleAvailableUnstake -= amount;
        emit Unstake(msg.sender, amount);
        IERC20(LX).safeTransfer(msg.sender, amount);
    }

    /// @dev Contract also needs ability to receive yield and claim that yield based on share of contract.
    function shareReward(uint256 amount, uint256 cycle) external nonReentrant {  //todo discuss
        updateGlobalCacheCycle();
        require(cycle >= getCurrentCycle(), "reward for past cycle");  // todo: discuss == current
        IERC20(LX).safeTransferFrom(msg.sender, address(this), amount);
        cycleTotalReward[cycle] += amount;
    }

    function getRevision() pure public returns(uint256) {
        return 2;
    }
}