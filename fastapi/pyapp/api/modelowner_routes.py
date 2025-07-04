from fastapi import APIRouter, Depends
from pydantic import BaseModel
from dotenv import load_dotenv, set_key, unset_key, dotenv_values


from services.blockchain_services import get_w3
from services.model_architect import getGenesisModelIpfs, get_DINTaskCoordinator_Instance
from services.DAO_services import get_DINCoordinator_Instance, get_DINtokenContract_Instance, get_DINValidatorStake_Instance

from .schemas import Tier1Batch, Tier2Batch

router = APIRouter(prefix="/modelowner", tags=["Model Owner"])


@router.post("/startGI")
def start_GI():
    try:
        env_config = dotenv_values(".env")
        
        w3 = get_w3()
        
        model_owner_address = env_config.get("ModelOwner_Address")
        
        DINTaskCoordinator_Contract_Address = env_config.get("DINTaskCoordinator_Contract_Address")
        
        deployed_DINTaskCoordinatorContract = get_DINTaskCoordinator_Instance(dintaskcoordinator_address=DINTaskCoordinator_Contract_Address)
        
        curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()
        tx_hash = deployed_DINTaskCoordinatorContract.functions.startGI(curr_GI+1).transact({
            "from": model_owner_address,
            "gas": 3000000,
            "gasPrice": w3.to_wei("5", "gwei"),
        })
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return {"message": "GI started successfully",
                "status": "success"}
    except Exception as e:
        return {"message": str(e),
                "status": "error"}

@router.post("/getModelOwnerState")
def get_modelowner_state():
    
    try:
        env_config = dotenv_values(".env")
        w3 = get_w3()
        model_owner_address = env_config.get("ModelOwner_Address")
        
        client_models_created_f = env_config.get("ClientModelsCreatedF")
        
        if model_owner_address is None:
            model_owner_address = w3.eth.accounts[1] 
            set_key(".env", "ModelOwner_Address", model_owner_address)
        
        DinCoordinator_Contract_Address = env_config.get("DINCoordinator_Contract_Address")
        
        DINToken_Contract_Address = env_config.get("DINToken_Contract_Address")
        
        DINTaskCoordinator_Contract_Address = env_config.get("DINTaskCoordinator_Contract_Address")
        
        IS_GenesisModelCreated = env_config.get("IS_GenesisModelCreated")
        model_hash = env_config.get("GenesisModelIpfsHash")
        if DINTaskCoordinator_Contract_Address is None:
            dintaskcoordinator_dintoken_balance = 0
        else:
            deployed_DINTokenContract = get_DINtokenContract_Instance(dintoken_address=DINToken_Contract_Address)
            dintaskcoordinator_dintoken_balance = deployed_DINTokenContract.functions.balanceOf(DINTaskCoordinator_Contract_Address).call()
        
        
        if DINToken_Contract_Address is None:
            model_owner_dintoken_balance = 0
            
        else:
            deployed_DINtokenContract = get_DINtokenContract_Instance(dintoken_address=DINToken_Contract_Address)
            model_owner_dintoken_balance = deployed_DINtokenContract.functions.balanceOf(model_owner_address).call()
        
        registered_validators = []
            
        if DINTaskCoordinator_Contract_Address is not None:
            deployed_DINTaskCoordinatorContract = get_DINTaskCoordinator_Instance(dintaskcoordinator_address=DINTaskCoordinator_Contract_Address)
            
            curr_GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()
            
            curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()
            
            if curr_GIstate >= 2 and curr_GIstate < 4:
                registered_validators = deployed_DINTaskCoordinatorContract.functions.getDINtaskValidators(curr_GI).call()
            
        return {
            "message": "Model owner state fetched successfully",
            "status": "success",
            "model_owner_address": model_owner_address,
            "model_owner_eth_balance": w3.from_wei(w3.eth.get_balance(model_owner_address), 'ether'),
            "model_owner_dintoken_balance": model_owner_dintoken_balance,
            "dintaskcoordinator_address": DINTaskCoordinator_Contract_Address,
            "dintaskcoordinator_dintoken_balance": dintaskcoordinator_dintoken_balance,
            "IS_GenesisModelCreated": IS_GenesisModelCreated,
            "model_ipfs_hash": model_hash,
            "registered_validators": registered_validators,
            "client_models_created_f": client_models_created_f
            }
            
    except Exception as e:
        return {"message": str(e),
                "status": "error",
                "model_owner_address": None,
                "model_owner_eth_balance": None,
                "model_owner_dintoken_balance": None,
                "dintaskcoordinator_address": None,
                "dintaskcoordinator_dintoken_balance": None,
                "IS_GenesisModelCreated": False,
                "model_ipfs_hash": None,
                "IS_GenesisModelCreated": False,
                "model_ipfs_hash": None
                }
    

