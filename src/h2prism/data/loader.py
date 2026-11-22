"""
H2-PRISM Data Access & Loader Module
Owner: Yazan (Lead, Dataset Audit, Data Engineering & Dataset Readiness)
Provides direct, one-line access to H2-SimNet scenarios, splits, and sample datasets.
"""

import hashlib
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
import pandas as pd
import numpy as np

# Standard dataset search paths
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
RAW_DATASET_DIR = WORKSPACE_ROOT / "data" / "raw" / "H2-SimNet-Dataset"
SAMPLE_DATASET_DIR = WORKSPACE_ROOT / "data" / "sample"
AUDIT_DIR = WORKSPACE_ROOT / "01_dataset_audit"
MANIFEST_FILE = AUDIT_DIR / "provisional" / "PROVISIONAL_DATA_FREEZE_MANIFEST.csv"
FOLDS_FILE = AUDIT_DIR / "folds.csv"
CHECKSUM_FILE = AUDIT_DIR / "raw_checksums.sha256"


def _verified_sample_copy(raw_rel_file: str) -> Optional[Path]:
    """AUDIT FIX (pending Yazan review): return the data/sample copy of a raw file ONLY if its
    SHA-256 equals the raw file's entry in raw_checksums.sha256. Sample files share basenames
    with files from other topologies (e.g. leakG4.parquet exists for Center/Downstream/Upstream),
    so a name match alone could silently return the wrong scenario."""
    if not CHECKSUM_FILE.exists():
        return None
    cand = SAMPLE_DATASET_DIR / Path(raw_rel_file).name
    if not cand.exists():
        return None
    expected = None
    for line in CHECKSUM_FILE.read_text(encoding="utf-8").splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) == 2 and parts[1].lstrip("*") == raw_rel_file:
            expected = parts[0]
            break
    if expected is None:
        return None
    if hashlib.sha256(cand.read_bytes()).hexdigest() != expected:
        return None
    return cand


def get_dataset_dir() -> Path:
    """Returns the primary dataset directory if it exists, otherwise falls back to sample dir."""
    if RAW_DATASET_DIR.exists() and any(RAW_DATASET_DIR.iterdir()):
        return RAW_DATASET_DIR
    elif SAMPLE_DATASET_DIR.exists() and any(SAMPLE_DATASET_DIR.iterdir()):
        return SAMPLE_DATASET_DIR
    return RAW_DATASET_DIR


def is_raw_dataset_available() -> bool:
    """Checks whether the full ~1 GB raw H2-SimNet dataset is present on disk."""
    return RAW_DATASET_DIR.exists() and (RAW_DATASET_DIR / "H2-SimNet-clean").exists()


def list_scenarios(eligible_only: bool = True) -> pd.DataFrame:
    """
    Returns a catalog of all scenarios in the dataset with their IDs, families, topologies, and classes.
    """
    if not MANIFEST_FILE.exists():
        raise FileNotFoundError(f"Manifest file not found at {MANIFEST_FILE}")
    
    df = pd.read_csv(MANIFEST_FILE)
    if eligible_only and "eligible_primary" in df.columns:
        df = df[df["eligible_primary"] == True].copy()
    
    # Map raw label to standard 4-class target
    label_map = {
        "NORMAL": "NORMAL",
        "Leak_G3": "LEAK",
        "Leak_G4": "LEAK",
        "Leak_G5": "LEAK",
        "Leak_G6": "LEAK",
        "Leak_G3_G4": "LEAK",
        "Leak_G3_G6": "LEAK",
        "Leak_G5_G6": "LEAK",
        "CompressorFault": "COMPRESSOR_FAULT",
        "CompressorDelay": "COMPRESSOR_DELAY",
    }
    df["target_class"] = df["event_label_raw"].map(label_map).fillna("UNKNOWN")
    return df


