from typing import TypedDict

import brownie


def test_no_balance(LX, LXP, sythetic_delegation, accounts):
    admin = accounts[0]
    user1 = accounts[1]
    amount = 1 * 10**18
    LX.approve(sythetic_delegation.address, amount, {'from': user1})
    with brownie.reverts("not enough LXP on the contract address"):
        sythetic_delegation.stake(amount, {'from': user1})


def test_stake(LX, LXP, sythetic_delegation, accounts):
    admin = accounts[0]
    user1 = accounts[1]
    delegation_balance = 100 * 10**18

    LXP.transfer(sythetic_delegation.address, delegation_balance, {'from': admin})

    amount = 1 * 10**18
    LX.approve(sythetic_delegation.address, amount, {'from': user1})
    sythetic_delegation.stake(amount, {'from': user1})
    assert sythetic_delegation.getUserTotalStake(user1, {'from': user1}) == amount


def test_stake_unstake_fails(LX, LXP, sythetic_delegation, accounts):
    admin = accounts[0]
    user1 = accounts[1]
    delegation_balance = 100 * 10**18

    LXP.transfer(sythetic_delegation.address, delegation_balance, {'from': admin})

    amount = 1 * 10**18
    LX.approve(sythetic_delegation.address, amount, {'from': user1})
    sythetic_delegation.stake(amount, {'from': user1})
    assert sythetic_delegation.getUserTotalStake(user1, {'from': user1}) == amount

    with brownie.reverts("not enough unfrozen LXP in current cycle"):
        sythetic_delegation.unstake(amount, {'from': user1})


def test_stake_unstake_in_the_next_cycle(LX, LXP, sythetic_delegation, accounts, chain, stub):
    chain.sleep(1)
    admin = accounts[0]
    user1 = accounts[1]
    delegation_balance = 100 * 10**18

    LXP.transfer(sythetic_delegation.address, delegation_balance, {'from': admin})

    amount = 1 * 10**18
    LX.approve(sythetic_delegation.address, amount, {'from': user1})
    sythetic_delegation.stake(amount, {'from': user1})
    assert sythetic_delegation.getUserTotalStake(user1, {'from': user1}) == amount

    assert sythetic_delegation.getClaimableRewardOfUserForNow(user1) == 0  # no reward
    LXP.approve(sythetic_delegation.address, amount, {'from': user1})
    assert sythetic_delegation.getUserNextCycleStake(user1) == amount
    assert sythetic_delegation.getUserNextCycleAvailableUnstake(user1) == 0
    sythetic_delegation.requestToUnstakeInTheNextCycle(amount, {'from': user1})
    assert sythetic_delegation.getUserNextCycleStake(user1) == 0
    assert sythetic_delegation.getUserNextCycleAvailableUnstake(user1) == amount

    assert sythetic_delegation.getUserCurrentCycleAvailableUnstake(user1) == 0
    assert sythetic_delegation.getUserNextCycleAvailableUnstake(user1) == amount

    cycle1 = sythetic_delegation.getCurrentCycle()
    time1 = sythetic_delegation.timeFromCycleStart()

    chain.sleep(100)
    stub.inc()  # force new block

    time2 = sythetic_delegation.timeFromCycleStart()
    assert time2 - time1 >= 100

    chain.sleep(14 * 24 * 3600)  # sleep 2 weeks
    stub.inc()  # force new block

    cycle2 = sythetic_delegation.getCurrentCycle()
    assert cycle2 - cycle1 == 1

    assert sythetic_delegation.getUserCurrentCycleAvailableUnstake(user1) == amount
    sythetic_delegation.updateGlobalCache({'from': user1})
    sythetic_delegation.updateUserCache(user1, {'from': user1})

    assert sythetic_delegation.getGlobalCacheCycle() == sythetic_delegation.getCurrentCycle()
    assert sythetic_delegation.getUserCacheCycle(user1) == sythetic_delegation.getCurrentCycle()

    assert sythetic_delegation.getUserCurrentCycleAvailableUnstake(user1) == amount
    assert sythetic_delegation.getUserNextCycleAvailableUnstake(user1) == amount

    sythetic_delegation.unstake(amount, {'from': user1})


