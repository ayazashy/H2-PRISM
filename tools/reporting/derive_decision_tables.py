#!/usr/bin/env python3
"""
Authoritative decision-level reporting tables derived from a recorded run's window-level outputs (A13 / F10 reporting).

Why: the runner's aggregate decision_reasons.csv keeps only the FIRST token of a compound reason code (a consequence
such as SPECIFIC_REJECTED_SINGLE_CANDIDATE, not the blocking cause), and rq2.csv pools whichever held-out topologies
were estimable without saying which (forensic FA-10, FA-11). Both facts are recoverable losslessly from the run's own
window-level decisions.parquet / predictions.parquet, which this module reads (never writes) and cross-checks against
the run's registered rq2.csv before writing anything.

Outputs (<out>/<run_dir>/, default 03_results/derived/<run_dir>/):
  rq2_scoped.csv                 per variant x target x mode x class x scope (POOLED_ESTIMABLE or one topology):
                                 denominators (windows, runs, families, scenario ancestors), outcome counts, SPECIFIC
                                 correctness (undefined if no SPECIFIC), ambiguity inclusion (undefined if no set),
                                 topologies_included / topologies_excluded with the exclusion reason
  decision_reasons_primary.csv   mutually exclusive PRIMARY reason per non-SPECIFIC decision (precedence REASON_PRECEDENCE)
  decision_reasons_contributing.csv  non-exclusive contributing reasons (a decision counts once per applicable reason)
  support_flags_scoped.csv       per topology x class: windows, windows with each flag (non-exclusive), any-flag,
                                 flag-free, and the exact flag combinations (exclusive)
  matched_selection_ties.csv     share of each estimable matched selection decided by the PA-1 tie key
  DERIVED_MANIFEST.json          source hashes, run key, code hash, cross-check results
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CLASSES = ["NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"]
SPECIFIC, AMBIGUITY, UNRESOLVED = "SPECIFIC", "AMBIGUITY_SET", "UNRESOLVED"

# Documented precedence for the mutually exclusive PRIMARY reason (first match wins). Rationale: a decision forced to
# UNRESOLVED by an out-of-support / invalid flag never reached ranking; a support flag that blocks SPECIFIC is the
# cause of every downstream rejection; ranking below the matched-coverage cut comes next; set-construction outcomes
# (too broad / all classes) and single-candidate rejection are consequences that only remain when nothing else applies.
REASON_PRECEDENCE = (
    ("FLAG:", "UNRESOLVED_BY_SUPPORT_FLAG"),
    ("FLAG_BLOCKS_SPECIFIC", "SPECIFIC_BLOCKED_BY_SUPPORT_FLAG"),
    ("INVALID_SCORE", "INVALID_SCORE"),
    ("SCORE_BELOW_THRESHOLD", "BELOW_MATCHED_COVERAGE_CUT"),
    ("SET_TOO_BROAD", "AMBIGUITY_SET_TOO_BROAD"),
    ("ALL_CLASS_SET_PREVENTED", "AMBIGUITY_SET_TOO_BROAD"),
    ("SPECIFIC_REJECTED_SINGLE_CANDIDATE", "SINGLE_CANDIDATE_REJECTED"),
)
REASON_LABELS = [lab for _, lab in REASON_PRECEDENCE]


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


sys.path.insert(0, str(REPO / "src"))
from h2prism.independence import ancestor, independence_groups  # noqa: E402


def primary_reason(code) -> str:
    code = "" if code is None or (isinstance(code, float) and np.isnan(code)) else str(code)
    if code.startswith("ACCEPTED"):
        return "ACCEPTED"
    for key, label in REASON_PRECEDENCE:
        if key in code:
            return label
    return "OTHER"


def contributing_reasons(code) -> List[str]:
    code = "" if code is None or (isinstance(code, float) and np.isnan(code)) else str(code)
    out = sorted({label for key, label in REASON_PRECEDENCE if key in code})
    return out or (["ACCEPTED"] if code.startswith("ACCEPTED") else ["OTHER"])


def _incl(y, s) -> bool:
    return str(y) in str(s).split("|")


def _counts(g: pd.DataFrame) -> Dict:
    sp, am = g[g.policy_outcome == SPECIFIC], g[g.policy_outcome == AMBIGUITY]
    n_sp, n_am = len(sp), len(am)
    n_spc = int((sp.y_pred_specific == sp.y_true).sum())
    n_inc = int(sum(_incl(y, s) for y, s in zip(am.y_true, am.ambiguity_set)))
    return {"n_windows": len(g), "n_runs": int(g.Scenario_ID.nunique()), "n_families": int(g.Scenario_Family_ID.nunique()),
            "n_scenario_ancestors": int(g.Scenario_ID.map(ancestor).nunique()),
            "n_independence_groups": int(g.independence_group.nunique()),
            "n_specific": n_sp, "n_specific_correct": n_spc, "n_ambiguity_set": n_am, "n_ambiguity_includes_true": n_inc,
            "n_unresolved": int((g.policy_outcome == UNRESOLVED).sum()),
            "share_specific": n_sp / len(g), "share_ambiguity_set": n_am / len(g),
            "share_unresolved": float((g.policy_outcome == UNRESOLVED).mean()),
            "specific_correct": n_spc / n_sp if n_sp else np.nan,          # undefined (NaN) when no SPECIFIC decision
            "ambiguity_inclusion": n_inc / n_am if n_am else np.nan}       # undefined (NaN) when no ambiguity set


def derive(run: Path) -> Dict[str, pd.DataFrame]:
    dec = pd.read_parquet(run / "decisions.parquet")
    pred = pd.read_parquet(run / "predictions.parquet")
    est = pd.read_csv(run / "estimability.csv")
    groups = independence_groups(pred.Scenario_ID, pred.Scenario_Family_ID)
    meta = pred[["window_id", "Scenario_ID"]].assign(independence_group=pred.Scenario_ID.map(groups))
    d = dec.merge(meta, on="window_id", how="left", validate="many_to_one")
    if d.Scenario_ID.isna().any():
        raise ValueError("decision rows without a matching prediction row")
    topo_of_fold = pred.groupby("fold").topology.first().to_dict()
    all_topos = sorted(pred.topology.unique())
    rows, prim, contrib = [], [], []
    for (v, m, t, mo), g in d.groupby(["variant", "method", "target", "mode"]):
        inc = sorted(g.topology.unique())
        exc = [x for x in all_topos if x not in inc]
        e = est[(est.variant == v) & (est.method == m) & (est.target == t) & (est["mode"] == mo)]
        why = "; ".join(f"{topo_of_fold.get(r.fold)}: {r.status} (max attainable {r.test_max_attainable_coverage:.3f})"
                        for r in e.itertuples() if topo_of_fold.get(r.fold) in exc)
        scope_info = {"topologies_included": "|".join(inc), "topologies_excluded": "|".join(exc), "exclusion_reason": why}
        for c, gc in g.groupby("y_true"):
            rows.append({"variant": v, "method": m, "target": t, "mode": mo, "class": c, "scope": "POOLED_ESTIMABLE",
                         **scope_info, **_counts(gc)})
            for topo, gt in gc.groupby("topology"):
                rows.append({"variant": v, "method": m, "target": t, "mode": mo, "class": c, "scope": topo,
                             "topologies_included": topo, "topologies_excluded": "", "exclusion_reason": "", **_counts(gt)})
        ns = g[g.policy_outcome != SPECIFIC]
        for (c, oc), gg in ns.groupby(["y_true", "policy_outcome"]):
            pr = gg.reason_code.map(primary_reason).value_counts()
            for reason, n in pr.items():
                prim.append({"variant": v, "method": m, "target": t, "mode": mo, "class": c, "policy_outcome": oc,
                             "primary_reason": reason, "n": int(n), "n_non_specific_in_class": int((ns.y_true == c).sum()),
                             **scope_info})
        for c, gc in ns.groupby("y_true"):
            cr = gc.reason_code.map(contributing_reasons).explode().value_counts()
            for reason, n in cr.items():
                contrib.append({"variant": v, "method": m, "target": t, "mode": mo, "class": c, "contributing_reason": reason,
                                "n_decisions_with_reason": int(n), "n_non_specific_in_class": len(gc),
                                "note": "non-exclusive: a decision counts once for every reason that applies", **scope_info})
    flags = []
    fl = pred.support_flags.fillna("").astype(str)
    for (topo, c), idx in pred.groupby(["topology", "y_true"]).groups.items():
        f = fl.loc[idx]
        sets = f.map(lambda s: tuple(sorted(x for x in s.split("|") if x)))
        base = {"topology": topo, "class": c, "n_windows": len(f), "n_any_flag": int((f != "").sum()), "n_flag_free": int((f == "").sum())}
        names = sorted({x for s in sets for x in s})
        for name in names:
            flags.append({**base, "kind": "NON_EXCLUSIVE_FLAG", "flag_or_combination": name, "n": int(sets.map(lambda s: name in s).sum())})
        for combo, n in sets.value_counts().items():
            flags.append({**base, "kind": "EXCLUSIVE_COMBINATION", "flag_or_combination": "|".join(combo) or "NO_FLAG", "n": int(n)})
    ties = est[est.status == "ESTIMABLE"].copy()
    ties["topology"] = ties.fold.map(topo_of_fold)
    ties["share_selected_by_tie_key"] = ties.n_tied_selected / ties.requested_count
    ties = ties[["fold", "topology", "variant", "method", "target", "mode", "requested_count", "n_tied_at_boundary",
                 "n_tied_selected", "share_selected_by_tie_key"]]
    return {"rq2_scoped": pd.DataFrame(rows), "decision_reasons_primary": pd.DataFrame(prim),
            "decision_reasons_contributing": pd.DataFrame(contrib), "support_flags_scoped": pd.DataFrame(flags),
            "matched_selection_ties": ties}


def cross_check(run: Path, out: Dict[str, pd.DataFrame]) -> List[Dict]:
    """The derived pooled RQ2 must reproduce the run's registered rq2.csv (s_C rows) exactly."""
    checks = []
    p = run / "rq2.csv"
    if not p.exists() or p.stat().st_size <= 1:
        return [{"check": "rq2_registered_present", "ok": True, "detail": "no registered rq2 rows (nothing estimable)"}]
    reg = pd.read_csv(p)
    der = out["rq2_scoped"]
    der = der[(der.scope == "POOLED_ESTIMABLE") & (der.method == "s_C")]
    for r in reg.itertuples():
        x = der[(der.variant == r.variant) & (der.target == r.target) & (der["mode"] == r.mode) & (der["class"] == r._4)]
        ok = len(x) == 1 and int(x.n_windows.iloc[0]) == int(r.n) and int(x.n_families.iloc[0]) == int(r.n_families) and all(
            abs(float(x[f"share_{k}"].iloc[0]) - float(getattr(r, k))) < 1e-9 for k in ("specific", "ambiguity_set", "unresolved"))  # registered file: 10 significant digits
        checks.append({"check": f"rq2[{r.variant}|{r.target}|{r.mode}|{r._4}]", "ok": bool(ok)})
    pr = out["decision_reasons_primary"]
    if len(pr):
        tot = pr.groupby(["variant", "method", "target", "mode", "class"]).n.sum()
        nn = pr.groupby(["variant", "method", "target", "mode", "class"]).n_non_specific_in_class.first()
        checks.append({"check": "primary_reasons_exclusive_and_exhaustive", "ok": bool((tot == nn).all())})
    return checks


