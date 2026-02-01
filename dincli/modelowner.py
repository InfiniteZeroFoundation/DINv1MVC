import typer
import os
from pathlib import Path
from rich import print
from rich.table import Table
from typing import Optional
from rich.console import Console
from dotenv import dotenv_values, set_key, get_key, unset_key
from dincli.utils import resolve_network, get_w3, load_account, load_din_info, load_usdt_config, GIstatestrToIndex, GIstateToStr, load_custom_fn, cache_manifest, get_manifest_key, CACHE_DIR, is_ethereum_address
from dincli.contract_utils import get_contract_instance
from dincli.services.ipfs import retrieve_from_ipfs, upload_to_ipfs
from dincli.system import connect_wallet
from dincli.services.modelowner import getGenesisModelIpfs, getscoreforGM, create_audit_testDataCIDs

app = typer.Typer(help="Commands for Model Owners in DIN.")

# Deploy sub-app (for 'dincli modelowner deploy ...')
deploy_app = typer.Typer(help="Deploy task-level smart contracts")

model_app = typer.Typer(help="Model-level commands")
gi_app = typer.Typer(help="Global iteration commands")
aggregation_app = typer.Typer(help="Aggregation commands")
lms_app = typer.Typer(help="Local Model Submission commands")
auditor_batches_app = typer.Typer(help="Auditor Batches commands")
lms_evaluation_app = typer.Typer(help="Local Model Submission Evaluation commands")
slash_app = typer.Typer(help="Slash commands")

app.add_typer(deploy_app, name="deploy")
app.add_typer(model_app, name="model")
app.add_typer(gi_app, name="gi")
app.add_typer(aggregation_app, name="aggregation")
app.add_typer(lms_app, name="lms")
app.add_typer(auditor_batches_app, name="auditor-batches")
app.add_typer(lms_evaluation_app, name="lms-evaluation")
app.add_typer(slash_app, name="slash")

reg_app = typer.Typer(help="Registration commands for a Global Iteration")
gi_app.add_typer(reg_app, name="reg")

t1_app = typer.Typer(help="Tier 1 commands")
t2_app = typer.Typer(help="Tier 2 commands")
aggregation_app.add_typer(t1_app, name="T1")
aggregation_app.add_typer(t2_app, name="T2")

console = Console()

@deploy_app.command()
def task_coordinator(
    network: str = typer.Option(None, "--network", help="Target network (local|sepolia|mainnet)"),
    artifact_path: str = typer.Option(..., "--artifact", help="Path to DINTaskCoordinator contract artifact JSON (Hardhat format). "),
    din_validator_stake: str = typer.Option(None, "--din-validator-stake", help="DINValidatorStake contract address. If not provided, reads from .env or din_info.json")
):
    """
    Deploy the DINTaskCoordinator contract.
    """
    effective_network = resolve_network(network)
    
    w3 = get_w3(effective_network)

    # Load contract instance
    DINTaskCoordinator_contract = get_contract_instance(artifact_path, effective_network)
    
    # Load account
    account = load_account()
    
    # Resolve DINValidatorStake address
    if din_validator_stake:
        din_validator_stake_address = din_validator_stake
    else:
        # Try .env first
        env_config = dotenv_values(".env")
        din_validator_stake_address = env_config.get("DINValidatorStake_Contract_Address")
        
        # If not in .env, try din_info.json
        if not din_validator_stake_address:
            din_info = load_din_info()
            if effective_network in din_info and "stake" in din_info[effective_network]:
                din_validator_stake_address = din_info[effective_network]["stake"]
        
        if not din_validator_stake_address:
            print("[red]Error:[/red] DINValidatorStake contract address not found.")
            print("[yellow]Please provide --din-validator-stake or ensure it's set in .env or din_info.json[/yellow]")
            raise typer.Exit(1)
    
    print(f"[bold green]Deploying DINTaskCoordinator on network:[/bold green] {effective_network}")
    print(f"[cyan]Using DINValidatorStake:[/cyan] {din_validator_stake_address}")
    
    # Get nonce
    nonce = w3.eth.get_transaction_count(account.address)
    
    # Build deployment transaction
    tx = DINTaskCoordinator_contract.constructor(din_validator_stake_address).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": int(2.5 * 3000000),  # Match FastAPI route
        "gasPrice": w3.to_wei("5", "gwei"),
        "chainId": w3.eth.chain_id,
    })
    
    # Sign transaction
    signed_tx = account.sign_transaction(tx)
    
    # Send raw transaction
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    dintaskcoordinator_contract_address = tx_receipt.contractAddress
    
    print(f"[bold green]✓ DINTaskCoordinator contract deployed at:[/bold green] {dintaskcoordinator_contract_address}")
    
    # Save to .env
    env_path = Path(".env")
    if env_path.exists():
        set_key(".env", effective_network.upper()+"_DINTaskCoordinator_Contract_Address", dintaskcoordinator_contract_address)
        print(f"[green]✓ Saved DINTaskCoordinator address to {os.getcwd()}/.env as {effective_network.upper()}_DINTaskCoordinator_Contract_Address[/green]")
    else:
        print(f"[yellow]Warning:[/yellow] .env file not found. Address not saved.")
        print(f"[yellow]Please manually add to {os.getcwd()}/.env:[/yellow] {effective_network.upper()}_DINTaskCoordinator_Contract_Address={dintaskcoordinator_contract_address}")


@deploy_app.command()
def task_auditor(
    network: str = typer.Option(None, "--network", help="Target network (local|sepolia|mainnet)"),
    artifact_path: str = typer.Option(..., "--artifact", help="Path to DINTaskAuditor contract artifact JSON (Hardhat format)."),
    task_coordinator: str = typer.Option(None, "--taskCoordinator", help="DINTaskCoordinator contract address"),
    usdt_contract: str = typer.Option(None, "--usdt-contract", help="USDT contract address. If not provided, reads from .env or din_info.json"),
    din_validator_stake: str = typer.Option(None, "--din-validator-stake", help="DINValidatorStake contract address. If not provided, reads from .env or din_info.json"),
    task_coordinator_artifact: str = typer.Option(None, "--task-coordinator-artifact", help="Path to DINTaskCoordinator artifact (needed to call setDINTaskAuditorContract). If not provided, tries to find it automatically")
):
    """
    Deploy the DINTaskAuditor contract.
    """
    effective_network = resolve_network(network)
    
    w3 = get_w3(effective_network)
    
    # Load contract instance
    DINTaskAuditor_contract = get_contract_instance(artifact_path, effective_network)
    
    # Load account
    account = load_account()
    
    # Resolve USDT contract address
    if usdt_contract:
        usdt_contract_address = usdt_contract
    else:
        env_config = dotenv_values(".env")


        usdt_contract_address = env_config.get(effective_network.upper() + "_USDT_Contract_Address")
        if not usdt_contract_address:

            usdt_config = load_usdt_config()
            if effective_network in usdt_config and "usdt" in usdt_config[effective_network]:
                usdt_contract_address = usdt_config[effective_network]["usdt"]

            if not usdt_contract_address:
                print("[red]Error:[/red] USDT contract address not found.")
                print("[yellow]Please provide --usdt-contract or ensure " + effective_network.upper() + "_USDT_Contract_Address is set in .env[/yellow]")
                raise typer.Exit(1)
    
    # Resolve DINValidatorStake address
    if din_validator_stake:
        din_validator_stake_address = din_validator_stake
    else:
        env_config = dotenv_values(".env")
        din_validator_stake_address = env_config.get(effective_network.upper() + "_DINValidatorStake_Contract_Address")
        
        # If not in .env, try din_info.json
        if not din_validator_stake_address:
            din_info = load_din_info()
            if effective_network in din_info and "stake" in din_info[effective_network]:
                din_validator_stake_address = din_info[effective_network]["stake"]
        
        if not din_validator_stake_address:
            print("[red]Error:[/red] DINValidatorStake contract address not found.")
            print("[yellow]Please provide --din-validator-stake or ensure " + effective_network.upper() + "_DINValidatorStake_Contract_Address is set in .env or din_info.json[/yellow]")
            raise typer.Exit(1)

    # Resolve DINTaskCoordinator address
    if task_coordinator:
        task_coordinator_address = task_coordinator
    else:
        env_config = dotenv_values(".env")
        task_coordinator_address = env_config.get(effective_network.upper()+"_DINTaskCoordinator_Contract_Address")
        
        if not task_coordinator_address:
            print("[red]Error:[/red] DINTaskCoordinator contract address not found.")
            print(f"[yellow]Please provide --task-coordinator or ensure {effective_network.upper()}_DINTaskCoordinator_Contract_Address is set in {os.getcwd()}/.env[/yellow]")
            raise typer.Exit(1)
    
    print(f"[bold green]Deploying DINTaskAuditor on network:[/bold green] {effective_network}")
    print(f"[cyan]Using USDT address:[/cyan] {usdt_contract_address}")
    print(f"[cyan]Using DINValidatorStake address:[/cyan] {din_validator_stake_address}")
    print(f"[cyan]Using DINTaskCoordinator address:[/cyan] {task_coordinator_address}")
    
     
    # Get nonce
    nonce = w3.eth.get_transaction_count(account.address)
    
    # Build deployment transaction
    tx = DINTaskAuditor_contract.constructor(
        usdt_contract_address,
        din_validator_stake_address,
        task_coordinator_address
    ).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": int(2.5 * 3000000),  # Match FastAPI route
        "gasPrice": w3.to_wei("5", "gwei"),
        "chainId": w3.eth.chain_id,
    })
    
    # Sign transaction
    signed_tx = account.sign_transaction(tx)
    
    # Send raw transaction
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    dintaskauditor_contract_address = tx_receipt.contractAddress
    
    print(f"[bold green]✓ DINTaskAuditor contract deployed at:[/bold green] {dintaskauditor_contract_address}")
    
    # Save to .env
    env_path = Path(".env")
    if env_path.exists():
        set_key(".env", effective_network.upper() + "_"+task_coordinator_address+"_DINTaskAuditor_Contract_Address", dintaskauditor_contract_address)
        print(f"[green]✓ Saved DINTaskAuditor address to {os.getcwd()}/.env as {effective_network.upper()}_"+task_coordinator_address+"_DINTaskAuditor_Contract_Address[/green]")
    else:
        print(f"[yellow]Warning:[/yellow] .env file not found. Address not saved.")
        print(f"[yellow]Please manually add to .env:[/yellow] {effective_network.upper()}_"+task_coordinator_address+"_DINTaskAuditor_Contract_Address={dintaskauditor_contract_address}")
    
    # Set DINTaskAuditor in DINTaskCoordinator
    print(f"[cyan]Setting DINTaskAuditor in DINTaskCoordinator...[/cyan]")
    
    # Resolve DINTaskCoordinator artifact path
    if task_coordinator_artifact is None:
        # Try to find artifact file
        task_coordinator_artifact = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
        if not task_coordinator_artifact.exists():
            print(f"[yellow]Warning:[/yellow] DINTaskCoordinator artifact not found at {task_coordinator_artifact}")
            print(f"[yellow]Skipping setDINTaskAuditorContract call on DINTaskCoordinator. Please call it manually.[/yellow]")
            return dintaskauditor_contract_address
    
    # Load DINTaskCoordinator contract instance
    DINTaskCoordinator_contract = get_contract_instance(str(task_coordinator_artifact), effective_network, task_coordinator_address)
    
    # Get nonce for the setDINTaskAuditorContract call
    nonce = w3.eth.get_transaction_count(account.address)
    
    # Build transaction to set DINTaskAuditor in DINTaskCoordinator
    tx = DINTaskCoordinator_contract.functions.setDINTaskAuditorContract(dintaskauditor_contract_address).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": int(2.5 * 3000000),
        "gasPrice": w3.to_wei("5", "gwei"),
        "chainId": w3.eth.chain_id,
    })
    
    # Sign transaction
    signed_tx = account.sign_transaction(tx)
    
    # Send raw transaction
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    if tx_receipt.status == 1:
        print(f"[bold green]✓ DINTaskAuditor contract set in DINTaskCoordinator[/bold green]")
    else:
        print(f"[red]Error:[/red] Failed to set DINTaskAuditor in DINTaskCoordinator")
    
    return dintaskauditor_contract_address
    
    

    
