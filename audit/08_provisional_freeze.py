"""
H2-PRISM Audit Suite — Task Y8: Provisional Data Freeze Packaging
Owner: Yazan (Dataset Audit, Data Engineering & Dataset Readiness Lead)

Packages an essential early data freeze for Faisal to unblock ML feature engineering & pipeline development:
1. Generates 01_dataset_audit/provisional/PROVISIONAL_DATA_FREEZE_MANIFEST.csv
2. Copies frozen label mapping to 01_dataset_audit/provisional/PROVISIONAL_LABEL_MAPPING.yaml
3. Generates 01_dataset_audit/provisional/PROVISIONAL_DATA_FREEZE_NOTES.md
4. Generates 01_dataset_audit/provisional/PROVISIONAL_DATA_FREEZE_VERSION.txt
"""

import time
import shutil
from pathlib import Path
import pandas as pd

AUDIT_DIR = Path("01_dataset_audit")
PROV_DIR = AUDIT_DIR / "provisional"
PROV_DIR.mkdir(parents=True, exist_ok=True)

VERSION = "v0.1-provisional-2026-10-30"


def package_provisional_freeze():
    print("[*] Task Y8: Generating Provisional Data Freeze Package for Faisal...")
    
    # 1. Read scenario map and timing audit
    df_map = pd.read_csv(AUDIT_DIR / "DATASET_SCENARIO_MAP.csv")
    df_timing = pd.read_csv(AUDIT_DIR / "EVENT_TIMING_AUDIT.csv")
    
    # Merge timing info into manifest
    timing_cols = ["Scenario_ID", "duration_s", "event_onset_s", "event_offset_s", "event_active_duration_s", "timing_status"]
    df_manifest = df_map.merge(df_timing[timing_cols], on="Scenario_ID", how="left")
    
    # Add eligibility flag:
    # Mark single-fault scenarios as eligible for primary 4-class attribution
    # Mark compound faults as reserved for secondary multi-label evaluation
    def check_eligibility(row):
        lbl = str(row["event_label_raw"])
        if "Combined" in lbl or "overlapped" in str(row["file"]).lower() or "brokenc1g5" in str(row["file"]).lower() or "g4brokenc1" in str(row["file"]).lower():
            return False, "COMPOUND_FAULT_RESERVED_FOR_SECONDARY_MULTILABEL"
        return True, "ELIGIBLE_PRIMARY_4CLASS"
        
    elig_res = df_manifest.apply(check_eligibility, axis=1)
    df_manifest["eligible_primary"] = [e[0] for e in elig_res]
    df_manifest["exclusion_reason"] = [e[1] for e in elig_res]
    df_manifest["provisional_freeze_version"] = VERSION
    
    manifest_path = PROV_DIR / "PROVISIONAL_DATA_FREEZE_MANIFEST.csv"
    df_manifest.to_csv(manifest_path, index=False)
    print(f"[✓] Saved {manifest_path} ({len(df_manifest)} records)")
    
    # 2. Copy class mapping
    shutil.copy(AUDIT_DIR / "class_mapping.yaml", PROV_DIR / "PROVISIONAL_LABEL_MAPPING.yaml")
    print(f"[✓] Saved {PROV_DIR / 'PROVISIONAL_LABEL_MAPPING.yaml'}")
    
    # 3. Version text
    with open(PROV_DIR / "PROVISIONAL_DATA_FREEZE_VERSION.txt", "w") as f:
        f.write(f"{VERSION}\nGenerated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\nStatus: PROVISIONAL_DEVELOPMENT_ONLY\n")
    print(f"[✓] Saved {PROV_DIR / 'PROVISIONAL_DATA_FREEZE_VERSION.txt'}")
    
    # 4. Freeze notes
    n_total_files = len(df_manifest)
    n_scens = df_manifest["Scenario_ID"].nunique()
    n_fams = df_manifest["Scenario_Family_ID"].nunique()
    n_eligible_files = int(df_manifest["eligible_primary"].sum())
    
    notes_md = f"""# H2-PRISM Provisional Data Freeze Notes (Task Y8)
**Version**: `{VERSION}`  
**Author**: Yazan (Lead, Dataset Audit, Data Engineering & Dataset Readiness)  
**Consumer**: Faisal (ML & Experiments Lead)  
**Reviewer**: Ahmed (Research Lead & Provenance)  
**Date**: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}  
**Status**: **PROVISIONAL / DEVELOPMENT ONLY**

---

## 1. Scope & Objective of Early Handoff

This package enables **Faisal** to begin controlled pipeline development, window generation, and feature extraction immediately, without waiting for the final dataset readiness freeze (Y7).

### Key Rules of Engagement:
1. **Scope of Use**: Faisal may use this package for interface testing, feature extraction, windowing experiments, and baseline exploratory code.
2. **Never Represent as Final**: Any experimental output generated from this package must be marked `PROVISIONAL` or `DEVELOPMENT_ONLY`.
3. **No Outer-Test Tuning**: Grouped splits must respect the declared `Scenario_Family_ID`.

---

## 2. Package Summary & Metrics

| Entity | Count | Notes |
| :--- | :---: | :--- |
| **Total Physical Data Files** | **{n_total_files}** | 123 CSV + 119 Parquet files |
| **Underlying Scenarios (`Scenario_ID`)** | **{n_scens}** | Distinct simulation configurations |
| **Defensible Families (`Scenario_Family_ID`)** | **{n_fams}** | Primary grouped independence unit |
| **Eligible Files for Primary 4-Class** | **{n_eligible_files}** | Single-fault & normal scenarios |
| **Compound Fault Files (Reserved)** | **{n_total_files - n_eligible_files}** | Simultaneous Leak + Compressor faults |

---

## 3. Verified Channels & Loading Rules for Faisal

1. **Pressure Transmitters**: `PS1` through `PS12` (Unit: MPa, float64).
2. **Mass Flow Meters**: `MFS1` through `MFS4` (Unit: kg/s, float64).
3. **Temperature**: **ZERO localized temperature sensors exist**. Faisal must NOT assume or invent localized temperature columns!
4. **Time & Sampling**:
   - `Timestamp` column in seconds (or 1.0s implicit index).
   - Sampling rate is strictly 1 Hz (dt = 1.0 s).
   - Total duration per run is ~20,000 seconds.
5. **Exact Onset Timings**:
   - Available in `PROVISIONAL_DATA_FREEZE_MANIFEST.csv` under columns `event_onset_s` and `event_offset_s`.
   - Windows crossing the onset boundary should be labeled carefully or flagged as `BOUNDARY_CROSSING`.

---

## 4. Known Data-Quality Issues & Warnings

- **Phase-Event Confounding**: Compressor faults were only injected in initial ramp-up; leaks at steady state. Do NOT use phase as an ML feature.
- **Duplicate Exports**: Parquet and CSV files share identical underlying numerical signals. Faisal must train on ONE format (recommended: canonical Parquet) to avoid duplicate leakage.
"""
    with open(PROV_DIR / "PROVISIONAL_DATA_FREEZE_NOTES.md", "w") as f:
        f.write(notes_md)
    print(f"[✓] Saved {PROV_DIR / 'PROVISIONAL_DATA_FREEZE_NOTES.md'}")


def main():
    print("=" * 80)
    print(" H2-PRISM — TASK Y8: PROVISIONAL DATA FREEZE EARLY HANDOFF")
    print(" Owner: Yazan | Role: Dataset Audit & Readiness Lead")
    print("=" * 80)
    package_provisional_freeze()
    print("=" * 80)
    print("[✓] Task Y8 completed successfully.")
    print("=" * 80)


if __name__ == "__main__":
    main()
