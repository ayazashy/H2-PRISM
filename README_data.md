# H2-PRISM Data Reproducibility Guide
# Authored by Materials & Data Provenance Lead (Yazan / Person 3)

## 1. Dataset Source
- **Name**: H2-SimNet
- **Zenodo Record**: 17871393
- **Primary Domain**: Simulated hydrogen-blend pipeline network anomaly data

## 2. Acquisition Instructions
1. Download the archive from Zenodo record `17871393`.
2. Extract the uncompressed data into `data/raw/H2-SimNet/`.
3. Do not modify or overwrite files in `data/raw/`.

## 3. Directory Layout
```
data/
├── raw/
│   └── H2-SimNet/        # Untouched downloaded files
├── selected/             # The 6 selected benchmark scenarios
├── processed/            # Synchronized / standardized scenario representations
└── synthetic/            # Synthetic sensor faults (clearly separated!)
```

## 4. Verification Script
Run the forensic audit script:
```bash
python scripts/data_inspection/audit_dataset.py
```
This generates `AUDIT.md`, `results/materials_manifest.csv`, and `results/dataset_truth_table.md`.
