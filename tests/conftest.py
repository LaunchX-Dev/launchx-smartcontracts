import time

import pytest
from brownie import accounts, Staking, LaunchX, LaunchXP


@pytest.fixture
def staking_token(accounts, pm):
    # token = pm('brownie-mix/token-mix@1.0.0').Token.deploy("Test Staking Token", "STAKING_TEST", 18, 1e21, {'from': accounts[0]})
    token = LaunchX.deploy({'from': accounts[0]})
    for account in accounts[1:]:
        token.transfer(account, 100*1e18, {'from': accounts[0]})
    return token


@pytest.fixture
def staking_sythetic_token(accounts, pm):
    # token = pm('brownie-mix/token-mix@1.0.0').Token.deploy("Test Staking Token", "STAKING_TEST", 18, 1e21, {'from': accounts[0]})
    token = LaunchXP.deploy({'from': accounts[0]})
    for account in accounts[1:]:
        token.transfer(account, 100*1e18, {'from': accounts[0]})
    return token


def build_staking_contract(
        staking_token,
        staking_sythetic_token,
        chain,
):
    chain.sleep(1)  # brownie bug
    start = 365*24*3600 + chain.time()
    end = start + 1000
    contract = Staking.deploy(
        staking_token.address,
        staking_sythetic_token.address,
        start,
        end,
        {'from': accounts[0]},
    )
    return contract


@pytest.fixture()
def staking_contract(staking_token, staking_sythetic_token, chain):
    return build_staking_contract(staking_token=staking_token, staking_sythetic_token=staking_sythetic_token, chain=chain)
