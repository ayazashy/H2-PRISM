"""Source reconciliation, steady reachability, and evaluation-readiness experiments."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, replace
from enum import Enum
from fractions import Fraction as Q
import hashlib
import json
from math import isfinite
import os
from pathlib import Path
import subprocess
from time import perf_counter

import numpy as np
import pandas as pd

from .certified_evidence import Record, diagnose
from .data.loader import MANIFEST_FILE, RAW_DATASET_DIR, WORKSPACE_ROOT, list_scenarios, load_scenario
from .joint_network import JointNetwork
from .network_reference import localize
from .phase2 import DATA_HASH, MODEL, MODEL_DIR, PARQUET, SID, checked_file
from .phase3 import REGIONS, benchmark, digest, source_report, write_record
from .phase4 import CASES, comparison, physical, replay
from .steady_enclosure import Isotherm, junction_bracket

CSV_HASH = "965085bcd0db853112f46d199b2204bfc2dd2261bbb19db3dbbf42186ed78fcc"
UNCERTAINTY = {
    "pressure": "Pa", "mass_flow": "kg/s", "temperature": "K", "clock": "s",
    "boundary_inputs": "mixed", "initial_state": "mixed", "gas_properties": "mixed",
    "geometry": "mixed", "leak_parameters": "mixed", "model_discrepancy": "mixed",
    "numerical_error": "mixed",
}


class EvidenceBasis(str, Enum):
    MEASURED = "MEASURED"
    CALIBRATED = "CALIBRATED"
    MANUFACTURER = "MANUFACTURER_SPECIFIED"
    LITERATURE = "LITERATURE_SUPPORTED"
    ASSUMED = "ASSUMPTION_CONDITIONAL"
    UNKNOWN = "UNKNOWN"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True)
class ErrorBound(Record):
    name: str
    unit: str
    interval: tuple[float, float] | None
    basis: EvidenceBasis
    reference: str
    domain: str


def physical_eligibility(bounds: tuple[ErrorBound, ...], domain: str) -> tuple[str, ...]:
    by_name = {b.name: b for b in bounds}
    if len(by_name) != len(bounds):
        raise ValueError("duplicate uncertainty evidence")
    reasons = []
    for name, unit in UNCERTAINTY.items():
        b = by_name.get(name)
        if b is None or b.interval is None:
            reasons.append(f"{name}:MISSING")
            continue
        lo, hi = b.interval
        if (b.unit != unit or b.domain != domain or not b.reference.strip() or not isinstance(b.basis, EvidenceBasis) or
                not isfinite(lo) or not isfinite(hi) or lo > hi):
            reasons.append(f"{name}:INVALID")
        elif b.basis in (EvidenceBasis.ASSUMED, EvidenceBasis.UNSUPPORTED, EvidenceBasis.UNKNOWN):
            reasons.append(f"{name}:UNVERIFIED")
    return tuple(reasons)


def available_source_bounds():
    return tuple(ErrorBound(name, unit, None, EvidenceBasis.UNKNOWN,
                            "Center release and static SLX evidence; no verified deterministic bounds", MODEL)
                 for name, unit in UNCERTAINTY.items())


def clock_index(values):
    clock = pd.Index(tuple(Q(str(value)) for value in values), name="timestamp_s")
    if clock.empty or not clock.is_unique or not clock.is_monotonic_increasing:
        raise ValueError("invalid original source clock")
    return clock


def reconcile_source():
    root = RAW_DATASET_DIR
    csv = checked_file(root / MODEL_DIR / "normality_gest_center.csv", CSV_HASH)
    alias = checked_file(csv.parent.parent / csv.name, CSV_HASH)
    release = checked_file(root / PARQUET, DATA_HASH)
    raw = pd.read_csv(csv, dtype={"Timestamp": str}).set_index("Timestamp")
    frame = load_scenario(release)
    if frame.index.name != "Timestamp" or tuple(raw.columns) != tuple(SID) or not set(SID) <= set(frame):
        raise ValueError("source/release schema changed")
    raw.index, frame.index = clock_index(raw.index), clock_index(frame.index)
    common = raw.index.intersection(frame.index)
    if common.empty:
        raise ValueError("no exact source timestamps shared")
    values = {}
    for name, block in SID.items():
        a, b = raw.loc[common, name], frame.loc[common, name]
        valid = np.isfinite(a) & np.isfinite(b)
        discrepancy = (a[valid] - b[valid]).abs()
        values[name] = {"source_block": block, "unit": "MPa" if name.startswith("PS") else "kg/s (release metadata)",
                        "pairs": int(valid.sum()), "missing_pairs": int((~valid).sum()),
                        "median_absolute_difference": float(discrepancy.median()) if len(discrepancy) else None,
                        "max_absolute_difference": float(discrepancy.max()) if len(discrepancy) else None}
    return {
        "tier": "T3_ARCHIVAL_SOURCE_TRACE", "source_run_executed": False,
        "files": {p.relative_to(root).as_posix(): h for p, h in ((csv, CSV_HASH), (alias, CSV_HASH), (release, DATA_HASH))},
        "byte_identical_solver_csv_aliases": True, "source_rows": len(raw), "release_rows": len(frame),
        "exact_shared_timestamps": len(common), "shared_time_range_s": [str(common[0]), str(common[-1])],
        "clock_method": "exact equality of stored decimal timestamps; no interpolation, rounding, or shift",
        "source_step_counts_s": dict(Counter(str(b-a) for a, b in zip(raw.index, raw.index[1:]))),
        "release_step_counts_s": dict(Counter(str(b-a) for a, b in zip(frame.index, frame.index[1:]))),
        "excluded_release_columns": sorted(set(frame.columns) - set(raw.columns)),
        "signals": values, "release_transformation": "UNKNOWN",
        "signed_boundary_balance": "BLOCKED_NOT_ALL_PORT_ROLES_EFFECTIVE_SIGN_OR_STORAGE_TRACED",
        "ancestry": "Center solver exporter maps 13 channels to CSV; archive aliases are one record. Parquet processing unverified.",
    }


def independent_eligibility():
    catalog = list_scenarios()
    counted = catalog.groupby(["Scenario_ID", "Scenario_Family_ID", "topology", "target_class"]).size()
    rows = [{"scenario": key[0], "declared_family": key[1], "topology": key[2], "class": key[3],
             "archive_assets": int(n), "eligible_independent": False,
             "reason": "Archive provenance does not establish independent generation and physical ground truth"}
            for key, n in counted.items()]
    counts = Counter((row["topology"], row["class"]) for row in rows)
    return {
        "tier": "T3_SOURCE_DERIVED_SIMULATION", "eligible_confirmatory_families": 0,
        "manifest_sha256": hashlib.sha256(MANIFEST_FILE.read_bytes()).hexdigest(),
        "archival_declared_scenarios": len(rows),
        "provisional_scenario_counts": [{"topology_label": t, "class": c, "scenarios": n}
                                        for (t, c), n in sorted(counts.items())],
        "candidate_manifest": rows,
        "qualification": "Provisional topology labels include known source-attribution defects; no independent allocation",
        "protocol": {
            "status": "DRAFT_UNFROZEN_NO_ELIGIBLE_FAMILIES", "unit": "one independently generated verified family",
            "tiers": {"T1": "mathematical verification", "T2": "controlled physical model",
                      "T3": "source simulation", "T4": "independent physical measurements"},
            "proposed_ontology": ["NORMAL", "LEAK_A", "LEAK_B"],
            "sensor_target": "synchronized absolute pressure at each junction and signed boundary mass-flow measurements",
            "prelock_requirements": ["model version", "ontology", "sensor and gas configuration",
                                     "uncertainty and parameter bounds", "matched comparator version",
                                     "family assignments", "predeclared exclusion criteria"],
            "primary": ["family-level specific coverage", "selective risk when specific count is nonzero"],
            "secondary": ["true candidate inclusion", "false exclusion", "ambiguity", "unresolved",
                          "region inclusion", "candidate cardinality", "runtime"],
            "statistics": "paired family bootstrap only after independent family count supports inference",
            "empirical_metrics": None,
        },
    }


def isotherm(path):
    values = json.loads(path.read_text(encoding="utf-8"), parse_float=Q)["data"]
    i = values["T_TLU2"].index(300)
    return Isotherm(tuple(str(Q(p) * 1000000) for p in values["p_TLU2"]),
                    tuple(map(str, values["Z"][i])),
                    tuple(str(Q(mu) / 1000000) for mu in values["mu_TLU2"][i]),
                    str(Q(values["R_kJ_per_kgK"]) * 1000), "300")


def physical_matrix():
    from tools.simulation.h2net_v1_reference import TABLES
    model = physical()  # This calls the checksum-verifying table loader.
    table = isotherm(TABLES)
    brackets = []
    for panels in (4, 16, 64):
        lo, hi = junction_bracket(table, 220000, 105000, ("1", "1"), panels)
        pressure = model["results"]["NORMAL"]["A"]["pressure_pa"]
        brackets.append({"panels_per_segment": panels, "exact_pa": [str(lo), str(hi)],
                         "width_pa": float(hi - lo), "numerical_root_inside": lo <= Q(pressure) <= hi})
    sensitivity = junction_bracket(table, 220000, 105000, ("99/100", "101/100"), 16)
    leak = model["results"]["LEAK_A"]["A"]
    max_balance = max(abs(b["balance_residual_kg_s"]) for pair in model["results"].values() for b in pair.values())
    matrix = [
        {"component": "no-leak junction", "operating_range": "300 K; 105–220 kPa absolute",
         "reference": "Exact decimal pressure-table interpolant and integrated laminar closure",
         "configuration": "equal capillaries, fixed boundary pressures",
         "discrepancy": brackets[-1]["width_pa"], "criterion": "encloses independent quadrature root; width < 15 Pa",
         "verification": "PASSED" if all(b["numerical_root_inside"] for b in brackets)
         and brackets[-1]["width_pa"] < 15 else "FAILED", "validation": "UNVALIDATED",
         "limitation": "normal steady root only; model discrepancy and table property uncertainty not enclosed"},
        {"component": "leaky junction", "operating_range": "300 K; 100–220 kPa absolute",
         "reference": "Capillary balance plus local ideal isentropic orifice approximation",
         "configuration": "fixed constructed 2e-9 m2 opening and Cd=0.75",
         "discrepancy": max_balance, "criterion": "max absolute mass residual < 1e-16 kg/s",
         "verification": "PASSED" if max_balance < 1e-16 else "FAILED", "validation": "UNVALIDATED",
         "limitation": f"numerical {leak['leak']['regime']} root; no verified enclosure for discharge"},
    ]
    return {
        "tier": "T2_CONTROLLED_PHYSICAL_MODEL",
        "validation_matrix": matrix, "phase4_reference": model,
        "reachability": {"scope": "no-leak steady capillary algebraic model only",
                         "table_interpolant": json.loads(table.to_json()),
                         "boundaries_pa": [105000, 220000], "nominal_refinement": brackets,
                         "assumed_conductance_ratio": ["99/100", "101/100"],
                         "sensitivity_enclosure_pa": list(map(str, sensitivity)),
                         "leaky_and_source_exclusion": "INDETERMINATE",
                         "source_uncertainty_blockers": physical_eligibility(available_source_bounds(), MODEL)},
    }


def ablations():
    results = []
    for case in CASES:
        result, timing = comparison(case)
        results.append({"case": case, "joint_equal": result["joint_sets_identical"],
                        "joint": result["joint_membership"], "decision": result["decision"],
                        "with_replay": replay(result), "localization": result["localization"],
                        "input_gate": result["evidence_gate_ablation"], "record": result, "timing": timing})
    sweep = []
    for case in ("unique", "severe", "spatial_alias"):
        measurement, hypotheses, truth, _ = benchmark(case)
        hypotheses = tuple(replace(h, adapter=JointNetwork(h.adapter)) for h in hypotheses)
        for extra in (0, 100, 500, 1000):
            channels = tuple(replace(c, absolute_errors=tuple(e + extra for e in c.absolute_errors))
                             if c.unit == "Pa" else c for c in measurement.channels)
            start = perf_counter()
            outcome = diagnose(replace(measurement, channels=channels), hypotheses)
            elapsed = perf_counter() - start
            sweep.append({"case": case, "added_error_pa": extra, "decision": outcome.status.value,
                          "truth": truth, "feasible": outcome.certificate.feasible,
                          "excluded": outcome.certificate.excluded,
                          "localization": json.loads(localize(outcome, REGIONS).to_json()), "runtime_s": elapsed})
    return {"tier": "T1_MATHEMATICAL_VERIFICATION", "seed": None,
            "prespecified_sweep_pa": [0, 100, 500, 1000], "matched": results, "pressure_sweep": sweep,
            "summary": {"joint_set_agreement": sum(r["joint_equal"] for r in results),
                        "certificates_replayed": sum(r["with_replay"] for r in results),
                        "ungated_specific_gate_withheld_examples": sum(
                            bool(r["input_gate"] and r["input_gate"]["diagnosis"] == "UNRESOLVED" and
                                 list(r["input_gate"]["ungated_joint"].values()).count("FEASIBLE") == 1 and
                                 "INDETERMINATE" not in r["input_gate"]["ungated_joint"].values()) for r in results),
                        "full_policy_specific": sum(r["decision"]["status"] == "SPECIFIC" for r in results),
                        "empirical_accuracy": None}}


def plot(report, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
    local = report["comparisons"]["pressure_sweep"]
    levels = {"L0": 0, "L1": 1, "L2": 2}
    for case in ("unique", "severe", "spatial_alias"):
        rows = [r for r in local if r["case"] == case]
        a.plot([r["added_error_pa"] for r in rows], [levels[r["localization"]["level"]] for r in rows],
               "o-", label=case)
    a.set(xlabel="Added pressure-error bound (Pa)", ylabel="Localization level",
          yticks=(0, 1, 2), yticklabels=("L0", "L1", "L2"), title="T1 | Mathematical fixture sweep")
    a.legend()
    bounds = report["physical"]["reachability"]["nominal_refinement"]
    b.loglog([r["panels_per_segment"] for r in bounds], [r["width_pa"] for r in bounds], "o-")
    b.set(xlabel="Panels per table segment", ylabel="Enclosure width (Pa)", title="T2 | No-leak model quadrature")
    fig.suptitle(f"Phase 5 executed results | {report['sha256'][:12]}")
    with path.open("xb") as file:
        fig.savefig(file, format="png", dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("run", "figure", "replay"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--probe-log", type=Path)
    parser.add_argument("--matlab-root", type=Path)
    args = parser.parse_args()
    if args.action != "replay" and args.output is None:
        parser.error("--output required")
    if args.action == "run":
        source = source_report(args.probe_log)
        source["startup_dependency"] = "EXTERNAL_ACTION_REQUIRED"
        if args.matlab_root:
            source["installation_files"] = {
                name: (args.matlab_root / rel).exists() for name, rel in {
                    "matlab": "bin/matlab.exe", "simulink": "toolbox/simulink",
                    "simscape_foundation": "toolbox/physmod/simscape/library",
                    "release_marker": "VersionInfo.xml",
                }.items()
            }
        source["network_diagnostics"] = {
            "proxy_environment_present": any(os.environ.get(key) for key in ("HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY")),
            "cause": "Startup log identifies a service failure; proxy, endpoint and entitlement causes unverified",
        }
        source["next_action"] = ("After an authorized Windows restart, open MATLAB normally, verify sign-in and "
                                 "toolbox entitlement, then retry the isolated Center probe once. If 5202 persists, "
                                 "send the local Service Host diagnostics privately to MathWorks or the license admin.")
        source["runtime_checkout"] = "UNVERIFIED"
        report = {"schema": "phase5/1", "source": source, "reconciliation": reconcile_source(),
                  "physical": physical_matrix(), "uncertainty": [json.loads(b.to_json()) for b in available_source_bounds()],
                  "comparisons": ablations(), "eligibility": independent_eligibility(),
                  "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=WORKSPACE_ROOT,
                                                   text=True).strip()}
        report = json.loads(json.dumps(report))
        report["sha256"] = digest(report)
        write_record(args.output, report)
    else:
        if args.input is None:
            parser.error("--input required")
        report = json.loads(args.input.read_text(encoding="utf-8"))
        if report["sha256"] != digest({k: v for k, v in report.items() if k != "sha256"}):
            raise SystemExit("record checksum mismatch")
        if args.action == "replay":
            if not all(replay(r["record"]) for r in report["comparisons"]["matched"]):
                raise SystemExit("joint replay failed")
            if reconcile_source() != report["reconciliation"] or independent_eligibility() != report["eligibility"]:
                raise SystemExit("source or evaluation manifest replay failed")
            enclosure = json.loads(json.dumps(physical_matrix()["reachability"]))
            if enclosure != report["physical"]["reachability"]:
                raise SystemExit("steady enclosure replay failed")
            print("Replayed ten joint records and the steady certificate")
        else:
            plot(report, args.output)


if __name__ == "__main__":
    main()
