# launchx-smartcontracts
smart contracts of LaunchX Finance

## Compile

```bash
brownie pm install "OpenZeppelin/openzeppelin-contracts@4.1.0"
brownie compile
```

## Deploy

### bsc testnet
```bash
brownie networks add live bsc-testnet host=https://data-seed-prebsc-1-s1.binance.org:8545/ chainid=97 explorer=https://api-testnet.bscscan.com/api

brownie run deploy.py --network bsc-testnet
```

### bsc mainnet
```bash
brownie networks add live bsc-mainnet host=https://bsc-dataseed.binance.org/ chainid=56 explorer=https://api.bscscan.com/api

brownie run deploy.py --network bsc-mainnet

brownie run deploy_synth.py --network bsc-mainnet

brownie run upgrade_synth.py --network bsc-mainnet
```

## Test

### Local
```bash
brownie test
```

### On TestNet

```bash
brownie run make_tx.py --network bsc-testnet

Running 'scripts/make_tx.py::main'...
Enter the password to unlock this account: 
Transaction sent: 0x8d4232b46b65a01b5436e4d5963c2319db317a8abe32f1871bf5225e848cc0ac
  Gas price: 10.0 gwei   Gas limit: 27379   Nonce: 810
  LaunchX.approve confirmed - Block: 10465092   Gas used: 24890 (90.91%)

Transaction sent: 0x91992f785474310712bc973c09ee15afb298c396aa31124448df2d16c34ffa3d
  Gas price: 10.0 gwei   Gas limit: 181291   Nonce: 811
  Staking.depositToken confirmed - Block: 10465094   Gas used: 144120 (79.50%)
```



## Deployments
### BSC MainNet
```python
launchX_address = '0xc43570263e924c8cf721f4b9c72eed1aec4eb7df'
launchXP_address = '0xea75d0c4e47d875cdd13df4b3019295aeb397e9c'
# todo: staking  
```
