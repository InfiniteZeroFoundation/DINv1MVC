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


load_dotenv()

router = APIRouter()

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

@router.get("/reset/resetall")
def resetall():
    try:
        return {"message": "ALL Reset successfully",
                "status": "success"}
    except Exception as e:
        return {"message": str(e),
                "status": "error"}

@router.get("/test")
def test():
    return {"message": "Router is working!"}