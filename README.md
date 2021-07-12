# launchx-smartcontracts
smart contracts of LaunchX Finance

## Compile

```bash
brownie pm install "OpenZeppelin/openzeppelin-contracts@4.1.0"
brownie compile
```

## Deploy

```bash
brownie networks add live bsc-testnet host=https://data-seed-prebsc-1-s1.binance.org:8545/ chainid=97 explorer=https://api-testnet.bscscan.com/api

brownie run deploy.py --network bsc-testnet
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
### 2021-07-10
```bash
v@vpc:~/PycharmProjects/igor/launchx-smartcontracts$ brownie run deploy.py --network bsc-testnet
Brownie v1.13.1 - Python development framework for Ethereum

LaunchxSmartcontractsProject is the active project.

Running 'scripts/deploy.py::main'...
Enter the password to unlock this account: 
Transaction sent: 0x4dc03acfb9ca1f0339a4b149c01d36008194b7c85da04cdc72682a01d2d09b36
  Gas price: 10.0 gwei   Gas limit: 647859   Nonce: 806
  LaunchX.constructor confirmed - Block: 10464960   Gas used: 588963 (90.91%)
  LaunchX deployed at: 0xE922b6d1386BDe6Eb586bec18F9a4c58D518B0f1

Transaction sent: 0x38d6fa243b14def53ed8ffdaf0ddeec6130e49008fb8489a6bdf33a4d5cd7912
  Gas price: 10.0 gwei   Gas limit: 647951   Nonce: 807
  LaunchXP.constructor confirmed - Block: 10464963   Gas used: 589047 (90.91%)
  LaunchXP deployed at: 0x90BC605075335FCdB23d824A0a64Cc311ea071EF

Transaction sent: 0xf930480cc6d92d05e2ae5742e44ac69818f34a331b9c6617b06342ad7eedc14f
  Gas price: 10.0 gwei   Gas limit: 1391447   Nonce: 808
  Staking.constructor confirmed - Block: 10464968   Gas used: 1264952 (90.91%)
  Staking deployed at: 0xd48Bea9843ACE352c8e9C0E0F65F89c90b80387a

```