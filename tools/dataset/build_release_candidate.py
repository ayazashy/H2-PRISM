#!/usr/bin/env python3
"""
Protocol 2.0 release candidate RC1 (single candidate; NOT APPROVED; confirmatory execution BLOCKED).

Built from the pinned candidate config CANDIDATE_PROTOCOL_2_0.yaml with the component decisions of the project lead's
direction (2026-11-13) and the D2 diagram trace:
  B  source-model topology (manifest v0.3)          INCLUDED_CONDITIONAL on D1 = option B
  C  13 name-matched "common" sensors               EXCLUDED: names are not positions (SENSOR_CORRESPONDENCE.csv)
  C' 12 position-matched sensor blocks (map v0.1)   INCLUDED_CONDITIONAL on D2 acceptance AND development arm H
  D  independence-group support counting            INCLUDED (integrity rule)
  E  evidence-conflict policy                       OPTIONAL, default OFF (no development evidence either way)
  F  E_h evidence margin                            EXCLUDED (code and counterexample tests retained)
  D(x) inside s_C                                    RETAINED as comparator; semantics disclosed
Also writes the registered development arm H_POSITION_MATCHED (no authorization is created here).
Outputs: 06_audit_preparation/protocol2/release_candidate/{P2_0_RC1.yaml, P2_0_RC1.sha256, RC1_COMPONENTS.csv},
         06_audit_preparation/protocol2/arms/H_POSITION_MATCHED.yaml, ABLATION_MATRIX_ADDENDUM_H.csv.
Usage: python tools/dataset/build_release_candidate.py
"""

from __future__ import annotations

import copy
import hashlib
import sys
from pathlib import Path

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[2]
P2 = REPO / "06_audit_preparation" / "protocol2"
CAND = P2 / "CANDIDATE_PROTOCOL_2_0.yaml"
PMAP = P2 / "CANDIDATE_SENSOR_POSITION_MAP_V01.csv"
BASE = REPO / "06_audit_preparation" / "FINAL_EXPERIMENT_CONFIG.yaml"
OUT = P2 / "release_candidate"
RC_STATUS = "RELEASE_CANDIDATE_P2_0_RC1_NOT_APPROVED"

sys.path.insert(0, str(REPO / "src"))
from h2prism.position_map import canonical_channels, load_position_map  # noqa: E402


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


COMPONENTS = [
    ("B", "source-model topology attribution (manifest v0.3)", "INCLUDED_CONDITIONAL", "D1 = option B (Yazan)",
     "dev group-balanced accuracy 0.47 -> 0.88; confident predictions outside the Center+Upstream fold almost absent"),
    ("C", "13 name-matched sensors PS1-PS10, MFS1-MFS3", "EXCLUDED",
     "refuted by the diagram trace: down model logs other blocks as PS5-PS10",
     "arm C/G1 results describe a mixed representation, not common sensors"),
    ("C_prime", "12 position-matched sensor blocks (map v0.1)", "INCLUDED_CONDITIONAL",
     "D2 acceptance of the position map (Yazan) AND authorized development arm H run and reviewed (project lead / Faisal)",
     "support diagnostic only (no classifier fitted); no development performance yet"),
    ("D", "independence-group support counting", "INCLUDED", "Faisal acceptance as integrity rule",
     "no classifier change; pseudo-independent support = 0"),
    ("E", "evidence-conflict policy", "OPTIONAL_DEFAULT_OFF", "Faisal design choice",
     "no estimable operating point with errors in development"),
    ("F", "E_h evidence margin", "EXCLUDED", "re-evaluate only on independent data",
     "undefined for ~80% of windows; AUROC not above D(x)"),
    ("Dx", "D(x) inside s_C", "RETAINED_AS_COMPARATOR", "registered contrast s_C vs s_C_minus_D",
     "neighbourhood class agreement only; no increment at the single matched development point"),
    ("CAL", "calibration selection none/sigmoid", "INCLUDED", "development-only selection, fallback none",
     "none selected in every fold"),
    ("TGT", "development-only target rule", "INCLUDED", "Faisal", "targets fixed before any outer evaluation"),
    ("META", "fail-closed meta-model", "INCLUDED", "Faisal", "undefined -> NOT_ESTIMABLE, never a substitute score"),
    ("UNIT", "bootstrap unit = independence group", "INCLUDED", "Faisal (D4)", "13 groups on current data"),
]


