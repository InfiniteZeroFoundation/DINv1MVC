import typer
import os
from rich import print
from dincli.utils import resolve_network, CONFIG_DIR, load_tasks, save_tasks, load_account, get_w3, get_env_key, load_din_info, cache_manifest
from pathlib import Path
from dincli.services.ipfs import upload_to_ipfs
from dincli.contract_utils import get_contract_instance
from rich.console import Console

console = Console()

app = typer.Typer(help="Manage DIN tasks/models across networks.")

model_owner_app = typer.Typer( help="model owner commands")


app.add_typer(model_owner_app, name="model-owner")



@app.command()
def list(
    network: str = typer.Option(None, help="Target network"),
    models: bool = typer.Option(False, "--models", help="List models"),
    roles: bool = typer.Option(False, "--roles", help="List roles for a model"),
    model_id: str = typer.Option(None, "--model-id", help="Model ID (e.g. model_0)"),
):
    """
    List networks, models, or roles depending on flags.
    """

    effective_network = resolve_network(network)

    tasks = load_tasks()

    if "networks" not in tasks:
        tasks["networks"] = {}

    if effective_network not in tasks["networks"]:
        tasks["networks"][effective_network] = {}



@app.command()
def add(
    network: str = typer.Option(...),
    model_id: int = typer.Option(...),
    role: str = typer.Option(...),
):
    """
    Add a model role binding.
    """

    if role not in ["aggregator", "auditor", "client", "model-owner"]:
        print(f"[red]Error:[/red] Invalid role: {role}")
        raise typer.Exit(1)

    effective_network = resolve_network(network)

    tasks = load_tasks()

    if "networks" not in tasks:
        tasks["networks"] = {}

    if effective_network not in tasks["networks"]:
        tasks["networks"][effective_network] = {}

    if "model_" + str(model_id) not in tasks["networks"][effective_network]:

        roles = []
        manifesto_cid = "None"
        genesis_model_cid = "None"
        
        if role not in roles:
            roles.append(role)
        
        tasks["networks"][effective_network]["model_" + str(model_id)] = {
            "manifesto_cid": manifesto_cid,
            "genesis_model_cid": genesis_model_cid,
            "roles": roles
        }

    

    tasks["networks"][effective_network][model_id][role] = True

    save_tasks(tasks)

    print(f"[green]Model role binding added successfully: {model_id} {role}[/green]")





# @app.command()
# def remove(
#     network: str = typer.Option(None, "--network", help="Target network (local|sepolia|mainnet)"),
# )

# @app.command()
# def activate(
#     network: str = typer.Option(None, "--network", help="Target network (local|sepolia|mainnet)"),
# )

# @app.command()
# def deactivate(
#     network: str = typer.Option(None, "--network", help="Target network (local|sepolia|mainnet)"),
# )


# @app.command()
# def update(
#     network: str = typer.Option(None, "--network", help="Target network (local|sepolia|mainnet)"),
# )

@app.command()
def explore(
    network: str = typer.Option(None, "--network", help="Target network (local|sepolia|mainnet)"),
    model_id: int = typer.Option(..., "--model-id", help="Model ID (e.g. 0,1,2)"),
    update: bool = typer.Option(False, "--update", help="Update model info"),
):
    """
    Explore a model.
    """
    effective_network = resolve_network(network)

    w3 = get_w3(effective_network)


    cache_manifest(model_id, effective_network, True, update)


    
@model_owner_app.command("register") 
def register(
    network: str = typer.Option(None, "--network"),
    taskCoordinator: str = typer.Option(None, "--taskCoordinator"),
    taskAuditor: str = typer.Option(None, "--taskAuditor"),
    dinregistry_artifact: str = typer.Option(None, "--dinregistry-artifact"),
    manifestpath: str = typer.Option(None, "--manifestpath"),
    manifestCID: str = typer.Option(None, "--manifestCID"),
    isOpenSource: bool = typer.Option(False, "--isOpenSource"),
):
    """ 
    Register a model in DINRegistry
    """ 
    effective_network = resolve_network(network)

    w3 = get_w3(effective_network)


    if not taskCoordinator:
        taskCoordinator = get_env_key(effective_network.upper() + "_DINTaskCoordinator_Contract_Address")

    if not taskAuditor:
        taskAuditor = get_env_key(effective_network.upper() + "_" + taskCoordinator + "_DINTaskAuditor_Contract_Address")

    if not dinregistry_artifact:
        dinregistry_artifact = Path(__file__).parent / "abis" / "DINModelRegistry.json"

    if not manifestCID:
        console.print("[gray]Manifest CID not provided, uploading manifest to IPFS...[/gray]")
        if not manifestpath:
            manifestpath = Path(os.getcwd()) / "tasks" /effective_network.lower() / taskCoordinator / "manifest.json"
            console.print(f"[gray]Custom manifest path not provided, using default manifest path: {manifestpath}[/gray]")
        if not os.path.exists(manifestpath):
            console.print("[red]Error:[/red] Manifest not found at path: {manifestpath}")
            raise typer.Exit(1)
        manifestCID = upload_to_ipfs(str(manifestpath), "manifest")
       
    # Load account
    account = load_account()

    din_info = load_din_info()

    if effective_network in din_info and "registry" in din_info[effective_network]:
        dinregistry = din_info[effective_network]["registry"]
    else:
        print("[red]Error:[/red] Please provide dinregistry")
        raise typer.Exit(1)

    # Get nonce
    nonce = w3.eth.get_transaction_count(account.address)

    dinregistry_contract = get_contract_instance(dinregistry_artifact, effective_network, dinregistry)

    console.print(f"[green]Registering model in DINRegistry[/green]")
    console.print(f"[gray]Manifest CID: {manifestCID}[/gray]")
    console.print(f"[gray]Task Coordinator: {taskCoordinator}[/gray]")
    console.print(f"[gray]Task Auditor: {taskAuditor}[/gray]")
    console.print(f"[gray]Is Open Source: {isOpenSource}[/gray]")

    tx = dinregistry_contract.functions.registerModel(manifestCID, taskCoordinator, taskAuditor, isOpenSource).build_transaction({
        'value':  w3.to_wei(0.01, 'ether'),
        'from': account.address,
        'nonce': nonce,
        'gas': 1000000,
        'gasPrice': w3.eth.gas_price,
        'chainId': w3.eth.chain_id
    })

    signed_tx = account.sign_transaction(tx)


    # Send raw transaction
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if tx_receipt.status == 1:
        console.print(f"[green]Model registered successfully in DINRegistry[/green]")

        events = dinregistry_contract.events.ModelRegistered().process_receipt(tx_receipt)

        if events:
            event = events[0]  # Usually one, but could be more in complex cases
            args = event['args']
            console.print("[bold cyan]ModelRegistered Event Emitted:[/bold cyan]")
            console.print(f"  Model ID: {args['modelId']}")
            console.print(f"  Owner: {args['owner']}")
            console.print(f"  Is Open Source: {args['isOpenSource']}")
            console.print(f"  Manifest CID: {args['manifestCID']}")
            console.print(f"  Transaction Hash: {tx_hash.hex()}")
    else:
        console.print("[yellow]Warning: ModelRegistered event not found in receipt.[/yellow]")
            
    
    
