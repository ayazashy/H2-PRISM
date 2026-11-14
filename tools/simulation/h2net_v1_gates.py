#!/usr/bin/env python3
"""
H2Net v1 stage gates for the Windows handoff (fail-closed). Every stage prints what is missing and exits 2.

  python tools/simulation/h2net_v1_gates.py template          -> writes PARAMETER_DECISIONS_TEMPLATE.yaml (placeholders)
  python tools/simulation/h2net_v1_gates.py check <stage>     -> exit 0 = gate open, 2 = closed (reasons printed)
stages
  targets   X06: decision record DECIDED / DECIDED_WITH_DEFERRALS; S3, S4 (with demand_levels), S6, V8 decided by a named
            person (delegates to h2net_v1_v2_targets.gate/params)
  build     targets + S7 sensor amendment and S8 decided; EXECUTOR_DESIGNATION.yaml names the executor and is signed by the
            project lead; H2Net v1 grant ACTIVE with unchanged bound hashes; V2_TARGETS.json computed from THIS record
  validate  build + MATLAB readiness reports pass tools/matlab/check_matlab_reports.py; BUILD_REPORT.json says COMPLETE
  v7        validate + a separate grant AUTH_H2NET_V1_V7.yaml (authorized: true, ACTIVE, scope VALIDATION:H2NET_V1_V7)
  dataset   validate + VALIDATION_REPORT.json overall PASS (V2-V6, V8, D1) + methods_review decided by Faisal (detectability,
            independence/partition, shortcut controls, leak labels, noise model WITH cited sources) + a separate grant
            AUTH_H2NET_V1_DATASET.yaml (scope SIMULATION_GENERATION:H2NET_V1_DATASET, bound to the decision-record hash)
Nothing here records or infers an approval: placeholders ("<...>") and missing names always close the gate.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import h2net_v1_v2_targets as v2t  # noqa: E402

REPO = v2t.pn.REPO
H2 = REPO / "06_audit_preparation" / "simulation" / "h2net_v1"
DECISIONS = H2 / "PARAMETER_DECISIONS.yaml"
RUN = REPO / "h2net_v1_run"                          # all outputs of Yazan's execution (git-ignored)
EXECUTOR = H2 / "EXECUTOR_DESIGNATION.yaml"
AUTH_H2NET = H2 / "AUTH_MODEL_DEVELOPMENT_H2NET_V1_REQUEST.yaml"
AUTH_V7 = H2 / "AUTH_H2NET_V1_V7.yaml"
AUTH_DATASET = H2 / "AUTH_H2NET_V1_DATASET.yaml"
STAGES = ("targets", "build", "validate", "v7", "dataset")


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _named(v) -> bool:
    return bool(v) and not str(v).strip().startswith("<")


def _load(p: Path):
    return yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else None


def _grant_ok(path: Path, scope: str, problems: list, bind_decisions: bool = False):
    g = _load(path)
    if not g:
        problems.append(f"missing separate authorization {path.name} (scope {scope})")
        return
    if not (g.get("authorized") is True and g.get("status") == "ACTIVE" and g.get("scope") == scope and _named(g.get("authorized_by"))):
        problems.append(f"{path.name}: needs authorized: true, status: ACTIVE, scope: {scope}, named authorized_by")
    if bind_decisions and g.get("decisions_sha256") != sha(DECISIONS):
        problems.append(f"{path.name}: decisions_sha256 does not match the current decision record")


def check(stage: str, decisions: Path = DECISIONS, run: Path = RUN) -> list:
    problems = []
    dec = _load(decisions)
    if dec is None:
        return [f"decision record missing: {decisions}"]
    try:
        v2t.gate(dec)
        v2t.params(dec)
    except v2t.Refused as e:
        problems.append(f"decision record: {e}")
    if stage == "targets" or problems:
        return problems
    for k in ("S7_sensors_and_units", "S8_numerics"):
        v = dec.get(k) or {}
        if not (v.get("decided") and _named(v.get("decided_by"))):
            problems.append(f"{k} must be decided with a named decided_by (S7: sensor set of the design-freeze spec 2.1)")
    s7 = ((dec.get("S7_sensors_and_units") or {}).get("value") or {})
    if "MFS0" not in json.dumps(s7):
        problems.append("S7 value does not include the mass-balance sensors (MFS0, MFS2s, MFS5-7, PS_N6, PS_END)")
    ex = _load(EXECUTOR)
    if not (ex and _named(ex.get("executor")) and _named(ex.get("designated_by")) and ex.get("grant") == "MODEL_DEVELOPMENT:H2NET_V1"):
        problems.append(f"{EXECUTOR.name}: executor and designated_by (project lead) must be named for grant MODEL_DEVELOPMENT:H2NET_V1")
    g = _load(AUTH_H2NET) or {}
    if not (g.get("authorized") is True and g.get("status") == "ACTIVE"):
        problems.append("H2Net v1 grant not ACTIVE")
    for b in (g.get("specification"), g.get("reference_code")):
        if not b or sha(REPO / b["file"]) != b["sha256"]:
            problems.append(f"grant-bound file changed: {b and b['file']} (grant void; request a new one)")
    tg = run / "targets" / "V2_TARGETS.json"
    if not tg.exists() or json.loads(tg.read_text(encoding="utf-8")).get("decisions_sha256") != sha(decisions):
        problems.append(f"{tg.relative_to(REPO) if tg.is_relative_to(REPO) else tg}: compute V2 targets from the current decision record first")
    if stage == "build":
        return problems
    rd = run / "readiness"
    r = subprocess.run([sys.executable, str(REPO / "tools/matlab/check_matlab_reports.py"), str(rd)], capture_output=True, text=True)
    if r.returncode != 0:
        problems.append(f"MATLAB readiness not verified in {rd}: {r.stdout.strip().splitlines()[:3]}")
    br = run / "build" / "BUILD_REPORT.json"
    if not br.exists() or json.loads(br.read_text(encoding="utf-8")).get("status") != "COMPLETE":
        problems.append("BUILD_REPORT.json missing or not COMPLETE (every structural op must succeed)")
    if stage == "validate":
        return problems
    if stage == "v7":
        _grant_ok(AUTH_V7, "VALIDATION:H2NET_V1_V7", problems)
        return problems
    vr = run / "validation" / "VALIDATION_REPORT.json"
    if not vr.exists() or json.loads(vr.read_text(encoding="utf-8")).get("overall") != "PASS":
        problems.append("VALIDATION_REPORT.json missing or not PASS")
    mr = dec.get("methods_review") or {}
    if not (mr.get("decided") and _named(mr.get("decided_by")) and "faisal" in str(mr.get("decided_by")).lower()):
        problems.append("methods_review must be decided by Faisal (detectability, independence, shortcut controls, labels, noise model)")
    nm = (mr.get("value") or {}).get("noise_model") or {}
    if not nm or any(not _named(c.get("source")) for c in nm.values() if isinstance(c, dict)):
        problems.append("noise_model must give, per channel type, sigma and a cited source")
    _grant_ok(AUTH_DATASET, "SIMULATION_GENERATION:H2NET_V1_DATASET", problems, bind_decisions=True)
    return problems


TEMPLATE = """# H2Net v1 decision record TEMPLATE (design-freeze spec, commit dd2f548 + reconciliation e0d5697).
# Owners copy the sections into PARAMETER_DECISIONS.yaml and replace EVERY <...>. Placeholders keep every gate closed.
status: <DECIDED | DECIDED_WITH_DEFERRALS>
decided_by: <names and roles>
date: <YYYY-MM-DD>
S1_gas: {decided: true, value: normal hydrogen, H2_REALGAS_TLU2.json}
S2_thermal_boundary: {decided: false, deferred: true, reason: "U-value source missing; steady-state targets are isothermal"}
S3_compressor_stations:            # M1 = D1 + D7 (design-freeze spec section 1)
  decided: <true>
  decided_by: <Yazan + designated modeller>
  value:
    supply_reservoir_pressure_MPa: 3.2
    C1_pressure_source_sid_55: {discharge_setpoint_MPa: 5.0, power_spec: isentropic}
    C2_pressure_source_sid_239: {discharge_setpoint_MPa: 6.5, power_spec: isentropic}
    aftercoolers: {after: [55, 239], outlet_temperature_K: 313.15, outlet_tolerance_K: <V3 band, e.g. 0.5>, cooler_pipe_length_m: <sized in V3, e.g. 200>}
    efficiency_for_power_reporting: [0.75, 0.85]
    down_model_letdown_sid_111: <"isenthalpic reduction to 4.0 MPa" | DEFERRED>