@app.command("deposit-reward-in-dintask-auditor")
def deposit_reward_in_dintask_auditor(
    network: str = typer.Option(None, "--network", help="Target network (local|sepolia|mainnet)"),
    amount: int = typer.Option(..., "--amount", help="Amount of rewards to deposit in USDT"),
    dintask_auditor: str = typer.Option(None, "--dintask-auditor", help="DINTaskAuditor contract address"),
    usdt_contract: str = typer.Option(None, "--usdt-contract", help="USDT contract address. If not provided, reads from .env or usdt_config.json")
):
    """
    Deposit rewards into the DINTaskAuditor contract.
    """
    effective_network = resolve_network(network)
    
    w3 = get_w3(effective_network)
    
    # Load account
    account = load_account()
    
    # Resolve USDT contract address
    if usdt_contract:
        usdt_address = usdt_contract
    else:
        env_config = dotenv_values(".env")
        usdt_address = env_config.get(effective_network.upper() + "_USDT_Contract_Address")
        
        if not usdt_address:
            usdt_config = load_usdt_config()
            if effective_network in usdt_config and "usdt" in usdt_config[effective_network]:
                usdt_address = usdt_config[effective_network]["usdt"]
                
        if not usdt_address:
            print("[red]Error:[/red] USDT contract address not found.")
            print("[yellow]Please provide --usdt-contract or ensure " + effective_network.upper() + "_USDT_Contract_Address is set in .env[/yellow]")
            raise typer.Exit(1)

    # Resolve DINTaskAuditor address
    if dintask_auditor:
        dintask_auditor_address = dintask_auditor
    else:
        # Reuse env_config already loaded above (or reload if needed)
        env_config = dotenv_values(".env")
    
        # Step 1: Get Task Coordinator address
        task_coordinator_key = f"{effective_network.upper()}_DINTaskCoordinator_Contract_Address"
        task_coordinator_address = env_config.get(task_coordinator_key)

        if not task_coordinator_address:
            print("[red]Error:[/red] DINTaskCoordinator contract address not found.")
            print(f"[yellow]Please ensure {task_coordinator_key} is set in {os.getcwd()}/.env[/yellow]")
            raise typer.Exit(1)
    
        # Step 2: Use it to build the Auditor key
        auditor_key = f"{effective_network.upper()}_{task_coordinator_address}_DINTaskAuditor_Contract_Address"
        dintask_auditor_address = env_config.get(auditor_key)
        
        if not dintask_auditor_address:
            print("[red]Error:[/red] DINTaskAuditor contract address not found.")
            print(f"[yellow]Please ensure {auditor_key} is set in {os.getcwd()}/.env[/yellow]")
            raise typer.Exit(1)

    print(f"[bold green]Depositing rewards on network:[/bold green] {effective_network}")
    print(f"[cyan]Using USDT address:[/cyan] {usdt_address}")
    print(f"[cyan]Using DINTaskAuditor address:[/cyan] {dintask_auditor_address}")
    print(f"[cyan]Amount:[/cyan] {amount}")

    # Load USDT contract (ERC20)
    # We need a generic ERC20 ABI or just the USDT ABI. 
    # Assuming DinToken.json is an ERC20 compliant token which we can use for ABI.
    # Or we can use a minimal ABI for approve.
    
    # Minimal ERC20 ABI (enough for approve + decimals + balanceOf)
    erc20_abi = [
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function",
        },
        {
            "constant": True,
            "inputs": [{"name": "owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "", "type": "uint256"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function",
        },
        {
        "constant": True,
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"},
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function",
        },
        {
            "constant": False,
            "inputs": [
                {"name": "spender", "type": "address"},
                {"name": "value", "type": "uint256"},
            ],
            "name": "approve",
            "outputs": [{"name": "", "type": "bool"}],
            "payable": False,
            "stateMutability": "nonpayable",
            "type": "function",
        },
        
        # --- Added: transfer ---
        {
            "constant": False,
            "inputs": [
                {"name": "to", "type": "address"},
                {"name": "value", "type": "uint256"},
            ],
            "name": "transfer",
            "outputs": [{"name": "", "type": "bool"}],
            "payable": False,
            "stateMutability": "nonpayable",
            "type": "function",
        },
        # --- Added: transferFrom ---
        {
            "constant": False,
            "inputs": [
                {"name": "from", "type": "address"},
                {"name": "to", "type": "address"},
                {"name": "value", "type": "uint256"},
            ],
            "name": "transferFrom",
            "outputs": [{"name": "", "type": "bool"}],
            "payable": False,
            "stateMutability": "nonpayable",
            "type": "function",
        }
    ]

    
    usdt_contract_instance = w3.eth.contract(address=usdt_address, abi=erc20_abi)

    # Get decimals
    decimals = usdt_contract_instance.functions.decimals().call()

    amount_wei = int(amount * (10 ** decimals))

    sender_balance = usdt_contract_instance.functions.balanceOf(account.address).call()

    if sender_balance < amount_wei:
        human_balance = sender_balance / (10 ** decimals)
        console.print(f"[red]Error:[/red] Insufficient USDT balance.")
        console.print(f"[yellow]Available: {human_balance:.6f} USDT | Requested: {amount} USDT[/yellow]")
        raise typer.Exit(1)

    # Load DINTaskAuditor contract
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskAuditor.json"
    if not artifact_path.exists():
         print(f"[red]Error:[/red] DINTaskAuditor artifact not found at {artifact_path}")
         raise typer.Exit(1)

    DINTaskAuditor_contract = get_contract_instance(str(artifact_path), effective_network, dintask_auditor_address)

    # --- Print summary ---
    console.print(f"[bold green]Depositing {amount} USDT on network:[/bold green] {effective_network}")
    console.print(f"[cyan]USDT contract:[/cyan] {usdt_address}")
    console.print(f"[cyan]DINTaskAuditor:[/cyan] {dintask_auditor_address}")
    console.print(f"[cyan]From account:[/cyan] {account.address}")


    current_allowance = usdt_contract_instance.functions.allowance(account.address, dintask_auditor_address).call()

    if current_allowance > 0  and current_allowance != amount_wei:
        console.print(f"[yellow]Resetting existing allowance of {current_allowance / (10 ** decimals):.6f} USDT to 0 for USDT compatibility...[/yellow]")
        reset_tx = usdt_contract_instance.functions.approve(dintask_auditor_address, 0).build_transaction({
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 60000,
            "gasPrice": w3.to_wei("5", "gwei"),
            "chainId": w3.eth.chain_id,
        })
        signed = account.sign_transaction(reset_tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        console.print(f"[dim]Reset tx: {tx_hash.hex()}[/dim]")
        w3.eth.wait_for_transaction_receipt(tx_hash)
        console.print("[green]✓ Reset allowance[/green]")

    if current_allowance != amount_wei or current_allowance == 0:
        # --- Step 1: Approve ---
        console.print(f"[cyan]Approving DINTaskAuditor to spend {amount} USDT...[/cyan]")
        nonce = w3.eth.get_transaction_count(account.address)
        approve_tx = usdt_contract_instance.functions.approve(dintask_auditor_address, amount_wei).build_transaction({
            "from": account.address,
            "nonce": nonce,
            "gas": 100_000,
            "gasPrice": w3.to_wei("5", "gwei"),
            "chainId": w3.eth.chain_id,
        })
        signed = account.sign_transaction(approve_tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        console.print(f"[dim]Approve tx:[/dim] {tx_hash.hex()}")
        w3.eth.wait_for_transaction_receipt(tx_hash)
        console.print("[green]✓ Approval confirmed[/green]")


    owner = DINTaskAuditor_contract.functions.owner().call()
    console.print(f"[cyan]Owner:[/cyan] {owner}")
    mock_addr_in_contract = DINTaskAuditor_contract.functions.mockusdt().call()
    console.print(f"[cyan]mockusdt in contract:[/cyan] {mock_addr_in_contract}")
    console.print(f"[cyan]USDT address used in CLI:[/cyan] {usdt_address}")

    usdt_balance = usdt_contract_instance.functions.balanceOf(account.address).call()
    console.print(f"[cyan]USDT balance:[/cyan] {usdt_balance / (10 ** decimals):.6f}")
    console.print(f"[cyan]USDT allowance:[/cyan] {usdt_contract_instance.functions.allowance(account.address, dintask_auditor_address).call() / (10 ** decimals):.6f}")



    # --- Step 2: Deposit ---
    console.print("[cyan]Calling depositReward...[/cyan]")
    nonce = w3.eth.get_transaction_count(account.address)
    deposit_tx = DINTaskAuditor_contract.functions.depositReward(amount_wei).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 200_000,
        "gasPrice": w3.to_wei("5", "gwei"),
        "chainId": w3.eth.chain_id,
    })
    signed = account.sign_transaction(deposit_tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    console.print(f"[dim]Deposit tx:[/dim] {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt.status != 1:
        console.print("[red]✗ Deposit transaction reverted[/red]")
        raise typer.Exit(1)

    # --- Final balances (optional but useful for CLI feedback) ---
    final_sender = usdt_contract_instance.functions.balanceOf(account.address).call() / (10 ** decimals)
    final_auditor = usdt_contract_instance.functions.balanceOf(dintask_auditor_address).call() / (10 ** decimals)
    eth_balance = w3.from_wei(w3.eth.get_balance(account.address), "ether")

    console.print("[bold green]✓ Rewards deposited successfully![/bold green]")
    console.print(f"[cyan]Your USDT balance:[/cyan] {final_sender:.6f}")
    console.print(f"[cyan]Auditor USDT balance:[/cyan] {final_auditor:.6f}")
    console.print(f"[cyan]Your ETH balance:[/cyan] {eth_balance:.6f} ETH")


    owner = DINTaskAuditor_contract.functions.owner().call()
    console.print(f"[cyan]Owner of DINTaskAuditor:[/cyan] {owner}")
    return


@app.command()
def add_slasher(
    task_coordinator_flag: bool = typer.Option(False, "--taskCoordinator", help="Add task coordinator as slasher"),
    task_auditor_flag: bool = typer.Option(False, "--taskAuditor", help="Add task auditor as slasher"),
    network: str = typer.Option(None, "--network", help="Network to use"),
    contract_address: str = typer.Option(None, "--contract", help="Contract address to use DIN Task Coordinator"),
):

    effective_network = resolve_network(network)
    if not effective_network:
        console.print("[red]Error:[/red] Invalid network specified")
        raise typer.Exit(1)

    w3 = get_w3(effective_network)
    if not w3:
        console.print("[red]Error:[/red] Failed to connect to network")
        raise typer.Exit(1)

    account = load_account()


    env_config = dotenv_values(".env")

    if task_coordinator_flag and task_auditor_flag:
        console.print("[red]Error:[/red] Cannot add both task coordinator and task auditor as slashers simultaneously")
        raise typer.Exit(1)
    elif not task_coordinator_flag and not task_auditor_flag:
        console.print("[red]Error:[/red] You must specify either --taskCoordinator or --taskAuditor")
        raise typer.Exit(1)


    if not contract_address:
        
        contract_address = env_config[effective_network.upper() + "_DINTaskCoordinator_Contract_Address"]

        if not contract_address:
            console.print(f"[bold red] X {effective_network.upper()}_DINTaskCoordinator_Contract_Address not found in {os.getcwd()}/.env file[/bold red]")
            raise typer.Exit(1)


    # --- Print summary ---
    console.print(f"[bold green]Adding slasher on network:[/bold green] {effective_network}")
    console.print(f"[cyan]DIN Task Coordinator Contract:[/cyan] {contract_address}")
    console.print(f"[cyan]From account:[/cyan] {account.address}")

    # --- Step 1: Add slasher ---

    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"

    # if artifact_path does not exist, raise error
    if not artifact_path.exists():
        console.print("[red]Error:[/red] ABI file not found")
        raise typer.Exit(1)
    

    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, contract_address)

    if task_coordinator_flag:
        console.print("[cyan]Confirming DIN Task Coordinator as slasher...[/cyan]")
        nonce = w3.eth.get_transaction_count(account.address)
        add_slasher_tx = deployed_DINTaskCoordinatorContract.functions.setDINTaskCoordinatorAsSlasher().build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 200_000,
        "gasPrice": w3.to_wei("5", "gwei"),
        "chainId": w3.eth.chain_id,
        })
        signed = account.sign_transaction(add_slasher_tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        console.print(f"[dim]Confirming DIN Task Coordinator as slasher tx:[/dim] {tx_hash.hex()}")
        w3.eth.wait_for_transaction_receipt(tx_hash)
        console.print("[green]✓ DIN Task Coordinator confirmed as slasher![/green]")

    if task_auditor_flag:
        console.print("[cyan]Confirming DIN Task Auditor as slasher...[/cyan]")
        nonce = w3.eth.get_transaction_count(account.address)
        add_slasher_tx = deployed_DINTaskCoordinatorContract.functions.setDINTaskAuditorAsSlasher().build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 200_000,
        "gasPrice": w3.to_wei("5", "gwei"),
        "chainId": w3.eth.chain_id,
        })
        signed = account.sign_transaction(add_slasher_tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        console.print(f"[dim]Confirming DIN Task Auditor as slasher tx:[/dim] {tx_hash.hex()}")
        w3.eth.wait_for_transaction_receipt(tx_hash)
        console.print("[green]✓ DIN Task Auditor confirmed as slasher![/green]")

    return

@model_app.command("create-genesis")
def create_genesis(
    network: str = typer.Option(None, "--network", help="Network to use"),
    help: bool = typer.Option(False, "--help","-h", help="Show help"),
    default: bool = typer.Option(False, "--default", help="use default service"),
    task_coordinator_address: str = typer.Option(None, "--taskCoordinator", help="Task coordinator address"),
):
    effective_network = resolve_network(network)

    if not task_coordinator_address:
        task_coordinator_address = get_key(".env", effective_network.upper() + "_DINTaskCoordinator_Contract_Address")
        if not task_coordinator_address:
            console.print(f"[bold red] X {effective_network.upper()}_DINTaskCoordinator_Contract_Address not found in {os.getcwd()}/.env file[/bold red]")
            raise typer.Exit(1)

    if help:
        console.print("[bold green]Usage:[/bold green]")
        console.print("  dincli model-owner model create-genesis --network <network>")
        console.print("\nIf --default flag is not specified, dincli will use getGenesisModelIpfs() from")
        console.print(f"{Path(os.getcwd()) / 'tasks' / effective_network.lower() / task_coordinator_address / 'services' / 'modelowner.py'}")
        console.print(f"The genesis model hash will be set in {os.getcwd()}/.env under {effective_network.upper() + "_" + task_coordinator_address}_GENESIS_MODEL_IPFS_HASH")
        raise typer.Exit(0)

    
    if not default:
        ### Start - To Delete ###
        tasks_dir = Path.cwd() / 'tasks' / effective_network.lower()
        # Ensure tasks_dir exists
        if not tasks_dir.exists():
            raise FileNotFoundError(f"Tasks directory not found: {tasks_dir}")
        # Find all subdirs that look like Ethereum addresses
        eth_like_subdirs = [
            p for p in tasks_dir.iterdir()
            if p.is_dir() and is_ethereum_address(p.name)
        ]

        # Check if target already exists
        target_folder = tasks_dir / task_coordinator_address

        target_normalized = task_coordinator_address.lower()

        # Check if target already exists (case-insensitively)
        target_exists = any(
            p.name.lower() == target_normalized for p in eth_like_subdirs
        )

        if not target_exists:
            # Filter out the target itself just in case (shouldn't be needed, but safe)
            candidates = [p for p in eth_like_subdirs if p.name.lower() != target_normalized]
            if len(candidates) == 1:
                # Exactly one folder exists → assume it's the one to rename
                old_folder = candidates[0]
                console.print(f"Auto-renaming task coordinator folder: {old_folder.name} → {task_coordinator_address}")
                old_folder.rename(target_folder)
            elif len(candidates) == 0:
                raise FileNotFoundError(
                    f"No existing Ethereum-like coordinator folder found in {tasks_dir}, "
                    f"and target '{task_coordinator_address}' does not exist."
                )
            else:
                raise RuntimeError(
                    f"Multiple Ethereum-like coordinator folders found, but target is missing. "
                    f"Cannot auto-rename. Candidates: {[p.name for p in candidates]}"
                )
        ### End - To Delete ###
        # Construct the path

        if get_manifest_key(effective_network, "getGenesisModelIpfs", None, task_coordinator_address)["type"] == "custom":
            service_path_str = get_manifest_key(effective_network, "getGenesisModelIpfs", None, task_coordinator_address)["path"]
            service_path = Path(service_path_str)

        file_path = Path.cwd() / 'tasks' / effective_network.lower() / task_coordinator_address / service_path
        if not file_path.exists():
            raise FileNotFoundError(f"Required file does not exist: {file_path}")

        console.print("[bold green]Creating genesis model...[/bold green]")
        fn = load_custom_fn(
            file_path,
            "getGenesisModelIpfs"
        )
        base_path = Path(os.getcwd()) / "tasks" / effective_network.lower() / task_coordinator_address
        model_hash = fn(base_path)
    else:
        model_hash = getGenesisModelIpfs(base_path = Path(os.getcwd()) / "tasks" / effective_network.lower() / task_coordinator_address)
    
    
    console.print(f"[bold green]Genesis model created successfully![/bold green]")
    console.print(f"[cyan]Model hash:[/cyan] {model_hash}")

    # set in .env
    set_key(".env", effective_network.upper() + "_" + task_coordinator_address + "_GENESIS_MODEL_IPFS_HASH", model_hash)
    
    return

@model_app.command("submit-genesis")
def submit_genesis(
    network: str = typer.Option(None, "--network", help="Network to use"),
    ipfs_hash: str = typer.Option(None, "--ipfs-hash", help="IPFS hash of the model"),
    task_coordinator_address: str = typer.Option(None, "--taskCoordinator", help="Task coordinator address"),
    score: int = typer.Option(None, "--score", help="Score of the model"),
    default: bool = typer.Option(False, "--default", help="use default service"),
    help: bool = typer.Option(False, "--help","-h", help="Show help"),
):
    effective_network = resolve_network(network)

    if not task_coordinator_address:
        task_coordinator_address = get_key(".env", effective_network.upper() + "_DINTaskCoordinator_Contract_Address")
        if not task_coordinator_address:
            console.print(f"[bold red] X {effective_network.upper()}_DINTaskCoordinator_Contract_Address not found in {os.getcwd()}/.env file[/bold red]")
            raise typer.Exit(1)
    
    if help:
        console.print("[bold green]Usage:[/bold green]")
        console.print("  dincli model-owner model submit-genesis --network <network>")
        console.print("\nIf --default flag is not specified, dincli will use submitGenesisModel() from")
        console.print(f"{Path(os.getcwd()) / 'tasks' / effective_network.lower() / task_coordinator_address / 'services' / 'modelowner.py'}")
        console.print("\n [yellow]Warning:[/yellow] the test dataset must be available at: ")
        console.print(f"  {Path(os.getcwd()) / effective_network.lower() / task_coordinator_address / 'dataset' / 'test' / 'test_dataset.pt'}")
        console.print("\n [yellow]Warning:[/yellow] the genesis model must be available at: ")
        console.print(f"  {Path(os.getcwd()) / effective_network.lower() / task_coordinator_address / 'models' / 'genesis_model.pth'}")
        console.print(f"\n [yellow]Warning:[/yellow] If --ipfs-hash is not specified, the genesis model IPFS hash will be read from {os.getcwd()}/.env under {effective_network.upper() + "_" + task_coordinator_address + "_GENESIS_MODEL_IPFS_HASH"}")
        raise typer.Exit(0)


    w3 = get_w3(effective_network)
    
    account = load_account()
    
    if not ipfs_hash:
        ipfs_hash = get_key(".env", effective_network.upper() + "_" + task_coordinator_address + "_GENESIS_MODEL_IPFS_HASH")
    
    console.print(f"[bold green]Submitting genesis model to DIN Task Coordinator![/bold green]")
    console.print(f"[cyan]IPFS hash:[/cyan] {ipfs_hash}")
    console.print(f"[cyan]Task coordinator address:[/cyan] {task_coordinator_address}")
    console.print(f"[cyan]From account:[/cyan] {account.address}")
    
    # --- Step 1: Submit genesis model ---
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"

    # if artifact_path does not exist, raise error
    if not artifact_path.exists():
        console.print("[red]Error:[/red] ABI file not found")
        raise typer.Exit(1)

    if score:
        accuracy = score
    else:
        if not default:
            tasks_dir = Path.cwd() / 'tasks' / effective_network.lower()
            target_folder = tasks_dir / task_coordinator_address


            if get_manifest_key(effective_network, "getscoreforGM", None, task_coordinator_address)["type"] == "custom":
                service_path_str = get_manifest_key(effective_network, "getscoreforGM", None, task_coordinator_address)["path"]
                service_path = target_folder / Path(service_path_str)

                if not service_path.exists():
                    retrieve_from_ipfs(get_manifest_key(effective_network,"getscoreforGM", None, task_coordinator_address)["ipfs"], service_path)
                
                model_service_path_str = target_folder / get_manifest_key(effective_network, "ModelArchitecture", None, task_coordinator_address)["path"]
                model_service_path = target_folder / Path(model_service_path_str)

                if not model_service_path.exists():
                    retrieve_from_ipfs(get_manifest_key(effective_network,"ModelArchitecture", None, task_coordinator_address)["ipfs"], model_service_path)
                fn = load_custom_fn(service_path, "getscoreforGM")
                accuracy = fn(0, ipfs_hash, target_folder)
        else:
            accuracy = getscoreforGM(0, ipfs_hash, base_path=Path(os.getcwd()) / "tasks" / effective_network.lower() / task_coordinator_address)

    
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator_address)
    
    setGenesisModelIpfsHash_tx = deployed_DINTaskCoordinatorContract.functions.setGenesisModelIpfsHash(ipfs_hash).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 200_000,
        "gasPrice": w3.to_wei("5", "gwei"),
        "chainId": w3.eth.chain_id,
    })

    signed = account.sign_transaction(setGenesisModelIpfsHash_tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    console.print(f"[dim]Submitting genesis model tx:[/dim] {tx_hash.hex()}")
    w3.eth.wait_for_transaction_receipt(tx_hash)
    console.print("[green]✓ Genesis model submitted![/green]")
    
    
    set_key(".env", effective_network.upper() + "_" + task_coordinator_address + "_IS_GenesisModelCreated", "True")

         
    console.print("Genesis model accuracy:", accuracy)
    nonce = w3.eth.get_transaction_count(account.address)
        
    tx = deployed_DINTaskCoordinatorContract.functions.setTier2Score(0, int(accuracy)).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 3000000,
        "gasPrice": w3.to_wei("5", "gwei"),
        "chainId": w3.eth.chain_id,
    })
        
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    console.print(f"[dim]Submitting genesis model tier 2 score tx:[/dim] {tx_hash.hex()}")
    w3.eth.wait_for_transaction_receipt(tx_hash)
    console.print("[green]✓ Genesis model tier 2 score set![/green]")

