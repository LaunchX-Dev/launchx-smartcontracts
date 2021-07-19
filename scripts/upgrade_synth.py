import time, datetime

from brownie import (
    accounts, web3, Contract,
    Staking,
    LaunchX,
    LaunchXP,
    SyntheticDelegation,
    TransparentUpgradeableProxy,
    network,
)


def main():
    if network.chain.id == 56:  # bsc mainnet
        logic_admin = accounts.load('metamask-main')
        upgrade_admin = accounts.load('nftdev_1')
        launchX = LaunchX.at('0xc43570263e924c8cf721f4b9c72eed1aec4eb7df')
        launchXP = LaunchXP.at('0xea75d0c4e47d875cdd13df4b3019295aeb397e9c')
        SyntheticDelegationProxy_address = '0xffcEc11d50e5E047DDfD3292Ce9722a63377eE54'
        SyntheticDelegationProxy = Contract.from_abi(
            "SyntheticDelegation", SyntheticDelegationProxy_address, SyntheticDelegation.abi)
        SyntheticDelegationUpgradeableProxy = Contract.from_abi(
            "TransparentUpgradeableProxy",
            SyntheticDelegationProxy_address,
            TransparentUpgradeableProxy.abi,
        )
    else:
        raise ValueError(f'unknown {network.chain.id=}')

    synthetic_logic = SyntheticDelegation.deploy({'from': logic_admin})
    SyntheticDelegationUpgradeableProxy.upgradeTo(synthetic_logic, {'from': upgrade_admin})
    assert SyntheticDelegationProxy.getRevision.call({"from": logic_admin}) == 2
