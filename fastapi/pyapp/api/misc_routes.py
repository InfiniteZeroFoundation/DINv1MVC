from fastapi import APIRouter, Depends
from dotenv import load_dotenv, set_key, unset_key, dotenv_values
router = APIRouter(tags=["Miscellaneous"])


from services.dataset_service import load_mnist_dataset, save_datasets
from services.partition_service import partition_dataset, save_partitioned_data

from services.model_architect import get_DINTaskCoordinator_Instance

@router.get("/getGIState")
def get_GIState():
    try:
        env_config = dotenv_values(".env")
        DINTaskCoordinator_Contract_Address = env_config.get("DINTaskCoordinator_Contract_Address")
        print("getting GI state")
        if DINTaskCoordinator_Contract_Address is None:
            return {"message": "DINTaskCoordinator_Contract_Address not found",
                    "status": "error",
                    "GI": 0,
                    "GIstatedes": "DINTaskCoordinator contract not deployed"}
        else:
            
            deployed_DINTaskCoordinatorContract = get_DINTaskCoordinator_Instance(dintaskcoordinator_address=DINTaskCoordinator_Contract_Address)
            
            GI = deployed_DINTaskCoordinatorContract.functions.GI().call()
            
            GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()
            
            if GIstate == 0:
                GIstatedes = "Awaiting Genesis Model"
            elif GIstate == 1:
                GIstatedes = "Genesis Model Created"
            elif GIstate == 2:
                GIstatedes = "GI started"
            elif GIstate == 3:
                GIstatedes = "LM submissions started"
            elif GIstate == 4:
                GIstatedes = "LM submissions closed"
            elif GIstate == 5:
                GIstatedes = "LM submissions evaluation closed"
            elif GIstate == 6:
                GIstatedes = "T1nT2B created"
            elif GIstate == 7:
                GIstatedes = "T1B aggregation started"
            elif GIstate == 8:
                GIstatedes = "T1B aggregation done"
            elif GIstate == 9:
                GIstatedes = "T2B aggregation started"
            elif GIstate == 10:
                GIstatedes = "T2B aggregation done"
            elif GIstate == 11:
                GIstatedes = "Validators slashed"
            elif GIstate == 12:
                GIstatedes = "GI ended"
            
            
            return {"message": "GI state fetched successfully",
                    "status": "success",
                    "GI": GI,
                    "GIstate": GIstate,
                    "GIstatedes": GIstatedes}
    except Exception as e:
        return {"message": str(e),
                "status": "error",
                "GI": None,
                "GIstate": None,
                "GIstatedes": None}


@router.get("/distribute/dataset")
def distribute_dataset():
    num_clients = 9
    try:
        
        print("distributing dataset in misc routes")
        
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
        unset_key(".env", "DINCoordinator_Contract_Address")
        unset_key(".env", "DINToken_Contract_Address")
        unset_key(".env", "TaskCoordinator_Contract_Address")
        unset_key(".env", "IS_GenesisModelCreated")
        unset_key(".env", "GenesisModelIpfsHash")
        unset_key(".env", "ClientModelsCreatedF")
        unset_key(".env", "DINTaskCoordinator_Contract_Address")
        unset_key(".env", "ModelOwner_Address")
        unset_key(".env", "DINValidatorStake_Contract_Address")
        unset_key(".env", "DINCoordinator_DINValidatorStake_Contract_Address")
        unset_key(".env", "DPModeUsed")
        unset_key(".env", "DINTaskCoordinatorISslasher")
        unset_key(".env", "TetherMock_Contract_Address")
        
        
        
        return {"message": "ALL Reset successfully",
                "status": "success"}
    except Exception as e:
        return {"message": str(e),
                "status": "error"}

@router.get("/test")
def test():
    return {"message": "Router is working!"}