@gi_app.command(help="Start a global iteration")
def start(
    gi: Optional[int] = typer.Option(None, "--gi", help="Global iteration (optional)"),
    network: str = typer.Option(None, "--network", help="Network to use"),
    model_id: int = typer.Option(..., "--model-id", help="Model ID"),
    threshold: Optional[int] = typer.Option(None, "--threshold", help="Threshold (optional)"),

):

    effective_network = resolve_network(network)
    w3 = get_w3(effective_network)
    account = load_account()

    task_coordinator_address = get_manifest_key(effective_network, "DINTaskCoordinator_Contract", model_id)
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"

    # if artifact_path does not exist, raise error
    if not artifact_path.exists():
        console.print("[red]Error:[/red] ABI file not found")
        raise typer.Exit(1)
    
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator_address)
    
    curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()
    
    if gi:
        if gi!=curr_GI+1:
            console.print("[red]Error:[/red] Invalid global iteration")
            raise typer.Exit(1)

    console.print(f"[bold green]Starting global iteration {curr_GI+1}! on TaskCoordinator {task_coordinator_address}[/bold green]")
    console.print(f"[cyan]Network:[/cyan] {effective_network}")
    console.print(f"[cyan]From account:[/cyan] {account.address}")


    if curr_GI == 0:
        gmcid = deployed_DINTaskCoordinatorContract.functions.genesisModelIpfsHash().call()
    else:
        batch_id, _, _, gmcid = deployed_DINTaskCoordinatorContract.functions.getTier2Batch(curr_GI,0).call()
    

    if get_manifest_key(effective_network, "getscoreforGM", model_id)["type"] == "custom":
        model_base_path = Path(CACHE_DIR) / effective_network /  f"model_{model_id}" 
        service_path_str = get_manifest_key(effective_network, "getscoreforGM", model_id)["path"]

        model_service_path_str = get_manifest_key(effective_network, "ModelArchitecture", model_id)["path"]

        custom_modelowner_service_path = model_base_path / Path(service_path_str)
        
        custom_model_service_path = model_base_path / Path(model_service_path_str)

        if not custom_modelowner_service_path.exists():
            retrieve_from_ipfs(get_manifest_key(effective_network,"getscoreforGM", model_id)["ipfs"], custom_modelowner_service_path)

        if not custom_model_service_path.exists():
            retrieve_from_ipfs(get_manifest_key(effective_network,"ModelArchitecture", model_id)["ipfs"], custom_model_service_path)

        fn = load_custom_fn(
            custom_modelowner_service_path,
            "getscoreforGM")

        if not (Path(model_base_path)/"models"/"genesis_model.pth").exists():
            retrieve_from_ipfs(get_manifest_key(effective_network,"Genesis_Model_CID", model_id), str(Path(model_base_path)/"models"/"genesis_model.pth"))

        if not (Path(model_base_path)/"dataset"/"test"/"test_dataset.pt").exists():
            console.print("[red]Error:[/red] Test dataset not found at ", str(Path(model_base_path)/"dataset"/"test"/"test_dataset.pt"))
            console.print("[yellow]Warning:[/yellow] please ensure the test dataset is present at ", str(Path(model_base_path)/"dataset"/"test"/"test_dataset.pt"))
            raise typer.Exit(1) 


        
        accuracy = fn(curr_GI, gmcid, model_base_path)
    else:
        accuracy = getscoreforGM(curr_GI, gmcid, base_path= Path(CACHE_DIR) / effective_network /  f"model_{model_id}")
    console.print("Current GI:", curr_GI, "\nGM Accuracy:", accuracy)

    if threshold:
        accuracy = int(accuracy - threshold)
        console.print("Threshold:", threshold)
    else:
        accuracy = int(accuracy - 5)
        console.print("Threshold not provided, using default value of 5")
    tx = deployed_DINTaskCoordinatorContract.functions.startGI(curr_GI+1, accuracy).build_transaction({
        "from": account.address,
        "gas": 3000000,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gasPrice": w3.to_wei("5", "gwei"),
    })

    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    unset_key(".env", effective_network.lower()+ "_"+str(model_id)+"_ClientModelsCreatedF")
    
    console.print(f"[dim]Global iteration started tx:[/dim] {tx_hash.hex()}")
    console.print("passScore for GI ", curr_GI+1, " is ", int(accuracy))
    console.print("[green]✓ Global iteration started![/green]")
    
    
