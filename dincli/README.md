
# DIN CLI structured:

```
dincli <role> <command> [options]
```

Where `<role>` ∈ { `model-owner`, `auditor`, `aggregator`, `dindao` }

That’s the **Typer multi-app pattern**, which allows subcommands for each stakeholder role, e.g.:

```
dincli model-owner train
dincli validator onboard
dincli auditor verify
dincli aggregator aggregate
dincli dindao status
```

#### **4. Update `pyproject.toml`**

Your CLI entry point doesn’t change — still:

```toml
[project.scripts]
dincli = "main:app"
```

---

#### **5. Test it**

Reinstall the CLI in editable mode:

```bash
pip install -e .
```

Now test your role-aware CLI:

```bash
dincli --help
dincli model-owner --help
dincli model-owner train ./Dataset/clients/clientDataset_1.pt --dp-mode afterTraining
dincli validator onboard
```

---

✅ **Result Example:**

```
Usage: dincli [OPTIONS] COMMAND [ARGS]...

DIN Command Line Interface (DIN CLI)

Commands:
  version        Show current DIN CLI version.
  model-owner    Commands for Model Owners in DIN.
  validator      Commands for Validators in DIN.
  auditor        Commands for Auditors in DIN.
  aggregator     Commands for Aggregators in DIN.
  dindao         Commands for DIN DAO governance.
```

---

Would you like me to help you define **role-specific command sets** (like what each role can do from CLI: e.g., `train`, `submit`, `audit`, `stake`, etc.) next?
That will make your `dincli` a full operational command-line interface for the devnet phase.
