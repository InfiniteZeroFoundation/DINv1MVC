In this guide we will describe the workflow of the DIN Protocol for a model.

In Model Workflow there are 5 main entities:

1. Model-Owner
2. DIN-Representative (later DIN-DAO)
3. Auditors
4. Aggregators
5. Clients (Model-Trainees)

The DIN devnet is deployed on the Optimism Sepolia testnet with code name `SEPOLIA_OP_DEVNET` 

so all entities must configure their dincli to use this network as 

```bash
dincli system configure-network --network "sepolia_op_devnet"
```

In current DIN Protocol, the model owner needs to deploy a taskCoordinator contract and a taskAuditor contract specific to each model. 

# Workflow

## 1. Deploy TaskCoordinator - Model Owner

Model Owner deploys a taskCoordinator contract specific to each model.
```bash
dincli system connect-wallet --account 1
dincli model-owner deploy task-coordinator --artifact "/home/azureuser/projects/devnet/hardhat/artifacts/contracts/DINTaskCoordinator.sol/DINTaskCoordinator.json"
```

dincli will store the taskCoordinator contract address in the .env file as `SEPOLIA_OP_DEVNET_DINTaskCoordinator_Contract_Address` in your local project directory.

## 2. Deploy TaskAuditor - Model Owner

Model Owner deploys a taskAuditor contract specific to each model.
```bash
dincli system connect-wallet --account 1
dincli model-owner deploy task-auditor --artifact "/home/azureuser/projects/devnet/hardhat/artifacts/contracts/DINTaskAuditor.sol/DINTaskAuditor.json"
```

dincli will store the taskAuditor contract address in the .env file as `SEPOLIA_OP_DEVNET_<task_coordinator_contract_address>_DINTaskAuditor_Contract_Address` in your local project directory.

## 3. Request Slasher Authorization - Model Owner

Before a model can be registered with `DINModelRegistry`, both its `TaskCoordinator` and `TaskAuditor` contracts must be authorized as **slashers** on the `DINValidatorStake` contract. The model owner must request this authorization from the **DIN-Representative** off-chain.

> [!IMPORTANT]
> Your model **cannot** be registered with `DINModelRegistry` until your `TaskCoordinator` (and `TaskAuditor`) contracts are whitelisted as authorized slashers. Complete this step **before** attempting model registration — the registry contract will revert if the contracts are not yet authorized.

### Official Contact Channels

Reach out to the DIN-Representative through any of the following channels:

