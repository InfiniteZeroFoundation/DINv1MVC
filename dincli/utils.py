import json
from web3 import Web3
from pathlib import Path
from platformdirs import user_config_dir
from typing import Optional
from eth_account import Account
import os

from .config.networks import NETWORKS

CONFIG_DIR = Path(user_config_dir("dincli"))
CONFIG_FILE = CONFIG_DIR / "config.json"

WALLET_FILE = CONFIG_DIR / "wallet.json"


# Optional: only import dotenv if needed
try:
    from dotenv import load_dotenv, dotenv_values
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False


def save_config(data):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Config saved to {CONFIG_FILE}")


def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            print(f"Config loaded from {CONFIG_FILE}")
            return json.load(f)
    print(f"No config found at {CONFIG_FILE}")
    return {}


def get_config(key):
    config = load_config()
    return config.get(key, None)

def load_usdt_config():
    config_path = Path(__file__).parent / "config" / "usdt_config.json"
    with open(config_path, "r") as f:
        return json.load(f)
    
def resolve_network(cli_network: str | None = None, default: str = "local") -> str:
    """
    Resolve network: use CLI arg if provided, else config, else default.
    """
    # 1. CLI takes highest precedence
    if cli_network is not None:
        return cli_network

    # 2. Check .env (ignore empty strings)
    from_env = get_env_key("network")
    if from_env and isinstance(from_env, str) and from_env.strip():
        return from_env.strip()

    # 3. Check global config
    cfg = load_config()
    from_config = cfg.get("network")
    if from_config and isinstance(from_config, str) and from_config.strip():
        return from_config.strip()

    # 4. Fallback
    return default

def resolve_ipfs_config():
    """
    Resolve ipfs config
    """
    default = "local"

    ipfs_api_url_add = "None"
    ipfs_api_url_retrieve = "None"

    # 2. Check .env (ignore empty strings)
    from_env = get_env_key("ipfs_api_url_add".upper())
    if from_env and isinstance(from_env, str) and from_env.strip():
        ipfs_api_url_add = from_env.strip()

    from_env = get_env_key("ipfs_api_url_retrieve".upper())
    if from_env and isinstance(from_env, str) and from_env.strip():
        ipfs_api_url_retrieve = from_env.strip()

    if ipfs_api_url_add == "None" or ipfs_api_url_retrieve == "None":
        ipfs_config_path = Path(__file__).parent / "config" / "ipfs_config.json"
        with open(ipfs_config_path, "r") as f:
            ipfs_config = json.load(f)
            ipfs_api_url_add = ipfs_config.get("local").get("ipfs_api_url_add")
            ipfs_api_url_retrieve = ipfs_config.get("local").get("ipfs_api_url_retrieve")

    return ipfs_api_url_add, ipfs_api_url_retrieve

