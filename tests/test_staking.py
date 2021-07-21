import time

import brownie


def test_time(chain):
    chain.sleep(1)  # bug
    time_before = chain.time()
    chain.sleep(100)
    assert chain.time() - (time_before + 100) < 1


def test_deposit_withdraw(staking_contract, LX, LXP, accounts, chain):
    user = accounts[1]
    deposit_amount = 10**18

    # pre checks
    assert LX.address == staking_contract.getStakingToken()
    assert LXP.address == staking_contract.getStakingSyntheticToken()
    assert staking_contract.getLockStartTimestamp() < staking_contract.getLockEndTimestamp()
    assert staking_contract.getLockStartTimestamp() > chain.time()
    assert staking_contract.getLockEndTimestamp() > chain.time()
    chain.sleep(staking_contract.getLockStartTimestamp() - chain.time() + 10)  # move to the middle of lock period
    assert staking_contract.getLockStartTimestamp() < chain.time()
    assert staking_contract.getLockEndTimestamp() > chain.time()

    assert staking_contract.getNumberOfStakers() == 0

    assert LX.approve(staking_contract.address, deposit_amount, {'from': user}).return_value
    staking_contract.depositToken(LX.address, deposit_amount, {'from': user})

    assert staking_contract.getNumberOfStakers() == 1
    assert staking_contract.getTotalTokenStakedAmount(LX.address) == deposit_amount
    assert staking_contract.getTotalTokenBalanceAmount(LX.address) == deposit_amount
    assert staking_contract.getUserTokenStakedAmount(user, LX.address) == deposit_amount
    assert staking_contract.getUserTokenBalanceAmount(user, LX.address) == deposit_amount
    assert staking_contract.getStakerByIndex(0) == user

    with brownie.reverts("WITHDRAW_BEFORE_END"):
        staking_contract.withdrawToken(LX.address, deposit_amount, {'from': user})

    chain.sleep(staking_contract.getLockEndTimestamp() - chain.time() + 10)  # move out of lock period

    with brownie.reverts("INSUFFICIENT_USER_DEPOSIT"):
        staking_contract.withdrawToken(LX.address, deposit_amount+1, {'from': user})

    staking_contract.withdrawToken(LX.address, deposit_amount, {'from': user})

    assert staking_contract.getNumberOfStakers() == 1
    assert staking_contract.getTotalTokenStakedAmount(LX.address) == deposit_amount
    assert staking_contract.getTotalTokenBalanceAmount(LX.address) == 0
    assert staking_contract.getUserTokenStakedAmount(user, LX.address) == deposit_amount
    assert staking_contract.getUserTokenBalanceAmount(user, LX.address) == 0
    assert staking_contract.getStakerByIndex(0) == user


def test_deposit_emergency_withdraw(staking_contract, LX, LXP, accounts, chain):
    admin = accounts[0]
    user = accounts[1]
    deposit_amount = 10 ** 18

    # pre checks
    assert LX.address == staking_contract.getStakingToken()
    assert LXP.address == staking_contract.getStakingSyntheticToken()
    assert staking_contract.getLockStartTimestamp() < staking_contract.getLockEndTimestamp()
    assert staking_contract.getLockStartTimestamp() > chain.time()
    assert staking_contract.getLockEndTimestamp() > chain.time()
    chain.sleep(staking_contract.getLockStartTimestamp() - chain.time() + 10)  # move to the middle of lock period
    assert staking_contract.getLockStartTimestamp() < chain.time()
    assert staking_contract.getLockEndTimestamp() > chain.time()

    assert staking_contract.getNumberOfStakers() == 0

    assert LX.approve(staking_contract.address, deposit_amount, {'from': user}).return_value
    staking_contract.depositToken(LX.address, deposit_amount, {'from': user})

    assert staking_contract.getNumberOfStakers() == 1
    assert staking_contract.getTotalTokenStakedAmount(LX.address) == deposit_amount
    assert staking_contract.getTotalTokenBalanceAmount(LX.address) == deposit_amount
    assert staking_contract.getUserTokenStakedAmount(user, LX.address) == deposit_amount
    assert staking_contract.getUserTokenBalanceAmount(user, LX.address) == deposit_amount
    assert staking_contract.getStakerByIndex(0) == user


    # note: we do not sleep
    staking_contract.setEmergency({'from': admin})
    with brownie.reverts("IN_EMERGENCY"):
        staking_contract.depositToken(LX.address, deposit_amount, {'from': user})
    with brownie.reverts("IN_EMERGENCY"):
        staking_contract.setEmergency({'from': admin})

    staking_contract.withdrawToken(LX.address, deposit_amount, {'from': user})

    assert staking_contract.getNumberOfStakers() == 1
    assert staking_contract.getTotalTokenStakedAmount(LX.address) == deposit_amount
    assert staking_contract.getTotalTokenBalanceAmount(LX.address) == 0
    assert staking_contract.getUserTokenStakedAmount(user, LX.address) == deposit_amount
    assert staking_contract.getUserTokenBalanceAmount(user, LX.address) == 0
    assert staking_contract.getStakerByIndex(0) == user


def test_failed_receive(staking_contract, accounts):
    with brownie.reverts("DISABLED"):
        accounts[0].transfer(staking_contract.address, "1 ether")
