"""D1 (H2-SimNet topology attribution): evidence-referenced correction matrix and a GATED replication workflow.

Two modes:
  matrix   (default) — build the per-run correction matrix from the registered manifest v0.2, candidate v0.3 and the
           forensic sensor-signature evidence. Read-only; never changes a label or manifest.
  replicate — refuses (exit 3, BLOCKED_BY_PROVENANCE) unless BOTH
           (a) an owner decision record 06_audit_preparation/protocol2/OWNER_DECISION_D1.yaml exists with
               decision: B, decided_by: <dataset owner>, date, and the v0.3 manifest SHA-256 it approves; and
           (b) a runner authorization YAML (scope EXPLORATORY_REPLICATION) is passed with --authorization.
           Only then does it print the exact frozen-runner command; it never fabricates either record.
Usage: python d1_correction.py [matrix|replicate --authorization <yaml>]
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import pandas as pd
import yaml

V2 = Path(__file__).resolve().parents[2]
REPO = Path(__file__).resolve().parents[4]
P2 = REPO / "06_audit_preparation/protocol2"
V02 = REPO / "06_audit_preparation/phase6_resolution/CANDIDATE_MANIFEST_V02.csv"
V03 = P2 / "CANDIDATE_MANIFEST_V03.csv"
ATT = REPO / "03_results/diagnostics/forensics/source_model_attribution.csv"
DECISION = P2 / "OWNER_DECISION_D1.yaml"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def matrix():
    v2 = pd.read_csv(V02)
    v3 = pd.read_csv(V03)
    att = pd.read_csv(ATT)
    m = v2[["Scenario_ID", "topology", "label_mapped", "eligible_primary"]].merge(
        v3[["Scenario_ID", "topology_release", "topology_source_model", "source_model_evidence"]], on="Scenario_ID", how="left").merge(
        att[["Scenario_ID", "source_folder_or_file", "file_sha256", "extended_sensors_active", "abs_PS4_minus_PS8",
             "abs_PS4_minus_PS9", "inferred_source_model", "consistent"]], on="Scenario_ID", how="left")
    m["verified_fact"] = ("sensor signature measured in the file: extended sensors active=" + m.extended_sensors_active.astype(str)
                          + ", |PS4-PS8|=" + m.abs_PS4_minus_PS8.astype(str) + ", |PS4-PS9|=" + m.abs_PS4_minus_PS9.astype(str)
                          + " -> source model " + m.inferred_source_model)
    m["inference_not_verified"] = m.consistent.map({False: "release folder naming swapped (authors' intended naming not stated in the release)",
                                                    True: "none"})
    m["proposed_change"] = m.apply(lambda r: f"topology {r.topology} -> {r.topology_source_model}" if r.topology != r.topology_source_model else "none", axis=1)
    m["labels_changed"] = False
    m["decision_status"] = "PROPOSED_ONLY — D1 NOT_RECORDED"
    out = V2 / "01_audit"
    out.mkdir(parents=True, exist_ok=True)
    m.to_csv(out / "D1_CORRECTION_MATRIX.csv", index=False, lineterminator="\n")
    s = dict(runs=len(m), topology_changes=int((m.proposed_change != "none").sum()),
             eligible_changes=int(((m.proposed_change != "none") & m.eligible_primary).sum()),
             label_changes=0, v02_sha256=sha(V02), v03_sha256=sha(V03), attribution_sha256=sha(ATT),
             owner_decision_record_present=DECISION.exists())
    pd.Series(s).to_csv(out / "D1_CORRECTION_SUMMARY.csv", header=["value"], lineterminator="\n")
    print(s)


def replicate(auth: Path | None):
    if not DECISION.exists():
        print(f"BLOCKED_BY_PROVENANCE: no owner decision record at {DECISION.relative_to(REPO)}. The dataset owner (Yazan) must "
              "record D1 (A/B/C); this script never creates that record.")
        sys.exit(3)
    d = yaml.safe_load(DECISION.read_text(encoding="utf-8"))
    if d.get("decision") != "B" or d.get("approved_manifest_sha256") != sha(V03) or not d.get("decided_by") or not d.get("date"):
        print("BLOCKED_BY_PROVENANCE: decision record is not D1 = B for the current v0.3 manifest hash.")
        sys.exit(3)
    if auth is None or not auth.exists() or yaml.safe_load(auth.read_text(encoding="utf-8")).get("scope") != "EXPLORATORY_REPLICATION":
        print("BLOCKED_BY_AUTHORIZATION: pass --authorization <yaml> with scope EXPLORATORY_REPLICATION (project lead).")
        sys.exit(3)
    print("Authorized. Run, then analyse with h1_validation/scripts/h1_analysis.py --r2-run <out>:")
    print(f"python tools/experiments/run_primary_protocol.py --config <v0.3-derived config> --authorization {auth} "
          "--execute-primary --out 03_results/primary_protocol/EXPLORATORY_REPLICATION_V03")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", nargs="?", default="matrix", choices=["matrix", "replicate"])
    ap.add_argument("--authorization", type=Path)
    a = ap.parse_args()
    matrix() if a.mode == "matrix" else replicate(a.authorization)