@router.post("/depositAndMintDINTokens")
def deposit_and_mint_dintokens():
    try:
        env_config = dotenv_values(".env")
        w3 = get_w3()
        model_owner_address = env_config.get("ModelOwner_Address")
        dincoordinator_address = env_config.get("DINCoordinator_Contract_Address")
        deploy_dincoordinator_contract = get_DINCoordinator_Instance(dincoordinator_address=dincoordinator_address)
        
        DINToken_Contract_Address = env_config.get("DINToken_Contract_Address")
        
        tx_hash = deploy_dincoordinator_contract.functions.depositAndMint().transact({
            "from": model_owner_address,
            "gas": 3000000,
            "gasPrice": w3.to_wei("5", "gwei"),
            "value": w3.to_wei("1", "ether"),
        })
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if DINToken_Contract_Address is None:
            model_owner_dintoken_balance = 0
        else:
            deployed_DINtokenContract = get_DINtokenContract_Instance(dintoken_address=DINToken_Contract_Address)
            model_owner_dintoken_balance = deployed_DINtokenContract.functions.balanceOf(model_owner_address).call()
            
        return {"message": "DIN tokens deposited and minted successfully",
                "status": "success",
                "model_owner_dintoken_balance": model_owner_dintoken_balance,
                "model_owner_eth_balance": w3.from_wei(w3.eth.get_balance(model_owner_address), 'ether')}
    except Exception as e:
        return {"message": str(e),
                "status": "error"}

@router.post("/depositRewardInDINTaskCoordinator")
def deposit_reward_in_dintaskcoordinator():
    try:
        env_config = dotenv_values(".env")
        w3 = get_w3()
        
        model_owner_address = env_config.get("ModelOwner_Address")
        dintoken_contract_address = env_config.get("DINToken_Contract_Address")
        dintaskcoordinator_contract_address = env_config.get("DINTaskCoordinator_Contract_Address")
        deployed_dintoken_contract = get_DINtokenContract_Instance(dintoken_address=dintoken_contract_address)
        
        amount = 1000000
        
        
        print(" in fn deposit_reward_in_dintaskcoordinator")
        print("dintoken_contract_address:", dintoken_contract_address)
        print("dintaskcoordinator_contract_address:", dintaskcoordinator_contract_address)
        print("model_owner_address:", model_owner_address)
        print("Approving DINTaskCoordinator contract...")
        
        
        tx_hash = deployed_dintoken_contract.functions.approve(dintaskcoordinator_contract_address, amount).transact({
            "from": model_owner_address,
            "gas": 3000000,
            "gasPrice": w3.to_wei("5", "gwei")
        })
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        deployed_dintaskcoordinator_contract = get_DINTaskCoordinator_Instance(dintaskcoordinator_address=dintaskcoordinator_contract_address)
        
        deployed_dintaskcoordinator_contract.functions.depositReward(amount).transact({
            "from": model_owner_address,
            "gas": 3000000,
            "gasPrice": w3.to_wei("5", "gwei")
        })
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        
        
        if dintoken_contract_address is None:
            model_owner_dintoken_balance = 0
        else:
            deployed_DINtokenContract = get_DINtokenContract_Instance(dintoken_address=dintoken_contract_address)
            model_owner_dintoken_balance = deployed_DINtokenContract.functions.balanceOf(model_owner_address).call()
            
            dintaskcoordinator_dintoken_balance = deployed_DINtokenContract.functions.balanceOf(dintaskcoordinator_contract_address).call()
            
        return {"message": "DIN reward deposited successfully",
                "status": "success",
                "model_owner_dintoken_balance": model_owner_dintoken_balance,
                "dintaskcoordinator_dintoken_balance": dintaskcoordinator_dintoken_balance,
                "model_owner_eth_balance": w3.from_wei(w3.eth.get_balance(model_owner_address), 'ether')}
    except Exception as e:
        print("Error depositing reward:", e)
        return {"message": str(e),
                "status": "error"}
        