@reg_app.command()  
def aggregators_open(
    network: str = typer.Option(None, "--network", help="Target network (local|sepolia|mainnet)"),
    model_id: int = typer.Option(..., "--model-id", help="Model ID"),
    gi: int = typer.Option(None, "--gi", help="Global iteration number"),
):
    effective_network = resolve_network(network)
    w3 = get_w3(effective_network)
    account = load_account()
    
    task_coordinator_address = get_manifest_key(effective_network, "DINTaskCoordinator_Contract", model_id)
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
    
    # if artifact_path does not exist, raise error
    if not artifact_path.exists():
        console.print("[red]Error:[/red] ABI file not found")
        raise typer.Exit(1)
    
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator_address)

    curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()
    if gi:
        if gi!=curr_GI:
            console.print("[red]Error:[/red] Invalid global iteration")
            raise typer.Exit(1)
    
    console.print(f"[bold green]Opening aggregators registration for global iteration {curr_GI} on TaskCoordinator {task_coordinator_address}![/bold green]")
    console.print(f"[cyan]Network:[/cyan] {effective_network}")
    console.print(f"[cyan]From account:[/cyan] {account.address}")
    
    tx = deployed_DINTaskCoordinatorContract.functions.startDINaggregatorsRegistration(curr_GI).build_transaction({
        "from": account.address,
        "gas": 3000000,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gasPrice": w3.to_wei("5", "gwei"),
        "chainId": w3.eth.chain_id,
    })
    
    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt.status == 0:
        console.print("[red]Error:[/red] Aggregators registration opening failed")
        raise typer.Exit(1)
    console.print(f"[dim]Aggregators opened registration tx:[/dim] {tx_hash.hex()}")
    console.print("[green]✓ Aggregators registration opened![/green]")        

reg_app.command()
def aggregators_close(
    network: str = typer.Option(None, "--network", help="Target network (local|sepolia|mainnet)"),
    task_coordinator: str = typer.Option(None, "--taskCoordinator", help="DINTaskCoordinator contract address"),
    gi: int = typer.Option(None, "--gi", help="Global iteration number"),
):
    effective_network = resolve_network(network)
    w3 = get_w3(effective_network)
    account = load_account()

    if not task_coordinator:
        task_coordinator = get_key(".env", "DINTaskCoordinator_Contract_Address")
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
    
    # if artifact_path does not exist, raise error
    if not artifact_path.exists():
        console.print("[red]Error:[/red] ABI file not found")
        raise typer.Exit(1)
    
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator)
    
    curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()
    if gi:
        if gi!=curr_GI:
            console.print("[red]Error:[/red] Invalid global iteration")
            raise typer.Exit(1)
    
    console.print(f"[bold green]Closing aggregators registration for global iteration {curr_GI} on TaskCoordinator {task_coordinator}![/bold green]")
    console.print(f"[cyan]Network:[/cyan] {effective_network}")
    console.print(f"[cyan]From account:[/cyan] {account.address}")
    
    tx = deployed_DINTaskCoordinatorContract.functions.closeDINvalidatorRegistration(curr_GI).build_transaction({
        "from": account.address,
        "gas": 3000000,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gasPrice": w3.to_wei("5", "gwei"),
        "chainId": w3.eth.chain_id,
    })
    
    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt.status == 0:
        console.print("[red]Error:[/red] Aggregators registration closing failed")
        raise typer.Exit(1)
    console.print(f"[dim]Aggregators closed registration tx:[/dim] {tx_hash.hex()}")
    console.print("[green]✓ Aggregators registration closed![/green]")
    
@reg_app.command()
def aggregators_close(
    network: str = typer.Option(None, "--network", help="Target network (local|sepolia|mainnet)"),
    model_id: int = typer.Option(..., "--model-id", help="Model ID"),
    gi: int = typer.Option(None, "--gi", help="Global iteration number"),
):      
    effective_network = resolve_network(network)
    w3 = get_w3(effective_network)
    account = load_account()
    
    task_coordinator_address = get_manifest_key(effective_network, "DINTaskCoordinator_Contract", model_id)
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
    
    # if artifact_path does not exist, raise error
    if not artifact_path.exists():
        console.print("[red]Error:[/red] ABI file not found")
        raise typer.Exit(1)
    
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator_address)
    
    curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()
    if gi:
        if gi!=curr_GI:
            console.print("[red]Error:[/red] Invalid global iteration")
            raise typer.Exit(1)
    
    console.print(f"[bold green]Closing aggregators registration for global iteration {curr_GI} on TaskCoordinator {task_coordinator_address}![/bold green]")
    console.print(f"[cyan]Network:[/cyan] {effective_network}")
    console.print(f"[cyan]From account:[/cyan] {account.address}")
    
    tx = deployed_DINTaskCoordinatorContract.functions.closeDINaggregatorsRegistration(curr_GI).build_transaction({
        "from": account.address,
        "gas": 3000000,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gasPrice": w3.to_wei("5", "gwei"),
        "chainId": w3.eth.chain_id,
    })
    
    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt.status == 0:
        console.print("[red]Error:[/red] Aggregators registration closing failed")
        raise typer.Exit(1)
    console.print(f"[dim]Aggregators registration closed tx:[/dim] {tx_hash.hex()}")
    console.print("[green]✓ Aggregators registration closed![/green]")
    
@reg_app.command()
def auditors_open(
    network: str = typer.Option(None, "--network", help="Target network (local|sepolia|mainnet)"),
    model_id: int = typer.Option(..., "--model-id", help="Model ID"),
    gi: int = typer.Option(None, "--gi", help="Global iteration number"),
):      
    effective_network = resolve_network(network)
    w3 = get_w3(effective_network)
    account = load_account()
    
    task_coordinator_address = get_manifest_key(effective_network, "DINTaskCoordinator_Contract", model_id)
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
    
    # if artifact_path does not exist, raise error
    if not artifact_path.exists():
        console.print("[red]Error:[/red] ABI file not found")
        raise typer.Exit(1)
    
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator_address)
    
    curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()
    if gi:
        if gi!=curr_GI:
            console.print("[red]Error:[/red] Invalid global iteration")
            raise typer.Exit(1)
    
    console.print(f"[bold green]Opening auditors registration for global iteration {curr_GI} on TaskCoordinator {task_coordinator_address}![/bold green]")
    console.print(f"[cyan]Network:[/cyan] {effective_network}")
    console.print(f"[cyan]From account:[/cyan] {account.address}")
    
    tx = deployed_DINTaskCoordinatorContract.functions.startDINauditorsRegistration(curr_GI).build_transaction({
        "from": account.address,
        "gas": 3000000,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gasPrice": w3.to_wei("5", "gwei"),
        "chainId": w3.eth.chain_id,
    })
    
    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt.status == 0:
        console.print("[red]Error:[/red] Auditors registration opening failed")
        raise typer.Exit(1)
    console.print(f"[dim]Auditors opened registration tx:[/dim] {tx_hash.hex()}")
    console.print("[green]✓ Auditors registration opened![/green]")

@gi_app.command("show-registered-auditors", help="Show registered auditors")
def show_registered_auditors(
    network: str = typer.Option(None, "--network", help="Target network (local|sepolia|mainnet)"),
    model_id: int = typer.Option(..., "--model-id", help="Model ID"),
    gi: int = typer.Option(None, "--gi", help="Global iteration number"),
):    
    effective_network = resolve_network(network)
    w3 = get_w3(effective_network)
    account = load_account()
    
    task_coordinator_address = get_manifest_key(effective_network, "DINTaskCoordinator_Contract", model_id)
    task_auditor_address = get_manifest_key(effective_network, "DINTaskAuditor_Contract", model_id)
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskAuditor.json"
    
    # if artifact_path does not exist, raise error
    if not artifact_path.exists():
        console.print("[red]Error:[/red] ABI file not found")
        raise typer.Exit(1)
    
    deployed_DINTaskAuditorContract = get_contract_instance(str(artifact_path), effective_network, task_auditor_address)

    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
    
    # if artifact_path does not exist, raise error
    if not artifact_path.exists():
        console.print("[red]Error:[/red] ABI file not found")
        raise typer.Exit(1)
    
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator_address)
    
    curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()
    curr_GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()
    if gi:
        if gi!=curr_GI:
            console.print("[red]Error:[/red] Invalid global iteration")
            raise typer.Exit(1)

    if curr_GIstate < GIstatestrToIndex("DINauditorsRegistrationStarted"):
        console.print("[red]Error:[/red] No auditors registered yet as DINauditorsRegistrationStarted has not been reached")
        raise typer.Exit(1)

    
    console.print(f"[bold green]Showing registered auditors for global iteration {curr_GI} on TaskCoordinator {task_coordinator_address} and TaskAuditor {task_auditor_address}![/bold green]")
    console.print(f"[cyan]Network:[/cyan] {effective_network}")
    console.print(f"[cyan]From account:[/cyan] {account.address}")


    
    registered_auditors = deployed_DINTaskAuditorContract.functions.getDINtaskAuditors(curr_GI).call()
    console.print(str(len(registered_auditors)) + " Registered Auditors:", registered_auditors)    
    console.print("[green]✓ Registered auditors shown![/green]")


@gi_app.command("show-registered-aggregators", help="Show registered aggregators")
def show_registered_aggregators(
    network: str = typer.Option(None, "--network", help="Target network (local|sepolia|mainnet)"),
    model_id: int = typer.Option(..., "--model-id", help="Model ID"),
    gi: int = typer.Option(None, "--gi", help="Global iteration number"),
):
    effective_network = resolve_network(network)
    w3 = get_w3(effective_network)
    account = load_account()
    
    task_coordinator_address = get_manifest_key(effective_network, "DINTaskCoordinator_Contract", model_id)
   
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
    
    # if artifact_path does not exist, raise error
    if not artifact_path.exists():
        console.print("[red]Error:[/red] ABI file not found")
        raise typer.Exit(1)
    
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator_address)
    
    curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()
    if gi:
        if gi!=curr_GI:
            console.print("[red]Error:[/red] Invalid global iteration")
            raise typer.Exit(1)

    curr_GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()

    if curr_GIstate < GIstatestrToIndex("DINaggregatorsRegistrationStarted"):
        console.print("[red]Error:[/red] No aggregators registered yet as DINaggregatorsRegistrationStarted has not been reached")
        raise typer.Exit(1)

    console.print(f"[bold green]Showing registered aggregators for global iteration {curr_GI} on TaskCoordinator {task_coordinator_address}![/bold green]")
    console.print(f"[cyan]Network:[/cyan] {effective_network}")
    console.print(f"[cyan]From account:[/cyan] {account.address}")
    
    registered_aggregators = deployed_DINTaskCoordinatorContract.functions.getDINtaskAggregators(curr_GI).call()
    console.print(str(len(registered_aggregators)) + " Registered Aggregators:", registered_aggregators)    
    console.print("[green]✓ Registered aggregators shown![/green]")


@gi_app.command()
def show_state(
    network: str = typer.Option(None, "--network", help="Target network (local|sepolia|mainnet)"),
    model_id: str = typer.Option(None, "--model-id", help="Model ID"),
    gi: int = typer.Option(None, "--gi", help="Global iteration number"),
):
    effective_network = resolve_network(network)
    w3 = get_w3(effective_network)
    account = load_account()
    
    task_coordinator_address = get_manifest_key(effective_network, "DINTaskCoordinator_Contract", model_id)
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
    
    # if artifact_path does not exist, raise error
    if not artifact_path.exists():
        console.print("[red]Error:[/red] ABI file not found")
        raise typer.Exit(1)
    
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator_address)
    
    curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()
    if gi:
        if gi!=curr_GI:
            console.print("[red]Error:[/red] Invalid global iteration")
            raise typer.Exit(1)

    curr_GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()

    console.print(f"[bold green]Showing global iteration state for global iteration {curr_GI} on TaskCoordinator {task_coordinator_address}![/bold green]")
    console.print(f"[cyan]Network:[/cyan] {effective_network}")
    console.print(f"[cyan]From account:[/cyan] {account.address}")
    console.print(f"[cyan]Global iteration numerical state:[/cyan] {curr_GIstate}")
    console.print(f"[cyan]Global iteration state:[/cyan] {GIstateToStr(curr_GIstate)}")
    console.print("[green]✓ Global iteration state shown![/green]")

@reg_app.command("auditors-close", help="Close auditors registration")
def auditors_close(
    network: str = typer.Option(None, "--network", help="Target network (local|sepolia|mainnet)"),
    model_id: int = typer.Option(..., "--model-id", help="Model ID"),
    gi: int = typer.Option(None, "--gi", help="Global iteration number"),
):
    effective_network = resolve_network(network)
    w3 = get_w3(effective_network)
    account = load_account()
    
    task_coordinator_address = get_manifest_key(effective_network, "DINTaskCoordinator_Contract", model_id)
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
    
    # if artifact_path does not exist, raise error
    if not artifact_path.exists():
        console.print("[red]Error:[/red] ABI file not found")
        raise typer.Exit(1)
    
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator_address)
    
    curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()
    if gi:
        if gi!=curr_GI:
            console.print("[red]Error:[/red] Invalid global iteration")
            raise typer.Exit(1)
    
    console.print(f"[bold green]Closing auditors registration for global iteration {curr_GI} on TaskCoordinator {task_coordinator_address}![/bold green]")
    console.print(f"[cyan]Network:[/cyan] {effective_network}")
    console.print(f"[cyan]From account:[/cyan] {account.address}")
    
    tx = deployed_DINTaskCoordinatorContract.functions.closeDINauditorsRegistration(curr_GI).build_transaction({
        "from": account.address,
        "gas": 3000000,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gasPrice": w3.to_wei("5", "gwei"),
        "chainId": w3.eth.chain_id,
    })
    
    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt.status == 0:
        console.print("[red]Error:[/red] Auditors registration closing failed")
        raise typer.Exit(1)
    console.print(f"[dim]Auditors closed registration tx:[/dim] {tx_hash.hex()}")
    console.print("[green]✓ Auditors registration closed![/green]")

