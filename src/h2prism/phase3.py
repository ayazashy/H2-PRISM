"""Reproduce network cases, matched set membership, replay, and source inventory."""
from __future__ import annotations

import argparse
from dataclasses import replace
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
from time import perf_counter

from .certified_evidence import Channel, HypothesisModel, MeasurementContract, diagnose
from .data.loader import RAW_DATASET_DIR, WORKSPACE_ROOT
from .data_contracts import NetworkRecord, SensorRecord
from .gas_physics import PerfectGas
from .network_reference import NetworkHypothesis, NetworkReference, Region, Storage, Transfer, localize
from .phase2 import MODEL, MODEL_HASH, source_case
from .physical_reference import Bound, BoundStatus

REGIONS = ("LEAK_A", "LEAK_B", "LEAK_C")
CASES = ("normal", "unique", "reduced", "flow_only", "wide", "unsupported", "mismatch", "severe", "spatial_alias", "joint_gap")
SCHEMA = "network-benchmark/1"


def benchmark(case: str, samples: int = 3):
    if case not in CASES or not 2 <= samples <= 65 or (case == 'joint_gap' and samples < 3):
        raise ValueError("unknown case or unsupported sample count")
    domain = "controlled-choked-network-v1"

    def bound(interval, unit):
        return Bound(interval, unit, BoundStatus.ASSUMED, "declared analytical benchmark", domain)

    nodes = ("J", "A", "B", "C")
    edges = tuple((f"P_{node}", "J", node) for node in nodes[1:])
    net = NetworkRecord(domain, nodes, edges, "prescribed-transfer discrete benchmark",
                        {"designation": "constructed ideal gas, gamma=3"})
    # Net boundary rates balance the signed prescribed internal transfers.
    storage = tuple(Storage(node, 30, bound((100, 100), "kg"), bound((q - 0.0625, q + 0.0625), "kg/s"))
                    for node, q in zip(nodes, (6, -2, -2, -2)))
    transfers = tuple(Transfer(*edge, bound((2, 2), "kg/s")) for edge in edges)
    sensors = tuple(SensorRecord(f"P_{node}", domain, "node", node, "pressure", "Pa", 1) for node in nodes)
    sensors += tuple(SensorRecord(f"F_{e[0]}", domain, "edge", e[0], "mass_flow", "kg/s", 1) for e in edges)
    ref = NetworkReference(net, storage, transfers, sensors, PerfectGas(100, 1, 150, 1e-5, 0.02),
                           300, 1, 65, domain, bound((0, 0), "s"), bound((0, 0), "Pa"))
    area = (1 / 2048, 3 / 2048) if case != "severe" else (3 / 2048, 5 / 2048)
    regions = tuple(Region(name, edge[0], edge[2], (0, 1), bound(area, "m2"),
                           bound((0.5, 1), "1"), 10000)
                    for name, edge in zip(REGIONS, edges))
    if case == "spatial_alias":
        regions = (replace(regions[0], interval=(0, 0.5)),
                   replace(regions[0], name="LEAK_B", interval=(0.5, 1)), regions[2])
    models = (HypothesisModel("NORMAL", NetworkHypothesis(ref, None), ("PRESCRIBED_RATE_VARIATION",)),)
    models += tuple(HypothesisModel(r.name, NetworkHypothesis(ref, r), ("LUMPED_BRANCH_REGION",)) for r in regions)
    if case == "unsupported":
        models += (HypothesisModel("COMPRESSOR_FAULT", None, ("NO_VALIDATED_COMPRESSOR_MODEL",)),
                   HypothesisModel("DELAY", None, ("NO_VERIFIED_DELAY_MODEL",)))
    if case == "reduced":
        used = tuple(s for s in sensors if s.location_id not in {"A", "B", "C"})
        # C is observed, leaving A, B and NORMAL indistinguishable.
        used += (sensors[3],)
    elif case == "flow_only":
        used = sensors[4:]
    else:
        used = sensors
    times = tuple(range(samples))
    measurement = MeasurementContract(used, times, (), case, f"controlled:{case}:{samples}",
                                      "controlled network benchmark", "declared bounded absolute error")
    truth = "NORMAL" if case in {"normal", "joint_gap"} else "LEAK_A"
    truth_region = None if truth == "NORMAL" else regions[0]
    _, values, _, truth_path = ref.evaluate(measurement, truth_region)
    channels = []
    for i, sensor in enumerate(used):
        block = values[i * samples:(i + 1) * samples]
        # Exact dyadic fixtures for short runs; cover float serialization at longer windows.
        rounded = tuple(map(float, block))
        errors = tuple(max(1e-9, float(2 * abs(Fraction(f) - q))) for f, q in zip(rounded, block))
        if case == "wide" and sensor.quantity == "pressure":
            errors = (1e6,) * samples
        if case == "joint_gap" and sensor.sensor_id == "P_A":
            rounded = (100000, 100020, 99960) + (100000,) * (samples - 3)
        if case == "mismatch" and sensor.quantity == "pressure":
            rounded = (200000,) * samples
        channels.append(Channel(sensor.sensor_id, sensor.unit, times, "exact discrete model clock", rounded, errors))
    measurement = replace(measurement, channels=tuple(channels))
    return measurement, models, None if case in {"mismatch", "joint_gap"} else truth, truth_path


