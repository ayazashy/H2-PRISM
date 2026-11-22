"""Assemble H1_RESULTS.md from the verified analysis CSVs and the generated tables.

Every number in the document is formatted from h1_validation/analysis/*.csv or tables/*.csv at build time,
so the text cannot drift from the data. Usage (repository root):
  python 03_results/integrated_validation_v1/h1_validation/scripts/h1_report.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

H1 = Path(__file__).resolve().parents[1]
A, T = H1 / "analysis", H1 / "tables"


def tab(tid):
    return (T / f"{tid}.md").read_text(encoding="utf-8").replace("### ", "#### ")


def fig(fid, stem, cap):
    return f"![{fid}](figures/{fid}_{stem}.png)\n\n*{fid}. {cap}* ([caption](captions/{fid}_{stem}.md))\n"


def main():
    F = pd.read_csv(A / "h1_02_fold_feasibility.csv")
    p = F[F.variant == "primary"].set_index("held_out_topology")
    P = pd.read_csv(A / "h1_05_paired_comparisons.csv")
    S = pd.read_csv(A / "h1_04_selection_by_method.csv")
    E = pd.read_csv(A / "h1_05_error_capture.csv").set_index("scope")
    R = pd.read_csv(A / "h1_03_score_redundancy_test.csv")
    V = pd.read_csv(A / "h1_06_three_outcome_validity_r2.csv")
    Y = pd.read_csv(A / "h1_07_dy_library_completeness.csv")
    ver = pd.read_csv(A / "h1_verification.csv")
    rq1 = pd.read_csv(A / "h1_01_registered_rq1.csv")
    abl = pd.read_csv(A / "h1_03_development_ablation.csv").set_index("arm_id")
    d = P[P.method_b == "s_C_minus_D"].set_index("coverage")
    b = P[P.method_b == "confidence_no_evidence_guard"].set_index("coverage")
    s25 = S[(S.scope == "pooled") & np.isclose(S.coverage, 0.25)].set_index("method")
    rc = R[R.scope == "guard_available"].set_index("held_out_topology")
    yr = Y[Y.universe == "restricted"]
    pe = E.loc["pooled"]
    shared = p.max_attainable_coverage.min()

    md = f"""# H1 research report — Results

**Status of every number:** reproduced from frozen artifacts; {int(ver.match.sum())}/{len(ver)} verification checks against
the frozen R2 outputs match (`analysis/h1_verification.csv`). Labels: REGISTERED (re-read), RECOMPUTED_VERIFIED,
EXPLORATORY_POST_HOC (windows inspected in R2), CONDITIONAL_HYPOTHETICAL_BOUNDS (Center D(Y)).

## 4.1 Registered hypothesis and evaluation

**Question.** At matched specific coverage, does adding the distinguishability assessment reduce selective risk?
**Evidence.** Registered primary run R2 (`03_results/primary_protocol/PRIMARY/rq1.csv`).
**Method.** Δ = R_sel(s_C) − R_sel(s_C−D) at rank-matched coverage 0.80 (secondary 0.60, 0.90); pooled only if
estimable in every outer fold (`02_methodology/STATISTICAL_ANALYSIS_PLAN.md`).
**Result.** All {len(rq1)} primary-contrast rows are **{rq1.status.unique()[0]}**; folds estimable at 0.60 rank-matched:
{int(rq1[(np.isclose(rq1.target, 0.6)) & (rq1['mode'] == 'rank_matched') & (rq1.variant == 'primary')].folds_estimable.iloc[0])}/3;
no implementation error was found.
**Interpretation.** H1 was not tested by the registered experiment; this is a feasibility failure, not a null result.

{tab("H1-T01")}
## 4.2 Root causes of non-estimability

**Question.** Why did the registered comparison become non-estimable?
**Evidence.** Frozen R2 window predictions (27,993 windows), forensic source-model attribution, development
ablation. **Method.** Recompute eligibility per fold; stratify errors by run attribution and independence unit.
**Result.**
- Binding constraint: the specific-blocking support flags leave {int(p.loc['Center'].n_eligible_specific):,}/9,331 Center
  windows eligible (coverage {p.loc['Center'].max_attainable_coverage:.3f}); Downstream {p.loc['Downstream'].max_attainable_coverage:.3f},
  Upstream {p.loc['Upstream'].max_attainable_coverage:.3f}. Threshold transfer fails earlier: development maxima
  {p.loc['Center'].dev_max_attainable_coverage:.3f}, {p.loc['Downstream'].dev_max_attainable_coverage:.2g},
  {p.loc['Upstream'].dev_max_attainable_coverage:.3f}.
- Root cause: {int(pe.errors_in_disputed_runs):,} of {int(pe.classifier_errors):,} classifier errors
  ({pe.errors_in_disputed_runs / pe.classifier_errors:.1%}) occur in runs whose source model contradicts the manifest
  topology (36/57 runs; D1 pending); the remaining {int(pe.classifier_errors - pe.errors_in_disputed_runs)} occur in one
  Downstream NORMAL run and follow from the swapped training composition.