@lms_app.command()    
def open(
    network: str = typer.Option(None, "--network", help="Target network (local|sepolia|mainnet)"),
    model_id: int = typer.Option(..., "--model-id", help="Model ID"),
    gi: int = typer.Option(None, "--gi", help="Global iteration number"),
):

    effective_network = resolve_network(network)
    w3 = get_w3(effective_network)
    account = load_account()
    
    task_coordinator_address = get_manifest_key(effective_network, "DINTaskCoordinator_Contract", model_id)
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
    
    # if artifact_path does not exist, raise error
    if not artifact_path.exists():
        console.print("[red]Error:[/red] ABI file not found")
        raise typer.Exit(1)
    
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator_address)
    
    curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()
    if gi:
        if gi!=curr_GI:
            console.print("[red]Error:[/red] Invalid global iteration")
            raise typer.Exit(1)
    
    console.print(f"[bold green]Opening local model submissions for global iteration {curr_GI} on TaskCoordinator {task_coordinator_address}![/bold green]")
    console.print(f"[cyan]Network:[/cyan] {effective_network}")
    console.print(f"[cyan]From account:[/cyan] {account.address}")
    
    tx = deployed_DINTaskCoordinatorContract.functions.startLMsubmissions(curr_GI).build_transaction({
        "from": account.address,
        "gas": 3000000,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gasPrice": w3.to_wei("5", "gwei"),
        "chainId": w3.eth.chain_id,
    })
    
    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt.status == 0:
        console.print("[red]Error:[/red] Local model submissions opening failed")
        raise typer.Exit(1)
    console.print(f"[dim]Local model submissions opened tx:[/dim] {tx_hash.hex()}")
    console.print("[green]✓ Local model submissions opened![/green]")

@lms_app.command()
def show_models(
    network: str = typer.Option(None, "--network", help="Target network (local|sepolia|mainnet)"),
    model_id: int = typer.Option(..., "--model-id", help="Model ID"),
    gi: int = typer.Option(None, "--gi", help="Global iteration to use"),
):
    effective_network = resolve_network(network)
    w3 = get_w3(effective_network)
    account = load_account()
    
    task_coordinator_address = get_manifest_key(effective_network, "DINTaskCoordinator_Contract", model_id)
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
    
    # if artifact_path does not exist, raise error
    if not artifact_path.exists():
        console.print("[red]Error:[/red] ABI file not found")
        raise typer.Exit(1)
    
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator_address)
    
    curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()
    if not gi:
        ref_gi = curr_GI
    else:
        if gi > curr_GI:
            console.print(f"[red]Error:[/red] Invalid global iteration {gi} given in command: gi > curr_GI ({curr_GI})")
            raise typer.Exit(1)
        ref_gi = gi

    task_auditor_address = get_manifest_key(effective_network, "DINTaskAuditor_Contract", model_id)
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskAuditor.json"
    
    # if artifact_path does not exist, raise error
    if not artifact_path.exists():
        console.print("[red]Error:[/red] ABI file not found")
        raise typer.Exit(1)
    
    deployed_DINTaskAuditorContract = get_contract_instance(str(artifact_path), effective_network, task_auditor_address)
    
    console.print(f"[bold green]Showing local model submissions for global iteration {ref_gi} on TaskCoordinator {task_coordinator_address} and TaskAuditor {task_auditor_address}![/bold green]")
    console.print(f"[cyan]Network:[/cyan] {effective_network}")
    console.print(f"[cyan]From account:[/cyan] {account.address}")

    client_model_ipfs_hashes = []
    ClientAddresses = []

    GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()

    if (ref_gi == curr_GI and GIstate >= GIstatestrToIndex("LMSstarted")) or (ref_gi < curr_GI):
        lm_submissions = deployed_DINTaskAuditorContract.functions.getClientModels(ref_gi).call()
        if len(lm_submissions) == 0:
            console.print("[red]Error:[/red] No local model submissions found")
            raise typer.Exit(1)
        else:
            console.print(f"[green]✓ {len(lm_submissions)} Local model submissions found![/green]")
        for i in range(len(lm_submissions)):

            client_model_ipfs_hash = lm_submissions[i][1]
            ClientAddresses.append(lm_submissions[i][0])
            client_model_ipfs_hashes.append(client_model_ipfs_hash)
            console.print(f"[green]✓ Client {ClientAddresses[i]} submitted model {client_model_ipfs_hash}![/green]")

        console.print(f"[bold green]✓ Local model submissions shown![/bold green]")
    else:
        console.print(f"[red]Error:[/red] Invalid global iteration {ref_gi} given in command: gi > curr_GI ({curr_GI})")
        raise typer.Exit(1)
        

@lms_app.command()    
def close(
    network: str = typer.Option(None, "--network", help="Target network (local|sepolia|mainnet)"),
    model_id: int = typer.Option(..., "--model-id", help="Model ID"),
    gi: int = typer.Option(None, "--gi", help="Global iteration number"),
):

    effective_network = resolve_network(network)
    w3 = get_w3(effective_network)
    account = load_account()

    task_coordinator_address = get_manifest_key(effective_network, "DINTaskCoordinator_Contract", model_id)
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
    
    # if artifact_path does not exist, raise error
    if not artifact_path.exists():
        console.print("[red]Error:[/red] ABI file not found")
        raise typer.Exit(1)
    
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator_address)
    
    curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()

    GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()

    if gi:
        if gi!=curr_GI:
            console.print("[red]Error:[/red] Invalid global iteration")
            raise typer.Exit(1)

    console.print(f"[bold green]Closing local model submissions for global iteration {curr_GI} on TaskCoordinator {task_coordinator_address}![/bold green]")

    if curr_GI < 1 or GIstate != GIstatestrToIndex("LMSstarted"):
        console.print(f"[red]Error:[/red] Can not close LM submissions at this time. GIstate is {GIstateToStr(GIstate)} and curr_GI is {curr_GI}")
        raise typer.Exit(1)

    
   
    console.print(f"[cyan]Network:[/cyan] {effective_network}")
    console.print(f"[cyan]From account:[/cyan] {account.address}")
    
    tx = deployed_DINTaskCoordinatorContract.functions.closeLMsubmissions(curr_GI).build_transaction({
        "from": account.address,
        "gas": 3000000,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gasPrice": w3.to_wei("5", "gwei"),
        "chainId": w3.eth.chain_id,
    })
    
    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt.status == 0:
        console.print("[red]Error:[/red] Local model submissions closing failed")
        raise typer.Exit(1)
    console.print(f"[dim]Local model submissions closed tx:[/dim] {tx_hash.hex()}")
    console.print("[green]✓ Local model submissions closed![/green]")
      
@auditor_batches_app.command()
def create(
    network: str = typer.Option(None, "--network", help="Target network (local|sepolia|mainnet)"),
    model_id: int = typer.Option(..., "--model-id", help="Model ID"),
    gi: int = typer.Option(None, "--gi", help="Global iteration number"),
):
    effective_network = resolve_network(network)
    w3 = get_w3(effective_network)
    account = load_account()
    
    task_coordinator_address = get_manifest_key(effective_network, "DINTaskCoordinator_Contract", model_id)
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
    
    # if artifact_path does not exist, raise error
    if not artifact_path.exists():
        console.print("[red]Error:[/red] ABI file not found")
        raise typer.Exit(1)
    
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator_address)
    
    curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()

    GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()

    if gi:
        if gi!=curr_GI:
            console.print("[red]Error:[/red] Invalid global iteration")
            raise typer.Exit(1)

    if curr_GI < 1 or GIstate != GIstatestrToIndex("LMSclosed"):
        console.print("[red]Error:[/red] Can not create auditor batches at this time")
        raise typer.Exit(1)
    
    console.print(f"[bold green]Creating auditor batches for global iteration {curr_GI} on TaskCoordinator {task_coordinator_address}![/bold green]")
    console.print(f"[cyan]Network:[/cyan] {effective_network}")
    console.print(f"[cyan]From account:[/cyan] {account.address}")
    
    tx = deployed_DINTaskCoordinatorContract.functions.createAuditorsBatches(curr_GI).build_transaction({
        "from": account.address,
        "gas": 3000000,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gasPrice": w3.to_wei("5", "gwei"),
        "chainId": w3.eth.chain_id,
    })
    
    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt.status == 0:
        console.print("[red]Error:[/red] Auditor batches creation failed")
        raise typer.Exit(1)
    console.print(f"[dim]Auditor batches created tx:[/dim] {tx_hash.hex()}")
    console.print("[green]✓ Auditor batches created![/green]")

@auditor_batches_app.command()
def show(
    network: str = typer.Option(None, "--network", help="Target network (local|sepolia|mainnet)"),
    model_id: int = typer.Option(..., "--model-id", help="Model ID"),
    gi: int = typer.Option(None, "--gi", help="Global iteration number"),
):
    

    effective_network = resolve_network(network)
    w3 = get_w3(effective_network)
    account = load_account()
    
    task_coordinator_address = get_manifest_key(effective_network, "DINTaskCoordinator_Contract", model_id)
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
    
    # if artifact_path does not exist, raise error
    if not artifact_path.exists():
        console.print("[red]Error:[/red] ABI file not found")
        raise typer.Exit(1)
    
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator_address)

    task_auditor_address = get_manifest_key(effective_network, "DINTaskAuditor_Contract", model_id)
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskAuditor.json"
    
    # if artifact_path does not exist, raise error
    if not artifact_path.exists():
        console.print("[red]Error:[/red] ABI file not found")
        raise typer.Exit(1)
    
    deployed_DINTaskAuditorContract = get_contract_instance(str(artifact_path), effective_network, task_auditor_address)
    
    curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()

    GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()

    if not gi:
        ref_gi = curr_GI
    else:
        if gi > curr_GI:
            console.print(f"[red]Error:[/red] Invalid global iteration {gi} given in command: gi > curr_GI ({curr_GI})")
            raise typer.Exit(1)
        ref_gi = gi


    if (ref_gi == curr_GI and GIstate >= GIstatestrToIndex("AuditorsBatchesCreated")) or (ref_gi < curr_GI):

        console.print(f"[bold green]Showing auditor batches for global iteration {ref_gi} on TaskCoordinator {task_coordinator_address}![/bold green]")
        console.print(f"[cyan]Network:[/cyan] {effective_network}")
        console.print(f"[cyan]From account:[/cyan] {account.address}")

        audtor_batch_count = deployed_DINTaskAuditorContract.functions.AuditorsBatchCount(ref_gi).call()

        console.print(f"[bold green]Auditor batches count:[/bold green] {audtor_batch_count}")

        raw_audit_batches = []
        processed_audit_batches = []
    
        for i in range(audtor_batch_count):
            raw_audit_batches.append(deployed_DINTaskAuditorContract.functions.getAuditorsBatch(ref_gi, i).call())

        for batch in raw_audit_batches:
            batch_id, auditors, model_indexes, test_cid = batch
            processed_audit_batches.append({"batch_id": batch_id, "auditors": auditors, "model_indexes": model_indexes, "test_cid": test_cid or "None"})

    

        # After building `processed_audit_batches`:
        if not processed_audit_batches:
            console.print("[yellow]No auditor batches found.[/yellow]")
        else:
            table = Table(title=f"Auditor Batches for GI {curr_GI}", show_header=True, header_style="bold magenta")
            table.add_column("Batch ID", style="dim")
            table.add_column("Auditors", overflow="fold")
            table.add_column("Model Indexes", overflow="fold")
            table.add_column("Test CID")

            for batch in processed_audit_batches:
                table.add_row(
                    str(batch["batch_id"]),
                    ", ".join(batch["auditors"]) if batch["auditors"] else "—",
                    ", ".join(map(str, batch["model_indexes"])) if batch["model_indexes"] else "—",
                    batch["test_cid"] if batch["test_cid"] != "None" else "—"
                )
    
            console.print(table)

            console.print("[green]✓ Auditor batches shown![/green]")

    else:
        console.print("[red]Error:[/red] Can not show auditor batches at this time as GIstate is ",GIstateToStr(GIstate))
        raise typer.Exit(1)

