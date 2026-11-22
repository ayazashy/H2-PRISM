#!/usr/bin/env python3
"""
H2-PRISM read-only research artifact validator (Task A12 -- Ahmed; schema
interpretation requires Faisal acceptance, dataset identifiers Yazan verification).

STATUS: IMPLEMENTED + TESTED (fixture-based). READ-ONLY: input artifacts are opened
for reading only; outputs go to a separate --out-dir, which must not contain any
input artifact.

Checks per artifact listed in a spec YAML (see configs/artifact_validation.yaml):
  * existence                                  -> MISSING_ARTIFACT
  * required columns (from interface contracts) -> MISSING_COLUMNS
  * unique key columns                         -> DUPLICATE_KEYS
  * non-null required identifier columns       -> NULL_IDENTIFIERS
  * expected SHA-256 (if declared)             -> HASH_MISMATCH
  * status vocabulary                          -> UNSUPPORTED_STATUS
  * checksum-manifest reconciliation (optional) e.g. data/sample vs raw_checksums.sha256
Missing evidence (MISSING_ARTIFACT, NOT_CHECKED) is reported separately from failed
validation (FAIL); nothing is backfilled.

Usage:
  python tools/research_audit/validate_artifacts.py --spec configs/artifact_validation.yaml \
      --out-dir 06_audit_preparation/artifact_validation
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import yaml

ALLOWED_STATUSES = {
    "VERIFIED", "REPORTED_UNVERIFIED", "INFERRED", "PENDING", "NOT_AVAILABLE", "SPECIFIED",
    "IMPLEMENTED", "TESTED", "EXECUTED", "VALIDATED", "FROZEN", "DEFERRED", "NOT_SUPPORTED",
    "PROVISIONAL", "DEVELOPMENT_ONLY", "EXPLORATORY_SECONDARY", "BLOCKED", "PARTIALLY_IMPLEMENTED",
    "NOT_STARTED", "UNKNOWN",
}


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def read_table(path: Path) -> pd.DataFrame:
    if path.suffix == ".csv":
        return pd.read_csv(path)
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    if path.suffix == ".json":
        return pd.DataFrame(json.loads(path.read_text(encoding="utf-8")))
    raise ValueError(f"unsupported tabular type {path.suffix}")


def _row(artifact, rule, outcome, detail, disposition=""):
    return {"artifact": artifact, "rule": rule, "outcome": outcome, "detail": detail, "disposition": disposition}


def validate_artifact(root: Path, spec: Dict, contracts: Optional[Dict]) -> List[Dict]:
    rel = spec["path"]
    p = root / rel
    out: List[Dict] = []
    if not p.exists():
        out.append(_row(rel, "exists", "MISSING_ARTIFACT", "file not found",
                        "evidence absent - not a validation failure of content"))
        return out
    out.append(_row(rel, "exists", "PASS", ""))
    if spec.get("sha256"):
        got = sha256_file(p)
        out.append(_row(rel, "sha256", "PASS" if got == spec["sha256"] else "HASH_MISMATCH",
                        f"expected {spec['sha256']} got {got}"))
    if p.suffix not in (".csv", ".parquet", ".json"):
        return out
    try:
        df = read_table(p)
    except Exception as exc:  # noqa: BLE001 - report, never crash the whole audit
        out.append(_row(rel, "readable", "FAIL", f"{type(exc).__name__}: {exc}"))
        return out
    req = list(spec.get("required_columns", []))
    schema = spec.get("schema")
    if schema and contracts:
        sch = contracts.get("contracts", {}).get(schema, {})
        req += [c["name"] if isinstance(c, dict) else c for c in sch.get("required_columns", [])]
        req += list(sch.get("metadata_columns", []))
    req = list(dict.fromkeys(req))
    if req:
        miss = [c for c in req if c not in df.columns]
        out.append(_row(rel, f"required_columns[{schema or 'spec'}]", "FAIL" if miss else "PASS",
                        f"missing: {miss}" if miss else f"{len(req)} columns present"))
    key = spec.get("unique_key")
    if key:
        key = [key] if isinstance(key, str) else list(key)
        if all(k in df.columns for k in key):
            dup = int(df.duplicated(subset=key).sum())
            out.append(_row(rel, f"unique_key{key}", "FAIL" if dup else "PASS", f"{dup} duplicate key rows"))
        else:
            out.append(_row(rel, f"unique_key{key}", "NOT_CHECKED", "key columns absent"))
    for col in spec.get("non_null", []):
        if col in df.columns:
            nn = int(df[col].isna().sum())
            out.append(_row(rel, f"non_null[{col}]", "FAIL" if nn else "PASS", f"{nn} null values"))
    sc = spec.get("status_column")
    if sc:
        if sc in df.columns:
            bad = sorted(set(map(str, df[sc].dropna().unique())) - ALLOWED_STATUSES)
            out.append(_row(rel, f"status_vocabulary[{sc}]", "UNSUPPORTED_STATUS" if bad else "PASS",
                            f"unsupported: {bad}" if bad else ""))
        else:
            out.append(_row(rel, f"status_vocabulary[{sc}]", "NOT_CHECKED", "status column absent"))
    return out


def reconcile_checksums(root: Path, manifest_rel: str, files_glob: str, match_by: str = "basename_and_hash") -> List[Dict]:
    """Check that each file matching ``files_glob`` has its SHA-256 listed in the manifest."""
    out: List[Dict] = []
    man = root / manifest_rel
    if not man.exists():
        return [_row(manifest_rel, "checksum_manifest", "MISSING_ARTIFACT", "checksum manifest not found")]
    entries = {}
    for line in man.read_text(encoding="utf-8").splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) == 2:
            entries.setdefault(parts[0], []).append(parts[1].lstrip("*"))
    files = sorted(root.glob(files_glob))
    if not files:
        out.append(_row(files_glob, "checksum_reconciliation", "MISSING_ARTIFACT", "no files matched"))
    for f in files:
        h = sha256_file(f)
        hits = entries.get(h, [])
        same_name = [e for e in hits if Path(e).name == f.name]
        if same_name:
            out.append(_row(str(f.relative_to(root)).replace("\\", "/"), "checksum_reconciliation", "PASS",
                            f"matches {same_name[0]}" + (f" (+{len(hits) - 1} more)" if len(hits) > 1 else "")))
        elif hits:
            out.append(_row(str(f.relative_to(root)).replace("\\", "/"), "checksum_reconciliation", "FAIL",
                            f"hash matches differently named entry {hits[0]}"))
        else:
            out.append(_row(str(f.relative_to(root)).replace("\\", "/"), "checksum_reconciliation", "FAIL",
                            "hash not present in checksum manifest"))
    return out


def run(spec_path: Path, out_dir: Path, root: Path) -> pd.DataFrame:
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    contracts = None
    if spec.get("contracts"):
        cp = root / spec["contracts"]
        contracts = yaml.safe_load(cp.read_text(encoding="utf-8")) if cp.exists() else None
    inputs = {(root / a["path"]).resolve() for a in spec.get("artifacts", [])}
    out_dir = out_dir.resolve()
    if any(str(i).startswith(str(out_dir) + "\\") or str(i).startswith(str(out_dir) + "/") or i == out_dir for i in inputs):
        raise SystemExit("refusing: --out-dir contains an input artifact (validator is read-only)")
    rows: List[Dict] = []
    for a in spec.get("artifacts", []):
        rows += validate_artifact(root, a, contracts)
    for rc in spec.get("checksum_reconciliation", []):
        rows += reconcile_checksums(root, rc["manifest"], rc["files_glob"])
    df = pd.DataFrame(rows, columns=["artifact", "rule", "outcome", "detail", "disposition"])
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "ARTIFACT_VALIDATION_DISCREPANCIES.csv", index=False, lineterminator="\n")
    counts = df["outcome"].value_counts().to_dict()
    lines = ["# Artifact validation summary (generated, read-only)", "",
             f"Spec: `{spec_path.as_posix()}`", "", "| Outcome | Count |", "| --- | ---: |"]
    lines += [f"| {k} | {v} |" for k, v in sorted(counts.items())]
    lines += ["", "Non-PASS rows:", ""]
    for _, r in df[df["outcome"] != "PASS"].iterrows():
        lines.append(f"- **{r['outcome']}** `{r['artifact']}` [{r['rule']}] {r['detail']}")
    (out_dir / "ARTIFACT_VALIDATION_SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return df


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--spec", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--root", type=Path, default=Path("."))
    a = ap.parse_args(argv)
    df = run(a.spec, a.out_dir, a.root)
    print(df["outcome"].value_counts().to_string())
    return 1 if (df["outcome"].isin(["FAIL", "HASH_MISMATCH", "UNSUPPORTED_STATUS"])).any() else 0


if __name__ == "__main__":
    sys.exit(main())
