from fastapi import APIRouter, HTTPException, Body
from web3 import Web3
import os, shutil
from dotenv import load_dotenv, set_key, unset_key, dotenv_values
import requests
import json
from collections import OrderedDict
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import pickle


from services.dataset_service import load_mnist_dataset, save_datasets
from services.partition_service import partition_dataset, save_partitioned_data
from services.model_architect import getGenesisModelIpfs, get_w3, get_DINCoordinator_Instance
from services.client_services import train_client_model_and_upload_to_ipfs

load_dotenv()

router = APIRouter()

RPC_URL = os.getenv("RPC_URL")           # e.g. "http://127.0.0.1:8545"


@router.get("/distribute/dataset")
def distribute_dataset():
    num_clients = 9
    try:
        
        # Step 1: Load the dataset
        train_dataset, test_dataset = load_mnist_dataset()

        # Step 2: Save the datasets to disk
        save_datasets(train_dataset, test_dataset, output_dir="./Dataset")
        
        # Step 3: Partition the dataset
        partitioned_data = partition_dataset(train_dataset, num_clients)
        
        # Step 4: Save the partitioned data
        save_partitioned_data(partitioned_data, output_dir="./Dataset/clients")
        
        return {"message": "Dataset distributed successfully",
                "status": "success"}
    except Exception as e:
        return {"message": str(e),
                "status": "error"}


@router.post("/modelowner/getGenesisModelsetF")
def get_genesis_modelsetF():
    try:
        env_config = dotenv_values(".env")
        IS_GenesisModelCreated = env_config.get("IS_GenesisModelCreated")
        model_hash = env_config.get("GenesisModelIpfsHash")
        dincoordinator_address = env_config.get("DINCoordinator_Contract_Address")
        return {"message": "Genesis model state fetched successfully",
                "status": "success",
                "IS_GenesisModelCreated": IS_GenesisModelCreated,
                "model_ipfs_hash": model_hash,
                "dincordinator_address": dincoordinator_address}
    except Exception as e:
        return {"message": str(e),
                "status": "error",
                "IS_GenesisModelCreated": False, 
                "model_ipfs_hash": None,
                "dincordinator_address": None}


@router.post("/modelowner/createGenesisModel")
def create_genesis_model():
    try:
        
        w3 = get_w3()
        model_hash = getGenesisModelIpfs()
        
        model_owner_account = w3.eth.accounts[0] # = w3.eth.account.from_key(private_keys[0])
        print("Model owner account:", model_owner_account)

        
        DINCoordinator_contract = get_DINCoordinator_Instance()
        constructor_tx_hash  = DINCoordinator_contract.constructor().transact({
            "from": model_owner_account,
            "gas": 3000000,
            "gasPrice": w3.to_wei("5", "gwei"),
        })
        constructor_receipt = w3.eth.wait_for_transaction_receipt(constructor_tx_hash)
        dincoordinator_contract_address = constructor_receipt.contractAddress
        
        
        print("DINCoordinator contract deployed at:", dincoordinator_contract_address)
        
        # Create contract instance
        deployed_DINCoordinatorContract = get_DINCoordinator_Instance(dincoordinator_address=dincoordinator_contract_address)
        
        tx_hash = deployed_DINCoordinatorContract.functions.setGenesisModelIpfsHash(model_hash).transact({
            "from": model_owner_account,
            "gas": 3000000,
            "gasPrice": w3.to_wei("5", "gwei"),
        })
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
        print("GenesisModelIpfsHash set in DINCoordinator contract with hash: ", model_hash)
        
        set_key(".env", "DINCoordinator_Contract_Address", dincoordinator_contract_address)
        set_key(".env", "IS_GenesisModelCreated", "True")
        set_key(".env", "GenesisModelIpfsHash", model_hash)
        
        env_config = dotenv_values(".env")
        dincoordinator_address = env_config.get("DINCoordinator_Contract_Address")
        
        
        return {"message": "Genesis model created & uploaded to IPFS successfully, logged in smart contract",
                "status": "success",
                "IS_GenesisModelCreated": True,
                "model_ipfs_hash": model_hash,
                "dincordinator_address": dincoordinator_address}
    except Exception as e:
        return {"message": str(e),
                "status": "error",
                "IS_GenesisModelCreated": False,
                "model_ipfs_hash": None,
                "dincordinator_address": None}