@auditor_batches_app.command("create-testdataset")
def create_testdataset(
    network: str = typer.Option(None, "--network", help="Target network (local|sepolia|mainnet)"),
    model_id: int = typer.Option(..., "--model-id", help="Model ID"),
    gi: int = typer.Option(None, "--gi", help="Global iteration number"),
    submit: bool = typer.Option(False, "--submit", help="Submit test dataset to TaskCoordinator"),
    test_data_path: str = typer.Option(None, "--test-data-path", help="Path to test dataset"),
):
    effective_network = resolve_network(network)
    w3 = get_w3(effective_network)
    account = load_account()
    
    task_coordinator_address = get_manifest_key(effective_network, "DINTaskCoordinator_Contract", model_id)
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
    
    # if artifact_path does not exist, raise error
    if not artifact_path.exists():
        console.print("[red]Error:[/red] ABI file not found")
        raise typer.Exit(1)
    
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator_address)

    task_auditor_address = get_manifest_key(effective_network, "DINTaskAuditor_Contract", model_id)
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskAuditor.json"
    
    # if artifact_path does not exist, raise error
    if not artifact_path.exists():
        console.print("[red]Error:[/red] ABI file not found")
        raise typer.Exit(1)
    
    deployed_DINTaskAuditorContract = get_contract_instance(str(artifact_path), effective_network, task_auditor_address)
    
    curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()

    GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()

    if gi:
        if gi!=curr_GI:
            console.print(f"[red]Error:[/red] Invalid global iteration given in command: gi ({gi}) != curr_GI ({curr_GI})")
            raise typer.Exit(1)

    if curr_GI < 1 or GIstate != GIstatestrToIndex("AuditorsBatchesCreated"):
        console.print("[red]Error:[/red] Can not create test dataset at this time as GIstate is ",GIstateToStr(GIstate))
        raise typer.Exit(1)

    console.print(f"[bold green]Creating test dataset for global iteration {curr_GI} on TaskCoordinator {task_coordinator_address}![/bold green]")

    audtor_batch_count = deployed_DINTaskAuditorContract.functions.AuditorsBatchCount(curr_GI).call()

    model_base_path = Path(CACHE_DIR) / effective_network /  f"model_{model_id}"


    if get_manifest_key(effective_network, "create_audit_testDataCIDs", model_id)["type"] == "custom":
        service_path_str = get_manifest_key(effective_network, "create_audit_testDataCIDs", model_id)["path"]
        custom_modelowner_service_path = model_base_path / Path(service_path_str)
        if not custom_modelowner_service_path.exists():
            retrieve_from_ipfs(get_manifest_key(effective_network,"create_audit_testDataCIDs", model_id)["ipfs"], custom_modelowner_service_path)

        fn = load_custom_fn(custom_modelowner_service_path, "create_audit_testDataCIDs")
        audit_testDataCIDs = fn(audtor_batch_count, curr_GI, str(model_base_path), test_data_path)
    else:
        audit_testDataCIDs = create_audit_testDataCIDs(audtor_batch_count, curr_GI)
    
    #audit_testDataCIDs = ['QmYHc4Y6pmMKFohYDJXkFCCrLAQBUhwGuD6ebGZUxi34ea', 'QmSvTuP4XmcNnaYAqYkv6ewUKU7v2PCAnnLB9DqE7MTrAg', 'QmSdiTciKYBTxHKntjY3Pko8szD5D1nXVLU2mVWrsZhWdE', 'QmcLCGEz9FDHti6c2PPUqAh8rzGpQSwFAZi4QifcYkQB49', 'QmRZydYdpcHTpSSNy7MsX2K29KuUwEsoRxDkT9NEHqu6CQ', 'QmfBeoeqxb3SecGj4qUWcYYZ5AtCsUPyBn8deUj4RQofxw']

    console.print("audit_testDataCIDs", audit_testDataCIDs)
    
    console.print(f"[bold green] ✓ Created test subdatasets for global iteration {curr_GI}![/bold green]")

    if submit:

        console.print(f"[bold green]Assigning test dataset for global iteration {curr_GI} on TaskAuditor {task_auditor_address}![/bold green]")

        for batch_id in range(audtor_batch_count):
            tx = deployed_DINTaskAuditorContract.functions.assignAuditTestDataset(curr_GI, batch_id, audit_testDataCIDs[batch_id]).build_transaction({
                "from": account.address,
                "nonce": w3.eth.get_transaction_count(account.address),
                "gas": 3000000,
                "gasPrice": w3.to_wei("5", "gwei"),
                "chainId": w3.eth.chain_id
            })

            signed_tx = account.sign_transaction(tx)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt.status == 0:
                console.print("[red]Error:[/red] Failed to assign test dataset for auditor batch :", batch_id)
            else:
                console.print("[green]✓ Test dataset assigned for auditor batch :", batch_id)

        tx = deployed_DINTaskCoordinatorContract.functions.setTestDataAssignedFlag(curr_GI, True).build_transaction({
                "from": account.address,
                "nonce": w3.eth.get_transaction_count(account.address),
                "gas": 3000000,
                "gasPrice": w3.to_wei("5", "gwei"),
                "chainId": w3.eth.chain_id
            })
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt.status == 0:
            console.print("[red]Error:[/red] Failed to set test dataset assigned flag for global iteration", curr_GI)
            raise typer.Exit(1)
            
        console.print(f"[green]✓ Test dataset assigned for auditor batches for global iteration {curr_GI}![/green]")


@lms_evaluation_app.command()
def start(
    network: str = typer.Option(None, "--network", help="Target network (local|sepolia|mainnet)"),
    model_id: str = typer.Option(None, "--model-id", help="Model ID"),
    gi: int = typer.Option(None, "--gi", help="Global iteration number"),
):

    effective_network = resolve_network(network)
    w3 = get_w3(effective_network)
    account = load_account()
    
    task_coordinator_address = get_manifest_key(effective_network, "DINTaskCoordinator_Contract", model_id)
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
    
    # if artifact_path does not exist, raise error
    if not artifact_path.exists():
        console.print("[red]Error:[/red] ABI file not found")
        raise typer.Exit(1)
    
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator_address)

    curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()
    
    GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()
    
    if gi:
        if gi!=curr_GI:
            console.print("[red]Error:[/red] Invalid global iteration")
            raise typer.Exit(1)

    if curr_GI < 1 or GIstate != GIstatestrToIndex("AuditorsBatchesCreated"):
        console.print("[red]Error:[/red] Can not start LMS evaluation at this time as GIstate is ",GIstateToStr(GIstate))
        raise typer.Exit(1)
    
    console.print(f"[bold green]Starting LMS evaluation for global iteration {curr_GI} on TaskCoordinator {task_coordinator_address}![/bold green]")

    tx = deployed_DINTaskCoordinatorContract.functions.startLMsubmissionsEvaluation(curr_GI).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 3000000,
        "gasPrice": w3.to_wei("5", "gwei"),
        "chainId": w3.eth.chain_id
    })

    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status == 0:
        console.print("[red]Error:[/red] Failed to start LMS evaluation for global iteration", curr_GI)
        raise typer.Exit(1)
    console.print(f"[green]✓ LMS evaluation started for global iteration {curr_GI} on TaskCoordinator {task_coordinator_address}![/green]")
    

@lms_evaluation_app.command()
def close(
    network: str = typer.Option(None, "--network", help="Target network (local|sepolia|mainnet)"),
    model_id: str = typer.Option(..., "--model-id", help="Model ID"),
    gi: int = typer.Option(None, "--gi", help="Global iteration number"),
):
    effective_network = resolve_network(network)
    w3 = get_w3(effective_network)
    account = load_account()
    
    task_coordinator_address = get_manifest_key(effective_network, "DINTaskCoordinator_Contract", model_id)
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
    
    # if artifact_path does not exist, raise error
    if not artifact_path.exists():
        console.print("[red]Error:[/red] ABI file not found")
        raise typer.Exit(1)
    
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator_address)

    curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()

    GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()
    
    if gi:
        if gi!=curr_GI:
            console.print("[red]Error:[/red] Invalid global iteration ",gi," current is ",curr_GI)
            raise typer.Exit(1)
    
    console.print(f"[bold green]Closing LMS evaluation for global iteration {curr_GI} on TaskCoordinator {task_coordinator_address}![/bold green]")

    if GIstate != GIstatestrToIndex("LMSevaluationStarted"):
        console.print("[red]Error:[/red] Can not close LMS evaluation at this time as GIstate is ",GIstateToStr(GIstate))
        raise typer.Exit(1)

    tx = deployed_DINTaskCoordinatorContract.functions.closeLMsubmissionsEvaluation(curr_GI).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        "gas": 3000000,
        "gasPrice": w3.to_wei("5", "gwei"),
        "chainId": w3.eth.chain_id
    })

    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status == 0:
        console.print("[red]Error:[/red] Failed to close LMS evaluation for global iteration", curr_GI)
        raise typer.Exit(1)
    console.print(f"[green]✓ LMS evaluation closed for global iteration {curr_GI} on TaskCoordinator {task_coordinator_address}![/green]")

@aggregation_app.command("create-t1nt2-batches")
def create_tier1_tier2_batches(
    network: str = typer.Option(None, "--network", help="Network to use"),
    model_id: str = typer.Option(..., "--model-id", help="Model ID"),
    gi: int = typer.Option(None, "--gi", help="Global iteration number"),
):
    effective_network = resolve_network(network)
    w3 = get_w3(effective_network)
    account = load_account()

    task_coordinator_address = get_manifest_key(effective_network, "DINTaskCoordinator_Contract", model_id)
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
    if not artifact_path.exists():
        console.print("[red]Error:[/red] ABI file not found")
        raise typer.Exit(1)
        
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator_address)
    
    curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()
    GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()

    if gi:
        if curr_GI != gi:
            console.print(f"[red]Error:[/red] invalid global iteration {gi} does not match current GI {curr_GI}")
            raise typer.Exit(1)
    
    if GIstate != GIstatestrToIndex("LMSevaluationClosed"):
        console.print(f"[red]Error:[/red] GI state is {GIstateToStr(GIstate)} ({GIstate}), expected LMSevaluationClosed {GIstatestrToIndex("LMSevaluationClosed")}")
        raise typer.Exit(1)

    
    console.print(f"[bold green]Creating Tier 1 & Tier 2 batches for GI {curr_GI}...[/bold green]")
    
    tx = deployed_DINTaskCoordinatorContract.functions.autoCreateTier1AndTier2(curr_GI).build_transaction({
        "from": account.address,
        "gas": 3000000,
        "gasPrice": w3.to_wei("5", "gwei"),
        "nonce": w3.eth.get_transaction_count(account.address),
        "chainId": w3.eth.chain_id
    })
    
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    console.print(f"[dim]Tx hash: {tx_hash.hex()}[/dim]")
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status == 1:
        console.print("[green]✓ Tier 1 & Tier 2 batches created successfully[/green]")
    else:
        console.print("[red]Error: Transaction failed[/red]")
        raise typer.Exit(1)


@aggregation_app.command("show-t1-batches")
def show_t1_batches(
    network: str = typer.Option(None, "--network", help="Network to use"),
    model_id: str = typer.Option(..., "--model-id", help="Model ID"),
    gi: int = typer.Option(None, "--gi", help="Global iteration number"),
    detailed: bool = typer.Option(False, "--detailed", help="Show detailed information"),
):
    effective_network = resolve_network(network)
    w3 = get_w3(effective_network)
    account = load_account() 

    task_coordinator_address = get_manifest_key(effective_network, "DINTaskCoordinator_Contract", model_id)
        
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator_address)

    curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()
    
    # Check if batches can exist
    # GIstate must be >= T1nT2Bcreated (7)
    GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()


    if not gi:
        ref_gi = curr_GI
    else:
        if gi > curr_GI:
            console.print(f"[red]Error:[/red] Invalid global iteration {gi} given in command: gi > curr_GI ({curr_GI})")
            raise typer.Exit(1)
        ref_gi = gi

    if (ref_gi == curr_GI and GIstate >= GIstatestrToIndex("T1nT2Bcreated")) or (ref_gi < curr_GI):
        console.print(f"[green]✓ Showing Tier 1 batches for GI {ref_gi} (GIstate: {GIstateToStr(GIstate)}) on network {effective_network} for model {model_id} on TaskCoordinator {task_coordinator_address}[/green]")

    else:
        console.print(f"[red]Error:[/red] GI state is {GIstateToStr(GIstate)}. Batches do not exist yet.")
        raise typer.Exit(1)
   

    t1_count = deployed_DINTaskCoordinatorContract.functions.tier1BatchCount(curr_GI).call()
    if not detailed:
        table = Table(title=f"Tier 1 Batches (GI: {curr_GI})")
        table.add_column("Batch ID", justify="right", style="cyan")
        table.add_column("Aggregators", style="magenta")
        table.add_column("Model Indexes", style="green")
        table.add_column("Finalized", style="yellow")
        table.add_column("Final CID", style="white")

        for i in range(t1_count):
            bid, validators, model_idxs, finalized, cid = deployed_DINTaskCoordinatorContract.functions.getTier1Batch(curr_GI, i).call()
            
            val_display = "\n".join([f"{v[:6]}...{v[-4:]}" for v in validators])
            idxs_display = ", ".join(map(str, model_idxs))
            
            table.add_row(str(bid), val_display, idxs_display, str(finalized), cid or "")
            
        console.print(table)


    if detailed:

        detailed_table = Table(title=f"Detailed Tier 1 Batches (GI: {curr_GI})")
        detailed_table.add_column("Batch ID", justify="right", style="cyan")
        detailed_table.add_column("Aggregator Address", style="magenta")
        detailed_table.add_column("Submitted CID", style="green")
        detailed_table.add_column("Model Indexes", style="green")
        detailed_table.add_column("Finalized CID", style="white")
        for i in range(t1_count):
            bid, validators, model_idxs, finalized, final_cid = deployed_DINTaskCoordinatorContract.functions.getTier1Batch(curr_GI, i).call()
            
            for validator in validators:
                submitted_cid = deployed_DINTaskCoordinatorContract.functions.t1SubmissionCID(curr_GI, bid, validator).call()
                idxs_display = ", ".join(map(str, model_idxs))
                detailed_table.add_row(str(bid), validator, submitted_cid or "None", idxs_display, final_cid or "Pending")
        
        console.print(detailed_table)
        


