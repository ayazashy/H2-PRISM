"""Analyse the D(Y) experiment runs: invariant checks, outcome summaries, localization, counterfactuals,
and template-level pairwise isolability with an exhaustive minimum-sensor-set search.

Inputs: analysis/dy_experiment_runs.csv (av_dy_experiments.py), the frozen Center grid
(center_evidence_enhancement/analysis/dy_decisions.json, TAB_C03) and the hash-verified Center captures
(for template-level isolability only). Usage: python av_dy_analysis.py --workspace <Center workspace>
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

AV = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "src"))
from h2prism import center_enhancement as ce  # noqa: E402

A = AV / "analysis"
ALLOWED = {"FEASIBLE": {"FEASIBLE"}, "EXCLUDED": {"FEASIBLE", "EXCLUDED", "INDETERMINATE"},
           "INDETERMINATE": {"INDETERMINATE", "FEASIBLE"}}
LAD = {"S1": (1e-6, 1e-5), "S2": (1e-5, 1e-4), "S3": (1e-4, 1e-3), "S4": (1e-3, 1e-2), "S5": (1e-2, 1e-1),
       "S6": (1e-1, 1.0), "REF": (ce.SOLVER_DELTA["pressure_MPa"], ce.SOLVER_DELTA["flow_kg_s"])}
TAG = "CONDITIONAL_HYPOTHETICAL_BOUNDS"


def statuses(js):
    return {h: s for h, (s, _) in json.loads(js).items()}


def transitions(before, after):
    """Count hypothesis-status transitions from a more-informative to a less-informative run."""
    n = viol = 0
    detail = []
    for h, s in before.items():
        if h not in after:
            continue
        n += 1
        if after[h] not in ALLOWED[s]:
            viol += 1
            detail.append(f"{h}:{s}->{after[h]}")
    return n, viol, detail


def invariants(d):
    rows = []
    e1 = d[d.experiment == "E1_sensors"]
    base = e1[e1.config == "all"].set_index(["query", "scenario"])
    for _, r in e1[e1.config != "all"].iterrows():
        b = base.loc[(r["query"], r["scenario"])]
        n, v, det = transitions(statuses(b.status_json), statuses(r.status_json))
        rows.append(dict(test="sensor removal (subset of all 13 channels)", pair=f"all -> {r.config}", query=r["query"],
                         scenario=r.scenario, hypotheses_compared=n, violations=v, detail=";".join(det)))
    e2 = d[d.experiment == "E2_clock_bound"].copy()
    e2["tau"] = e2.bound
    for (q, s), g in e2.groupby(["query", "scenario"]):
        g = g.sort_values("tau")
        for (_, a), (_, b) in itertools.combinations(g.iterrows(), 2):
            n, v, det = transitions(statuses(a.status_json), statuses(b.status_json))
            rows.append(dict(test="clock-bound widening", pair=f"tau {a.tau:g} -> {b.tau:g} s", query=q, scenario=s,
                             hypotheses_compared=n, violations=v, detail=";".join(det)))
    # bound widening on the frozen 672-decision grid and the new E4 runs (partial order on (eps_P, eps_F))
    fz = json.loads((REPO / "03_results/validation/center_evidence_enhancement/analysis/dy_decisions.json").read_text(encoding="utf-8"))
    fr = pd.DataFrame([dict(query=x["query"], group=x["group"], universe=x["universe"], bound=x["clock_bound_s"],
                            scenario=x["scenario"],
                            status={**{h: "FEASIBLE" for h in x["consistent"]}, **{h: "EXCLUDED" for h in x["excluded"]},
                                    **{h: "INDETERMINATE" for h in x["indeterminate"]}}) for x in fz])
    for key, g in fr.groupby(["query", "group", "universe", "bound"]):
        g = g.set_index("scenario")
        for a, b in itertools.permutations(g.index, 2):
            if LAD[a][0] <= LAD[b][0] and LAD[a][1] <= LAD[b][1] and a != b:
                n, v, det = transitions(g.loc[a, "status"], g.loc[b, "status"])
                rows.append(dict(test="bound widening (frozen grid)", pair=f"{a} -> {b}", query=key[0],
                                 scenario=f"{key[1]}|{key[2]}|tau{key[3]:g}", hypotheses_compared=n, violations=v,
                                 detail=";".join(det)))
    I = pd.DataFrame(rows)
    I.to_csv(A / "dy_invariant_checks.csv", index=False, lineterminator="\n")
    return I


def summarise(d):
    def agg(g):
        n = len(g)
        spec = g.decision == "SPECIFIC"
        amb = g[g.decision == "AMBIGUOUS"]
        return pd.Series({"decisions": n, "specific": int(spec.sum()), "specific_correct": int((g.outcome == "SPECIFIC_CORRECT").sum()),
                          "specific_wrong": int((g.outcome == "SPECIFIC_WRONG").sum()), "specific_coverage": spec.mean(),
                          "wrong_specific_risk": (g.outcome == "SPECIFIC_WRONG").sum() / spec.sum() if spec.sum() else np.nan,
                          "ambiguous": len(amb), "ambiguous_truth_in": int((g.outcome == "AMBIGUOUS_TRUTH_IN").sum()),
                          "mean_ambiguity_set_size": amb.n_feasible.mean() if len(amb) else np.nan,
                          "unresolved_model_mismatch": int((g.outcome == "UNRESOLVED_MODEL_MISMATCH").sum()),
                          "unresolved_indeterminate": int((g.outcome == "UNRESOLVED_INDETERMINATE_HYPOTHESES").sum()),
                          "truth_retained": int(g.truth_retained.sum()), "truth_in_library": int(g.truth_in_library.sum()),
                          "mean_excluded_hypotheses": g.n_excluded.mean()})
    d = d.copy()
    d["config_family"] = d.config.str.replace(r"_\d\d$", "", regex=True)
    S = d.groupby(["experiment", "config_family"]).apply(agg, include_groups=False).reset_index()
    S["n_channels"] = d.groupby(["experiment", "config_family"]).n_channels.first().values
    S["label"] = TAG
    S.to_csv(A / "dy_outcome_summary.csv", index=False, lineterminator="\n")
    ev = d[d.experiment == "E1_sensors"].groupby("n_channels").apply(agg, include_groups=False).reset_index()
    ev["configs"] = d[d.experiment == "E1_sensors"].groupby("n_channels").config.nunique().values
    ev.to_csv(A / "dy_evidence_availability.csv", index=False, lineterminator="\n")
    byq = d.groupby(["experiment", "config_family", "query"]).outcome.value_counts().unstack(fill_value=0).reset_index()
    byq.to_csv(A / "dy_outcome_by_query.csv", index=False, lineterminator="\n")
    return S, ev


def localization(d):
    """Location decisions of the restricted formal policy vs nearest-template ranking (Level 1-2 only)."""
    site = {"WITHDRAWAL_SID213": "SID213", "WITHDRAWAL_SID312": "SID312", "WITHDRAWAL_SID215": "SID215"}
    c3 = pd.read_csv(REPO / "03_results/validation/center_evidence_enhancement/tables/TAB_C03.csv")
    rows = []
    for _, r in c3.iterrows():
        ranks = {s: r[f"rank_SID{s}"] for s in ("213", "312", "215")}
        true = str(r.true_SID)
        tr = ranks.get(true)
        supported = tr not in ("—", None) and str(tr) != "nan"
        rows.append(dict(method="B3 nearest-template ranking", query=r["query"], condition=r.condition, true_site=f"SID{true}",
                         true_site_supported=supported, issued_site=f"SID{r.top1}", top1_correct=r.top1_result == "correct",
                         true_rank=int(tr) if supported else np.nan, reciprocal_rank=1 / int(tr) if supported else 0.0,
                         margin=r.margin, location_specific=True))
    w = d[(d.experiment == "E1_sensors") & (d.config == "all") & d["query"].isin(["SID213", "ALT", "SID312", "SID215"])]
    for _, r in w.iterrows():
        sel = site.get(r.selected, "")
        rows.append(dict(method="formal D(Y), restricted universe", query=r["query"], condition=r.scenario,
                         true_site=ce.TRUE_SITE[r["query"]], true_site_supported=bool(r.truth_in_library),
                         issued_site=sel or ("non-location hypothesis: " + r.selected if r.selected else ""),
                         top1_correct=sel == ce.TRUE_SITE[r["query"]] if sel else np.nan, true_rank=np.nan,
                         reciprocal_rank=np.nan, margin=np.nan, location_specific=bool(sel)))
    L = pd.DataFrame(rows)
    L.to_csv(A / "localization_cases.csv", index=False, lineterminator="\n")
    return L


def counterfactuals(d):
    """Minimal single changes that alter a correct SPECIFIC decision of the all-channel run."""
    base = d[(d.experiment == "E1_sensors") & (d.config == "all") & (d.outcome == "SPECIFIC_CORRECT")]
    rows = []
    for _, b in base.iterrows():
        k = (b["query"], b.scenario)
        sens = d[(d.experiment == "E1_sensors") & d.config.str.startswith("drop_") & (d["query"] == k[0]) & (d.scenario == k[1])]
        rows.append(dict(query=k[0], scenario=k[1], change="loss of one channel",
                         altering=";".join(f"{r.config[5:]}->{r.outcome}" for _, r in sens.iterrows() if r.outcome != b.outcome)))
        dl = d[(d.experiment == "E3_delay") & (d["query"] == k[0]) & (d.scenario == k[1]) & (d.bound == 1.0)]
        rows.append(dict(query=k[0], scenario=k[1], change="observation delay at tau = 1 s",
                         altering=";".join(f"{r.config}->{r.outcome}" for _, r in dl.iterrows() if r.outcome != b.outcome)))
        lib = d[(d.experiment == "E4_library") & (d["query"] == k[0]) & (d.scenario == k[1])]
        rows.append(dict(query=k[0], scenario=k[1], change="hypothesis universe",
                         altering=";".join(f"{r.config}->{r.outcome}" for _, r in lib.iterrows() if r.outcome != b.outcome)))
    C = pd.DataFrame(rows)
    C.to_csv(A / "dy_counterfactuals.csv", index=False, lineterminator="\n")
    return C


def isolability(ws):
    """Template-level pairwise isolability: no observation can be consistent with both hypotheses iff for every
    pair of admissible shifts some coordinate has |h_i - h_j| > 2 eps_total(kind)."""
    data = ce.load(Path(ws))
    hyps = {"HN": ("NORMAL_ZERO",), "H213": ("SID213", "ALT"), "H312": ("SID312",), "H215": ("SID215",),
            "HP55": ("PRESSURE",), "HT59": ("TIMING",)}
    allidx = np.arange(len(data.names))
    stacks = {h: np.concatenate([ce.shifted_windows(data, t, allidx, 1.0) for t in ts]) for h, ts in hyps.items()}
    kinds = np.array([0 if k == "pressure" else 1 for k in data.kinds])
    pairs = list(itertools.combinations(hyps, 2))
    P = {}
    for a, b in pairs:
        diff = np.abs(stacks[a][:, None] - stacks[b][None, :])          # (Sa, Sb, N, C)
        P[(a, b)] = diff.max(axis=2)                                     # (Sa, Sb, C): max over time per channel
    rows, minsets = [], []
    configs = {"all": allidx, "pressure_only": np.flatnonzero(kinds == 0), "flow_only": np.flatnonzero(kinds == 1)}
    configs.update({f"drop_{n}": np.array([i for i in allidx if data.names[i] != n]) for n in data.names})
    for scen in ("S3", "S4", "S5", "REF"):
        eps = np.where(kinds == 0, LAD[scen][0], LAD[scen][1])
        for cfg, idx in configs.items():
            for a, b in pairs:
                g = (P[(a, b)][:, :, idx] - 2 * eps[idx]).max(axis=2)
                rows.append(dict(scenario=scen, config=cfg, hyp_a=a, hyp_b=b, isolable=bool(g.min() > 0),
                                 worst_case_margin=float(g.min())))
        # exhaustive minimum sensor sets preserving all isolable pairs of the full set
        full = {(a, b) for a, b in pairs if (P[(a, b)] - 2 * eps).max(axis=2).min() > 0}
        best = None
        for k in range(1, len(allidx) + 1):
            hits = []
            for sub in itertools.combinations(allidx, k):
                sub = np.array(sub)
                ok = all((P[p][:, :, sub] - 2 * eps[sub]).max(axis=2).min() > 0 for p in full)
                if ok:
                    hits.append(sub)
            if hits:
                best = (k, hits)
                break
        minsets.append(dict(scenario=scen, isolable_pairs_full_set=len(full), total_pairs=len(pairs),
                            min_channels=best[0] if best else np.nan, n_minimal_sets=len(best[1]) if best else 0,
                            minimal_sets=";".join("+".join(data.names[i] for i in s) for s in best[1][:20]) if best else "",
                            isolable_pairs_list=";".join(f"{a}-{b}" for a, b in sorted(full))))
    pd.DataFrame(rows).to_csv(A / "dy_pairwise_isolability.csv", index=False, lineterminator="\n")
    pd.DataFrame(minsets).to_csv(A / "dy_minimum_sensor_sets.csv", index=False, lineterminator="\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", default=os.environ.get("H2PRISM_CENTER_WORKSPACE"))
    a = ap.parse_args()
    d = pd.read_csv(A / "dy_experiment_runs.csv", keep_default_na=False, na_values=[""])
    d["selected"] = d.selected.fillna("")
    I = invariants(d)
    S, ev = summarise(d)
    localization(d)
    counterfactuals(d)
    isolability(a.workspace)
    print("invariant comparisons:", len(I), "hypothesis checks:", int(I.hypotheses_compared.sum()),
          "violations:", int(I.violations.sum()))


if __name__ == "__main__":
    main()