S4_demand_and_leaks:               # M2, M3, leaks
  decided: <true>
  decided_by: <Yazan (+ Faisal for labels)>
  value:
    nominal_demand_kg_s: {G3: 4.0, G5: 4.0, G4: 5.0, G6: 5.0, END: 2.0}
    demand_levels: [0.6, 0.8, 1.0, 1.2, 1.4]
    allocation_variants: [nominal, shift_G3G5_+25pct]
    load_profiles: {types: [constant, step, ramp, sinusoid], step_fraction: 0.2, ramp_fraction: 0.2, ramp_s: 600, sinus_fraction: 0.15, sinus_period_s: 1800}
    leaks: {pipes: [47, 48, 49, 309, 106, 221], position_fraction: 0.5, Cd: 0.64, classes_percent: [0.5, 2.0, 10.0],
            severity_definition: <A | B>, onset_ramp_s: 10}
S5_discretisation: {decided: false, deferred: true, reason: "segment length from V5; inertia scope <owner>"}
S6_roughness_and_initial_state:    # M4
  decided: <true>
  decided_by: <designated modeller>
  value: {roughness_m: 4.5e-5, initial_state: V2 targets}
  source: <citation>
S7_sensors_and_units:              # amendment: design-freeze spec 2.1
  decided: <true>
  decided_by: <Yazan>
  value: {base: position map v0.1, add: [MFS0, MFS2s, MFS5, MFS6, MFS7, PS_N6, PS_END], released_MFS2: <keep as MFS2_chamber | drop>,
          units: {pressure: MPa absolute, mass_flow: kg/s, temperature: K}}
