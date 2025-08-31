// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.28;

import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

enum GIstates {
    AwaitingDINTaskAuditorToBeSet,
    AwaitingDINTaskCoordinatorAsSlasher,
    AwaitingDINTaskAuditorAsSlasher,
    AwaitingGenesisModel,
    GenesisModelCreated,
    GIstarted,
    DINvalidatorRegistrationStarted,
    DINvalidatorRegistrationClosed,
    DINauditorRegistrationStarted,
    DINauditorRegistrationClosed,
    LMSstarted,
    LMSclosed,
    LMSevaluationStarted,
    LMSevaluationClosed,
    T1nT2Bcreated,
    T1AggregationStarted,
    T1AggregationDone,
    T2AggregationStarted,
    T2AggregationDone,
    AuditorsSlashed,
    ValidatorSlashed,
    GIended
}

interface IMockUSDT {

    function transferFrom(address from, address to, uint256 value) external returns (bool);
    
}

interface IDinValidatorStake {
    function getStake(address validator) external view returns (uint256);
    function slash(address validator, uint256 amount) external;
}


interface IDINTaskCoordinator {
    function GI() external view returns (uint256);
    function GIstate() external view returns (uint8); // or an enum getter
}

contract DINTaskAuditor is Ownable {


    IMockUSDT public mockusdt;

    IDinValidatorStake public dinvalidatorStakeContract;

    IDINTaskCoordinator public dintaskcoordinatorContract;

    uint public totalDepositedRewards = 0;

    uint256 public minStake = 1_000_000;

    mapping(uint => address[]) public dinAuditors;

    // Track if an address is registered for a given _GI
    mapping(uint => mapping(address => bool)) public isDINAuditor;

    event RewardDeposited(address indexed modelOwner, uint256 amount);

    event DINAuditorRegistered(uint indexed GI, address indexed auditor);

    constructor(address _mockusdt, address _dinvalidatorStakeContract_address, address _dintaskcoordinator_contract_address) Ownable(msg.sender) {
        mockusdt = IMockUSDT(_mockusdt);
        dinvalidatorStakeContract = IDinValidatorStake(_dinvalidatorStakeContract_address);
        dintaskcoordinatorContract = IDINTaskCoordinator(_dintaskcoordinator_contract_address);
    
    }


    function depositReward(uint _amount) public onlyOwner {
        require(_amount > 0, "Amount must be greater than 0");

        // Pull MockUSDT from sender (ModelOwner)
        bool success = mockusdt.transferFrom(msg.sender, address(this), _amount);
        require(success, "MockUSDT transfer failed");

        totalDepositedRewards += _amount;
        emit RewardDeposited(msg.sender, _amount);
    }

    function registerDINAuditor(uint _GI) public {
        require(dintaskcoordinatorContract.GIstate() == uint8(GIstates.DINauditorRegistrationStarted), "DINauditor registration not open");
        require(_GI == dintaskcoordinatorContract.GI(), "Invalid GlobalIteration");
        require(!isDINAuditor[_GI][msg.sender], "Auditor already registered");
        uint256 stake = dinvalidatorStakeContract.getStake(msg.sender);
        require(stake >= minStake, "Insufficient stake to register");

        dinAuditors[_GI].push(msg.sender);
        isDINAuditor[_GI][msg.sender] = true;

        emit DINAuditorRegistered(_GI, msg.sender);

    }

    function getDINtaskAuditors(uint _GI) public view returns (address[] memory) {
        return dinAuditors[_GI];
    }
        


}