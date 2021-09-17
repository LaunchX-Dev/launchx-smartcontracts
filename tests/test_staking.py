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
    assert staking_contract.getEmergency() == False
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
    assert staking_contract.getEmergency() == True
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

def test_multiple_stakers(staking_contract, LX, LXP, accounts, chain):
    user1 = accounts[1]
    user2 = accounts[2]
    user3 = accounts[3]
    deposit_amount_1 = 2**18
    deposit_amount_2 = 3**18
    deposit_amount_3 = 5**18

    # todo: ...

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

    # deposit by user1
    assert LX.approve(staking_contract.address, deposit_amount_1, {'from': user1}).return_value
    staking_contract.depositToken(LX.address, deposit_amount_1, {'from': user1})

    assert staking_contract.getNumberOfStakers() == 1
    assert staking_contract.getTotalTokenStakedAmount(LX.address) == deposit_amount_1
    assert staking_contract.getTotalTokenBalanceAmount(LX.address) == deposit_amount_1
    assert staking_contract.getUserTokenStakedAmount(user1, LX.address) == deposit_amount_1
    assert staking_contract.getUserTokenBalanceAmount(user1, LX.address) == deposit_amount_1
    assert staking_contract.getUserTokenStakedAmount(user2, LX.address) == 0
    assert staking_contract.getUserTokenBalanceAmount(user2, LX.address) == 0
    assert staking_contract.getUserTokenStakedAmount(user3, LX.address) == 0
    assert staking_contract.getUserTokenBalanceAmount(user3, LX.address) == 0
    assert staking_contract.getStakerByIndex(0) == user1

    # deposit by user2
    assert LX.approve(staking_contract.address, deposit_amount_2, {'from': user2}).return_value
    staking_contract.depositToken(LX.address, deposit_amount_2, {'from': user2})

    assert staking_contract.getNumberOfStakers() == 2
    assert staking_contract.getTotalTokenStakedAmount(LX.address) == deposit_amount_1 + deposit_amount_2
    assert staking_contract.getTotalTokenBalanceAmount(LX.address) == deposit_amount_1 + deposit_amount_2
    assert staking_contract.getUserTokenStakedAmount(user1, LX.address) == deposit_amount_1
    assert staking_contract.getUserTokenBalanceAmount(user1, LX.address) == deposit_amount_1
    assert staking_contract.getUserTokenStakedAmount(user2, LX.address) == deposit_amount_2
    assert staking_contract.getUserTokenBalanceAmount(user2, LX.address) == deposit_amount_2
    assert staking_contract.getUserTokenStakedAmount(user3, LX.address) == 0
    assert staking_contract.getUserTokenBalanceAmount(user3, LX.address) == 0
    assert staking_contract.getStakerByIndex(1) == user2

    # deposit by user3
    assert LX.approve(staking_contract.address, deposit_amount_3, {'from': user3}).return_value
    staking_contract.depositToken(LX.address, deposit_amount_3, {'from': user3})

    assert staking_contract.getNumberOfStakers() == 3
    assert staking_contract.getTotalTokenStakedAmount(LX.address) == deposit_amount_1 + deposit_amount_2 + deposit_amount_3
    assert staking_contract.getTotalTokenBalanceAmount(LX.address) == deposit_amount_1 + deposit_amount_2 + deposit_amount_3
    assert staking_contract.getUserTokenStakedAmount(user1, LX.address) == deposit_amount_1
    assert staking_contract.getUserTokenBalanceAmount(user1, LX.address) == deposit_amount_1
    assert staking_contract.getUserTokenStakedAmount(user2, LX.address) == deposit_amount_2
    assert staking_contract.getUserTokenBalanceAmount(user2, LX.address) == deposit_amount_2
    assert staking_contract.getUserTokenStakedAmount(user3, LX.address) == deposit_amount_3
    assert staking_contract.getUserTokenBalanceAmount(user3, LX.address) == deposit_amount_3
    assert staking_contract.getStakerByIndex(2) == user3

    # move out of lock period
    chain.sleep(staking_contract.getLockEndTimestamp() - chain.time() + 10)

    # withdraw by user1
    staking_contract.withdrawToken(LX.address, deposit_amount_1, {'from': user1})

    assert staking_contract.getNumberOfStakers() == 3
    assert staking_contract.getTotalTokenStakedAmount(LX.address) == deposit_amount_1 + deposit_amount_2 + deposit_amount_3
    assert staking_contract.getTotalTokenBalanceAmount(LX.address) == deposit_amount_2 + deposit_amount_3
    assert staking_contract.getUserTokenStakedAmount(user1, LX.address) == deposit_amount_1
    assert staking_contract.getUserTokenBalanceAmount(user1, LX.address) == 0
    assert staking_contract.getUserTokenStakedAmount(user2, LX.address) == deposit_amount_2
    assert staking_contract.getUserTokenBalanceAmount(user2, LX.address) == deposit_amount_2
    assert staking_contract.getUserTokenStakedAmount(user3, LX.address) == deposit_amount_3
    assert staking_contract.getUserTokenBalanceAmount(user3, LX.address) == deposit_amount_3

    # withdraw by user2
    staking_contract.withdrawToken(LX.address, deposit_amount_2, {'from': user2})

    assert staking_contract.getNumberOfStakers() == 3
    assert staking_contract.getTotalTokenStakedAmount(LX.address) == deposit_amount_1 + deposit_amount_2 + deposit_amount_3
    assert staking_contract.getTotalTokenBalanceAmount(LX.address) == deposit_amount_3
    assert staking_contract.getUserTokenStakedAmount(user1, LX.address) == deposit_amount_1
    assert staking_contract.getUserTokenBalanceAmount(user1, LX.address) == 0
    assert staking_contract.getUserTokenStakedAmount(user2, LX.address) == deposit_amount_2
    assert staking_contract.getUserTokenBalanceAmount(user2, LX.address) == 0
    assert staking_contract.getUserTokenStakedAmount(user3, LX.address) == deposit_amount_3
    assert staking_contract.getUserTokenBalanceAmount(user3, LX.address) == deposit_amount_3

    # withdraw by user3
    staking_contract.withdrawToken(LX.address, deposit_amount_3, {'from': user3})

    assert staking_contract.getNumberOfStakers() == 3
    assert staking_contract.getTotalTokenStakedAmount(LX.address) == deposit_amount_1 + deposit_amount_2 + deposit_amount_3
    assert staking_contract.getTotalTokenBalanceAmount(LX.address) == 0
    assert staking_contract.getUserTokenStakedAmount(user1, LX.address) == deposit_amount_1
    assert staking_contract.getUserTokenBalanceAmount(user1, LX.address) == 0
    assert staking_contract.getUserTokenStakedAmount(user2, LX.address) == deposit_amount_2
    assert staking_contract.getUserTokenBalanceAmount(user2, LX.address) == 0
    assert staking_contract.getUserTokenStakedAmount(user3, LX.address) == deposit_amount_3
    assert staking_contract.getUserTokenBalanceAmount(user3, LX.address) == 0

    with brownie.reverts("INSUFFICIENT_USER_DEPOSIT"):
        staking_contract.withdrawToken(LX.address, 1, {'from': user1})
    with brownie.reverts("INSUFFICIENT_USER_DEPOSIT"):
        staking_contract.withdrawToken(LX.address, 1, {'from': user2})
    with brownie.reverts("INSUFFICIENT_USER_DEPOSIT"):
        staking_contract.withdrawToken(LX.address, 1, {'from': user3})


