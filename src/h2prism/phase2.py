"""Run and replay the Phase 2 reference and source-observation experiments."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from time import perf_counter
from xml.etree import ElementTree
from zipfile import ZipFile

from .certified_evidence import (
    AffineBoxAdapter, Channel, DecisionStatus, HypothesisModel, MeasurementContract, diagnose,
)
from .data.loader import RAW_DATASET_DIR, WORKSPACE_ROOT, list_scenarios, load_scenario
from .data_contracts import NetworkRecord, SensorRecord
from .gas_physics import PerfectGas
from .phase2_evaluation import EvaluationCase, summarize
from .physical_reference import Bound, BoundStatus, ControlVolume, Evidence, EvidenceCategory, EvidenceLedger, Uncertainty

SCENARIO = "SCEN_CENTER_NORMAL_BASELINE_NORMALITY_GEST_CENTER"
MODEL = "Normal_HNetwork_gest_center"
PARQUET = "H2-SimNet-clean/normality-scenarios/parquet/normality_gest_center.parquet"
MODEL_DIR = "MATLAB_SIMSCAPE_Simulation/normality_scenarios/normality_datasets"
DATA_HASH = "8f11abe64f4991cfefa8c91d33e4ad720d53e93ef040e425c7d292814a645c74"
MODEL_HASH = "710711f41e33adb9ea54220580adefd0065eeb9a8a376727dd045fc474ed7b1e"
SID = dict(zip([f"PS{i}" for i in range(1, 11)] + ["MFS1", "MFS2", "MFS3"],
               ("50", "51", "52", "109", "187", "318", "392", "418", "428", "431", "311", "210", "218")))
COMPATIBILITY = {
    "stored_clock": "AVAILABLE_AND_VERIFIED",
    "pressure_converter_units": "AVAILABLE_AND_VERIFIED",
    "released_mass_flow_units": "AVAILABLE_BUT_UNVERIFIED",
    "source_geometry": "AVAILABLE_AND_VERIFIED",
    "release_to_source_transformation": "MISSING",
    "signed_control_volume_boundary_rates": "MISSING",
    "operating_input_histories": "MISSING",
    "temperature_telemetry": "MISSING",
    "resolved_initial_state": "AVAILABLE_BUT_UNVERIFIED",
    "hydrogen_gas_model": "INCOMPATIBLE",
    "sensor_clock_parameter_and_discrepancy_bounds": "MISSING",
}


def checked_file(path: Path, expected: str) -> Path:
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError(f"source checksum mismatch: {path.name}")
    return path


def source_inventory(raw: Path) -> dict:
    data = checked_file(raw / PARQUET, DATA_HASH)
    model = checked_file(raw / MODEL_DIR / f"{MODEL}.slx", MODEL_HASH)
    assets = sorted(p.relative_to(raw).as_posix() for p in raw.rglob("*") if p.is_file())
    with ZipFile(model) as archive:
        xml = ElementTree.fromstring(archive.read("simulink/systems/system_root.xml"))
    blocks = {b.attrib["SID"]: b for b in xml.findall("Block")}

    def properties(sid, names):
        entries = {p.attrib["Name"]: p.text for p in blocks[sid].iter("P") if "Name" in p.attrib}
        return {key: {"value": entries[key], "unit": entries.get(key + "_unit")}
                for key in names if key in entries}

    selected = set(SID.values()) | {"1", "4", "47", "48", "49", "106", "107", "221", "309",
                                    "239", "55", "195", "200", "217", "224", "316"}
    connections = []
    for line in xml.findall("Line"):
        endpoints = [p.text for p in line.iter("P") if p.get("Name") in {"Src", "Dst", "SrcConnect", "DstConnect"}]
        if any(endpoint and endpoint.split("#")[0] in selected for endpoint in endpoints):
            connections.append(endpoints)
    ledger = (
        Evidence("gas_block", properties("4", ("gas_spec", "R", "Z", "cp_ref", "mu_ref", "k_ref", "T_ref",
                  "h_ref", "T_min_perfect", "T_max_perfect", "p_min_perfect", "p_max_perfect")), "mixed",
                 f"{model.name} system_root.xml SID 4", EvidenceCategory.SOURCE, "STATIC_XML_VERIFIED",
                 SCENARIO, MODEL, limitations="Air-like specific gas constant; composition not declared."),
        Evidence("composition", None, "mol/mol", f"{model.name} SID 4", EvidenceCategory.UNKNOWN,
                 "MISSING", SCENARIO, MODEL, ("gas_block",), "Release title does not specify a blend."),
        Evidence("deterministic_error_bounds", None, "mixed", "ReadME.txt and raw verification report",
                 EvidenceCategory.UNKNOWN, "MISSING", SCENARIO, MODEL,
                 limitations="Gaussian noise description does not specify finite hard bounds."),
    )
    return {
        "authority": "Zenodo V2 DOI 10.5281/zenodo.17871393; raw_verification/ZENODO_SOURCE_PROVENANCE.json",
        "selection": "Manifest-eligible Center NORMAL clean Parquet with stored clock and local named source model",
        "source_files": {data.relative_to(raw).as_posix(): DATA_HASH, model.relative_to(raw).as_posix(): MODEL_HASH},
        "available_asset_counts": {suffix: sum(a.endswith(suffix) for a in assets)
                                   for suffix in (".parquet", ".csv", ".slx", ".m", ".txt")},
        "ancestry": f"{MODEL_DIR}/models_launcher.m and save_model_data_center.m link model to solver CSV; "
                    "the 1 s release conversion and exact run configuration are unverified",
        "blocks": {sid: {"name": blocks[sid].attrib["Name"], "parameters": properties(sid, (
            "length", "area", "roughness", "p_init", "T_init", "mdot_init", "source_type", "pressure_spec",
            "reservoir_pressure", "reservoir_temperature", "pressure_differential", "power_spec"))}
            for sid in sorted(selected)},
        "block_port_connections": connections,
        "sensor_to_block": SID,
        "sensor_map_basis": "SLX root Goto/From paths to subsystem 462 inputs 1?13, MATLAB exporter",
        "sensor_converter_sids": dict(zip(SID, ("56", "57", "58", "113", "192", "319", "395",
                                                "419", "429", "432", "314", "211", "219"))),
        "excluded_columns": ["PS11", "PS12", "MFS4"],
        "measurement_semantics": {
            "PS": "Pressure converter configured in MPa; reference semantics require source verification",
            "MFS": "Mass flow rate reported in kg/s at sensor ports; boundary roles and signs unresolved",
            "temperature": "No released temperature telemetry",
        },
        "compatibility": COMPATIBILITY,
        "evidence_ledger": json.loads(EvidenceLedger(ledger).to_json()),
        "uncertainty": {name: json.loads(Bound(None, unit, BoundStatus.UNKNOWN,
                                              "No deterministic bound in local release evidence", MODEL).to_json())
                        for name, unit in (("pressure_error", "MPa"), ("mass_flow_error", "kg/s"),
                                           ("temperature", "K"), ("synchronization", "s"),
                                           ("initial_mass", "kg"), ("boundary_rates", "kg/s"),
                                           ("parameters", "mixed"), ("model_discrepancy", "Pa"))},
    }


def source_case(raw: Path, start: int = 0, stop: int = 3) -> tuple[MeasurementContract, dict]:
    inventory = source_inventory(raw)
    expected_path = f"H2-SimNet-Dataset/{PARQUET}"
    catalog = list_scenarios()
    match = catalog[(catalog["Scenario_ID"] == SCENARIO) & (catalog["file"] == expected_path)]
    if len(match) != 1 or match.iloc[0]["target_class"] != "NORMAL":
        raise ValueError("expected one manifest-eligible NORMAL export")
    frame = load_scenario(raw / PARQUET)
    if frame.index.name != "Timestamp" or not 0 <= start < stop <= len(frame):
        raise ValueError("stored timestamp index or window invalid")
    window = frame.iloc[start:stop]
    timestamps = tuple(map(float, window.index))
    sensors = tuple(SensorRecord(name, MODEL, "block", sid,
                                "pressure" if name.startswith("PS") else "mass_flow",
                                "MPa" if name.startswith("PS") else "kg/s", 1)
                    for name, sid in SID.items())
    channels = tuple(Channel(s.sensor_id, s.unit, timestamps, "stored Parquet Timestamp index",
                             tuple(map(float, window[s.sensor_id])), ())
                     for s in sensors if s.sensor_id in window)
    family = str(match.iloc[0]["Scenario_Family_ID"])
    measurement = MeasurementContract(sensors, timestamps, channels, SCENARIO, family,
                                      f"sha256:{DATA_HASH}#rows={start}:{stop}", "UNKNOWN_BOUND: release supplies no hard error set")
    inventory["measurement_qc"] = measurement.issues()
    inventory["compatibility_verdict"] = "BLOCKED_MISSING_SOURCE_PHYSICS_AND_UNCERTAINTY"
    inventory["observation"] = {"scenario": SCENARIO, "family": family, "rows": [start, stop],
                                "stored_interval_s": 1, "conversions": [],
                                "missing_sample_rows": {name: window.index[window[name].isna()].tolist()
                                                        for name in SID if name in window}}
    return measurement, inventory


def reference(case: str) -> tuple[MeasurementContract, tuple[HypothesisModel, ...]]:
    network = NetworkRecord("lumped-fixture", ("CV",), (), "isothermal conservation fixture",
                            {"designation": "constructed single-component perfect gas"})
    gas = PerfectGas(250, 1, 1000, 1e-5, 0.02, "constructed fixture gas")
    domain = "cv-v1"
    ledger = EvidenceLedger(tuple(Evidence(key, value, unit, "declared controlled fixture",
                                           EvidenceCategory.ENGINEERING, "ASSUMED", network.network_id, domain)
                                  for key, value, unit in (("volume", 75, "m3"), ("temperature", 300, "K"),
                                                           ("specific_gas_constant", 250, "J/(kg K)"),
                                                           ("compressibility", 1, "1"))))

    def bound(lo, hi, unit):
        return Bound((lo, hi), unit, BoundStatus.ASSUMED, "declared controlled fixture", domain)

    uncertainty = Uncertainty(bound(100, 100, "kg"), bound(2, 2, "kg/s"), bound(2, 2, "kg/s"),
                              bound(0, 0, "kg/s"), bound(0, 0, "s"), bound(0, 0, "Pa"))
    cv = ControlVolume(network, domain, "CV", "P", 75, 300, gas, uncertainty, ledger,
                       "NONNEGATIVE_INLET_OUTLET_SEPARATE_LEAK", 10)
    leaky = replace(cv, uncertainty=replace(uncertainty, leak=bound(1, 1, "kg/s")))
    models = (HypothesisModel("NORMAL", cv, ("zero additional withdrawal",)),
              HypothesisModel("LEAK", leaky, ("controlled extra withdrawal at CV; no orifice law",)))
    times = (0, 1, 2)
    errors = (0, 1000, 2000) if case == "overlap" else (0, 0, 0)
    values = (100000, 99000, 98000) if case == "leak" else (100000,) * 3
    if case == "missing":
        errors = ()
    sensor = SensorRecord("P", network.network_id, "node", "CV", "pressure", "Pa", 1)
    measurement = MeasurementContract((sensor,), times, (Channel("P", "Pa", times, "fixture clock", values, errors),),
                                      case, f"fixture:{case}", "closed-form fixture", "declared absolute errors")
    return measurement, models


def replay(payload: dict) -> dict[str, bool]:
    certificate = payload["decision"]["certificate"]
    record = certificate["measurement"]
    measurement = MeasurementContract(
        tuple(SensorRecord(**s) for s in record["sensors"]), tuple(record["timestamps_s"]),
        tuple(Channel(**c) for c in record["channels"]), record["run_id"], record["independence_group"],
        record["source_id"], record["uncertainty_basis"], record["cadence_tolerance_s"],
    )
    issues = measurement.issues()
    checks = {}
    for result in certificate["results"]:
        state = result["status"]
        if state == "INDETERMINATE":
            continue
        name = result["hypothesis"]
        config = payload["model_configuration"].get(name)
        if config is None or issues:
            checks[name] = False
            continue
        # Rebuild the originally declared model and compare against the recorded proof.
        _, models = reference(payload["experiment_id"])
        original = next((m for m in models if m.name == name), None)
        if original is None or config != json.loads(original.adapter.to_json()):
            checks[name] = False
            continue
        try:
            affine = original.adapter.affine(measurement)
            if result["witness"] is not None:
                candidate = tuple(map(Fraction, result["witness"]))
                affine = replace(affine, search=lambda _: candidate)
            replayed = affine.check(HypothesisModel(name, affine, ()), measurement)
        except (TypeError, ValueError, ArithmeticError):
            checks[name] = False
            continue
        fresh = json.loads(replayed.to_json())
        checks[name] = all(fresh[key] == result[key] for key in ("status", "reason", "witness", "separation", "affine_model"))
    return checks


def execute(case: str, output: Path) -> dict:
    if case == "source":
        measurement, evidence = source_case(RAW_DATASET_DIR)
        models = tuple(HypothesisModel(name, None, ("SOURCE_PHYSICS_INCOMPATIBLE_OR_INCOMPLETE",))
                       for name in ("NORMAL", "LEAK", "COMPRESSOR_FAULT", "DELAY"))
    else:
        measurement, models = reference(case)
        evidence = {"kind": "ANALYTICAL_REFERENCE", "ground_truth": "LEAK" if case == "leak" else "NORMAL"}
    start = perf_counter()
    decision = diagnose(measurement, models)
    elapsed = perf_counter() - start
    payload = {
        "experiment_id": case, "schema": "phase2/1",
        "software_base": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=WORKSPACE_ROOT, text=True).strip(),
        "implementation_sha256": {
            name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ("phase2.py", "physical_reference.py", "certified_evidence.py")
        },
        "evidence_manifest": evidence,
        "input_manifest": {"source_id": measurement.source_id, "family": measurement.independence_group},
        "model_configuration": {m.name: json.loads(m.adapter.to_json()) if m.adapter else None for m in models},
        "validation": "SOURCE_ADAPTER_BLOCKED" if case == "source" else "EXACT_REFERENCE_ONLY",
        "empirical_evaluation_eligible": False,
        "decision": json.loads(decision.to_json()),
        "reproduce": f'$env:PYTHONPATH="src"; .venv/Scripts/python.exe -m h2prism.phase2 {case} --output "{output.as_posix()}"',
    }
    payload["certificate_replay"] = replay(payload)
    payload["reference_accounting"] = summarize((EvaluationCase(
        measurement.independence_group, "ANALYTICAL_REFERENCE", decision, evidence.get("ground_truth"),
        case != "source", case != "source",
        all(payload["certificate_replay"].values()) if payload["certificate_replay"] else None,
    ),))
    # Runtime is measured and isolated from the deterministic evidence payload.
    output.mkdir(parents=True, exist_ok=False)
    (output / "result.json").write_text(json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (output / "runtime.json").write_text(json.dumps({"diagnose_wall_seconds": elapsed}) + "\n", encoding="utf-8")
    return payload


def rebuild_figure(result_path: Path, output: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    payload = json.loads(result_path.read_text(encoding="utf-8"))
    cert = payload["decision"]["certificate"]
    if payload["validation"] != "EXACT_REFERENCE_ONLY" or not cert["feasible"]:
        raise ValueError("Figure requires an executed feasible controlled reference case")
    clock = cert["measurement"]["timestamps_s"]
    channel = cert["measurement"]["channels"][0]
    fig, ax = plt.subplots(figsize=(6.4, 3.8), layout="constrained")
    for result in cert["results"]:
        model = result["affine_model"]
        if model is None:
            continue
        bounds = [tuple(map(Fraction, b)) for b in model["bounds"]]
        lower, upper = [], []
        for base, row in zip(model["offset"], model["matrix"]):
            terms = [(Fraction(a) * lo, Fraction(a) * hi) for a, (lo, hi) in zip(row, bounds)]
            lower.append(float(Fraction(base) + sum(map(min, terms))))
            upper.append(float(Fraction(base) + sum(map(max, terms))))
        line, = ax.plot(clock, lower, label=result["hypothesis"])
        ax.fill_between(clock, lower, upper, color=line.get_color(), alpha=0.2)
    ax.errorbar(clock, channel["values"], yerr=channel["absolute_errors"],
                fmt="ko", capsize=4, label="Observed admissible intervals")
    ax.set(title=f"ANALYTICAL REFERENCE | {payload['decision']['status']}",
           xlabel="Time (s)", ylabel="Pressure (Pa)")
    ax.legend()
    with output.open("xb") as file:
        fig.savefig(file, format="png", dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=("normal", "leak", "overlap", "missing", "source", "replay", "figure"))
    parser.add_argument("--output", type=Path, required=True, help="New output directory, or result.json for replay")
    parser.add_argument("--input", type=Path, help="Executed result.json for figure")
    args = parser.parse_args()
    if args.case == "figure":
        if args.input is None:
            parser.error("figure requires --input")
        rebuild_figure(args.input, args.output)
    elif args.case == "replay":
        checks = replay(json.loads(args.output.read_text(encoding="utf-8")))
        print(json.dumps(checks, sort_keys=True))
        if not checks or not all(checks.values()):
            raise SystemExit(1)
    else:
        payload = execute(args.case, args.output)
        print(payload["decision"]["status"])


if __name__ == "__main__":
    main()