def conventional_membership(measurement, models):
    """Outer-set intersection baseline. Overlap is retained without a joint-witness test."""
    if measurement.issues():
        return {m.name: "UNAVAILABLE" for m in models}
    observation = measurement.intervals()
    results = {}
    for model in models:
        adapter = model.adapter
        if adapter is None:
            results[model.name] = "UNAVAILABLE"
            continue
        try:
            bounds, _, _, _ = adapter.network.evaluate(measurement, adapter.region)
        except (ValueError, TypeError, ArithmeticError):
            results[model.name] = "UNAVAILABLE"
            continue
        results[model.name] = ("RETAINED" if all(a <= hi and lo <= b for (lo, hi), (a, b)
                                                in zip(bounds, observation)) else "REJECTED")
    return results


def build(case: str, samples: int = 3):
    measurement, models, truth, path = benchmark(case, samples)
    start = perf_counter()
    decision = diagnose(measurement, models)
    elapsed = perf_counter() - start
    start = perf_counter()
    baseline = conventional_membership(measurement, models)
    baseline_elapsed = perf_counter() - start
    loc = localize(decision, REGIONS)
    retained = [h for h, status in baseline.items() if status == "RETAINED"]
    baseline_status = ("UNRESOLVED" if "UNAVAILABLE" in baseline.values() or not retained else
                       "SPECIFIC" if len(retained) == 1 else "AMBIGUOUS")
    predictions = {}
    for model in models:
        if model.adapter is not None:
            box, response, _, states = model.adapter.network.evaluate(measurement, model.adapter.region)
            predictions[model.name] = {"outer": [[str(lo), str(hi)] for lo, hi in box],
                                       "midpoint_predictions": list(map(str, response)),
                                       "midpoint_masses": [list(map(str, row)) for row in states]}
    payload = {
        "schema": SCHEMA, "case": case, "samples": samples,
        "tier": "TIER_2_CONTROLLED_DISCRETE_NETWORK", "generating_case": measurement.independence_group,
        "ground_truth": truth, "truth_mass_path_kg": [list(map(str, row)) for row in path] if truth else None,
        "models": {m.name: json.loads(m.adapter.to_json()) if m.adapter else None for m in models},
        "decision": json.loads(decision.to_json()), "localization": json.loads(loc.to_json()),
        "prediction_records": predictions,
        "conventional": {"hypotheses": baseline, "decision": baseline_status, "retained": retained},
    }
    payload["sha256"] = digest(payload)
    performance = {"certified_seconds": elapsed, "baseline_seconds": baseline_elapsed,
                   "hypotheses": len(models), "channels": len(measurement.sensors),
                   "nodes": 4, "pipes": 3, "regions": len(REGIONS), "samples": samples,
                   "certificate_bytes": len(decision.to_json().encode()),
                   "model_evaluations_per_method": sum(m.adapter is not None for m in models)}
    return payload, performance


def digest(payload) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def replay(payload: dict) -> bool:
    try:
        if payload["sha256"] != digest({k: v for k, v in payload.items() if k != "sha256"}):
            return False
        regenerated, _ = build(payload["case"], payload["samples"])
        return payload == regenerated
    except (KeyError, ValueError, TypeError, ArithmeticError):
        return False


