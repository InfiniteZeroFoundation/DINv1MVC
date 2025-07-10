// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.28;

import "./DinToken.sol"; // Import the DINToken contract interface

interface IDinValidatorStake {
    function add_slasher_contract(address _slasher_contract) external;
    function remove_slasher_contract(address _slasher_contract) external;
}
    
contract DinCoordinator {

    address public owner;  
    
    DinToken public dintoken;
    IDinValidatorStake public dinvalidatorStakeContract;

    uint256 public constant DIN_PER_ETH = 1_000_000 ; // 1 ETH = 1 million DIN tokens

    event DepositAndMint(address indexed user, uint256 ethAmount, uint256 mintAmount);

    constructor() {
        owner = msg.sender;

        // Deploy DINToken
        dintoken = new DinToken();
        // Transfer minting rights from DINToken deployer to this contract
        dintoken.updateMinter(address(this));
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }


    function depositAndMint() external payable {
        require(msg.value > 0, "No ETH sent");

        uint256 mintAmount = msg.value * DIN_PER_ETH / 1 ether;
        dintoken.mint(msg.sender, mintAmount);

        emit DepositAndMint(msg.sender, msg.value, mintAmount);
    }

    function withdraw() external onlyOwner {
        payable(owner).transfer(address(this).balance);
    }

    function add_slasher_contract(address _slasher_contract) external onlyOwner {
        dinvalidatorStakeContract.add_slasher_contract(_slasher_contract);
    }
    
    function remove_slasher_contract(address _slasher_contract) external onlyOwner {
        dinvalidatorStakeContract.remove_slasher_contract(_slasher_contract);
    }

    function add_dinvalidatorStakeContract(address _dinvalidatorStakeContract) external onlyOwner {
        dinvalidatorStakeContract = IDinValidatorStake(_dinvalidatorStakeContract);
    }
}