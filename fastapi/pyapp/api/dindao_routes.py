from fastapi import APIRouter, Depends
from services.blockchain_services import get_w3
from services.DAO_services import get_DINCoordinator_Instance, get_DINtokenContract_Instance, get_DINValidatorStake_Instance
from dotenv import load_dotenv, set_key, unset_key, dotenv_values

router = APIRouter(prefix="/dindao", tags=["DIN DAO"])

        
@router.post("/deployDINCoordinator")
def deploy_dincoordinator():
    try:
        
        w3 = get_w3()
        DINCoordinator_contract = get_DINCoordinator_Instance()
        
        constructor_tx_hash  = DINCoordinator_contract.constructor().transact({
            "from": w3.eth.accounts[0],
            "gas": 3000000,
            "gasPrice": w3.to_wei("5", "gwei"),
        })
        constructor_receipt = w3.eth.wait_for_transaction_receipt(constructor_tx_hash)
        dincoordinator_contract_address = constructor_receipt.contractAddress
        
        print("DINCoordinator contract deployed at:", dincoordinator_contract_address)
        
        
        set_key(".env", "DINCoordinator_Contract_Address", dincoordinator_contract_address)
        # Create contract instance
        deployed_DINCoordinatorContract = get_DINCoordinator_Instance(dincoordinator_address=dincoordinator_contract_address)
        
        DINCoordinator_Eth_balance = w3.from_wei(w3.eth.get_balance(dincoordinator_contract_address), 'ether')  
        
        env_config = dotenv_values(".env")
        dincoordinator_address = env_config.get("DINCoordinator_Contract_Address")
        
        
        dintoken_address = deployed_DINCoordinatorContract.functions.dintoken().call()
        
        set_key(".env", "DINToken_Contract_Address", dintoken_address)
        
        env_config = dotenv_values(".env")
        dintoken_address = env_config.get("DINToken_Contract_Address")
        
        
        w3.eth.accounts[0]
        
        return {"message": "DINCoordinator contract deployed successfully",
                "status": "success",
                "dincordinator_address": dincoordinator_address,
                "dintoken_address": dintoken_address,
                "DINDAORepresentative_address": w3.eth.accounts[0],
                "DINDAORepresentative_Eth_balance": w3.from_wei(w3.eth.get_balance(w3.eth.accounts[0]), 'ether'),
                "DINCoordinator_Eth_balance": DINCoordinator_Eth_balance}
    except Exception as e:
        return {"message": str(e),
                "status": "error",
                "dincordinator_address": None,
                "dintoken_address": None,
                "DINDAORepresentative_address": w3.eth.accounts[0],
                "DINDAORepresentative_Eth_balance": w3.from_wei(w3.eth.get_balance(w3.eth.accounts[0]), 'ether'),
                "DINCoordinator_Eth_balance": None}

@router.post("/deployDinValidatorStake")
def deploy_dinvalidatorstake():
    try:
        env_config = dotenv_values(".env")
        w3 = get_w3()
        
        DINValidatorStake_contract = get_DINValidatorStake_Instance()
        
        constructor_tx_hash  = DINValidatorStake_contract.constructor(env_config.get("DINToken_Contract_Address")).transact({
            "from": w3.eth.accounts[0],
            "gas": 3000000,
            "gasPrice": w3.to_wei("5", "gwei"),
        })
        constructor_receipt = w3.eth.wait_for_transaction_receipt(constructor_tx_hash)
        dinvalidatorstake_address = constructor_receipt.contractAddress
        
        set_key(".env", "DINValidatorStake_Contract_Address", dinvalidatorstake_address)
        
        print("DINValidatorStake contract deployed at:", dinvalidatorstake_address)
        
        return {"message": "DinValidatorStake contract deployed successfully",
                "status": "success",
                "dinvalidatorstake_address": dinvalidatorstake_address}
    except Exception as e:
        return {"message": str(e),
                "status": "error",
                "dinvalidatorstake_address": None}

@router.post("/getDINDAOState")
def get_dindao_state():
    try:
        env_config = dotenv_values(".env")
        DINCoordinator_Contract_Address = env_config.get("DINCoordinator_Contract_Address")
        DINToken_Contract_Address = env_config.get("DINToken_Contract_Address")
        w3 = get_w3()
        DINDAORepresentative_address = w3.eth.accounts[0]
        DINValidatorStake_Contract_Address = env_config.get("DINValidatorStake_Contract_Address")
        
        if DINCoordinator_Contract_Address is None:
            DINCoordinator_Eth_balance = 0
        else:
            DINCoordinator_Eth_balance = w3.from_wei(w3.eth.get_balance(DINCoordinator_Contract_Address), 'ether')    
            
        
        return {"message": "DINDAO state fetched successfully",
                "status": "success",
                "dincordinator_address": DINCoordinator_Contract_Address,
                "dintoken_address": DINToken_Contract_Address,
                "DINDAORepresentative_address": DINDAORepresentative_address,
                "DINDAORepresentative_Eth_balance": w3.from_wei(w3.eth.get_balance(DINDAORepresentative_address), 'ether'),
                "DINCoordinator_Eth_balance": DINCoordinator_Eth_balance,
                "DINValidatorStake_address": DINValidatorStake_Contract_Address}
    except Exception as e:
        return {"message": str(e),
                "status": "error"}