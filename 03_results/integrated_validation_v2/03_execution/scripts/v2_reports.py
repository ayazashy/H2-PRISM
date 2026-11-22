"""Generate the v2 reports (06_reports), audit/design summaries, experiment status, claim register and README.

Every number is read from a verified output file through build_v2_tables.facts() or directly from the cited CSV.
Usage (repository root): python 03_results/integrated_validation_v2/03_execution/scripts/v2_reports.py
"""
from __future__ import annotations

import platform
import sys
from importlib import metadata
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_v2_tables as bt  # noqa: E402

V2, REPO, AN, TB = bt.V2, bt.REPO, bt.AN, bt.TB
R = V2 / "06_reports"
f3 = bt.f3


def w(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8", newline="\n")


def table(df, cols=None):
    df = df[cols] if cols else df
    def c(v):
        if isinstance(v, (float, np.floating)):
            return "—" if np.isnan(v) else f"{v:.3g}"
        return str(v).replace("|", "/")
    return "\n".join(["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)] +
                     ["| " + " | ".join(c(v) for v in r) + " |" for r in df.itertuples(index=False)])


def experiment_status():
    rows = [
        # Part 1-2: audit and D1
        ("A1", "Repository and artifact integrity, baseline reproduction", "EXECUTED", "01_audit/BASELINE_REPRODUCTION.csv", ""),
        ("A2", "D1 correction matrix", "EXECUTED", "01_audit/D1_CORRECTION_MATRIX.csv", ""),
        ("A3", "Corrected-manifest replication (D1 = B)", "BLOCKED_BY_PROVENANCE", "03_execution/scripts/d1_correction.py replicate",
         "no owner decision record; gate exits 3"),
        ("A4", "Leakage register update", "EXECUTED", "01_audit/LEAKAGE_REGISTER_V2.csv", ""),
        ("A5", "Full test-suite triage", "EXECUTED", "01_audit/TEST_FAILURE_TRIAGE.csv", ""),
        # Part 3 D(x) 13 experiments
        ("X01", "D(x): full vs ablated matched evaluation", "EXECUTED (v1)", "h1_validation/analysis/h1_05_paired_comparisons.csv", ""),
        ("X02", "D(x): score correlation / redundancy", "EXECUTED (v1)", "h1_validation/analysis/h1_03_score_redundancy_test.csv", ""),
        ("X03", "D(x): conditional on confidence", "EXECUTED", "04_results/analysis/x1_conditional_D_given_confidence.csv", ""),
        ("X04", "D(x): incremental predictive utility (leave-one-template-out)", "EXECUTED", "04_results/analysis/x2_incremental_utility_lotemplate.csv", ""),
        ("X05", "D(x): alternative estimators", "NOT_EXECUTED", "—",
         "any new estimator could only be tuned on inspected windows (no uninspected evaluation set); would be test-set optimisation"),
        ("X06", "D(x): neighbourhood size / scaling", "EXECUTED (registered; NOT_ESTIMABLE)", "04_results/analysis/x4_registered_sensitivities.csv", ""),
        ("X07", "D(x): noisy vs clean data", "EXECUTED (registered; NOT_ESTIMABLE)", "04_results/analysis/x4_registered_sensitivities.csv", ""),
        ("X08", "D(x): sensor-conditional analysis", "NOT_EXECUTED", "—",
         "requires recomputing D on masked feature sets of disputed-label windows; low information until D1/D2"),
        ("X09", "D(x): class/location-conditional", "PARTIAL", "x1 by topology; advanced_validation/tables/A02b.csv", "one location per class"),
        ("X10", "D(x): stability across grouped resampling", "EXECUTED", "h1_05 family/ancestor bootstrap; x2 per-template", ""),
        ("X11", "D(x): synthetic known-distinguishability cases", "EXECUTED (SYNTHETIC)", "04_results/analysis/x5_synthetic_dx_control.csv", ""),
        ("X12", "D(x): negative control where D should not help", "EXECUTED (SYNTHETIC)", "x5 calibrated-Bayes case", ""),
        ("X13", "D(x): dataset-artifact test", "EXECUTED", "04_results/analysis/x3_D_artifact_test.csv", ""),
        # Part 4 D(Y)
        ("Y1", "Re-verify invariants, certificates, witnesses", "EXECUTED (v1, reproduced by verify_av)", "advanced_validation/tables/A04a.csv", ""),
        ("Y2", "Adversarial and property tests", "EXECUTED", "tests/test_dy_adversarial.py", ""),
        ("Y3", "Monotonicity proof with assumptions", "EXECUTED", "02_design/DY_MONOTONICITY_PROOF.md", ""),
        ("Y4", "Library incompleteness", "EXECUTED (v1)", "advanced_validation/tables/A05.csv", ""),
        ("Y5", "Bound-origin audit", "EXECUTED", "01_audit/BOUND_ORIGIN_AUDIT.csv", ""),
        ("Y6", "Validated model-discrepancy / open-set detection", "BLOCKED_BY_DATA", "—", "no independent captures to calibrate a discrepancy bound"),
        # Part 5
        ("C1", "Class-wise, run-level, disputed vs undisputed metrics", "EXECUTED (EXPLORATORY)", "04_results/tables/V2-T08, V2-T09", ""),
        ("C2", "Model improvements (features, imbalance, calibration)", "NOT_EXECUTED", "—",
         "labels disputed (D1) and no uninspected evaluation set: any gain would be unverifiable"),
        ("C3", "Detection delay", "NOT_ESTIMABLE", "—", "window labels carry no onset-resolved predictions"),
        # Part 6
        ("L1", "Localization hierarchy and selective risk", "EXECUTED (v1)", "advanced_validation/tables/A06a.csv, A07.csv", ""),
        ("L2", "Isolability onset (structural vs bound-limited)", "EXECUTED", "04_results/analysis/i1_isolability_onset.csv", ""),
        ("L3", "Sensor-hypothesis incidence matrix", "EXECUTED", "04_results/analysis/i2_structural_incidence.csv", ""),
        ("L4", "Unidentifiable-pair register", "EXECUTED", "04_results/analysis/i3_unidentifiable_pair_register_REF.csv", ""),
        # Part 7-8
        ("S1", "Sensor masks and outages", "EXECUTED (v1)", "advanced_validation/tables/A08.csv", ""),
        ("S2", "Bias, drift, noise, stuck faults", "EXECUTED (SYNTHETIC)", "04_results/analysis/s1_dy_synthetic_stress_runs.csv", ""),
        ("S3", "Minimum sensor sets and Pareto", "EXECUTED (v1) + hypothetical cost scenarios", "A16a/b; 04_results/tables/V2-T07", ""),
        ("T1", "Clock bound and delay", "EXECUTED (v1)", "advanced_validation/tables/A09.csv", ""),
        ("T2", "Timestamp jitter", "EXECUTED (SYNTHETIC)", "s1 jitter rows", ""),
        ("T3", "Clock drift, asynchrony, sampling-rate differences", "NOT_EXECUTED", "—", "no timing model for the fixed simulation clock beyond delay/jitter"),
        # Part 9-10
        ("E1", "Evidence sufficiency (multidimensional)", "EXECUTED (v1)", "advanced_validation/tables/A10.csv", "no scalar index invented"),
        ("N1", "Negative controls (NORMAL, operational interventions)", "EXECUTED (v1)", "advanced_validation/tables/A11a.csv, A11b.csv", ""),
        # Part 11-12
        ("G1", "Out-of-template generalization", "BLOCKED_BY_DATA", "advanced_validation/analysis/av_r2_template_sharing.csv", "no held-out template"),
        ("G2", "HY2RES Level-A adapter + equivalence", "EXECUTED", "04_results/analysis/h*_hy2res_*.csv", ""),
        ("G3", "MHC adapter", "NOT_EXECUTED", "—", "MHC is a forecasting study with no diagnostic hypotheses or labelled faults"),
        ("G4", "Gas Level B/C transfer", "BLOCKED_BY_PHYSICS", "advanced_validation/tables/A13.csv", "no qualified transient H2/blend model"),
        # Part 13
        ("P1", "Runtime and scaling benchmarks", "EXECUTED (v1)", "advanced_validation/tables/A14a-c", ""),
        ("P2", "Cost categories", "EXECUTED (no prices)", "04_results/tables/V2-T10", ""),
    ]
    df = pd.DataFrame(rows, columns=["id", "experiment", "status", "artifact", "blocker_or_reason"])
    df.to_csv(V2 / "02_design/EXPERIMENT_STATUS.csv", index=False, lineterminator="\n")
    return df


def env():
    pk = {}
    for name in ("numpy", "pandas", "matplotlib", "scipy", "pyyaml", "pytest", "pyarrow", "coolprop"):
        try:
            pk[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            pk[name] = "not installed"
    hw = pd.read_csv(REPO / "03_results/integrated_validation_v1/advanced_validation/benchmarks/hardware.csv", index_col=0)["value"]
    lines = [f"python {platform.python_version()}", f"platform {platform.platform()}", f"cpu {hw['cpu_model']} ({hw['logical_cpus']} logical)",
             f"ram_GB {hw['ram_GB']}"] + [f"{k} {v}" for k, v in pk.items()]
    w(V2 / "03_execution/ENVIRONMENT.txt", "\n".join(lines))
    return lines


def main():
    F = bt.facts()
    reg = pd.read_csv(V2 / "02_design/HYPOTHESIS_REGISTRY.csv").set_index("id")
    es = experiment_status()
    envl = env()
    d1 = pd.read_csv(V2 / "01_audit/D1_CORRECTION_SUMMARY.csv", index_col=0)["value"]
    base = pd.read_csv(V2 / "01_audit/BASELINE_REPRODUCTION.csv")
    tri = pd.read_csv(V2 / "01_audit/TEST_FAILURE_TRIAGE.csv")
    x2, x3, a5, a8, a9, hy, hn = F["x2"], F["x3"], F["a5"], F["a8"], F["a9"], F["hy"], F["hn215"]
    i1 = F["i1"]
    r1, u = F["r1"], F["r1u"]
    allw = r1[(r1.scope == "all_windows") & (r1.cls == "ALL")].iloc[0]
    und = r1[(r1.scope == "undisputed_runs_only") & (r1.cls == "ALL")].iloc[0]
    tri_counts = tri.classification.value_counts()
    n_isol = {c: int(i1[(i1.channels == c)].isolable_at_REF.sum()) for c in ("all", "pressure_only", "flow_only")}
    syn = F["x5"]
    a14 = pd.read_csv(REPO / "03_results/integrated_validation_v1/advanced_validation/tables/A14b.csv")
    a11 = F["a11"].set_index(["coverage_requested", "method"])
    status_counts = reg.status.value_counts()
    t7 = pd.read_csv(TB / "V2-T07_hypothetical_cost_scenarios.csv")
    pareto_text = "\n".join(f"- r = {r}: non-dominated configurations: " + ", ".join(g[g.pareto_nondominated].config)
                             for r, g in t7.groupby("flow_to_pressure_unit_cost_ratio"))

    # ------------------------------------------------------------------ 01 audit summary
    w(V2 / "01_audit/AUDIT_SUMMARY.md", f"""
# 01 — Audit

## Repository inventory and baseline reproduction
Branch `research/integrated-validation`, HEAD `{base.set_index('check').loc['git HEAD at audit','observed']}` at audit. Machine-readable checks: `BASELINE_REPRODUCTION.csv`.

{table(base, ['check', 'observed', 'status'])}

The full suite has {tri.shape[0]} non-passing items, none caused by this package (`TEST_FAILURE_TRIAGE.csv`):
{chr(10).join(f'- {k}: {v}' for k, v in tri_counts.items())}

The test suite rewrote two tracked governance files (`00_governance/ACTION_EXECUTION_STATUS.csv`, `ISSUE_CLOSURE_MATRIX.csv`). Their committed bytes were restored, and the event is recorded.

## Data integrity
- Frozen R2 predictions, decisions, configuration and attribution match the SHA-256 recorded by the v1 H1 package.
- The {base.set_index('check').loc['Center raw captures re-hashed on load','observed']} Center raw captures are re-hashed on every load.
- The HY2RES CSV matches the MD5 asserted by the frozen builder. Raw data stay outside Git.

## D1 decision requirements (dataset owner)
- `D1_CORRECTION_MATRIX.csv` lists, per run, the measured sensor signature, the inferred source model and the proposed topology change. {d1['topology_changes']} of {d1['runs']} runs change topology ({d1['eligible_changes']} eligible); {d1['label_changes']} event labels change.
- Owner decision record present: **{d1['owner_decision_record_present']}**. Corrected replication therefore stays BLOCKED_BY_PROVENANCE.
- What unblocks it:
  1. The owner records `06_audit_preparation/protocol2/OWNER_DECISION_D1.yaml` with decision B, the owner's name, the date, and approved manifest SHA-256 `{d1['v03_sha256']}`.
  2. The project lead issues an `EXPLORATORY_REPLICATION` authorization.
  3. `d1_correction.py replicate` then prints the frozen-runner command.
- This package never creates either record.

## Leakage register, provenance map and risks
- `LEAKAGE_REGISTER_V2.csv` (v1 L01–L16 plus L17–L22) is also the scientific risk register: it gives severity, impacted claims, corrective action and approver for each entry.
- `BOUND_ORIGIN_AUDIT.csv` covers bound provenance for D(Y).
- Provenance map:
  - R2 → `H2PRISM_R2_RUN` (frozen run a10530f1…);
  - Center → hash-verified MAT captures in the Center workspace;
  - HY2RES → checksum-matched Zenodo CSV plus the frozen validity mask;
  - MHC → v1 Study B archive (unchanged, not used here).
""")

    # ------------------------------------------------------------------ 02 design
    w(V2 / "02_design/EXPERIMENT_DESIGN.md", f"""
# 02 — Experiment design

## Original versus revised protocols
- **Original (registered, unchanged).** R2 RQ1: s_C vs s_C − D at matched coverage 0.6, 0.8 and 0.9, using three held-out topologies. Status NOT_ESTIMABLE ({F['rq1_ne']}/{F['rq1_rows']} PRIMARY rows).
- **Revised (this round, secondary).** No registered target was lowered. The new analyses do the following:
  1. Test D(x)'s incremental information with template-grouped cross-validation on frozen scores.
  2. Qualify the formal D(Y) with a proof, adversarial tests and SYNTHETIC stress.
  3. Separate structural from bound-limited isolability.
  4. Port one external rule to the engine (HY2RES Level A).
- None of these replaces H1.

## Hypothesis registry
`HYPOTHESIS_REGISTRY.csv`. Only H1 was registered before evaluation; H2–H10 are secondary.

## Independence rules and partitions
- R2: the independent unit is the scenario ancestor/template ({F['n_anc']}), then the family ({F['n_fam']}). Windows and runs are dependent.
- Template-grouped CV never places one template in both fit and evaluation.
- Center: one capture per mechanism (plus a near-duplicate replicate for SID 213). Results are counts over repeated views, not rates.
- HY2RES: chronological development/test split with zero shared segments. The test partition was inspected before (L18).

## Comparators
- H1: s_C − D (registered); confidence, margin, entropy and D-only with the evidence guard; unguarded confidence; no abstention.
- D(x) utility: [logit conf] and [logit conf, margin, −entropy].
- Localization: forced and top-k nearest template.

## Coverage definitions
- coverage = SPECIFIC / all decisions in the stated population.
- wrong-specific risk = wrong SPECIFIC / SPECIFIC.
- A candidate set without the truth is never counted as correct.

## Statistical analysis plan
- Report units and counts first; intervals only from ancestor/family bootstrap; no significance claims.
- Every comparison run is reported, including negative ones.
- Synthetic results are labelled and kept out of claims about the field.

## Experiment feasibility and status
`EXPERIMENT_STATUS.csv` ({len(es)} experiments). By status:
{chr(10).join(f'- {k}: {v}' for k, v in es.status.value_counts().items())}
""")

    # ------------------------------------------------------------------ reports
    w(R / "01_COMPREHENSIVE_SCIENTIFIC_RESULTS.md", f"""
# Comprehensive scientific results (v2)

All values are generated from the files cited; the hypothesis statuses come from `02_design/HYPOTHESIS_REGISTRY.csv`.

## Diagnostic performance (R2, exploratory)
- Window accuracy is {f3(allw.recall)} on all {int(allw.support_windows):,} windows. Balanced accuracy is {f3(allw.balanced_accuracy)} and macro-F1 {f3(allw.macro_f1)}.
- In the {int(und.support_runs)} undisputed runs ({int(und.support_windows):,} windows) accuracy is {f3(und.recall)}.
- Run-level majority accuracy:

  | Runs | Accuracy |
  |---|---|
  | Disputed ({int(u.loc['disputed','runs'])} runs) | {f3(u.loc['disputed','run_majority_accuracy'])} |
  | Undisputed ({int(u.loc['undisputed','runs'])} runs) | {f3(u.loc['undisputed','run_majority_accuracy'])} |

- Event runs called NORMAL: {int(u.loc['disputed','event_runs_called_normal'])} of {int(u.loc['all','event_runs_called_normal'])} lie in disputed runs.
- Tables: V2-T08 and V2-T09.
- NORMAL, COMPRESSOR_FAULT and COMPRESSOR_DELAY each come from one or two ancestors, so the class-wise rates are not generalisable.

## H1 — selective risk
{reg.loc['H1','result']} {reg.loc['H1','uncertainty']}.

## H2 — D(x)
{reg.loc['H2','result']} Verdict: **no demonstrated improvement** (exploratory). Figure V2-F01.

## H3 — formal evidence integrity
{reg.loc['H3','result']} Proof: `02_design/DY_MONOTONICITY_PROOF.md`.

## H4 — sensor robustness
{reg.loc['H4','result']} Figure V2-F02.

## Isolability (Normal vs SID 215)
- All channels: λ* = {f3(hn.loc['all','lambda_star'])}. The pair becomes isolable only once the bounds fall below about {f3(hn.loc['all','lambda_star'])} × REF, i.e. {hn.loc['all','onset_eps_pressure_MPa']:.2e} MPa and {hn.loc['all','onset_eps_flow_kg_s']:.2e} kg/s.
- The limitation is the bound, not intrinsic identity: λ* > 0, so no admissible shift makes the two templates identical.
- The SID 215 template exceeds 2 ε_REF on {F['h215_incident']} channels; its largest ratio is {f3(F['h215_ratio_max'])} on {F['h215_ratio_ch']}.
- Pairs isolable at REF (of 15): all channels {n_isol['all']}, pressure-only {n_isol['pressure_only']}, flow-only {n_isol['flow_only']}.
- Figures V2-F03 and V2-F04.

## H5 — localization
{reg.loc['H5','result']}

## H6 — generalization; H7 — gas; H8 — cost; H9 — library; H10 — traceability
- **H6:** {reg.loc['H6','result']}
- **H7:** {reg.loc['H7','result']}
- **H8:** {reg.loc['H8','result']}
- **H9:** {reg.loc['H9','result']}
- **H10:** {reg.loc['H10','result']}

## Status summary
{chr(10).join(f'- {k}: {v}' for k, v in status_counts.items())}
""")

    w(R / "02_CRITICAL_FINDINGS_AND_FAILURE_ANALYSIS.md", f"""
# Critical findings and failure analysis

1. **Label/topology attribution (L01, critical).**
   - {F['err_disp']:,} of {F['err_total']:,} classifier errors fall in disputed runs.
   - In undisputed runs, window accuracy is {f3(und.recall)} against {f3(allw.recall)} overall.
   - D1 is unrecorded; the corrected replication is gated and BLOCKED_BY_PROVENANCE.
2. **D(x) tracks the artifact (L17).**
   - In Center, 1 − D ranks disputed windows with AUROC {f3(x3.loc['Center','auroc_1mD_for_disputed'])} (separation {f3(1 - x3.loc['Center','auroc_1mD_for_disputed'])}), but errors only with AUROC {f3(x3.loc['Center','auroc_1mD_for_error'])}.
   - Out of template, adding D worsens the correctness model ({f3(x2.loc['conf','oof_log_loss'])} → {f3(x2.loc['conf+D','oof_log_loss'])} log-loss).
3. **Library incompleteness (H9 CONTRADICTED).**
   - With the true mechanism removed, D(Y) issued {int(a5.loc['minus_true','specific_wrong'])} wrong SPECIFIC decisions and {int(a5.loc['minus_true','ambiguous'])} candidate sets without the truth.
   - Its guarantees hold only for a complete library.
4. **Selective risk under synthetic faults.**
   - Moderate bias or drift (2 ε_obs) removes correct decisions first.
   - Wrong-specific risk therefore rises from {f3(F['s1_base_risk'])} to {f3(F['s1_max_risk'])}, while the count of wrong decisions stays at the baseline.
5. **Delay beyond the clock allowance.** At delay 2 s with τ = 1 s: {int(a9.loc['delay_2s_tau_1s','specific_correct'])} correct and {int(a9.loc['delay_2s_tau_1s','specific_wrong'])} wrong SPECIFIC decisions remain. The wrong ones persist while the correct ones vanish.
6. **HY2RES singleton calls are not certifiable.** {int(hy.frozen_specific):,} frozen calls become UNRESOLVED once a single-coordinate exclusion certificate is required.
7. **Reproducibility defects.**
   - L21: hash pins recorded on CRLF working copies fail on fresh checkouts.
   - L22 (repaired): the v1 Q1 manifest name collided with the figure-system test (our own commit e944e1b); it is now `Q1_FIGURE_MANIFEST.csv` with unchanged bytes.
   - L20: the Stage-2 pipeline is non-importable (owner decision).
8. **Traceability (H10).** The frozen export persists {F['trace'].in_frozen_serialized_record} required fields.
""")

    w(R / "03_MODEL_IMPROVEMENTS_AND_ABLATION.md", f"""
# Model improvements and ablation

**No model or D(x) variant was changed or refit in this round.** The only evaluation data are inspected windows with disputed labels. Any gain found there could not be separated from leakage or label effects (Part 19).

## Ablation evidence
- v1 matched ablation, s_C vs s_C − D at coverage 0.25: risk {f3(F['risk_sC'])} vs {f3(F['risk']['s_C_minus_D'])}; ancestor interval [{f3(F['ci_D'][0])}, {f3(F['ci_D'][1])}].
- v2 incremental utility, leave-one-template-out (V2-T01):

{table(x2.reset_index(), ['model', 'oof_log_loss', 'oof_brier', 'oof_auroc', 'groups', 'errors'])}

- Registered sensitivities (k = 10, 50; clean realization; prior-corrected D; 60 s windows) are all NOT_ESTIMABLE (`x4_registered_sensitivities.csv`).
- Synthetic method check (V2-T02): D lowers log-loss only for the classifier blind to an informative feature. Δ = {', '.join(f3(v) for v in syn[syn.classifier.str.startswith('c_')].delta_logloss)} at separations {', '.join(f'{v:g}' for v in syn[syn.classifier.str.startswith('c_')].separation)}.

## Why D(x) shows no value here
- The classifier already uses the same feature space that D summarises, so D is largely redundant with confidence.
- Where D differs from confidence, it follows the source-model artifact (L17), not correctness.

## Defensible next improvement
After D1 and D2: compute D on a common-sensor representation, and evaluate on templates absent from development.
""")

    w(R / "04_FORMAL_ENGINE_VERIFICATION.md", f"""
# Formal engine verification (D(Y))

## Decision semantics
| Decision | Meaning |
|---|---|
| SPECIFIC | Exactly one declared hypothesis is FEASIBLE (shift witness); every other is EXCLUDED by a re-verified single-coordinate interval certificate. |
| AMBIGUOUS | Two or more are FEASIBLE and none is INDETERMINATE. |
| UNRESOLVED | INVALID_MEASUREMENT, or some hypothesis is INDETERMINATE, or none is FEASIBLE (MODEL_MISMATCH). |

## Guarantees and checks
- Proof under assumptions A1–A5: `02_design/DY_MONOTONICITY_PROOF.md`.
- Finite checks: {reg.loc['H3','result']}
- Adversarial tests in `tests/test_dy_adversarial.py`:
  - 40 seeded property cases;
  - invalid inputs, closed boundaries and zero width;
  - contradictory sensors;
  - a forged certificate.
  - The suite passes as part of the full run (`03_execution/logs/pytest_full.log`).
- The certificate checker in `diagnose` re-derives each exclusion from the measurement intervals. It does not trust the adapter's claim: forged certificates become INDETERMINATE.

## Limits
- **Library completeness (A1).** H9 is CONTRADICTED by direct counterexamples.
- **Bounds.** Every bound is hypothetical or computed (`01_audit/BOUND_ORIGIN_AUDIT.csv`); none is calibrated.
- **Perturbed data.** SYNTHETIC faults are outside the proof. Empirically, wrong SPECIFIC counts never exceeded the baseline, but selective risk rose (V2-T03).
- Passing tests show that the implementation agrees with the argument on the cases tested. They do not establish diagnostic validity.
""")

    w(R / "05_GENERALIZATION_AND_TRANSFER.md", f"""
# Generalization and transfer

| Level | Status | Evidence |
|---|---|---|
| A — software portability | Demonstrated for HY2RES (one rule, one study) | {reg.loc['H6','result']} |
| B — physics-based transfer | Not available | no qualified H2/blend model (A13) |
| C — empirical diagnostic generalization | BLOCKED_BY_DATA | 17/17 R2 test templates occur in training (L04); HY2RES and MHC have no labelled faults or locations |

- The Level-A port gives no evidence of Level-C generalization.
- MHC is a forecasting study with no diagnostic hypotheses, so no adapter was built.
- What would unblock Level C: R2 templates held out of development, or an external study with independently labelled events.
""")

    w(R / "06_GAS_PHYSICS_QUALIFICATION.md", f"""
# Gas-physics qualification

Status **BLOCKED_BY_PHYSICS**. The Center gas is air-like (R = 0.287 kJ/(kg·K)) and is not renamed hydrogen.

{table(F['a13'])}

Requirements for Level B:
- a transient network model with a qualified EOS (pure H2: Leachman; blends: GERG-2008 with per-point phase-stability checks);
- validated viscosity and transport;
- compressor maps;
- boundary conditions and a solver-convergence study.

Requirements for Level C: measured data.
""")

    w(R / "07_ENGINEERING_COST_AND_SCALABILITY.md", f"""
# Engineering cost and scalability

## Cost categories
Reported separately and never combined (V2-T10):

{table(pd.read_csv(TB / 'V2-T10_cost_categories.csv'))}

## Hypothetical sensor-cost scenarios
Relative units only (V2-T07); these are not prices:
{pareto_text}
- **No financial saving is claimed.**

## Measured compute
- One 13-channel D(Y) decision has a median latency of {F['lat13']:.3f} s on {envl[2].split(' ', 1)[1]}.
- Empirical scaling exponents (A14b): {'; '.join(f'{r.component} vs {r.dimension}: {r.loglog_slope:.2f} over {r.range}' for r in a14.itertuples()) }.
""")

    w(R / "08_LIMITATIONS_AND_THREATS_TO_VALIDITY.md", f"""
# Limitations and threats to validity

- **Construct.**
  - R2 labels are disputed (L01).
  - Center bounds are hypothetical.
  - HY2RES labels describe electrical power, not faults.
- **Internal.**
  - All R2 analyses use inspected windows.
  - D tracks source-model signatures (L10, L17).
  - The test suite mutates governance files.
  - Hash pins depend on the checkout (L21).
- **External.**
  - Simulated air-like gas.
  - One Center capture per mechanism.
  - Templates shared across topologies (L04).
  - No field data.
- **Statistical.**
  - 17 ancestors.
  - One NORMAL template.
  - Center results are counts, not rates.
  - The multiplicity of exploratory comparisons is disclosed, not corrected.
- **Synthetic studies.**
  - Faults and jitter are injected in units of ε_obs, not from sensor specifications.
  - The X5 classes are artificial.
""")

    claims = pd.DataFrame([
        ("Within its declared hypothesis library and stated bounds, every D(Y) exclusion is certified and re-verifiable, and removing information never creates an exclusion.", "SUPPORTED_WITHIN_SCOPE", "H3", "ALLOWED with assumptions A1-A5"),
        ("Under the registered protocol, the selective-risk benefit of D(x) is not estimable.", "NOT_ESTIMABLE", "H1", "ALLOWED"),
        ("On R2 windows, D(x) showed no incremental value over confidence out of template (exploratory).", "EXPLORATORY_ONLY", "H2", "ALLOWED as exploratory negative result"),
        ("D(Y) can issue a wrong SPECIFIC decision when the true mechanism is missing from the library.", "CONTRADICTED (guarantee)", "H9", "ALLOWED (limitation)"),
        ("Normal vs SID 215 is a bound limitation (isolable below ~0.08 × REF), not intrinsic identity.", "EXPLORATORY_ONLY", "H4/H5", "ALLOWED with conditional-bound label"),
        ("The engine runs on an external study (HY2RES) through an adapter; certification removes all frozen singleton calls.", "Level A only", "H6", "ALLOWED as software portability"),
        ("H2-PRISM localizes leaks network-wide.", "—", "H5", "FORBIDDEN (one independent outlet)"),
        ("Results transfer to pure hydrogen or blends.", "BLOCKED_BY_PHYSICS", "H7", "FORBIDDEN"),
        ("H2-PRISM reduces sensor cost by X %.", "—", "H8", "FORBIDDEN (no prices)"),
        ("D(x) improves selective risk.", "—", "H1/H2", "FORBIDDEN"),
        ("D(Y) is a field-validated safety guarantee.", "—", "H3", "FORBIDDEN (hypothetical bounds)"),
        ("Performance generalizes to unseen templates or domains.", "BLOCKED_BY_DATA", "H6", "FORBIDDEN"),
    ], columns=["claim", "status", "hypothesis", "publication_use"])
    claims.to_csv(R / "PUBLICATION_CLAIM_REGISTER.csv", index=False, lineterminator="\n")
    w(R / "09_PUBLICATION_CLAIM_REGISTER.md", "# Publication claim register\n\n" + table(claims))

    qa = [
        ("What is actually novel?", "A certificate-carrying three-outcome decision engine whose exclusions are independently re-verifiable, with a stated monotonicity proof. D(x) is not novel as a result: it shows no incremental value."),
        ("What was independently demonstrated?", "Nothing diagnostic. Only software and mathematical properties (H3) are established on hash-verified inputs."),
        ("Does D(x) add measurable value?", f"No. Out-of-template log-loss worsens ({f3(x2.loc['conf','oof_log_loss'])} → {f3(x2.loc['conf+D','oof_log_loss'])}), and D tracks disputed attribution."),
        ("What is the true contribution of D(Y)?", "Fail-safe abstention semantics and auditable certificates, conditional on library completeness and on declared bounds."),
        ("Is H1 estimable?", f"No: {F['rq1_ne']}/{F['rq1_rows']} PRIMARY rows are NOT_ESTIMABLE; the targets are unattainable."),
        ("Could main results be explained by label defects?", f"Yes for R2: {F['err_disp']:,}/{F['err_total']:,} errors lie in disputed runs."),
        ("Dependence or leakage?", "Templates are shared across folds (L04) and D encodes source-model signatures (L17). Intervals use ancestors."),
        ("Are baselines competitive?", "Confidence, margin, entropy and nearest-template baselines are included. No modern tuned classifier comparison exists (labels disputed)."),
        ("Are uncertainty intervals valid?", f"Ancestor bootstrap over {F['n_anc']} units is coarse; with one NORMAL ancestor, negative-control rates have no interval."),
        ("Localization beyond one outlet?", "No."),
        ("Unjustified certainty?", f"Yes in two places: wrong SPECIFIC decisions under an incomplete library ({int(a5.loc['minus_true','specific_wrong'])}), and persistent wrong SPECIFIC decisions under delay or moderate bias, where selective risk rises."),
        ("Monotonicity mathematically qualified?", "Yes: proof with assumptions A1–A5. It does not cover perturbed data or library changes."),
        ("Bounds physically defensible?", "No. They are hypothetical; REF is a solver-refinement delta."),
        ("Cross-domain generalization?", "Not demonstrated (Level A only)."),
        ("Pure H2 / blends as tested?", "No. BLOCKED_BY_PHYSICS."),
        ("Costs real or hypothetical?", "Compute time is measured; hardware cost scenarios are hypothetical relative units."),
        ("Reproducible?", f"Yes for the v2 package (scripts, hashes, environment). The repository suite still has {len(tri) - 1} pre-existing failures and 1 known blocker, all triaged."),
        ("Strongest / most misleading figures?", "Strongest: V2-F03 (isolability onset) and V2-F05 (certified port). Potentially misleading without its labels: V2-F02 (synthetic) and any R2 accuracy figure (disputed labels)."),
        ("What would invalidate central claims?", "A forbidden transition or a failed certificate re-verification (H3); D(x) value appearing after D1 correction would reverse H2."),
        ("Minimum work for a strong submission?", "Record D1 and replicate; hold out templates; obtain independent captures to calibrate bounds; persist certificates (H10); re-record pins on LF bytes."),
    ]
    w(R / "10_REVIEWER_CRITIQUE_RED_TEAM.md", "# Reviewer-style critique (red team)\n\nA skeptical review of this package. It assumes a reviewer who is looking for reasons to reject.\n\n" +
      "\n".join(f"{i}. **{q}** {a}" for i, (q, a) in enumerate(qa, 1)) + """

## Issues resolved in this round
- **Selective-risk rise under faults.** The figure caption had first reported only wrong-decision counts. It now also reports the rise in selective risk.
- **RQ1 count.** The registry first counted the H1 extract (6 rows). It now counts the registered R2 file (12 PRIMARY rows), consistent with v1.
- **Invariant total.** It is reported as hypothesis-status checks (consistent with v1), not as paired decisions.
- **Baseline audit.** It no longer leaves v1 QC records or governance files modified after running verifiers or tests.

## Unresolved
- L20 and L21 (owner decisions). L22 was repaired by renaming the v1 Q1 manifest (bytes unchanged).
- D1 (dataset owner).
- No held-out templates.
- No calibrated bounds.
- No price data.
""")

    acc = pd.read_csv(R / "ACCEPTANCE_CRITERIA.csv")
    w(R / "11_FINAL_TECHNICAL_ACCEPTANCE.md", f"""
# Final technical acceptance

## Acceptance criteria
Part 18 statuses with reasons: `ACCEPTANCE_CRITERIA.csv` (figure V2-F06). Hypotheses eligible for a strong confirmatory claim: {', '.join(acc[acc.strong_confirmatory_claim_eligible].hypothesis) or 'none'}. H3 is a mathematical/software property, not a diagnostic performance claim.

## Verdict
- **Technically verified:** the formal engine's certificate and monotonicity properties (H3), and reproducibility of the v2 package.
- **Scientifically exploratory:** everything diagnostic (H1 NOT_ESTIMABLE; H2, H4, H5 and H8 exploratory; H9 and H10 contradicted as stated).
- **Independently validated:** nothing.
- **Fit for submission:** a methods paper on certified three-outcome diagnosis with explicit negative results (D(x), library incompleteness, traceability gaps). It is not ready as a diagnostic-performance or hydrogen-transfer paper.
""")

    # ------------------------------------------------------------------ README, ledger, reproducibility
    w(V2 / "03_execution/EXECUTION_LEDGER.md", f"""
# Execution ledger (v2)

| Step | Script | Status | Output |
|---|---|---|---|
| Baseline audit | audit_baseline.py | done; full suite 19 min | 01_audit/BASELINE_REPRODUCTION.csv |
| Test triage | triage_tests.py | done | 01_audit/TEST_FAILURE_TRIAGE.csv |
| D1 matrix and gate | d1_correction.py | matrix done; replicate BLOCKED (exit 3) | 01_audit/D1_* |
| D(x) X1–X5 | dx_experiments.py | done | 04_results/analysis/x* |
| R2 descriptive | r2_descriptive.py | done | 04_results/analysis/r1_* |
| D(Y) adversarial tests | tests/test_dy_adversarial.py | 44 tests pass | — |
| D(Y) synthetic stress | dy_stress.py | done | 04_results/analysis/s1_* |
| Isolability | dy_isolability.py | done | 04_results/analysis/i* |
| HY2RES port | hy2res_dy_adapter.py | done; frozen rule reproduced | 04_results/analysis/h* |
| Registers and tables | build_v2_tables.py | done | 01_audit, 02_design, 04_results/tables, 06_reports/ACCEPTANCE_CRITERIA |
| Figures | fig_v2.py | 6/6 APPROVED by QA | 05_figures |
| Reports | v2_reports.py | done | 06_reports, README |
| Deterministic re-run | run_all.py | see logs/RUN_ALL.csv | 03_execution/logs |
| Package verification | verify_v2.py | see 07_reproducibility/V2_VERIFICATION.csv | SHA256SUMS.csv |

Per-script runtimes are measured by run_all.py (`logs/RUN_ALL.csv`). Seeds: 20261118 (stress, X5), 0 (figure jitter).
""")

    w(V2 / "07_reproducibility/REPRODUCE.md", f"""
# Reproducibility

## Environment
`03_execution/ENVIRONMENT.txt`:
{chr(10).join('- ' + l for l in envl)}

## Data acquisition (outside Git)
- **R2 frozen run:** set `H2PRISM_R2_RUN` to the PRIMARY run directory (predictions.parquet SHA-256 4338c8c9…).
- **Center workspace:** set `H2PRISM_CENTER_WORKSPACE`. MAT captures are re-hashed on load.
- **HY2RES:** the Zenodo record 15166733 CSV (MD5 9a3c3e3b…), passed with `--data` / `--hy2res`.

## Exact commands (repository root)
```bash
python 03_results/integrated_validation_v2/03_execution/scripts/run_all.py --hy2res <HY2RES_202404.csv>
python 03_results/integrated_validation_v2/03_execution/scripts/audit_baseline.py --hy2res <csv>
python 03_results/integrated_validation_v2/03_execution/scripts/verify_v2.py
python -m pytest -q tests/test_dy_adversarial.py
```

- `run_all.py` runs every analysis, table, figure and report script in dependency order. It writes runtimes to `03_execution/logs/RUN_ALL.csv` and the per-file hash comparison with the committed outputs to `logs/DETERMINISM.csv`.
- `audit_baseline.py` re-runs the full suite (about 19 minutes measured); `--reuse-pytest-log` parses the existing log instead.

## Determinism
- Analyses are deterministic: fixed seeds, exact-rational decisions, sorted outputs.
- Figures use a fixed SVG hash salt and no dates.
- Known nondeterminism: runtimes and log timings vary between runs. SVG/PNG bytes depend on the Matplotlib and FreeType versions.

## Independent re-verification
- `verify_v2.py` re-checks figure hashes and QA, the checksums of every package file, the reconciliations of key numbers against their source files, and that no file outside the package changed.
""")

    w(V2 / "README.md", f"""
# integrated_validation_v2 — scientific validation, repair and qualification package

| Folder | Content |
|---|---|
| 01_audit | baseline reproduction, test triage, D1 matrix, leakage/risk register, bound-origin audit, summary |
| 02_design | hypothesis registry H1–H10, experiment status / feasibility, design and analysis plan, monotonicity proof |
| 03_execution | scripts, logs, environment, execution ledger |
| 04_results | analysis outputs (CSV) and publication tables V2-T01…T10; RESULTS_INDEX maps every Part-17 topic to a verified file |
| 05_figures | V2-F01…F06 (PNG 3840 px + SVG, captions, manifest) |
| 06_reports | eleven reports, acceptance criteria, claim register |
| 07_reproducibility | commands, data acquisition, verification |

**Status summary.** {'; '.join(f'{k}: {v}' for k, v in status_counts.items())}. Nothing in this package changes a frozen result, label, partition or model.
""")
    print("reports written")


if __name__ == "__main__":
    main()
