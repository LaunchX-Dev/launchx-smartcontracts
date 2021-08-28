// SPDX-License-Identifier: unlicensed
pragma solidity 0.8.4;
import "../SyntheticDelegation.sol";

/// @notice exposes internal variables for unit tests.
contract SyntheticDelegationMock is SyntheticDelegation {
    function raw_totalCurrentCycleStakeAmount() external view returns(uint256) {
        return _totalCurrentCycleStakeAmount;
    }

    function raw_totalNextCycleStakeAmount() external view returns(uint256) {
        return _totalNextCycleStakeAmount;
    }

    function raw_globalCacheCycle() external view returns(uint256) {
        return _globalCacheCycle;
    }

    function raw_cycleTotalReward(uint256 cycle) external view returns(uint256) {
        return _cycleTotalReward[cycle];
    }

    function raw_cycleTotalStaked(uint256 cycle) external view returns(uint256) {
        return _cycleTotalStaked[cycle];
    }
}