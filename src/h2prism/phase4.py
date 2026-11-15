"""Execute and replay Phase 4 joint membership and physical reference runs."""
from __future__ import annotations

import argparse
from dataclasses import replace
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import subprocess
from time import perf_counter

from .certified_evidence import ConsistencyStatus, diagnose
from .data.loader import WORKSPACE_ROOT
from .gas_physics import Pipe
from .joint_network import JointNetwork
from .network_reference import localize
from .phase3 import CASES, REGIONS, benchmark, conventional_membership, digest, source_report, write_record
from .pressure_reference import CapillaryReference


def closed_pair_enclosure(p_a, p_b, decay, elapsed, pairs=12):
    """Equal isothermal storages, no boundaries or leak; exact decay-rate enclosure.

    decay is the fixed positive coefficient in d(p_a-p_b)/dt = -decay*(p_a-p_b).
    For the pressure-squared transfer law it includes the constant pressure sum.
    """
    p_a, p_b, decay, elapsed = map(Q, (p_a, p_b, decay, elapsed))
    x = decay * elapsed
    if min(p_a, p_b, decay) <= 0 or not 0 <= x <= 1 or pairs < 1:
        raise ValueError("outside the alternating-series verification domain")
    term = total = Q(1)
    for n in range(1, 2 * pairs):
        term *= -x / n
        total += term
    lower, upper = total, total - term * x / (2 * pairs)
    mean, half_diff = (p_a + p_b) / 2, (p_a - p_b) / 2
    return tuple(tuple(sorted((mean + sign * half_diff * lower, mean + sign * half_diff * upper)))
                 for sign in (1, -1))


def status_map(results):
    return {r.hypothesis: r.status.value for r in results}


def comparison(case: str):
    measurement, hypotheses, truth, _ = benchmark(case)
    adapters = tuple(replace(h, adapter=JointNetwork(h.adapter)) if h.adapter else h for h in hypotheses)
    start = perf_counter()
    # Conventional joint feasibility and the policy use exactly the same model,
    # domains, measurements and solver; this call has no decision/localization policy.
    joint = status_map(h.adapter.check(h, measurement) for h in adapters if h.adapter)
    joint.update({h.name: "INDETERMINATE" for h in adapters if h.adapter is None})
    baseline_time = perf_counter() - start
    start = perf_counter()
    decision = diagnose(measurement, adapters)
    policy_time = perf_counter() - start
    old = diagnose(measurement, hypotheses)
    gating_example = None
    if case == "unique":
        channels = (replace(measurement.channels[0], resampled=True), *measurement.channels[1:])
        invalid = replace(measurement, channels=channels)
        gated = diagnose(invalid, adapters)
        ungated = status_map(h.adapter.check(h, invalid) for h in adapters)
        gating_example = {"counterfactual": "Identical samples marked resampled",
                          "diagnosis": gated.status.value, "ungated_joint": ungated,
                          "reasons": gated.certificate.measurement_issues}
    payload = {
        "case": case, "evidence_tier": "EXACT_MATHEMATICAL_BENCHMARK",
        "generating_case": measurement.independence_group,
        "shared_ancestry": "Phase 3 gamma=3 four-storage constructed fixture",
        "confirmatory_evaluation_eligible": False,
        "ground_truth": truth, "ground_truth_provenance": "constructed fixture" if truth else "out-of-model challenge",
        "outer_membership": conventional_membership(measurement, hypotheses),
        "prior_midpoint_policy": status_map(old.certificate.results),
        "joint_membership": joint, "joint_sets_identical": joint == status_map(decision.certificate.results),
        "localization": json.loads(localize(decision, REGIONS).to_json()),
        "decision": json.loads(decision.to_json()), "evidence_gate_ablation": gating_example,
        "models": {h.name: json.loads(h.adapter.to_json()) if h.adapter else None for h in hypotheses},
        "solver": {"identity": "RATIONAL_SHARED_RATE_ELIMINATION", "max_cells": 256, "samples": 3,
                   "precision": "exact rational; budget exhaustion remains indeterminate"},
    }
    payload = json.loads(json.dumps(payload))
    payload["sha256"] = digest(payload)
    return payload, {"joint_s": baseline_time, "policy_with_certificate_s": policy_time,
                     "certificate_bytes": len(decision.to_json().encode())}


def replay(record):
    try:
        fresh, _ = comparison(record["case"])
        return record == fresh
    except (ValueError, TypeError, KeyError, ArithmeticError):
        return False


