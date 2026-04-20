# Preface

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

Also each actor/stakeholder needs to have a wallet address to interact with the DIN Protocol. Before executing any command, the actor/stakeholder needs to connect their wallet to the DIN CLI.

```bash
dincli system connect-wallet --account <account_id>
```

> [!NOTE]
> More on wallet configuration can be found in the [DIN CLI Documentation](common.md).


In current DIN Protocol, the model owner needs to deploy a taskCoordinator contract and a taskAuditor contract specific to each model. 

# Workflow

## 1. Deploy TaskCoordinator - Model Owner

Model Owner deploys a taskCoordinator contract specific to each model.
```bash
dincli model-owner deploy task-coordinator --artifact "/home/azureuser/projects/devnet/hardhat/artifacts/contracts/DINTaskCoordinator.sol/DINTaskCoordinator.json"
```

dincli will store the taskCoordinator contract address in the .env file as `SEPOLIA_OP_DEVNET_DINTaskCoordinator_Contract_Address` in your local project directory which we call `root_dir`.

## 2. Deploy TaskAuditor - Model Owner

Model Owner deploys a taskAuditor contract specific to each model.
```bash
dincli model-owner deploy task-auditor --artifact "/home/azureuser/projects/devnet/hardhat/artifacts/contracts/DINTaskAuditor.sol/DINTaskAuditor.json"
```

dincli will store the taskAuditor contract address in the .env file as `SEPOLIA_OP_DEVNET_<task_coordinator_contract_address>_DINTaskAuditor_Contract_Address` in your local project directory which we call `root_dir`.

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

The model owner should upload and pin the model.py file to IPFS and get the IPFS CID of the model.py file. Model Owner should add the following entry in the manifest file where the `ipfs` is the IPFS CID of the model.py file and `stakeholders` is the list of stakeholders that will use this service.

```json
    "ModelArchitecture": {
        "type": "custom",
        "path": "services/model.py",
        "ipfs": "QmXvkKtoHHBAMGNCLEqsvt6mPJS7G7shHKj6U1HZ8Ha4Ly",
        "stakeholders": [
            "modelowner",
            "auditors",
            "aggregators",
            "clients"
        ]
    },
```

#### 6.1.2. `modelowner.py`

This service is used to define the functions that will be used by the model owner to interact with the DIN Protocol for this model. 


1. `getGenesisModelIpfs(base_path)`: This function is used to get the genesis model. It takes the base path as an argument and returns the IPFS CID of the genesis model. 
    > The model owner should upload and pin the modelowner.py file to IPFS and get the IPFS CID of the model.py file. Model Owner should add the following entry in the manifest file where the `ipfs` is the IPFS CID of the model.py file and `stakeholders` is the list of stakeholders that will use this service.

```json
    "getGenesisModelIpfs": {
        "type": "custom",
        "path": "services/modelowner.py",
        "ipfs": "QmWvssDTW1YpQjaVi6eZoMUuAUTxmKhkxKR1suJ4FNYWee",
        "stakeholders": [
            "modelowner"
        ]
    },
```

2. `getscoreforGM(gi, gmcid, base_path)`: This function is used to get the score for the global model. It takes the global iteration index, model CID, and base path as arguments and returns the score for the global model. 
    > The model owner should upload and pin the modelowner.py file to IPFS and get the IPFS CID of the model.py file. Model Owner should add the following entry in the manifest file where the `ipfs` is the IPFS CID of the model.py file and `stakeholders` is the list of stakeholders that will use this service.

```json
    "getscoreforGM": {
        "type": "custom",
        "path": "services/modelowner.py",
        "ipfs": "QmWvssDTW1YpQjaVi6eZoMUuAUTxmKhkxKR1suJ4FNYWee",
        "stakeholders": [
            "modelowner"
        ]
    },
```

