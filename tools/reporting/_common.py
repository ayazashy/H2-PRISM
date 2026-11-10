"""Shared helpers for A13 reporting tools (read-only consumers of result artifacts)."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
import yaml

FINAL_STATUSES = {"VALIDATED", "FROZEN"}
NON_RESULT_DATA_STATUSES = {"ILLUSTRATIVE", "FIXTURE", "SYNTHETIC", "DEMO"}


class ReportingInputError(RuntimeError):
    """Raised when mandatory evidence is absent or invalid; never silently skipped."""


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_path(p: Path) -> str:
    return sha256_bytes(Path(p).read_bytes())


def load_config(path: Path) -> Tuple[Dict, str]:
    raw = Path(path).read_bytes()
    return yaml.safe_load(raw.decode("utf-8")), sha256_bytes(raw)


def load_input(root: Path, spec: Dict) -> pd.DataFrame:
    p = root / spec["input"]
    if not p.exists():
        raise ReportingInputError(f"[{spec.get('id')}] mandatory input missing: {spec['input']}")
    df = pd.read_csv(p) if p.suffix == ".csv" else pd.read_parquet(p)
    req = spec.get("required_columns", [])
    miss = [c for c in req if c not in df.columns]
    if miss:
        raise ReportingInputError(f"[{spec.get('id')}] input {spec['input']} missing columns {miss}")
    if "selective_risk" in df.columns and "coverage" not in df.columns:
        raise ReportingInputError(f"[{spec.get('id')}] selective_risk reported without coverage (prohibited)")
    return df


def classify(spec: Dict, df: pd.DataFrame) -> Tuple[str, str]:
    """Return (destination_kind, watermark). destination_kind in {final, preliminary, illustrative}."""
    if "data_status" in df.columns:
        vals = {str(v).upper() for v in df["data_status"].dropna().unique()}
        if vals & NON_RESULT_DATA_STATUSES:
            return "illustrative", "ILLUSTRATIVE FIXTURE - NOT A RESEARCH RESULT"
    status = str(spec.get("evidence_status", "")).upper()
    if status in FINAL_STATUSES:
        return "final", ""
    return "preliminary", f"PRELIMINARY ({status or 'UNDECLARED'}) - NOT A VALIDATED RESULT"
