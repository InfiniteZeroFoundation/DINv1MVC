from fastapi import APIRouter
from pydantic import BaseModel
from dotenv import load_dotenv, set_key, unset_key, dotenv_values

from services.blockchain_services import get_w3
from services.model_architect import get_DINTaskCoordinator_Instance
from services.DAO_services import get_DINCoordinator_Instance, get_DINtokenContract_Instance, get_DINValidatorStake_Instance
from services.client_services import train_client_model_and_upload_to_ipfs

from .schemas import Tier2Batch

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.post("/getClientModelsCreatedF")
def get_client_models_created_f():
    try:
        env_config = dotenv_values(".env")
        client_models_created_f = env_config.get("ClientModelsCreatedF")=="True"
        
        print("Client models created state:", client_models_created_f)
        w3 = get_w3()
        
        env_config = dotenv_values(".env")
        DINTaskCoordinator_Contract_Address = env_config.get("DINTaskCoordinator_Contract_Address")
        
        dp_mode = env_config.get("DPModeUsed")
        
        client_model_ipfs_hashes = []
        ClientAddresses = []
        
        if client_models_created_f:
            deployed_DINTaskCoordinatorContract = get_DINTaskCoordinator_Instance(dintaskcoordinator_address=DINTaskCoordinator_Contract_Address)
            
            current_GI = deployed_DINTaskCoordinatorContract.functions.getGI().call()
            
            lm_submissions = deployed_DINTaskCoordinatorContract.functions.getClientModels(current_GI).call()
            
            print("lm_submissions: ", lm_submissions)
            
            for i in range(len(lm_submissions)):
                client_model_ipfs_hash = lm_submissions[i][1]
                ClientAddresses.append(lm_submissions[i][0])
                client_model_ipfs_hashes.append(client_model_ipfs_hash)
                
            
            
        return {"message": "Client models state fetched successfully",
                "status": "success",
                "client_models_created_f": client_models_created_f,
                "client_model_ipfs_hashes": client_model_ipfs_hashes,
                "client_addresses": ClientAddresses,
                "dp_mode": dp_mode}
    except Exception as e:
        return {"message": str(e),
                "status": "error",
                "client_models_created_f": False,
                "client_model_ipfs_hashes": None,
                "client_addresses": None,
                "dp_mode": None}


class ClientModelCreateRequest(BaseModel):
    selectedDPMode: str  # Must be one of: "disabled", "beforeTraining", or "afterTraining"

@router.post("/createClientModels")
def create_client_models(request: ClientModelCreateRequest):
    try:
        print("createClientModels")
        dp_mode = request.selectedDPMode
        print("DPMode: ", dp_mode)
        

        # Optional: Validate the value
        valid_modes = ["disabled", "afterTraining"]
        if dp_mode not in valid_modes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid DPMode. Must be one of {valid_modes}."
            )
        
        w3 = get_w3()
        
        env_config = dotenv_values(".env")
        DINTaskCoordinator_Contract_Address = env_config.get("DINTaskCoordinator_Contract_Address")
        
        deployed_DINTaskCoordinatorContract = get_DINTaskCoordinator_Instance(dintaskcoordinator_address=DINTaskCoordinator_Contract_Address)
        
        current_GI = deployed_DINTaskCoordinatorContract.functions.getGI().call()
        initial_model_ipfs_hash = None
        t2_list = []
        if current_GI > 1:
            t2_batches_count = 1
            for i in range(t2_batches_count):
                (bid, val, fin, cid) = deployed_DINTaskCoordinatorContract.functions.getTier2Batch(current_GI-1, i).call()
                t2_list.append(Tier2Batch(batch_id=bid, validators=val, finalized=fin, final_cid=cid))
                 

            t2_batch_gi_minus_1 = t2_list[0]
            
            
            initial_model_ipfs_hash = t2_batch_gi_minus_1.final_cid
        
        
        genesis_model_ipfs_hash = deployed_DINTaskCoordinatorContract.functions.getGenesisModelIpfsHash().call()
            
        client_model_ipfs_hashes = train_client_model_and_upload_to_ipfs(genesis_model_ipfs_hash, initial_model_ipfs_hash, dp_mode=dp_mode)
            
        for i, ipfs_model_hash in enumerate(client_model_ipfs_hashes):
            deployed_DINTaskCoordinatorContract.functions.submitLocalModel(ipfs_model_hash, current_GI).transact({
                "from": w3.eth.accounts[i+2],
                "gas": 3000000,
                "gasPrice": w3.to_wei("5", "gwei"),
            })
            
        set_key(".env", "ClientModelsCreatedF", "True")
        
        set_key(".env", "DPModeUsed", dp_mode)
        
        return {"message": "Client models created successfully",
                "status": "success",
                "client_models_created_f": True,
                "client_model_ipfs_hashes": client_model_ipfs_hashes,
                "client_addresses": w3.eth.accounts[2:2+len(client_model_ipfs_hashes)]}
    except Exception as e:
        return {"message": str(e),
                "status": "error",
                "client_models_created_f": False}
 