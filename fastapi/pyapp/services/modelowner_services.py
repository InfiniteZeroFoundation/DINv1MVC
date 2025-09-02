import torch
import os
from services.ipfs_service import upload_to_ipfs

def create_audit_testDataCIDs(batch_counts: int, gi: int):
    print("batch_counts", batch_counts)
    test_data = torch.load(f"./Dataset/test/test_dataset.pt", weights_only=False)
    
    total_test_samples = len(test_data)
    
    testData_percentage_per_auditor_batch = 5
    
    # Number of samples each batch gets
    samples_per_batch = int(total_test_samples * (testData_percentage_per_auditor_batch / 100))
    
    audit_testDataCIDs = []
    
    for batch_id in range(batch_counts):
        
        torch.manual_seed(batch_id)
        
        # Generate random indices
        random_indices = torch.randperm(total_test_samples)[:samples_per_batch]
        
        # Create shuffled subset
        assigned_testData = torch.utils.data.Subset(test_data, random_indices)
        
        os.makedirs(f"./Dataset/auditorTestDatasets", exist_ok=True)
        
        torch.save(assigned_testData, f"./Dataset/auditorTestDatasets/auditorDataset_{gi}_{batch_id}.pt")
        
        ipfs_hash = upload_to_ipfs(f"./Dataset/auditorTestDatasets/auditorDataset_{gi}_{batch_id}.pt", f"Auditor Dataset for gi_{gi} index {batch_id} uploaded")
        
        audit_testDataCIDs.append(ipfs_hash)
    return audit_testDataCIDs
        
        
        