def build():
    cand = yaml.safe_load(CAND.read_text(encoding="utf-8"))
    pmap = load_position_map(PMAP)
    canon = canonical_channels(pmap)
    pm = {"file": PMAP.relative_to(REPO).as_posix(), "sha256": _sha(PMAP)}
    rc = copy.deepcopy(cand)
    rc["status"] = RC_STATUS
    rc["version"] = "protocol-2.0-rc1"
    rc["derived_from"] = {"file": CAND.relative_to(REPO).as_posix(), "sha256": _sha(CAND)}
    rc["features"]["channels"] = canon
    rc["features"]["position_map"] = pm
    rc["policy_primary"].pop("evidence_conflict", None)  # E optional, default off
    rc["distinguishability"]["semantics"] = (
        "D(x) = q(1) - q(2) of the k-nearest-neighbour class shares in the development reference: agreement of the "
        "neighbourhood with one class, NOT physical distinguishability and NOT independent evidence")
    rc["evaluation"]["uncertainty"]["unit"] = "independence_group"
    rc["evaluation"]["claims"] = {
        "cross_topology_comparability": "NOT_CLAIMED until D2 is accepted; then only for the 12 mapped blocks",
        "primary_contrast": "s_C vs s_C_minus_D at the development-fixed target; null is reported as null",
        "superiority": "never claimed from development evidence or from inconclusive confirmation results"}
    rc["execution"] = {
        "confirmatory": "BLOCKED",
        "blocked_until": ["D1 recorded by dataset owner", "D2 position map accepted by dataset owner",
                          "development arm H authorized, run and reviewed", "component decisions recorded by methods owner",
                          "independent confirmation data per INDEPENDENT_CONFIRMATION_DATA_SPEC.md, partition hashed",
                          "new status and a new authorization scoped to the frozen config hash"],
        "current_data_role": "development only; never confirmatory selection"}
    rc["owner_signoffs"] = {"yazan": "NOT_RECORDED", "faisal": "NOT_RECORDED", "ahmed": "NOT_RECORDED"}
    rc["components"] = {c[0]: {"description": c[1], "decision": c[2], "requires": c[3], "development_evidence": c[4]}
                        for c in COMPONENTS}
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / "P2_0_RC1.yaml"
    p.write_text("# Protocol 2.0 RELEASE CANDIDATE RC1 - NOT APPROVED. Confirmatory execution BLOCKED (runner refuses\n"
                 f"# status {RC_STATUS}). Generated by tools/dataset/build_release_candidate.py.\n"
                 + yaml.safe_dump(rc, sort_keys=False), encoding="utf-8")
    (OUT / "P2_0_RC1.sha256").write_text(f"{_sha(p)}  P2_0_RC1.yaml\n", encoding="utf-8")
    pd.DataFrame(COMPONENTS, columns=["component", "description", "decision", "requires", "development_evidence"]) \
        .to_csv(OUT / "RC1_COMPONENTS.csv", index=False, lineterminator="\n")

    # registered development arm H (= G1 with the position map instead of name-matched channels); no authorization
    g1 = yaml.safe_load((P2 / "arms" / "G1_DATA_CORRECTIONS.yaml").read_text(encoding="utf-8"))
    h = copy.deepcopy(g1)
    h["arm_id"] = "H_POSITION_MATCHED"
    h["version"] = "protocol-2.0-ablation:H_POSITION_MATCHED"
    h["features"]["channels"] = canon
    h["features"]["position_map"] = pm
    hp = P2 / "arms" / "H_POSITION_MATCHED.yaml"
    hp.write_text("# Registered DEVELOPMENT-ONLY arm H_POSITION_MATCHED (tools/dataset/build_release_candidate.py).\n"
                  "# NOT AUTHORIZED. Runs only with --develop and an authorization scoped DEVELOPMENT_EXPERIMENT:H_POSITION_MATCHED.\n"
                  + yaml.safe_dump(h, sort_keys=False), encoding="utf-8")
    pd.DataFrame([{
        "arm_id": "H_POSITION_MATCHED", "components": "B+C_prime",
        "scientific_question": "With diagram position-matched sensors, is the down model still out of support, and do classifier and decision metrics hold?",
        "targeted_failure": "FA-02 revised: name-matched channels compare different physical sensors",
        "acceptance_criterion": "no unmapped or padded channel among inputs (structural) AND dev OUT_OF_SUPPORT share in folds with the down model lower than G1 AND dev group-balanced accuracy not lower than G1 by more than 0.05",
        "evidence_status": "EXPLORATORY_DEVELOPMENT", "config_file": hp.relative_to(REPO).as_posix(), "config_sha256": _sha(hp),
        "authorization_scope": "DEVELOPMENT_EXPERIMENT:H_POSITION_MATCHED", "authorization_status": "NOT_AUTHORIZED",
        "registered": "2026-11-13, before any run"}]).to_csv(P2 / "ABLATION_MATRIX_ADDENDUM_H.csv", index=False, lineterminator="\n")
    print(_sha(p), _sha(hp))


if __name__ == "__main__":
    build()
