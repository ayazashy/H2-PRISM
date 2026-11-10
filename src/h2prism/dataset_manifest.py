"""
H2-PRISM portable, deterministic canonical dataset manifest (CANDIDATE_NOT_APPROVED).

STATUS: IMPLEMENTED + TESTED. This module produces *candidate* artifacts for review by
Yazan (dataset authority), Faisal (technical) and Ahmed (scientific). It never writes
to the raw data and never decides which realization is used for modelling.

Determinism and portability guarantees
* All paths are normalised to POSIX form relative to the dataset parent directory
  (``norm_path``); backslashes, ``./`` prefixes and duplicate separators are removed.
* Every collection is sorted by normalised path / key, never by traversal order.
* Scenario identity comes from (topology, segment directory, run stem) parsed from the
  normalised path; files whose location is not informative (e.g. archive-root copies)
  are resolved ONLY by exact content identity (SHA-256 of bytes) to a located file.
* Sensor content fingerprints are computed on the sensor columns in canonical order,
  so column order and CSV-vs-Parquet storage do not change them; numerical
  equivalence is decided with an explicit tolerance, not by fingerprint alone.

Realization types (one simulated run can have several realizations):
  CLEAN_SIMULATION            H2-SimNet-clean tree, no added noise
  NOISE_ADDED_RELEASE         anomalous-/normality-scenarios trees (dataset ReadME: Gaussian noise added)
  NOISE_ADDED_VARIANT         ``*_noisy`` files (same run + noise, verified against the clean file)
  RAW_SOLVER_EXPORT           MATLAB_SIMSCAPE_Simulation CSVs (variable step, subset of channels, no labels)
  MISFILED_COPY               file whose path does not identify a scenario but whose bytes equal a located file
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

SENSORS: Tuple[str, ...] = tuple(f"PS{i}" for i in range(1, 13)) + tuple(f"MFS{i}" for i in range(1, 5))
LABELS: Tuple[str, ...] = ("label_anomaly", "Leak", "CompressorFault", "CompressorDelay",
                           "leak_G3", "leak_G4", "leak_G5", "leak_G6")
LOCATIONS: Tuple[str, ...] = ("leak_G3", "leak_G4", "leak_G5", "leak_G6")
TOPOLOGY_CODES = {"cent": "Center", "center": "Center", "down": "Downstream", "up": "Upstream"}
STATUS = "CANDIDATE_NOT_APPROVED"

CLEAN, RELEASE, NOISY_VARIANT, SOLVER, MISFILED = (
    "CLEAN_SIMULATION", "NOISE_ADDED_RELEASE", "NOISE_ADDED_VARIANT", "RAW_SOLVER_EXPORT", "MISFILED_COPY")


# ----------------------------------------------------------------------------- paths
def norm_path(p) -> str:
    """Normalise a path string to POSIX form (no backslashes, no ./, no duplicate /)."""
    s = str(p).replace("\\", "/")
    s = re.sub(r"/+", "/", s)
    while s.startswith("./"):
        s = s[2:]
    return str(PurePosixPath(s))


def discover_files(dataset_parent: Path, suffixes: Sequence[str] = (".csv", ".parquet")) -> List[str]:
    """Return normalised relative paths of all data files, sorted (traversal-order independent)."""
    root = Path(dataset_parent)
    found = [norm_path(p.relative_to(root)) for p in root.rglob("*") if p.is_file() and p.suffix in suffixes]
    return sorted(set(found))


@dataclass(frozen=True)
class Location:
    tree: str           # clean | release | solver_export
    fmt: str            # csv | parquet
    topology: str       # Center | Downstream | Upstream | UNLOCATED
    segment_dir: str    # start_transient | assestment_transient | constant_segment | normal_run | UNLOCATED
    stem: str
    run_stem: str       # stem without the _noisy suffix
    noisy_suffix: bool


def parse_location(rel: str) -> Location:
    r = norm_path(rel)
    fmt = r.rsplit(".", 1)[-1].lower()
    tree = ("clean" if "/H2-SimNet-clean/" in f"/{r}" else
            "solver_export" if "/MATLAB_SIMSCAPE_Simulation/" in f"/{r}" else "release")
    stem = PurePosixPath(r).stem
    noisy = stem.endswith("_noisy")
    run_stem = stem[: -len("_noisy")] if noisy else stem
    m = re.search(r"anom_gest(cent|center|down|up)/([A-Za-z_]+)/[^/]+$", r)
    if m:
        return Location(tree, fmt, TOPOLOGY_CODES[m.group(1)], m.group(2), stem, run_stem, noisy)
    m = re.search(r"normality_gest_(center|cent|down|up)$", stem)
    if m:
        return Location(tree, fmt, TOPOLOGY_CODES[m.group(1)], "normal_run", stem, "normality", noisy)
    return Location(tree, fmt, "UNLOCATED", "UNLOCATED", stem, run_stem, noisy)


def scenario_id(topology: str, segment_dir: str, run_stem: str) -> str:
    return f"CS_{topology.upper()}_{segment_dir.upper()}_{run_stem.upper()}"


# ----------------------------------------------------------------------------- content
def sha256_bytes(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read_frame(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path) if str(path).endswith(".parquet") else pd.read_csv(path)


def time_axis_info(df: pd.DataFrame) -> Dict[str, object]:
    """Locate the time axis: a ``Timestamp`` column or a stored index named ``Timestamp``."""
    if "Timestamp" in df.columns:
        t, src = pd.to_numeric(df["Timestamp"], errors="coerce").to_numpy(float), "COLUMN_Timestamp"
    elif df.index.name == "Timestamp":
        t, src = np.asarray(df.index, dtype=float), "INDEX_Timestamp"
    else:
        return {"time_source": "NONE", "dt_unique": "", "t_start": np.nan, "t_end": np.nan}
    d = np.unique(np.round(np.diff(t), 9)) if len(t) > 1 else np.array([])
    return {"time_source": src, "dt_unique": ";".join(f"{x:g}" for x in d[:5]),
            "t_start": float(t[0]) if len(t) else np.nan, "t_end": float(t[-1]) if len(t) else np.nan}


def sensor_matrix(df: pd.DataFrame) -> Tuple[List[str], np.ndarray]:
    cols = [c for c in SENSORS if c in df.columns]  # canonical order, independent of file column order
    return cols, df[cols].to_numpy(dtype=float)


def sensor_fingerprint(df: pd.DataFrame, decimals: int = 6) -> str:
    cols, X = sensor_matrix(df)
    h = hashlib.sha256(("|".join(cols) + f"|{X.shape}").encode())
    h.update(np.ascontiguousarray(np.round(X, decimals)).tobytes())
    return h.hexdigest()


def label_summary(df: pd.DataFrame, t: Optional[np.ndarray] = None) -> Dict[str, object]:
    """Exact row-level label facts (raw labels are reported, never modified)."""
    if "label_anomaly" not in df.columns:
        return {"has_labels": False}
    out: Dict[str, object] = {"has_labels": True}
    tt = t if t is not None else np.arange(len(df), dtype=float)
    active = []
    for c in LABELS:
        v = df[c].to_numpy() == 1 if c in df.columns else np.zeros(len(df), bool)
        if v.any():
            idx = np.flatnonzero(v)
            active.append(c)
            out[f"{c}__onset_s"] = float(tt[idx[0]])
            out[f"{c}__last_active_s"] = float(tt[idx[-1]])
            out[f"{c}__returns_to_zero"] = bool(idx[-1] < len(df) - 1)
    out["active_label_columns"] = ";".join(active)
    leak = df["Leak"].to_numpy() == 1
    cf = df["CompressorFault"].to_numpy() == 1
    cd = df["CompressorDelay"].to_numpy() == 1
    loc = df[list(LOCATIONS)].to_numpy() == 1
    out["event_types"] = ";".join(n for n, v in (("LEAK", leak), ("COMPRESSOR_FAULT", cf), ("COMPRESSOR_DELAY", cd)) if v.any())
    out["leak_locations"] = ";".join(c.replace("leak_", "") for c, v in zip(LOCATIONS, loc.any(axis=0)) if v)
    out["rows_location_without_leak"] = int((loc.any(axis=1) & ~leak).sum())
    out["rows_leak_without_location"] = int((leak & ~loc.any(axis=1)).sum())
    out["rows_multiple_event_types"] = int(((leak.astype(int) + cf + cd) > 1).sum())
    out["rows_anomaly_flag_mismatch"] = int(((df["label_anomaly"].to_numpy() == 1) != (leak | cf | cd | loc.any(axis=1))).sum())
    return out


# ----------------------------------------------------------------------------- inventory
def build_file_inventory(dataset_parent: Path, files: Optional[Iterable[str]] = None) -> pd.DataFrame:
    """One row per data file with location, realization hints, checksums, time and label facts.

    ``files`` may be given in any order and with any separator; output is sorted and identical.
    """
    root = Path(dataset_parent)
    rels = sorted({norm_path(f) for f in (files if files is not None else discover_files(root))})
    rows = []
    for r in rels:
        p = root / r
        loc = parse_location(r)
        df = read_frame(p)
        ti = time_axis_info(df)
        t = None
        if ti["time_source"] == "INDEX_Timestamp":
            t = np.asarray(df.index, dtype=float)
        elif ti["time_source"] == "COLUMN_Timestamp":
            t = pd.to_numeric(df["Timestamp"], errors="coerce").to_numpy(float)
        cols, _ = sensor_matrix(df)
        rows.append({
            "file": r, "format": loc.fmt, "tree": loc.tree, "topology_from_path": loc.topology,
            "segment_dir": loc.segment_dir, "stem": loc.stem, "run_stem": loc.run_stem,
            "noisy_suffix": loc.noisy_suffix, "sha256": sha256_bytes(p), "n_rows": len(df),
            "sensor_columns_present": len(cols), "missing_sensors": ";".join(c for c in SENSORS if c not in cols),
            "sensor_fingerprint_6dp": sensor_fingerprint(df), **ti, **label_summary(df, t),
        })
    inv = pd.DataFrame(rows)
    return inv.sort_values("file", kind="mergesort").reset_index(drop=True)


def assign_scenarios(inv: pd.DataFrame) -> pd.DataFrame:
    """Add candidate Scenario_ID, realization type and resolution evidence (deterministic)."""
    inv = inv.copy()
    located = inv[inv["topology_from_path"] != "UNLOCATED"]
    by_sha: Dict[str, List[str]] = {}
    for _, r in located.sort_values("file").iterrows():
        by_sha.setdefault(r["sha256"], []).append(r["file"])
    sid, real, evid = [], [], []
    loc_of = {r["file"]: (r["topology_from_path"], r["segment_dir"], r["run_stem"]) for _, r in located.iterrows()}
    for _, r in inv.iterrows():
        if r["topology_from_path"] == "UNLOCATED":
            twins = by_sha.get(r["sha256"], [])
            keys = sorted({loc_of[f] for f in twins})
            if len(keys) == 1:
                sid.append(scenario_id(*keys[0]))
                real.append(MISFILED)
                evid.append(f"EXACT_BYTES_EQUAL:{twins[0]}")
            else:
                sid.append("UNRESOLVED_" + r["stem"].upper())
                real.append(MISFILED)
                evid.append("NO_UNIQUE_BYTE_IDENTICAL_LOCATED_FILE" if not keys else f"AMBIGUOUS:{keys}")
            continue
        sid.append(scenario_id(r["topology_from_path"], r["segment_dir"], r["run_stem"]))
        if r["tree"] == "solver_export":
            real.append(SOLVER)
        elif r["noisy_suffix"]:
            real.append(NOISY_VARIANT)
        elif r["tree"] == "clean":
            real.append(CLEAN)
        else:
            real.append(RELEASE)
        evid.append("PATH_LOCATION")
    inv["candidate_Scenario_ID"] = sid
    inv["realization_type"] = real
    inv["scenario_resolution_evidence"] = evid
    return inv


def canonical_file(inv: pd.DataFrame, scenario: str, realization: str) -> Optional[str]:
    """Deterministic canonical file for one realization: Parquet before CSV (Parquet stores the
    Timestamp index and labels; the CSV of the same tree is numerically equivalent), then path."""
    c = inv[(inv["candidate_Scenario_ID"] == scenario) & (inv["realization_type"] == realization)]
    if c.empty:
        return None
    c = c.assign(_rank=c["format"].map({"parquet": 0, "csv": 1}).fillna(2))
    return c.sort_values(["_rank", "file"], kind="mergesort").iloc[0]["file"]


# ----------------------------------------------------------------------------- relationships
def compare_realizations(a: pd.DataFrame, b: pd.DataFrame, atol: float = 1e-9) -> Dict[str, object]:
    """Numerical comparison of two realizations of (supposedly) one run."""
    ca, Xa = sensor_matrix(a)
    cb, Xb = sensor_matrix(b)
    common = [c for c in ca if c in cb]
    if len(a) != len(b) or not common:
        return {"comparable": False}
    Xa = a[common].to_numpy(float)
    Xb = b[common].to_numpy(float)
    d = Xb - Xa
    labs = [c for c in LABELS if c in a.columns and c in b.columns]
    lag1 = [np.corrcoef(d[:-1, j], d[1:, j])[0, 1] for j in range(d.shape[1]) if d[:, j].std() > 0]
    return {
        "comparable": True,
        "numerically_equal_atol": bool(np.allclose(Xa, Xb, atol=atol, rtol=0)),
        "labels_identical": bool(all((a[c].to_numpy() == b[c].to_numpy()).all() for c in labs)) if labs else None,
        "max_abs_diff": float(np.abs(d).max()),
        "max_abs_mean_diff": float(np.abs(d.mean(axis=0)).max()),
        "median_residual_sd": float(np.median(d.std(axis=0))),
        "median_lag1_autocorr": float(np.median(lag1)) if lag1 else float("nan"),
    }


def shared_pre_event_rows(a: pd.DataFrame, b: pd.DataFrame) -> Tuple[int, int, float]:
    """(rows compared before the earlier onset, length of identical leading block, max |diff| pre-event)."""
    def onset(df):
        if "label_anomaly" not in df.columns:
            return len(df)
        idx = np.flatnonzero(df["label_anomaly"].to_numpy() == 1)
        return int(idx[0]) if idx.size else len(df)
    if len(a) != len(b):
        return 0, 0, float("nan")
    cut = min(onset(a), onset(b))
    _, Xa = sensor_matrix(a)
    _, Xb = sensor_matrix(b)
    if cut == 0:
        return 0, 0, float("nan")
    eq_rows = np.all(Xa[:cut] == Xb[:cut], axis=1)
    lead = int(np.argmin(eq_rows)) if not eq_rows.all() else cut
    return cut, lead, float(np.abs(Xa[:cut] - Xb[:cut]).max())


def union_find(nodes: Iterable[str], edges: Iterable[Tuple[str, str]]) -> Dict[str, str]:
    parent = {n: n for n in sorted(set(nodes))}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)
    return {n: find(n) for n in parent}


def weak_strong_partner(sid: str) -> Optional[str]:
    m = re.match(r"(.+)_(WEAK|STRONG)$", sid)
    if not m:
        return None
    return m.group(1) + ("_STRONG" if m.group(2) == "WEAK" else "_WEAK")