@router.post("/deployDINTaskCoordinator")
def deploy_dintaskcoordinator():
    try:
        env_config = dotenv_values(".env")
        w3 = get_w3()
        model_owner_address = env_config.get("ModelOwner_Address")
        DINToken_Contract_Address = env_config.get("DINToken_Contract_Address")
        
        DinValidatorStake_Contract_Address = env_config.get("DINValidatorStake_Contract_Address")
        
        DINTaskCoordinator_contract = get_DINTaskCoordinator_Instance()
        constructor_tx_hash  = DINTaskCoordinator_contract.constructor(DINToken_Contract_Address, DinValidatorStake_Contract_Address).transact({
            "from": model_owner_address,
            "gas": 2*3000000,
            "gasPrice": w3.to_wei("5", "gwei"),
        })
        constructor_receipt = w3.eth.wait_for_transaction_receipt(constructor_tx_hash)
        dintaskcoordinator_contract_address = constructor_receipt.contractAddress
        
        print("DINTaskCoordinator contract deployed at:", dintaskcoordinator_contract_address)
        
        set_key(".env", "DINTaskCoordinator_Contract_Address", dintaskcoordinator_contract_address)
        
        DINToken_contract = get_DINtokenContract_Instance(dintoken_address=DINToken_Contract_Address)
        
        dintaskcoordinatorDintokenBalance = DINToken_contract.functions.balanceOf(dintaskcoordinator_contract_address).call()
        
        return {"message": "DINTaskCoordinator contract deployed successfully",
                "status": "success",
                "dintaskcoordinator_contract_address": dintaskcoordinator_contract_address,
                "dintaskcoordinator_dintoken_balance": dintaskcoordinatorDintokenBalance, 
                }
        
    except Exception as e:
        print("Error deploying DINTaskCoordinator:", e)
        return {"message": str(e),
                "status": "error"}


@router.post("/createGenesisModel")
def create_genesis_model():
    try:
        
        w3 = get_w3()
        model_hash = getGenesisModelIpfs()
        
        
        
        env_config = dotenv_values(".env")
        
        model_owner_account = env_config.get("ModelOwner_Address")
        print("Model owner account:", model_owner_account)
        
        DINToken_Contract_Address = env_config.get("DINToken_Contract_Address")
        
        DINTaskCoordinator_Contract_Address = env_config.get("DINTaskCoordinator_Contract_Address")
        
        deployed_DINTaskCoordinatorContract = get_DINTaskCoordinator_Instance(dintaskcoordinator_address=DINTaskCoordinator_Contract_Address)
        
        tx_hash = deployed_DINTaskCoordinatorContract.functions.setGenesisModelIpfsHash(model_hash).transact({
            "from": model_owner_account,
            "gas": 3000000,
            "gasPrice": w3.to_wei("5", "gwei"),
        })
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
        print("GenesisModelIpfsHash set in DINTaskCoordinator contract with hash: ", model_hash)
        

        set_key(".env", "IS_GenesisModelCreated", "True")
        set_key(".env", "GenesisModelIpfsHash", model_hash)
    

        
        return {"message": "Genesis model created & uploaded to IPFS successfully, logged in smart contract",
                "status": "success",
                "IS_GenesisModelCreated": True,
                "model_ipfs_hash": model_hash,}
    except Exception as e:
        return {"message": str(e),
                "status": "error",
                "IS_GenesisModelCreated": False,
                "model_ipfs_hash": None}