def ensure_dataset_available(auto_download: bool = False) -> bool:
    """Checks if raw dataset is installed; auto-downloads if requested."""
    if is_raw_dataset_available():
        return True
    if auto_download:
        import sys
        scripts_dir = WORKSPACE_ROOT / "scripts"
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
        from download_data import setup_dataset
        setup_dataset()
        return is_raw_dataset_available()
    return False


def load_scenario(
    identifier: Union[str, Path],
    format: str = "parquet",
    auto_download: bool = False,
) -> pd.DataFrame:
    """
    Directly loads a scenario as a pandas DataFrame.
    
    Args:
        identifier: Can be:
            1. Short scenario name (e.g., 'leakG3', 'brokenC1_strong', 'normality_gest_center')
            2. Scenario ID (e.g., 'SCEN_CENTER_STEADY_STATE_LEAKG3')
            3. File name (e.g., 'leakG3.parquet' or 'leakG3.csv')
            4. Relative path (e.g., 'data/raw/H2-SimNet-Dataset/...')
        format: 'parquet' (preferred, faster) or 'csv'
    
    Returns:
        pd.DataFrame containing 20,000 timesteps of SCADA measurements and labels.
    """
    if not is_raw_dataset_available() and auto_download:
        ensure_dataset_available(auto_download=True)

    id_str = str(identifier).strip()
    
    # 1. Direct path check
    direct_p = Path(id_str)
    if direct_p.exists() and direct_p.is_file():
        return _read_file(direct_p)
    
    # Check inside WORKSPACE_ROOT
    ws_p = WORKSPACE_ROOT / id_str
    if ws_p.exists() and ws_p.is_file():
        return _read_file(ws_p)
        
    raw_p = WORKSPACE_ROOT / "data" / "raw" / id_str
    if raw_p.exists() and raw_p.is_file():
        return _read_file(raw_p)

    # 2. Check in sample dir first if raw not available
    if SAMPLE_DATASET_DIR.exists():
        for sample_f in SAMPLE_DATASET_DIR.glob(f"*{id_str}*"):
            if sample_f.suffix in [".parquet", ".csv"]:
                return _read_file(sample_f)

    # 3. Search via manifest
    if MANIFEST_FILE.exists():
        df_man = pd.read_csv(MANIFEST_FILE)
        
        # Match by Scenario_ID
        match = df_man[df_man["Scenario_ID"].astype(str).str.upper() == id_str.upper()]
        
        # Match by filename
        if len(match) == 0:
            match = df_man[df_man["file"].str.endswith(f"/{id_str}") | (df_man["file"] == id_str)]
            
        # Match by substring without extension
        if len(match) == 0:
            stem = Path(id_str).stem
            match = df_man[df_man["file"].str.contains(f"/{stem}\\.", regex=True, na=False)]
            
        if len(match) > 0:
            rel_file = match.iloc[0]["file"]
            
            # Prefer requested format
            if format == "parquet" and rel_file.endswith(".csv"):
                pq_cand = rel_file.replace("/csv/", "/parquet/").replace(".csv", ".parquet")
                full_pq = WORKSPACE_ROOT / "data" / "raw" / pq_cand
                if full_pq.exists():
                    return _read_file(full_pq)
                    
            full_path = WORKSPACE_ROOT / "data" / "raw" / rel_file
            if full_path.exists():
                return _read_file(full_path)

            # AUDIT FIX: checksum-verified fallback to the tracked sample copy
            for cand_rel in ([pq_cand] if format == "parquet" and rel_file.endswith(".csv") else []) + [rel_file]:
                sample = _verified_sample_copy(cand_rel)
                if sample is not None:
                    return _read_file(sample)

    # 4. Fallback: recursive glob inside data/raw
    if RAW_DATASET_DIR.exists():
        stem = Path(id_str).stem
        candidates = list(RAW_DATASET_DIR.rglob(f"{stem}.{format}"))
        if not candidates:
            candidates = list(RAW_DATASET_DIR.rglob(f"*{stem}*.{format}"))
        if candidates:
            return _read_file(candidates[0])

    raise FileNotFoundError(
        f"Could not locate scenario '{identifier}'.\n"
        f"The full H2-SimNet dataset (998 MB) is not present locally.\n"
        f"Run 'python3 setup_data.py' to automatically download and extract it in 1 click from Zenodo.\n"
        f"Direct download link: https://zenodo.org/records/17871393/files/H2-SimNet-Dataset.zip?download=1"
    )


