"""L21 repair: make every checkout reproduce the bytes that the repository's provenance pins certify.

Input: L21_CRLF_PIN_SCAN.csv (l21_scan_crlf_pins.py). For every pinned file:
  * content equivalence is re-proved from the committed blob: sha256(blob) == canonical LF hash, the blob holds no CR,
    and sha256(blob with b"\n" -> b"\r\n") == CRLF hash;
  * CRLF_PIN only  -> append `<path> text eol=crlf` to .gitattributes (convention of commit 484f58c);
  * LF_PIN only    -> append `<path> text eol=lf`;
  * pinned in both encodings by authoritative records -> no line-ending rule can satisfy both; left unchanged, reported.
LF hashes in this project's own derived inventory (integrated_validation_v1 FIGURE_INVENTORY.csv, which hashed this
checkout's LF bytes) and in execution logs are informational, not authoritative pins; they are listed in the log.
Then the affected working copies are re-materialized and every one is checked against its pin.
No pin, record or blob is edited: only .gitattributes and working copies change.
Writes 03_results/maintenance/L21_MIGRATION_LOG.csv.
Usage (repository root): python 03_results/maintenance/l21_apply_eol.py
"""
import hashlib
import subprocess
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
M = REPO / "03_results/maintenance"
NON_AUTHORITATIVE = ("03_results/integrated_validation_v1/publication_q1/quality_control/FIGURE_INVENTORY.csv",
                     "03_results/integrated_validation_v2/03_execution/logs/")
HEADER = ("\n# L21 (maintenance): files whose provenance pins certify specific line endings check out with exactly those\n"
          "# bytes on every platform, as in 484f58c. Content is unchanged (blobs stay LF);\n"
          "# see 03_results/maintenance/L21_MIGRATION_LOG.csv.\n")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def git(*a):
    r = subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True)
    if r.returncode not in (0, 1) or (r.returncode == 1 and a[0] != "grep"):   # git grep exits 1 when nothing matches
        raise subprocess.CalledProcessError(r.returncode, ["git", *a], r.stdout, r.stderr)
    return r.stdout


def records_with(h):
    return [p for p in git("grep", "-l", "-F", h, "HEAD", "--").replace("HEAD:", "").split() if p]


def main():
    scan = pd.read_csv(M / "L21_CRLF_PIN_SCAN.csv")
    rows, rules = [], []
    for f, g in scan.groupby("pinned_file", sort=True):
        blob = subprocess.run(["git", "show", f"HEAD:{f}"], cwd=REPO, capture_output=True, check=True).stdout
        lf_h, crlf_h = g.lf_sha256.iloc[0], g.crlf_sha256.iloc[0]
        equivalent = b"\r" not in blob and sha(blob) == lf_h and sha(blob.replace(b"\n", b"\r\n")) == crlf_h
        crlf_recs, lf_recs = records_with(crlf_h), records_with(lf_h)
        auth_crlf = [p for p in crlf_recs if not p.startswith(NON_AUTHORITATIVE)]
        auth_lf = [p for p in lf_recs if not p.startswith(NON_AUTHORITATIVE)]
        if not equivalent:
            action, rule = "LEFT_UNCHANGED_NOT_EQUIVALENT", ""
        elif auth_crlf and auth_lf:
            action, rule = "LEFT_UNCHANGED_CONFLICTING_PINS", ""
        elif auth_crlf:
            action, rule = "EOL_PINNED_CRLF", "crlf"
        elif auth_lf:
            action, rule = "EOL_PINNED_LF", "lf"
        else:
            action, rule = "LEFT_UNCHANGED_NO_AUTHORITATIVE_PIN", ""
        if rule:
            rules.append((f, rule))
        rows.append(dict(file=f, previous_eol_attribute=g.eol_attribute.iloc[0], action=action, content_equivalent=equivalent,
                         canonical_lf_sha256=lf_h, crlf_sha256=crlf_h, crlf_pinned_in="; ".join(auth_crlf),
                         lf_pinned_in="; ".join(auth_lf),
                         non_authoritative_records="; ".join(sorted(set(crlf_recs + lf_recs) - set(auth_crlf + auth_lf))),
                         worktree_sha256_before=sha((REPO / f).read_bytes())))
    ga = REPO / ".gitattributes"
    text = ga.read_bytes().decode("utf-8")
    assert "L21 (maintenance)" not in text, "already applied"
    ga.write_bytes((text.rstrip("\n") + "\n" + HEADER + "".join(f"{p} text eol={r}\n" for p, r in rules)).encode("utf-8"))
    paths = [p for p, _ in rules]
    for p in paths:                                   # re-materialize with the new attribute
        (REPO / p).unlink()
    for i in range(0, len(paths), 50):
        subprocess.run(["git", "checkout", "--", *paths[i:i + 50]], cwd=REPO, check=True)
    log = pd.DataFrame(rows)
    log["worktree_sha256_after"] = [sha((REPO / f).read_bytes()) for f in log.file]
    target = log.action.map({"EOL_PINNED_CRLF": "crlf_sha256", "EOL_PINNED_LF": "canonical_lf_sha256"})
    log["after_matches_pin"] = [r.worktree_sha256_after == getattr(r, t) if isinstance(t, str) else False
                                for r, t in zip(log.itertuples(), target)]
    log.to_csv(M / "L21_MIGRATION_LOG.csv", index=False, lineterminator="\n")
    print(log.action.value_counts().to_string())
    fixed = log[log.action.str.startswith("EOL_PINNED")]
    print("re-pinned files whose working copy now equals the pin:", int(fixed.after_matches_pin.sum()), "/", len(fixed))
    print(log[~log.action.str.startswith("EOL_PINNED")][["file", "action", "crlf_pinned_in", "lf_pinned_in"]].to_string())


if __name__ == "__main__":
    main()
