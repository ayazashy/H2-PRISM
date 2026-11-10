#!/usr/bin/env python3
"""
Build candidate manifest v0.2 (PROVISIONALLY_SELECTED - PENDING YAZAN SIGNOFF) from the pinned
Phase-3 candidate package. No raw data are read or modified; selections are recorded, not approved.

Selected candidate options (Phase 6 resolution; see 06_audit_preparation/phase6_resolution/YAZAN_RESOLUTION.md):
  Scenario_Family_ID      = family_primary (extended/conservative kept for sensitivity)          Y-D03/Y-D04
  exclusions              = compound (leakG4brokenC1) and annotation conflict (brokenC1G5_weak)   Y-D05b/c
  multi-location leaks    = LEAK                                                                  Y-D05d
  post-delay rows         = excluded at window level (labels untouched)                           Y-D06a
  phase                   = not used; verified onset recorded                                     Y-D06b
  location analysis       = prohibited for files whose filename and labels disagree (leakG5G6)    Y-D05a

Usage (repo root): python tools/dataset/build_manifest_v02.py
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "06_audit_preparation" / "pre_experiment_review"
OUT = ROOT / "06_audit_preparation" / "phase6_resolution" / "CANDIDATE_MANIFEST_V02.csv"
STATUS = "PROVISIONALLY_SELECTED_PENDING_YAZAN_SIGNOFF"
VERSION = "v0.2-candidate"


def main() -> None:
    m = pd.read_csv(PKG / "CANDIDATE_SCENARIO_MANIFEST.csv")
    inv = pd.read_csv(PKG / "CANDIDATE_FILE_INVENTORY.csv").set_index("file")
    out = pd.DataFrame({
        "Scenario_ID": m.Scenario_ID,
        "Scenario_Family_ID": m.family_primary,
        "family_extended_sensitivity": m.family_extended,
        "family_conservative_sensitivity": m.family_conservative,
        "topology": m.topology,
        "run_stem": m.run_stem,
        "raw_label_columns": m.raw_active_label_columns.fillna(""),
        "label_mapped": m.candidate_primary_class,
        "eligible_primary": m.eligible_primary_candidate,
        "exclusion_reason": m.class_note.where(~m.eligible_primary_candidate, ""),
        "timing_status": "ROW_LEVEL_LABELS_ONSET_VERIFIED",
        "onset_s": m.onset_s_verified,
        "delay_last_active_s": m.delay_last_active_s,
        "window_label_rule": "row_level; boundary windows excluded; pre/post-event rows excluded (PENDING F-D05)",
        "phase_used": False,
        "location_analysis_allowed": m.filename_vs_label_locations.eq("MATCH"),
        "file_noise_added": m.canonical_noise_added_file,
        "sha256_noise_added": m.canonical_noise_added_file.map(lambda f: inv.loc[f, "sha256"] if isinstance(f, str) and f in inv.index else ""),
        "file_clean": m.canonical_clean_file,
        "sha256_clean": m.canonical_clean_sha256,
        "candidate_primary_realization": "noise_added (PENDING F-D01)",
        "evidence": "pre_experiment_review/FAMILY_RELATIONSHIP_EVIDENCE.csv; LABEL_AND_TIMING_CORRECTIONS.md",
        "manifest_version": VERSION,
        "status": STATUS,
    }).sort_values("Scenario_ID", kind="mergesort")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    data = out.to_csv(index=False, lineterminator="\n", float_format="%.10g").encode("utf-8")
    OUT.write_bytes(data)
    print(OUT.name, len(out), "rows; eligible", int(out.eligible_primary.sum()), "; sha256", hashlib.sha256(data).hexdigest())


if __name__ == "__main__":
    main()
