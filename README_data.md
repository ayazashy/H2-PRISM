# H2-PRISM Data Reproducibility Guide
# Authored by Materials & Data Provenance Lead (Yazan / Person 3)

## 1. Dataset Source
- **Name**: H2-SimNet
- **Zenodo Record**: 17871393
- **Primary Domain**: Simulated hydrogen-blend pipeline network anomaly data

## 2. Acquisition Instructions
1. Download the archive from Zenodo record `17871393`.
2. Extract the uncompressed data into `data/raw/H2-SimNet-Dataset/`.
3. Do not modify or overwrite files in `data/raw/`.

## 3. Directory Layout
```
data/
├── raw/
│   └── H2-SimNet-Dataset/   # Untouched downloaded files (123 CSVs + Simscape models)
├── selected/                # The 6 selected benchmark scenarios
├── processed/               # Synchronized / standardized scenario representations (1 Hz, Pa/kg·s)
└── synthetic/               # Synthetic sensor faults (clearly separated!)
```

## 4. Verification & Curation Scripts
1. Run the forensic audit script:
```bash
python scripts/data_inspection/audit_dataset.py
```
This generates `results/materials_manifest.csv` and `results/dataset_truth_table.md`.

2. Curate and standardize the 6 canonical benchmark scenarios:
```bash
python scripts/data_inspection/select_scenarios.py
```
Outputs standardized datasets into `data/processed/`.
