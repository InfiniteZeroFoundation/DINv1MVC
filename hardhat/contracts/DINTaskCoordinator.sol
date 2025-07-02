// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.28;

import "./DinToken.sol"; // Import the DINToken contract interface

interface IDinValidatorStake {
    function getStake(address validator) external view returns (uint256);
}


contract DINTaskCoordinator {

    uint8 public constant T1_VALIDATORS_PER_BATCH = 3;
    uint8 public constant T1_MODELS_PER_BATCH     = 3;

    address public owner;  // model owner
    string public genesisModelIpfsHash; // genesis model ipfs hash
    uint public GI = 0; // GlobalIteration
    uint256 public minStake = 1_000_000;
    enum GIstates {
        AwaitingGenesisModel,
        GenesisModelCreated,
        GIstarted,
        LMSstarted,
        LMSclosed,
        LMSevaluationClosed,
        T1Bcreated,
        T1AggregationDone,
        T2Bcreated,
        T2AggregationDone,
        GIended
    }
    GIstates public GIstate;

    mapping (uint => address[]) public dinValidators;

    struct LMSubmission {
        address client;
        string  modelCID;
        bool    evaluated;   // ← set by evaluateLM()
        bool    approved;    // ← set by evaluateLM()
    }
    
    mapping(uint => LMSubmission[]) public lmSubmissions;

    ///  GI  ➜  submitter  ➜  bool
    mapping(uint => mapping(address => bool)) public clientHasSubmitted;

    uint public totalDepositedRewards = 0;

    struct Tier1Batch {
        uint           batchId;             // Unique inside round
        address[]      validators;          // Validators assigned
        uint[]         modelIndexes;        // Indexes into approvedModels[GI]
        bool           finalized;           // True after majority
        string         finalCID;            // Majority‐agreed CID
    }
    
    mapping(uint => Tier1Batch[]) public tier1Batches;

    // Audit & voting maps            GI  ➜  batchId ➜ validator  ➜  …
    mapping(uint => mapping(uint => mapping(address => string))) public t1SubmissionCID;
    mapping(uint => mapping(uint => mapping(address => bool  ))) public t1Submitted;
    mapping(uint => mapping(uint => mapping(string  => uint ))) public t1Votes;   // CID ➜ votes

    struct Tier2Batch {
        uint      batchId;
        address[] validators;     // Tier‑2 validators
        uint[]    t1BatchIds;     // which Tier‑1 batches are aggregated
        bool      finalized;
        string    finalCID;
    }
    
    mapping(uint => Tier2Batch[]) public tier2Batches;

    mapping(uint => mapping(uint => mapping(address => string))) public t2SubmissionCID;
    mapping(uint => mapping(uint => mapping(address => bool  ))) public t2Submitted;
    mapping(uint => mapping(uint => mapping(string  => uint ))) public t2Votes;

    DinToken public dintoken;
    IDinValidatorStake public dinvalidatorStakeContract;

    event RewardDeposited(address indexed modelOwner, uint256 amount);

    event Tier1BatchAuto(uint indexed GI, uint indexed batchId, address[3] validators, uint[3] modelIdx);
    event Tier2BatchAuto(uint indexed GI, uint indexed batchId, address[] validators);

    constructor(address dintoken_address, address dinvalidatorStakeContract_address) {
        owner = msg.sender;
        dintoken = DinToken(dintoken_address);
        dinvalidatorStakeContract = IDinValidatorStake(dinvalidatorStakeContract_address);
        GIstate = GIstates.AwaitingGenesisModel;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }


    function depositReward(uint _amount) public onlyOwner {
        require(_amount > 0, "Amount must be greater than 0");

        // Pull DIN tokens from sender (ModelOwner)
        bool success = dintoken.transferFrom(msg.sender, address(this), _amount);
        require(success, "DINToken transfer failed");

        totalDepositedRewards += _amount;
        emit RewardDeposited(msg.sender, _amount);
    }

    function setGenesisModelIpfsHash(string memory _genesisModelIpfsHash) public onlyOwner {
        genesisModelIpfsHash = _genesisModelIpfsHash;
        GIstate = GIstates.GenesisModelCreated;
    }

    function getGenesisModelIpfsHash() public view returns (string memory) {
        return genesisModelIpfsHash;
    }

    function startGI(uint _GI) public onlyOwner {
        require(GIstate == GIstates.GenesisModelCreated || GIstate == GIstates.GIended, "GI can not be started");
        require(_GI == GI+1, "Invalid GlobalIteration");
        GIstate = GIstates.GIstarted;
        GI++;
    }

    function startLMsubmissions(uint _GI) public onlyOwner {
        require(GIstate == GIstates.GIstarted, "GI is not started");
        require(_GI == GI, "Invalid GlobalIteration");
        GIstate = GIstates.LMSstarted;
    }

    function closeLMsubmissions(uint _GI) public onlyOwner {
        require(GIstate == GIstates.LMSstarted, "LM submissions are not started");
        require(_GI == GI, "Invalid GlobalIteration");
        GIstate = GIstates.LMSclosed;
    }

    function registerDINvalidator(uint _GI) public {
        require(GIstate == GIstates.GIstarted, "validators can only be registered when the GI is started");
        uint256 stake = dinvalidatorStakeContract.getStake(msg.sender);
        require(stake >= minStake, "Insufficient stake to register");
        address[] storage validators = dinValidators[_GI];

        // Optional: prevent double registration
        for (uint256 i = 0; i < validators.length; i++) {
            require(validators[i] != msg.sender, "Validator already registered");
        }

        validators.push(msg.sender);

    }

    function getDINtaskValidators(uint _GI) public view returns (address[] memory) {
        return dinValidators[_GI];
    }

    function submitLocalModel(string memory _clientModel, uint _GI) public {
        require(_GI == GI, "Invalid GI");
        require(GIstate == GIstates.LMSstarted, "Submissions not open");
        require(!clientHasSubmitted[_GI][msg.sender], "Already submitted");

        lmSubmissions[_GI].push(LMSubmission({
            client:    msg.sender,
            modelCID:  _clientModel,
            evaluated: false,
            approved:  false
        }));
        clientHasSubmitted[_GI][msg.sender] = true;
    }

    function _clearclientHasSubmitted(uint _GI) internal {
        // iterate once over the array to know who to delete
        LMSubmission[] storage list = lmSubmissions[_GI];
        for (uint i = 0; i < list.length; i++) {
            delete clientHasSubmitted[_GI][list[i].client];
        }
    }

    function getClientModels(uint _GI) public view returns (LMSubmission[] memory) {
        return lmSubmissions[_GI];
    }

    function getGI() public view returns (uint) {
        return GI;
    }

    function evaluateLM(
        uint _GI,
        address _client,
        bool _approved            // true = keep, false = drop
    ) external onlyOwner {
        require(GIstate == GIstates.LMSclosed, "Not evaluable");
        require(_GI == GI, "Wrong GI");
        LMSubmission[] storage list = lmSubmissions[_GI];
        bool found = false;
        for (uint i = 0; i < list.length; i++) {
            if (list[i].client == _client) {
                require(!list[i].evaluated, "Already evaluated");
                list[i].evaluated = true;
                list[i].approved = _approved;
                found = true;
                break;
            }
        }
        require(found, "Submission not found");
    }

    // When owner has walked through all clients:
    function finalizeEvaluation(uint _GI) external onlyOwner {
        require(GIstate == GIstates.LMSclosed, "Eval not ready");
        require(_GI == GI, "Wrong GI");
        GIstate = GIstates.LMSevaluationClosed;
    }

}
