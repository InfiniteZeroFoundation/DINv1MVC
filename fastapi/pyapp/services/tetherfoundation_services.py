from web3 import Web3
from dotenv import dotenv_values
import json   

from services.blockchain_services import get_w3

def get_TetherMock_Instance(tethermock_address=None):
    w3 = get_w3()
    if tethermock_address is None:
        tethermock_address = dotenv_values(".env").get("TetherMock_Contract_Address")
    
    with open("../../hardhat/artifacts/contracts/MockUSDT.sol/MockUSDT.json") as f:
        tethermock_data = json.load(f)
        tethermock_abi = tethermock_data["abi"]
        tethermock_bytecode = tethermock_data["bytecode"]
    
    if tethermock_address:
        deployed_TetherMockContract = w3.eth.contract(address=tethermock_address, abi=tethermock_abi)
        return deployed_TetherMockContract
    else:
        return w3.eth.contract(abi=tethermock_abi, bytecode=tethermock_bytecode)
        