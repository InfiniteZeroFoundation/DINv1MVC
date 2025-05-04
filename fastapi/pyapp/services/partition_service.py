import torch
import numpy as np
import os

def partition_dataset(dataset, num_clients, seed=42):
    """
    Partition the dataset into `num_clients` subsets and extract the actual data.

    Args:
        dataset: The dataset to partition.
        num_clients: Number of clients to distribute the dataset to.
        seed: Random seed for reproducibility (default: 42).

    Returns:
        A list of lists, where each inner list contains the actual data for a client.
    """
    total_samples = len(dataset)
    indices = list(range(total_samples))

    # Set the random seed for reproducibility
    np.random.seed(seed)

    # Shuffle indices for random partitioning
    np.random.shuffle(indices)

    # Split indices into `num_clients` chunks
    partitions = np.array_split(indices, num_clients)

    # Extract the actual data for each partition
    partitioned_data = []
    for partition in partitions:
        subset_data = [dataset[idx] for idx in partition]
        partitioned_data.append(subset_data)

    return partitioned_data


def save_partitioned_data(partitioned_data, output_dir="./Dataset/clients"):
    """
    Save partitioned data to disk.

    Args:
        partitioned_data: A list of lists, where each inner list contains the actual data for a client.
        output_dir: Directory where partitioned data will be saved.
    """
    os.makedirs(output_dir, exist_ok=True)

    for i, partition in enumerate(partitioned_data):
        # Save the actual data for the i-th client
        torch.save(partition, f"{output_dir}/clientDataset_{i+1}.pt")