def summarize(cases: list[dict]) -> dict:
    count = len(cases)
    if not count:
        raise ValueError("at least one benchmark is required")
    unique = [p for p in cases if p["localization"]["level"] == "L2"]
    known = [p for p in cases if p["ground_truth"] in REGIONS]
    specific = [p for p in cases if p["decision"]["status"] == "SPECIFIC"]
    known_specific = [p for p in specific if p["ground_truth"] is not None]
    return {
        "scope": "Descriptive controlled configurations; shared model, no independent empirical replicates",
        "cases": count, "specific_coverage": len(specific) / count,
        "selective_risk": (sum(p["decision"]["hypothesis"] != p["ground_truth"] for p in known_specific)
                           / len(specific) if specific and len(known_specific) == len(specific) else None),
        "unique_region_coverage": len(unique) / count,
        "incorrect_unique_regions": sum(p["localization"]["candidates"] != [p["ground_truth"]] for p in unique),
        "region_inclusion": (sum(p["ground_truth"] in p["localization"]["candidates"] for p in known)
                             / len(known) if known else None),
        "mean_candidate_size": sum(len(p["localization"]["candidates"]) for p in cases) / count,
        "localization_unavailable": sum(p["localization"]["level"] == "L0" for p in cases) / count,
        "spatial_resolution": None,
        "baseline_agreement": sum(p["decision"]["status"] == p["conventional"]["decision"] for p in cases),
    }


