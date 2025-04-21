import torch
import numpy as np
import os

def partition_dataset(dataset, num_clients, seed=42):
    """
    Partition the dataset into `num_clients` subsets.

    Args:
        dataset: The dataset to partition.
        num_clients: Number of clients to distribute the dataset to.
        seed: Random seed for reproducibility (default: 42).

    Returns:
        A list of partitioned datasets.
    """

    total_samples = len(dataset)
    indices = list(range(total_samples))

    # Set the random seed for reproducibility
    np.random.seed(seed)

    # Shuffle indices for random partitioning
    np.random.shuffle(indices)

    # Split indices into `num_clients` chunks
    partitions = np.array_split(indices, num_clients)

    # Create partitioned datasets
    partitioned_data = []
    for i, partition in enumerate(partitions):
        subset = torch.utils.data.Subset(dataset, partition)
        partitioned_data.append(subset)

    return partitioned_data


def save_partitioned_data(partitioned_data, output_dir="./Dataset/clients"):
    """
    Save partitioned data to disk.
    """
    os.makedirs(output_dir, exist_ok=True)

    for i, partition in enumerate(partitioned_data):
        # Save each partition as a list of indices
        indices = [idx for idx in partition.indices]
        torch.save(indices, f"{output_dir}/clientDataset_{i+1}.pt")