def write(run: Path, out_dir: Path) -> Dict:
    out = derive(run)
    checks = cross_check(run, out)
    if not all(c["ok"] for c in checks):
        bad = [c["check"] for c in checks if not c["ok"]]
        raise ValueError(f"derived tables do not reproduce the registered rq2.csv: {bad[:5]}")
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, df in out.items():
        df.to_csv(out_dir / f"{name}.csv", index=False, lineterminator="\n", float_format="%.10g")
    man = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
    rec = {"source_run_dir": run.name, "source_run_key": man.get("run_key"), "source_artifact_class": man.get("artifact_class"),
           "source_status": man.get("status"),
           "source_sha256": {f: _sha(run / f) for f in ("decisions.parquet", "predictions.parquet", "estimability.csv", "rq2.csv",
                                                        "run_manifest.json") if (run / f).exists()},
           "code_sha256": _sha(Path(__file__)), "reason_precedence": REASON_LABELS, "cross_checks": checks,
           "outputs": {f"{k}.csv": _sha(out_dir / f"{k}.csv") for k in out}}
    (out_dir / "DERIVED_MANIFEST.json").write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    # carry the source run identity next to the derived tables so builders resolve provenance (class, status, run key)
    (out_dir / "run_manifest.json").write_text(json.dumps({k: man.get(k) for k in (
        "artifact_class", "status", "run_key", "config_sha256", "effective_config_sha256", "git_commit", "authorization",
        "sensitivity")} | {"derived_from": run.name}, indent=2) + "\n", encoding="utf-8")
    return rec


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=Path, default=REPO / "03_results" / "primary_protocol" / "PRIMARY")
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args(argv)
    out = a.out or REPO / "03_results" / "derived" / a.run.name
    rec = write(a.run, out)
    print(json.dumps({"out": str(out), "checks": len(rec["cross_checks"]), "all_ok": all(c["ok"] for c in rec["cross_checks"])}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