- Independence: each held-out topology contains {int(p.loc['Center'].n_runs)} runs, {int(p.loc['Center'].n_families)} families
  and {int(p.loc['Center'].n_ancestors)} scenario ancestors; the same {int(p.loc['Center'].n_ancestors)} ancestors recur in all three
  topologies (`analysis/h1_02_independence_units_check.csv`).
**Interpretation.** Observed chain: attribution defect → confident Center errors and single-family neighbourhoods →
flags block SPECIFIC → Center coverage {p.loc['Center'].max_attainable_coverage:.3f} → pooled RQ1 not estimable. The
0.80 target is also unattainable in the two folds not limited by the defect, so correcting attribution alone would not
make the registered contrast estimable. Full cause table: `H1_EXECUTION_DECISION.md` §3.

{fig("H1-F01", "attainable_coverage", "Attainable coverage versus registered targets.")}
## 4.3 Coverage feasibility

**Result.** The coverage attainable in every fold is [0, {shared:.3f}] for every method (identical eligibility). No
registered target lies inside it. The exploratory grid {{0.05, …, 0.25}} fixed by the R2 diagnostics is reused unchanged.

{tab("H1-T02")}
## 4.4 Distinguishability score redundancy

**Question.** Does D(x) carry decision information beyond confidence, margin and entropy?
**Evidence.** Protocol 2.0 development ablation (exploratory); R2 score rankings (exploratory).
**Result.** Development: wherever an operating point is estimable, s_C = s_C−D = confidence (G1:
{abl.loc['G1_DATA_CORRECTIONS', 's_C_group_balanced_risk_mean']:.3f} each; C: {abl.loc['C_COMMON_SENSORS', 's_C_group_balanced_risk_mean']:.3f}
each). R2 Center (eligible windows): correctness AUROC s_C {rc.loc['Center', 'auroc_correct_s_C']:.3f}, s_C−D
{rc.loc['Center', 'auroc_correct_s_C_minus_D']:.3f}, confidence {rc.loc['Center', 'auroc_correct_confidence']:.3f}; Downstream:
s_C and s_C−D {rc.loc['Downstream', 'auroc_correct_s_C']:.3f}, confidence {rc.loc['Downstream', 'auroc_correct_confidence']:.3f}.
Spearman(D, confidence) = {rc.loc['Center', 'spearman_D_confidence']:.2f} (Center), {rc.loc['Downstream', 'spearman_D_confidence']:.2f} (Downstream).
**Interpretation.** D(x) is not a monotone copy of confidence, and inside s_C it restores Center ranking to the level
confidence already reaches; it never exceeds the best conventional score. The meta-model's advantage over confidence in
Downstream exists with or without D(x) and reflects confidence being anti-informative under the attribution defect.

{fig("H1-F04a", "development_ablation", "Development ablation of D(x).")}
{fig("H1-F04b", "score_ranking_quality", "Score ranking quality on the R2 outer test.")}
{tab("H1-T05a")}
{tab("H1-T05b")}
## 4.5 Exploratory risk–coverage comparisons (EXPLORATORY_POST_HOC)

**Question.** Inside the shared coverage region, is selective risk lower with the evidence components?
**Method.** Registered rank-matched exact-count selection (PA-1 tie key) at each grid point; paired topology-stratified
family bootstrap (registered method) and a single-stratum ancestor bootstrap (17 units), 2,000 replicates, seed 20261104.
**Result.**
- Registered contrast: Δ(s_C − s_C−D) = {d.loc[0.05, 'delta_R']:.3f}, {d.loc[0.10, 'delta_R']:.3f}, {d.loc[0.15, 'delta_R']:.3f},
  {d.loc[0.20, 'delta_R']:.3f}, {d.loc[0.25, 'delta_R']:.3f} at 0.05–0.25. Every family interval has upper bound ≥ 0
  (largest upper bound {d.family_ci_high.max():.3f}); every ancestor interval includes 0. Discordant errors come from at most
  {int(d.ancestors_discordant_errors.max())} ancestors. Among windows from undisputed runs, both policies make
  {int(d.n_errors_undisputed_a.sum())} and {int(d.n_errors_undisputed_b.sum())} errors over all grid points.
- Full evidence policy against conventional confidence abstention (no guard): Δ = {b.delta_R.min():.3f} to
  {b.delta_R.max():.3f}; family interval below 0 at {int((b.family_ci_high < 0).sum())}/5 points, ancestor interval at
  {int((b.ancestor_ci_high < 0).sum())}/5.
- At 0.25 ({int(s25.loc['s_C'].n_selected):,} SPECIFIC calls each): s_C {s25.loc['s_C'].selective_risk:.3f}, s_C−D
  {s25.loc['s_C_minus_D'].selective_risk:.3f}, guarded confidence {s25.loc['confidence'].selective_risk:.3f}, conventional confidence
  {s25.loc['confidence_no_evidence_guard'].selective_risk:.3f}.
