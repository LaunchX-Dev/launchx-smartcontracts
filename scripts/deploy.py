import time

from brownie import (
    accounts, web3, Contract,
    Staking,
    LaunchX,
    LaunchXP
)


def main():
    admin = accounts.load('nftdev_0')
    launchX = LaunchX.deploy({'from': admin})
    launchXP = LaunchXP.deploy({'from': admin})
    staking = Staking.deploy(
        launchX.address,
        launchXP.address,
        int(time.time()),
        int(time.time()+100*365*24*3600),  # staking allowed forever
        {'from': admin},
    )