| Channel  | Link / Handle |
|----------|--------------|
| Discord  | `#model-onboarding` channel on the DIN Discord server |
| Telegram | [@DINProtocol](https://t.me/DINProtocol) |
| Email    | devnet@dinprotocol.io |

### Required Information for Your Request

Please include all of the following in your message so the DIN-Representative can review and process your request efficiently:

1. **TaskCoordinator contract address** — deployed in Step 1.
2. **TaskAuditor contract address** — deployed in Step 2.
3. **Network / Chain ID** — e.g., `Optimism Sepolia (chainId: 11155420)`.
4. **Deployment transaction hashes** — for both contracts (used for independent on-chain verification).
5. **Model description** — model type, intended use-case, and whether it is open-source or proprietary.
6. **Model-owner wallet address** — the account used for deployment.

> [!NOTE]
> The DIN-Representative will verify that:
> - Both contracts were deployed by the stated model-owner address.
> - The `TaskCoordinator` implements the `IDINTaskCoordinator` interface and references the correct `DINValidatorStake` contract.
> - The `TaskAuditor` is correctly linked to the `TaskCoordinator`.
> - No malicious or unauthorized slashing logic is embedded in the contracts.
>
> Review typically takes **1–3 business days**. You will be notified through the same channel you used to submit your request.

> [!WARNING]
> Do **not** attempt to call `addSlasher` directly — only the DIN-Representative wallet is permitted to invoke this function through `DinCoordinator`. Unauthorized calls will revert on-chain.

---

## 4. Authorize Contracts as Slashers - DIN-Representative

Once the DIN-Representative reviews and approves the request, they execute the following on-chain to register both contracts as authorized slashers:

```bash
# Switch to DIN-Representative account (account 0)
dincli system connect-wallet --account 0

# Register TaskCoordinator as an authorized slasher
dincli dindao add-slasher --contract <TASK_COORDINATOR_ADDRESS>

# Register TaskAuditor as an authorized slasher
dincli dindao add-slasher --contract <TASK_AUDITOR_ADDRESS>
```

> [!NOTE]
> After this step, both contracts are recognized by `DINValidatorStake` as authorized slashers. Validators (auditors / aggregators) who violate protocol rules can now be slashed by these contracts.

Once complete, the DIN-Representative will notify the model-owner through the same channel used to submit the request.

---

## 5. Confirm Slasher Authorization - Model Owner

Once the DIN-Representative confirms the slasher authorization for both taskCoordinator and taskAuditor contracts, Model Owner confirms the slasher authorization on their end by calling the add-slasher function on both contracts.

```bash
dincli system connect-wallet --account 1

dincli model-owner add-slasher --taskCoordinator 

dincli model-owner add-slasher --taskAuditor 
```

> [!IMPORTANT]
> Please, note that the addresses of the taskCoordinator and taskAuditor contracts must be stored in the .env file as `SEPOLIA_OP_DEVNET_DINTaskCoordinator_Contract_Address` and `SEPOLIA_OP_DEVNET_<task_coordinator_contract_address>_DINTaskAuditor_Contract_Address` respectively. 

After this step, model owner can proceed to the next step in the model workflow.

## 6. Create manifest - Model Owner

Model Owner creates a manifest file for the model. Creating a manifest file involves some steps.


### 6.1. Create services - Model Owner

Model Owner creates services for the model. These services are python scripts that will be used by different actors/stakeholders in the DIN Protocol. DIN Protocol provides a template for each service. 

> [!NOTE]
> The Model Owner can use the templates provided by the DIN Protocol to create the services. It is upto the model owner to define the actual logic of the services but certain functions must be implemented as per the DIN Protocol specifications. The DIN-Protocol team can help Model Owner to create the custom services. Model Onwer can use torch/tensorflow/keras or any other framework to create the model and related services.


1. `model.py` to define model architecture
2. `modelowner.py` for model owner
3. `client.py` for clients
4. `auditor.py` for auditors
5. `aggregator.py` for aggregators

#### 6.1.1. `model.py`

This service is to define the model architecture. 
`ModelArchitecture` class should be defined to define the model architecture where `__init__` and `forward` methods are implemented. 

#### 6.1.2. `modelowner.py`

This service is used to define the functions that will be used by the model owner to interact with the DIN Protocol for this model. 


1. `getGenesisModelIpfs(base_path)`: This function is used to get the genesis model. It takes the base path as an argument and returns the IPFS CID of the genesis model. 
2. `getscoreforGM(gi, gmcid, base_path)`: This function is used to get the score for the global model. It takes the global iteration index, model CID, and base path as arguments and returns the score for the global model. 
3. `create_audit_testDataCIDs(batch_counts, gi, base_path, test_data_path)`: This function is used to create the audit test data CIDs. It takes the number of audit batches to create, global iteration index, base path, and test data path as arguments and returns the audit test data CIDs. The `testData_percentage_per_auditor_batch` is the percentage of test data that will be used for each auditor batch and is 5%. 

#### 6.1.3. `client.py`

This service is used to define the functions that will be used by the clients to interact with the DIN Protocol for this model. 

1. `train_client_model_and_upload_to_ipfs(genesis_model_ipfs_hash, account_address, effective_network="local", initial_model_ipfs_hash=None, dp_mode="disabled", model_base_dir="", gi=None,)` is used to train the client model and upload it to IPFS. It takes the genesis model IPFS hash, account/client address, effective network, initial model IPFS hash, differential privacy mode, model base directory, and global iteration index as arguments and returns the client model IPFS hash.

Model Owner may/ or may not define the Differential Privacy (DP) logic for the model. If the model owner defines the DP logic for the model and set `dp_mode: "enabled"` in manifest file, then the client model will be trained with the DP mode using the DP logic defined in the client.py file. 


#### 6.1.4. `auditor.py`

This service is used to define the functions that will be used by the auditors to interact with the DIN Protocol for this model. 

1. `Score_model_by_auditor(gi, genesis_model_cid, batch_id, model_index, auditor_address, testDataCID, lm_cid, model_base_dir)` is used to score the model by the auditor. It takes the global iteration index, genesis model IPFS hash, batch index, model index, auditor address, test data CID, local model IPFS hash, and model base directory as arguments and returns the score and eligibility for the local model.

#### 6.1.5. `aggregator.py`

This service is used to define the functions that will be used by the aggregators to interact with the DIN Protocol for this model. 

1. `get_aggregated_cid_t1(curr_GI, aggregator_address, model_cids, genesis_model_ipfs_hash, bid, model_base_dir)` is used to aggregate the local models in T1 aggregation batch by the aggregator. It takes the global iteration index, aggregator address, local model cids, genesis model IPFS hash, batch index, and model base directory as arguments and returns the aggregated model IPFS hash.

2. `get_aggregated_cid_t2(curr_GI, aggregator_address, model_cids, genesis_model_ipfs_hash, bid, model_base_dir)` is used to aggregate the local models in T2 aggregation batch by the aggregator. It takes the global iteration index, aggregator address, local model cids, genesis model IPFS hash, batch index, and model base directory as arguments and returns the aggregated model IPFS hash.


## 7. Use Model - Model Owner

Model Owner uses the trained model for commercial purposes.

## 7. Update Model - Model Owner

Model Owner updates the trained model with the DIN Protocol.

## 8. Delete Model - Model Owner

Model Owner deletes the trained model from the DIN Protocol.

## 9. Register Model - Model Owner

Model Owner registers the model with the DIN ModelRegistry contract.

## 10. Train Model - Model Owner

Model Owner trains the model using DIN Protocol.

## 11. Deploy Model - Model Owner

Model Owner deploys the trained model to the DIN Protocol.

## 12. Use Model - Model Owner

Model Owner uses the trained model for commercial purposes.

## 13. Update Model - Model Owner

Model Owner updates the trained model with the DIN Protocol.

## 14. Delete Model - Model Owner

Model Owner deletes the trained model from the DIN Protocol.

## 15. Register Model - Model Owner

Model Owner registers the model with the DIN ModelRegistry contract.

## 16. Train Model - Model Owner

Model Owner trains the model using DIN Protocol.

## 17. Deploy Model - Model Owner

Model Owner deploys the trained model to the DIN Protocol.

## 18. Use Model - Model Owner

Model Owner uses the trained model for commercial purposes.

## 19. Update Model - Model Owner

Model Owner updates the trained model with the DIN Protocol.

## 20. Delete Model - Model Owner

Model Owner deletes the trained model from the DIN Protocol.

## 21. Register Model - Model Owner

Model Owner registers the model with the DIN ModelRegistry contract.

## 22. Train Model - Model Owner

Model Owner trains the model using DIN Protocol.

## 23. Deploy Model - Model Owner

Model Owner deploys the trained model to the DIN Protocol.

## 24. Use Model - Model Owner

Model Owner uses the trained model for commercial purposes.

## 25. Update Model - Model Owner

Model Owner updates the trained model with the DIN Protocol.

## 26. Delete Model - Model Owner

Model Owner deletes the trained model from the DIN Protocol.

## 27. Register Model - Model Owner

Model Owner registers the model with the DIN ModelRegistry contract.

## 28. Train Model - Model Owner

Model Owner trains the model using DIN Protocol.

## 29. Deploy Model - Model Owner

Model Owner deploys the trained model to the DIN Protocol.

## 30. Use Model - Model Owner

Model Owner uses the trained model for commercial purposes.

## 31. Update Model - Model Owner

Model Owner updates the trained model with the DIN Protocol.

## 32. Delete Model - Model Owner

Model Owner deletes the trained model from the DIN Protocol.

## 33. Register Model - Model Owner

Model Owner registers the model with the DIN ModelRegistry contract.

## 34. Train Model - Model Owner

Model Owner trains the model using DIN Protocol.

## 35. Deploy Model - Model Owner

Model Owner deploys the trained model to the DIN Protocol.

## 36. Use Model - Model Owner

Model Owner uses the trained model for commercial purposes.

## 37. Update Model - Model Owner

Model Owner updates the trained model with the DIN Protocol.

## 38. Delete Model - Model Owner

Model Owner deletes the trained model from the DIN Protocol.

## 39. Register Model - Model Owner

Model Owner registers the model with the DIN ModelRegistry contract.

## 40. Train Model - Model Owner

Model Owner trains the model using DIN Protocol.

## 41. Deploy Model - Model Owner

Model Owner deploys the trained model to the DIN Protocol.

## 42. Use Model - Model Owner

Model Owner uses the trained model for commercial purposes.

## 43. Update Model - Model Owner

Model Owner updates the trained model with the DIN Protocol.

## 44. Delete Model - Model Owner

Model Owner deletes the trained model from the DIN Protocol.

## 45. Register Model - Model Owner

Model Owner registers the model with the DIN ModelRegistry contract.

## 46. Train Model - Model Owner

Model Owner trains the model using DIN Protocol.

## 47. Deploy Model - Model Owner

Model Owner deploys the trained model to the DIN Protocol.

## 48. Use Model - Model Owner

Model Owner uses the trained model for commercial purposes.

## 49. Update Model - Model Owner

Model Owner updates the trained model with the DIN Protocol.

## 50. Delete Model - Model Owner

Model Owner deletes the trained model from the DIN Protocol.

## 51. Register Model - Model Owner

Model Owner registers the model with the DIN ModelRegistry contract.

## 52. Train Model - Model Owner

Model Owner trains the model using DIN Protocol.

## 53. Deploy Model - Model Owner

Model Owner deploys the trained model to the DIN Protocol.

## 54. Use Model - Model Owner

Model Owner uses the trained model for commercial purposes.

## 55. Update Model - Model Owner

Model Owner updates the trained model with the DIN Protocol.

## 56. Delete Model - Model Owner

Model Owner deletes the trained model from the DIN Protocol.

## 57. Register Model - Model Owner

Model Owner registers the model with the DIN ModelRegistry contract.

## 58. Train Model - Model Owner

Model Owner trains the model using DIN Protocol.

## 59. Deploy Model - Model Owner

Model Owner deploys the trained model to the DIN Protocol.

## 60. Use Model - Model Owner

Model Owner uses the trained model for commercial purposes.

## 61. Update Model - Model Owner

Model Owner updates the trained model with the DIN Protocol.

## 62. Delete Model - Model Owner

Model Owner deletes the trained model from the DIN Protocol.

## 63. Register Model - Model Owner

Model Owner registers the model with the DIN ModelRegistry contract.

## 64. Train Model - Model Owner

Model Owner trains the model using DIN Protocol.

## 65. Deploy Model - Model Owner

Model Owner deploys the trained model to the DIN Protocol.

## 66. Use Model - Model Owner

Model Owner uses the trained model for commercial purposes.

## 67. Update Model - Model Owner

Model Owner updates the trained model with the DIN Protocol.

## 68. Delete Model - Model Owner

Model Owner deletes the trained model from the DIN Protocol.

## 69. Register Model - Model Owner

Model Owner registers the model with the DIN ModelRegistry contract.

## 70. Train Model - Model Owner

Model Owner trains the model using DIN Protocol.

## 71. Deploy Model - Model Owner

Model Owner deploys the trained model to the DIN Protocol.

## 72. Use Model - Model Owner

Model Owner uses the trained model for commercial purposes.

## 73. Update Model