import os
import time

from brownie import accounts, Staking, LaunchX, LaunchXP


def main():
    admin = accounts.load('nftdev_0')
    staking = Staking.at('0xd48Bea9843ACE352c8e9C0E0F65F89c90b80387a')
    launchX = LaunchX.at('0xE922b6d1386BDe6Eb586bec18F9a4c58D518B0f1')
    launchXP = LaunchXP.at('0x90BC605075335FCdB23d824A0a64Cc311ea071EF')

    assert staking.getStakingToken() == launchX.address
    assert staking.getStakingSyntheticToken() == launchXP.address
    assert time.time() > staking.getLockStartTimestamp()
    assert time.time() < staking.getLockEndTimestamp()

    deposit_amount = 10**18
    launchX.approve(staking.address, deposit_amount, {'from': admin})
    staking.depositToken(launchX.address, deposit_amount, {'from': admin})
    assert staking.getUserTokenBalanceAmount(admin, launchX.address) == deposit_amount