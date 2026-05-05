# Model_0 — Infinite Zero Network Protocol

Model_0 is the first instantiation of the **Infinite Zero Network**, a decentralized AI training and validation protocol secured by Ethereum smart contracts.

The system coordinates distributed model training, aggregation, and validation through cryptoeconomic incentives and on-chain enforcement.

---

## 🧭 Protocol Overview

Model_0 operates in **global iterations**, where each iteration defines a complete lifecycle of:

- Distributed training
- Aggregation of model updates
- Independent validation
- On-chain finalization

### Current Status

- ✅ Global Iteration 1 completed  
- 🔄 Global Iteration 2 in progress  

---

## 🔐 Security Model (Ethereum-Enforced Protocol)

The Infinite Zero Network is secured by **Ethereum smart contracts deployed on Sepolia OP Devnet**.

Ethereum is the **source of truth for all protocol state transitions and economic enforcement**.

### On-chain responsibilities

- Participant registration (all roles)
- Stake locking and slashing conditions (DIN token)
- Global iteration state machine
- Submission validation rules
- Incentive distribution and finalization

### System architecture

| Layer | Responsibility |
|------|--------|
| Ethereum (on-chain) | State, validation, incentives, enforcement |
| IPFS (Filebase) | Dataset storage and distribution |
| Off-chain compute | Training, aggregation, auditing |
| Participants | Execute computation + submit results |

---

### Data availability layer (IPFS via Filebase)

The system uses **IPFS (via Filebase)** as its decentralized storage and distribution layer.

It is responsible for:

- MNIST dataset distribution across clients
- Client-specific dataset partitions
- Storage of references to training data and artifacts

> 💡 Ethereum does not store large datasets — IPFS ensures scalable, content-addressed data availability across participants.

---

### Core guarantee

The system is **fully verifiable end-to-end**:

- Ethereum enforces correctness, incentives, and finality  
- IPFS ensures reproducible and distributed data availability  
- Off-chain compute enables scalable ML execution  

> 💡 Trust is shifted from participants to cryptographic and economic enforcement.

---

## 🎭 Participation Model

Participants interact through three composable roles:

### Aggregators
- Aggregate distributed model updates
- Produce unified model states

### Auditors
- Independently evaluate submitted results
- Validate correctness and consistency

### Clients
- Train local models on assigned datasets
- Submit updates to the network

> Roles are composable — a single participant may act as Client, Auditor, and Aggregator simultaneously.

---

## 🧠 Validator Model (No Mining)

This system does **not use mining or Proof-of-Work**.

Instead, it uses a **role-based validation system enforced by Ethereum**:

- Aggregators propose model state transitions
- Auditors verify correctness of outputs
- Ethereum finalizes accepted results

> Aggregators + Auditors collectively function as **validators**, with enforcement handled on-chain.

---

## 💻 System Requirements

- RAM: 4 GB  
- Disk: ~30 GB  
- CPU: Standard (GPU not required)  
- Python: 3.x with virtual environment  

Dependencies:
- `dincli`
- ML runtime (~2 GB, e.g. PyTorch)

---

## ⚙️ Protocol Interaction (DIN CLI)

```bash
dincli system init

---

### 🔧 Configuration

Set RPC URL in `.env`:

```env
SEPOLIA_OP_DEVNET_RPC_URL=<your_rpc_url>
```

Add Ethereum private keys:

```env
ETH_PRIVATE_KEY_0=...
ETH_PRIVATE_KEY_1=...
```

---

### ✅ Recommended

* Use **Filebase** as your IPFS provider (see `setup.md` for details)

---

## 🧩 Aggregators

### Step 1: Explore Model

```bash
dincli task explore 0
```

### Step 2: Check Global Iteration State

```bash
dincli task gi show-state 0
```

### Step 3: Register (if state = `DINaggregatorsRegistrationStarted`)

```bash
# Connect wallet (example: account index 0)
dincli system connect-wallet --account 0

# Check ETH balance
dincli system --eth-balance

# Buy DIN tokens
dincli aggregator dintoken buy 0.00001

# Stake tokens
dincli aggregator dintoken stake 10

# Verify stake
dincli aggregator dintoken read-stake

# Register as aggregator
dincli aggregator register 0
```

---

### Step 4: Check Global Iteration State

```bash
dincli task gi show-state 0
```

### Step 5: Check your Aggregation Batch (if state = `T1nT2Bcreated`)

```bash
# Check T1 batch assigned to you
dincli model-owner aggregation show-t1-batches 0 --detailed