@router.post("/startGI")
def start_GI():
    try:
        env_config = dotenv_values(".env")
        
        w3 = get_w3()
        
        model_owner_address = env_config.get("ModelOwner_Address")
        
        DINTaskCoordinator_Contract_Address = env_config.get("DINTaskCoordinator_Contract_Address")
        
        deployed_DINTaskCoordinatorContract = get_DINTaskCoordinator_Instance(dintaskcoordinator_address=DINTaskCoordinator_Contract_Address)
        
        tx_hash = deployed_DINTaskCoordinatorContract.functions.startGI().transact({
            "from": model_owner_address,
            "gas": 3000000,
            "gasPrice": w3.to_wei("5", "gwei"),
        })
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return {"message": "GI started successfully",
                "status": "success"}
    except Exception as e:
        return {"message": str(e),
                "status": "error"}

@router.post("/startLMsubmissions")
def start_LMsubmissions():
    try:
        env_config = dotenv_values(".env")
        
        w3 = get_w3()
        
        model_owner_address = env_config.get("ModelOwner_Address")
        
        DINTaskCoordinator_Contract_Address = env_config.get("DINTaskCoordinator_Contract_Address")
        
        deployed_DINTaskCoordinatorContract = get_DINTaskCoordinator_Instance(dintaskcoordinator_address=DINTaskCoordinator_Contract_Address)
        
        
        curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()
        tx_hash = deployed_DINTaskCoordinatorContract.functions.startLMsubmissions(curr_GI).transact({
            "from": model_owner_address,
            "gas": 3000000,
            "gasPrice": w3.to_wei("5", "gwei"),
        })
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return {"message": "LM submissions started successfully",
                "status": "success"}
    except Exception as e:
        print("Error starting LM submissions:", e)
        return {"message": str(e),
                "status": "error"}

@router.post("/closeLMsubmissions")
def close_LMsubmissions():
    try:
        print("in closeLMsubmissions")
        env_config = dotenv_values(".env")
        
        w3 = get_w3()
        
        model_owner_address = env_config.get("ModelOwner_Address")
        
        DINTaskCoordinator_Contract_Address = env_config.get("DINTaskCoordinator_Contract_Address")
        
        deployed_DINTaskCoordinatorContract = get_DINTaskCoordinator_Instance(dintaskcoordinator_address=DINTaskCoordinator_Contract_Address)
        
        curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()
        
        GI_state = deployed_DINTaskCoordinatorContract.functions.GIstate().call()
        
        if curr_GI < 1 or GI_state != 3:
            raise Exception("Can not close LM submissions at this time")
        tx_hash = deployed_DINTaskCoordinatorContract.functions.closeLMsubmissions(curr_GI).transact({
            "from": model_owner_address,
            "gas": 3000000,
            "gasPrice": w3.to_wei("5", "gwei"),
        })
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return {"message": "LM submissions closed successfully",
                "status": "success"}
    except Exception as e:
        print("Error closing LM submissions:", e)
        return {"message": str(e),
                "status": "error"}


@router.post("/getClientModels")
def get_modelowner_client_models():
    try:
        env_config = dotenv_values(".env")
        
        w3 = get_w3()
        
        model_owner_address = env_config.get("ModelOwner_Address")
        
        DINTaskCoordinator_Contract_Address = env_config.get("DINTaskCoordinator_Contract_Address")
        
        deployed_DINTaskCoordinatorContract = get_DINTaskCoordinator_Instance(dintaskcoordinator_address=DINTaskCoordinator_Contract_Address)
        
        curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()
        
        curr_GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()
        
        if curr_GIstate < 4:
            raise Exception("Can not get client models at this time")
        
        lm_submissions = deployed_DINTaskCoordinatorContract.functions.getClientModels(curr_GI).call()
        
        print("lm_submissions: ", lm_submissions)
        
        
        
        return {"message": "LM submissions collected successfully",
                "status": "success",
                "lm_submissions": lm_submissions}
    except Exception as e:
        print("Error collecting LM submissions:", e)
        return {"message": str(e),
                "status": "error"}
        