3. `create_audit_testDataCIDs(batch_counts, gi, base_path, test_data_path)`: This function is used to create the audit test data CIDs. It takes the number of audit batches to create, global iteration index, base path, and test data path as arguments and returns the audit test data CIDs. The `testData_percentage_per_auditor_batch` is the percentage of test data that will be used for each auditor batch and is 5%. 
    > The model owner should upload and pin the modelowner.py file to IPFS and get the IPFS CID of the model.py file. Model Owner should add the following entry in the manifest file where the `ipfs` is the IPFS CID of the model.py file and `stakeholders` is the list of stakeholders that will use this service.

```json
    "create_audit_testDataCIDs": {
        "type": "custom",
        "path": "services/modelowner.py",
        "ipfs": "QmWvssDTW1YpQjaVi6eZoMUuAUTxmKhkxKR1suJ4FNYWee",
        "stakeholders": [
            "modelowner"
        ]
    },
```

#### 6.1.3. `client.py`

This service is used to define the functions that will be used by the clients to interact with the DIN Protocol for this model. 

1. `train_client_model_and_upload_to_ipfs(genesis_model_ipfs_hash, account_address, effective_network="local", initial_model_ipfs_hash=None, dp_mode="disabled", model_base_dir="", gi=None,)` is used to train the client model and upload it to IPFS. It takes the genesis model IPFS hash, account/client address, effective network, initial model IPFS hash, differential privacy mode, model base directory, and global iteration index as arguments and returns the client model IPFS hash.

Model Owner may/ or may not define the Differential Privacy (DP) logic for the model. If the model owner defines the DP logic for the model and set `dp_mode: "enabled"` in manifest file, then the client model will be trained with the DP mode using the DP logic defined in the client.py file. 

    > The model owner should upload and pin the client.py file to IPFS and get the IPFS CID of the client.py file. Model Owner should add the following entry in the manifest file where the `ipfs` is the IPFS CID of the client.py file and `stakeholders` is the list of stakeholders that will use this service.

```json
    "train_client_model_and_upload_to_ipfs": {
        "type": "custom",
        "path": "services/client.py",
        "ipfs": "QmWvssDTW1YpQjaVi6eZoMUuAUTxmKhkxKR1suJ4FNYWee",
        "stakeholders": [
            "clients"
        ]
    },
```


#### 6.1.4. `auditor.py`

This service is used to define the functions that will be used by the auditors to interact with the DIN Protocol for this model. 

1. `Score_model_by_auditor(gi, genesis_model_cid, batch_id, model_index, auditor_address, testDataCID, lm_cid, model_base_dir)` is used to score the model by the auditor. It takes the global iteration index, genesis model IPFS hash, batch index, model index, auditor address, test data CID, local model IPFS hash, and model base directory as arguments and returns the score and eligibility for the local model.
    > The model owner should upload and pin the auditor.py file to IPFS and get the IPFS CID of the auditor.py file. Model Owner should add the following entry in the manifest file where the `ipfs` is the IPFS CID of the auditor.py file and `stakeholders` is the list of stakeholders that will use this service.

```json
    "Score_model_by_auditor": {
        "type": "custom",
        "path": "services/auditor.py",
        "ipfs": "QmWvssDTW1YpQjaVi6eZoMUuAUTxmKhkxKR1suJ4FNYWee",
        "stakeholders": [
            "auditors"
        ]
    },
```

#### 6.1.5. `aggregator.py`

This service is used to define the functions that will be used by the aggregators to interact with the DIN Protocol for this model. 

1. `get_aggregated_cid_t1(curr_GI, aggregator_address, model_cids, genesis_model_ipfs_hash, bid, model_base_dir)` is used to aggregate the local models in T1 aggregation batch by the aggregator. It takes the global iteration index, aggregator address, local model cids, genesis model IPFS hash, batch index, and model base directory as arguments and returns the aggregated model IPFS hash.
    > The model owner should upload and pin the aggregator.py file to IPFS and get the IPFS CID of the aggregator.py file. Model Owner should add the following entry in the manifest file where the `ipfs` is the IPFS CID of the aggregator.py file and `stakeholders` is the list of stakeholders that will use this service.