# Check T2 batch assigned to you
dincli model-owner aggregation show-t2-batches 0 --detailed
```

---

### Step 6: Check Global Iteration State

```bash
dincli task gi show-state 0
```

### Step 7: Aggregate your T1 Batch (if state = `T1AggregationStarted`)

```bash
# show the aggregator its assigned t1 batches
dincli aggregator show-t1-batches 0 --detailed

# aggregate the assigned t1 batches
dincli aggregator aggregate-t1 0 --submit
```

---

### Step 8: Aggregate your T2 Batch (if state = `T2AggregationStarted`)

```bash
# show the aggregator its assigned t2 batches
dincli aggregator show-t2-batches 0 --detailed

# aggregate the assigned t2 batches
dincli aggregator aggregate-t2 0 --submit
```

---

## 🛡️ Auditors

### Step 1: Explore Model

```bash
dincli task explore 0
```

### Step 2: Check Global Iteration State

```bash
dincli task gi show-state 0
```

### Step 3: Register (if state = `DINauditorsRegistrationStarted`)

```bash
# Connect wallet
dincli system connect-wallet --account 0

# Check ETH balance
dincli system --eth-balance

# Buy DIN tokens
dincli auditor dintoken buy 0.00001

# Stake tokens
dincli auditor dintoken stake 10

# Verify stake
dincli auditor dintoken read-stake

# Register as auditor
dincli auditor register 0
```

---

### Step 4: Check Global Iteration State

```bash
dincli task gi show-state 0
```

### Step 5: Check your Auditor Batch (if state = `AuditorsBatchesCreated`)

```bash
dincli auditor lms-evaluation show-batch 0
```

If a batch is shown, you will soon be required to audit it.

---

### Step 6: Check Global Iteration State

```bash
dincli task gi show-state 0
```

### Step 7: Audit your assigned batch (if state = `LMSevaluationStarted`)

```bash
# check your assigned batch
dincli auditor lms-evaluation show-batch 0

# audit your batch (scripts run automatically)
dincli auditor lms-evaluation evaluate 0 --submit
```

---

## 🤖 Clients

### Step 1: Explore Model

```bash
dincli task explore 0
```

### Step 2: Check Global Iteration State

```bash
dincli task gi show-state 0
```

### Step 3: Submit Local Model (if state = `LMSstarted`)

```bash
# Connect wallet
dincli system connect-wallet --account 0

# Check ETH balance
dincli system --eth-balance

# Train and submit local model
dincli client train-lms 0 --submit

# Show submitted models
dincli client lms show-models 0
```

---

### 💡 Optional (Recommended First Step)

```bash
# Train locally without submitting 
dincli client train-lms 0
```

---

## 📂 Dataset Requirements

Ensure your dataset is located at:

```
<CACHE_DIR>/sepolia_op_devnet/model_0/dataset/clients/<account_address>/data.pt
```

Find your cache directory:

```bash
dincli system get-cache-dir
```

---

## 📊 MNIST Dataset Distribution

Model_0 uses the **MNIST dataset**, integrated into `dincli`.

### 📦 Distribute Dataset

```bash
dincli system dataset distribute-mnist \
  --seed <seed> \
  --model-id <model-id> \
  --test-train \
  --clients \
  --num-clients <num-clients> \
  --start-client-index <start-client-index>
```

---

### 📌 Parameters

| Argument               | Description                         |
| ---------------------- | ----------------------------------- |
| `--seed`               | Random seed for shuffling           |
| `--model-id`           | Creates model directory             |
| `--test-train`         | Creates dataset directory           |
| `--clients`            | Enables client dataset distribution |
| `--num-clients`        | Number of participating clients     |
| `--start-client-index` | Starting wallet index               |

---

### ✅ Example

```bash
dincli system dataset distribute-mnist \
  --seed 42 \
  --model-id 0 \
  --test-train \
  --clients \
  --num-clients 9 \
  --start-client-index 0
```

---

## ⚠️ Account Indexing Requirement

Ensure sufficient private keys in `.env`.

### Formal Requirement

```
MAX_INDEX ≥ start-client-index + num-clients - 1
```

### Interpretation

* Clients are assigned sequentially and inclusively
* Total keys required = `num-clients`

### Example

If:

* `start-client-index = 2`
* `num-clients = 9`

Then:

```
ETH_PRIVATE_KEY_2 → ETH_PRIVATE_KEY_10
```

---

## 🧠 Final Notes

* Always verify the **Global Iteration State** before taking action
* Use multiple accounts strategically
* Stay active in community channels for updates

---

> 🚀 You are now ready to participate in **Model_0** and contribute to decentralized AI on the InfiniteZero Network.
