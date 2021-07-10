import time

import brownie


def test_time(chain):
    chain.sleep(1)  # bug
    time_before = chain.time()
    chain.sleep(100)
    assert chain.time() - (time_before + 100) < 1


def test_deposit_share_claim(staking_contract, staking_token, staking_sythetic_token, accounts, chain):
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


    assert staking_token.approve(staking_contract.address, deposit_amount, {'from': user}).return_value
    staking_contract.depositToken(staking_token.address, deposit_amount, {'from': user})

    chain.sleep(staking_contract.getLockEndTimestamp() - chain.time() + 10)  # move out of lock period
    staking_contract.withdrawToken(staking_token.address, deposit_amount, {'from': user})
