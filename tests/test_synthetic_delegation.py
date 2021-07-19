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

    with brownie.reverts("not enough unfrozen LXP in current period"):
        sythetic_delegation.unstake(amount, {'from': user1})


def test_stake_unstake_in_the_next_period(LX, LXP, sythetic_delegation, accounts, chain, stub):
    chain.sleep(1)
    admin = accounts[0]
    user1 = accounts[1]
    delegation_balance = 100 * 10**18

    LXP.transfer(sythetic_delegation.address, delegation_balance, {'from': admin})

    amount = 1 * 10**18
    LX.approve(sythetic_delegation.address, amount, {'from': user1})
    sythetic_delegation.stake(amount, {'from': user1})
    assert sythetic_delegation.getUserTotalStake(user1, {'from': user1}) == amount

    LXP.approve(sythetic_delegation.address, amount, {'from': user1})
    sythetic_delegation.claimToUnstakeInNextPeriod(amount, {'from': user1})

    assert sythetic_delegation.getUserCurrentPeriodAvailableUnstake(user1) == 0
    assert sythetic_delegation.getUserNextPeriodAvailableUnstake(user1) == amount

    index1 = sythetic_delegation.getCurrentPeriodIndex()
    time1 = sythetic_delegation.timeFromPeriodStart()

    chain.sleep(100)
    stub.inc()  # force new block

    time2 = sythetic_delegation.timeFromPeriodStart()
    assert time2 - time1 >= 100

    chain.sleep(14 * 24 * 3600)  # sleep 2 weeks
    stub.inc()  # force new block

    index2 = sythetic_delegation.getCurrentPeriodIndex()
    assert index2 - index1 == 1

    with brownie.reverts("update cache please"):
        assert sythetic_delegation.getUserCurrentPeriodAvailableUnstake(user1) == amount

    sythetic_delegation.updateGlobalCachePeriod({'from': user1})
    sythetic_delegation.updateUserCachePeriod(user1, {'from': user1})

    assert sythetic_delegation.getGlobalCachePeriod() == sythetic_delegation.getCurrentPeriodIndex()
    assert sythetic_delegation.getUserCachePeriod(user1) == sythetic_delegation.getCurrentPeriodIndex()

    assert sythetic_delegation.getUserCurrentPeriodAvailableUnstake(user1) == amount
    assert sythetic_delegation.getUserNextPeriodAvailableUnstake(user1) == amount

    sythetic_delegation.unstake(amount, {'from': user1})
