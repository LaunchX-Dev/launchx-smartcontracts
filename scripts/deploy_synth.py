import time, datetime

import brownie
from brownie import (
    accounts, web3, Contract,
    Staking,
    LaunchX,
    LaunchXP,
    SyntheticDelegation,
    TransparentUpgradeableProxy,
)


def main():
    assert brownie.network.chain.id == 56, 'not bsc mainnet'
    logic_admin = accounts.load('metamask-main')
    upgrade_admin = accounts.load('upgradeAdmin')
    launchX_address = '0xc43570263e924c8cf721f4b9c72eed1aec4eb7df'
    launchXP_address = '0xea75d0c4e47d875cdd13df4b3019295aeb397e9c'

    synthetic_logic = SyntheticDelegation.deploy({'from': logic_admin})
    synthetic_init_call = synthetic_logic.initialize.encode_input(launchX_address, launchXP_address)
    synthetic_proxy = TransparentUpgradeableProxy.deploy(
        synthetic_logic.address, upgrade_admin, synthetic_init_call,
        {'from': logic_admin}
    )
    synthetic_upgradeable = Contract.from_abi("SyntheticDelegation", synthetic_proxy.address, SyntheticDelegation.abi)
    assert synthetic_upgradeable.getRevision.call({"from": logic_admin}) == 1
