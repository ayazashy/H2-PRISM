"""Structural admission checks for a prospective validation manifest."""
import argparse
import json
from pathlib import Path

PARTITIONS = ("development", "calibration", "untouched_test")
LABELS = {"NORMAL", "LEAK", "FAULT", "DELAY"}
REQUIRED = ("root_id","model_sha256","raw_export_sha256","scenario_id","partition",
            "topology_id","profile_id","gas_definition","event_class","sensor_schema",
            "initial_state_receipt","boundary_history","solver_and_time_grid","units",
            "measurement_error_evidence","label_source","independence_receipt")


def admission(records, regions):
    issues = []
    if not regions or len(set(regions)) != len(regions):
        issues.append("require a predefined nonempty location universe")
    seen = set()
    for row in records:
        missing = [key for key in REQUIRED if not row.get(key)]
        if missing:
            issues.append(f"{row.get('scenario_id')}: missing {missing}")
        sid = row.get("scenario_id")
        if sid in seen:
            issues.append(f"{sid}: duplicate scenario")
        seen.add(sid)
        label = row.get("event_class")
        if row.get("partition") not in PARTITIONS or label not in LABELS:
            issues.append(f"{sid}: invalid class or partition")
        if label != "NORMAL" and (row.get("onset_clock") is None or row.get("end_clock") is None):
            issues.append(f"{sid}: missing event times")
        if label == "LEAK" and row.get("location_truth") not in regions:
            issues.append(f"{sid}: leak location outside predefined candidate set")
    # Any shared raw data or producing checkpoint must stay in one split.
    for field in ("root_id","parent_checkpoint","raw_export_sha256"):
        assigned = {}
        for row in records:
            value = row.get(field)
            if not value:
                continue
            partition = row.get("partition")
            if value in assigned and assigned[value] != partition:
                issues.append(f"{field} crosses partitions: {value}")
            assigned[value] = partition
    counts = {}
    for part in PARTITIONS:
        rows = [r for r in records if r.get("partition")==part]
        counts[part] = {label:len({r["root_id"] for r in rows if r.get("root_id")
                                  and r.get("event_class")==label}) for label in sorted(LABELS)}
        if not all(counts[part].values()):
            issues.append(f"{part}: required class lacks root")
        found = {r.get("location_truth") for r in rows if r.get("event_class")=="LEAK" and r.get("root_id")}
        if not set(regions)<=found:
            issues.append(f"{part}: missing location support")
    return dict(status="BLOCKED" if issues else "STRUCTURAL_CHECKS_PASSED",
                root_counts=counts,issues=sorted(set(issues)),
                limitations="Receipts, generating independence, physical evidence and statistical precision require separate review.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest",type=Path,help="JSON with records and regions arrays")
    args = parser.parse_args()
    result = admission(**json.loads(args.manifest.read_text(encoding="utf-8-sig")))
    print(json.dumps(result,indent=2))
    raise SystemExit(1 if result["issues"] else 0)
