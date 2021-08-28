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

    with brownie.reverts("update user cache"):
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
    attrs = ['currentCycleStake',
    'nextCycleStake',
    'currentCycleAvailableUnstake',
    'nextCycleAvailableUnstake',
    'cacheCycle',
    'currentCycleClaimed',]
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

    profile1 = get_profile(sythetic_delegation, user1)
    profile2 = get_profile(sythetic_delegation, user2)

    # not updated yet
    assert profile1['cacheCycle'] == sythetic_delegation.getCurrentCycle() - 1
    assert profile1['currentCycleStake'] == 0
    assert profile1['nextCycleStake'] == stake1

    assert sythetic_delegation.raw_cycleTotalReward(sythetic_delegation.getCurrentCycle()) == reward_amount

    with brownie.reverts("update global cache"):
        assert sythetic_delegation.getClaimableRewardOfUserForNow(user1) == int(reward_amount * stake1 / (stake1 + stake2))
    with brownie.reverts("update global cache"):
        assert sythetic_delegation.getClaimableRewardOfUserForNow(user2) == int(reward_amount * stake1 / (stake1 + stake2))

    sythetic_delegation.updateGlobalCache()
    assert sythetic_delegation.raw_cycleTotalReward(sythetic_delegation.getCurrentCycle() - 1) == 0
    assert sythetic_delegation.raw_cycleTotalStaked(sythetic_delegation.getCurrentCycle() - 1) == 0
    assert sythetic_delegation.raw_cycleTotalReward(sythetic_delegation.getCurrentCycle()) == reward_amount
    assert sythetic_delegation.raw_cycleTotalStaked(sythetic_delegation.getCurrentCycle()) == stake1 + stake2
    assert sythetic_delegation.raw_cycleTotalReward(sythetic_delegation.getCurrentCycle()+1) == 0
    assert sythetic_delegation.raw_cycleTotalStaked(sythetic_delegation.getCurrentCycle()+1) == 0

    assert sythetic_delegation.getClaimableRewardOfUserForNow(user1) == 0
    assert sythetic_delegation.getClaimableRewardOfUserForNow(user2) == 0

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
