import typer
from rich import print
from typing import Optional
from rich.console import Console
from pathlib import Path
from dotenv import dotenv_values, set_key, get_key, unset_key
from dincli.utils import resolve_network, get_w3, load_account, load_din_info, load_usdt_config, get_config, GIstatestrToIndex
from dincli.contract_utils import get_contract_instance
from dincli.services.client import train_client_model_and_upload_to_ipfs

app = typer.Typer(help="Commands for DIN clients in DIN.")

console = Console()


download_app = typer.Typer(help="Download model related files")
lms_app = typer.Typer(help="LMS related commands")

app.add_typer(download_app, name="download")
app.add_typer(lms_app, name="lms")

@app.command()
def train_lms(
    network: Optional[str] = typer.Option("local", help="Network to connect to"),
    submit: Optional[bool] = typer.Option(False, help="Submit the model to DIN"),
    task_auditor: Optional[str] = typer.Option(None, "--task-auditor", help="Task auditor address"),
    task_coordinator: Optional[str] = typer.Option(None, "--task-coordinator", help="Task coordinator address"),
    dpmode: Optional[str] = typer.Option("disabled", "--dpmode", help="DpMode to use"),
    gi: Optional[int] = typer.Option(None, "--gi", help="Global iteration to use"),
    demo: Optional[bool] = typer.Option(False, "--demo", help="Demo mode"),
):
    effective_network = resolve_network(network)
    
    w3 = get_w3(effective_network)
    account = load_account()


    if not task_auditor:
        task_auditor = get_key(".env", "DINTaskAuditor_Contract_Address")

    if not task_coordinator:
        task_coordinator = get_key(".env", "DINTaskCoordinator_Contract_Address")

    if not dpmode:
        dpmode = "disabled"

    artifact_path = Path(__file__).parent / "abis" / "DINTaskAuditor.json"
    
    # if artifact_path does not exist, raise error
    if not artifact_path.exists():
        console.print("[red]Error:[/red] ABI file not found")
        raise typer.Exit(1)
    
    deployed_DINTaskAuditorContract = get_contract_instance(str(artifact_path), effective_network, task_auditor)

    
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
    
    # if artifact_path does not exist, raise error
    if not artifact_path.exists():
        console.print("[red]Error:[/red] ABI file not found")
        raise typer.Exit(1)
    
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator)

    current_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()

    if gi:
        if gi != current_GI:
            console.print("[red]Error:[/red] Global iteration does not match current GI")
            raise typer.Exit(1)

   

    console.print("Training local model with task auditor: ", task_auditor, " and task coordinator: ", task_coordinator, " and current GI: ", current_GI)

    console.print("Using DpMode: ", dpmode)


    genesis_model_ipfs_hash = deployed_DINTaskCoordinatorContract.functions.genesisModelIpfsHash().call()

    console.print("Using Genesis Model IPFS Hash: ", genesis_model_ipfs_hash)

    initial_model_ipfs_hash = None
    t2_list = []
    if current_GI > 1:
        t2_batches_count = 1
        for i in range(t2_batches_count):
            (bid, val, fin, cid) = deployed_DINTaskCoordinatorContract.functions.getTier2Batch(current_GI-1, i).call()
            t2_list.append(Tier2Batch(batch_id=bid, validators=val, finalized=fin, final_cid=cid))
                 

            t2_batch_gi_minus_1 = t2_list[0]
            
            
            initial_model_ipfs_hash = t2_batch_gi_minus_1.final_cid

    console.print("Using Latest Global Model IPFS Hash: ", initial_model_ipfs_hash)

    

    client_model_ipfs_hash = train_client_model_and_upload_to_ipfs(
        genesis_model_ipfs_hash,
        account.address,
        effective_network,
        initial_model_ipfs_hash=initial_model_ipfs_hash,
        dp_mode=dpmode
    )

    if submit:
        console.print("Submitting local model to task auditor: ", task_auditor, "with IPFS hash: ", client_model_ipfs_hash)


        tx = deployed_DINTaskAuditorContract.functions.submitLocalModel(client_model_ipfs_hash, current_GI).build_transaction({"from": account.address,
        "gas": 3000000,
        "gasPrice": w3.to_wei("5", "gwei"),
        "nonce": w3.eth.get_transaction_count(account.address),
        "chainId": w3.eth.chain_id
        })

        signed_tx = account.sign_transaction(tx)

        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)


        if tx_receipt.status == 1:
            message = f" ✓ Local model submitted to task auditor: {task_auditor} with IPFS hash: {client_model_ipfs_hash}"
            console.print(f"[bold green]{message}[/bold green]")
        else:
            message = f" ✗ Local model submission failed to task auditor: {task_auditor} with IPFS hash: {client_model_ipfs_hash}"
            console.print(f"[bold red]{message}[/bold red]")



@lms_app.command()
def show_models(
    network: str = typer.Option(None, "--network", help="Target network (local|sepolia|mainnet)"),
    task_coordinator: str = typer.Option(None, "--task-coordinator", help="Task coordinator address"),
    task_auditor: str = typer.Option(None, "--task-auditor", help="Task auditor address"),
    gi: int = typer.Option(None, "--gi", help="Global iteration to use"),
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

    if not task_auditor:
        task_auditor = get_key(".env", "DINTaskAuditor_Contract_Address")
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskAuditor.json"
    
    # if artifact_path does not exist, raise error
    if not artifact_path.exists():
        console.print("[red]Error:[/red] ABI file not found")
        raise typer.Exit(1)
    
    deployed_DINTaskAuditorContract = get_contract_instance(str(artifact_path), effective_network, task_auditor)
    
    
    console.print(f"[bold green]Showing local model submissions for global iteration {curr_GI} on TaskCoordinator {task_coordinator} and TaskAuditor {task_auditor}![/bold green]")
    console.print(f"[cyan]Network:[/cyan] {effective_network}")
    console.print(f"[cyan]From account:[/cyan] {account.address}")

    client_model_ipfs_hashes = []
    ClientAddresses = []

    GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()

    if GIstate >= GIstatestrToIndex("LMSstarted"):
        lm_submissions = deployed_DINTaskAuditorContract.functions.getClientModels(curr_GI).call()
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

    

@download_app.command()
def gm_initial():
    console.print("Downloading GM initial file...")

@download_app.command()
def gm_latest():
    console.print("Downloading GM latest file...")

@download_app.command()
def scheme():
    console.print("Downloading scheme file...")