@router.post("/clients/getClientModelsCreatedF")
def get_client_models_created_f():
    try:
        env_config = dotenv_values(".env")
        client_models_created_f = env_config.get("ClientModelsCreatedF")=="True"
        
        print("Client models created state:", client_models_created_f)
        w3 = get_w3()
        
        env_config = dotenv_values(".env")
        DINCoordinator_Contract_Address = env_config.get("DINCoordinator_Contract_Address")
        
        client_model_ipfs_hashes = []
        ClientAddresses = None
        
        if client_models_created_f:
            deployed_DINCoordinatorContract = get_DINCoordinator_Instance(dincoordinator_address=DINCoordinator_Contract_Address)
            
            current_GI = deployed_DINCoordinatorContract.functions.getGI().call()
            
            ClientAddresses = deployed_DINCoordinatorContract.functions.getClientAddresses(current_GI).call()
            
            
            
            for i, client_address in enumerate(ClientAddresses):
                client_model_ipfs_hash = deployed_DINCoordinatorContract.functions.getClientModel(current_GI, client_address).call()
                client_model_ipfs_hashes.append(client_model_ipfs_hash)
                
            
            
        return {"message": "Client models state fetched successfully",
                "status": "success",
                "client_models_created_f": client_models_created_f,
                "client_model_ipfs_hashes": client_model_ipfs_hashes,
                "client_addresses": ClientAddresses}
    except Exception as e:
        return {"message": str(e),
                "status": "error",
                "client_models_created_f": False,
                "client_model_ipfs_hashes": None,
                "client_addresses": None}


@router.post("/clients/createClientModels")
def create_client_models():
    try:
        w3 = get_w3()
        
        env_config = dotenv_values(".env")
        DINCoordinator_Contract_Address = env_config.get("DINCoordinator_Contract_Address")
        
        deployed_DINCoordinatorContract = get_DINCoordinator_Instance(dincoordinator_address=DINCoordinator_Contract_Address)
        
        current_GI = deployed_DINCoordinatorContract.functions.getGI().call()
        
        
        genesis_model_ipfs_hash = deployed_DINCoordinatorContract.functions.getGenesisModelIpfsHash().call()
            
        client_model_ipfs_hashes = train_client_model_and_upload_to_ipfs(genesis_model_ipfs_hash)
            
        for i, ipfs_model_hash in enumerate(client_model_ipfs_hashes):
            deployed_DINCoordinatorContract.functions.submitLocalModel(ipfs_model_hash, current_GI).transact({
                "from": w3.eth.accounts[i+1],
                "gas": 3000000,
                "gasPrice": w3.to_wei("5", "gwei"),
            })
            
        set_key(".env", "ClientModelsCreatedF", "True")
        
        return {"message": "Client models created successfully",
                "status": "success",
                "client_models_created_f": True,
                "client_model_ipfs_hashes": client_model_ipfs_hashes,
                "client_addresses": w3.eth.accounts[1:1+len(client_model_ipfs_hashes)]}
    except Exception as e:
        return {"message": str(e),
                "status": "error",
                "client_models_created_f": False}


@router.get("/reset/resetall")
def resetall():
    try:
        unset_key(".env", "DINCoordinator_Contract_Address")
        unset_key(".env", "IS_GenesisModelCreated")
        unset_key(".env", "GenesisModelIpfsHash")
        unset_key(".env", "ClientModelsCreatedF")
        return {"message": "ALL Reset successfully",
                "status": "success"}
    except Exception as e:
        return {"message": str(e),
                "status": "error"}

@router.get("/test")
def test():
    return {"message": "Router is working!"}