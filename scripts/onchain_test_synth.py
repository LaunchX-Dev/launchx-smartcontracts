import os
import time

from brownie import accounts, Staking, LaunchX, LaunchXP, SyntheticDelegation, Contract, network


def main():
    if network.chain.id == 56:  # bsc mainnet
        logic_admin = accounts.load('metamask-main')
        launchX = LaunchX.at('0xc43570263e924c8cf721f4b9c72eed1aec4eb7df')
        launchXP = LaunchXP.at('0xea75d0c4e47d875cdd13df4b3019295aeb397e9c')
        SyntheticDelegationProxy = Contract.from_abi(
            "SyntheticDelegation", '0xffcEc11d50e5E047DDfD3292Ce9722a63377eE54', SyntheticDelegation.abi)
    else:
        raise ValueError(f'unknown {network.chain.id=}')

    assert SyntheticDelegationProxy.getRevision.call({'from': logic_admin}) == 1