@aggregation_app.command("show-t2-batches")
def show_t2_batches(
    network: str = typer.Option(None, "--network", help="Network to use"),
    model_id: str = typer.Option(None, "--model-id", help="Model ID"),
    gi: int = typer.Option(None, "--gi", help="Global iteration number"),
    detailed: bool = typer.Option(False, "--detailed", help="Show detailed information"),
):
    effective_network = resolve_network(network)
    w3 = get_w3(effective_network)
    account = load_account() 

    task_coordinator_address = get_manifest_key(effective_network, "DINTaskCoordinator_Contract", model_id)
        
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator_address)

    curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()
    GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()

    if not gi:
        ref_gi = curr_GI
    else:
        if gi > curr_GI:
            console.print(f"[red]Error:[/red] Invalid global iteration {gi} given in command: gi > curr_GI ({curr_GI})")
            raise typer.Exit(1)
        ref_gi = gi

    if (ref_gi == curr_GI and GIstate >= GIstatestrToIndex("T1nT2Bcreated")) or (ref_gi < curr_GI):
        console.print(f"[bold green]Showing Tier 2 batches for GI {ref_gi} (GIstate: {GIstateToStr(GIstate)}) on network {effective_network} for model {model_id} on TaskCoordinator {task_coordinator_address}![/bold green]")
    else:
        console.print(f"[red]Error:[/red] GI state is {GIstateToStr(GIstate)}. Batches do not exist yet.")
        raise typer.Exit(1)

    # Assuming 1 T2 batch for now as per reference code
    t2_count = 1 
    
    table = Table(title=f"Tier 2 Batches (GI: {curr_GI})")
    table.add_column("Batch ID", justify="right", style="cyan")
    table.add_column("Aggregators", style="magenta")
    if detailed:
        table.add_column("Submitted CID", style="green")
    table.add_column("Finalized", style="yellow")
    table.add_column("Final CID", style="white")
    
    for i in range(t2_count):
        try:
            bid, validators, finalized, cid = deployed_DINTaskCoordinatorContract.functions.getTier2Batch(curr_GI, i).call()
            val_display = "\n".join([f"{v[:6]}...{v[-4:]}" for v in validators])
            if not detailed:
                table.add_row(str(bid), val_display, str(finalized), cid or "")
            else:
                submitted_cid_display = "\n".join(deployed_DINTaskCoordinatorContract.functions.t2SubmissionCID(curr_GI, bid, v).call() for v in validators)
                table.add_row(str(bid), val_display, submitted_cid_display, str(finalized), cid or "")
        except Exception:
            # Maybe batch doesn't exist if count assumption is wrong or not created
            pass

    console.print(table)


@t1_app.command("start")
def start_t1_aggregation(
    network: str = typer.Option(None, "--network", help="Network to use"),
    model_id: str = typer.Option(None, "--model-id", help="Model ID"),
    gi: int = typer.Option(None, "--gi", help="Global iteration number"),
):
    effective_network = resolve_network(network)
    w3 = get_w3(effective_network)
    account = load_account()

    task_coordinator_address = get_manifest_key(effective_network, "DINTaskCoordinator_Contract", model_id)
        
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator_address)
    
    curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()

    GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()

    if gi:
        if curr_GI != gi:
            console.print(f"[red]Error:[/red] invalid global iteration {gi} does not match current GI {curr_GI}")
            raise typer.Exit(1)
    
    if GIstate < GIstatestrToIndex("T1nT2Bcreated"):
        console.print(f"[red]Error:[/red] GI state is {GIstateToStr(GIstate)}. GI state T1nT2Bcreated not passed yet.")
        raise typer.Exit(1)
    
    console.print(f"[bold green]Starting Tier 1 Aggregation for GI {curr_GI}...[/bold green]")
    
    tx = deployed_DINTaskCoordinatorContract.functions.startT1Aggregation(curr_GI).build_transaction({
        "from": account.address,
        "gas": 3000000,
        "gasPrice": w3.to_wei("5", "gwei"),
        "nonce": w3.eth.get_transaction_count(account.address),
        "chainId": w3.eth.chain_id,
    })
    
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    console.print(f"[dim]Tx hash: {tx_hash.hex()}[/dim]")
    
    w3.eth.wait_for_transaction_receipt(tx_hash)
    console.print("[green]✓ Tier 1 Aggregation started[/green]")


@t1_app.command("close")
def close_t1_aggregation(
    network: str = typer.Option(None, "--network", help="Network to use"),
    model_id: str = typer.Option(None, "--model-id", help="Model ID"),
    gi: int = typer.Option(None, "--gi", help="Global iteration number"),
):
    effective_network = resolve_network(network)
    w3 = get_w3(effective_network)
    account = load_account()

    task_coordinator_address = get_manifest_key(effective_network, "DINTaskCoordinator_Contract", model_id)
        
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator_address)
    
    curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()
    GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()
    
    if gi:
        if curr_GI != gi:
            console.print(f"[red]Error:[/red] invalid global iteration {gi} does not match current GI {curr_GI}")
            raise typer.Exit(1)

    if GIstate < GIstatestrToIndex("T1AggregationStarted"):
        console.print(f"[red]Error:[/red] GI state is {GIstateToStr(GIstate)}. GI state T1AggregationStarted not passed yet.")
        raise typer.Exit(1)
    
    console.print(f"[bold green]Finalizing Tier 1 Aggregation for GI {curr_GI}... on model {model_id} and network {effective_network} and task coordinator {task_coordinator_address}![/bold green]")
    
    tx = deployed_DINTaskCoordinatorContract.functions.finalizeT1Aggregation(curr_GI).build_transaction({
        "from": account.address,
        "gas": 3000000,
        "gasPrice": w3.to_wei("5", "gwei"),
        "nonce": w3.eth.get_transaction_count(account.address),
        "chainId": w3.eth.chain_id,
    })
    
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    console.print(f"[dim]Tx hash: {tx_hash.hex()}[/dim]")
    
    w3.eth.wait_for_transaction_receipt(tx_hash)
    console.print("[green]✓ Tier 1 Aggregation finalized[/green]")


@t2_app.command("start")
def start_t2_aggregation(
    network: str = typer.Option(None, "--network", help="Network to use"),
    model_id: str = typer.Option(None, "--model-id", help="Model ID"),
    gi: int = typer.Option(None, "--gi", help="Global iteration number"),
):
    effective_network = resolve_network(network)
    w3 = get_w3(effective_network)
    account = load_account()

    task_coordinator_address = get_manifest_key(effective_network, "DINTaskCoordinator_Contract", model_id)
        
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator_address)
    
    curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()

    GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()

    if gi:
        if curr_GI != gi:
            console.print(f"[red]Error:[/red] invalid global iteration {gi} does not match current GI {curr_GI}")
            raise typer.Exit(1)

    if GIstate < GIstatestrToIndex("T1AggregationDone"):
        console.print(f"[red]Error:[/red] GI state is {GIstateToStr(GIstate)}. GI state T1AggregationDone not passed yet.")
        raise typer.Exit(1)
    
    console.print(f"[bold green]Starting Tier 2 Aggregation for GI {curr_GI}... on model {model_id} and network {effective_network} and task coordinator {task_coordinator_address}![/bold green]")
    
    tx = deployed_DINTaskCoordinatorContract.functions.startT2Aggregation(curr_GI).build_transaction({
        "from": account.address,
        "gas": 3000000,
        "gasPrice": w3.to_wei("5", "gwei"),
        "nonce": w3.eth.get_transaction_count(account.address),
    })
    
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    console.print(f"[dim]Tx hash: {tx_hash.hex()}[/dim]")
    
    w3.eth.wait_for_transaction_receipt(tx_hash)
    console.print("[green]✓ Tier 2 Aggregation started[/green]")


@t2_app.command("close")
def close_t2_aggregation(
    network: str = typer.Option(None, "--network", help="Network to use"),
    model_id: str = typer.Option(None, "--model-id", help="Model ID"),
    gi: int = typer.Option(None, "--gi", help="Global iteration number"),
):
    effective_network = resolve_network(network)
    w3 = get_w3(effective_network)
    account = load_account()

    task_coordinator_address = get_manifest_key(effective_network, "DINTaskCoordinator_Contract", model_id)
        
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator_address)
    
    curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()

    GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()

    if gi:
        if curr_GI != gi:
            console.print(f"[red]Error:[/red] invalid global iteration {gi} does not match current GI {curr_GI}")
            raise typer.Exit(1)

    if GIstate < GIstatestrToIndex("T2AggregationStarted"):
        console.print(f"[red]Error:[/red] GI state is {GIstateToStr(GIstate)}. GI state T2AggregationStarted not passed yet.")
        raise typer.Exit(1)
    
    console.print(f"[bold green]Finalizing Tier 2 Aggregation for GI {curr_GI}... on model {model_id} and network {effective_network} and task coordinator {task_coordinator_address}![/bold green]")
    
    # 1. Finalize T2 Aggregation
    console.print("[cyan]Calling finalizeT2Aggregation...[/cyan]")
    tx = deployed_DINTaskCoordinatorContract.functions.finalizeT2Aggregation(curr_GI).build_transaction({
        "from": account.address,
        "gas": 3000000,
        "gasPrice": w3.to_wei("5", "gwei"),
        "nonce": w3.eth.get_transaction_count(account.address),
    })
    
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    console.print(f"[dim]Tx hash: {tx_hash.hex()}[/dim]")
    w3.eth.wait_for_transaction_receipt(tx_hash)
    
    # 2. Get Tier 2 batch to find final CID
    tier2_batch = deployed_DINTaskCoordinatorContract.functions.getTier2Batch(curr_GI, 0).call()
    # (bid, validators, finalized, cid)
    finalCID = tier2_batch[3]
    
    console.print(f"[cyan]Final CID:[/cyan] {finalCID}")
    
    # 3. Calculate score
    console.print("[cyan]Calculating score for final model...[/cyan]")

    if get_manifest_key(effective_network, "getscoreforGM", model_id)["type"] == "custom":
        model_base_path = Path(CACHE_DIR) / effective_network /  f"model_{model_id}" 
        service_path_str = get_manifest_key(effective_network, "getscoreforGM", model_id)["path"]

        model_service_path_str = get_manifest_key(effective_network, "ModelArchitecture", model_id)["path"]

        custom_modelowner_service_path = model_base_path / Path(service_path_str)
        
        custom_model_service_path = model_base_path / Path(model_service_path_str)

        if not custom_modelowner_service_path.exists():
            retrieve_from_ipfs(get_manifest_key(effective_network,"getscoreforGM", model_id)["ipfs"], custom_modelowner_service_path)

        if not custom_model_service_path.exists():
            retrieve_from_ipfs(get_manifest_key(effective_network,"ModelArchitecture", model_id)["ipfs"], custom_model_service_path)

        fn = load_custom_fn(
            custom_modelowner_service_path,
            "getscoreforGM")

        if not (Path(model_base_path)/"models"/"genesis_model.pth").exists():
            retrieve_from_ipfs(get_manifest_key(effective_network,"Genesis_Model_CID", model_id), str(Path(model_base_path)/"models"/"genesis_model.pth"))

        if not (Path(model_base_path)/"dataset"/"test"/"test_dataset.pt").exists():
            console.print("[red]Error:[/red] Test dataset not found at ", str(Path(model_base_path)/"dataset"/"test"/"test_dataset.pt"))
            console.print("[yellow]Warning:[/yellow] please ensure the test dataset is present at ", str(Path(model_base_path)/"dataset"/"test"/"test_dataset.pt"))
            raise typer.Exit(1) 


        
        accuracy = fn(curr_GI, finalCID, model_base_path)

    else:
        accuracy = getscoreforGM(curr_GI, finalCID)

    console.print(f"[green]Accuracy:[/green] {accuracy}")
    
    # 4. Set Tier 2 score
    console.print("[cyan]Setting Tier 2 score...[/cyan]")
    nonce = w3.eth.get_transaction_count(account.address)
    tx = deployed_DINTaskCoordinatorContract.functions.setTier2Score(curr_GI, int(accuracy)).build_transaction({
        "from": account.address,
        "gas": 3000000,
        "gasPrice": w3.to_wei("5", "gwei"),
        "nonce": nonce,
    })
    
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    console.print(f"[dim]Score Tx hash: {tx_hash.hex()}[/dim]")
    
    w3.eth.wait_for_transaction_receipt(tx_hash)
    
    console.print("[green]✓ Tier 2 Aggregation finalized and score set[/green]")

@slash_app.command("auditors")
def slash_auditors(
    network: str = typer.Option(None, "--network", help="Network to use"),
    model_id: int = typer.Option(..., "--model-id", help="Model ID"),
    gi: int = typer.Option(None, "--gi", help="Global iteration number"),
):
    effective_network = resolve_network(network)
    w3 = get_w3(effective_network)
    account = load_account()

    task_coordinator_address = get_manifest_key(effective_network, "DINTaskCoordinator_Contract", model_id)
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator_address)
    
    curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()

    GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()

    if gi is not None and curr_GI != gi:
        console.print(f"[red]Error:[/red] GI is {curr_GI}. GI {gi} not passed yet.")
        raise typer.Exit(1)

    if GIstate < GIstatestrToIndex("T2AggregationDone"):
        console.print(f"[red]Error:[/red] GI state is {GIstateToStr(GIstate)}. GI state T2AggregationDone not passed yet.")
        raise typer.Exit(1)
    
    console.print(f"[bold green]Slashing for GI {curr_GI}...[/bold green]")
    
    # 1. Slash
    console.print(f"[cyan]Calling slashAuditors... for GI {curr_GI} with account {account.address} on task coordinator {task_coordinator_address}[/cyan]")
    tx = deployed_DINTaskCoordinatorContract.functions.slashAuditors(curr_GI).build_transaction({
        "from": account.address,
        "gas": 3000000,
        "gasPrice": w3.to_wei("5", "gwei"),
        "nonce": w3.eth.get_transaction_count(account.address),
        "chainId": w3.eth.chain_id,
    })
    
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt.status == 0:
        console.print(f"[red]Error:[/red] Slash Auditors Transaction failed with status {receipt.status}")
        raise typer.Exit(1)
    console.print(f"[dim]Tx hash: {tx_hash.hex()}[/dim]")
   
    
    console.print("[green]✓ Auditors slashed[/green]")

