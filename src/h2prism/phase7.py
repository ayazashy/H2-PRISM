"""Execute the Phase 7 archive lineage and benchmark availability gates."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd

from .data.loader import RAW_DATASET_DIR, WORKSPACE_ROOT, load_scenario
from .phase2 import DATA_HASH, MODEL_DIR, PARQUET, SID, checked_file
from .phase3 import digest, write_record
from .phase5 import CSV_HASH, clock_index, independent_eligibility
from .phase6 import PAPER, execution_gate, external_candidates

CLEAN_CSV = "H2-SimNet-clean/normality-scenarios/csv/normality_gest_center.csv"
TOP_CSV = "normality-scenarios/csv/normality_gest_center.csv"
CLEAN_HASH = "e5b58b7c1ab4a8304df8cdc2e8493a02996387b772dd2b7119f94dbdef623ddf"
TOP_HASH = "4c93e21aa9c513f29b9e731f13f5a01628ffcf471c8ffd45dbe8566fde9adccb"


def read_csv(path):
    frame = pd.read_csv(path, dtype={"Timestamp": str}).set_index("Timestamp")
    frame.index = clock_index(frame.index)
    return frame


def archive_lineage():
    root = RAW_DATASET_DIR
    raw_path = checked_file(root / MODEL_DIR / "normality_gest_center.csv", CSV_HASH)
    solver_alias = checked_file(raw_path.parent.parent / raw_path.name, CSV_HASH)
    clean_path = checked_file(root / CLEAN_CSV, CLEAN_HASH)
    parquet_path = checked_file(root / PARQUET, DATA_HASH)
    top_path = checked_file(root / TOP_CSV, TOP_HASH)
    raw, clean, top = map(read_csv, (raw_path, clean_path, top_path))
    parquet = load_scenario(parquet_path)
    if parquet.index.name != "Timestamp":
        raise ValueError("Parquet clock missing")
    parquet.index = clock_index(parquet.index)
    channels = list(SID)
    if list(raw.columns) != channels or any(not set(channels) <= set(f) for f in (clean, parquet, top)):
        raise ValueError("unexpected source channel mapping")
    if not clean.index.equals(parquet.index) or not top.index.equals(parquet.index):
        raise ValueError("released grids differ")
    common = raw.index.intersection(parquet.index)
    if len(common) < 2:
        raise ValueError("insufficient exact shared archive timestamps")
    left, right = raw.loc[common, channels], parquet.loc[common, channels]
    residual = right - left
    cdelta = parquet[channels] - clean[channels]
    tdelta = parquet[channels] - top[channels]
    if not all(np.isfinite(f.to_numpy()).all() for f in (residual, cdelta, tdelta)):
        raise ValueError("nonfinite archive comparison")
    # Numerical threshold is for testing serialization/identity, not physical uncertainty.
    tol = 1e-9
    clean_same = float(cdelta.abs().to_numpy().max()) <= tol
    on_same_clock = float(residual.abs().to_numpy().max()) <= tol
    offsets = {name: float(residual[name].max() - residual[name].min()) for name in channels}
    scales = {name: {str(factor): float((right[name] - factor * left[name]).abs().max())
                     for factor in (0.001, 1, 1000)} for name in ("MFS1", "MFS2", "MFS3")}
    remap = {}
    for name in ("PS1", "MFS3"):
        family = [ch for ch in channels if ch.startswith("PS" if name == "PS1" else "MFS")]
        remap[name] = {ch: float((right[name] - left[ch]).abs().max()) for ch in family}
    records = []

    def add(hypothesis, required, available, test, outcome):
        records.append(dict(hypothesis=hypothesis, required=required, available=available, test=test, outcome=outcome))

    add("Different runs", "Runtime identifiers, shared run hashes",
        "Archived aliases share bytes; Parquet lacks run identifier", "Compared aliases and clocks", "UNRESOLVED")
    add("Different inputs or initial states", "Effective state and boundary histories",
        "Static model and launcher only", "Determined runtime histories absent", "UNRESOLVED")
    add("Model-version change", "Pin both generating models",
        "One pinned Center SLX; paper describes a distinct solver configuration",
        "Compared available provenance, not runnable model versions", "UNRESOLVED")
    add("Additional filtering or processing", "Versioned production code and intermediate inputs",
        "Author reports linear resampling; no pinned trace from archived CSV",
        "Exact shared-knot comparison rejects linear resampling alone", "UNRESOLVED")
    add("Constant pressure reference offset alone", "Common pressure basis or constant offset",
        "Same documented MPa channel units", "Measured residual range rather than fitting an offset",
        "REJECTED" if offsets["PS1"] > tol else "UNRESOLVED")
    add("Simple flow metric-prefix conversion alone", "Source and release converter unit provenance",
        "Release denotes kg/s; runtime inherited units absent",
        "Tested factors 0.001, 1, 1000 at shared timestamps without fitting",
        "REJECTED" if min(scales["MFS3"].values()) > tol else "UNRESOLVED")
    add("Pure traced-channel remap alone", "Versioned channel map",
        "Thirteen source-backed channels", "Tested every within-quantity source column for PS1 and MFS3",
        "REJECTED" if any(min(values.values()) > tol for values in remap.values()) else "UNRESOLVED")
    add("Startup or solver state", "Runtime logs and effective settings",
        "Archived launcher fixed-step 0.8 s; authors report variable step and tolerance 1e-3",
        "Compared documented solver configurations", "UNRESOLVED")
    add("Published resampling alone", "Exact clocks and interpolation rule",
        "Archived and release clocks; publication documents linear interpolation to 1 s",
        "Linear interpolation preserves the values at the 5,000 shared knots",
        "REJECTED" if not on_same_clock else "UNRESOLVED")
    add("Clean CSV-to-Parquet serialization causes discrepancy", "Clean release CSV and Parquet",
        "Both hash-pinned and on the same stored grid", "Compared all 13 traced channels at every release timestamp",
        "REJECTED" if clean_same and not on_same_clock else "UNRESOLVED")
    add("Clean release CSV and Parquet are numerically equivalent on traced channels",
        "Hash-pinned clean files, same clock and channel mapping", "Both archive files",
        "Compared full traced channel grid within 1e-9 native units", "CONFIRMED" if clean_same else "REJECTED")
    return {
        "status": "UNRESOLVED_EXACT_SOURCE_TO_RELEASE_LINEAGE",
        "tier": "T3_ARCHIVAL_TRACE_ONLY", "fresh_source_reproduction": False,
        "hashes": {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in (raw_path, solver_alias, clean_path, parquet_path, top_path)},
        "published_processing": PAPER, "numeric_identity_tolerance_native_units": tol,
        "shared_timestamps": len(common), "clean_release_timestamps": len(parquet),
        "clean_csv_vs_parquet_max": float(cdelta.abs().to_numpy().max()),
        "top_level_csv_vs_clean_parquet_max_by_channel": {ch: float(tdelta[ch].abs().max()) for ch in channels},
        "independent_source_minus_release_sign": "release minus archived solver",
        "units": {ch: "MPa (SLX pressure converters)" if ch.startswith("PS")
                  else "kg/s (release metadata; source converter inheritance unverified)" for ch in channels},
        "archival_residual_peaks": {ch: {"signed": float(residual[ch].loc[residual[ch].abs().idxmax()]),
                                         "time_s": str(residual[ch].abs().idxmax())} for ch in channels},
        "constant_offset_residual_ranges": offsets, "flow_factors_max_residual": scales,
        "candidate_remap_max_residual": remap, "hypotheses": records,
    }


def qualification():
    options = external_candidates()
    decisions = ("ACCESS_REQUIRED", "CONDITIONALLY_USABLE", "CONDITIONALLY_USABLE")
    for option, decision in zip(options, decisions):
        option.update({"decision": decision, "ground_truth_available_for_ingestion": False,
                       "physics_compatible": False, "uncertainty_available": False,
                       "sensor_compatibility_for_certification": "UNVERIFIED",
                       "independent_unit": None, "diagnostic_eligible": False, "localization_eligible": False,
                       "evidence_review": "Publication and repository metadata only; no qualified raw run ingested"})
    options[0]["published_instrumentation"] = {
        "gas": "Hydrogen and nitrogen test series", "sensor_ids": ["PT1–PT6", "FT1–FT2"],
        "positions": "Inline sensor and two controlled orifice positions shown in rig schematic",
        "sensor_models": "PT1 RS PRO pressure transducer; PT2?PT6 Kulite pressure transducers; inlet/outlet Coriolis meters",
        "published_conditions": "Pressure traces shown at 4 and 10 bar initial pressure; both leak sites documented",
        "clock_and_calibration": "Article reports a PT1 error specification. Per-run clocks, sampling settings and "
                                 "calibration records still required for defensible bounds",
        "published_sampling": "10 kHz reported for the localization example; per-run files not obtained",
        "repeat_units": "Run independence not verified without acquisition and restart records",
    }
    return {"candidate_register": options, "eligible_physical_families": 0,
            "independent_analysis_executed": False, "independent_metrics": None,
            "verdict": "BLOCKED_BY_EXTERNAL_EVIDENCE"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase6-probe-log", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = {
        "schema": "phase7/1", "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=WORKSPACE_ROOT, text=True).strip(),
        "archive": archive_lineage(),
        "matlab": {"last_execution": execution_gate(args.phase6_probe_log, 1),
                   "new_launch": False, "new_authorized_startup_evidence": False,
                   "gate": "NO_GO_PENDING_AUTHORIZED_TOOLBOX_CHECKOUT"},
        "external": qualification(), "archive_evaluation": independent_eligibility(),
        "prior_matched_comparator": "Phase 4 joint set-membership equivalence retained; no independent baseline results",
    }
    report["sha256"] = digest(report)
    write_record(args.output, report)


if __name__ == "__main__":
    main()
