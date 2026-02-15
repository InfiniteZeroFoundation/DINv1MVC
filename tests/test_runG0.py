import os
import pytest

# Define constants for paths
PROJECT_ROOT = "/home/azureuser/projects/DINv1MVC"
HARDHAT_ARTIFACTS = os.path.join(PROJECT_ROOT, "hardhat/artifacts/contracts")

def test_run_g0_flow(cli_cmd):
    """
    Replicates the workflow from bashscripts/runG0.sh
    """
    # 13: show python -m dincli.main system where
    cli_cmd(["system", "where"])

    # 21: show python -m dincli.main system connect-wallet --account 0
    cli_cmd(["system", "connect-wallet", "--account", "0"])

    # 22: show python -m dincli.main dindao deploy din-coordinator --artifact ...
    din_coord_artifact = os.path.join(HARDHAT_ARTIFACTS, "DinCoordinator.sol/DinCoordinator.json")
    cli_cmd(["dindao", "deploy", "din-coordinator", "--artifact", din_coord_artifact])

    # 24: show python -m dincli.main system dump-abi --official --artifact ...
    cli_cmd(["system", "dump-abi", "--official", "--artifact", din_coord_artifact])

    # 26: show python -m dincli.main system dump-abi --official --artifact ... (DinToken)
    din_token_artifact = os.path.join(HARDHAT_ARTIFACTS, "DinToken.sol/DinToken.json")
    cli_cmd(["system", "dump-abi", "--official", "--artifact", din_token_artifact])

    # 28: show python -m dincli.main dindao deploy din-validator-stake --network local --artifact ...
    din_stake_artifact = os.path.join(HARDHAT_ARTIFACTS, "DinValidatorStake.sol/DinValidatorStake.json")
    cli_cmd(["dindao", "deploy", "din-validator-stake", "--network", "local", "--artifact", din_stake_artifact])

    # 30: show python -m dincli.main system dump-abi --official --artifact ...
    cli_cmd(["system", "dump-abi", "--official", "--artifact", din_stake_artifact])

    # 32: show python -m dincli.main dindao deploy din-model-registry --network local --artifact ...
    din_registry_artifact = os.path.join(HARDHAT_ARTIFACTS, "DINModelRegistry.sol/DINModelRegistry.json")
    cli_cmd(["dindao", "deploy", "din-model-registry", "--network", "local", "--artifact", din_registry_artifact])

    # 34: show python -m dincli.main system dump-abi --official --artifact ...
    cli_cmd(["system", "dump-abi", "--official", "--artifact", din_registry_artifact])

    # 36: show python -m dincli.main system connect-wallet --account 1
    cli_cmd(["system", "connect-wallet", "--account", "1"])

    # 37: show python -m dincli.main system --eth-balance --usdt-balance
    cli_cmd(["system", "--eth-balance", "--usdt-balance"])

    # 39: show python -m dincli.main system buy-usdt 3000 --network local --yes
    cli_cmd(["system", "buy-usdt", "3000", "--network", "local", "--yes"])

    # 42: show python -m dincli.main model-owner deploy task-coordinator --network local --artifact ...
    task_coord_artifact = os.path.join(HARDHAT_ARTIFACTS, "DINTaskCoordinator.sol/DINTaskCoordinator.json")
    cli_cmd(["model-owner", "deploy", "task-coordinator", "--network", "local", "--artifact", task_coord_artifact])

    # 44: show python -m dincli.main system dump-abi --artifact ... --official
    cli_cmd(["system", "dump-abi", "--artifact", task_coord_artifact, "--official"])

    # 46: show python -m dincli.main model-owner deploy task-auditor --network local --artifact ...
    task_auditor_artifact = os.path.join(HARDHAT_ARTIFACTS, "DINTaskAuditor.sol/DINTaskAuditor.json")
    cli_cmd(["model-owner", "deploy", "task-auditor", "--network", "local", "--artifact", task_auditor_artifact])

    # 48: show python -m dincli.main system dump-abi --artifact ... --official
    cli_cmd(["system", "dump-abi", "--artifact", task_auditor_artifact, "--official"])

    # 52: show python -m dincli.main model-owner deposit-reward-in-dintask-auditor --network local --amount 1000
    cli_cmd(["model-owner", "deposit-reward-in-dintask-auditor", "--network", "local", "--amount", "1000"])

    # 54: show python -m dincli.main system connect-wallet --account 0
    cli_cmd(["system", "connect-wallet", "--account", "0"])

    # 56: show python -m dincli.main dindao add-slasher --taskCoordinator --network local
    cli_cmd(["dindao", "add-slasher", "--taskCoordinator", "--network", "local"])

    # 58: show python -m dincli.main system connect-wallet --account 1
    cli_cmd(["system", "connect-wallet", "--account", "1"])

    # 60: show python -m dincli.main model-owner add-slasher --taskCoordinator --network local
    cli_cmd(["model-owner", "add-slasher", "--taskCoordinator", "--network", "local"])

    # 62: show python -m dincli.main system connect-wallet --account 0
    cli_cmd(["system", "connect-wallet", "--account", "0"])

    # 64: show python -m dincli.main dindao add-slasher --taskAuditor --network local
    cli_cmd(["dindao", "add-slasher", "--taskAuditor", "--network", "local"])

    # 67: show python -m dincli.main system connect-wallet --account 1
    cli_cmd(["system", "connect-wallet", "--account", "1"])

    # 69: show python -m dincli.main model-owner add-slasher --taskAuditor --network local
    cli_cmd(["model-owner", "add-slasher", "--taskAuditor", "--network", "local"])

    # 74: show python -m dincli.main system connect-wallet --account 1
    # Repeated connect-wallet --account 1, but harmless
    cli_cmd(["system", "connect-wallet", "--account", "1"])

    # 79: show python -m dincli.main model-owner model create-genesis --network local
    # Manual step from bash script:
    # mkdir -p /home/azureuser/projects/DINv1MVC/tasks/local/<address>
    # cp /home/azureuser/.cache/dincli/local/model_0/manifest.json ...

    # 1. Get Task Coordinator Address from .env
    # We need to read the .env file generated/updated by dincli
    env_file = os.path.join(PROJECT_ROOT, ".env")
    task_coord_address = None
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                if "LOCAL_DINTaskCoordinator_Contract_Address=" in line:
                    task_coord_address = line.split("=")[1].strip()
                    break
    
    if not task_coord_address:
        pytest.fail("Could not find LOCAL_DINTaskCoordinator_Contract_Address in .env")

    print(f"Found Task Coordinator Address: {task_coord_address}")

    # 2. Create directory
    # tasks/local/<address>
    tasks_dir = os.path.join(PROJECT_ROOT, "tasks", "local", task_coord_address)
    os.makedirs(tasks_dir, exist_ok=True)
    
    # 3. Copy manifest
    # Source: /home/azureuser/.cache/dincli/local/model_0/manifest.json
    source_manifest = "/home/azureuser/.cache/dincli/local/model_0/manifest.json"
    if not os.path.exists(source_manifest):
         pytest.fail(f"Source manifest not found at {source_manifest}")

    import shutil
    target_manifest = os.path.join(tasks_dir, "manifest.json")
    shutil.copy(source_manifest, target_manifest)
    print(f"Copied manifest to {target_manifest}")

    cli_cmd(["model-owner", "model", "create-genesis", "--network", "local"])

    # 88: show python -m dincli.main model-owner model submit-genesis --network local
    cli_cmd(["model-owner", "model", "submit-genesis", "--network", "local"])

    # 90: show python -m dincli.main task model-owner register --network local
    cli_cmd(["task", "model-owner", "register", "--network", "local"])

    # 92: show python -m dincli.main system connect-wallet --account 0
    cli_cmd(["system", "connect-wallet", "--account", "0"])

    # 94: show python -m dincli.main dindao registry total-models --network local
    cli_cmd(["dindao", "registry", "total-models", "--network", "local"])

    # 96: show python -m dincli.main task explore 0
    cli_cmd(["task", "explore", "0"])