def physical():
    # Reuse the frozen, hash-verifying repository loader; no substitute H2 values.
    from tools.simulation.h2net_v1_reference import TABLES, load_h2_tables

    reference = CapillaryReference(load_h2_tables())
    incoming = Pipe("supply", "junction", 20, 0.001, 0)
    outgoing = Pipe("junction", "sink", 20, 0.001, 0)
    supply, sink, ambient = 220000, 105000, 100000
    configurations = {"NORMAL": (0, 0), "LEAK_A": (2e-9, 0), "LEAK_B": (0, 2e-9)}
    results, refinement = {}, {}
    for event, areas in configurations.items():
        solutions = [[reference.branch(incoming, outgoing, supply, sink, area, ambient=ambient,
                                       tolerance_pa=tol, quadrature_tol=qtol) for area in areas]
                     for tol, qtol in ((1.0, 1e-6), (0.01, 1e-8), (1e-7, 1e-10))]
        results[event] = dict(zip(("A", "B"), solutions[-1]))
        refinement[event] = [{"pressure_tolerance_pa": tol,
                              "quadrature_relative_tolerance": qtol,
                              "max_pressure_delta_from_finest_pa": max(abs(a["pressure_pa"] - b["pressure_pa"])
                                                                    for a, b in zip(run, solutions[-1]))}
                             for (tol, qtol), run in zip(((1.0, 1e-6), (0.01, 1e-8), (1e-7, 1e-10)), solutions)]
    return {
        "evidence_tier": "PHYSICALLY_PARAMETERIZED_REFERENCE_MODEL",
        "physical_validation": "UNAVAILABLE_NO_INDEPENDENT_MEASUREMENTS",
        "parameter_provenance": "Constructed capillary geometry, boundaries, openings and Cd; published EOS table",
        "property_table": TABLES.relative_to(WORKSPACE_ROOT).as_posix(),
        "property_table_sha256": hashlib.sha256(TABLES.read_bytes()).hexdigest(),
        "gas": reference.gas.source, "temperature_k": reference.temperature_k,
        "pressure_domain_pa": reference.pressure_domain_pa,
        "geometry": {"branch_count": 2, "capillaries_per_branch": 2, "length_m_each": 20,
                     "diameter_m_each": 0.001, "junction_volume_m3": 0.001},
        "boundaries_pa": {"supply": supply, "sink": sink, "leak_ambient": ambient},
        "openings_m2": configurations, "assumed_cd": 0.75,
        "regime_screens": {"max_reynolds": reference.reynolds_limit, "max_mach_reference": reference.mach_limit},
        "results": results, "refinement": refinement,
        "leak_checks": {str(p): reference.leak(p, ambient, 2e-9, 0.75)
                        for p in (100000, 170000, 220000)},
        "sensor_identifiability": {
            "total_inlet_is_symmetric": sum(v["inlet"]["kg_s"] for v in results["LEAK_A"].values()) ==
                                         sum(v["inlet"]["kg_s"] for v in results["LEAK_B"].values()),
            "local_pressures_differ": results["LEAK_A"]["A"]["pressure_pa"] != results["LEAK_B"]["A"]["pressure_pa"],
        },
        "certification": "NONE_FOR_TABULATED_CAPILLARY_OR_DISCHARGE_MODEL",
        "continuous_math_check": {
            "scope": "Closed equal-storage constant-property analytical fixture only",
            "initial_pa": [200000, 100000], "inverse_seconds": "1/2", "seconds": "1",
            "enclosures_pa": [list(map(str, item))
                              for item in closed_pair_enclosure(200000, 100000, Q(1, 2), 1)],
        },
    }


def summarize(records):
    specific = [r for r in records if r["decision"]["status"] == "SPECIFIC"]
    modeled = [r for r in records if r["ground_truth"] is not None]
    leaks = [r for r in modeled if r["ground_truth"] in REGIONS]
    localized = [r for r in records if r["localization"]["level"] == "L2"]
    return {
        "scope": "Descriptive shared mathematical fixtures only",
        "cases": len(records), "equivalent_joint_sets": sum(r["joint_sets_identical"] for r in records),
        "coverage": len(specific) / len(records),
        "selective_risk": (sum(r["decision"]["hypothesis"] != r["ground_truth"] for r in specific)
                           / len(specific) if specific and all(r["ground_truth"] for r in specific) else None),
        "decisions": {key: sum(r["decision"]["status"] == key for r in records)
                      for key in ("SPECIFIC", "AMBIGUOUS", "UNRESOLVED")},
        "known_truth_false_exclusions": sum(r["ground_truth"] in r["decision"]["certificate"]["excluded"]
                                            for r in modeled),
        "true_region_inclusion": sum(r["ground_truth"] in r["localization"]["candidates"] for r in leaks) / len(leaks),
        "mean_region_candidates": sum(len(r["localization"]["candidates"]) for r in records) / len(records),
        "unique_region_coverage": len(localized) / len(records),
        "incorrect_unique_regions": sum(r["localization"]["candidates"] != [r["ground_truth"]] for r in localized),
        "independent_empirical_metrics": None,
    }