```json
    "get_aggregated_cid_t1": {
        "type": "custom",
        "path": "services/aggregator.py",
        "ipfs": "QmWvssDTW1YpQjaVi6eZoMUuAUTxmKhkxKR1suJ4FNYWee",
        "stakeholders": [
            "aggregators"
        ]
    },
```

2. `get_aggregated_cid_t2(curr_GI, aggregator_address, model_cids, genesis_model_ipfs_hash, bid, model_base_dir)` is used to aggregate the local models in T2 aggregation batch by the aggregator. It takes the global iteration index, aggregator address, local model cids, genesis model IPFS hash, batch index, and model base directory as arguments and returns the aggregated model IPFS hash.
    > The model owner should upload and pin the aggregator.py file to IPFS and get the IPFS CID of the aggregator.py file. Model Owner should add the following entry in the manifest file where the `ipfs` is the IPFS CID of the aggregator.py file and `stakeholders` is the list of stakeholders that will use this service.

```json
    "get_aggregated_cid_t2": {
        "type": "custom",
        "path": "services/aggregator.py",
        "ipfs": "QmWvssDTW1YpQjaVi6eZoMUuAUTxmKhkxKR1suJ4FNYWee",
        "stakeholders": [
            "aggregators"
        ]
    },
```


### 6.2. Create manifest file

Model Owner creates a manifest file for the model. In addition to above entries as per 6.1, the model owner should define following meta-data in manifest.json file

1. `name` : name of the model
2. `version`: version of the model
3. `description`
4. `author`
5. `license`
6. `model_type`: open source or proprietary
7. `technical details`: technical details of the model
8. `Genesis_Model_CID`: IPFS CID of the genesis model
dp_mode
DINTaskCoordinator_Contract
DINTaskAuditor_Contract


In addition to above entries, the model owner can define any custom fields in manifest.json file as per their requirements. The custom fields/parmeters can be used in services by accessing them via `get_manifest_key` function. The manifest and parameters can be updated as the model training progresses.
Model Owner should place the manifest.json file at `<root_dir>/tasks/sepolia_op_devnet/<task_coordinator_contract_address>/manifest.json`.

The model Owner can setup Markkdown guides specific to their model for clients, aggregators, auditors and other stakeholders in manifest.json file as `guides` field. (Example: `"guides": { "clients": "<client_guide_ipfs_hash>", "aggregators": "<aggregator_guide_ipfs_hash>", "auditors": "<auditor_guide_ipfs_hash>" }`)  
## 7. Create and Submit Genesis Model - Model Owner

Model Owner creates and submits the genesis model to the TaskCoordinator contract. 

The following dincli command is used to create the genesis model:

```bash
dincli model-owner model create-genesis
```

> make sure that the manifest.json file is present at `<root_dir>/tasks/sepolia_op_devnet/<task_coordinator_contract_address>/manifest.json` before running the above command. The above dincli command will use `getGenesisModelIpfs` in `modelowner.py` service  to create the genesis model and upload it to IPFS and store the IPFS CID in the .env file as `SEPOLIA_OP_DEVNET_<TASK_COORDINATOR_CONTRACT_ADDRESS>_GENESIS_MODEL_IPFS_HASH`. Please note that dincli can automatically fetch the service from IPFS using the coressponding entry for `getGenesisModelIpfs` in the manifest.json file.

The model owner can submit the genesis model to the TaskCoordinator contract using the following dincli command:

```bash
dincli model-owner model submit-genesis
```

> make sure that the appropriate test dataset for the model is available at `<root_dir>/tasks/sepolia_op_devnet/<task_coordinator_contract_address>/dataset/test/test_dataset.pt` before running the above command. These test data will be used to evaluate the genesis model and calculate the score. This score will set the threshold range for the final eligibility of local models.

## 8. Register Model - Model Owner