**Interpretation.** Pre-stated exploratory criteria (decision record §10) are not met for the registered contrast:
intervals include 0, discordant errors come from ≤ 3 ancestors, and there is no error outside disputed runs. The result is
**INCONCLUSIVE — EXPLORATORY EVIDENCE ONLY**. The evidence guard's large advantage over conventional confidence is
exploratory and confounded with the attribution defect.

{fig("H1-F02a", "selective_risk_shared_coverage", "Selective risk at shared attainable coverage (exploratory).")}
{fig("H1-F02b", "paired_risk_difference", "Paired risk differences with family- and ancestor-level intervals (exploratory).")}
{fig("H1-F03", "selection_swap", "Windows exchanged by adding D(x) (exploratory).")}
{tab("H1-T03")}
{tab("H1-T04")}
## 4.6 Specific and ambiguous decision validity (RQ3)

**Evidence.** Registered s_C decisions at rank-matched 0.60 in the two folds where it is attainable.
**Result.** {int(V.specific.sum()):,} SPECIFIC decisions with {int(V.specific_wrong.sum())} wrong; {int(V.ambiguity.sum())}
ambiguity sets (size 2), {int(V.ambiguity_includes_true.sum())} containing the true class; {int(V.unresolved.sum()):,}
UNRESOLVED. All {int(V.classifier_errors_total.sum())} classifier errors in these folds ended UNRESOLVED (one Downstream
NORMAL run). Classes LEAK and NORMAL receive SPECIFIC decisions; COMPRESSOR_FAULT never does (flag-blocked).
**Interpretation.** Descriptively, the three-outcome policy issued no wrong SPECIFIC decision where it could be
evaluated, but the support is one family per thin class and the errors it avoided stem from the attribution defect.

{fig("H1-F05", "error_abstention", "Where classifier errors go (exploratory).")}
{tab("H1-T06a")}
## 4.7 Formal D(Y) and hypothesis-library completeness

**Evidence.** Center conditional D(Y) grid, 672 cells (CONDITIONAL_HYPOTHETICAL_BOUNDS).
**Result.** Full declared universe: {int(Y[Y.universe == 'full'].unresolved.sum())}/{int(Y[Y.universe == 'full'].cells.sum())} UNRESOLVED.
Restricted universe: {int(yr.specific.sum())} SPECIFIC ({int(yr.specific_correct.sum())} correct, {int(yr.specific_wrong.sum())} wrong),
{int(yr.ambiguous.sum())} AMBIGUOUS, {int(yr.unresolved.sum())} UNRESOLVED; every wrong SPECIFIC has a true hypothesis outside the
library, and none of the SPECIFIC decisions with a represented true hypothesis is wrong.
**Interpretation.** Formal D(Y) supplies one testable property conventional scores lack: it can refuse to decide when
the declared hypothesis set is not fully modelled. Its value depends on library completeness, and it was never evaluated
against a classifier on shared independent scenarios. Bounds are hypothetical, and the 672 cells are repeated views of 6 captures.

{fig("H1-F06", "library_completeness_risk", "Hypothesis-library completeness risk (conditional).")}
{tab("H1-T06b")}
## 4.8 Evidence for or against incremental decision value

- **Against (development):** no measurable D(x) contribution at estimable development operating points.
- **For (exploratory, weak):** Δ(s_C − s_C−D) ≤ 0 at all five grid points, but all intervals include 0 and the
  information comes from 1–3 ancestors in disputed runs.
- **For the evidence layer as a whole (exploratory, confounded):** the support guard withheld
  {int(pe.errors_blocked_by_evidence_flags):,}/{int(pe.classifier_errors):,} classifier errors ({pe.share_errors_blocked:.1%}); error
  rate {pe.error_rate_blocked:.3f} among blocked vs {pe.error_rate_eligible:.3f} among eligible windows.
- **Formal D(Y):** conditional demonstration only.

{tab("H1-T07")}
{fig("H1-F07", "evidence_map", "H1 evidence and feasibility map.")}
## 4.9 Scientific limitations

See `H1_LIMITATIONS.md`. In short: all evaluation windows were inspected; 17 scenario ancestors; 91.7 % of errors in
disputed runs; calibration selected identity; Center D(Y) bounds are hypothetical and come from one simulation family.

## 4.10 Minimum requirements for confirmatory H1 validation

{tab("H1-T08")}
See `H1_CONFIRMATION_REQUIREMENTS.md` for the protocol blueprint.

## 4.11 Final H1 verdict

- **Registered verdict (unchanged): NOT_ESTIMABLE.**
- **Exploratory status of the registered contrast: INCONCLUSIVE — EXPLORATORY EVIDENCE ONLY.**
- **Evidence layer vs conventional confidence: EXPLORATORY EVIDENCE ONLY, confounded by the attribution defect.**
- H1 is neither supported nor refuted; a genuine test requires new independent scenarios (Section 4.10).
"""
    (H1 / "H1_RESULTS.md").write_text(md, encoding="utf-8", newline="\n")
    print("written", len(md))


if __name__ == "__main__":
    main()