@slash_app.command("aggregators")
def slash_aggregators(
    network: str = typer.Option(None, "--network", help="Network to use"),
    model_id: int = typer.Option(..., "--model-id", help="Model ID"),
    gi: int = typer.Option(None, "--gi", help="Global iteration number"),
):
    effective_network = resolve_network(network)
    w3 = get_w3(effective_network)
    account = load_account()

    task_coordinator_address = get_manifest_key(effective_network, "DINTaskCoordinator_Contract", model_id)
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator_address)
    
    curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()

    GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()

    if gi is not None and curr_GI != gi:
        console.print(f"[red]Error:[/red] invalid GI, current GI is {curr_GI}")
        raise typer.Exit(1)

    if GIstate < GIstatestrToIndex("AuditorsSlashed"):
        console.print(f"[red]Error:[/red] GI state is {GIstateToStr(GIstate)}. GI state AuditorsSlashed not passed yet.")
        raise typer.Exit(1)
    
    console.print(f"[bold green]Slashing Aggregators for GI {curr_GI}...[/bold green]")

    # 1. Slash
    console.print(f"[cyan]Calling slash Aggregators... for GI {curr_GI} with account {account.address} on task coordinator {task_coordinator}[/cyan]")
    tx = deployed_DINTaskCoordinatorContract.functions.slashValidators(curr_GI).build_transaction({
        "from": account.address,
        "gas": 3000000,
        "gasPrice": w3.to_wei("5", "gwei"),
        "nonce": w3.eth.get_transaction_count(account.address),
        "chainId": w3.eth.chain_id,
    })
    
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt.status == 0:
        console.print(f"[red]Error:[/red] Slash Aggregators Transaction failed with status {receipt.status}")
        raise typer.Exit(1)
    console.print(f"[dim]Tx hash: {tx_hash.hex()}[/dim]")
   
    
    console.print("[green]✓ Aggregators slashed[/green]")

@gi_app.command()
def end(
    network: str = typer.Option(None, "--network", help="Network to use"),
    model_id: int = typer.Option(..., "--model-id", help="Model ID"),
    gi: int = typer.Option(None, "--gi", help="Global iteration number"),
):
    effective_network = resolve_network(network)
    w3 = get_w3(effective_network)
    account = load_account()

    task_coordinator_address = get_manifest_key(effective_network, "DINTaskCoordinator_Contract", model_id)
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator_address)
    
    curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()

    GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()

    if gi is not None and curr_GI != gi:
            console.print(f"[red]Error:[/red] invalid GI, current GI is {curr_GI}")
            raise typer.Exit(1)

    if GIstate < GIstatestrToIndex("AggregatorsSlashed"):
        console.print(f"[red]Error:[/red] GI state is {GIstateToStr(GIstate)}. GI state AggregatorsSlashed not passed yet.")
        raise typer.Exit(1)
    
    console.print(f"[bold green]Ending GI {curr_GI}...[/bold green]")   
    
    # 1. End
    console.print(f"[cyan]Calling end GI... for GI {curr_GI} with account {account.address} on task coordinator {task_coordinator}[/cyan]")
    tx = deployed_DINTaskCoordinatorContract.functions.endGI(curr_GI).build_transaction({
        "from": account.address,
        "gas": 3000000,
        "gasPrice": w3.to_wei("5", "gwei"),
        "nonce": w3.eth.get_transaction_count(account.address),
        "chainId": w3.eth.chain_id,
    })
    
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt.status == 0:
        console.print(f"[red]Error:[/red] End Transaction failed with status {receipt.status}")
        raise typer.Exit(1)
    console.print(f"[dim]Tx hash: {tx_hash.hex()}[/dim]")
    
    
    console.print("[green]✓ GI ended[/green]")



@lms_evaluation_app.command("show")
def show(
    network: str = typer.Option(None, "--network", help="Network to use"),
    auditors: bool = typer.Option(False, "--auditors", help="Show auditor evaluations"),
    gi: int = typer.Option(None, "--gi", help="Global iteration number"),
    model_id: str = typer.Option(None, "--model-id", help="Model ID"),
    models: bool = typer.Option(False, "--models", help="Show auditors lms evaluations per lms"),
):
    effective_network = resolve_network(network)
    w3 = get_w3(effective_network)
    account = load_account()

    task_coordinator_address = get_manifest_key(effective_network, "DINTaskCoordinator_Contract", model_id)
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator_address)
    
    curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()

    GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()

    task_auditor_address = get_manifest_key(effective_network, "DINTaskAuditor_Contract", model_id)
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskAuditor.json"
    deployed_DINTaskAuditorContract = get_contract_instance(str(artifact_path), effective_network, task_auditor_address)

    if not gi:
        ref_gi = curr_GI
    else:
        if gi > curr_GI:
            console.print(f"[red]Error:[/red] Invalid global iteration {gi} given in command: gi > curr_GI ({curr_GI})")
            raise typer.Exit(1)
        ref_gi = gi


    if (ref_gi == curr_GI and GIstate >= GIstatestrToIndex("AuditorsBatchesCreated")) or (ref_gi < curr_GI):
        console.print(f"[bold green]Showing LMS Evaluation for GI {curr_GI} on TaskCoordinator {task_coordinator_address} and TaskAuditor {task_auditor_address}...[/bold green]")   
    else:
        console.print(f"[red]Error:[/red] GI state is {GIstateToStr(GIstate)}. GI state AuditorsBatchesCreated not passed yet.")
        raise typer.Exit(1)
    
    # load lm submissions (client models) once
    raw_lm_submissions = deployed_DINTaskAuditorContract.functions.getClientModels(curr_GI).call()
    lm_submissions = {}
    for idx, sub in enumerate(raw_lm_submissions):
        client, model_cid, submitted_at, eligible, evaluated, approved, final_avg = sub
        lm_submissions[idx] = {
            "model_index": idx,
            "client": client,
            "model_cid": model_cid,
            "submitted_at": submitted_at,
            "eligible": eligible,
            "evaluated": evaluated,
            "approved": approved,
            "final_avg": final_avg,
        }

    # Precompute audit batches and mappings only if needed (auditors view or models view)
    audtor_batch_count = deployed_DINTaskAuditorContract.functions.AuditorsBatchCount(curr_GI).call()
    model_idx_to_batch_id = {}
    model_idx_to_test_cid = {}
    batch_id_to_auditors = {}
    model_idx_to_auditors = {}
    all_auditors = set()

    if auditors or models:
        raw_audit_batches = []
        for i in range(audtor_batch_count):
            batch = deployed_DINTaskAuditorContract.functions.getAuditorsBatch(curr_GI, i).call()
            if batch:
                raw_audit_batches.append(batch)

        for batch_data in raw_audit_batches:
            batch_id, batch_auditors, model_indexes, test_cid = batch_data
            batch_id_to_auditors[batch_id] = list(batch_auditors)
            for m_idx in model_indexes:
                model_idx_to_batch_id[m_idx] = batch_id
                model_idx_to_test_cid[m_idx] = test_cid
                # collect auditors assigned to each model
                model_idx_to_auditors.setdefault(m_idx, set()).update(batch_auditors)
            all_auditors.update(batch_auditors)

        # normalize model_idx_to_auditors sets to lists
        for k in model_idx_to_auditors:
            model_idx_to_auditors[k] = sorted(model_idx_to_auditors[k])

    # If auditors view requested: build per-auditor assigned models and their on-chain states
    assigned_lm_submissions = {}
    if auditors:
        for auditor_addr in sorted(all_auditors):
            assigned_lm_submissions[auditor_addr] = []
            # find models assigned to this auditor by scanning model_idx_to_auditors
            for model_idx, auditors_list in model_idx_to_auditors.items():
                if auditor_addr not in auditors_list:
                    continue
                batch_id = model_idx_to_batch_id.get(model_idx)
                has_voted = deployed_DINTaskAuditorContract.functions.hasAuditedLM(curr_GI, batch_id, auditor_addr, model_idx).call()
                is_eligible = deployed_DINTaskAuditorContract.functions.LMeligibleVote(curr_GI, batch_id, auditor_addr, model_idx).call()
                audit_scores = deployed_DINTaskAuditorContract.functions.auditScores(curr_GI, batch_id, auditor_addr, model_idx).call()

                lm = lm_submissions.get(model_idx)
                client = lm["client"] if lm else "Unknown"
                model_cid = lm["model_cid"] if lm else "N/A"
                test_cid = model_idx_to_test_cid.get(model_idx)

                assigned_lm_submissions[auditor_addr].append({
                    "model_index": model_idx,
                    "client": client,
                    "model_cid": model_cid,
                    "batch_id": batch_id,
                    "has_voted": has_voted,
                    "is_eligible": is_eligible,
                    "audit_scores": audit_scores,
                    "test_cid": test_cid,
                })

    # Print LM submissions table (keeps your existing output)
    lm_submissions_table = Table(title=f"LM Submissions for GI {curr_GI}", show_header=True, header_style="bold magenta")
    lm_submissions_table.add_column("Model Index", style="dim")
    lm_submissions_table.add_column("Client", overflow="fold")
    lm_submissions_table.add_column("Model CID", overflow="fold")
    lm_submissions_table.add_column("Submitted At", overflow="fold")
    lm_submissions_table.add_column("Eligible", overflow="fold")
    lm_submissions_table.add_column("Evaluated", overflow="fold")
    lm_submissions_table.add_column("Approved", overflow="fold")
    lm_submissions_table.add_column("Final Avg", overflow="fold")

    for sub in lm_submissions.values():
        lm_submissions_table.add_row(
            str(sub["model_index"]),
            str(sub["client"]),
            str(sub["model_cid"]),
            str(sub["submitted_at"]),
            str(sub["eligible"]),
            str(sub["evaluated"]),
            str(sub["approved"]),
            str(sub["final_avg"]) if sub["final_avg"] != "None" else "—"
        )
    console.print(lm_submissions_table)

    # Print per-auditor assigned tables if requested
    if auditors:
        for auditor_addr in sorted(assigned_lm_submissions.keys()):
            assigned_lm_submissions_table = Table(
                title=f"Assigned LM Submissions for GI {curr_GI} for auditor {auditor_addr}",
                show_header=True,
                header_style="bold magenta"
            )
            assigned_lm_submissions_table.add_column("Model Index", style="dim")
            assigned_lm_submissions_table.add_column("Client", overflow="fold")
            assigned_lm_submissions_table.add_column("Model CID", overflow="fold")
            assigned_lm_submissions_table.add_column("Batch ID", overflow="fold")
            assigned_lm_submissions_table.add_column("Has Voted", overflow="fold")
            assigned_lm_submissions_table.add_column("Is Eligible", overflow="fold")
            assigned_lm_submissions_table.add_column("Audit Scores", overflow="fold")
            assigned_lm_submissions_table.add_column("Test CID", overflow="fold")

            for sub in assigned_lm_submissions[auditor_addr]:
                assigned_lm_submissions_table.add_row(
                    str(sub["model_index"]),
                    str(sub["client"]),
                    str(sub["model_cid"]),
                    str(sub["batch_id"]),
                    str(sub["has_voted"]),
                    str(sub["is_eligible"]),
                    str(sub["audit_scores"]) if sub["audit_scores"] is not None else "—",
                    str(sub["test_cid"]) if sub["test_cid"] is not None else "—"
                )
            console.print(assigned_lm_submissions_table)

    # Print per-model evaluation tables if requested (--models)
    if models:
        # iterate through all models (sorted)
        for model_idx in sorted(lm_submissions.keys()):
            batch_id = model_idx_to_batch_id.get(model_idx)
            auditors_for_model = model_idx_to_auditors.get(model_idx, [])
            model_eval_table = Table(title=f"Evaluations for Model {model_idx} (GI {curr_GI})", show_header=True, header_style="bold cyan")
            model_eval_table.add_column("Auditor", overflow="fold")
            model_eval_table.add_column("Batch ID", style="dim")
            model_eval_table.add_column("Has Voted")
            model_eval_table.add_column("Is Eligible")
            model_eval_table.add_column("Audit Scores", overflow="fold")

            if not auditors_for_model:
                model_eval_table.add_row("—", str(batch_id) if batch_id is not None else "—", "—", "—", "—")
            else:
                for auditor_addr in auditors_for_model:
                    has_voted = deployed_DINTaskAuditorContract.functions.hasAuditedLM(curr_GI, batch_id, auditor_addr, model_idx).call()
                    is_eligible = deployed_DINTaskAuditorContract.functions.LMeligibleVote(curr_GI, batch_id, auditor_addr, model_idx).call()
                    audit_scores = deployed_DINTaskAuditorContract.functions.auditScores(curr_GI, batch_id, auditor_addr, model_idx).call()
                    model_eval_table.add_row(
                        str(auditor_addr),
                        str(batch_id),
                        str(has_voted),
                        str(is_eligible),
                        str(audit_scores) if audit_scores is not None else "—"
                    )
            console.print(model_eval_table)
            test_cid = model_idx_to_test_cid.get(model_idx)
            if test_cid:
                console.print(f"[dim]Test CID for model {model_idx}'s batch: {test_cid}[/dim]")




    