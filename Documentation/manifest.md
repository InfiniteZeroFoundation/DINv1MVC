# Manifest

The manifest is a JSON file containing the metadata for your model and task. It serves as the central configuration that ties together the model, its services, and contract addresses.

## Location

The manifest file must be placed at:

```
<root_dir>/tasks/<network>/task_<coordinator_address>/manifest.json
```

For example:
```
<root_dir>/tasks/sepolia_op_devnet/task_0x1e31...4b133/manifest.json
```

> [!NOTE]
> If the manifest file is absent when the genesis setup (`dincli task model-owner create-genesis`) runs, it is automatically created with default values from the default manifest CID (`QmQaPUfVAyQBrkRvHZWyH8tbNukmcgEmghYFGZA6LKo8tp`).

---

## Manifest Fields

### Metadata Fields

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Name of the model |
| `version` | Yes | Version of the model |
| `description` | No | Description of the model |
| `author` | No | Author of the model |
| `technical details` | No | Technical details of the model |

### Contract & Model Fields

| Field | Required | Description |
|---|---|---|
| `Genesis_Model_CID` | Yes | IPFS CID of the genesis model. Set after running `dincli model-owner model create-genesis` |
| `DINTaskCoordinator_Contract` | Yes | Address of the deployed TaskCoordinator contract |
| `DINTaskAuditor_Contract` | Yes | Address of the deployed TaskAuditor contract |
| `dp_mode` | No | Differential Privacy mode: `"disabled"` or `"enabled"` (default: `"disabled"`) |

### Service Entries

Each service function is registered in the manifest as a JSON object with the following structure:

```json
"<function_name>": {
    "type": "custom",
    "path": "services/<service_file>.py",
    "ipfs": "<IPFS_CID_OF_SERVICE_FILE>",
    "stakeholders": ["<role1>", "<role2>"]
}
```

| Key | Description |
|---|---|
| `type` | Service type (currently `"custom"`) |
| `path` | Local relative path to the service file |
| `ipfs` | IPFS CID of the uploaded and pinned service file |
| `stakeholders` | List of roles that use this service (e.g., `"modelowner"`, `"clients"`, `"auditors"`, `"aggregators"`) |

For detailed documentation on each service file and the functions that must be implemented, see [services.md](services.md).

### Guides Field (Optional)

The Model Owner can set up Markdown guides specific to their model for clients, aggregators, auditors and other stakeholders:

```json
"guides": {
    "clients": "<client_guide_ipfs_hash>",
    "aggregators": "<aggregator_guide_ipfs_hash>",
    "auditors": "<auditor_guide_ipfs_hash>"
}
```

### Custom Fields

The model owner can define any custom fields in the manifest file as per their requirements. Custom fields/parameters can be accessed in services via the `get_manifest_key` function. The manifest and parameters can be updated as the model training progresses.

---

## Example Manifest

```json
{
    "name": "mnist-digits",
    "version": "1.0.0",
    "description": "MNIST model to detect digits",
    "author": "Umer Majeed (infinite Zero)",
    "technical details": "",
    "Genesis_Model_CID": "QmWetTBYPwgCJLJ9RbjHnubPVeHgApax8fNW1z1uUcrgoy",
    "DINTaskCoordinator_Contract": "0x1e315573CE1b0A7c0De6d55f5A4858c98454b133",
    "DINTaskAuditor_Contract": "0x31D9FB450A313BDAe3aC0e512bCDfEab7297851a",
    "dp_mode": "disabled",
    "getGenesisModelIpfs": {
        "type": "custom",
        "path": "services/modelowner.py",
        "ipfs": "QmWvssDTW1YpQjaVi6eZoMUuAUTxmKhkxKR1suJ4FNYWee",
        "stakeholders": ["modelowner"]
    },
    "getscoreforGM": {
        "type": "custom",
        "path": "services/modelowner.py",
        "ipfs": "QmWvssDTW1YpQjaVi6eZoMUuAUTxmKhkxKR1suJ4FNYWee",
        "stakeholders": ["modelowner"]
    },
    "ModelArchitecture": {
        "type": "custom",
        "path": "services/model.py",
        "ipfs": "QmXvkKtoHHBAMGNCLEqsvt6mPJS7G7shHKj6U1HZ8Ha4Ly",
        "stakeholders": ["modelowner", "auditors", "aggregators", "clients"]
    },
    "train_client_model_and_upload_to_ipfs": {
        "type": "custom",
        "path": "services/client.py",
        "ipfs": "QmUcoG7w4CK8ZpcSNQnPV9ZUi9XmZo3CCK3CPrWReQcaTS",
        "stakeholders": ["clients"]
    },
    "create_audit_testDataCIDs": {
        "type": "custom",
        "path": "services/modelowner.py",
        "ipfs": "QmWvssDTW1YpQjaVi6eZoMUuAUTxmKhkxKR1suJ4FNYWee",
        "stakeholders": ["modelowner"]
    },
    "Score_model_by_auditor": {
        "type": "custom",
        "path": "services/auditor.py",
        "ipfs": "QmbKu52v5Dkg9yi28BwTe5mfXRwaF1Dju9i5oikfNn2HAu",
        "stakeholders": ["auditors"]
    },
    "get_aggregated_cid_t1": {
        "type": "custom",
        "path": "services/aggregator.py",
        "ipfs": "QmP8Xhee2MT5gouPMohnR63xadyKEvnLsaKbqk7ZvoWrBZ",
        "stakeholders": ["aggregators"]
    },
    "get_aggregated_cid_t2": {
        "type": "custom",
        "path": "services/aggregator.py",
        "ipfs": "QmP8Xhee2MT5gouPMohnR63xadyKEvnLsaKbqk7ZvoWrBZ",
        "stakeholders": ["aggregators"]
    }
}
```

---

## Updating the Manifest

Once the model is registered and assigned a model ID, the manifest file should be updated with the `Model ID` field and re-uploaded to IPFS. The following dincli command can be used to update the model CID in the DINModelRegistry contract:

```bash
dincli task model-owner update-manifest <model_id> [--modelCID <model_cid>] [--manifestpath <manifest_path>]
```
