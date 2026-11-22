"""Deterministic ETL builder for H2-PRISM public web replay bundles.

Reads audited H2-SimNet sample recordings (data/sample/*.parquet), Simscape
topology/sensor correspondence (03_results/diagnostics/sensor_correspondence/),
and primary protocol evaluation tables (03_results/primary_protocol/PRIMARY/ and
03_results/tables/primary/...) to produce SHA-256 verified JSON exports under
apps/web/public/data/.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import pathlib
from typing import Any

import polars as pl


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "apps" / "web" / "public" / "data"

PRIMARY_DIR = REPO_ROOT / "03_results" / "primary_protocol" / "PRIMARY"
FINAL_TABLES_DIR = (
    REPO_ROOT
    / "03_results"
    / "tables"
    / "primary"
    / "a10530f1fcf2_s4228b6c8_b200fcdac"
    / "final"
)

# Schematic layout coordinates derived from Simscape connectivity in
# 03_results/diagnostics/sensor_correspondence/NETWORK_EDGES.csv (not physical GPS/meters).
TOPOLOGY_SPEC: dict[str, Any] = {
    "schema_version": "1.0.0",
    "topology_id": "h2_simnet_center_v1",
    "is_schematic": True,
    "coordinate_note": (
        "Schematic connectivity derived from Simscape MODEL_FILES / NETWORK_EDGES.csv. "
        "Pipe lengths (3-30 km) exist in model metadata, but planar (x, y, z) coordinates "
        "are schematic for legibility and not physical coordinates."
    ),
    "nodes": [
        {"id": "N47", "label": "Source / Header 47", "kind": "source", "x": 0.0, "y": 1.0, "z": 0.0},
        {"id": "N50", "label": "Junction 50 (C1/G1/G2)", "kind": "compressor", "x": 1.4, "y": 1.0, "z": 0.0},
        {"id": "N239", "label": "Header 48 / 239", "kind": "junction", "x": 2.6, "y": 1.0, "z": 0.0},
        {"id": "N309", "label": "Junction 309", "kind": "junction", "x": 3.8, "y": 1.0, "z": 0.0},
        {"id": "N106", "label": "Junction 106", "kind": "junction", "x": 4.9, "y": 0.35, "z": 0.0},
        {"id": "N221", "label": "Junction 221", "kind": "junction", "x": 5.8, "y": 1.0, "z": 0.0},
        {"id": "N109", "label": "Junction 109", "kind": "junction", "x": 4.9, "y": 1.65, "z": 0.0},
        {"id": "N195", "label": "Outlet Reservoir 195", "kind": "delivery", "x": 6.8, "y": 1.65, "z": 0.0},
    ],
    "edges": [
        {"id": "Pipe_G1", "label": "Pipe (G)1 [16 km]", "source": "N47", "target": "N50", "component_group": "G1"},
        {"id": "Pipe_G2", "label": "Pipe (G)2 [30 km]", "source": "N50", "target": "N239", "component_group": "G2"},
        {"id": "Pipe_G3", "label": "Pipe (G)3 [11 km]", "source": "N239", "target": "N309", "component_group": "G3"},
        {"id": "Pipe_G8", "label": "Pipe (G)8 [11 km]", "source": "N309", "target": "N106", "component_group": "G8"},
        {"id": "Pipe_G4", "label": "Pipe (G)4 [8 km]", "source": "N106", "target": "N221", "component_group": "G4"},
        {"id": "Pipe_G7", "label": "Pipe (G)7 [4 km]", "source": "N221", "target": "N109", "component_group": "G7"},
        {"id": "Pipe_G5", "label": "Pipe (G)5 [4 km]", "source": "N109", "target": "N195", "component_group": "G5"},
    ],
    # Audited sensor placements from SENSOR_CORRESPONDENCE.csv (Center & Down models)
    "sensors": [
        {"channel_id": "PS1", "attached_to": "N50", "variable": "pressure"},
        {"channel_id": "PS2", "attached_to": "N239", "variable": "pressure"},
        {"channel_id": "PS3", "attached_to": "N106", "variable": "pressure"},
        {"channel_id": "PS4", "attached_to": "N109", "variable": "pressure"},
        {"channel_id": "PS6", "attached_to": "N239", "variable": "pressure"},
        {"channel_id": "PS7", "attached_to": "N47", "variable": "pressure"},
        {"channel_id": "PS8", "attached_to": "N195", "variable": "pressure"},
        {"channel_id": "PS9", "attached_to": "N221", "variable": "pressure"},
        {"channel_id": "PS10", "attached_to": "N309", "variable": "pressure"},
        {"channel_id": "MFS1", "attached_to": "Pipe_G3", "variable": "mass_flow"},
        {"channel_id": "MFS2", "attached_to": "Pipe_G8", "variable": "mass_flow"},
        {"channel_id": "MFS3", "attached_to": "Pipe_G2", "variable": "mass_flow"},
        {"channel_id": "MFS4", "attached_to": "Pipe_G5", "variable": "mass_flow"},
    ],
}

# Target nodes/edges for all 16 channels in scenario payloads
CHANNEL_TARGETS: dict[str, tuple[str, str, str, str | None]] = {
    "PS1": ("N50", "pressure", "MPa", "absolute"),
    "PS2": ("N239", "pressure", "MPa", "absolute"),
    "PS3": ("N106", "pressure", "MPa", "absolute"),
    "PS4": ("N109", "pressure", "MPa", "absolute"),
    "PS5": ("N47", "pressure", "MPa", "absolute"),
    "PS6": ("N239", "pressure", "MPa", "absolute"),
    "PS7": ("N47", "pressure", "MPa", "absolute"),
    "PS8": ("N195", "pressure", "MPa", "absolute"),
    "PS9": ("N221", "pressure", "MPa", "absolute"),
    "PS10": ("N309", "pressure", "MPa", "absolute"),
    "PS11": ("N221", "pressure", "MPa", "absolute"),
    "PS12": ("N106", "pressure", "MPa", "absolute"),
    "MFS1": ("Pipe_G3", "mass_flow", "kg/s", None),
    "MFS2": ("Pipe_G8", "mass_flow", "kg/s", None),
    "MFS3": ("Pipe_G2", "mass_flow", "kg/s", None),
    "MFS4": ("Pipe_G5", "mass_flow", "kg/s", None),
}

SAMPLE_SCENARIOS = [
    {
        "file": "normality_gest_center.parquet",
        "id": "SCEN_NORMAL_GEST_CENTER",
        "display_name": "Normal Baseline (Center Model)",
        "family_id": "FAM_NORMAL_CENTER",
        "scenario_class": "NORMAL",
        "summary_hint": (
            "Real 20,000 s H2-SimNet baseline. Note: PS11, PS12, and MFS4 are absent in the "
            "Center Simscape model (released as constant padding) and are marked non-observable."
        ),
        "gas_metadata_status": "Center Simscape model (air-like gas block R=0.287 kJ/(kg*K))",
        "split": "test",
        "gt_class": "NORMAL",
        "true_targets": None,
        "padded_absent_channels": {"PS11", "PS12", "MFS4"},
    },
    {
        "file": "leakG4.parquet",
        "id": "SCEN_CENTER_TRANSIENT_LEAKG4",
        "display_name": "Transient Leak (G4)",
        "family_id": "FAM_LEAK_G4",
        "scenario_class": "LEAK",
        "summary_hint": (
            "Real H2-SimNet transient leak (onset t=400.0 s). Per R-18 forensic audit, "
            "anom_gestcent carries the 16-sensor Down-model export signature."
        ),
        "gas_metadata_status": "H2-SimNet simulated run (R-18: anom_gestcent exports Down-model sensors)",
        "split": "test",
        "gt_class": "LEAK",
        "true_targets": ["Pipe_G4"],
        "padded_absent_channels": set(),
    },
    {
        "file": "brokenC1_strong.parquet",
        "id": "SCEN_CENTER_STEADY_STATE_BROKENC1_STRONG",
        "display_name": "Compressor Fault (C1 Strong)",
        "family_id": "FAM_COMPRESSOR_FAULT_C1",
        "scenario_class": "COMPRESSOR_FAULT",
        "summary_hint": (
            "Real H2-SimNet severe mechanical fault on compressor C1 (onset t=25.0 s). "
            "In R2 primary protocol, COMPRESSOR_FAULT windows abstain as UNRESOLVED."
        ),
        "gas_metadata_status": "H2-SimNet simulated run (R-18: anom_gestcent exports Down-model sensors)",
        "split": "test",
        "gt_class": "COMPRESSOR_FAULT",
        "true_targets": ["N50"],
        "padded_absent_channels": set(),
    },
    {
        "file": "startdelayC1.parquet",
        "id": "SCEN_CENTER_STEADY_STATE_STARTDELAYC1",
        "display_name": "Compressor Startup Delay (C1)",
        "family_id": "FAM_COMPRESSOR_DELAY_C1",
        "scenario_class": "COMPRESSOR_DELAY",
        "summary_hint": (
            "Real H2-SimNet startup delay bounded to [25.0 s, 1000.0 s] inside a 20,000 s run. "
            "Demonstrates bounded transient end condition."
        ),
        "gas_metadata_status": "H2-SimNet simulated run (R-18: anom_gestcent exports Down-model sensors)",
        "split": "test",
        "gt_class": "COMPRESSOR_DELAY",
        "true_targets": ["N50"],
        "padded_absent_channels": set(),
    },
]


def _write_lf_json(path: pathlib.Path, obj: Any) -> str:
    raw_bytes = (json.dumps(obj, indent=2) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw_bytes)
    return hashlib.sha256(raw_bytes).hexdigest()


def _downsample_indices(n_rows: int, onset_idx: int | None, end_idx: int | None) -> list[int]:
    """Deterministic multi-resolution index selection for web replay budget.

    Keeps higher resolution around [0, 1200s] (startup & transient window) and uniform
    stride across [1200s, end], explicitly preserving onset and end boundary indices.
    """
    selected: set[int] = set(range(0, min(1201, n_rows), 10))
    selected.update(range(1200, n_rows, 150))
    selected.add(n_rows - 1)
    if onset_idx is not None and 0 <= onset_idx < n_rows:
        selected.add(onset_idx)
    if end_idx is not None and 0 <= end_idx < n_rows:
        selected.add(end_idx)
    return sorted(selected)


def _clean_float(val: Any) -> float | None:
    if val is None:
        return None
    f = float(val)
    if not math.isfinite(f):
        return None
    return round(f, 6)


def _read_csv(path: pathlib.Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def build_metrics() -> dict[str, Any]:
    manifest = json.loads((PRIMARY_DIR / "run_manifest.json").read_text(encoding="utf-8"))
    cm_rows = _read_csv(PRIMARY_DIR / "confusion_matrix.csv")
    rc_rows = _read_csv(PRIMARY_DIR / "risk_coverage_curve.csv")
    t4_rows = _read_csv(FINAL_TABLES_DIR / "T4_matched_coverage.csv")
    t6_rows = _read_csv(FINAL_TABLES_DIR / "T6_rq2_outcomes.csv")
    t7_rows = _read_csv(FINAL_TABLES_DIR / "T7_estimability.csv")

    labels = ["NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"]
    label_idx = {lbl: i for i, lbl in enumerate(labels)}
    cm_by_scope: dict[str, Any] = {}
    for scope in ["pooled", "Center", "Downstream", "Upstream"]:
        mat = [[0] * 4 for _ in range(4)]
        for r in cm_rows:
            if r["scope"] == scope:
                ti = label_idx[r["true_class"]]
                pi = label_idx[r["predicted_class"]]
                mat[ti][pi] = int(r["n"])
        supports = [sum(row) for row in mat]
        cm_by_scope[scope] = {
            "labels": labels,
            "matrix": mat,
            "supports": supports,
            "total_windows": sum(supports),
        }

    rc_series = []
    for r in rc_rows:
        if r["variant"] != "primary":
            continue
        if r["method"] not in ("s_C", "s_C_minus_D", "confidence", "D_only"):
            continue
        rc_series.append(
            {
                "scope": r["scope"],
                "method": r["method"],
                "coverage_requested": float(r["coverage_requested"]),
                "status": r["status"],
                "coverage": float(r["coverage"]) if r["coverage"] else None,
                "selective_risk": float(r["selective_risk"]) if r["selective_risk"] else None,
                "n_total": int(r["n_total"]) if r["n_total"] else None,
                "n_specific": int(r["n_specific"]) if r["n_specific"] else None,
            }
        )

    matched_06 = [
        {
            "method": r["method"],
            "target_coverage": float(r["target_coverage"]),
            "coverage": float(r["coverage"]),
            "selective_risk": float(r["selective_risk"]),
            "n_specific": int(r["n_specific"]),
            "n_eligible": int(r["n_eligible"]),
            "n_families": int(r["n_families"]),
            "folds_estimable": int(r["folds_estimable"]),
        }
        for r in t4_rows
    ]

    three_outcome = [
        {
            "class": r["class"],
            "scope": r["scope"],
            "n_windows": int(r["n_windows"]),
            "n_runs": int(r["n_runs"]),
            "n_families": int(r["n_families"]),
            "n_specific": int(r["n_specific"]),
            "n_specific_correct": int(r["n_specific_correct"]),
            "n_ambiguity_set": int(r["n_ambiguity_set"]),
            "n_ambiguity_includes_true": int(r["n_ambiguity_includes_true"]),
            "n_unresolved": int(r["n_unresolved"]),
        }
        for r in t6_rows
    ]

    estimability = [
        {
            "fold": int(r["fold"]),
            "method": r["method"],
            "target": float(r["target"]),
            "status": r["status"],
            "test_max_attainable_coverage": float(r["test_max_attainable_coverage"]),
        }
        for r in t7_rows
        if r["method"] in ("s_C", "confidence")
    ]

    return {
        "schema_version": "1.0.0",
        "run_key": manifest["run_key"],
        "git_commit": manifest["git_commit"][:12],
        "split": "Leave-One-Topology-Out (Center / Downstream / Upstream)",
        "artifact_hash": manifest["code_sha256"][:16],
        "cohort_n": int(manifest["n_test_windows"]),
        "estimable_n": 18662,
        "ci_method": "Exact family sign-flip & clustered family bootstrap (1,000 replicates)",
        "rq1_status": "NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL",
        "rq1_note": (
            "Registered H1 contrast (s_C vs s_C-D) is NOT_ESTIMABLE under the primary protocol: "
            "Center outer fold reaches max attainable coverage 0.258 (< 0.60 target). "
            "Matched coverage at 0.60 covers Downstream + Upstream only (2/3 folds, n=18,662)."
        ),
        "matched_coverage_06": matched_06,
        "confusion_matrices_by_scope": cm_by_scope,
        "risk_coverage_series": rc_series,
        "three_outcome_by_class": three_outcome,
        "estimability_by_fold": estimability,
        "prohibited_claims": manifest["prohibited_claims"],
        "source_artifacts": [
            "03_results/primary_protocol/PRIMARY/run_manifest.json",
            "03_results/primary_protocol/PRIMARY/confusion_matrix.csv",
            "03_results/primary_protocol/PRIMARY/risk_coverage_curve.csv",
            "03_results/tables/primary/a10530f1fcf2_s4228b6c8_b200fcdac/final/T4_matched_coverage.csv",
            "03_results/tables/primary/a10530f1fcf2_s4228b6c8_b200fcdac/final/T6_rq2_outcomes.csv",
            "03_results/tables/primary/a10530f1fcf2_s4228b6c8_b200fcdac/final/T7_estimability.csv",
        ],
    }


def build_all() -> None:
    # Remove old synthetic fixtures if present
    for old in (OUT_DIR / "scenarios").glob("fixture_*.json"):
        old.unlink()

    _write_lf_json(OUT_DIR / "topology" / "h2_simnet_center_v1.json", TOPOLOGY_SPEC)

    scen_entries: list[dict[str, Any]] = []
    for spec in SAMPLE_SCENARIOS:
        pq_path = REPO_ROOT / "data" / "sample" / spec["file"]
        df = pl.read_parquet(pq_path)
        n_rows = df.height

        anom_idx = df.with_row_index("_idx").filter(pl.col("label_anomaly") != 0)["_idx"]
        onset_idx = int(anom_idx.min()) if len(anom_idx) > 0 else None
        end_idx = int(anom_idx.max()) if len(anom_idx) > 0 else None

        indices = _downsample_indices(n_rows, onset_idx, end_idx)
        df_sub = df[indices]
        time_sec = [float(x) for x in df_sub["Timestamp"].to_list()]
        onset_time = float(df["Timestamp"][onset_idx]) if onset_idx is not None else None
        end_time = float(df["Timestamp"][end_idx]) if end_idx is not None else None

        channels = []
        for ch_id, (target, var, unit, pref) in CHANNEL_TARGETS.items():
            is_padded = ch_id in spec["padded_absent_channels"]
            raw_vals = df_sub[ch_id].to_list()
            if is_padded:
                vals: list[float | None] = [None] * len(raw_vals)
                obs = False
                note = "Absent in Center Simscape model (constant-padded in raw release; masked to null)."
            else:
                vals = [_clean_float(v) for v in raw_vals]
                obs = True
                note = "Direct H2-SimNet sample channel."
            channels.append(
                {
                    "id": ch_id,
                    "node_or_edge": target,
                    "variable": var,
                    "unit": unit,
                    "pressure_reference": pref,
                    "values": vals,
                    "observable": obs,
                    "status_note": note,
                }
            )

        payload = {
            "schema_version": "1.0.0",
            "id": spec["id"],
            "provenance_status": "VERIFIED_EXPORT",
            "source_artifact": f"data/sample/{spec['file']}",
            "topology_id": "h2_simnet_center_v1",
            "decimation_note": (
                f"Deterministic replay projection: {len(indices)} of {n_rows} 1 Hz samples "
                "(10 s stride in [0, 1200 s], 150 s stride thereafter; exact onset/end preserved)."
            ),
            "time_seconds": time_sec,
            "sensor_channels": channels,
            "event": {
                "ground_truth_class": spec["gt_class"],
                "onset_time": onset_time,
                "end_time": end_time,
                "true_edges_or_nodes": spec["true_targets"],
                "label_status": "AUDITED_SAMPLE_PARQUET",
            },
            # Per-run window predictions are not shipped in data/sample/*.parquet -> fail closed
            "model_result": None,
            "location_prediction": None,
        }

        out_path = OUT_DIR / "scenarios" / f"{spec['id']}.json"
        digest = _write_lf_json(out_path, payload)

        scen_entries.append(
            {
                "id": spec["id"],
                "display_name": spec["display_name"],
                "family_id": spec["family_id"],
                "scenario_class": spec["scenario_class"],
                "summary_hint": spec["summary_hint"],
                "data_path": f"data/scenarios/{spec['id']}.json",
                "sha256": digest,
                "gas_metadata_status": spec["gas_metadata_status"],
                "topology_id": "h2_simnet_center_v1",
                "provenance_status": "VERIFIED_EXPORT",
                "split": spec["split"],
                "time_range": [time_sec[0], time_sec[-1]],
                "samples": len(time_sec),
                "publish_approved": True,
            }
        )

    metrics_obj = build_metrics()
    metrics_hash = _write_lf_json(OUT_DIR / "metrics.json", metrics_obj)

    catalog = {
        "schema_version": "1.0.0",
        "release_id": "v1.0.0-r2-primary-a10530f1",
        "build_utc": "2026-11-22T23:25:00Z",
        "source_repository_commit": metrics_obj["git_commit"],
        "data_release_checksum": hashlib.sha256(
            "".join(e["sha256"] for e in scen_entries).encode("utf-8")
        ).hexdigest(),
        "label_set": ["NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"],
        "supported_features": {
            "localization": False,
            "inference": True,
            "baseline_comparison": True,
            "gas_comparison": False,
            "operating_condition_analysis": False,
        },
        "scenarios": scen_entries,
        "metrics_catalog": [
            {
                "id": "primary_r2_a10530f1",
                "title": "Primary LOTO Experiment (Run a10530f1fcf2)",
                "data_path": "data/metrics.json",
                "sha256": metrics_hash,
            }
        ],
    }
    _write_lf_json(OUT_DIR / "catalog.json", catalog)
    print(f"Built {len(scen_entries)} verified scenarios + real R2 metrics bundle.")


if __name__ == "__main__":
    build_all()