Model Owner updates the manisfest file at`<root_dir>/tasks/sepolia_op_devnet/<task_coordinator_contract_address>/manifest.json`, specially the `Genesis_Model_CID`, `DINTaskCoordinator_Contract`, and `DINTaskAuditor_Contract`  fields with the IPFS CID of the genesis model, DINTaskCoordinator contract address and DINTaskAuditor contract address respectively.

Model Owner then register the model with the DIN Protocolat DINModelRegistry contract using the following dincli command:

```bash
dincli task model-owner register --isOpenSource [true/false]
```

Once the model is registered, the model is assigned a model ID. The manifest file may be updated with the model id field `Model ID` and uploaded to IPFS again. Other fields in manifest file can also be updated as per requirement. The following dincli command can be used to update the model CID in DINModelRegistry contract:

```bash
dincli task model-owner update-manifest <model_id> [--modelCID <model_cid>] [--manifestpath <manifest_path>]
```

## 9. Start Global Iteration (GI) - Model Owner

After the model is registered, the Model Owner can initiate the Federated Learning process. The FL process is organized into Global Iterations (GI) where aggregators, auditors, and clients interact with the protocol.

The Model Owner starts a new Global Iteration for the specific model.

```bash
dincli model-owner gi start <model_id>
```

---

## 10. Aggregator Registration - Model Owner & Aggregators

The Model Owner opens aggregator registration. Then, aggregators buy and stake DIN tokens before registering. Once all aggregators have registered, the Model Owner closes the registration.



**Model Owner** opens aggregator registration:

```bash
dincli model-owner gi reg aggregators-open <model_id>
```

**Aggregators** buy tokens, stake, and register (repeat for each aggregator):

```bash
# buy DIN tokens
dincli aggregator dintoken buy 0.00001
# stake DIN tokens
dincli aggregator dintoken stake 10
# read stake
dincli aggregator dintoken read-stake
# register aggregator in current GI
dincli aggregator register <model_id>
```

**Model Owner** reviews and closes aggregator registration:

```bash
# show registered aggregators in current GI
dincli model-owner gi show-registered-aggregators <model_id>
# close aggregator registration
dincli model-owner gi reg aggregators-close <model_id>
```

---

## 11. Auditor Registration - Model Owner & Auditors

Similar to aggregators, the Model Owner opens auditor registration. Auditors stake tokens and register, after which the Model Owner closes registration.

**Model Owner** opens auditor registration:

```bash
dincli model-owner gi reg auditors-open <model_id>
```

**Auditors** buy tokens, stake, and register (repeat for each auditor):

```bash
# buy DIN tokens
dincli auditor dintoken buy 0.00001
# stake DIN tokens
dincli auditor dintoken stake 10
# read stake
dincli auditor dintoken read-stake
# register auditor in current GI
dincli auditor register <model_id>
```

**Model Owner** reviews and closes auditor registration:

```bash
# show registered auditors in current GI
dincli model-owner gi show-registered-auditors <model_id>
# close auditor registration
dincli model-owner gi reg auditors-close <model_id>
```

---

## 12. Local Model Submission (LMS) - Model Owner & Clients

The Model Owner opens the LMS phase allowing clients to download the genesis/global model, train on their local datasets, and submit their local models.

**Model Owner** opens LMS:

```bash
dincli model-owner lms open <model_id>
```

**Clients** train and submit their local models (repeat for each client):

```bash
# train and submit local model
dincli client train-lms <model_id> --submit
# show submitted local model
dincli client lms show-models <model_id>
```

> [!IMPORTANT]
> The client local training data must be  located at `<CACHE_DIR>/sepolia_op_devnet/model_<model_id>/dataset/clients/<account_address>/data.pt`
> where `CACHE_DIR` is the path to the cache directory of the dincli.
> and can be found by running the command `dincli system cache-dir`.

**Model Owner** reviews submissions and closes LMS:

