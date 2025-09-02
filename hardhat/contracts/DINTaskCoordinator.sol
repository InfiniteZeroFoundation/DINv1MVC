// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.28;


import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

interface IDinValidatorStake {
    function getStake(address validator) external view returns (uint256);
    function slash(address validator, uint256 amount) external;
    function is_slasher_contract(address slasher_contract) external view returns (bool);
}

interface IDINTaskAuditor {
    function createAuditorsBatches(uint _GI) external returns (bool);
    function setTestDataAssignedFlag(uint _GI, bool flag) external;
}
    


contract DINTaskCoordinator is Ownable {

    

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
        AuditorsBatchesCreated,
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



    IDinValidatorStake public dinvalidatorStakeContract;
    IDINTaskAuditor public dinTaskAuditorContract;

    uint public GI = 0; // GlobalIteration

    GIstates public GIstate;

    string public genesisModelIpfsHash; // genesis model ipfs hash

    uint256 public minStake = 1_000_000;

    mapping(uint => address[]) public dinValidators;

    // Track if an address is registered for a given _GI
    mapping(uint => mapping(address => bool)) public isDINValidator;
  
    event DINValidatorRegistered(uint indexed GI, address indexed validator);


    constructor(address dinvalidatorStakeContract_address) Ownable(msg.sender) {

        dinvalidatorStakeContract = IDinValidatorStake(dinvalidatorStakeContract_address);
        GIstate = GIstates.AwaitingDINTaskAuditorToBeSet;
    }



    function setDINTaskAuditorContract(address _dintaskauditor_contract_address) public onlyOwner {
        require(GIstate == GIstates.AwaitingDINTaskAuditorToBeSet, "DINTaskAuditor contract can not be set");
        dinTaskAuditorContract = IDINTaskAuditor(_dintaskauditor_contract_address);
        GIstate = GIstates.AwaitingDINTaskCoordinatorAsSlasher;
    }

    function setDINTaskCoordinatorAsSlasher() public onlyOwner {
        require(GIstate == GIstates.AwaitingDINTaskCoordinatorAsSlasher, "DINTaskCoordinator can not be set as slasher");
        require(dinvalidatorStakeContract.is_slasher_contract(address(this)), "DINTaskCoordinator is not a slasher");
        GIstate = GIstates.AwaitingDINTaskAuditorAsSlasher;
    }

    function setDINTaskAuditorAsSlasher() public onlyOwner {
        require(GIstate == GIstates.AwaitingDINTaskAuditorAsSlasher, "DINTaskAuditor can not be set as slasher");
        require(dinvalidatorStakeContract.is_slasher_contract(address(dinTaskAuditorContract)), "DINTaskAuditor is not a slasher");
        GIstate = GIstates.AwaitingGenesisModel;
    }

    function setGenesisModelIpfsHash(string memory _genesisModelIpfsHash) public onlyOwner {
        require(GIstate == GIstates.AwaitingGenesisModel, "Genesis model ipfs hash can not be set");
        genesisModelIpfsHash = _genesisModelIpfsHash;
        GIstate = GIstates.GenesisModelCreated;
    }

    function startGI(uint _GI) public onlyOwner {
        require(GIstate == GIstates.GenesisModelCreated || GIstate == GIstates.GIended, "GI can not be started");
        require(_GI == GI+1, "Invalid GlobalIteration");
        GIstate = GIstates.GIstarted;
        GI++;
    }

    function startDINvalidatorRegistration(uint _GI) public onlyOwner {
        require(GIstate == GIstates.GIstarted, "DINvalidator registration can not be started");
        require(_GI == GI, "Invalid GlobalIteration");
        GIstate = GIstates.DINvalidatorRegistrationStarted;
    }

    function registerDINvalidator(uint _GI) public {
        require(GIstate == GIstates.DINvalidatorRegistrationStarted, "validators registration not open");
        uint256 stake = dinvalidatorStakeContract.getStake(msg.sender);
        require(stake >= minStake, "Insufficient stake to register");
        // Check if already registered using O(1) lookup
        require(!isDINValidator[_GI][msg.sender], "Validator already registered");

        // Add to list and mark as registered
        dinValidators[_GI].push(msg.sender);
        isDINValidator[_GI][msg.sender] = true;

        emit DINValidatorRegistered(_GI, msg.sender);

    }

    

    function closeDINvalidatorRegistration(uint _GI) public onlyOwner {
        require(GIstate == GIstates.DINvalidatorRegistrationStarted, "DINvalidator registration can not be finished");
        require(_GI == GI, "Invalid GlobalIteration");
        GIstate = GIstates.DINvalidatorRegistrationClosed;
    }


    function getDINtaskValidators(uint _GI) public view returns (address[] memory) {
        return dinValidators[_GI];
    }

    function startDINauditorRegistration(uint _GI) public onlyOwner {
        require(GIstate == GIstates.DINvalidatorRegistrationClosed, "DINauditor registration can not be started");
        require(_GI == GI, "Invalid GlobalIteration");
        GIstate = GIstates.DINauditorRegistrationStarted;
    }

    function closeDINauditorRegistration(uint _GI) public onlyOwner {
        require(GIstate == GIstates.DINauditorRegistrationStarted, "DINauditor registration can not be finished");
        require(_GI == GI, "Invalid GlobalIteration");
        GIstate = GIstates.DINauditorRegistrationClosed;
    }

    function startLMsubmissions(uint _GI) public onlyOwner {
        require(GIstate == GIstates.DINauditorRegistrationClosed, "LM submissions can not be started");
        require(_GI == GI, "Invalid GlobalIteration");
        GIstate = GIstates.LMSstarted;
    }

    function closeLMsubmissions(uint _GI) public onlyOwner {
        require(GIstate == GIstates.LMSstarted, "LM submissions are not started");
        require(_GI == GI, "Invalid GlobalIteration");
        GIstate = GIstates.LMSclosed;
    }


    function createAuditorsBatches(uint _GI) public onlyOwner {
        require(GIstate == GIstates.LMSclosed, "LM submissions evaluation can not be started");
        require(_GI == GI, "Invalid GlobalIteration");


        bool success = dinTaskAuditorContract.createAuditorsBatches(_GI);
        require(success, "Failed to create auditors batches");
        
        GIstate = GIstates.AuditorsBatchesCreated;
        
    }

    function setTestDataAssignedFlag ( uint _GI, bool flag ) external onlyOwner {
        require(_GI == GI, "Wrong GI");
        require(GIstate == GIstates.AuditorsBatchesCreated, "TC: can not set TestDataAssignedFlag");

        dinTaskAuditorContract.setTestDataAssignedFlag(_GI, flag);


    }


    function startLMsubmissionsEvaluation(uint _GI) public onlyOwner {
        require(GIstate == GIstates.AuditorsBatchesCreated, "LM submissions evaluation can not be started");
        require(_GI == GI, "Invalid GlobalIteration");

        GIstate = GIstates.LMSevaluationStarted;
    }

    function closeLMsubmissionsEvaluation(uint _GI) public onlyOwner {
        require(GIstate == GIstates.LMSevaluationStarted, "LM submissions evaluation can not be finished");
        require(_GI == GI, "Invalid GlobalIteration");
        GIstate = GIstates.LMSevaluationClosed;
    }

}