def figure(record, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    physical_result = record["physical"]
    labels = list(physical_result["results"])
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
    for i, node in enumerate(("A", "B")):
        x = [j + 0.28 * i for j in range(len(labels))]
        axes[0].bar(x, [physical_result["results"][k][node]["pressure_pa"] / 1000 for k in labels],
                    width=0.27, label=f"Junction {node}")
    axes[0].set_xticks([i + 0.14 for i in range(len(labels))], labels)
    axes[0].set(ylabel="Equilibrium pressure (kPa)", title="Physically parameterized capillary reference")
    axes[0].legend()
    cases = record["cases"]
    counts = [[sum(v == "RETAINED" for v in r["outer_membership"].values()),
               sum(v == "FEASIBLE" for v in r["joint_membership"].values())] for r in cases]
    axes[1].plot(range(len(cases)), [n[0] for n in counts], "o-", label="Outer retained")
    axes[1].plot(range(len(cases)), [n[1] for n in counts], "x--", label="Joint feasible")
    axes[1].set_xticks(range(len(cases)), [c["case"] for c in cases], rotation=40, ha="right")
    axes[1].set(ylabel="Hypotheses", title="Exact mathematical benchmark")
    axes[1].legend()
    fig.suptitle(f"Phase 4 executed results | {record['sha256'][:12]}")
    with path.open("xb") as f:
        fig.savefig(f, format="png", dpi=160)
    plt.close(fig)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("action", choices=("benchmark", "replay", "figure", "source"))
    cli.add_argument("--input", type=Path)
    cli.add_argument("--output", type=Path)
    cli.add_argument("--matlab-root", type=Path)
    args = cli.parse_args()
    if args.action in {"replay", "figure"} and args.input is None:
        cli.error("--input is required")
    if args.action != "replay" and args.output is None:
        cli.error("--output is required")
    if args.action == "benchmark":
        runs = [comparison(case) for case in CASES]
        records = [record for record, _ in runs]
        started = perf_counter()
        replayed = {r["case"]: replay(r) for r in records}
        replay_seconds = perf_counter() - started
        if not all(replayed.values()):
            raise SystemExit("replay failed")
        report = {"schema": "phase4/1", "cases": records, "metrics": summarize(records),
                  "physical": physical(), "replay": replayed,
                  "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=WORKSPACE_ROOT,
                                                   text=True).strip()}
        report = json.loads(json.dumps(report))
        report["sha256"] = digest(report)
        write_record(args.output, report)
        write_record(args.output.with_name(args.output.stem + "-timing.json"),
                     {"runs": [runtime for _, runtime in runs], "total_replay_seconds": replay_seconds})
    elif args.action == "source":
        report = source_report(args.input)
        if args.matlab_root:
            report["matlab_installation_files"] = {
                name: (args.matlab_root / rel).exists() for name, rel in {
                    "executable": "bin/matlab.exe", "simulink": "toolbox/simulink",
                    "simscape": "toolbox/physmod/simscape", "foundation": "toolbox/physmod/simscape/library",
                }.items()
            }
        report["license_checkout"] = "UNVERIFIED_STARTUP_FAILED_BEFORE_MODEL_LOADING"
        report["source_reproduction"] = "BLOCKED"
        write_record(args.output, report)
    else:
        report = json.loads(args.input.read_text(encoding="utf-8"))
        if report["sha256"] != digest({k: v for k, v in report.items() if k != "sha256"}):
            raise SystemExit("benchmark checksum mismatch")
        if args.action == "replay":
            cases = report["cases"]
            if not cases or not all(replay(r) for r in cases):
                raise SystemExit("joint record mismatch")
            print(f"Replayed {len(cases)} joint records")
        else:
            figure(report, args.output)


if __name__ == "__main__":
    main()
