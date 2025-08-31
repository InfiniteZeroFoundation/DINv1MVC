from fastapi import APIRouter, Depends
from pydantic import BaseModel
from dotenv import load_dotenv, set_key, unset_key, dotenv_values
import time
from services.DAO_services import get_DINtokenContract_Instance, get_DINValidatorStake_Instance, get_DINCoordinator_Instance
from services.blockchain_services import get_w3
from services.model_architect import get_DINTaskCoordinator_Instance, GIstatestrToIndex, GIstateToStr, get_DINTaskAuditor_Instance

router = APIRouter(prefix="/auditors", tags=["Auditors"])

@router.post("/getAuditorsState")
def get_auditors_state():
    try:
        
        env_config = dotenv_values(".env")
        
        w3 = get_w3()
        
        Auditors_Adresses = w3.eth.accounts[50:50+9]
        
        AuditorsETHBalances = []
        AuditorsDINtokenBalances = []
        AuditorsDinStakedTokens = []
        registered_auditors = []
        
        DINAuditorCoordinator_Contract_Address = env_config.get("DINAuditorCoordinator_Contract_Address")
        DinToken_Contract_Address = env_config.get("DINToken_Contract_Address")
        DinValidatorStake_Contract_Address = env_config.get("DINValidatorStake_Contract_Address")
        
        deployed_DINtokenContract = get_DINtokenContract_Instance(dintoken_address=DinToken_Contract_Address)
        
        for auditor_address in Auditors_Adresses:
            
            auditor_eth_balance = w3.from_wei(w3.eth.get_balance(auditor_address), 'ether')
            AuditorsETHBalances.append(auditor_eth_balance)
            
            if DinToken_Contract_Address is  not None:
                auditor_dintoken_balance = deployed_DINtokenContract.functions.balanceOf(auditor_address).call()
                AuditorsDINtokenBalances.append(auditor_dintoken_balance)
            else:
                AuditorsDINtokenBalances.append(0)
            
            if DinValidatorStake_Contract_Address is not None:
                deployed_DINValidatorStakeContract = get_DINValidatorStake_Instance(dinvalidatorstake_address=DinValidatorStake_Contract_Address)
                auditor_din_staked_tokens = deployed_DINValidatorStakeContract.functions.getStake(auditor_address).call()
                AuditorsDinStakedTokens.append(auditor_din_staked_tokens)
            else:
                AuditorsDinStakedTokens.append(0)
        
        return {"message": "Auditors state fetched successfully",
                "status": "success",
                "auditors_addresses": Auditors_Adresses,
                "registered_auditors": registered_auditors,
                "auditors_eth_balances": AuditorsETHBalances,
                "DINValidatorStakeAddress": DinValidatorStake_Contract_Address,
                "dintoken_address": DinToken_Contract_Address,
                "auditors_dintoken_balances": AuditorsDINtokenBalances,
                "auditors_din_staked_tokens": AuditorsDinStakedTokens
                
                }
    except Exception as e:
        return {"message": str(e),
                "status": "error"}

     
@router.post("/buyDINTokens")
def buy_dintokens():
    try:
        env_config = dotenv_values(".env")
        w3 = get_w3()
        
        
        Auditors_Adresses = w3.eth.accounts[50:50+9]
        
        DinToken_Contract_Address = env_config.get("DINToken_Contract_Address")
        
        deployed_DINtokenContract = get_DINtokenContract_Instance(dintoken_address=DinToken_Contract_Address)
        
        dincoordinator_contract_address = env_config.get("DINCoordinator_Contract_Address")
        
        deployed_dincoordinator = get_DINCoordinator_Instance(dincoordinator_address=dincoordinator_contract_address) 
        
        for auditor_address in Auditors_Adresses:
            tx_hash = deployed_dincoordinator.functions.depositAndMint().transact({
                "from": auditor_address,
                "gas": 3000000,
                "gasPrice": w3.to_wei("5", "gwei"),
                "value": w3.to_wei("1", "ether"),
            })
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            time.sleep(0.1)
        
        
        
        
        return {"message": "DIN tokens bought successfully",
                "status": "success"}

    except Exception as e:
        return {"message": str(e),
                "status": "error"}
        
        
class AuditorAddressRequest(BaseModel):
    auditor_address: str