```bash
# show submitted local models by clients
dincli model-owner lms show-models <model_id>
# close LMS
dincli model-owner lms close <model_id>
```

---

## 13. Auditor Evaluation - Model Owner & Auditors

The Model Owner prepares evaluation batches and test data, then auditors evaluate the submitted local models to determine their quality and assign scores.

**Model Owner** prepares evaluation batches and starts evaluation:

```bash
# create evaluation batches
dincli model-owner auditor-batches create <model_id>
# show evaluation batches
dincli model-owner auditor-batches show <model_id>
# create test dataset
dincli model-owner auditor-batches create-testdataset <model_id> --submit
# start evaluation
dincli model-owner lms-evaluation start <model_id>
# show evaluation results
dincli model-owner lms-evaluation show <model_id> --auditors --models
```

> [NOTE]
> The test dataset maybe located at `<CACHE_DIR>/sepolia_op_devnet/model_<model_id>/dataset/test/test_dataset.pt`
> where `CACHE_DIR` is the path to the cache directory of the dincli.
> and can be found by running the command `dincli system cache-dir`.

**Auditors** evaluate their assigned batches (repeat for each auditor):

```bash
# show the auditor its assigned auditor batches
dincli auditor lms-evaluation show-batch <model_id>
# evaluate the assigned auditor batches, automatically evalates all lms in assigned batch
dincli auditor lms-evaluation evaluate <model_id> --submit
```

**Model Owner** reviews and closes evaluation:

```bash
# show evaluation results from all auditors
dincli model-owner lms-evaluation show <model_id> --models
# close evaluation
dincli model-owner lms-evaluation close <model_id>
```

---

## 14. Model Aggregation (T1 and T2) - Model Owner & Aggregators

Eligible local models are aggregated hierarchically. Tier 1 (T1) aggregation combines sub-batches, and Tier 2 (T2) aggregation combines the results of T1 into the new global model.

**Model Owner** generates T1 & T2 batches and starts T1 aggregation:

```bash
# create t1 and t2 batches
dincli model-owner aggregation create-t1nt2-batches <model_id>
# show t1 and t2 batches
dincli model-owner aggregation show-t1-batches <model_id> --detailed
dincli model-owner aggregation show-t2-batches <model_id> --detailed
# start t1 aggregation
dincli model-owner aggregation T1 start <model_id>
```

**Aggregators** perform T1 aggregation (repeat for each aggregator):

```bash
# show the aggregator its assigned t1 batches
dincli aggregator show-t1-batches <model_id> --detailed
# aggregate the assigned t1 batches
dincli aggregator aggregate-t1 <model_id> --submit
```

**Model Owner** closes T1 and starts T2 aggregation:

```bash
# show t1 batches
dincli model-owner aggregation show-t1-batches <model_id> --detailed
# close t1 aggregation
dincli model-owner aggregation T1 close <model_id>
# start t2 aggregation
dincli model-owner aggregation T2 start <model_id>
# show t2 batches
dincli model-owner aggregation show-t2-batches <model_id> --detailed
```

**Aggregators** perform T2 aggregation (repeat for each aggregator):

```bash
# show the aggregator its assigned t2 batches
dincli aggregator show-t2-batches <model_id> --detailed
# aggregate the assigned t2 batches
dincli aggregator aggregate-t2 <model_id> --submit
```

**Model Owner** closes T2 aggregation:

```bash
# show t2 batches
dincli model-owner aggregation show-t2-batches <model_id> --detailed
# close t2 aggregation
dincli model-owner aggregation T2 close <model_id>
```

---

## 15. Slashing & End Global Iteration - Model Owner

Any malicious or non-performing actors (auditors or aggregators) are penalized, and the Global Iteration is finalized.

```bash
# show current state
dincli model-owner gi show-state <model_id>
# slash auditors
dincli model-owner slash auditors <model_id>
# slash aggregators
dincli model-owner slash aggregators <model_id>
# end global iteration
dincli model-owner gi end <model_id>
```