class UserProfile(TypedDict):
    currentCycleStake: int
    nextCycleStake: int
    currentCycleAvailableUnstake: int
    nextCycleAvailableUnstake: int
    cacheCycle: int
    currentCycleClaimed: int


def get_profile(sc, user):
    attrs = [
        'currentCycleStake',
        'nextCycleStake',
        'currentCycleAvailableUnstake',
        'nextCycleAvailableUnstake',
        'cacheCycle',
        'currentCycleClaimed',
    ]
    return UserProfile(zip(attrs, sc.getProfile(user)))


def test_reward(LX, LXP, sythetic_delegation, accounts, chain, stub):
    chain.sleep(1)  # brownie bug
    admin = accounts[0]
    user1 = accounts[1]
    user2 = accounts[2]

    cycle = sythetic_delegation.getCurrentCycle()
    assert sythetic_delegation.raw_globalCacheCycle() == 0
    assert get_profile(sythetic_delegation, user1)['cacheCycle'] == 0
    assert get_profile(sythetic_delegation, user2)['cacheCycle'] == 0

    delegation_balance = 100 * 10**18
    LXP.transfer(sythetic_delegation.address, delegation_balance, {'from': admin})

    stake1 = 2 * 10**18
    LX.approve(sythetic_delegation.address, stake1, {'from': user1})
    sythetic_delegation.stake(stake1, {'from': user1})

    assert sythetic_delegation.raw_globalCacheCycle() == cycle  # cache updated
    assert sythetic_delegation.raw_totalCurrentCycleStakeAmount() == 0
    assert sythetic_delegation.raw_totalNextCycleStakeAmount() == stake1

    stake2 = 1 * 10**18
    LX.approve(sythetic_delegation.address, stake2, {'from': user2})
    sythetic_delegation.stake(stake2, {'from': user2})

    assert sythetic_delegation.raw_globalCacheCycle() == cycle  # cache updated
    assert sythetic_delegation.raw_totalCurrentCycleStakeAmount() == 0
    assert sythetic_delegation.raw_totalNextCycleStakeAmount() == stake1 + stake2

    reward_amount = 1 * 10**16

    assert sythetic_delegation.getClaimableRewardOfUserForNow(user1) == 0
    assert sythetic_delegation.getClaimableRewardOfUserForNow(user2) == 0

    with brownie.reverts("SC does not remember past user stake"):
        sythetic_delegation.cycleRewardsOfUser(user1, cycle-1)
    with brownie.reverts("SC does not remember past user stake"):
        sythetic_delegation.cycleRewardsOfUser(user2, cycle-1)
    assert sythetic_delegation.cycleRewardsOfUser(user1, cycle) == 0
    assert sythetic_delegation.cycleRewardsOfUser(user2, cycle) == 0
    assert sythetic_delegation.cycleRewardsOfUser(user1, cycle+1) == 0
    assert sythetic_delegation.cycleRewardsOfUser(user2, cycle+1) == 0

    LX.approve(sythetic_delegation.address, reward_amount, {'from': admin})
    with brownie.reverts("require: cycle > getCurrentCycle()"):
        sythetic_delegation.shareReward(reward_amount, cycle, {'from': admin})
    sythetic_delegation.shareReward(reward_amount, cycle+1, {'from': admin})
    # no reward yet
    assert sythetic_delegation.getClaimableRewardOfUserForNow(user1) == 0
    assert sythetic_delegation.getClaimableRewardOfUserForNow(user2) == 0

    assert sythetic_delegation.getTotalNextCycleStakeAmount() == stake1 + stake2
    assert sythetic_delegation.getTotalCurrentCycleStakeAmount() == 0

    chain.sleep(14 * 24 * 3600)  # sleep 2 weeks
    stub.inc()  # force new block

    assert sythetic_delegation.getTotalNextCycleStakeAmount() == stake1 + stake2
    assert sythetic_delegation.getTotalCurrentCycleStakeAmount() == stake1 + stake2  # before update cache

    with brownie.reverts("SC does not remember past user stake"):
        sythetic_delegation.cycleRewardsOfUser(user1, cycle-1)
    with brownie.reverts("SC does not remember past user stake"):
        sythetic_delegation.cycleRewardsOfUser(user2, cycle-1)
    with brownie.reverts("SC does not remember past user stake"):
        sythetic_delegation.cycleRewardsOfUser(user1, cycle)
    with brownie.reverts("SC does not remember past user stake"):
        sythetic_delegation.cycleRewardsOfUser(user2, cycle)
    assert sythetic_delegation.getCurrentCycle() == cycle + 1
    assert sythetic_delegation.cycleRewardsOfUser(user1, cycle+1) == int(reward_amount * stake1 / (stake1 + stake2))-1  # rounding down
    assert sythetic_delegation.cycleRewardsOfUser(user2, cycle+1) == int(reward_amount * stake2 / (stake1 + stake2))

    profile1 = get_profile(sythetic_delegation, user1)
    profile2 = get_profile(sythetic_delegation, user2)

    # not updated yet
    assert profile1['cacheCycle'] == sythetic_delegation.getCurrentCycle() - 1
    assert profile1['currentCycleStake'] == 0
    assert profile1['nextCycleStake'] == stake1

    # not updated yet
    assert profile2['cacheCycle'] == sythetic_delegation.getCurrentCycle() - 1
    assert profile2['currentCycleStake'] == 0
    assert profile2['nextCycleStake'] == stake2

    assert sythetic_delegation.raw_cycleTotalReward(sythetic_delegation.getCurrentCycle()) == reward_amount

    # tx = sythetic_delegation.getClaimableRewardOfUserForNow2(user1)
    # import pprint
    # pprint.pprint(tx.events['E1'])

    assert sythetic_delegation.getClaimableRewardOfUserForNow(user1) == int(reward_amount * stake1 // (stake1 + stake2))
    assert sythetic_delegation.getClaimableRewardOfUserForNow(user2) == int(reward_amount * stake2 // (stake1 + stake2))

    sythetic_delegation.updateGlobalCache()
    assert sythetic_delegation.raw_cycleTotalReward(sythetic_delegation.getCurrentCycle() - 1) == 0
    assert sythetic_delegation.raw_cycleTotalStaked(sythetic_delegation.getCurrentCycle() - 1) == 0
    assert sythetic_delegation.raw_cycleTotalReward(sythetic_delegation.getCurrentCycle()) == reward_amount
    assert sythetic_delegation.raw_cycleTotalStaked(sythetic_delegation.getCurrentCycle()) == stake1 + stake2
    assert sythetic_delegation.raw_cycleTotalReward(sythetic_delegation.getCurrentCycle()+1) == 0
    assert sythetic_delegation.raw_cycleTotalStaked(sythetic_delegation.getCurrentCycle()+1) == 0

    chain.sleep(14 * 24 * 3600)  # sleep 2 weeks
    stub.inc()  # force new block

    expected_reward1 = int(reward_amount * stake1 // (stake1 + stake2))
    expected_reward2 = int(reward_amount * stake2 // (stake1 + stake2))

    sythetic_delegation.updateGlobalCache()
    assert sythetic_delegation.getClaimableRewardOfUserForNow(user1) == expected_reward1
    assert sythetic_delegation.getClaimableRewardOfUserForNow(user2) == expected_reward2

    # update
    balanceBefore1 = LX.balanceOf(user1)
    balanceBefore2 = LX.balanceOf(user2)
    sythetic_delegation.updateUserCache(user1)
    sythetic_delegation.updateUserCache(user2)
    assert LX.balanceOf(user1) - balanceBefore1 == expected_reward1
    assert LX.balanceOf(user2) - balanceBefore2 == expected_reward2

    assert get_profile(sythetic_delegation, user1)['cacheCycle'] == sythetic_delegation.getCurrentCycle()
    assert get_profile(sythetic_delegation, user2)['cacheCycle'] == sythetic_delegation.getCurrentCycle()
    # reward is transfered because of updateUserCache
    assert sythetic_delegation.getClaimableRewardOfUserForNow(user1) == 0
    assert sythetic_delegation.getClaimableRewardOfUserForNow(user2) == 0

    balanceBefore1 = LX.balanceOf(user1)
    balanceBefore2 = LX.balanceOf(user2)
    sythetic_delegation.claimReward({'from': user1})
    sythetic_delegation.claimReward({'from': user2})
    assert LX.balanceOf(user1) - balanceBefore1 == 0
    assert LX.balanceOf(user2) - balanceBefore2 == 0


# Tests that users can't unstake before staking period, during staking period,
# during staking period after requesting, after staking period more than requested.
def test_illegal_unstaking(LX, LXP, sythetic_delegation, accounts, chain, stub):
    chain.sleep(1)  # brownie bug
    admin = accounts[0]
    user1 = accounts[1]
    user2 = accounts[2]

    init_cycle = sythetic_delegation.getCurrentCycle()

    # provide lp tokens
    delegation_balance = 100 * 10**18
    LXP.transfer(sythetic_delegation.address, delegation_balance, {'from': admin})

    # provide reward for next cycle
    # rewards = [2 * 10**16, 3 * 10**16, 5 * 10**16]
    # LX.approve(sythetic_delegation.address, rewards[0], {'from': admin})
    # sythetic_delegation.shareReward(rewards[0], init_cycle+1, {'from': admin})

    # init user caches
    sythetic_delegation.updateUserCache(user1, {'from': user1})
    sythetic_delegation.updateUserCache(user2, {'from': user2})

    # stake #1 by user1
    stakes1 = [2 * 10**18, 3 * 10**18, 5 * 10**18]
    LX.approve(sythetic_delegation.address, stakes1[0], {'from': user1})
    sythetic_delegation.stake(stakes1[0], {'from': user1})

    assert sythetic_delegation.getTotalCurrentCycleStakeAmount() == 0
    assert sythetic_delegation.getTotalNextCycleStakeAmount() == stakes1[0]
    assert sythetic_delegation.getUserCurrentCycleAvailableUnstake(user1) == 0
    assert sythetic_delegation.getUserCurrentCycleAvailableUnstake(user2) == 0
    assert sythetic_delegation.getUserNextCycleStake(user1) == stakes1[0]
    assert sythetic_delegation.getUserNextCycleStake(user2) == 0
    assert sythetic_delegation.getUserNextCycleAvailableUnstake(user1) == 0
    assert sythetic_delegation.getUserNextCycleAvailableUnstake(user2) == 0

    with brownie.reverts("not enough unfrozen LXP in current cycle"):
        sythetic_delegation.unstake(1, {'from': user1})

    # stake #2 by user2
    stakes2 = [7 * 10**18, 11 * 10**18]
    LX.approve(sythetic_delegation.address, stakes2[0], {'from': user2})
    sythetic_delegation.stake(stakes2[0], {'from': user2})

    assert sythetic_delegation.getTotalCurrentCycleStakeAmount() == 0
    assert sythetic_delegation.getTotalNextCycleStakeAmount() == stakes1[0] + stakes2[0]
    assert sythetic_delegation.getUserCurrentCycleAvailableUnstake(user1) == 0
    assert sythetic_delegation.getUserCurrentCycleAvailableUnstake(user2) == 0
    assert sythetic_delegation.getUserNextCycleStake(user1) == stakes1[0]
    assert sythetic_delegation.getUserNextCycleStake(user2) == stakes2[0]
    assert sythetic_delegation.getUserNextCycleAvailableUnstake(user1) == 0
    assert sythetic_delegation.getUserNextCycleAvailableUnstake(user2) == 0

    with brownie.reverts("not enough unfrozen LXP in current cycle"):
        sythetic_delegation.unstake(1, {'from': user1})
    with brownie.reverts("not enough unfrozen LXP in current cycle"):
        sythetic_delegation.unstake(1, {'from': user2})

    # stake #3 by user1
    LX.approve(sythetic_delegation.address, stakes1[1], {'from': user1})
    sythetic_delegation.stake(stakes1[1], {'from': user1})

    assert sythetic_delegation.getTotalCurrentCycleStakeAmount() == 0
    assert sythetic_delegation.getTotalNextCycleStakeAmount() == stakes1[0] + stakes2[0] + stakes1[1]
    assert sythetic_delegation.getUserCurrentCycleAvailableUnstake(user1) == 0
    assert sythetic_delegation.getUserCurrentCycleAvailableUnstake(user2) == 0
    assert sythetic_delegation.getUserNextCycleStake(user1) == stakes1[0] + stakes1[1]
    assert sythetic_delegation.getUserNextCycleStake(user2) == stakes2[0]
    assert sythetic_delegation.getUserNextCycleAvailableUnstake(user1) == 0
    assert sythetic_delegation.getUserNextCycleAvailableUnstake(user2) == 0

    with brownie.reverts("not enough unfrozen LXP in current cycle"):
        sythetic_delegation.unstake(1, {'from': user1})
    with brownie.reverts("not enough unfrozen LXP in current cycle"):
        sythetic_delegation.unstake(1, {'from': user2})

    # sleep until next cycle
    chain.sleep(14 * 24 * 3600)  # sleep 2 weeks
    stub.inc()  # force new block
    sythetic_delegation.updateGlobalCache()
    sythetic_delegation.updateUserCache(user1, {'from': user1})
    sythetic_delegation.updateUserCache(user2, {'from': user2})
    assert sythetic_delegation.getCurrentCycle() == init_cycle + 1

    assert sythetic_delegation.getTotalCurrentCycleStakeAmount() == stakes1[0] + stakes2[0] + stakes1[1]
    assert sythetic_delegation.getTotalNextCycleStakeAmount() == stakes1[0] + stakes2[0] + stakes1[1]
    assert sythetic_delegation.getUserCurrentCycleAvailableUnstake(user1) == 0
    assert sythetic_delegation.getUserCurrentCycleAvailableUnstake(user2) == 0
    assert sythetic_delegation.getUserNextCycleStake(user1) == stakes1[0] + stakes1[1]
    assert sythetic_delegation.getUserNextCycleStake(user2) == stakes2[0]
    assert sythetic_delegation.getUserNextCycleAvailableUnstake(user1) == 0
    assert sythetic_delegation.getUserNextCycleAvailableUnstake(user2) == 0

    with brownie.reverts("not enough unfrozen LXP in current cycle"):
        sythetic_delegation.unstake(1, {'from': user1})
    with brownie.reverts("not enough unfrozen LXP in current cycle"):
        sythetic_delegation.unstake(1, {'from': user2})

    # sleep 3 more cycles
    chain.sleep(3 * 14 * 24 * 3600)  # sleep 6 weeks
    stub.inc()  # force new block
    sythetic_delegation.updateGlobalCache()
    sythetic_delegation.updateUserCache(user1, {'from': user1})
    sythetic_delegation.updateUserCache(user2, {'from': user2})
    assert sythetic_delegation.getCurrentCycle() == init_cycle + 4

    assert sythetic_delegation.getTotalCurrentCycleStakeAmount() == stakes1[0] + stakes2[0] + stakes1[1]
    assert sythetic_delegation.getTotalNextCycleStakeAmount() == stakes1[0] + stakes2[0] + stakes1[1]
    assert sythetic_delegation.getUserCurrentCycleAvailableUnstake(user1) == 0
    assert sythetic_delegation.getUserCurrentCycleAvailableUnstake(user2) == 0
    assert sythetic_delegation.getUserNextCycleStake(user1) == stakes1[0] + stakes1[1]
    assert sythetic_delegation.getUserNextCycleStake(user2) == stakes2[0]
    assert sythetic_delegation.getUserNextCycleAvailableUnstake(user1) == 0
    assert sythetic_delegation.getUserNextCycleAvailableUnstake(user2) == 0

    with brownie.reverts("not enough unfrozen LXP in current cycle"):
        sythetic_delegation.unstake(1, {'from': user1})
    with brownie.reverts("not enough unfrozen LXP in current cycle"):
        sythetic_delegation.unstake(1, {'from': user2})

    # stake #4 by user2
    LX.approve(sythetic_delegation.address, stakes2[1], {'from': user2})
    sythetic_delegation.stake(stakes2[1], {'from': user2})

    assert sythetic_delegation.getTotalCurrentCycleStakeAmount() == stakes1[0] + stakes2[0] + stakes1[1]
    assert sythetic_delegation.getTotalNextCycleStakeAmount() == stakes1[0] + stakes2[0] + stakes1[1] + stakes2[1]
    assert sythetic_delegation.getUserCurrentCycleAvailableUnstake(user1) == 0
    assert sythetic_delegation.getUserCurrentCycleAvailableUnstake(user2) == 0
    assert sythetic_delegation.getUserNextCycleStake(user1) == stakes1[0] + stakes1[1]
    assert sythetic_delegation.getUserNextCycleStake(user2) == stakes2[0] + stakes2[1]
    assert sythetic_delegation.getUserNextCycleAvailableUnstake(user1) == 0
    assert sythetic_delegation.getUserNextCycleAvailableUnstake(user2) == 0

    with brownie.reverts("not enough unfrozen LXP in current cycle"):
        sythetic_delegation.unstake(1, {'from': user1})
    with brownie.reverts("not enough unfrozen LXP in current cycle"):
        sythetic_delegation.unstake(1, {'from': user2})

    # request to unstake
    LXP.approve(sythetic_delegation.address, 1, {'from': user1})
    sythetic_delegation.requestToUnstakeInTheNextCycle(1, {'from': user1})
    LXP.approve(sythetic_delegation.address, 1, {'from': user2})
    sythetic_delegation.requestToUnstakeInTheNextCycle(1, {'from': user2})

    assert sythetic_delegation.getTotalCurrentCycleStakeAmount() == stakes1[0] + stakes2[0] + stakes1[1]
    assert sythetic_delegation.getTotalNextCycleStakeAmount() == stakes1[0] + stakes2[0] + stakes1[1] + stakes2[1] - 2
    assert sythetic_delegation.getUserCurrentCycleAvailableUnstake(user1) == 0
    assert sythetic_delegation.getUserCurrentCycleAvailableUnstake(user2) == 0
    assert sythetic_delegation.getUserNextCycleStake(user1) == stakes1[0] + stakes1[1] - 1
    assert sythetic_delegation.getUserNextCycleStake(user2) == stakes2[0] + stakes2[1] - 1
    assert sythetic_delegation.getUserNextCycleAvailableUnstake(user1) == 1
    assert sythetic_delegation.getUserNextCycleAvailableUnstake(user2) == 1

    # can't unstake during current period after request
    with brownie.reverts("not enough unfrozen LXP in current cycle"):
        sythetic_delegation.unstake(1, {'from': user1})
    with brownie.reverts("not enough unfrozen LXP in current cycle"):
        sythetic_delegation.unstake(1, {'from': user2})

    # sleep until next cycle
    chain.sleep(14 * 24 * 3600)  # sleep 2 weeks
    stub.inc()  # force new block
    sythetic_delegation.updateGlobalCache()
    sythetic_delegation.updateUserCache(user1, {'from': user1})
    sythetic_delegation.updateUserCache(user2, {'from': user2})
    assert sythetic_delegation.getCurrentCycle() == init_cycle + 5

    assert sythetic_delegation.getTotalCurrentCycleStakeAmount() == stakes1[0] + stakes2[0] + stakes1[1] + stakes2[1] - 2
    assert sythetic_delegation.getTotalNextCycleStakeAmount() == stakes1[0] + stakes2[0] + stakes1[1] + stakes2[1] - 2
    assert sythetic_delegation.getUserCurrentCycleAvailableUnstake(user1) == 1
    assert sythetic_delegation.getUserCurrentCycleAvailableUnstake(user2) == 1
    assert sythetic_delegation.getUserNextCycleStake(user1) == stakes1[0] + stakes1[1] - 1
    assert sythetic_delegation.getUserNextCycleStake(user2) == stakes2[0] + stakes2[1] - 1
    assert sythetic_delegation.getUserNextCycleAvailableUnstake(user1) == 1
    assert sythetic_delegation.getUserNextCycleAvailableUnstake(user2) == 1

    # can't unstake more than requested
    with brownie.reverts("not enough unfrozen LXP in current cycle"):
        sythetic_delegation.unstake(2, {'from': user1})
    with brownie.reverts("not enough unfrozen LXP in current cycle"):
        sythetic_delegation.unstake(2, {'from': user2})

    # can unstake what requested
    sythetic_delegation.unstake(1, {'from': user1})
    sythetic_delegation.unstake(1, {'from': user2})

    assert sythetic_delegation.getTotalCurrentCycleStakeAmount() == stakes1[0] + stakes2[0] + stakes1[1] + stakes2[1] - 2
    assert sythetic_delegation.getTotalNextCycleStakeAmount() == stakes1[0] + stakes2[0] + stakes1[1] + stakes2[1] - 2
    assert sythetic_delegation.getUserCurrentCycleAvailableUnstake(user1) == 0
    assert sythetic_delegation.getUserCurrentCycleAvailableUnstake(user2) == 0
    assert sythetic_delegation.getUserNextCycleStake(user1) == stakes1[0] + stakes1[1] - 1
    assert sythetic_delegation.getUserNextCycleStake(user2) == stakes2[0] + stakes2[1] - 1
    assert sythetic_delegation.getUserNextCycleAvailableUnstake(user1) == 0
    assert sythetic_delegation.getUserNextCycleAvailableUnstake(user2) == 0


def test_request_unstake(LX, LXP, sythetic_delegation, accounts, chain, stub):
    chain.sleep(1)  # brownie bug
    admin = accounts[0]
    user = accounts[1]

    # provide lp tokens
    delegation_balance = 100 * 10**18
    LXP.transfer(sythetic_delegation.address, delegation_balance, {'from': admin})

    # init
    init_cycle = sythetic_delegation.getCurrentCycle()
    sythetic_delegation.updateUserCache(user, {'from': user})

    balance = LXP.balanceOf(user, {'from': user})
    if balance > 0:
        LXP.transfer(admin, balance, {'from': user})
    assert LXP.balanceOf(user, {'from': user}) == 0

    # stake
    stake_amount = 2 * 10**18
    unstake_amount = 1 * 10**18
    LX.approve(sythetic_delegation.address, stake_amount, {'from': user})
    sythetic_delegation.stake(stake_amount, {'from': user})

    assert sythetic_delegation.getUserCurrentCycleAvailableUnstake(user) == 0
    assert sythetic_delegation.getUserNextCycleStake(user) == stake_amount
    assert sythetic_delegation.getUserNextCycleAvailableUnstake(user) == 0

    # can't request more than staked
    assert LXP.balanceOf(user, {'from': user}) == stake_amount
    with brownie.reverts("NOT_ENOUGH_LXP"):
        sythetic_delegation.requestToUnstakeInTheNextCycle(stake_amount + 1, {'from': user})

    # request to unstake
    LXP.approve(sythetic_delegation.address, unstake_amount, {'from': user})
    sythetic_delegation.requestToUnstakeInTheNextCycle(unstake_amount, {'from': user})

    assert sythetic_delegation.getUserCurrentCycleAvailableUnstake(user) == 0
    assert sythetic_delegation.getUserNextCycleStake(user) == stake_amount - unstake_amount
    assert sythetic_delegation.getUserNextCycleAvailableUnstake(user) == unstake_amount

    # can't unstake this cycle
    with brownie.reverts("not enough unfrozen LXP in current cycle"):
        sythetic_delegation.unstake(stake_amount, {'from': user})

    # sleep until next cycle
    chain.sleep(14 * 24 * 3600)  # sleep 2 weeks
    stub.inc()  # force new block
    sythetic_delegation.updateGlobalCache()
    sythetic_delegation.updateUserCache(user, {'from': user})
    assert sythetic_delegation.getCurrentCycle() == init_cycle + 1

    assert sythetic_delegation.getUserCurrentCycleAvailableUnstake(user) == unstake_amount
    assert sythetic_delegation.getUserNextCycleStake(user) == stake_amount - unstake_amount
    assert sythetic_delegation.getUserNextCycleAvailableUnstake(user) == unstake_amount

    # can't unstake more than requested
    with brownie.reverts("not enough unfrozen LXP in current cycle"):
        sythetic_delegation.unstake(unstake_amount + 1, {'from': user})

    # unstake
    sythetic_delegation.unstake(unstake_amount, {'from': user})

    # check
    assert sythetic_delegation.getUserCurrentCycleAvailableUnstake(user) == 0
    assert sythetic_delegation.getUserNextCycleStake(user) == stake_amount - unstake_amount
    assert sythetic_delegation.getUserNextCycleAvailableUnstake(user) == 0

# SyntheticDelegaction contract doesn't support transferring LXP tokens. This test checks that.
def test_transferred_lpx(LX, LXP, sythetic_delegation, accounts, chain, stub):
    chain.sleep(1)  # brownie bug
    admin = accounts[0]
    user1 = accounts[1]
    user2 = accounts[2]

    # provide lp tokens
    delegation_balance = 100 * 10**18
    LXP.transfer(sythetic_delegation.address, delegation_balance, {'from': admin})

    # make sure users initially don't have any LXP
    balance = LXP.balanceOf(user1, {'from': user1})
    if balance > 0:
        LXP.transfer(admin, balance, {'from': user1})
    balance = LXP.balanceOf(user2, {'from': user2})
    if balance > 0:
        LXP.transfer(admin, balance, {'from': user2})
    assert LXP.balanceOf(user1, {'from': user1}) == 0
    assert LXP.balanceOf(user2, {'from': user2}) == 0

    # init
    init_cycle = sythetic_delegation.getCurrentCycle()
    sythetic_delegation.updateUserCache(user1, {'from': user1})
    sythetic_delegation.updateUserCache(user2, {'from': user2})

    # user1 stakes
    stake_amount = 2 * 10**18
    LX.approve(sythetic_delegation.address, stake_amount, {'from': user1})
    sythetic_delegation.stake(stake_amount, {'from': user1})

    assert sythetic_delegation.getUserCurrentCycleAvailableUnstake(user1) == 0
    assert sythetic_delegation.getUserCurrentCycleAvailableUnstake(user2) == 0
    assert sythetic_delegation.getUserNextCycleStake(user1) == stake_amount
    assert sythetic_delegation.getUserNextCycleStake(user2) == 0
    assert sythetic_delegation.getUserNextCycleAvailableUnstake(user1) == 0
    assert sythetic_delegation.getUserNextCycleAvailableUnstake(user2) == 0

    # transfer LXP tokens
    LXP.transfer(user2, stake_amount, {'from': user1})
    assert LXP.balanceOf(user1, {'from': user1}) == 0
    assert LXP.balanceOf(user2, {'from': user2}) == stake_amount

    # sleep until next cycle
    chain.sleep(14 * 24 * 3600)  # sleep 2 weeks
    stub.inc()  # force new block
    sythetic_delegation.updateGlobalCache()
    sythetic_delegation.updateUserCache(user1, {'from': user1})
    sythetic_delegation.updateUserCache(user2, {'from': user2})
    assert sythetic_delegation.getCurrentCycle() == init_cycle + 1

    # user1 can't request or unstake because don't have LXP tokens anymore
    LXP.approve(sythetic_delegation.address, stake_amount, {'from': user1})
    with brownie.reverts("NOT_ENOUGH_LXP"):
        sythetic_delegation.requestToUnstakeInTheNextCycle(stake_amount, {'from': user1})
    with brownie.reverts("not enough unfrozen LXP in current cycle"):
        sythetic_delegation.unstake(stake_amount, {'from': user1})

    # user2 can't request or unstake
    LXP.approve(sythetic_delegation.address, stake_amount, {'from': user2})
    with brownie.reverts("NOT_ENOUGH_STAKED"):
        sythetic_delegation.requestToUnstakeInTheNextCycle(stake_amount, {'from': user2})
    with brownie.reverts("not enough unfrozen LXP in current cycle"):
        sythetic_delegation.unstake(stake_amount, {'from': user2})
