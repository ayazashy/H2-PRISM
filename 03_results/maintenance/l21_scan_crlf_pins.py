"""L21: find every checksum pin whose validity depends on the checkout's line endings.

For each tracked text file stored with LF line endings in the index (git ls-files --eol: i/lf), the script computes the
SHA-256 of its canonical LF bytes and of the same content with CRLF endings. Every 64-hex token in tracked text records
is matched against both. Two checkout-dependent categories result:
  CRLF_PIN  a record pins the CRLF encoding: fresh LF checkouts (eol=lf attribute, or any non-Windows platform) fail;
  LF_PIN    a record pins the LF encoding of a file WITHOUT an eol=lf attribute: Windows checkouts with
            core.autocrlf=true write CRLF and fail.
LF pins of files that already carry eol=lf are portable and not reported. The content-equivalence proof is
constructive: CRLF bytes = LF bytes with every b"\n" replaced by b"\r\n" (blobs contain no CR).
Writes 03_results/maintenance/L21_CRLF_PIN_SCAN.csv (one row per pin occurrence).
Usage (repository root): python 03_results/maintenance/l21_scan_crlf_pins.py
"""
import hashlib
import re
import subprocess
from collections import defaultdict
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "03_results/maintenance/L21_CRLF_PIN_SCAN.csv"
TEXT = {".csv", ".json", ".yaml", ".yml", ".md", ".txt", ".sha256", ".py", ".toml", ".ini", ".tsv", ".log", ""}
HEX = re.compile(rb"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])")


def main():
    raw = subprocess.run(["git", "-c", "core.quotepath=false", "ls-files", "--eol", "-z"], cwd=REPO, capture_output=True,
                         check=True).stdout.decode("utf-8")
    lf, crlf, attr = {}, {}, {}
    tokens = defaultdict(set)
    skip = {OUT.relative_to(REPO).as_posix(), "03_results/maintenance/L21_MIGRATION_LOG.csv"}
    for e in filter(None, raw.split("\0")):
        meta, path = e.split("\t", 1)
        parts = meta.split()
        p = REPO / path
        if not p.is_file() or p.stat().st_size > 30_000_000 or path in skip:
            continue
        b = p.read_bytes()
        if parts[0] == "i/lf":
            canon = b.replace(b"\r\n", b"\n")
            lf[hashlib.sha256(canon).hexdigest()] = path
            crlf[hashlib.sha256(canon.replace(b"\n", b"\r\n")).hexdigest()] = path
            attr[path] = " ".join(parts[2:])
        if parts[0] != "i/-text" and p.suffix.lower() in TEXT:
            for t in set(HEX.findall(b)):
                tokens[t.decode()].add(path)
    lf_of = {v: k for k, v in lf.items()}
    crlf_of = {v: k for k, v in crlf.items()}
    rows = []
    for h, recs in tokens.items():
        if h in crlf and h not in lf:
            f, cat = crlf[h], "CRLF_PIN"
        elif h in lf and "eol=lf" not in attr.get(lf[h], ""):
            f, cat = lf[h], "LF_PIN"
        else:
            continue
        for r in sorted(recs):
            rows.append(dict(pinned_file=f, category=cat, eol_attribute=attr.get(f, ""), lf_sha256=lf_of[f],
                             crlf_sha256=crlf_of[f], record=r))
    df = pd.DataFrame(rows, columns=["pinned_file", "category", "eol_attribute", "lf_sha256", "crlf_sha256", "record"])
    df = df.sort_values(["pinned_file", "category", "record"])
    df.to_csv(OUT, index=False, lineterminator="\n")
    cats = df.groupby("pinned_file").category.agg(lambda s: "+".join(sorted(set(s))))
    print(f"{len(df)} pin occurrences in {df.record.nunique()} records; {df.pinned_file.nunique()} files")
    print(cats.value_counts().to_string())


if __name__ == "__main__":
    main()
