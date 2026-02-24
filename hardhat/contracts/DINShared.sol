// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.28;

// ─────────────────────────────────────────────────────────────────────────────
// Shared types & interfaces for the DIN protocol
// Imported by DINTaskCoordinator and DINTaskAuditor (and any future contracts).
// ─────────────────────────────────────────────────────────────────────────────

/// @notice Lifecycle states for a single Global Iteration (GI).
enum GIstates {
    AwaitingDINTaskAuditorToBeSet, // 0
    AwaitingDINTaskCoordinatorAsSlasher, // 1
    AwaitingDINTaskAuditorAsSlasher, // 2
    AwaitingGenesisModel, // 3
    GenesisModelCreated, // 4
    GIstarted, // 5
    DINaggregatorsRegistrationStarted, // 6
    DINaggregatorsRegistrationClosed, // 7
    DINauditorsRegistrationStarted, // 8
    DINauditorsRegistrationClosed, // 9
    LMSstarted, // 10
    LMSclosed, // 11
    AuditorsBatchesCreated, // 12
    LMSevaluationStarted, // 13
    LMSevaluationClosed, // 14
    T1nT2Bcreated, // 15
    T1AggregationStarted, // 16
    T1AggregationDone, // 17
    T2AggregationStarted, // 18
    T2AggregationDone, // 19
    AuditorsSlashed, // 20
    AggregatorsSlashed, // 21
    GIended // 22
}

// ─────────────────────────────────────────────────────────────────────────────
// Cross-contract interfaces
// ─────────────────────────────────────────────────────────────────────────────

interface IDinValidatorStake {
    function getStake(address validator) external view returns (uint256);

    function slash(address validator, uint256 amount) external;

    function is_slasher_contract(
        address slasher_contract
    ) external view returns (bool);
}

interface IDINTaskCoordinator {
    function GI() external view returns (uint256);

    function GIstate() external view returns (GIstates);
}

interface IDINTaskAuditor {
    function createAuditorsBatches(uint _GI) external returns (bool);

    function setTestDataAssignedFlag(uint _GI, bool flag) external;

    function finalizeEvaluation(uint _GI) external returns (bool);

    function approvedModelIndexes(
        uint _GI
    ) external view returns (uint[] memory);

    function updatePassScore(uint256 newPassScore) external;
}