def figures(suite_path: Path, output: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    suite = json.loads(suite_path.read_text(encoding="utf-8"))
    unique = next(case for case in suite["cases"] if case["case"] == "unique")
    model = unique["models"]["NORMAL"]["network"]
    graph = model["topology"]
    fig, grid = plt.subplots(2, 2, figsize=(11, 8), layout="constrained")
    axes = grid.ravel()
    point = {"J": (0, 0), "A": (1, 1), "B": (1, 0), "C": (1, -1)}
    for pipe, u, v in graph["edges"]:
        axes[0].annotate("", xy=point[v], xytext=point[u], arrowprops={"arrowstyle": "->"})
        axes[0].text(0.55, point[v][1] * 0.55 + 0.1, f"{pipe} / F_{pipe}")
    for node, (x, y) in point.items():
        axes[0].scatter(x, y)
        axes[0].text(x, y - 0.22, f"{node} / P_{node}", ha="center")
    axes[0].set(xlim=(-0.25, 1.35), ylim=(-1.35, 1.35), title="Prescribed branch transfers and sensors")
    axes[0].axis("off")
    samples = unique["samples"]
    for name, record in unique["prediction_records"].items():
        intervals = record["outer"][samples:2*samples]
        lo, hi = ([float(Fraction(pair[i])) for pair in intervals] for i in (0, 1))
        line, = axes[1].plot(range(samples), lo, label=name)
        axes[1].fill_between(range(samples), lo, hi, color=line.get_color(), alpha=0.14)
    axes[1].set(xlabel="Time (s)", ylabel="P_A (Pa)", title="Certified coordinate enclosures")
    axes[1].legend()
    group = {"EXCLUDED": 0, "INDETERMINATE": 1, "FEASIBLE": 2}
    status = [case["decision"]["certificate"]["results"][:4] for case in suite["cases"]]
    axes[2].imshow([[group[r["status"]] for r in row] for row in status], aspect="auto",
                   vmin=0, vmax=2, cmap=matplotlib.colors.ListedColormap(["#b6bac0", "#edbd55", "#239a88"]))
    axes[2].set_xticks(range(4), [r["hypothesis"] for r in status[0]])
    axes[2].set_yticks(range(len(status)), [c["case"] for c in suite["cases"]])
    axes[2].set_title("Grey: excluded ? gold: indeterminate ? teal: feasible", fontsize=10)
    scaling = suite["window_scaling"]
    for key, label in (("certified_seconds", "Certified"), ("baseline_seconds", "Outer membership")):
        axes[3].plot([r["samples"] for r in scaling], [1000 * r[key] for r in scaling], "o-", label=label)
    axes[3].set(xlabel="Samples per channel", ylabel="Wall time (ms)", title="Window scaling ? single runs")
    axes[3].legend()
    fig.suptitle(f"CONTROLLED DISCRETE NETWORK · {unique['sha256'][:12]}")
    with output.open("xb") as f:
        fig.savefig(f, format="png", dpi=160)
    plt.close(fig)


def source_report(probe_log: Path | None) -> dict:
    _, inventory = source_case(RAW_DATASET_DIR)
    graph_path = "06_audit_preparation/simulation/h2net_v1/candidate/RELEASED_NETWORK_GRAPH.json"
    graph_bytes = (WORKSPACE_ROOT / graph_path).read_bytes()
    graph = json.loads(graph_bytes)["models"][MODEL]
    if graph["sha256"] != MODEL_HASH:
        raise ValueError("released network graph was extracted from different source bytes")
    for component in graph["components"]:
        component.update({"source_reference": f"system_root.xml SID {component['sid']}",
                          "validation": "STATIC_XML_TRACE",
                          "reference_mass_flow_direction": "UNKNOWN"})
    graph["provenance"] = {"record": graph_path, "record_sha256": hashlib.sha256(graph_bytes).hexdigest(),
                           "extractor": "tools/simulation/extract_released_network.py"}
    probe = {"isolated_copy": True, "solver": "ode14x", "step_s": 0.8, "stop_s": 1.6,
             "outcome": "NOT_RECORDED", "simulation_outputs": None}
    if probe_log is not None:
        log = probe_log.read_bytes()
        probe["log_sha256"] = hashlib.sha256(log).hexdigest()
        messages = log.decode("utf-16" if log.startswith(b"\xff\xfe") else "utf-8-sig", errors="replace")
        if "5202" in messages:
            probe["outcome"] = "MATLAB_STARTUP_MATHWORKS_SERVICE_ERROR_5202"
        else:
            probe["outcome"] = "REVIEW_PROBE_LOG"
    inventory.update({
        "path": "B_PARTIALLY_RECOVERABLE", "model": MODEL, "source_physical_certification": "BLOCKED",
        "boundary_flow_orientation": "UNKNOWN_EFFECTIVE_SIGN_AND_CONTROL_VOLUME_ROLE",
        "compressor": "Controlled pressure-source blocks; validated fault map unavailable",
        "region_mapping": "UNKNOWN_NO_VALIDATED_SOURCE_FAULT_REGION_ASSIGNMENT",
        "source_port_graph": graph,
        "matlab_probe": probe,
    })
    return inventory


def write_record(path: Path, value):
    with path.open("x", encoding="utf-8") as file:
        json.dump(value, file, indent=2, sort_keys=True, allow_nan=False)
        file.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("benchmark", "replay", "source", "figure"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--input", type=Path)
    args = parser.parse_args()
    if args.action in {"replay", "figure"} and args.input is None:
        parser.error("--input is required")
    if args.action != "replay" and args.output is None:
        parser.error("--output is required")
    if args.action == "benchmark":
        cases = [build(name) for name in CASES]
        # Additional window lengths on the same model are complexity probes only.
        scaling = [build("unique", samples)[1] for samples in (3, 9, 17, 33, 65)]
        records = [p for p, _ in cases]
        replay_checks = {p["case"]: replay(p) for p in records}
        if not all(replay_checks.values()):
            raise SystemExit("certificate replay mismatch")
        write_record(args.output, {"cases": records, "metrics": summarize(records),
                                  "performance": [runtime for _, runtime in cases],
                                  "window_scaling": scaling, "replay": replay_checks,
                                  "software_commit": subprocess.check_output(
                                      ["git", "rev-parse", "HEAD"], cwd=WORKSPACE_ROOT, text=True).strip()})
    elif args.action == "replay":
        records = json.loads(args.input.read_text(encoding="utf-8"))["cases"]
        if not records or not all(replay(record) for record in records):
            raise SystemExit("certificate replay mismatch")
        print(f"Replayed {len(records)} complete case records")
    elif args.action == "source":
        write_record(args.output, source_report(args.input))
    else:
        figures(args.input, args.output)


if __name__ == "__main__":
    main()
