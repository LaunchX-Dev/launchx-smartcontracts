import time

import brownie


def test_time(chain):
    chain.sleep(1)  # bug
    time_before = chain.time()
    chain.sleep(100)
    assert chain.time() - (time_before + 100) < 1


def test_deposit_withdraw(staking_contract, staking_token, staking_sythetic_token, accounts, chain):
    user = accounts[1]
    deposit_amount = 10**18

    # pre checks
    assert staking_token.address == staking_contract.getStakingToken()
    assert staking_sythetic_token.address == staking_contract.getStakingSyntheticToken()
    assert staking_contract.getLockStartTimestamp() < staking_contract.getLockEndTimestamp()
    assert staking_contract.getLockStartTimestamp() > chain.time()
    assert staking_contract.getLockEndTimestamp() > chain.time()
    chain.sleep(staking_contract.getLockStartTimestamp() - chain.time() + 10)  # move to the middle of lock period
    assert staking_contract.getLockStartTimestamp() < chain.time()
    assert staking_contract.getLockEndTimestamp() > chain.time()

    assert staking_contract.getNumberOfStakers() == 0

    assert staking_token.approve(staking_contract.address, deposit_amount, {'from': user}).return_value
    staking_contract.depositToken(staking_token.address, deposit_amount, {'from': user})

    assert staking_contract.getNumberOfStakers() == 1
    assert staking_contract.getTotalTokenStakedAmount(staking_token.address) == deposit_amount
    assert staking_contract.getTotalTokenBalanceAmount(staking_token.address) == deposit_amount
    assert staking_contract.getUserTokenStakedAmount(user, staking_token.address) == deposit_amount
    assert staking_contract.getUserTokenBalanceAmount(user, staking_token.address) == deposit_amount
    assert staking_contract.getStakerByIndex(0) == user

    with brownie.reverts("WITHDRAW_BEFORE_END"):
        staking_contract.withdrawToken(staking_token.address, deposit_amount, {'from': user})

    chain.sleep(staking_contract.getLockEndTimestamp() - chain.time() + 10)  # move out of lock period

    with brownie.reverts("INSUFFICIENT_USER_DEPOSIT"):
        staking_contract.withdrawToken(staking_token.address, deposit_amount+1, {'from': user})

    staking_contract.withdrawToken(staking_token.address, deposit_amount, {'from': user})

    assert staking_contract.getNumberOfStakers() == 1
    assert staking_contract.getTotalTokenStakedAmount(staking_token.address) == deposit_amount
    assert staking_contract.getTotalTokenBalanceAmount(staking_token.address) == 0
    assert staking_contract.getUserTokenStakedAmount(user, staking_token.address) == deposit_amount
    assert staking_contract.getUserTokenBalanceAmount(user, staking_token.address) == 0
    assert staking_contract.getStakerByIndex(0) == user


def test_deposit_emergency_withdraw(staking_contract, staking_token, staking_sythetic_token, accounts, chain):
    admin = accounts[0]
    user = accounts[1]
    user2 = accounts[2]
    deposit_amount = 10 ** 18

    # pre checks
    assert staking_token.address == staking_contract.getStakingToken()
    assert staking_sythetic_token.address == staking_contract.getStakingSyntheticToken()
    assert staking_contract.getLockStartTimestamp() < staking_contract.getLockEndTimestamp()
    assert staking_contract.getLockStartTimestamp() > chain.time()
    assert staking_contract.getLockEndTimestamp() > chain.time()
    chain.sleep(staking_contract.getLockStartTimestamp() - chain.time() + 10)  # move to the middle of lock period
    assert staking_contract.getLockStartTimestamp() < chain.time()
    assert staking_contract.getLockEndTimestamp() > chain.time()

    assert staking_contract.getNumberOfStakers() == 0

    assert staking_token.approve(staking_contract.address, deposit_amount, {'from': user}).return_value
    staking_contract.depositToken(staking_token.address, deposit_amount, {'from': user})

    assert staking_contract.getNumberOfStakers() == 1
    assert staking_contract.getTotalTokenStakedAmount(staking_token.address) == deposit_amount
    assert staking_contract.getTotalTokenBalanceAmount(staking_token.address) == deposit_amount
    assert staking_contract.getUserTokenStakedAmount(user, staking_token.address) == deposit_amount
    assert staking_contract.getUserTokenBalanceAmount(user, staking_token.address) == deposit_amount
    assert staking_contract.getStakerByIndex(0) == user


    user2_balance_before = staking_token.balanceOf(user2)
    # note: we do not sleep
    staking_contract.emergencyWithdrawal(staking_token.address, user2, deposit_amount, {'from': admin})
    assert staking_token.balanceOf(user2) - user2_balance_before == deposit_amount

    # todo: discuss post-conditions
    # assert staking_contract.getNumberOfStakers() == 1
    # assert staking_contract.getTotalTokenStakedAmount(staking_token.address) == deposit_amount
    # assert staking_contract.getTotalTokenBalanceAmount(staking_token.address) == 0
    # assert staking_contract.getUserTokenStakedAmount(user, staking_token.address) == deposit_amount
    # assert staking_contract.getUserTokenBalanceAmount(user, staking_token.address) == 0
    # assert staking_contract.getStakerByIndex(0) == user
