// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.28;

import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import "./DINShared.sol";

contract DINTaskCoordinator is Ownable {
    IDinValidatorStake public dinvalidatorStakeContract;
    IDINTaskAuditor public dinTaskAuditorContract;

    uint public GI = 0; // GlobalIteration

    GIstates public GIstate;

    string public genesisModelIpfsHash; // genesis model ipfs hash

    uint256 public minStake = 1_000_000;

    mapping(uint => address[]) public dinAggregators;

    // Track if an address is registered for a given _GI as an aggregator
    mapping(uint => mapping(address => bool)) public isDINAggregator;

    uint256 public constant T1_AGGREGATORS_PER_BATCH = 3;
    uint256 public constant T1_MODELS_PER_BATCH = 3;
    uint256 public constant MIN_T1_MODELS_PER_BATCH = 2;

    struct Tier1Batch {
        uint batchId; // Unique inside round
        address[] aggregators; // Aggregators assigned
        uint[] modelIndexes; // Indexes into approvedModels[GI]
        bool finalized; // True after majority
        string finalCID; // Majority‐agreed CID
    }

    mapping(uint => Tier1Batch[]) public tier1Batches;

    // Audit & voting maps            GI  ➜  batchId ➜ validator  ➜  …
    mapping(uint => mapping(uint => mapping(address => string)))
        public t1SubmissionCID;
    mapping(uint => mapping(uint => mapping(address => bool)))
        public t1Submitted;
    mapping(uint => mapping(uint => mapping(string => uint))) public t1Votes; // CID ➜ votes

    struct Tier2Batch {
        uint batchId;
        address[] aggregators; // Tier‑2 aggregators
        bool finalized;
        string finalCID;
    }

    mapping(uint => Tier2Batch[]) public tier2Batches;
    mapping(uint => uint) public tier2Score;

    mapping(uint => mapping(uint => mapping(address => string)))
        public t2SubmissionCID;
    mapping(uint => mapping(uint => mapping(address => bool)))
        public t2Submitted;
    mapping(uint => mapping(uint => mapping(string => uint))) public t2Votes;

    event DINValidatorRegistered(uint indexed GI, address indexed validator);
    event Tier1BatchAuto(uint indexed GI, uint indexed batchId);
    event Tier2BatchAuto(uint indexed GI, uint indexed batchId);

    constructor(address dinvalidatorStakeContract_address) Ownable(msg.sender) {
        dinvalidatorStakeContract = IDinValidatorStake(
            dinvalidatorStakeContract_address
        );
        GIstate = GIstates.AwaitingDINTaskAuditorToBeSet;
    }

    function setDINTaskAuditorContract(
        address _dintaskauditor_contract_address
    ) public onlyOwner {
        require(
            GIstate == GIstates.AwaitingDINTaskAuditorToBeSet,
            "DINTaskAuditor contract can not be set"
        );
        dinTaskAuditorContract = IDINTaskAuditor(
            _dintaskauditor_contract_address
        );
        GIstate = GIstates.AwaitingDINTaskCoordinatorAsSlasher;
    }

    function setDINTaskCoordinatorAsSlasher() public onlyOwner {
        require(
            GIstate == GIstates.AwaitingDINTaskCoordinatorAsSlasher,
            "DINTaskCoordinator can not be set as slasher"
        );
        require(
            dinvalidatorStakeContract.is_slasher_contract(address(this)),
            "DINTaskCoordinator is not a slasher"
        );
        GIstate = GIstates.AwaitingDINTaskAuditorAsSlasher;
    }

    function setDINTaskAuditorAsSlasher() public onlyOwner {
        require(
            GIstate == GIstates.AwaitingDINTaskAuditorAsSlasher,
            "DINTaskAuditor can not be set as slasher"
        );
        require(
            dinvalidatorStakeContract.is_slasher_contract(
                address(dinTaskAuditorContract)
            ),
            "DINTaskAuditor is not a slasher"
        );
        GIstate = GIstates.AwaitingGenesisModel;
    }

    function setGenesisModelIpfsHash(
        string memory _genesisModelIpfsHash
    ) public onlyOwner {
        require(
            GIstate == GIstates.AwaitingGenesisModel,
            "Genesis model ipfs hash can not be set"
        );
        genesisModelIpfsHash = _genesisModelIpfsHash;
        GIstate = GIstates.GenesisModelCreated;
    }

    function startGI(uint _GI, uint score) public onlyOwner {
        require(
            GIstate == GIstates.GenesisModelCreated ||
                GIstate == GIstates.GIended,
            "GI can not be started"
        );
        require(_GI == GI + 1, "Invalid GlobalIteration");
        dinTaskAuditorContract.updatePassScore(score);
        GIstate = GIstates.GIstarted;
        GI++;
    }

    function startDINaggregatorsRegistration(uint _GI) public onlyOwner {
        require(
            GIstate == GIstates.GIstarted,
            "DINaggregators registration can not be started"
        );
        require(_GI == GI, "Invalid GlobalIteration");
        GIstate = GIstates.DINaggregatorsRegistrationStarted;
    }

    function registerDINaggregator(uint _GI) public {
        require(
            GIstate == GIstates.DINaggregatorsRegistrationStarted,
            "aggregators registration not open"
        );

        uint256 stake = dinvalidatorStakeContract.getStake(msg.sender);
        require(stake >= minStake, "Insufficient stake to register");
        // Check if already registered using O(1) lookup
        require(
            !isDINAggregator[_GI][msg.sender],
            "Validator already registered"
        );

        // Add to list and mark as registered
        dinAggregators[_GI].push(msg.sender);
        isDINAggregator[_GI][msg.sender] = true;

        emit DINValidatorRegistered(_GI, msg.sender);
    }

    function closeDINaggregatorsRegistration(uint _GI) public onlyOwner {
        require(
            GIstate == GIstates.DINaggregatorsRegistrationStarted,
            "DINaggregators registration can not be finished"
        );
        require(_GI == GI, "Invalid GlobalIteration");
        GIstate = GIstates.DINaggregatorsRegistrationClosed;
    }

    function getDINtaskAggregators(
        uint _GI
    ) public view returns (address[] memory) {
        return dinAggregators[_GI];
    }

    function startDINauditorsRegistration(uint _GI) public onlyOwner {
        require(
            GIstate == GIstates.DINaggregatorsRegistrationClosed,
            "DINauditor registration can not be started"
        );
        require(_GI == GI, "Invalid GlobalIteration");
        GIstate = GIstates.DINauditorsRegistrationStarted;
    }

    function closeDINauditorsRegistration(uint _GI) public onlyOwner {
        require(
            GIstate == GIstates.DINauditorsRegistrationStarted,
            "DINauditor registration can not be finished"
        );
        require(_GI == GI, "Invalid GlobalIteration");
        GIstate = GIstates.DINauditorsRegistrationClosed;
    }

    function startLMsubmissions(uint _GI) public onlyOwner {
        require(
            GIstate == GIstates.DINauditorsRegistrationClosed,
            "LM submissions can not be started"
        );
        require(_GI == GI, "Invalid GlobalIteration");
        GIstate = GIstates.LMSstarted;
    }

    function closeLMsubmissions(uint _GI) public onlyOwner {
        require(
            GIstate == GIstates.LMSstarted,
            "LM submissions are not started"
        );
        require(_GI == GI, "Invalid GlobalIteration");
        GIstate = GIstates.LMSclosed;
    }

    function createAuditorsBatches(uint _GI) public onlyOwner {
        require(
            GIstate == GIstates.LMSclosed,
            "LM submissions evaluation can not be started"
        );
        require(_GI == GI, "Invalid GlobalIteration");

        bool success = dinTaskAuditorContract.createAuditorsBatches(_GI);
        require(success, "Failed to create auditors batches");

        GIstate = GIstates.AuditorsBatchesCreated;
    }

    function setTestDataAssignedFlag(uint _GI, bool flag) external onlyOwner {
        require(_GI == GI, "Wrong GI");
        require(
            GIstate == GIstates.AuditorsBatchesCreated,
            "TC: can not set TestDataAssignedFlag"
        );

        dinTaskAuditorContract.setTestDataAssignedFlag(_GI, flag);
    }

    function startLMsubmissionsEvaluation(uint _GI) public onlyOwner {
        require(
            GIstate == GIstates.AuditorsBatchesCreated,
            "LM submissions evaluation can not be started"
        );
        require(_GI == GI, "Invalid GlobalIteration");

        GIstate = GIstates.LMSevaluationStarted;
    }

    function closeLMsubmissionsEvaluation(uint _GI) public onlyOwner {
        require(
            GIstate == GIstates.LMSevaluationStarted,
            "LM submissions evaluation can not be finished"
        );
        require(_GI == GI, "Invalid GlobalIteration");
        bool success = dinTaskAuditorContract.finalizeEvaluation(_GI);
        require(success, "Failed to finalize evaluation");
        GIstate = GIstates.LMSevaluationClosed;
    }

    /// @notice Build Tier‑1 and Tier‑2 batches automatically.
    /// @dev  REQUIRES: LM evaluation closed.  Validators must already be registered in dinAggregators[_GI].
    function autoCreateTier1AndTier2(uint _GI) external onlyOwner {
        require(
            GIstate == GIstates.LMSevaluationClosed,
            "Eval phase not closed"
        );
        require(_GI == GI, "Wrong GI");

        // ▸ 1. Pull and shuffle validator pool
        address[] storage valPool = dinAggregators[_GI];
        uint vLen = valPool.length;
        require(vLen >= T1_AGGREGATORS_PER_BATCH, "Not enough validators");
        _shuffleAddressArray(valPool);

        // ▸ 2. Build list of approved model indexes
        uint[] memory modelIdx = _collectApprovedModelIndexes(_GI);
        _shuffleUintArray(modelIdx);

        // ▸ 3. Greedily fill Tier-1 batches
        uint vPtr;
        uint mPtr;
        uint t1cnt;
        while (
            vPtr + T1_AGGREGATORS_PER_BATCH <= valPool.length &&
            (mPtr + T1_MODELS_PER_BATCH <= modelIdx.length ||
                (mPtr + MIN_T1_MODELS_PER_BATCH <= modelIdx.length &&
                    mPtr + T1_MODELS_PER_BATCH > modelIdx.length))
        ) {
            Tier1Batch storage b = tier1Batches[_GI].push();
            b.batchId = t1cnt++;

            for (uint256 k = 0; k < T1_AGGREGATORS_PER_BATCH; k++) {
                b.aggregators.push(valPool[vPtr + k]);
            }

            uint modelsToAssign = T1_MODELS_PER_BATCH;
            if (modelIdx.length - mPtr < T1_MODELS_PER_BATCH) {
                modelsToAssign = modelIdx.length - mPtr;
            }

            for (uint256 k = 0; k < modelsToAssign; k++) {
                b.modelIndexes.push(modelIdx[mPtr + k]);
            }

            emit Tier1BatchAuto(_GI, b.batchId);

            vPtr += T1_AGGREGATORS_PER_BATCH;
            mPtr += modelsToAssign;
        }

        // ▸ 4. Create Tier-2 batch with EXACTLY T1_AGGREGATORS_PER_BATCH validators if enough remain
        if (valPool.length - vPtr >= T1_AGGREGATORS_PER_BATCH) {
            Tier2Batch storage t2 = tier2Batches[_GI].push();
            t2.batchId = 0;
            for (uint256 k = 0; k < T1_AGGREGATORS_PER_BATCH; k++) {
                t2.aggregators.push(valPool[vPtr + k]);
            }

            emit Tier2BatchAuto(_GI, t2.batchId);
        }

        GIstate = GIstates.T1nT2Bcreated;
    }

    // ──────────── internal shuffle helpers ────────────
    function _shuffleAddressArray(address[] storage arr) internal {
        for (uint i = arr.length - 1; i > 0; i--) {
            uint j = uint(
                keccak256(
                    abi.encodePacked(blockhash(block.number - 1), i, arr.length)
                )
            ) % (i + 1);
            (arr[i], arr[j]) = (arr[j], arr[i]);
        }
    }

    function _shuffleUintArray(uint[] memory arr) internal view {
        for (uint i = arr.length - 1; i > 0; i--) {
            uint j = uint(
                keccak256(
                    abi.encodePacked(block.timestamp, i, arr.length, msg.sender)
                )
            ) % (i + 1);
            (arr[i], arr[j]) = (arr[j], arr[i]);
        }
    }

    function _collectApprovedModelIndexes(
        uint _GI
    ) internal view returns (uint[] memory out) {
        out = dinTaskAuditorContract.approvedModelIndexes(_GI);
        require(
            out.length >= T1_MODELS_PER_BATCH,
            "Not enough approved models"
        );
    }

    // ──────────── read helpers (optional UX) ────────────
    function tier1BatchCount(uint _GI) external view returns (uint) {
        return tier1Batches[_GI].length;
    }

    // read one Tier‑1 batch by index
    function getTier1Batch(
        uint _GI,
        uint _id
    )
        external
        view
        returns (
            uint batchId,
            address[] memory validators,
            uint[] memory modelIndexes,
            bool finalized,
            string memory finalCID
        )
    {
        require(_GI <= GI, "Wrong GI");
        require(_id < tier1Batches[_GI].length, "Batch not found");
        Tier1Batch storage b = tier1Batches[_GI][_id];
        return (
            b.batchId,
            b.aggregators,
            b.modelIndexes,
            b.finalized,
            b.finalCID
        );
    }

    function getTier2Batch(
        uint _GI,
        uint _id
    )
        external
        view
        returns (
            uint batchId,
            address[] memory validators,
            bool finalized,
            string memory finalCID
        )
    {
        require(_id == 0, "Only one Tier 2 batch");
        require(_GI <= GI, "Wrong GI");
        Tier2Batch storage b = tier2Batches[_GI][_id];
        return (b.batchId, b.aggregators, b.finalized, b.finalCID);
    }

    function startT1Aggregation(uint _GI) external onlyOwner {
        require(
            GIstate == GIstates.T1nT2Bcreated,
            "Not ready to start T1 aggregation"
        );
        require(_GI == GI, "Wrong GI");
        GIstate = GIstates.T1AggregationStarted;
    }

    function submitT1Aggregation(
        uint _GI,
        uint _batchId,
        string memory _aggregationCID
    ) external {
        require(
            GIstate == GIstates.T1AggregationStarted,
            "T1 aggregation not started"
        );
        require(_GI == GI, "Wrong GI");
        require(_batchId < tier1Batches[_GI].length, "Invalid batch");

        Tier1Batch storage b = tier1Batches[_GI][_batchId];

        // Verify sender is an assigned validator
        bool isAggregator = false;
        for (uint i = 0; i < b.aggregators.length; i++) {
            if (b.aggregators[i] == msg.sender) {
                isAggregator = true;
                break;
            }
        }
        require(isAggregator, "Not a batch aggregator");

        require(!t1Submitted[_GI][_batchId][msg.sender], "Already submitted");

        t1Submitted[_GI][_batchId][msg.sender] = true;
        t1SubmissionCID[_GI][_batchId][msg.sender] = _aggregationCID;

        // Increment vote count
        t1Votes[_GI][_batchId][_aggregationCID]++;
    }

    function finalizeT1Aggregation(uint _GI) external onlyOwner {
        require(
            GIstate == GIstates.T1AggregationStarted,
            "Not ready to finalize T1 aggregation"
        );
        require(_GI == GI, "Wrong GI");

        Tier1Batch[] storage batches = tier1Batches[_GI];

        for (uint i = 0; i < batches.length; i++) {
            Tier1Batch storage b = batches[i];

            // Determine the CID with the most votes
            string memory winningCID = "";
            uint maxVotes = 0;

            // Enumerate unique CIDs
            for (uint j = 0; j < b.aggregators.length; j++) {
                address aggregator = b.aggregators[j];
                if (t1Submitted[_GI][b.batchId][aggregator]) {
                    string memory cid = t1SubmissionCID[_GI][b.batchId][
                        aggregator
                    ];
                    uint votes = t1Votes[_GI][b.batchId][cid];
                    if (votes > maxVotes) {
                        maxVotes = votes;
                        winningCID = cid;
                    }
                }
            }

            require(bytes(winningCID).length > 0, "No submissions");
            b.finalized = true;
            b.finalCID = winningCID;
        }

        GIstate = GIstates.T1AggregationDone;
    }

    function startT2Aggregation(uint _GI) external onlyOwner {
        require(
            GIstate == GIstates.T1AggregationDone,
            "Not ready to start T2 aggregation"
        );
        require(_GI == GI, "Wrong GI");
        GIstate = GIstates.T2AggregationStarted;
    }

    function submitT2Aggregation(
        uint _GI,
        uint _batchId,
        string memory _aggregationCID
    ) external {
        require(
            GIstate == GIstates.T2AggregationStarted,
            "T2 aggregation not started"
        );
        require(_GI == GI, "Wrong GI");
        require(_batchId == 0, "Only one Tier 2 batch");

        Tier2Batch storage b = tier2Batches[_GI][_batchId];

        // Verify sender is an assigned validator
        bool isAggregator = false;
        for (uint i = 0; i < b.aggregators.length; i++) {
            if (b.aggregators[i] == msg.sender) {
                isAggregator = true;
                break;
            }
        }
        require(isAggregator, "Not a batch aggregator");

        require(!t2Submitted[_GI][_batchId][msg.sender], "Already submitted");

        t2Submitted[_GI][_batchId][msg.sender] = true;
        t2SubmissionCID[_GI][_batchId][msg.sender] = _aggregationCID;

        // Increment vote count
        t2Votes[_GI][_batchId][_aggregationCID]++;
    }

    function finalizeT2Aggregation(uint _GI) external onlyOwner {
        require(
            GIstate == GIstates.T2AggregationStarted,
            "Not ready to finalize T2 aggregation"
        );
        require(_GI == GI, "Wrong GI");

        Tier2Batch[] storage batches = tier2Batches[_GI];

        for (uint i = 0; i < batches.length; i++) {
            Tier2Batch storage b = batches[i];

            // Determine the CID with the most votes
            string memory winningCID = "";
            uint maxVotes = 0;

            // Enumerate unique CIDs
            for (uint j = 0; j < b.aggregators.length; j++) {
                address aggregator = b.aggregators[j];
                if (t2Submitted[_GI][b.batchId][aggregator]) {
                    string memory cid = t2SubmissionCID[_GI][b.batchId][
                        aggregator
                    ];
                    uint votes = t2Votes[_GI][b.batchId][cid];
                    if (votes > maxVotes) {
                        maxVotes = votes;
                        winningCID = cid;
                    }
                }
            }

            require(bytes(winningCID).length > 0, "No submissions");
            b.finalized = true;
            b.finalCID = winningCID;
        }

        GIstate = GIstates.T2AggregationDone;
    }

    function slashAuditors(uint _GI) external onlyOwner {
        require(
            GIstate == GIstates.T2AggregationDone,
            "Not ready to slash auditors"
        );
        require(_GI == GI, "Wrong GI");
        // The Actual Slashing logic maybe implemented here
        GIstate = GIstates.AuditorsSlashed;
    }

    function slashValidators(uint _GI) external onlyOwner {
        require(
            GIstate == GIstates.AuditorsSlashed,
            "Not ready to slash validators"
        );
        require(_GI == GI, "Wrong GI");

        uint256 slashAmount = minStake;

        // 1. Tier 1 batches
        Tier1Batch[] storage t1batches = tier1Batches[_GI];
        for (uint i = 0; i < t1batches.length; i++) {
            Tier1Batch storage b = t1batches[i];
            for (uint j = 0; j < b.aggregators.length; j++) {
                address aggregator = b.aggregators[j];

                bool submitted = t1Submitted[_GI][b.batchId][aggregator];
                bool submittedMatching = false;
                if (submitted) {
                    string memory cid = t1SubmissionCID[_GI][b.batchId][
                        aggregator
                    ];
                    submittedMatching = (keccak256(bytes(cid)) ==
                        keccak256(bytes(b.finalCID)));
                }
                if (!submitted || !submittedMatching) {
                    dinvalidatorStakeContract.slash(aggregator, slashAmount);
                }
            }
        }

        // 2. Tier 2 batches
        Tier2Batch[] storage t2batches = tier2Batches[_GI];
        for (uint i = 0; i < t2batches.length; i++) {
            Tier2Batch storage b = t2batches[i];
            for (uint j = 0; j < b.aggregators.length; j++) {
                address aggregator = b.aggregators[j];

                bool submitted = t2Submitted[_GI][b.batchId][aggregator];
                bool submittedMatching = false;
                if (submitted) {
                    string memory cid = t2SubmissionCID[_GI][b.batchId][
                        aggregator
                    ];
                    submittedMatching = (keccak256(bytes(cid)) ==
                        keccak256(bytes(b.finalCID)));
                }
                if (!submitted || !submittedMatching) {
                    dinvalidatorStakeContract.slash(aggregator, slashAmount);
                }
            }
        }

        GIstate = GIstates.AggregatorsSlashed;
    }

    function setTier2Score(uint _GI, uint _score) external onlyOwner {
        require(_GI == GI, "Wrong GI");
        require(
            GIstate == GIstates.T2AggregationDone ||
                GIstate == GIstates.GenesisModelCreated,
            "Not ready to set Tier 2 score"
        );
        tier2Score[_GI] = _score;
    }

    function getTier2Score(uint _GI) external view returns (uint) {
        return tier2Score[_GI];
    }

    function endGI(uint _GI) external onlyOwner {
        require(GIstate == GIstates.AggregatorsSlashed, "Not ready to end GI");
        require(_GI == GI, "Wrong GI");
        GIstate = GIstates.GIended;
    }
}
