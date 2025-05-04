// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.28;

contract DINCoordinator {

    address public owner;  // model owner
    string public genesisModelIpfsHash; // genesis model ipfs hash
    uint public GI = 0; // GlobalIteration

    mapping (uint => mapping(address => string)) public clientModels;
    mapping (uint => address[]) public clientAddresses;


    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    function setGenesisModelIpfsHash(string memory _genesisModelIpfsHash) public onlyOwner {
        genesisModelIpfsHash = _genesisModelIpfsHash;
        GI = 1;
    }

    function getGenesisModelIpfsHash() public view returns (string memory) {
        return genesisModelIpfsHash;
    }

    function submitLocalModel(string memory _clientModel, uint _GI) public {
        require(_GI == GI, "Invalid GlobalIteration");
        require(bytes(clientModels[_GI][msg.sender]).length == 0, "Already submitted a model");
        clientModels[_GI][msg.sender] = _clientModel;
        clientAddresses[_GI].push(msg.sender);
    }

    function getClientModel(uint _GI, address _clientAddress) public view returns (string memory) {
        return clientModels[_GI][_clientAddress];
    }

    function getClientAddresses(uint _GI) public view returns (address[] memory) {
        return clientAddresses[_GI];
    }

    function getGI() public view returns (uint) {
        return GI;
    }

}