MIN_STAKE = 1000000 

class ClientModelRequest(BaseModel):
    client_address: str
    approved: bool

@router.post("/approveClientModel")
def approve_client_model(request: ClientModelRequest):
    try:
        env_config = dotenv_values(".env")
        
        w3 = get_w3()
        
        model_owner_address = env_config.get("ModelOwner_Address")
        
        DINTaskCoordinator_Contract_Address = env_config.get("DINTaskCoordinator_Contract_Address")
        
        deployed_DINTaskCoordinatorContract = get_DINTaskCoordinator_Instance(dintaskcoordinator_address=DINTaskCoordinator_Contract_Address)
        
        curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()
        
        curr_GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()
        
        if curr_GIstate != 4:
            raise Exception("Can not approve client model at this time")
        
        deployed_DINTaskCoordinatorContract.functions.evaluateLM(curr_GI, request.client_address, request.approved).transact({
            "from": model_owner_address,
            "gas": 3000000,
            "gasPrice": w3.to_wei("5", "gwei"),
        })
        
        return {"message": "Client model approved successfully",
                "status": "success"}
    except Exception as e:
        print("Error approving client model:", e)
        return {"message": str(e),
                "status": "error"}
    
@router.post("/rejectClientModel")
def reject_client_model(request: ClientModelRequest):
    try:
        env_config = dotenv_values(".env")
        
        w3 = get_w3()
        
        model_owner_address = env_config.get("ModelOwner_Address")
        
        DINTaskCoordinator_Contract_Address = env_config.get("DINTaskCoordinator_Contract_Address")
        
        deployed_DINTaskCoordinatorContract = get_DINTaskCoordinator_Instance(dintaskcoordinator_address=DINTaskCoordinator_Contract_Address)
        
        curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()
        
        curr_GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()
        
        if curr_GIstate != 4:
            raise Exception("Can not reject client model at this time")
        
        deployed_DINTaskCoordinatorContract.functions.evaluateLM(curr_GI, request.client_address, False).transact({
            "from": model_owner_address,
            "gas": 3000000,
            "gasPrice": w3.to_wei("5", "gwei"),
        })
        
        return {"message": "Client model rejected successfully",
                "status": "success"}
    except Exception as e:
        print("Error rejecting client model:", e)
        return {"message": str(e),
                "status": "error"}
    
@router.post("/closeLMsubmissionsEvaluation")
def closeLMsubmissionsEvaluation():
    try:
        env_config = dotenv_values(".env")
        
        w3 = get_w3()
        
        model_owner_address = env_config.get("ModelOwner_Address")
        
        DINTaskCoordinator_Contract_Address = env_config.get("DINTaskCoordinator_Contract_Address")
        
        deployed_DINTaskCoordinatorContract = get_DINTaskCoordinator_Instance(dintaskcoordinator_address=DINTaskCoordinator_Contract_Address)
        
        curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()
        
        curr_GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()
        
        if curr_GIstate != 4:
            raise Exception("Can not close LM submissions evaluation at this time")
        
        deployed_DINTaskCoordinatorContract.functions.finalizeEvaluation(curr_GI).transact({
            "from": model_owner_address,
            "gas": 3000000,
            "gasPrice": w3.to_wei("5", "gwei"),
        })
        
        return {"message": "LM submissions evaluation closed successfully",
                "status": "success"}
    except Exception as e:
        print("Error closing LM submissions evaluation:", e)
        return {"message": str(e),
                "status": "error"}