S8_numerics:
  decided: <true>
  decided_by: <designated modeller>
  value: {reference_solver: ode15s, RelTol: 1.0e-6, MaxStep_s: 1.0, production_solver: "only if within V6 of the reference"}
operating_envelope_V8:             # M5
  decided: <true>
  decided_by: <Yazan + designated modeller>
  value:
    isothermal_reference_temperature_K: 313.15
    normal: {pressure_MPa: [3.0, 8.0], temperature_K: [270.0, 330.0], velocity_limit_m_s: 20.0, applies_at: pipe outlet}
    fault_and_delay: {min_pressure_MPa: 2.5, max_discharge_temperature_K: 450.0}   # 2.5 MPa is a LOWER bound
  source: <citations>
scenarios:                         # design-freeze spec section 3
  decided: <true>
  decided_by: <Yazan>
  value:
    run_duration_s: <e.g. 7200>
    sample_period_s: <e.g. 1.0>
    onset_window_s: [<e.g. 1800>, <e.g. 5400>]
    faults: [C1_trip, C1_half, C2_trip, C2_half]
    c2_setpoints_MPa: [6.3, 6.5, 6.7]
    delays_s: [60, 120, 240]
    families_per_topology: {development: 10, confirmation: 5}
    master_seed: <integer chosen by the owner>
methods_review:                    # Faisal (design-freeze spec section 4); required before dataset generation
  decided: <true>
  decided_by: <Faisal>
  value:
    detectability: {snr_detectable: 3.0, snr_low: 1.0, rule: "noise fixed from source before SNR; never tuned"}
    independence: {group: initial-state family, partition_by: family, confirmation_sealed: true}
    shortcut_controls: [common onset distribution, pre-onset equality, equal marginals, pre-onset probe at chance]
    leak_labels: <severity definition A | B>
    v4_tolerance_fraction: <restriction-flow tolerance vs the nozzle formula, e.g. 0.05>
    noise_model:
      pressure: {sigma_kPa: <value>, source: <citation>}
      mass_flow: {sigma_kg_s: <value>, source: <citation>}
      temperature: {sigma_K: <value>, source: <citation>}
"""


def main(argv) -> int:
    if argv[:1] == ["template"]:
        out = H2 / "PARAMETER_DECISIONS_TEMPLATE.yaml"
        out.write_text(TEMPLATE, encoding="utf-8", newline="\n")
        print(out)
        return 0
    if len(argv) == 2 and argv[0] == "check" and argv[1] in STAGES:
        p = check(argv[1])
        print(f"GATE {argv[1]}: " + ("OPEN" if not p else "CLOSED"))
        for x in p:
            print("  - " + x)
        return 0 if not p else 2
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
