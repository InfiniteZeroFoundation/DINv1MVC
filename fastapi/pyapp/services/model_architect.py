import torch
import torch.nn as nn
import torch.nn.functional as F
import os
from services.ipfs_service import upload_to_ipfs
import torch.nn.init as init
from web3 import Web3
from dotenv import dotenv_values
import json

RPC_URL = os.getenv("RPC_URL")           # e.g. "http://127.0.0.1:8545"

def get_w3():
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        if not w3.is_connected():
            raise HTTPException(status_code=400, detail="Could not connect to Ethereum node.")
        return w3
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not connect to Ethereum node: {e}")


class ModelArchitecture(nn.Module):
    def __init__(self):
        super(ModelArchitecture, self).__init__()
        self.fc1 = nn.Linear(28*28, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, 10)

    def forward(self, x):
        # x shape: [batch_size, 1, 28, 28]
        x = x.view(x.size(0), -1)         # flatten to [batch_size, 784]
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x
    
def initialize_weights(m):
    if isinstance(m, nn.Linear):
        # Initialize weights with Xavier uniform initialization
        init.xavier_uniform_(m.weight)
        # Initialize biases to zero
        if m.bias is not None:
            init.zeros_(m.bias)    

    
def getGenesisModelIpfs():
    model = ModelArchitecture()
    
    #initialize model
    model.apply(initialize_weights)
    
    # Save the trained genesis model to disk
    os.makedirs("./models", exist_ok=True)
    torch.save(model, "./models/modelowner/genesis_model.pth")
    
    # Upload the model to IPFS
    model_hash = upload_to_ipfs("./models/modelowner/genesis_model.pth", "Genesis model")
    return model_hash

def get_DINCoordinator_Instance(dincoordinator_address=None):
    w3 = get_w3()
    if dincoordinator_address is None:
        dincoordinator_address = dotenv_values(".env").get("DINCoordinator_Contract_Address")
    
    with open("../../hardhat/artifacts/contracts/DINCoordinator.sol/DINCoordinator.json") as f:
        dincoordinator_data = json.load(f)
        dincoordinator_abi = dincoordinator_data["abi"]
        dincoordinator_bytecode = dincoordinator_data["bytecode"]
    
    if dincoordinator_address:
        deployed_DINCoordinatorContract = w3.eth.contract(address=dincoordinator_address, abi=dincoordinator_abi)
        return deployed_DINCoordinatorContract
    else:
        return w3.eth.contract(abi=dincoordinator_abi, bytecode=dincoordinator_bytecode)
    