@router.post("/createTier1n2Batches")
def createTier1Batches():
    try:
        env_config = dotenv_values(".env")
        
        w3 = get_w3()
        
        model_owner_address = env_config.get("ModelOwner_Address")
        
        DINTaskCoordinator_Contract_Address = env_config.get("DINTaskCoordinator_Contract_Address")
        
        deployed_DINTaskCoordinatorContract = get_DINTaskCoordinator_Instance(dintaskcoordinator_address=DINTaskCoordinator_Contract_Address)
        
        curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()
        
        curr_GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()
        
        if curr_GIstate != 5:
            raise Exception("Can not create Tier 1 n 2 batches at this time")
        
        deployed_DINTaskCoordinatorContract.functions.autoCreateTier1AndTier2(curr_GI).transact({
            "from": model_owner_address,
            "gas": 3000000,
            "gasPrice": w3.to_wei("5", "gwei"),
        })
        
        return {"message": "Tier 1 n 2 batches created successfully",
                "status": "success"}
    except Exception as e:
        print("Error creating Tier 1 n 2 batches:", e)
        return {"message": str(e),
                "status": "error"}

class BatchPayload(BaseModel):
    tier1_batches: list[Tier1Batch]
    tier2_batches: list[Tier2Batch]
    message: str
    status: str
    
@router.post("/getTier1n2Batches")
def getTier1n2Batches():
    try:
        env_config = dotenv_values(".env")
        
        w3 = get_w3()
        
        model_owner_address = env_config.get("ModelOwner_Address")
        
        DINTaskCoordinator_Contract_Address = env_config.get("DINTaskCoordinator_Contract_Address")
        
        deployed_DINTaskCoordinatorContract = get_DINTaskCoordinator_Instance(dintaskcoordinator_address=DINTaskCoordinator_Contract_Address)
        
        curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()
        
        curr_GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()
        
        if curr_GIstate < 6:
            raise Exception("Can not get Tier 1 n 2 batches at this time")
        
        t1_batches_count  = deployed_DINTaskCoordinatorContract.functions.tier1BatchCount(curr_GI).call()
        
        t1_list = []
        
        for i in range(t1_batches_count):
            (bid, val, idxs, fin, cid) = deployed_DINTaskCoordinatorContract.functions.getTier1Batch(curr_GI, i).call()
            t1_list.append(Tier1Batch(batch_id=bid, validators=val, model_indexes=idxs, finalized=fin, final_cid=cid))
        
        t2_list = []
        t2_batches_count = 1
        
        for i in range(t2_batches_count):
            (bid, val, fin, cid) = deployed_DINTaskCoordinatorContract.functions.getTier2Batch(curr_GI, i).call()
            t2_list.append(Tier2Batch(batch_id=bid, validators=val, finalized=fin, final_cid=cid))
            
        return BatchPayload(tier1_batches=t1_list,
                            tier2_batches=t2_list,
                            message="Tier 1 n 2 batches retrieved successfully",
                            status="success")
    except Exception as e:
        print("Error getting Tier 1 n 2 batches:", e)
        return BatchPayload(tier1_batches=[],
                            tier2_batches=[],
                            message=str(e),
                            status="error")
  
@router.post("/startT1Aggregation")
def start_T1Aggregation():
    try:
        env_config = dotenv_values(".env")
        
        w3 = get_w3()
        
        model_owner_address = env_config.get("ModelOwner_Address")
        
        DINTaskCoordinator_Contract_Address = env_config.get("DINTaskCoordinator_Contract_Address")
        
        deployed_DINTaskCoordinatorContract = get_DINTaskCoordinator_Instance(dintaskcoordinator_address=DINTaskCoordinator_Contract_Address)
        
        curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()
        
        curr_GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()
        
        if curr_GIstate != 6:
            raise Exception("Can not start Tier 1 Aggregation at this time")
        
        deployed_DINTaskCoordinatorContract.functions.startT1Aggregation(curr_GI).transact({
            "from": model_owner_address,
            "gas": 3000000,
            "gasPrice": w3.to_wei("5", "gwei"),
        })
        
        return {"message": "Tier 1 Aggregation started successfully",
                "status": "success"}
    except Exception as e:
        print("Error starting Tier 1 Aggregation:", e)
        return {"message": str(e),
                "status": "error"}
        
     