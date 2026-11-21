"""Build advanced-validation tables A01-A20 (CSV + Markdown) from analysis outputs and curated, sourced registers.

Numbers come only from advanced_validation/analysis, benchmarks, h1_validation/analysis or frozen tables.
Rows for blocked studies carry a status, never a fabricated value.
Usage (repository root): python 03_results/integrated_validation_v1/advanced_validation/scripts/av_tables.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

AV = Path(__file__).resolve().parents[1]
ROOT = AV.parent
REPO = Path(__file__).resolve().parents[4]
A, T = AV / "analysis", AV / "tables"
H1A = ROOT / "h1_validation/analysis"
CEN = REPO / "03_results/validation/center_evidence_enhancement"


def fmt(v):
    if isinstance(v, (bool, np.bool_)):
        return "yes" if v else "no"
    if isinstance(v, (float, np.floating)):
        if np.isnan(v):
            return "—"
        if v == 0:
            return "0"
        return f"{v:.3g}" if abs(v) < 1e-3 or abs(v) >= 1e5 else f"{v:.4g}"
    if isinstance(v, (int, np.integer)):
        return f"{v:,}"
    return str(v)


def export(df, tid, title, note, sources):
    T.mkdir(parents=True, exist_ok=True)
    df.to_csv(T / f"{tid}.csv", index=False, lineterminator="\n", float_format="%.10g")
    head = "| " + " | ".join(map(str, df.columns)) + " |\n|" + "---|" * len(df.columns) + "\n"
    body = "\n".join("| " + " | ".join(fmt(v) for v in r) + " |" for r in df.itertuples(index=False))
    md = f"### {tid} — {title}\n\n{note}\n\n{head}{body}\n\nSource: " + "; ".join(f"`{s}`" for s in sources) + "\n"
    (T / f"{tid}.md").write_text(md, encoding="utf-8", newline="\n")
    return md


def a01():
    p = pd.read_csv(H1A / "h1_05_paired_comparisons.csv")
    df = p[["coverage", "method_b", "n_selected_each", "risk_a", "risk_b", "delta_R", "family_ci_low", "family_ci_high",
            "ancestor_ci_low", "ancestor_ci_high", "ancestors_discordant_errors", "n_errors_undisputed_a",
            "n_errors_undisputed_b"]].rename(columns={"method_b": "comparator", "risk_a": "risk_s_C", "risk_b": "risk_comparator",
                                                       "n_selected_each": "specific_each"})
    df.insert(5, "relative_change", (df.risk_s_C - df.risk_comparator) / df.risk_comparator.replace(0, np.nan))
    df["status"] = "EXPLORATORY_POST_HOC"
    return export(df, "A01", "H1 matched-coverage benchmark",
                  "Rank-matched exact-count selections on the 27,993 frozen R2 windows (identical counts per method). "
                  "relative_change undefined when the comparator risk is 0. Registered verdict unchanged: NOT_ESTIMABLE.",
                  ["h1_validation/analysis/h1_05_paired_comparisons.csv"])


def a02():
    a = pd.read_csv(A / "av_r2_wrong_specific_accounting.csv").drop(columns="analysis_status")
    c = pd.read_csv(A / "av_r2_wrong_specific_by_class.csv").drop(columns="analysis_status")
    c = c[c.coverage_requested.isin([1.0, 0.25])]
    m1 = export(a, "A02a", "Wrong-specific accounting (R2)",
                "Denominator: 27,993 windows (population); risk = wrong / specific. Confidence = max calibrated probability. "
                "Disputed runs: source-model attribution inconsistent with the manifest (D1 pending). EXPLORATORY_POST_HOC.",
                ["advanced_validation/analysis/av_r2_wrong_specific_accounting.csv"])
    m2 = export(c, "A02b", "Wrong-specific accounting by true class (R2; no abstention and coverage 0.25)",
                "class_coverage = specific / windows of the class. EXPLORATORY_POST_HOC.",
                ["advanced_validation/analysis/av_r2_wrong_specific_by_class.csv"])
    d = pd.read_csv(A / "dy_outcome_by_query.csv")
    d = d[(d.config_family.isin(["all", "restricted", "minus_true", "minus_NORMAL", "flow_only", "pressure_only"]))]
    m3 = export(d, "A02c", "Center formal D(Y) outcomes by query (counts over bound scenarios)",
                "CONDITIONAL_HYPOTHETICAL_BOUNDS; E1 rows: S3, S4, S5, REF; E4 rows: S1–S6, REF. Repeated views of one capture "
                "per query.", ["advanced_validation/analysis/dy_outcome_by_query.csv"])
    return "\n".join([m1, m2, m3])


def a03():
    ts = pd.read_csv(A / "av_r2_template_sharing.csv")
    gap = pd.read_csv(A / "av_r2_train_test_gap.csv")
    acc = pd.read_csv(A / "av_r2_wrong_specific_accounting.csv")
    a0 = acc[acc.method == "A_classifier_no_abstention"].iloc[0]
    rows = [
        ("L01 source-folder / topology attribution", "R2 (H2-SimNet)", "03_results/diagnostics/forensics/source_model_attribution.csv",
         f"36/57 runs inconsistent; {int(a0.wrong_in_disputed_runs):,}/{int(a0.n_wrong_specific):,} classifier errors in disputed runs",
         "critical", "R2 accuracy, RQ1 feasibility, every exploratory H1 contrast", "adopt manifest v0.3 (option B) or ask authors",
         "D1 (dataset owner)", "CONFIRMED DEFECT, UNCORRECTED"),
        ("L02 exact duplicate captures", "Center, R2", "TAB_C01.csv; source_model_attribution.csv",
         "13/13 Center capture hashes unique; 57/57 R2 file hashes unique", "none", "—", "none", "—", "CHECKED: NONE FOUND"),
        ("L03 near-duplicate templates", "Center", "TAB_C02/TAB_C03",
         "ALT vs SID213 differ only by a +0.005 MPa overlay (B3 2.8e-5); PS3 and PS10 bitwise identical channels",
         "high for localization", "SID 213 ranking and recognition (Q213-alt)", "report as one location, two captures",
         "none", "CONFIRMED, DISCLOSED"),
        ("L04 shared generating templates across held-out topologies", "R2",
         "advanced_validation/analysis/av_r2_template_sharing.csv",
         f"{int(ts.test_ancestors_also_in_training_topologies.min())}/{int(ts.test_ancestors.max())} test templates present in "
         f"training topologies in every fold (share of test windows {ts.share_test_windows_with_training_ancestor.min():.0%}); "
         "families disjoint", "critical for generalization", "any out-of-template generalization claim",
         "evaluate on templates absent from development", "new data", "CONFIRMED (design property)"),
        ("L05 window overlap within runs", "R2", "WINDOWING_SPEC.md",
         "windows serially dependent within runs; family-level grouping used", "medium", "window-level rates",
         "family / ancestor units", "none", "CONTROLLED (grouped evaluation)"),
        ("L06 split by row instead of source", "MHC, HY2RES", "study_b/split_manifest.csv; HY2RES Gate D",
         "MHC split by run; HY2RES chronological with 1 h embargo, 0 shared segments", "low", "—", "none", "—", "CHECKED: NOT PRESENT"),
        ("L07 preprocessing / calibration on evaluation data", "R2", "DISTINGUISHABILITY_MATHEMATICAL_SPEC.md; calibration_records.json",
         "z-scoring and calibration fitted on development only; identity calibration selected in all folds", "low", "—",
         "none", "—", "CHECKED: NOT PRESENT"),
        ("L08 hyperparameter selection after test inspection", "R2 / Protocol 2.0", "folds/*/selection.csv; PROTOCOL_2_0_OWNER_DECISIONS.md",
         "R2 selection inner-CV only; Protocol 2.0 arms reused inspected windows", "high for Protocol 2.0", "development ablation claims",
         "independent evaluation", "new data", "CONFIRMED RISK (Protocol 2.0 exploratory)"),
        ("L09 self-template matching", "Center", "TAB_C02",
         "frozen library recognition 7/7 by self or near-duplicate match; 3/5 without", "critical (Center)", "recognition claims",
         "leave-own-template-out (done)", "none", "CONFIRMED, CORRECTED IN ANALYSIS"),
        ("L10 topology / source identifiers in features", "R2", "FEATURE_DEFINITION_REGISTER.csv; diagnostics/feature_representation",
         "source-model sensor set (PS11, PS12, MFS4 only in down model) is visible in features; neighbour share from same model 0.85 for Center LEAK",
         "high", "classification and D(x) behaviour", "common-sensor representation (Protocol 2.0 arm C)", "D2", "CONFIRMED RISK"),
        ("L11 outcome-derived quantities", "MHC", "error_vs_change.csv",
         "|Δy| bins use the outcome; used for retrospective explanation only, never as features", "low", "—", "labelled retrospective",
         "—", "CONTROLLED"),
        ("L12 post hoc selection of evaluation points", "H1 exploratory", "diagnose_primary_run.py EXPLORATORY_GRID",
         "grid fixed before the H1 analysis; no point chosen by outcome", "medium", "exploratory H1", "fixed grid", "—", "CONTROLLED"),
        ("L13 repeated testing / multiplicity", "H1 exploratory", "h1_05_paired_comparisons.csv",
         "6 comparators × 5 coverages × 2 unit types reported; no significance claimed", "medium", "exploratory H1",
         "report all; no selection", "—", "DISCLOSED"),
        ("L14 training vs held-out gap", "R2", "advanced_validation/analysis/av_r2_train_test_gap.csv",
         "; ".join(f"fold {r.fold}: inner CV macro-F1 {r.inner_cv_macro_f1_selected:.3f} vs outer accuracy {r.outer_test_accuracy:.3f}"
                   for r in gap.itertuples()),
         "high", "overfitting interpretation", "gap is inverted in folds 2–3: dominated by label corruption and distribution shift, "
         "not by capacity", "—", "EXPLAINED (label corruption + shift)"),
        ("L15 HY2RES model-training code not tracked", "HY2RES", "STUDY_C_REPRODUCE.md",
         "frozen predictions verified by 60/60 metric reconciliation; historical test-access seal unverified", "medium",
         "HY2RES held-out claim", "recover or re-register the training script", "Study C owner", "UNVERIFIED RISK"),
        ("L16 MHC dataset version provenance", "MHC", "study_b/source_manifest.json",
         "Zenodo 10.5281/zenodo.19036733 v1.2; archive SHA-256 91755fb1…", "none", "—", "none", "—", "CHECKED"),
    ]
    df = pd.DataFrame(rows, columns=["issue", "affected_study", "files", "evidence", "severity", "impacted_claims",
                                     "corrective_action", "approval_needed", "status"])
    return export(df, "A03", "Data leakage and evaluation-integrity register",
                  "Confirmed defects are separated from risks that could not be verified.",
                  ["see 'files' column", "advanced_validation/analysis/av_r2_*"])


def a04():
    I = pd.read_csv(A / "dy_invariant_checks.csv")
    d = pd.read_csv(A / "dy_experiment_runs.csv")
    s = I.groupby("test").agg(paired_comparisons=("pair", "size"), hypothesis_checks=("hypotheses_compared", "sum"),
                              violations=("violations", "sum")).reset_index()
    s.loc[len(s)] = ["EXCLUDED certificates re-verified independently", len(d), int(d.excl_cert_total.sum()),
                     int(d.excl_cert_total.sum() - d.excl_cert_verified.sum())]
    s.loc[len(s)] = ["FEASIBLE witnesses re-verified (exact rationals)", len(d), int(d.witness_total.sum()),
                     int(d.witness_total.sum() - d.witness_verified.sum())]
    s["result"] = np.where(s.violations == 0, "PASS", "FAIL")
    m1 = export(s, "A04a", "Formal D(Y) mathematical and numerical integrity",
                "Allowed transitions when information is removed or uncertainty widened: FEASIBLE→FEASIBLE; "
                "EXCLUDED→any; INDETERMINATE→INDETERMINATE/FEASIBLE. 'violations' counts forbidden transitions or "
                "failed re-verifications.", ["advanced_validation/analysis/dy_invariant_checks.csv", "dy_experiment_runs.csv"])
    q = pd.DataFrame([
        ("Mathematical correctness (engine semantics)", "VERIFIED", "0 invariant violations; all certificates and witnesses re-verify"),
        ("Invalid-input handling", "IMPLEMENTED", "MeasurementContract.issues → UNRESOLVED/INVALID_MEASUREMENT (tests/test_certified_evidence.py)"),
        ("Unsupported hypotheses", "VERIFIED", "always INDETERMINATE; full universe 42/42 UNRESOLVED (E4)"),
        ("Observation and model bounds", "HYPOTHETICAL", "declared ladder S1–S6; REF = solver-refinement deltas (scale reference, not an enclosure)"),
        ("Physical uncertainty qualification", "NOT ESTABLISHED", "no instrument specification or model-error enclosure"),
        ("Decision correctness inside an incomplete library", "FAILS AS EXPECTED", "restricted universe: wrong SPECIFIC whenever truth absent and a rival fits"),
        ("Physical validation", "NOT ESTABLISHED", "air-like simulation, one source family"),
    ], columns=["aspect", "status", "evidence"])
    m2 = export(q, "A04b", "Formal D(Y) qualification by aspect", "Evidence versus decision are reported separately.",
                ["A04a", "A05", "02_methodology/HYDROGEN_MODEL_SPECIFICATION.md"])
    return m1 + "\n" + m2


def summary_rows(exp, families=None):
    s = pd.read_csv(A / "dy_outcome_summary.csv")
    s = s[s.experiment == exp]
    if families:
        s = s[s.config_family.isin(families)]
    return s.drop(columns=["label"])


def a05():
    return export(summary_rows("E4_library"), "A05", "Hypothesis-library completeness",
                  "All 13 channels, ±1 s, S1–S6 and REF (42 decisions per variant: 6 queries × 7 scenarios). "
                  "CONDITIONAL_HYPOTHETICAL_BOUNDS.", ["advanced_validation/analysis/dy_outcome_summary.csv"])


def a06():
    rows = [("Level 1 — candidate-site ranking", "DEMONSTRATED (conditional)", "4 withdrawal queries; 3 candidate outlets",
             "ranking exists for every query, but only queries with an independent same-outlet template can be correct"),
            ("Level 2 — correct categorical outlet identification", "DEMONSTRATED FOR ONE OUTLET",
             "SID 213: 2 captures (Q213 with replicate, Q213-alt); near-duplicates → 1 independent location",
             "SID 312 and SID 215 unsupported (no independent template)"),
            ("Level 3 — topological branch localization", "NOT DEMONSTRATED BEYOND LEVEL 2",
             "outlets are branch ends; no intra-branch position", "lumped pipes without inertia (HYDROGEN_MODEL_SPECIFICATION P6)"),
            ("Level 4 — physical coordinate / distance", "NOT POSSIBLE", "no coordinates; SIDs are block identifiers", "—"),
            ("Level 5 — validated real-world localization", "NOT ESTABLISHED", "MHC/HY2RES: no locations", "—")]
    m1 = export(pd.DataFrame(rows, columns=["level", "status", "eligible_cases", "limitation"]), "A06a",
                "Localization levels", "Highest demonstrated level: 2, for one outlet.", ["TAB_C03", "localization_cases.csv"])
    L = pd.read_csv(A / "localization_cases.csv")
    b = L[L.method.str.startswith("B3")]
    sup = b[b.true_site_supported]
    agg = pd.DataFrame([dict(method="B3 nearest-template (forced, own template excluded + replicate)", cases=len(b),
                             supported_cases=len(sup), independent_locations_supported=sup.true_site.nunique(),
                             top1_correct_supported=int(sup.top1_correct.sum()), top1_correct_all=int(b.top1_correct.sum()),
                             mean_reciprocal_rank_supported=sup.reciprocal_rank.mean(),
                             mean_reciprocal_rank_all_forced=b.reciprocal_rank.mean())])
    m2 = export(agg, "A06b", "Categorical location-ranking metrics",
                "Eight query×condition rows of TAB_C03 (4 queries × 2 template conditions); repeated captures are not independent "
                "locations. Reciprocal rank 0 when the true outlet is absent from the candidates.",
                ["advanced_validation/analysis/localization_cases.csv"])
    return m1 + "\n" + m2


def a07():
    L = pd.read_csv(A / "localization_cases.csv")
    b = L[L.method.str.startswith("B3") & (L.condition == "loto_replicate")]
    f = L[L.method.str.startswith("formal")]
    n_dy = int(f.location_specific.sum())
    cov = n_dy / len(f)
    k = int(round(cov * len(b)))
    bm = b.sort_values("margin", ascending=False).head(k)
    rows = [dict(policy="B3 nearest template, no abstention", cases=len(b), location_specific=len(b),
                 coverage=1.0, wrong_location=int((~b.top1_correct.astype(bool)).sum())),
            dict(policy=f"B3 nearest template, top-{k} by ranking margin (matched to D(Y) coverage)", cases=len(b),
                 location_specific=k, coverage=k / len(b), wrong_location=int((~bm.top1_correct.astype(bool)).sum())),
            dict(policy="Formal D(Y), restricted universe (4 scenarios per query)", cases=len(f), location_specific=n_dy,
                 coverage=cov, wrong_location=int((f.location_specific & (f.top1_correct == False)).sum()))]  # noqa: E712
    df = pd.DataFrame(rows)
    df["wrong_location_risk"] = df.wrong_location / df.location_specific.replace(0, np.nan)
    df["independent_locations_with_support"] = 1
    df["status"] = "H-Loc EXPLORATORY (4 queries, 1 supported location)"
    return export(df, "A07", "Selective localization (H-Loc)",
                  "Location-specific = a single outlet issued. Matched coverage uses the ranking margin, fixed as the selection "
                  "score before looking at correctness. With one supported location no rate generalises.",
                  ["advanced_validation/analysis/localization_cases.csv"])


def a08():
    return export(summary_rows("E1_sensors"), "A08", "Missing-sensor robustness",
                  "Restricted universe, ±1 s; 24 decisions per configuration (6 queries × S3, S4, S5, REF); random_dropk rows pool "
                  "20 fixed masks (480 decisions). CONDITIONAL_HYPOTHETICAL_BOUNDS.",
                  ["advanced_validation/analysis/dy_outcome_summary.csv"])


def a09():
    s = pd.concat([summary_rows("E2_clock_bound"), summary_rows("E3_delay")])
    return export(s, "A09", "Timing uncertainty and alignment",
                  "E2: admissible clock bound τ widened with no delay. E3: observed signal delayed by d with τ = 1 s (unchanged) or "
                  "τ = d (widened). Jitter not executed (no jitter model).", ["advanced_validation/analysis/dy_outcome_summary.csv"])


def a10():
    e = pd.read_csv(A / "dy_evidence_availability.csv")
    return export(e, "A10", "Evidence availability (channel count) versus decision outcome",
                  "All E1 configurations grouped by number of available channels (configurations differ in which channels; see A08).",
                  ["advanced_validation/analysis/dy_evidence_availability.csv"])


def a11():
    n = pd.read_csv(A / "av_r2_negative_control_normal.csv").drop(columns="analysis_status")
    n = n[n.coverage_requested.isin([1.0, 0.1, 0.25])]
    m1 = export(n, "A11a", "Negative control — R2 NORMAL windows",
                "False LEAK calls among SPECIFIC decisions on true NORMAL windows. All NORMAL windows come from ONE scenario "
                "template (one run per topology). EXPLORATORY_POST_HOC.", ["advanced_validation/analysis/av_r2_negative_control_normal.csv"])
    c = pd.read_csv(CEN / "tables/TAB_C02.csv")
    c = c[c["query"].isin(["PRESSURE", "TIMING", "NOMINAL"])][["query", "condition", "true_mechanism", "predicted", "status"]]
    c["method"] = "B3 nearest mechanism"
    d = pd.read_csv(A / "dy_experiment_runs.csv")
    d = d[(d.experiment == "E1_sensors") & (d.config == "all") & d["query"].isin(["PRESSURE", "TIMING"])]
    dd = d.groupby("query").outcome.agg(lambda s: "; ".join(f"{k} ×{v}" for k, v in s.value_counts().items())).reset_index()
    dd = dd.rename(columns={"outcome": "predicted"})
    dd["condition"], dd["true_mechanism"], dd["status"], dd["method"] = "restricted, S3/S4/S5/REF", "operational", "no false withdrawal call", "formal D(Y)"
    m2 = export(pd.concat([c, dd[c.columns]]), "A11b", "Negative control — Center operational interventions",
                "Pressure-command change (SID 55), command-issuance shift (SID 59) and nominal run. These are command "
                "interventions, not equipment failures.", ["TAB_C02", "dy_experiment_runs.csv"])
    return m1 + "\n" + m2


def a12():
    rows = [
        ("Data ingestion", "h2prism.nres.load_pairs (hash-verifying)", "study_b/replay.py + verify_source.py (own)", "own CSV reader (evidence_enhancement/analysis.py)", "REIMPLEMENTED per study"),
        ("Timestamp processing / causal windowing", "fixed-step 30 s prefix (center_enhancement)", "one-step pairs per run (benchmark.py)", "causal segments, lag-1 (own)", "STUDY-SPECIFIC"),
        ("Channel metadata and units", "SensorRecord (data_contracts)", "channel_map.json", "CHANNEL_SCHEMA.csv", "STUDY-SPECIFIC"),
        ("Quality checks", "MeasurementContract.issues", "source/eligibility checks (own)", "validity mask (own)", "REIMPLEMENTED"),
        ("Reference prediction", "templates (no learned model)", "persistence + Ridge (sklearn, own)", "persistence + contextual Ridge (code not tracked)", "REIMPLEMENTED concept"),
        ("Uncertainty interface", "declared hypothetical bounds", "none (recording grid analysed)", "none (recording grid analysed)", "CENTER ONLY"),
        ("Evidence qualification", "D(Y) certificates", "—", "min–max support guard (own)", "NOT SHARED"),
        ("Hypothesis representation / decision policy", "certified_evidence.diagnose (executed)", "not executed", "own operating-state rule", "NOT PORTED"),
        ("Reporting / figures", "shared Q1 style (publication_q1)", "shared Q1 style", "shared Q1 style", "SHARED (presentation only)"),
        ("Source provenance", "SHA-256 per capture", "archive SHA-256/MD5", "MD5/SHA-256 of CSV", "SAME PRINCIPLE, own code"),
    ]
    df = pd.DataFrame(rows, columns=["component", "Center", "MHC", "HY2RES", "classification"])
    df["h2prism_package_imports_MHC_HY2RES"] = "0 (no import of h2prism in study_b/* or hy2res scripts)"
    return export(df, "A12", "Cross-study portability (actual code paths)",
                  "From import inspection: the MHC and HY2RES pipelines import no module of the h2prism package; the formal engine "
                  "has been executed only on Center. Code reuse is not evidence of diagnostic generalization.",
                  ["study_b/*.py", "03_results/hy2res_external_validation/**/*.py", "src/h2prism/center_enhancement.py"])


def a13():
    v1 = json.loads((REPO / "06_audit_preparation/simulation/h2net_v1/properties/V1_REPORT.json").read_text(encoding="utf-8"))
    pr = json.loads((REPO / "06_audit_preparation/simulation/h2net_v1/H2CH4_FEASIBILITY_PROBE.json").read_text(encoding="utf-8"))
    probe = {round(x["x_CH4"], 2): x for x in pr["imposed_gas_phase"]}
    env = v1["meta"]["envelope_validated"]
    rows = [("Air-like legacy (Center)", "R = 0.287 kJ/(kg·K); perfect gas, cp = 0.3469 → γ = 5.75 (>5/3, unphysical)", "existing Simscape captures",
             "physically inconsistent gas specification", "A: engine runs on it", "B/C: NOT QUALIFIED"),
            ("Natural-gas reference", "no property provider", "none", "—", "A: refused by interface", "B/C: NOT AVAILABLE"),
            ("H2/CH4 blends (e.g. 80–95 % H2)", f"CoolProp 7.2.0 GERG-2008 binary (Kunz 2012) probe at 300 K, 5 MPa: default flash FAILED for x_CH4 0.05/0.10/0.20; imposed gas phase Z = {probe[0.1]['Z']:.4f} at x_CH4 = 0.10",
             "none", "phase stability per point and transport validation required", "A: refused by interface (MixtureProviderUnavailable)", "B/C: NOT AVAILABLE"),
            ("Pure H2", f"tables from Leachman EOS (CoolProp 7.2.0), envelope {env['T'][0]:g}–{env['T'][1]:g} K × {env['p_MPa'][0]:g}–{env['p_MPa'][1]:g} MPa; "
             f"max interpolation error ρ {v1['checks']['interpolation_max_relative_error']['rho']:.2%}", "property tables only; no transient model built (H2Net v1 BLOCKED)",
             "transient model, boundary conditions, solver verification", "A: provider resolves; engine unit-agnostic", "B/C: NOT AVAILABLE")]
    df = pd.DataFrame(rows, columns=["composition", "property_basis_in_repository", "diagnostic_data", "missing_for_transfer",
                                     "level_A_software", "levels_B_C"])
    return export(df, "A13", "Gas-specific physical-model qualification",
                  "Level A = software accepts the composition without changing decision semantics; B = physics-based simulation "
                  "transfer; C = experimentally qualified diagnostic transfer. No diagnostic transfer result exists for any gas.",
                  ["06_audit_preparation/simulation/h2net_v1/properties/V1_REPORT.json", "H2CH4_FEASIBILITY_PROBE.json",
                   "02_methodology/GAS_COMPOSITION_INTERFACE.md", "02_methodology/HYDROGEN_MODEL_SPECIFICATION.md"])


def a14():
    b = AV / "benchmarks"
    dy = pd.read_csv(b / "dy_scaling.csv")
    dx = pd.read_csv(b / "dx_scaling.csv")
    fits = pd.read_csv(b / "scaling_fits.csv")
    hw = pd.read_csv(b / "hardware.csv", index_col=0)["value"]
    rt = pd.read_csv(b / "dy_decision_runtime_from_experiments.csv")
    cols = ["component", "dimension", "value", "median_s", "p95_s", "min_s", "max_s", "reps", "peak_tracemalloc_MB"]
    m1 = export(pd.concat([dy[cols], dx[cols]]), "A14a", "Measured computational performance",
                f"Hardware: {hw['cpu_model']}, {hw['logical_cpus']} logical CPUs, {hw['ram_GB']} GB RAM, {hw['platform']}; Python "
                f"{hw['python']}, NumPy {hw['numpy']}; single process; 2 warm-up runs; peak memory from tracemalloc (Python "
                "allocations). D(x) rows use SYNTHETIC arrays (numerical benchmark only).",
                ["advanced_validation/benchmarks/*.csv"])
    m2 = export(fits, "A14b", "Empirical scaling exponents (log–log slope over the measured range only)",
                "Slopes describe this implementation and hardware over the stated range; they are not complexity proofs.",
                ["advanced_validation/benchmarks/scaling_fits.csv"])
    q = rt.runtime_s
    m3 = export(pd.DataFrame([dict(decisions=len(rt), median_s=q.median(), p95_s=q.quantile(0.95), p99_s=q.quantile(0.99),
                                   max_s=q.max(), workers=7, note="per-decision wall time inside 7 parallel workers")]),
                "A14c", "Per-decision latency across all 2,376 experiment decisions",
                "Formal D(Y) on real Center captures; variable channel counts, clock bounds and libraries.",
                ["advanced_validation/benchmarks/dy_decision_runtime_from_experiments.csv"])
    return "\n".join([m1, m2, m3])


def a15():
    rows = [("A sensor procurement", "c_s,i per channel type (pressure, mass flow)", "no source-supported price in repository", "symbolic"),
            ("B installation", "c_inst,i (site, hot-tap or insertion)", "not available", "symbolic"),
            ("C calibration", "c_cal,i per interval", "not available", "symbolic"),
            ("D maintenance", "c_m,i per year", "not available", "symbolic"),
            ("E data acquisition / communication", "c_daq per channel", "not available", "symbolic"),
            ("F power / infrastructure", "c_pwr", "not available", "symbolic"),
            ("G compute hardware", "measured latency (A14) × required decisions per hour", "latency measured; hardware price not available", "partly measured"),
            ("H software runtime", "CPU-seconds per decision (A14)", "measured", "measured (time, not money)"),
            ("I inspection / follow-up", "c_FP × false-specific rate + c_FN × missed-event rate", "rates only conditional (Center) or exploratory (R2)", "symbolic")]
    df = pd.DataFrame(rows, columns=["cost_term", "parametric_form", "source_supported_value", "status"])
    df["total_cost_model"] = "C_total = Σ_i n_i (c_s,i + c_inst,i + c_cal,i + T·c_m,i + c_daq) + c_pwr + c_compute + c_FP·FP + c_FN·FN"
    return export(df, "A15", "Sensor-system cost assumptions",
                  "No price is invented. A monetary saving cannot be quantified until source-supported values exist; only sensor "
                  "count (A16) and CPU time (A14) are measured.", ["none — no cost source in the repository"])


def a16():
    iso = pd.read_csv(A / "dy_pairwise_isolability.csv")
    piv = iso.groupby(["scenario", "config"]).isolable.sum().reset_index(name="isolable_pairs_of_15")
    s = summary_rows("E1_sensors")
    s = s[~s.config_family.str.startswith("random")][["config_family", "n_channels", "specific_coverage", "specific_correct",
                                                       "specific_wrong", "ambiguous", "unresolved_model_mismatch"]]
    ref = piv[piv.scenario == "REF"].set_index("config").isolable_pairs_of_15
    s["isolable_pairs_REF"] = s.config_family.map(ref)

    def dominated(r, all_):
        return any((o.n_channels <= r.n_channels) and (o.specific_correct >= r.specific_correct) and (o.specific_wrong <= r.specific_wrong)
                   and ((o.n_channels, o.specific_correct, o.specific_wrong) != (r.n_channels, r.specific_correct, r.specific_wrong))
                   for o in all_.itertuples())
    s["pareto_nondominated"] = [not dominated(r, s) for r in s.itertuples()]
    m1 = export(s, "A16a", "Sensor count versus diagnostic utility (Center, conditional)",
                "Pareto on (fewer channels, more correct SPECIFIC, fewer wrong SPECIFIC) over the predeclared structured "
                "configurations; channel count is the only cost axis measured. isolable_pairs_REF from template-level isolability.",
                ["dy_outcome_summary.csv", "dy_pairwise_isolability.csv"])
    m = pd.read_csv(A / "dy_minimum_sensor_sets.csv")
    m2 = export(m, "A16b", "Minimum sensor sets preserving formal pairwise isolability",
                "Exhaustive search over all 8,191 non-empty channel subsets; a set qualifies if every hypothesis pair isolable with "
                "all 13 channels stays isolable (template level, ±1 s, conditional bounds).",
                ["advanced_validation/analysis/dy_minimum_sensor_sets.csv"])
    return m1 + "\n" + m2


def a17():
    rows = [
        ("Chow", 1970, "pattern recognition (theory)", "—", "—", "optimal error–reject trade-off", "—", "Bayes reject rule", "error–reject relation", "NOT REPORTED", "NOT REPORTED", "theory", "10.1109/TIT.1970.1054406", "CONTEXTUAL (foundation of selective risk)"),
        ("Geifman & El-Yaniv", 2017, "image classification", "—", "images", "selective classification", "—", "DNN + rejection function", "2 % top-5 error with 99.9 % probability at ~60 % coverage (ImageNet; abstract)", "NOT REPORTED", "NOT REPORTED", "benchmark dataset", "NeurIPS 2017 (arXiv 1705.08500)", "CONTEXTUAL (risk–coverage methodology)"),
        ("Puig", 2010, "industrial and water systems", "—", "real case studies", "set-membership fault diagnosis and FTC", "plant sensors", "interval / set-membership", "NOT EXTRACTED", "NOT REPORTED", "NOT REPORTED", "real cases", "10.2478/v10006-010-0046-y", "CONTEXTUAL (closest formal analogue of D(Y))"),
        ("Krysander, Åslund & Nyberg", 2008, "automotive engine model", "—", "structural model", "structural diagnosability / MSO sets", "—", "structural analysis", "1,419 MSOs in < 0.5 s (abstract)", "reported (algorithm)", "NOT REPORTED", "model-based", "10.1109/TSMCA.2007.909555", "CONTEXTUAL (isolability analysis)"),
        ("Pérez et al.", 2014, "water distribution network (Barcelona)", "water", "pressure sensors, real network", "leak localization, sensor placement", "pressure", "model-based sensitivity", "NOT EXTRACTED", "NOT REPORTED", "NOT REPORTED", "real network", "10.1109/MCS.2014.2320336", "CONTEXTUAL (different fluid)"),
        ("Murvay & Silea", 2012, "gas pipelines (survey)", "gas", "survey", "leak detection and localization", "various", "survey", "—", "—", "—", "review", "10.1016/j.jlp.2012.05.010", "CONTEXTUAL (survey)"),
        ("Zhu et al.", 2022, "buried pipeline, hydrogen-blended natural gas", "H2/NG blend", "experiment + model", "leakage and diffusion", "concentration", "experimental rig + model", "leak mass-flow model error 6.85 % (listing)", "NOT REPORTED", "NOT REPORTED", "experimental", "10.1016/j.ijhydene.2022.10.185", "NOT COMPARABLE (dispersion, not diagnosis)"),
        ("Lu et al.", 2024, "hydrogen-blended natural gas, buried", "H2/NG blend", "CFD", "leakage diffusion and alarm time", "—", "CFD", "NOT EXTRACTED", "NOT REPORTED", "NOT REPORTED", "simulation", "10.1016/j.ijhydene.2024.02.075", "NOT COMPARABLE"),
        ("Review (IJHE)", 2024, "hydrogen pipeline transport", "H2", "review", "transient flow, friction, leakage", "—", "review", "—", "—", "—", "review", "10.1016/j.ijhydene.2024.04.140", "CONTEXTUAL (modelling requirements for gas transfer)"),
    ]
    df = pd.DataFrame(rows, columns=["study", "year", "physical_system", "gas_type", "data_type", "diagnostic_task", "sensors",
                                     "model", "reported_metric", "runtime", "cost", "validation_level", "source_doi", "comparability"])
    df["comparability_gate"] = "FAILED (different task, system, data or metric) — no head-to-head number"
    return export(df, "A17", "Published-study comparison",
                  "DOIs taken from publisher or bibliographic listings found by search on 2026-11-18; verify on the publisher page "
                  "before formal citation. 'Reported metric' quotes abstracts or listings only; NOT EXTRACTED means the paper was "
                  "not read for metrics. Missing cost is NOT REPORTED, never zero.", ["web search, 2026-11-18"])


def a18():
    fields = [("source capture / run identity", True, True, "MeasurementContract.source_id/run_id; JSON: query only"),
              ("timestamps / window", True, False, "MeasurementContract.timestamps_s; JSON: none (implicit 30 s)"),
              ("valid sensors", True, False, "sensors; JSON: group name only"),
              ("measured units", True, False, "SensorRecord.unit"),
              ("quality checks", True, True, "measurement_issues"),
              ("candidate hypotheses", True, True, "results / consistent+excluded+indeterminate"),
              ("predicted signatures", False, False, "template labels only; trajectories not serialized"),
              ("residuals", False, False, "not recorded"),
              ("observation bounds", True, True, "absolute_errors; JSON: eps × split"),
              ("model bounds", False, True, "adapter-internal only; JSON: eps × (1 − split)"),
              ("time-alignment choice", True, False, "witness shift for FEASIBLE only"),
              ("exclusion certificates", True, False, "IntervalSeparation in memory; JSON: names only"),
              ("feasibility witnesses", True, False, "witness (template, shift) in memory"),
              ("decision", True, True, "status"),
              ("reason code", True, True, "reason"),
              ("source-model version", False, False, "SLX hash not attached to the decision")]
    df = pd.DataFrame(fields, columns=["required_field", "in_engine_certificate", "in_frozen_serialized_record", "where"])
    d = pd.read_csv(A / "dy_experiment_runs.csv")
    tot = pd.DataFrame([dict(required_field="TRACE COVERAGE", in_engine_certificate=f"{int(df.in_engine_certificate.sum())}/16",
                             in_frozen_serialized_record=f"{int(df.in_frozen_serialized_record.sum())}/16",
                             where=f"certificate re-verification: {int(d.excl_cert_verified.sum()):,}/{int(d.excl_cert_total.sum()):,} "
                                   f"exclusions, {int(d.witness_verified.sum()):,}/{int(d.witness_total.sum()):,} witnesses")])
    df = pd.concat([df.astype(str), tot.astype(str)])
    return export(df, "A18", "Traceability and evidence audit",
                  "Checklist of scientifically required provenance fields for one formal decision. The engine certificate carries "
                  "more than the frozen JSON export; exclusion certificates are verifiable but not persisted in the frozen record.",
                  ["src/h2prism/certified_evidence.py", "center_evidence_enhancement/analysis/dy_decisions.json", "dy_experiment_runs.csv"])


def a19():
    rows = [("Registered H1", "NOT ESTIMABLE", "R2 rq1.csv 12/12", "Gate 06/19"),
            ("H1 exploratory (s_C vs s_C−D)", "INCONCLUSIVE", "A01: intervals include 0; 0 errors outside disputed runs", "L01, L04"),
            ("Evidence guard vs conventional confidence", "EXPLORATORY, CONFOUNDED", "A02a: 0 vs 655 false LEAK calls on NORMAL at 0.25 — one template", "L01, L04"),
            ("D(x) incremental information", "NOT SUPPORTED", "development ablation", "—"),
            ("D(Y) engine semantics and certificates", "VERIFIED (mathematical)", "A04a: 0 violations; 11,061 + 1,552 re-verified", "—"),
            ("D(Y) refuses with incomplete declared library", "CONDITIONALLY DEMONSTRATED", "A05 full: 42/42 UNRESOLVED", "hypothetical bounds"),
            ("Restricted library → false SPECIFIC", "CONDITIONALLY DEMONSTRATED", "A05: minus-true 2/2 SPECIFIC wrong; restricted 2/10", "hypothetical bounds"),
            ("Missing pressure sensors increase false specificity", "CONDITIONALLY DEMONSTRATED", "A08: flow-only 4 wrong vs 2 (all)", "one family"),
            ("Delay beyond admissible clock bound → abstention", "CONDITIONALLY DEMONSTRATED", "A09: correct SPECIFIC 8 → 0, wrong unchanged 2", "one family"),
            ("Formal minimum sensor set (template level)", "CONDITIONALLY DEMONSTRATED", "A16b: 2 channels (MFS1+MFS3) preserve 14/15 pairs at REF", "templates, not field"),
            ("Categorical localization", "LEVEL 2, ONE OUTLET", "A06: SID 213, 2 captures", "L03"),
            ("Fault classification / localization accuracy", "BLOCKED BY EVIDENCE", "no independent labels", "—"),
            ("Pure-H2 or H2/NG diagnostic transfer", "NOT ESTABLISHED", "A13: no transient gas-specific model", "—"),
            ("Cost saving", "NOT QUANTIFIABLE", "A15: no source-supported prices", "—"),
            ("Computational scaling", "MEASURED (this hardware)", "A14", "—"),
            ("Cross-study engine portability", "NOT DEMONSTRATED", "A12: engine executed on Center only", "—")]
    return export(pd.DataFrame(rows, columns=["claim", "evidence_level", "evidence", "limiting_factor"]), "A19",
                  "Scientific claim-to-evidence matrix (advanced validation)", "Evidence levels in the project vocabulary.",
                  ["tables A01–A18"])


def a20():
    rows = [("H1", "independent scenario templates absent from development", "17 shared templates; all inspected", "new simulation campaign (H2Net v1) or new dataset"),
            ("H1", "corrected attribution", "36/57 runs disputed", "D1 decision (dataset owner)"),
            ("H1", "attainable registered coverage (0.80) verified on development", "Center 0.258", "≥ 2 independent families per class in every development reference"),
            ("H1", "nonzero independent errors for both policies", "0 outside disputed runs", "only new data"),
            ("H-Loc", "≥ 2 independent templates per outlet for ≥ 3 outlets", "1 outlet supported (near-duplicate pair)", "new captures per outlet with independent profiles"),
            ("H-Loc", "pre-registered location-coverage target", "none", "write before data access"),
            ("D(Y)", "qualified observation bounds", "hypothetical", "instrument specifications and calibration records"),
            ("D(Y)", "qualified model-discrepancy bounds", "solver-refinement deltas only", "model-validation study against measurements"),
            ("D(Y)", "complete declared library with adapters", "6 of 9 declared hypotheses modelled", "adapters for SID 222, compressor fault, actuator delay"),
            ("Gas transfer", "transient pure-H2 model and verification", "H2Net v1 blocked", "S2–S6/S8 decisions + MATLAB execution"),
            ("Gas transfer", "mixture property provider", "probe only", "authorization MODEL_DEVELOPMENT:H2NET_V1_BLEND_TABLES")]
    return export(pd.DataFrame(rows, columns=["target", "prerequisite", "current_status", "how_to_obtain"]), "A20",
                  "Confirmatory prerequisites for H1, H-Loc, D(Y) and gas transfer", "Nothing here can be met with existing data alone.",
                  ["h1_validation/H1_CONFIRMATION_REQUIREMENTS.md", "A06", "A13"])


def main():
    parts = [a01(), a02(), a03(), a04(), a05(), a06(), a07(), a08(), a09(), a10(), a11(), a12(), a13(), a14(), a15(),
             a16(), a17(), a18(), a19(), a20()]
    (T / "AV_TABLES_BUNDLE.md").write_text("# Advanced validation tables A01–A20\n\n" + "\n".join(parts), encoding="utf-8",
                                           newline="\n")
    print("tables:", len(list(T.glob("A*.csv"))))


if __name__ == "__main__":
    main()