def load_fold(
    fold_id: int = 1,
    skip_missing: bool = False,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Loads train and test scenarios for a given outer fold (1, 2, or 3)
    according to 01_dataset_audit/folds.csv.

    AUDIT FIX (pending Yazan review): missing files previously caused a silent `continue`,
    so a fold could return empty train/test lists without any signal. Missing files now
    raise FileNotFoundError unless skip_missing=True, in which case a warning lists them.
    NOTE: folds.csv lists two files per Scenario_ID (two export trees whose contents differ,
    see 06_audit_preparation/YAZAN_DATASET_VERIFICATION.md); loading both double-counts the
    scenario. This function does not choose a canonical file - that is an open Y1/Y2 decision.

    Returns:
        Tuple of (train_list, test_list) where each element is a dict:
        {'scenario_id': ..., 'target_class': ..., 'topology': ..., 'data': pd.DataFrame}
    """
    if not FOLDS_FILE.exists():
        raise FileNotFoundError(f"Folds specification file not found at {FOLDS_FILE}")
        
    df_folds = pd.read_csv(FOLDS_FILE)
    fold_df = df_folds[df_folds["outer_fold_id"] == fold_id]
    if len(fold_df) == 0:
        raise ValueError(f"No records found for fold_id={fold_id}. Available folds: {sorted(df_folds['outer_fold_id'].unique())}")
        
    train_records = []
    test_records = []
    missing = []

    for _, row in fold_df.iterrows():
        try:
            df_scen = load_scenario(row["file"])
        except FileNotFoundError:
            missing.append(row["file"])
            continue
        item = {
            "Scenario_ID": row["Scenario_ID"],
            "Scenario_Family_ID": row["Scenario_Family_ID"],
            "target_class": row["target_class"],
            "topology": row["topology"],
            "file": row["file"],
            "data": df_scen,
        }
        if row["split_role"] == "train":
            train_records.append(item)
        else:
            test_records.append(item)

    if missing:
        msg = (f"fold {fold_id}: {len(missing)} of {len(fold_df)} fold files are not available locally "
               f"(first: {missing[0]}). Install the raw dataset or pass skip_missing=True.")
        if not skip_missing:
            raise FileNotFoundError(msg)
        warnings.warn(msg, RuntimeWarning, stacklevel=2)

    return train_records, test_records


def _read_file(path: Path) -> pd.DataFrame:
    """Helper to read parquet or csv."""
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    elif path.suffix == ".csv":
        return pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")


def get_dataset_summary() -> Dict[str, Any]:
    """Returns high-level statistics about the dataset installation."""
    raw_exists = is_raw_dataset_available()
    sample_exists = SAMPLE_DATASET_DIR.exists() and any(SAMPLE_DATASET_DIR.iterdir())
    
    return {
        "raw_dataset_available": raw_exists,
        "raw_dataset_path": str(RAW_DATASET_DIR) if raw_exists else None,
        "sample_dataset_available": sample_exists,
        "sample_dataset_path": str(SAMPLE_DATASET_DIR) if sample_exists else None,
        "active_data_dir": str(get_dataset_dir()),
        "total_manifest_scenarios": 58,
        "total_independent_families": 13,
        "primary_classes": ["NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"],
        "sensor_channels": {
            "pressure": [f"PS{i}" for i in range(1, 13)],
            "mass_flow": [f"MFS{i}" for i in range(1, 5)],
            "temperature": [],  # Verified 0 localized temperature sensors
        },
    }
