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

    assert sythetic_delegation.getClaimableRewardOfUser(user1) == 0  # no reward
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

    with brownie.reverts("update cache please"):
        assert sythetic_delegation.getUserCurrentCycleAvailableUnstake(user1) == amount

    sythetic_delegation.updateGlobalCacheCycle({'from': user1})
    sythetic_delegation.updateUserCacheCycle(user1, {'from': user1})

    assert sythetic_delegation.getGlobalCacheCycle() == sythetic_delegation.getCurrentCycle()
    assert sythetic_delegation.getUserCacheCycle(user1) == sythetic_delegation.getCurrentCycle()

    assert sythetic_delegation.getUserCurrentCycleAvailableUnstake(user1) == amount
    assert sythetic_delegation.getUserNextCycleAvailableUnstake(user1) == amount

    sythetic_delegation.unstake(amount, {'from': user1})


# todo test rewards
