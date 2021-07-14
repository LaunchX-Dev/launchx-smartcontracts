import time, datetime

from brownie import (
    accounts, web3, Contract,
    Staking,
    LaunchX,
    LaunchXP
)


def main():
    admin = accounts.load('metamask-main')
    # admin = accounts.load('nftdev_0')
    # launchX = LaunchX.deploy({'from': admin})
    # launchXP = LaunchXP.deploy({'from': admin})
    launchX_address = '0xc43570263e924c8cf721f4b9c72eed1aec4eb7df'
    launchXP_address = '0xea75d0c4e47d875cdd13df4b3019295aeb397e9c'
    start_end_list = [
        (datetime.datetime(2021, 7, 14).timestamp(), datetime.datetime(2021, 7, 15).timestamp()),
        (datetime.datetime(2021, 7, 15).timestamp(), datetime.datetime(2021, 7, 16).timestamp()),
        (datetime.datetime(2021, 7, 16).timestamp(), datetime.datetime(2021, 7, 17).timestamp()),
        (datetime.datetime(2021, 7, 17).timestamp(), datetime.datetime(2021, 7, 18).timestamp()),
        (datetime.datetime(2021, 7, 18).timestamp(), datetime.datetime(2021, 7, 19).timestamp()),
    ]
    for start, end in start_end_list:
        staking = Staking.deploy(
            launchX_address,
            launchXP_address,
            start,
            end,
            {'from': admin},
        )
