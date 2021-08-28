import time

import pytest
from brownie import accounts, Staking, LaunchX, LaunchXP, SyntheticDelegationMock, Stub


@pytest.fixture
def LX(accounts, pm):
    # token = pm('brownie-mix/token-mix@1.0.0').Token.deploy("Test Staking Token", "STAKING_TEST", 18, 1e21, {'from': accounts[0]})
    token = LaunchX.deploy({'from': accounts[0]})
    for account in accounts[1:]:
        token.transfer(account, 100*1e18, {'from': accounts[0]})
    return token


@pytest.fixture
def LXP(accounts, pm):
    # token = pm('brownie-mix/token-mix@1.0.0').Token.deploy("Test Staking Token", "STAKING_TEST", 18, 1e21, {'from': accounts[0]})
    token = LaunchXP.deploy({'from': accounts[0]})
    for account in accounts[1:]:
        token.transfer(account, 100*1e18, {'from': accounts[0]})
    return token


@pytest.fixture
def sythetic_delegation(accounts, LX, LXP):
    contract = SyntheticDelegationMock.deploy({'from': accounts[0]})
    contract.initialize(LX, LXP, {'from': accounts[0]})
    return contract


@pytest.fixture
def stub(accounts):
    contract = Stub.deploy({'from': accounts[0]})
    return contract


def build_staking_contract(
        LX,
        LXP,
        chain,
):
    chain.sleep(1)  # brownie bug
    start = 365*24*3600 + chain.time()
    end = start + 1000
    contract = Staking.deploy(
        LX.address,
        LXP.address,
        start,
        end,
        {'from': accounts[0]},
    )
    return contract


@pytest.fixture()
def staking_contract(LX, LXP, chain):
    return build_staking_contract(LX=LX, LXP=LXP, chain=chain)
