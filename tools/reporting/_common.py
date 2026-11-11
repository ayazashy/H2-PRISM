"""Shared helpers for A13 reporting tools (read-only consumers of result artifacts)."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
import yaml

FINAL_STATUSES = {"VALIDATED", "FROZEN", "VERIFIED"}  # VERIFIED: structural dataset descriptions only (no model outputs)
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
    try:
        df = pd.read_csv(p) if p.suffix == ".csv" else pd.read_parquet(p)
    except pd.errors.EmptyDataError:
        raise ReportingInputError(f"[{spec.get('id')}] no rows: input {spec['input']} is an empty table") from None
    if not len(df):
        raise ReportingInputError(f"[{spec.get('id')}] no rows: input {spec['input']} is an empty table")
    req = spec.get("required_columns", [])
    miss = [c for c in req if c not in df.columns]
    absent = [c for c in (spec.get("columns") or []) if c not in df.columns and c not in miss]
    if absent and "status" in df.columns and (df["status"] != "ESTIMABLE").all():
        df = df.assign(**{c: float("nan") for c in absent})  # selected table columns of all-NOT_ESTIMABLE rows
    if miss and "status" in df.columns and len(df) and (df["status"] != "ESTIMABLE").all():
        df = df.assign(**{c: float("nan") for c in miss})  # all rows NOT_ESTIMABLE: the values do not exist (empty, never 0)
        miss = []
    if miss:
        raise ReportingInputError(f"[{spec.get('id')}] input {spec['input']} missing columns {miss}")
    if "selective_risk" in df.columns and "coverage" not in df.columns:
        raise ReportingInputError(f"[{spec.get('id')}] selective_risk reported without coverage (prohibited)")
    for col, val in (spec.get("filter") or {}).items():  # select rows of a multi-variant runner output
        if col not in df.columns:
            raise ReportingInputError(f"[{spec.get('id')}] filter column {col} not in {spec['input']}")
        vals = val if isinstance(val, list) else [val]
        df = df[df[col].astype(str).isin([str(v) for v in vals])]
    if spec.get("filter") and df.empty:
        raise ReportingInputError(f"[{spec.get('id')}] no rows: filter {spec['filter']} matches nothing in {spec['input']}")
    return df.reset_index(drop=True)


def classify(spec: Dict, df: pd.DataFrame) -> Tuple[str, str]:
    """Return (destination_kind, watermark). destination_kind in {final, preliminary, illustrative}."""
    if "artifact_class" in df.columns:  # runner outputs: only PRIMARY/ROBUSTNESS/SENSITIVITY runs are research data
        vals = {str(v).upper() for v in df["artifact_class"].dropna().unique()}
        if vals & {"SYNTHETIC_TEST", "PREFLIGHT_ONLY"}:
            return "illustrative", "SYNTHETIC TEST OUTPUT - NOT A RESEARCH RESULT"
    if "data_status" in df.columns:
        vals = {str(v).upper() for v in df["data_status"].dropna().unique()}
        if vals & NON_RESULT_DATA_STATUSES:
            return "illustrative", "ILLUSTRATIVE FIXTURE - NOT A RESEARCH RESULT"
    status = str(spec.get("evidence_status", "")).upper()
    if status in FINAL_STATUSES:
        return "final", ""
    return "preliminary", f"PRELIMINARY ({status or 'UNDECLARED'}) - NOT A VALIDATED RESULT"
