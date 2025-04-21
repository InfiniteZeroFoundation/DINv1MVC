import torch
from torchvision import datasets, transforms
import os

def load_mnist_dataset():
    """
    Load and preprocess the MNIST dataset.
    """
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))  # mean, std for MNIST
    ])

    # Download MNIST training + test datasets
    train_dataset = datasets.MNIST(root='./data', train=True, download=True, transform=transform)
    test_dataset = datasets.MNIST(root='./data', train=False, download=True, transform=transform)

    return train_dataset, test_dataset

def save_datasets(train_dataset, test_dataset, output_dir="./Dataset"):
    """
    Save the train and test datasets as .pt files in the specified directories.
    """
    os.makedirs(f"{output_dir}/train", exist_ok=True)
    os.makedirs(f"{output_dir}/test", exist_ok=True)

    # Save train dataset
    torch.save(train_dataset, f"{output_dir}/train/train_dataset.pt")

    # Save test dataset
    torch.save(test_dataset, f"{output_dir}/test/test_dataset.pt")

    print("Datasets saved successfully!")