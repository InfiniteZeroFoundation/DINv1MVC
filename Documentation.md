# DIN MVP Documentation

## Table of Contents

1. [Introduction](#introduction)

2. [Dataset](#dataset)

3. [Dataset Distribution](#dataset-distribution)

4. [Clients](#clients)

5. [Validators](#validators)

<a id="introduction"></a>
## Introduction

<a id="dataset"></a>
## Dataset

The Dataset we are currently using is MNIST (train and test) Dataset

```python
train_dataset = datasets.MNIST(root='./data', train=True, download=True, transform=transform)
test_dataset  = datasets.MNIST(root='./data', train=False, download=True, transform=transform)
```

<a id="dataset-distribution"></a>
## Dataset Distribution

We will use the test dataset as dataset for testing
```python
test_dataset  = datasets.MNIST(root='./data', train=False, download=True, transform=transform)
```

while the training dataset will be used for training and distributed amoung clients (9 clients)
```python
train_dataset = datasets.MNIST(root='./data', train=True, download=True, transform=transform)
```

<a id="clients"></a>
## Clients

We are using 9 clients for training

<a id="validators"></a>
## Validators

We are using 3 validators for validation