def get_env_key(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get a key from:
    1. Current environment (e.g., SEPOLIA_RPC_URL)
    2. ./ .env file (if python-dotenv is installed)
    3. Default fallback
    """
    # 1. Already in environment? (e.g., from shell or parent process)
    if key in os.environ:
        return os.environ[key]

    # 2. Load from .env in current directory (if available)
    env_path = Path(".env")
    if HAS_DOTENV and env_path.exists():
        # Load .env into a dict (doesn't pollute os.environ)
        values = dotenv_values(dotenv_path=env_path)
        return values.get(key, default)

    return default


def resolve_network_value(
    network: str,
    key: str,
    default: Optional[str] = None
) -> str:
    """
    Resolve a network-specific config value with priority:
    1. .env in current directory (e.g., SEPOLIA_RPC_URL)
    2. Global user config (~/.din/config.json → config["networks"][network][key])
    3. Built-in defaults (NETWORKS[network][key])
    4. Fallback default (if provided)

    Example:
        resolve_network_value("sepolia", "rpc_url")
        → checks SEPOLIA_RPC_URL in .env, then config, then NETWORKS
    """
    if not network or not key:
        raise ValueError("network and key must be non-empty strings")
    
    # Normalize key to uppercase for .env (e.g., "rpc_url" → "RPC_URL")
    env_key_suffix = key.upper()
    env_var_name = f"{network.upper()}_{env_key_suffix}"
    
    
    # ✅ 1. Check .env in current working directory
    resolved_env_var_name = get_env_key(env_var_name)
    if resolved_env_var_name:
        return resolved_env_var_name
    
    
    # ✅ 2. Check global user config: ~/.din/config.json
    config = load_config()
    user_networks = config.get("networks", {})
    if network in user_networks and key in user_networks[network]:
        return user_networks[network][key]
    
    # ✅ 3. Check built-in defaults
    if network in NETWORKS and key in NETWORKS[network]:
        return NETWORKS[network][key]
    
    # ✅ 4. Fallback to provided default or raise error
    if default is not None:
        return default

    raise KeyError(
        f"Could not resolve '{key}' for network '{network}'.\n"
        f"→ Checked .env for '{env_var_name}'\n"
        f"→ Checked config.json → networks.{network}.{key}\n"
        f"→ Checked built-in NETWORKS['{network}']['{key}']\n"
        f"→ No fallback provided."
    )
    
        
def get_w3(effective_network):  
    try:  
        rpc_url = resolve_network_value(effective_network,"rpc_url")
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not w3.is_connected():
            raise ConnectionError(f"Could not connect to Ethereum node at {rpc_url}")
        return w3
    except Exception as e:
        raise ConnectionError(f"Could not connect to Ethereum node for network '{effective_network}': {e}") from e
    

def get_demo_private_key(account_index: int) -> str:
    """Load private key for Hardhat dev account by index."""
    # Path to accounts.json (relative to dincli package)
    accounts_file = Path(__file__).parent / "config" / "accounts.json"
    
    if not accounts_file.exists():
        raise FileNotFoundError(
            f"Demo accounts file not found: {accounts_file}\n"
            "Run `npx hardhat export-accounts` to generate it."
        )
    
    with open(accounts_file) as f:
        data = json.load(f)
    
    accounts = data.get("hardhat", [])
    if account_index < 0 or account_index >= len(accounts):
        raise IndexError(
            f"Account index {account_index} out of range. "
            f"Available: 0–{len(accounts) - 1}"
        )
    
    return accounts[account_index]["private_key"]


def load_account() -> Account:
    """Load wallet from ~/.din/wallet.json (handles demo + encrypted modes)."""


    if not WALLET_FILE.exists():
        print("[red]No wallet found. Run `dincli system connect-wallet` first.[/red]")
        raise typer.Exit(1)

    with open(WALLET_FILE) as f:
        data = json.load(f)

    # Demo mode: plaintext private key
    if data.get("demo_mode") is True:
        private_key = data["private_key"]
        return Account.from_key(private_key)

    # Encrypted mode: prompt for password
    password = getpass("Enter wallet password: ")
    try:
        private_key = Account.decrypt(data, password)
        return Account.from_key(private_key)
    except ValueError:
        raise ValueError("Invalid password or corrupted keystore.") 
    
    
def load_din_info() -> dict:
    path = Path(__file__).parent / "config" / "din_info.json"
    with open(path) as f:
        return json.load(f)

def save_din_info(data: dict):
    path = Path(__file__).parent / "config" / "din_info.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

stateDescription = [
        "Awaiting DINTaskAuditor to be set",
        "Awaiting DINTaskCoordinator to be set as slasher",
        "Awaiting DINTaskAuditor to be set as slasher",
        "Awaiting Genesis Model",
        "Genesis Model Created",
        "GI started",
        "DIN validator registration started",
        "DIN validator registration closed",
        "DIN auditor registration started",
        "DIN auditor registration closed",
        "LM submissions started",
        "LM submissions closed",
        "Auditors batches created",
        "LM submissions evaluation started",
        "LM submissions evaluation closed",
        "T1nT2B created",
        "T1B aggregation started",
        "T1B aggregation done",
        "T2B aggregation started",
        "T2B aggregation done",
        "Auditors slashed",
        "Validators slashed",
        "GI ended"
    ]

states = [
        "AwaitingDINTaskAuditorToBeSet",
        "AwaitingDINTaskCoordinatorAsSlasher",
        "AwaitingDINTaskAuditorAsSlasher",
        "AwaitingGenesisModel",
        "GenesisModelCreated",
        "GIstarted",
        "DINvalidatorRegistrationStarted",
        "DINvalidatorRegistrationClosed",
        "DINauditorRegistrationStarted",
        "DINauditorRegistrationClosed",
        "LMSstarted",
        "LMSclosed",
        "AuditorsBatchesCreated",
        "LMSevaluationStarted",
        "LMSevaluationClosed",
        "T1nT2Bcreated",
        "T1AggregationStarted",
        "T1AggregationDone",
        "T2AggregationStarted",
        "T2AggregationDone",
        "AuditorsSlashed",
        "ValidatorSlashed",
        "GIended"
    ]
    

GIstate_to_index = {state: idx for idx, state in enumerate(states)}  


def GIstateToDes(GIstate: int) -> str:

    if 0 <= GIstate < len(stateDescription):
        return stateDescription[GIstate]
    else:
        return f"UnknownState({GIstate})"
    

def GIstateToStr(GIstate: int) -> str:
    """
    Convert GIstate integer (from Solidity enum) to its string representation.
    Safe against errors by returning 'Unknown' for invalid states.
    """
    
    
    if 0 <= GIstate < len(states):
        return states[GIstate]
    else:
        return f"UnknownState({GIstate})"
    
def GIstatestrToIndex(GIstateStr: str) -> int:    
    return GIstate_to_index[GIstateStr]      