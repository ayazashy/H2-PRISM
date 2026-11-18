"""Read-only discovery of tabular result artifacts (CSV and Markdown tables) in result trees.

Scope: 03_results/**, study_b/**, 06_audit_preparation/** and 01_dataset_audit/**. For every CSV: rows, columns and
header; for Markdown files: the number of pipe tables and their sizes. Each file is given a role from its path and name:
PUBLICATION_TABLE, ANALYSIS_OUTPUT, REGISTER_OR_AUDIT, MANIFEST_OR_QC, RUN_OUTPUT. Nothing is modified.
Writes 03_results/poster_inventory/data/table_files_raw.csv.
"""
import re
import subprocess
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "03_results/poster_inventory/data"
ROOTS = ("03_results/", "study_b/", "06_audit_preparation/", "01_dataset_audit/")


def role(p):
    s, name = p.lower(), Path(p).name.lower()
    if "poster_inventory" in s:
        return "SELF"
    if any(k in name for k in ("manifest", "sha256sums", "verification", "inventory", "scope_check", "checksum", "index",
                               "triage", "register", "migration", "scan", "hashes", "provenance")):
        return "MANIFEST_OR_QC" if any(k in name for k in ("manifest", "sha256", "verification", "checksum", "scope", "hashes",
                                                           "migration", "scan", "index")) else "REGISTER_OR_AUDIT"
    if "/tables/" in s or re.match(r"(t\d|tab_|table_|h1-t|v2-t|a\d\d|ts\d)", name):
        return "PUBLICATION_TABLE"
    if any(k in s for k in ("/analysis/", "/benchmarks/", "/results/", "/evidence_enhancement/", "/publication/")):
        return "ANALYSIS_OUTPUT"
    if any(k in s for k in ("ablation_runs/", "primary_protocol/", "derived/", "diagnostics/", "/folds/", "runs/")):
        return "RUN_OUTPUT"
    return "REGISTER_OR_AUDIT"


def md_tables(text):
    tabs, cur = [], []
    for line in text.splitlines():
        if line.strip().startswith("|") and line.strip().endswith("|"):
            cur.append(line)
        elif cur:
            tabs.append(cur)
            cur = []
    if cur:
        tabs.append(cur)
    out = []
    for t in tabs:
        if len(t) >= 3 and re.match(r"^\|\s*:?-{3,}", t[1].strip()):
            out.append((len(t) - 2, t[0].count("|") - 1))
    return out


def main():
    files = subprocess.run(["git", "-c", "core.quotepath=false", "ls-files", "*.csv", "*.md", "*.tsv"], cwd=REPO,
                           capture_output=True, text=True, check=True).stdout.splitlines()
    rows = []
    for f in files:
        if not f.startswith(ROOTS):
            continue
        p = REPO / f
        r = dict(path=f, filename=p.name, folder=str(Path(f).parent).replace("\\", "/"), format=p.suffix[1:].upper(),
                 role=role(f), bytes=p.stat().st_size)
        if p.suffix.lower() in (".csv", ".tsv"):
            try:
                if p.stat().st_size > 50_000_000:
                    r.update(rows=None, columns=None, header="(not read: > 50 MB)")
                else:
                    d = pd.read_csv(p, sep="\t" if p.suffix == ".tsv" else ",", low_memory=False)
                    r.update(rows=len(d), columns=d.shape[1], header="|".join(map(str, d.columns))[:400])
            except Exception as e:                                          # malformed or non-tabular CSV
                r.update(rows=None, columns=None, header=f"(unreadable: {type(e).__name__})")
        else:
            t = md_tables(p.read_text(encoding="utf-8", errors="replace"))
            if not t:
                continue
            r.update(rows=sum(x[0] for x in t), columns=max(x[1] for x in t), header=f"{len(t)} markdown tables",
                     md_tables=len(t))
        rows.append(r)
    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "table_files_raw.csv", index=False, lineterminator="\n")
    print(len(df), "tabular files")
    print(df.groupby(["role", "format"]).size().to_string())
    pt = df[df.role == "PUBLICATION_TABLE"]
    print(pt.groupby("folder").size().sort_values(ascending=False).to_string())


if __name__ == "__main__":
    main()
