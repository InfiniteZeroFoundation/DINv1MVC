from web3 import Web3
from dotenv import dotenv_values
import os
from services.blockchain_services import get_w3
import torch
from services.ipfs_service import upload_to_ipfs, retrieve_from_ipfs
from torch.utils.data import DataLoader

RPC_URL = os.getenv("RPC_URL")           # e.g. "http://127.0.0.1:8545"

def get_auditor_batches(gi, DinTaskAuditingC_address):
    w3 = get_w3()
    
    DinTaskAuditingC = w3.eth.contract(address=DinTaskAuditingC_address, abi=DinTaskAuditing_abi)
    
    return DinTaskAuditingC.functions.auditBatches(gi).call()

def create_audit_testDataCIDs(gi, DinTaskAuditingC_address):
    auditor_batches = get_auditor_batches(gi, DinTaskAuditingC_address)
    
    num_batches = len(auditor_batches)
    
    test_data = torch.load(f"./Dataset/test/test_dataset.pt", weights_only=False)
    
    total_test_samples = len(test_data)
    
    testData_percentage_per_auditor_batch = 5
    
    # Number of samples each batch gets
    samples_per_batch = int(total_test_samples * (testData_percentage_per_auditor_batch / 100))
    
    assigned_audit_testDataCIDs = {}
    
    
    for i, e_batch_id in enumerate(auditor_batches):
        
        
        batch_id = auditor_batches[i].batch_id
        # Generate random indices
        random_indices = torch.randperm(total_samples)[:num_samples]
        
        # Create shuffled subset
        assigned_testData = torch.utils.data.Subset(test_data, random_indices)
        
        os.makedirs(f"./Dataset/auditor", exist_ok=True)
        
        torch.save(assigned_testData, f"./Dataset/auditor/auditorDataset_{gi}_{batch_id}.pt")
        
        ipfs_hash = upload_to_ipfs(f"./Dataset/auditor/auditorDataset_{gi}_{batch_id}.pt", f"Auditor Dataset for gi_{gi} batch {batch_id} uploaded")
        
        assigned_audit_testDataCIDs[auditor_batches[i].batch_id] = ipfs_hash
        
    w3 = get_w3()
    
    DinTaskAuditingC = w3.eth.contract(address=DinTaskAuditingC_address, abi=DinTaskAuditing_abi)
        
    for batch_id, ipfs_hash in assigned_audit_testDataCIDs.items():
        
        tx = DinTaskAuditingC.connect().functions.assignAuditTestDataset(gi, batch_id, ipfs_hash).transact()
        
        receipt = w3.eth.wait_for_transaction_receipt(tx)
        
        
def getauditor_batch_by_address(gi, auditor_address, DinTaskAuditingC_address):
    w3 = get_w3()
    
    DinTaskAuditingC = w3.eth.contract(address=DinTaskAuditingC_address, abi=DinTaskAuditing_abi)
    
    auditBatches = DinTaskAuditingC.functions.auditBatches(gi).call()
    
    for batch in auditBatches:
        if batch.auditors.contains(auditor_address):
            return batch
        
    return None

def get_auditor_testDataCID(gi, auditor_address, DinTaskAuditingC_address):
    w3 = get_w3()
    
    auditor_batch = getauditor_batch_by_address(gi, auditor_address, DinTaskAuditingC_address)
    
    if(auditor_batch is not None):
        return auditor_batch.testDataCID
    
    return None
    
    
def Score_models_by_auditors(gi, auditor_address, DinTaskAuditingC_address):
    w3 = get_w3()
    
    auditor_batch = getauditor_batch_by_address(gi, auditor_address, DinTaskAuditingC_address)
    
    
    if(auditor_batch is not None):
        testDataCID = auditor_batch.testDataCID
    
        model_indexes = auditor_batch.modelIndexes
        
    retrieve_from_ipfs(testDataCID, f"./Dataset/auditor/auditorDataset_{gi}_{auditor_batch.batch_id}.pt")
        
    testdata = torch.load(f"./Dataset/auditor/auditorDataset_{gi}_{auditor_batch.batch_id}.pt", weights_only=False)
    
    DinTaskAuditingC = w3.eth.contract(address=DinTaskAuditingC_address, abi=DinTaskAuditing_abi)
    
    genesis_model_cid = DinTaskAuditingC.functions.genesisModelIpfsHash().call()
    
    retrieve_from_ipfs(genesis_model_cid, f"./models/auditor/genesis_model.pt")
    
    for model_index in model_indexes:
        lm = DinTaskAuditingC.functions.lmSubmissions(gi, model_index).call()
        
        os.makedirs(f"./models/auditor", exist_ok=True)
        
        retrieve_from_ipfs(genesis_model.cid, f"./models/auditor/lm_{gi}_{model_index}.pt")
        
        lm_d = torch.load(f"./models/auditor/lm_{gi}_{model_index}.pt", weights_only=True)
        
        model_architecture = torch.load(f"./models/auditor/genesis_model.pt", weights_only=False)
        
        model_architecture.load_state_dict(lm_d)
        
        model_architecture.eval()
        
        # 2. Create DataLoader for test data
        # If testdata is a TensorDataset or Subset
        test_loader = DataLoader(testdata, batch_size=32, shuffle=False)

        # 3. Move model to device (GPU/CPU)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model_architecture.to(device)
        
        with torch.no_grad():  # No gradients needed
            for data, target in test_loader:
                data, target = data.to(device), target.to(device)

                # Forward pass
                outputs = model_architecture(data)

                # Get predicted class (for classification)
                # If outputs are logits, use argmax
                _, predicted = torch.max(outputs, 1)

                total += target.size(0)
                correct += (predicted == target).sum().item()

        accuracy = 100 * correct / total
        
        tx = DinTaskAuditingC.functions.updateModelScore(gi, model_index, accuracy).transact()
        
        receipt = w3.eth.wait_for_transaction_receipt(tx)
        
        print("Model score updated successfully")
        
        
        
        
        
        
        
        
        
        
        
        
        
    
    
    
    