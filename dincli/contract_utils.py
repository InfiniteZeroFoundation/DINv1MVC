from web3 import Web3
from dotenv import dotenv_values
import json   
from dincli.utils import get_w3
import os


def get_contract_instance(
    artifact_path: str,
    network: str,
    address: str | None = None
) :
    """
    Load a contract instance from an artifact (Hardhat format).
    
    Args:
        artifact_path: Path to JSON artifact (must have "abi")
        network: Target network (e.g., "local", "sepolia")
        address: If provided, returns deployed contract. If None, returns deployable contract (requires "bytecode").
    
    Returns:
        web3.contract.Contract
    """
    w3 = get_w3(network)
    
    if not os.path.isfile(artifact_path):
        raise FileNotFoundError(
            f"Contract artifact not found at: {artifact_path}\n"
            "Tip: Ensure the contract is compiled and the path is correct."
        )
    
    try:
        with open(artifact_path) as f:
            data = json.load(f)
    except JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse JSON in artifact: {artifact_path}\n"
            f"Reason: {str(e)}\n"
            "Tip: This may indicate a corrupted or incomplete build. Try recompiling the contract."
        ) from e
    
    if "abi" not in data:
        raise ValueError(f"Artifact {artifact_path} missing 'abi' field")
    abi = data["abi"]
    
    if address:
        # Interaction mode: only ABI needed
        return w3.eth.contract(address=address, abi=abi)
    else:
        # Deployment mode: bytecode required
        bytecode = data.get("bytecode")
        if not bytecode:
            raise ValueError(
                f"Artifact {artifact_path} missing 'bytecode' — required for deployment.\n"
                "Tip: Use `dincli dindao dump-abi --bytecode` to include it."
            )
        return w3.eth.contract(abi=abi, bytecode=bytecode)


# Optional: create thin aliases for clarity (no logic)
def get_DINCoordinator_Instance(artifact_path, network, address=None):
    return get_contract_instance(artifact_path, network, address)

def get_DINtokenContract_Instance(artifact_path, network, address=None):
    return get_contract_instance(artifact_path, network, address)

def get_DINValidatorStake_Instance(artifact_path, network, address=None):
    return get_contract_instance(artifact_path, network, address)