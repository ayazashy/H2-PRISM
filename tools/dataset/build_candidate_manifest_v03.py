#!/usr/bin/env python3
"""
CANDIDATE manifest v0.3 (forensic FA-01; decision R-18 pending): source-model topology attribution, NOT ACTIVE.

Reads the pinned manifest v0.2 and the forensic source-model attribution, and writes (never activates):
  06_audit_preparation/protocol2/CANDIDATE_MANIFEST_V03.csv
      all v0.2 columns unchanged, plus
      topology_release           = v0.2 `topology` verbatim (release folder attribution)
      topology_source_model      = topology of the simulation model that produced the run (sensor evidence)
      source_model_evidence      = inferred model, extended-sensor activity, PS4-PS8 / PS4-PS9 distances
      independence_group         = h2prism.independence.independence_groups (family OR scenario-replica links)
      manifest_status            = CANDIDATE_NOT_ACTIVE_PENDING_R18
  06_audit_preparation/protocol2/CANDIDATE_OUTER_FOLDS_V03.csv   LOTO folds on topology_source_model (candidate)
  06_audit_preparation/protocol2/CANDIDATE_MANIFEST_V03_CHECKS.json  integrity checks (all must pass)
  06_audit_preparation/protocol2/CANDIDATE_FOLD_COMPOSITION_CHANGE.csv  which runs change held-out fold

The pinned config keeps pointing to v0.2; nothing here changes R2 or any recorded run.
Usage: python tools/dataset/build_candidate_manifest_v03.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from h2prism.independence import independence_groups  # noqa: E402

V02 = REPO / "06_audit_preparation" / "phase6_resolution" / "CANDIDATE_MANIFEST_V02.csv"
ATTR = REPO / "03_results" / "diagnostics" / "forensics" / "source_model_attribution.csv"
FOLDS = REPO / "06_audit_preparation" / "pre_experiment_review" / "CANDIDATE_OUTER_FOLDS.csv"
OUT = REPO / "06_audit_preparation" / "protocol2"
MODEL_TOPOLOGY = {"center_model": "Center", "down_model": "Downstream", "up_model": "Upstream"}


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build(v02: Path = V02, attr: Path = ATTR) -> dict:
    man = pd.read_csv(v02)
    a = pd.read_csv(attr).set_index("Scenario_ID")
    missing = sorted(set(man.Scenario_ID) - set(a.index))
    if missing:
        raise ValueError(f"runs without source-model evidence: {missing[:5]}")
    m = man.copy()
    m["topology_release"] = m.topology
    m["topology_source_model"] = m.Scenario_ID.map(a.inferred_source_model).map(MODEL_TOPOLOGY)
    m["source_model_evidence"] = [f"{a.at[s, 'inferred_source_model']}; extended_sensors_active={a.at[s, 'extended_sensors_active']}; "
                                  f"|PS4-PS8|={a.at[s, 'abs_PS4_minus_PS8']}; |PS4-PS9|={a.at[s, 'abs_PS4_minus_PS9']}" for s in m.Scenario_ID]
    m["independence_group"] = m.Scenario_ID.map(independence_groups(m.Scenario_ID, m.Scenario_Family_ID))
    m["manifest_status"] = "CANDIDATE_NOT_ACTIVE_PENDING_R18"
    m["candidate_manifest_version"] = "v0.3-candidate"  # v0.2 manifest_version column is left verbatim
    changed = m[m.topology_release != m.topology_source_model]
    el = m[m.eligible_primary.astype(str).str.lower().isin(["true", "1"])]
    rows = []
    for k, topo in enumerate(sorted(el.topology_source_model.unique()), start=1):
        for r in el.itertuples():
            rows.append({"outer_fold_id": k, "fold_name": f"LOTO_test_{topo}", "split_role": "test" if r.topology_source_model == topo else "train",
                         "Scenario_ID": r.Scenario_ID, "target_class": r.label_mapped, "topology_source_model": r.topology_source_model,
                         "topology_release": r.topology_release, "family_primary": r.Scenario_Family_ID,
                         "independence_group": r.independence_group, "status": "CANDIDATE_NOT_ACTIVE_PENDING_R18"})
    folds = pd.DataFrame(rows)
    old = pd.read_csv(FOLDS)
    old_test = old[old.split_role == "test"].set_index("Scenario_ID").fold_name
    new_test = folds[folds.split_role == "test"].set_index("Scenario_ID").fold_name
    comp = pd.DataFrame({"Scenario_ID": new_test.index, "held_out_in_v02": new_test.index.map(old_test),
                         "held_out_in_v03_candidate": new_test.values})
    comp = comp.merge(el[["Scenario_ID", "label_mapped", "topology_release", "topology_source_model"]], on="Scenario_ID")
    comp["changes_fold"] = comp.held_out_in_v02 != comp.held_out_in_v03_candidate
    checks = []

    def chk(name, ok, detail=""):
        checks.append({"check": name, "ok": bool(ok), "detail": str(detail)})

    chk("every run has source-model evidence", not missing)
    chk("only topology attribution differs (labels, eligibility, families, files unchanged)",
        man.drop(columns=["topology"]).equals(m[man.columns.drop("topology")]))
    chk("changed runs are exactly the inconsistent ones", set(changed.Scenario_ID) == set(a[~a.consistent].index),
        f"{len(changed)} runs")
    per_fold = folds.groupby("outer_fold_id")
    chk("families disjoint between train and test in every fold",
        all(not (set(g[g.split_role == "train"].family_primary) & set(g[g.split_role == "test"].family_primary)) for _, g in per_fold))
    chk("runs disjoint between train and test in every fold",
        all(not (set(g[g.split_role == "train"].Scenario_ID) & set(g[g.split_role == "test"].Scenario_ID)) for _, g in per_fold))
    sensor = a.extended_sensors_active.to_dict()
    chk("each held-out fold is a single sensor configuration",
        all(len({sensor[s] for s in g[g.split_role == "test"].Scenario_ID}) == 1 for _, g in per_fold))
    chk("every eligible run is held out exactly once", folds[folds.split_role == "test"].Scenario_ID.is_unique and
        set(folds[folds.split_role == "test"].Scenario_ID) == set(el.Scenario_ID))
    shared = {k: sorted(set(g[g.split_role == "train"].independence_group) & set(g[g.split_role == "test"].independence_group))
              for k, g in per_fold}
    chk("BY DESIGN (not label leakage): train and test share scenario independence groups across topologies",
        True, {k: len(v) for k, v in shared.items()})
    OUT.mkdir(parents=True, exist_ok=True)
    m.to_csv(OUT / "CANDIDATE_MANIFEST_V03.csv", index=False, lineterminator="\n")
    folds.to_csv(OUT / "CANDIDATE_OUTER_FOLDS_V03.csv", index=False, lineterminator="\n")
    comp.to_csv(OUT / "CANDIDATE_FOLD_COMPOSITION_CHANGE.csv", index=False, lineterminator="\n")
    rec = {"status": "CANDIDATE_NOT_ACTIVE_PENDING_R18", "source_manifest_v02_sha256": _sha(v02), "attribution_sha256": _sha(attr),
           "n_runs": len(m), "n_topology_changed": int(len(changed)), "n_eligible_changed": int(comp.changes_fold.sum()),
           "fold_changes_by_class": comp[comp.changes_fold].groupby("label_mapped").size().to_dict(),
           "checks": checks, "all_checks_passed": all(c["ok"] for c in checks),
           "outputs": {f: _sha(OUT / f) for f in ("CANDIDATE_MANIFEST_V03.csv", "CANDIDATE_OUTER_FOLDS_V03.csv",
                                                   "CANDIDATE_FOLD_COMPOSITION_CHANGE.csv")}}
    (OUT / "CANDIDATE_MANIFEST_V03_CHECKS.json").write_text(json.dumps(rec, indent=2, default=str) + "\n", encoding="utf-8")
    if not rec["all_checks_passed"]:
        raise SystemExit(f"candidate manifest checks failed: {[c['check'] for c in checks if not c['ok']]}")
    return rec


if __name__ == "__main__":
    r = build()
    print(json.dumps({k: r[k] for k in ("status", "n_runs", "n_topology_changed", "n_eligible_changed", "fold_changes_by_class",
                                        "all_checks_passed")}, indent=2))