def test_deposit_fails_out_of_lock_period(staking_contract, LX, accounts, chain):
    user = accounts[1]
    deposit_amount = 10 ** 18

    assert staking_contract.getLockStartTimestamp() < staking_contract.getLockEndTimestamp()
    assert staking_contract.getLockStartTimestamp() > chain.time()

    with brownie.reverts("DEPOSIT_BEFORE_START"):
        staking_contract.depositToken(LX.address, deposit_amount, {'from': user})

    chain.sleep(staking_contract.getLockEndTimestamp() - chain.time() + 10) # move after the lock period
    assert staking_contract.getLockEndTimestamp() < chain.time()

    with brownie.reverts("DEPOSIT_AFTER_END"):
        staking_contract.depositToken(LX.address, deposit_amount, {'from': user})

def test_reverts_on_zero_amount(staking_contract, LX, accounts, chain):
    user = accounts[1]
    amount = 0

    chain.sleep(staking_contract.getLockStartTimestamp() - chain.time() + 10) # move to the middle of lock period
    assert staking_contract.getLockStartTimestamp() < chain.time()
    assert staking_contract.getLockEndTimestamp() > chain.time()

    with brownie.reverts("ZERO_AMOUNT"):
        staking_contract.depositToken(LX.address, amount, {'from': user})

    chain.sleep(staking_contract.getLockEndTimestamp() - chain.time() + 10) # move after the lock period
    assert staking_contract.getLockStartTimestamp() < chain.time()
    assert staking_contract.getLockEndTimestamp() < chain.time()

    with brownie.reverts("ZERO_AMOUNT"):
        staking_contract.withdrawToken(LX.address, amount, {'from': user})

