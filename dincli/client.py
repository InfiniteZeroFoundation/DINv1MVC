import typer
from rich import print
from typing import Optional
from rich.console import Console
from pathlib import Path
from dotenv import dotenv_values, set_key, get_key, unset_key
from dincli.utils import CACHE_DIR,resolve_network, get_w3, load_account, load_din_info, load_usdt_config, get_config, GIstatestrToIndex, get_manifest_key, load_custom_fn
from dincli.contract_utils import get_contract_instance
from dincli.services.ipfs import retrieve_from_ipfs, upload_to_ipfs
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
    model_id: Optional[int] = typer.Option(None, "--model-id", help="Model ID"),
    gi: Optional[int] = typer.Option(None, "--gi", help="Global iteration to use"),
):
    effective_network = resolve_network(network)
    
    w3 = get_w3(effective_network)
    account = load_account()


    task_auditor_address = get_manifest_key(effective_network, "DINTaskAuditor_Contract", model_id)
    task_coordinator_address = get_manifest_key(effective_network, "DINTaskCoordinator_Contract", model_id)

    dpmode = get_manifest_key(effective_network, "dp_mode", model_id)

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

    current_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()

    if gi:
        if gi != current_GI:
            console.print("[red]Error:[/red] Global iteration does not match current GI")
            raise typer.Exit(1)

   

    console.print("Training local model with task auditor: ", task_auditor_address, " and task coordinator: ", task_coordinator_address, " and current GI: ", current_GI)

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

    model_base_dir = Path(CACHE_DIR) / effective_network / f"model_{model_id}"
    if get_manifest_key(effective_network, "train_client_model_and_upload_to_ipfs", model_id)["type"] == "custom":

        client_service_path_str = get_manifest_key(effective_network, "train_client_model_and_upload_to_ipfs", model_id)["path"]

        model_service_path_str = get_manifest_key(effective_network, "ModelArchitecture", model_id)["path"]

        client_service_path = model_base_dir / Path(client_service_path_str)
        model_service_path = model_base_dir / Path(model_service_path_str)

        if not client_service_path.exists():
            retrieve_from_ipfs(get_manifest_key(effective_network,"train_client_model_and_upload_to_ipfs", model_id)["ipfs"], client_service_path)
        
        if not model_service_path.exists():
            retrieve_from_ipfs(get_manifest_key(effective_network,"ModelArchitecture", model_id)["ipfs"], model_service_path)

        fn = load_custom_fn(
            client_service_path,
            "train_client_model_and_upload_to_ipfs")

        client_model_ipfs_hash = fn(
            genesis_model_ipfs_hash,
            account.address,
            effective_network,
            initial_model_ipfs_hash=initial_model_ipfs_hash,
            dp_mode=dpmode,
            model_base_dir=model_base_dir,
            gi=current_GI,
        )


    else:

        client_model_ipfs_hash = train_client_model_and_upload_to_ipfs(
        genesis_model_ipfs_hash,
        account.address,
        effective_network,
        initial_model_ipfs_hash=initial_model_ipfs_hash,
        dp_mode=dpmode, 
        base_path=model_base_dir
        )

    if submit:
        console.print("Submitting local model to task auditor: ", task_auditor_address, "with IPFS hash: ", client_model_ipfs_hash)


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
            message = f" ✓ Local model submitted to task auditor: {task_auditor_address} with IPFS hash: {client_model_ipfs_hash}"
            console.print(f"[bold green]{message}[/bold green]")
        else:
            message = f" ✗ Local model submission failed to task auditor: {task_auditor_address} with IPFS hash: {client_model_ipfs_hash}"
            console.print(f"[bold red]{message}[/bold red]")



@lms_app.command()
def show_models(
    network: str = typer.Option(None, "--network", help="Target network (local|sepolia|mainnet)"),
    model_id: int = typer.Option(None, "--model-id", help="Model ID to use"),
    gi: int = typer.Option(None, "--gi", help="Global iteration to use"),
):
    
    effective_network = resolve_network(network)
    
    w3 = get_w3(effective_network)
    account = load_account()

    task_auditor_address = get_manifest_key(effective_network, "DINTaskAuditor_Contract", model_id)
    task_coordinator_address = get_manifest_key(effective_network, "DINTaskCoordinator_Contract", model_id)
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskCoordinator.json"
    
    # if artifact_path does not exist, raise error
    if not artifact_path.exists():
        console.print("[red]Error:[/red] ABI file not found")
        raise typer.Exit(1)
    
    deployed_DINTaskCoordinatorContract = get_contract_instance(str(artifact_path), effective_network, task_coordinator_address)
    
    curr_GI = deployed_DINTaskCoordinatorContract.functions.GI().call()
    
    
    artifact_path = Path(__file__).parent / "abis" / "DINTaskAuditor.json"
    
    # if artifact_path does not exist, raise error
    if not artifact_path.exists():
        console.print("[red]Error:[/red] ABI file not found")
        raise typer.Exit(1)
    
    deployed_DINTaskAuditorContract = get_contract_instance(str(artifact_path), effective_network, task_auditor_address)
    
    if not gi:
        ref_gi = curr_GI
    else:
        if gi > curr_GI:
            console.print(f"[red]Error:[/red] Invalid global iteration {gi} given in command: gi > curr_GI ({curr_GI})")
            raise typer.Exit(1)
        ref_gi = gi


    console.print(f"[bold green]Showing local model submissions for global iteration {ref_gi} on TaskCoordinator {task_coordinator_address} and TaskAuditor {task_auditor_address}![/bold green]")
    console.print(f"[cyan]Network:[/cyan] {effective_network}")
    console.print(f"[cyan]From account:[/cyan] {account.address}")

    GIstate = deployed_DINTaskCoordinatorContract.functions.GIstate().call()

    if (ref_gi == curr_GI and GIstate >= GIstatestrToIndex("LMSstarted")) or (ref_gi < curr_GI):
        has_submitted = deployed_DINTaskAuditorContract.functions.clientHasSubmitted(ref_gi, account.address).call()
        console.print(f"[green]✓ Client {account.address} has submitted {has_submitted}![/green]")
        if not has_submitted:
            console.print(f"[red]Error:[/red] No local model submission found for account {account.address} in global iteration {ref_gi}")
            raise typer.Exit(1)

        has_index = deployed_DINTaskAuditorContract.functions.clientSubmissionIndex(ref_gi, account.address).call()

        lm_submission = deployed_DINTaskAuditorContract.functions.lmSubmissions(ref_gi, has_index).call()
        

      
        console.print(f"[green]✓ Local model submission found![/green]")
        console.print(f"[green]✓ Client {lm_submission[0]} submitted model {lm_submission[1]}![/green]")

        console.print(f"[bold green]✓ Local model submissions shown![/bold green]")

    else:
        console.print("[red]Error:[/red] Invalid global iteration {gi} given in command: gi > curr_GI ({curr_GI})")
        raise typer.Exit(1)