@router.post("/buyDINTokensSingle")
def buy_dintokens_single(request: AuditorAddressRequest):
    try:
        auditor_address = request.auditor_address
        env_config = dotenv_values(".env")
        w3 = get_w3()
        print("Auditor address:", auditor_address)
        DinToken_Contract_Address = env_config.get("DINToken_Contract_Address")
        
        deployed_DINtokenContract = get_DINtokenContract_Instance(dintoken_address=DinToken_Contract_Address)
        
        dincoordinator_contract_address = env_config.get("DINCoordinator_Contract_Address")
        
        deployed_dincoordinator = get_DINCoordinator_Instance(dincoordinator_address=dincoordinator_contract_address) 
        
        tx_hash = deployed_dincoordinator.functions.depositAndMint().transact({
            "from": validator_address,
            "gas": 3000000,
            "gasPrice": w3.to_wei("5", "gwei"),
            "value": w3.to_wei("1", "ether"),
        })
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        time.sleep(0.1)
        
        return {"message": "DIN tokens bought successfully",
                "status": "success"}
        
        
    except Exception as e:
        return {"message": str(e),
                "status": "error"}

@router.post("/stakeDINTokens")
def stake_dintokens():
    try:
        env_config = dotenv_values(".env")
        w3 = get_w3()
        Auditors_Adresses = w3.eth.accounts[50:50+9]
        DinToken_Contract_Address = env_config.get("DINToken_Contract_Address")
        
        deployed_DINtokenContract = get_DINtokenContract_Instance(dintoken_address=DinToken_Contract_Address)
        
        DinValidatorStake_Contract_Address = env_config.get("DINValidatorStake_Contract_Address")
        
        deployed_DINValidatorStakeContract = get_DINValidatorStake_Instance(dinvalidatorstake_address=DinValidatorStake_Contract_Address)
        
        MIN_STAKE = 1000000
        
        for auditor_address in Auditors_Adresses:
            auditor_Din_token_balance = deployed_DINtokenContract.functions.balanceOf(auditor_address).call()
            if auditor_Din_token_balance >= MIN_STAKE:
                tx_approval_hash = deployed_DINtokenContract.functions.approve(DinValidatorStake_Contract_Address, MIN_STAKE).transact({"from": auditor_address})
                receipt = w3.eth.wait_for_transaction_receipt(tx_approval_hash)
                
                tx_stake_hash = deployed_DINValidatorStakeContract.functions.stake(MIN_STAKE).transact({"from": auditor_address})
                
                receipt = w3.eth.wait_for_transaction_receipt(tx_stake_hash)
      
        return {"message": "DIN tokens staked successfully",
                "status": "success"}          
                
    except Exception as e:
        return {"message": str(e),
                "status": "error"} 
        

@router.post("/stakeDINTokensSingle")
def stake_dintokens_single(request: AuditorAddressRequest): 
    try:    
        auditor_address = request.auditor_address
        env_config = dotenv_values(".env")
        w3 = get_w3()
        
        DinToken_Contract_Address = env_config.get("DINToken_Contract_Address")
        
        deployed_DINtokenContract = get_DINtokenContract_Instance(dintoken_address=DinToken_Contract_Address)
        
        DinValidatorStake_Contract_Address = env_config.get("DINValidatorStake_Contract_Address")
        
        deployed_DINValidatorStakeContract = get_DINValidatorStake_Instance(dinvalidatorstake_address=DinValidatorStake_Contract_Address)
        
        auditor_Din_token_balance = deployed_DINtokenContract.functions.balanceOf(auditor_address).call()
        
        if auditor_Din_token_balance >= MIN_STAKE:
            tx_approval_hash = deployed_DINtokenContract.functions.approve(DinValidatorStake_Contract_Address, MIN_STAKE).transact({"from": auditor_address})
            receipt = w3.eth.wait_for_transaction_receipt(tx_approval_hash)
            
            tx_stake_hash = deployed_DINValidatorStakeContract.functions.stake(MIN_STAKE).transact({"from": auditor_address})
            receipt = w3.eth.wait_for_transaction_receipt(tx_stake_hash)
        
            return {"message": "DIN tokens staked successfully",
                "status": "success"}          
                
    except Exception as e:
        return {"message": str(e),
                "status": "error"}      
        
        


                
            
        
        
    