#!/usr/bin/env python3
"""
Read-only raw-data investigation for the H2-PRISM dataset verification
(06_audit_preparation/RAW_DATASET_VERIFICATION_REPORT.md). Opens raw files for reading only.
No model is trained and nothing in data/raw is modified.

Usage (from repo root):  python 06_audit_preparation/raw_verification/investigate_raw.py
Outputs: 06_audit_preparation/raw_verification/{CROSS_TREE_COMPARISON,FILE_STRUCTURE,
         PRE_EVENT_SHARED_SEGMENTS,LABEL_CONSISTENCY}.csv
"""

from __future__ import annotations

from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

RAW = Path("data/raw/H2-SimNet-Dataset")
OUT = Path("06_audit_preparation/raw_verification")
SENS = [f"PS{i}" for i in range(1, 13)] + [f"MFS{i}" for i in range(1, 5)]
LAB = ["label_anomaly", "Leak", "CompressorFault", "CompressorDelay", "leak_G3", "leak_G4", "leak_G5", "leak_G6"]


def rel(p: Path) -> str:
    return p.relative_to(RAW.parent).as_posix()


def onset_row(df):
    if "label_anomaly" not in df:
        return None
    idx = np.flatnonzero(df["label_anomaly"].to_numpy() == 1)
    return int(idx[0]) if idx.size else None


def main():
    pqs = sorted(RAW.rglob("*.parquet"))
    # ---- 1. structure of every parquet / csv
    rows = []
    for p in pqs + sorted(RAW.rglob("*.csv")):
        if p.suffix == ".parquet":
            md = pq.read_metadata(p)
            sch = pq.read_schema(p)
            df = pd.read_parquet(p)
            pandas_md = (sch.metadata or {}).get(b"pandas", b"")[:0]
        else:
            df = pd.read_csv(p)
        idx = df.index
        rows.append({
            "file": rel(p), "n_rows": len(df), "n_cols": df.shape[1],
            "columns": ";".join(map(str, df.columns)),
            "has_time_column": any(str(c).lower() in ("timestamp", "time", "t") for c in df.columns),
            "index_is_default_range": isinstance(idx, pd.RangeIndex) and idx.start == 0 and idx.step == 1,
            "has_labels": "label_anomaly" in df.columns,
            "onset_row": onset_row(df),
            "label_cols_monotone_step": all(
                (np.diff(df[c].to_numpy()) >= 0).all() for c in LAB if c in df.columns),
        })
    st = pd.DataFrame(rows)
    st.to_csv(OUT / "FILE_STRUCTURE.csv", index=False, lineterminator="\n")

    # ---- 2. clean tree vs other tree, same relative sub-path
    cmp = []
    for p in pqs:
        r = p.relative_to(RAW).as_posix()
        if not r.startswith("H2-SimNet-clean/"):
            continue
        q = RAW / r.replace("H2-SimNet-clean/", "", 1)
        if not q.exists():
            continue
        a, b = pd.read_parquet(p), pd.read_parquet(q)
        if a.shape != b.shape:
            cmp.append({"clean_file": rel(p), "other_file": rel(q), "same_shape": False}); continue
        d = b[SENS].to_numpy(float) - a[SENS].to_numpy(float)
        rng = a[SENS].max() - a[SENS].min()
        resid_sd = d.std(axis=0)
        labs_equal = all((a[c] == b[c]).all() for c in LAB if c in a and c in b)
        lag1 = [np.corrcoef(d[:-1, j], d[1:, j])[0, 1] if d[:, j].std() > 0 else np.nan for j in range(d.shape[1])]
        cmp.append({
            "clean_file": rel(p), "other_file": rel(q), "same_shape": True,
            "labels_identical": labs_equal,
            "max_abs_diff": float(np.abs(d).max()),
            "mean_diff_max_abs_over_channels": float(np.abs(d.mean(axis=0)).max()),
            "resid_sd_over_range_median": float(np.nanmedian(resid_sd / np.where(rng.to_numpy() > 0, rng.to_numpy(), np.nan))),
            "resid_sd_over_range_max": float(np.nanmax(resid_sd / np.where(rng.to_numpy() > 0, rng.to_numpy(), np.nan))),
            "resid_lag1_autocorr_median": float(np.nanmedian(lag1)),
            "clean_is_smoother": bool(np.abs(np.diff(a[SENS].to_numpy(float), axis=0)).mean()
                                      < np.abs(np.diff(b[SENS].to_numpy(float), axis=0)).mean()),
        })
    pd.DataFrame(cmp).to_csv(OUT / "CROSS_TREE_COMPARISON.csv", index=False, lineterminator="\n")

    # ---- 3. shared pre-event segments within the clean tree (simulation ancestry)
    clean = [p for p in pqs if "H2-SimNet-clean" in p.as_posix()]
    data = {rel(p): pd.read_parquet(p) for p in clean}
    ons = {k: onset_row(v) for k, v in data.items()}
    shared = []
    for a, b in combinations(sorted(data), 2):
        A, B = data[a], data[b]
        if len(A) != len(B):
            continue
        oa, ob = ons[a], ons[b]
        cut = min(x for x in (oa, ob, len(A)) if x is not None)
        if cut < 10:
            continue
        d = np.abs(A[SENS].to_numpy(float)[:cut] - B[SENS].to_numpy(float)[:cut]).max()
        full = np.abs(A[SENS].to_numpy(float) - B[SENS].to_numpy(float)).max()
        shared.append({"file_a": a, "file_b": b, "rows_compared_pre_event": cut,
                       "max_abs_diff_pre_event": float(d), "identical_pre_event": bool(d == 0.0),
                       "max_abs_diff_full": float(full)})
    pd.DataFrame(shared).to_csv(OUT / "PRE_EVENT_SHARED_SEGMENTS.csv", index=False, lineterminator="\n")

    # ---- 4. label consistency per file (row level)
    lc = []
    for k, df in data.items():
        if "label_anomaly" not in df:
            continue
        L = df[LAB].to_numpy()
        leak, cf, cd, an = (df[c].to_numpy() == 1 for c in ("Leak", "CompressorFault", "CompressorDelay", "label_anomaly"))
        loc_any = df[["leak_G3", "leak_G4", "leak_G5", "leak_G6"]].to_numpy().max(axis=1) == 1
        lc.append({
            "file": k,
            "rows_anomaly": int(an.sum()),
            "rows_anomaly_without_type": int((an & ~(leak | cf | cd)).sum()),
            "rows_type_without_anomaly": int((~an & (leak | cf | cd)).sum()),
            "rows_leak_without_location": int((leak & ~loc_any).sum()),
            "rows_location_without_leak": int((~leak & loc_any).sum()),
            "rows_multi_type": int(((leak.astype(int) + cf + cd) > 1).sum()),
            "first_onset_row": onset_row(df),
            "active_cols": ";".join(c for c in LAB if (df[c] == 1).any()),
            "labels_nondecreasing": bool((np.diff(L, axis=0) >= 0).all()),
        })
    pd.DataFrame(lc).to_csv(OUT / "LABEL_CONSISTENCY.csv", index=False, lineterminator="\n")
    print("done", len(st), len(cmp), len(shared), len(lc))


if __name__ == "__main__":
    main()