def test_only_staking_token(staking_contract, LX, LXP, accounts, chain):
    user = accounts[1]
    lx_deposit_amount = 10 ** 18
    lxp_deposit_amount = 5 ** 18
    non_staking_token = accounts[0] # any address that's not LX or LXP

    assert staking_contract.getTotalTokenStakedAmount(LX.address, {'from': user}) == 0
    assert staking_contract.getTotalTokenStakedAmount(LXP.address, {'from': user}) == 0
    with brownie.reverts("NOT_STAKING_TOKEN"):
        staking_contract.getTotalTokenStakedAmount(non_staking_token, {'from': user})

    assert staking_contract.getTotalTokenBalanceAmount(LX.address, {'from': user}) == 0
    assert staking_contract.getTotalTokenBalanceAmount(LXP.address, {'from': user}) == 0
    with brownie.reverts("NOT_STAKING_TOKEN"):
        staking_contract.getTotalTokenBalanceAmount(non_staking_token, {'from': user})

    assert staking_contract.getUserTokenStakedAmount(user, LX.address, {'from': user}) == 0
    assert staking_contract.getUserTokenStakedAmount(user, LXP.address, {'from': user}) == 0
    with brownie.reverts("NOT_STAKING_TOKEN"):
        staking_contract.getUserTokenStakedAmount(user, non_staking_token, {'from': user})

    assert staking_contract.getUserTokenBalanceAmount(user, LX.address, {'from': user}) == 0
    assert staking_contract.getUserTokenBalanceAmount(user, LXP.address, {'from': user}) == 0
    with brownie.reverts("NOT_STAKING_TOKEN"):
        staking_contract.getUserTokenBalanceAmount(user, non_staking_token, {'from': user})

    # deposit
    chain.sleep(staking_contract.getLockStartTimestamp() - chain.time() + 10) # move to the middle of lock period
    assert staking_contract.getLockStartTimestamp() < chain.time()
    assert staking_contract.getLockEndTimestamp() > chain.time()
    
    with brownie.reverts("NOT_STAKING_TOKEN"):
        staking_contract.depositToken(non_staking_token, lx_deposit_amount, {'from': user})

    assert LX.approve(staking_contract.address, lx_deposit_amount, {'from': user}).return_value
    staking_contract.depositToken(LX.address, lx_deposit_amount, {'from': user})
    assert staking_contract.getUserTokenBalanceAmount(user, LX.address) == lx_deposit_amount

    assert LXP.approve(staking_contract.address, lxp_deposit_amount, {'from': user}).return_value
    staking_contract.depositToken(LXP.address, lxp_deposit_amount, {'from': user})
    assert staking_contract.getUserTokenBalanceAmount(user, LXP.address) == lxp_deposit_amount

    # withdraw
    chain.sleep(staking_contract.getLockEndTimestamp() - chain.time() + 10) # move after the lock period
    assert staking_contract.getLockStartTimestamp() < chain.time()
    assert staking_contract.getLockEndTimestamp() < chain.time()

    with brownie.reverts("NOT_STAKING_TOKEN"):
        staking_contract.withdrawToken(non_staking_token, lx_deposit_amount, {'from': user})

    staking_contract.withdrawToken(LX.address, lx_deposit_amount, {'from': user})
    assert staking_contract.getUserTokenBalanceAmount(user, LX.address) == 0

    staking_contract.withdrawToken(LXP.address, lxp_deposit_amount, {'from': user})
    assert staking_contract.getUserTokenBalanceAmount(user, LXP.address) == 0