# H2-PRISM Dataset Access & Provisioning Guide
**Owner**: Yazan (Lead, Dataset Audit, Data Engineering & Dataset Readiness)

---

## 1. Where Is the Dataset Stored?

| Dataset Tier | Directory Path | Size | Status in Git | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Full Raw Benchmark** | `data/raw/H2-SimNet-Dataset/` | **998 MB** (265 files) | **Ignored** (`.gitignore`) | Complete peer-reviewed H2-SimNet archive (Zenodo 17871393) with all parquet/csv runs, simulations, and documentation. |
| **Quickstart Sample** | `data/sample/` | **10 MB** (4 scenarios) | **Tracked** in Git | 4 full-length (20,000 timestep) representative scenarios covering all 4 target classes for instant offline testing without downloading 1 GB. |

---

## 2. Instant Python API: Load in 2 Lines of Code

The core Python package `h2prism.data` provides direct, one-line loading of scenarios, metadata, and cross-validation folds:

```python
from h2prism.data import load_scenario, list_scenarios, load_fold

# 1. List all 58 distinct scenarios:
scenarios = list_scenarios()
print(scenarios[["Scenario_ID", "target_class", "topology"]].head())

# 2. Load any scenario directly by short name, ID, or file path:
df_leak = load_scenario("leakG4")  # (20,000 timesteps x 24 channels)
df_norm = load_scenario("normality_gest_center")

# 3. Access sensor readings:
print(f"Inlet Pressure (PS1)  : {df_leak['PS1'].iloc[0]:.2f} MPa")
print(f"Inlet Mass Flow (MFS1): {df_leak['MFS1'].iloc[0]:.2f} kg/s")

# 4. Load full outer fold (1, 2, or 3) train & test splits for model training:
train_scenarios, test_scenarios = load_fold(fold_id=1)
print(f"Fold 1: {len(train_scenarios)} train scenarios, {len(test_scenarios)} test scenarios")
```

---

## 3. Instant CLI Inspection

Anyone can inspect dataset availability and verify scenario loading from the terminal:

```bash
# Print dataset summary and test instant scenario loading
python3 -m h2prism.data

# Or view dataset provisioning status
python3 scripts/download_data.py --summary
```

---

## 4. Fresh Clone Provisioning (1-Click Automated Setup)

Because raw benchmarks cannot be pushed to Git (~1 GB), running `setup_data.py` at the repository root automatically downloads, extracts, and provisions the dataset in a single step:

```bash
# 1-click automated download & extraction:
python3 setup_data.py
```

### What this command does:
1. Downloads `H2-SimNet-Dataset.zip` (509 MB) directly from the official Zenodo link:
   [`https://zenodo.org/records/17871393/files/H2-SimNet-Dataset.zip?download=1`](https://zenodo.org/records/17871393/files/H2-SimNet-Dataset.zip?download=1)
2. Unzips it into `data/raw/H2-SimNet-Dataset/` (998 MB uncompressed).
3. Automatically deletes the `.zip` archive to save disk space.
4. Validates cryptographic SHA-256 hashes against `01_dataset_audit/raw_checksums.sha256`.
5. Executes a test load on `leakG4.parquet` to confirm the environment is 100% operational.
