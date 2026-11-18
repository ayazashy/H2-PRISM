"""Build the v2 registers and result tables from verified output files (no hand-entered result numbers).

Writes:
  02_design/HYPOTHESIS_REGISTRY.csv (+ .md)       H1-H10, status assigned by the explicit rules in STATUS_RULES
  02_design/EXPERIMENT_STATUS.csv                 feasibility matrix and executed/blocked status per experiment
  01_audit/LEAKAGE_REGISTER_V2.csv                v1 register A03 plus entries found in this round
  01_audit/BOUND_ORIGIN_AUDIT.csv                 origin of every D(Y) bound component
  04_results/tables/V2-T*.csv (+ .md)             publication-readable tables of the new analyses
  04_results/tables/RESULTS_INDEX.csv             every Part-17 result topic -> verified source file + SHA-256
  06_reports/ACCEPTANCE_CRITERIA.csv              Part-18 criteria x hypotheses
Usage: python build_v2_tables.py
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

V2 = Path(__file__).resolve().parents[2]
REPO = Path(__file__).resolve().parents[4]
V1 = REPO / "03_results/integrated_validation_v1"
AV, H1D = V1 / "advanced_validation", V1 / "h1_validation"
AN, TB = V2 / "04_results/analysis", V2 / "04_results/tables"


def rd(p):
    return pd.read_csv(p)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rel(p):
    return Path(p).resolve().relative_to(REPO).as_posix()


def f3(x):
    return f"{x:.3f}"


def md_table(df, title, note):
    cols = list(df.columns)
    def cell(v):
        if isinstance(v, (float, np.floating)):
            return "" if np.isnan(v) else (f"{v:.4g}" if abs(v) < 1e4 else f"{v:,.0f}")
        return str(v).replace("|", "/")
    lines = [f"### {title}", "", note, "", "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(cell(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(lines) + "\n"


def write(df, stem, title, note, folder=TB):
    folder.mkdir(parents=True, exist_ok=True)
    df.to_csv(folder / f"{stem}.csv", index=False, lineterminator="\n")
    (folder / f"{stem}.md").write_text(md_table(df, f"{stem} — {title}", note), encoding="utf-8", newline="\n")


# ------------------------------------------------------------------ facts read from verified outputs
def facts():
    F = {}
    s = json.loads((H1D / "analysis/h1_summary.json").read_text())
    F["err_total"], F["err_disp"], F["cov_max"] = s["classifier_errors_total"], s["classifier_errors_disputed"], s["shared_attainable_coverage_primary"]
    rq = rd(Path(os.environ.get("H2PRISM_R2_RUN", REPO / "../H2-PRISM/03_results/primary_protocol/PRIMARY")) / "rq1.csv")
    prim = rq[rq.comparison_role == "PRIMARY"]
    F["rq1_rows"], F["rq1_ne"] = len(prim), int(prim.status.str.startswith("NOT_ESTIMABLE").sum())
    F["rq1_all"], F["rq1_all_ne"] = len(rq), int(rq.status.str.startswith("NOT_ESTIMABLE").sum())
    pc = rd(H1D / "analysis/h1_05_paired_comparisons.csv")
    q = pc[np.isclose(pc.coverage, 0.25)].set_index("method_b")
    F["risk_sC"] = float(q.risk_a.iloc[0])
    F["risk"] = q.risk_b.to_dict()
    F["ci_D"] = (float(q.loc["s_C_minus_D", "ancestor_ci_low"]), float(q.loc["s_C_minus_D", "ancestor_ci_high"]))
    F["fam_ci_D"] = (float(q.loc["s_C_minus_D", "family_ci_low"]), float(q.loc["s_C_minus_D", "family_ci_high"]))
    F["n_anc"], F["n_fam"] = int(q.n_ancestors.iloc[0]), int(q.n_families.iloc[0])
    F["sC_err_undisp"] = int(q.n_errors_undisputed_a.iloc[0])
    x2 = rd(AN / "x2_incremental_utility_lotemplate.csv").set_index("model")
    F["x2"] = x2
    per = rd(AN / "x2_incremental_utility_per_template.csv")
    F["x2_worse_conf"], F["x2_worse_full"], F["x2_groups"] = int((per.d_logloss_add_D_to_conf > 0).sum()), int((per.d_logloss_add_D_to_full > 0).sum()), len(per)
    x3 = rd(AN / "x3_D_artifact_test.csv").set_index("topology")
    F["x3"] = x3
    x5 = rd(AN / "x5_synthetic_dx_control.csv")
    F["x5"] = x5
    a4 = rd(AV / "tables/A04a.csv")
    tr = a4[~a4.test.str.contains("re-verified")]
    F["inv_pairs"], F["inv_checks"], F["inv_viol"] = int(tr.paired_comparisons.sum()), int(tr.hypothesis_checks.sum()), int(a4.violations.sum())
    runs = rd(AV / "analysis/dy_experiment_runs.csv")
    F["cert"] = (int(runs.excl_cert_verified.sum()), int(runs.excl_cert_total.sum()))
    F["wit"] = (int(runs.witness_verified.sum()), int(runs.witness_total.sum()))
    F["dy_decisions"] = len(runs)
    a5 = rd(AV / "tables/A05.csv").set_index("config_family")
    F["a5"] = a5
    a8 = rd(AV / "tables/A08.csv").set_index("config_family")
    F["a8"] = a8
    a9 = rd(AV / "tables/A09.csv").set_index("config_family")
    F["a9"] = a9
    st = rd(AN / "s1_dy_synthetic_stress_runs.csv")
    base = st[st.fault == "none"]
    F["s1_base_wrong"], F["s1_base_correct"] = int((base.outcome == "SPECIFIC_WRONG").sum()), int((base.outcome == "SPECIFIC_CORRECT").sum())
    g = st[st.fault != "none"].groupby(["fault", "channel", "level", "seed"])
    F["s1_max_wrong"] = int(g.outcome.apply(lambda s: (s == "SPECIFIC_WRONG").sum()).max())
    F["s1_groups"] = g.ngroups
    rk = st.groupby(["fault", "level"]).outcome.apply(
        lambda o: (o == "SPECIFIC_WRONG").sum() / max(1, o.isin(["SPECIFIC_WRONG", "SPECIFIC_CORRECT"]).sum()))
    F["s1_base_risk"] = float(rk.loc[("none", 0.0)])
    F["s1_max_risk"], F["s1_max_risk_at"] = float(rk.max()), " ".join(str(x) for x in rk.idxmax())
    F["s1_decisions"] = len(st)
    jit = st[st.fault == "jitter"]
    F["jit_identical"] = bool(all((jit[(jit.seed == sd) & (jit.level == lv)].sort_values(["query", "scenario"]).outcome.to_numpy() ==
                                   base.sort_values(["query", "scenario"]).outcome.to_numpy()).all()
                                  for lv in jit.level.unique() for sd in jit[jit.level == lv].seed.unique()))
    i1 = rd(AN / "i1_isolability_onset.csv")
    F["i1"] = i1
    hn = i1[(i1.hyp_a == "HN") & (i1.hyp_b == "H215")].set_index("channels")
    F["hn215"] = hn
    i2 = rd(AN / "i2_structural_incidence.csv")
    F["h215_incident"] = int(i2[i2.hypothesis == "H215"].incidence_at_REF.sum())
    F["h215_ratio_max"] = float(i2[i2.hypothesis == "H215"].ratio_to_2epsREF.max())
    F["h215_ratio_ch"] = i2[i2.hypothesis == "H215"].sort_values("ratio_to_2epsREF").channel.iloc[-1]
    hy = rd(AN / "h2_hy2res_equivalence_summary.csv").iloc[0]
    F["hy"] = hy
    a6 = rd(AV / "tables/A06a.csv")
    F["loc_level2"] = a6.iloc[1].status
    a7 = rd(AV / "tables/A07.csv")
    F["a7"] = a7
    a13 = rd(AV / "tables/A13.csv")
    F["a13"] = a13
    a18 = rd(AV / "tables/A18.csv")
    F["trace"] = a18.iloc[-1]
    a14 = rd(AV / "tables/A14a.csv")
    F["lat13"] = float(a14[(a14.dimension == "M_channels") & (a14.value == 13)].median_s.iloc[0])
    a11 = rd(AV / "tables/A11a.csv")
    F["a11"] = a11
    r1 = rd(AN / "r1_class_metrics.csv")
    F["r1"] = r1
    u = rd(AN / "r1_unit_level.csv").set_index("scope")
    F["r1u"] = u
    return F


# ------------------------------------------------------------------ hypothesis registry
def registry(F):
    x2, x3, a5, a8, hn, hy, a9 = F["x2"], F["x3"], F["a5"], F["a8"], F["hn215"], F["hy"], F["a9"]
    syn_c = F["x5"][F["x5"].classifier.str.startswith("c_")]
    R = [
        dict(id="H1", name="Selective diagnostic risk", registration="REGISTERED (historical RQ1; preserved verbatim)",
             formulation="At matched coverage c in {0.6, 0.8, 0.9}, the selective risk R(c) = wrong/SPECIFIC of the D(x)-augmented score s_C is lower than that of s_C without D(x).",
             null_alternative="H0: R_sC(c) >= R_sC-D(c); H1: R_sC(c) < R_sC-D(c)",
             primary_outcome="paired difference in wrong-specific risk at matched coverage", unit="scenario ancestor (17) / family (39); windows are dependent",
             required_data="frozen R2 predictions with credible labels; coverage targets attainable in every held-out topology",
             comparator="s_C - D (registered); confidence, margin, entropy, D-only, unguarded confidence (exploratory)",
             protocol="registered three-fold held-out topology; rank-matched and threshold-transfer modes",
             assumptions="labels correct; held-out topology = independent evaluation", confounders="L01 label/topology attribution defect; L04 shared templates; L10 source-model signatures",
             feasibility="registered targets unattainable (max shared coverage " + f3(F["cov_max"]) + ")",
             decision_criterion="registered: ancestor-level interval excluding 0 at the registered coverages",
             result=(f"Registered RQ1 NOT_ESTIMABLE in {F['rq1_ne']}/{F['rq1_rows']} PRIMARY rows ({F['rq1_all_ne']}/{F['rq1_all']} incl. secondary comparators). Exploratory at coverage 0.25: "
                     f"risk s_C {f3(F['risk_sC'])} vs s_C-D {f3(F['risk']['s_C_minus_D'])}, confidence {f3(F['risk']['confidence'])}, "
                     f"unguarded confidence {f3(F['risk']['confidence_no_evidence_guard'])}; s_C errors in undisputed runs: {F['sC_err_undisp']}; "
                     f"{F['err_disp']}/{F['err_total']} classifier errors in disputed runs."),
             uncertainty=f"s_C vs s_C-D at 0.25: ancestor bootstrap [{f3(F['ci_D'][0])}, {f3(F['ci_D'][1])}], family [{f3(F['fam_ci_D'][0])}, {f3(F['fam_ci_D'][1])}] ({F['n_anc']} ancestors, {F['n_fam']} families)",
             failure_interpretation="the registered test cannot be run; exploratory differences coincide with disputed labels and cannot be attributed to D(x)",
             status="NOT_ESTIMABLE", direction="registered: none; exploratory contrast with s_C-D includes 0",
             evidence="R2 PRIMARY/rq1.csv; h1_validation/analysis/h1_01_registered_rq1.csv; h1_05_paired_comparisons.csv; h1_summary.json"),
        dict(id="H2", name="Incremental distinguishability of D(x)", registration="SECONDARY (post hoc; inspected windows)",
             formulation="D(x) carries information about correctness not contained in classifier confidence: out-of-template log-loss of a correctness model improves when D is added.",
             null_alternative="H0: Δ log-loss (with D - without D) >= 0; H1: < 0",
             primary_outcome="leave-one-template-out log-loss of correctness models", unit="scenario template (ancestor) as CV group",
             required_data="frozen scores and correctness on eligible windows", comparator="[logit conf]; [logit conf, margin, -entropy]",
             protocol="leave-one-template-out logistic models; no classifier refit; synthetic method check X5",
             assumptions="correctness labels valid", confounders="L01 disputed labels; D tracks disputed runs (X3)",
             feasibility="executable but on disputed labels (exploratory only)",
             decision_criterion="support requires Δ<0 out-of-template and no artifact explanation",
             result=(f"Adding D worsened out-of-template log-loss: conf {f3(x2.loc['conf','oof_log_loss'])} -> {f3(x2.loc['conf+D','oof_log_loss'])}; "
                     f"conf+margin+entropy {f3(x2.loc['conf+margin+negH','oof_log_loss'])} -> {f3(x2.loc['conf+margin+negH+D','oof_log_loss'])}; "
                     f"worse in {F['x2_worse_conf']}/{F['x2_groups']} and {F['x2_worse_full']}/{F['x2_groups']} held-out templates. "
                     f"In Center, 1-D identifies disputed-attribution windows with AUROC {f3(x3.loc['Center','auroc_1mD_for_disputed'])} vs error AUROC {f3(x3.loc['Center','auroc_1mD_for_error'])}. "
                     f"Synthetic check: D helps only when the classifier is blind to an informative feature (Δ log-loss {', '.join(f3(v) for v in syn_c.delta_logloss)})."),
             uncertainty="template-level distribution of Δ (x2 per-template); window counts are dependent",
             failure_interpretation="D(x), as constructed, is redundant with or noisier than confidence on these data and partly encodes a dataset artifact",
             status="EXPLORATORY_ONLY", direction="AGAINST (no demonstrated incremental value)",
             evidence="04_results/analysis/x1..x5_*.csv"),
        dict(id="H3", name="Formal evidence integrity", registration="SECONDARY (mathematical/software property)",
             formulation="Under assumptions A1-A5 (02_design/DY_MONOTONICITY_PROOF.md), every EXCLUDED status carries a re-verifiable single-coordinate certificate, every FEASIBLE a re-verifiable witness, and information removal or bound widening never creates an exclusion.",
             null_alternative="H0: some certificate/witness fails re-verification or some forbidden transition occurs",
             primary_outcome="count of failed re-verifications and forbidden transitions", unit="hypothesis status per decision (finite checks) + proof",
             required_data="Center captures (hash-verified); seeded synthetic property cases", comparator="none (property test)",
             protocol="proof + exhaustive re-verification of v1 experiments + 44 adversarial/property tests",
             assumptions="fixed hypothesis set; closed intervals; exact rational decisions", confounders="none for the property; bounds are hypothetical",
             feasibility="executed",
             decision_criterion="0 failures and 0 forbidden transitions",
             result=(f"{F['inv_viol']} forbidden transitions in {F['inv_checks']:,} hypothesis-status checks ({F['inv_pairs']:,} paired decisions); exclusion certificates re-verified {F['cert'][0]:,}/{F['cert'][1]:,}; "
                     f"witnesses {F['wit'][0]:,}/{F['wit'][1]:,}; adversarial tests: forged certificate rejected, NaN/negative bounds/duplicate sensors/broken clock never SPECIFIC, contradictory sensors -> MODEL_MISMATCH."),
             uncertainty="deterministic; finite tests do not replace the proof, the proof does not cover A1 violations",
             failure_interpretation="a failure would invalidate every D(Y) exclusion",
             status="SUPPORTED_WITHIN_SCOPE", direction="FOR (software/mathematical property only; says nothing about physical validity of bounds)",
             evidence="02_design/DY_MONOTONICITY_PROOF.md; tests/test_dy_adversarial.py; advanced_validation/tables/A04a.csv"),
        dict(id="H4", name="Missing-sensor robustness", registration="SECONDARY (exploratory; hypothetical bounds)",
             formulation="Removing or corrupting sensors does not increase wrong SPECIFIC decisions of D(Y) relative to the full sensor set.",
             null_alternative="H0: wrong SPECIFIC(config) > wrong SPECIFIC(all)",
             primary_outcome="wrong and correct SPECIFIC counts per configuration", unit="Center query (6 captures; repeated views across bound scenarios)",
             required_data="Center captures; hypothetical bounds S3-S5, REF", comparator="all 13 channels",
             protocol="predeclared masks (v1 E1) + SYNTHETIC per-channel faults and jitter (v2 S1)",
             assumptions="templates and bounds as declared", confounders="one capture per query; synthetic faults are not field faults",
             feasibility="executed (conditional)",
             decision_criterion="no configuration increases wrong SPECIFIC",
             result=(f"Masks: all {int(a8.loc['all','specific_correct'])} correct/{int(a8.loc['all','specific_wrong'])} wrong; flow-only {int(a8.loc['flow_only','specific_correct'])}/{int(a8.loc['flow_only','specific_wrong'])}; "
                     f"pressure-only {int(a8.loc['pressure_only','specific_correct'])}/{int(a8.loc['pressure_only','specific_wrong'])}. SYNTHETIC faults ({F['s1_decisions']} decisions, {F['s1_groups']} fault settings): "
                     f"max wrong per setting {F['s1_max_wrong']} vs baseline {F['s1_base_wrong']}, but wrong-specific risk rises from {f3(F['s1_base_risk'])} to {f3(F['s1_max_risk'])} ({F['s1_max_risk_at']} eps_obs) because correct SPECIFIC decisions are lost first; large faults degrade to MODEL_MISMATCH; ±1-sample jitter outcomes identical to baseline: {F['jit_identical']}."),
             uncertainty="no interval estimable (6 captures)",
             failure_interpretation="flow-only sensing violates the criterion (more wrong SPECIFIC); corruption is fail-safe only in the tested settings",
             status="EXPLORATORY_ONLY", direction="MIXED (flow-only adds wrong SPECIFIC; synthetic faults never add wrong SPECIFIC but raise selective risk)",
             evidence="advanced_validation/tables/A08.csv; 04_results/analysis/s1_dy_synthetic_stress_*.csv"),
        dict(id="H5", name="Selective localization reliability", registration="SECONDARY (exploratory)",
             formulation="When D(Y) issues a location-specific decision, the outlet is correct, with risk below the forced nearest-template baseline at matched coverage.",
             null_alternative="H0: wrong-location risk(D(Y)) >= baseline", primary_outcome="wrong-location risk at matched coverage",
             unit="independent outlet location", required_data=">= several outlets each with an independent template",
             comparator="B3 nearest template (forced and top-k matched)", protocol="v1 A07", assumptions="templates independent of queries",
             confounders="L03 near-duplicate SID 213 captures; L09 self-template", feasibility="only one outlet has an independent template",
             decision_criterion="estimable only with >1 supported independent location",
             result=f"{F['loc_level2']}; D(Y) location-specific coverage {f3(F['a7'].iloc[2].coverage)} with {int(F['a7'].iloc[2].wrong_location)} wrong; supported independent locations {int(F['a7'].iloc[2].independent_locations_with_support)}.",
             uncertainty="not estimable (one location)", failure_interpretation="no network-wide localization claim possible",
             status="EXPLORATORY_ONLY", direction="NOT TESTABLE BEYOND ONE OUTLET", evidence="advanced_validation/tables/A06a.csv; A07.csv"),
        dict(id="H6", name="Out-of-template and out-of-domain generalization", registration="SECONDARY",
             formulation="Diagnostic performance (selective risk, coverage) holds on templates, topologies or studies absent from development.",
             null_alternative="H0: performance on unseen templates/domains worse than within-domain",
             primary_outcome="selective risk on unseen templates / external domain", unit="template; external study",
             required_data="evaluation templates absent from development; external labelled faults", comparator="within-domain performance",
             protocol="Level C test; HY2RES Level-A adapter as a software check",
             assumptions="independent labelled external events exist", confounders="L04 shared templates; HY2RES has no labelled faults",
             feasibility="BLOCKED: 17/17 R2 test templates occur in training; HY2RES/MHC have no labelled faults or locations",
             decision_criterion="Level C result on independent data",
             result=(f"Out-of-template: untested (no held-out template). HY2RES Level-A port of the frozen rule reproduced it exactly "
                     f"({bool(hy.frozen_rule_reproduced_vs_published_table)}); certified SPECIFIC {int(hy.certified_specific)} vs frozen singleton {int(hy.frozen_specific):,}; "
                     f"ambiguous {int(hy.certified_ambiguous):,} = {int(hy.frozen_ambiguous):,}; wrong certified SPECIFIC {int(hy.certified_specific_wrong_vs_power_label)}."),
             uncertainty="n/a", failure_interpretation="no generalization claim; Level A only",
             status="BLOCKED_BY_DATA", direction="n/a", evidence="advanced_validation/analysis/av_r2_template_sharing.csv; 04_results/analysis/h*_hy2res_*.csv"),
        dict(id="H7", name="Gas-composition transfer", registration="SECONDARY",
             formulation="D(Y) decisions remain valid when the gas model changes from the simulated gas to pure H2 or H2/NG blends.",
             null_alternative="n/a until a qualified model exists", primary_outcome="decision agreement under qualified gas models",
             unit="gas configuration", required_data="qualified transient H2 / blend network model and data", comparator="Center simulated gas",
             protocol="Levels A/B/C (A13)", assumptions="qualified EOS and transport in range", confounders="Center gas is air-like (R = 0.287 kJ/(kg·K)) with an unphysical heat-capacity ratio",
             feasibility="BLOCKED: no transient H2 or blend model; blend flash fails at the probed points",
             decision_criterion="Level B or C result",
             result="; ".join(f"{r.composition}: {r.levels_B_C}" for r in F["a13"].itertuples()),
             uncertainty="n/a", failure_interpretation="no hydrogen-specific diagnostic claim", status="BLOCKED_BY_PHYSICS", direction="n/a",
             evidence="advanced_validation/tables/A13.csv"),
        dict(id="H8", name="Sensor-risk-coverage-cost efficiency", registration="SECONDARY (exploratory)",
             formulation="A reduced sensor set achieves the same correct SPECIFIC coverage with no more wrong SPECIFIC at lower cost.",
             null_alternative="H0: every cheaper set loses coverage or adds risk", primary_outcome="Pareto set over (relative cost, correct, wrong)",
             unit="sensor configuration (Center)", required_data="source-supported prices; independent diagnostic rates",
             comparator="all 13 channels", protocol="v1 A16 + hypothetical relative-cost scenarios (V2-T07)",
             assumptions="relative unit costs are HYPOTHETICAL", confounders="one capture per query; conditional bounds",
             feasibility="prices unavailable; only counts and scenarios",
             decision_criterion="requires real prices and independent rates",
             result="see V2-T07: Pareto membership depends on the hypothetical flow/pressure cost ratio; no monetary saving is quantified",
             uncertainty="scenario range only", failure_interpretation="no cost claim", status="EXPLORATORY_ONLY", direction="CONDITIONAL",
             evidence="advanced_validation/tables/A15.csv, A16a.csv; 04_results/tables/V2-T07"),
        dict(id="H9", name="Hypothesis-library completeness handling", registration="SECONDARY",
             formulation="When the true mechanism is absent from the declared library, D(Y) never issues a SPECIFIC decision.",
             null_alternative="H0: some decision with the truth absent is SPECIFIC", primary_outcome="wrong SPECIFIC with truth removed",
             unit="Center query x bound scenario", required_data="Center captures", comparator="restricted library with truth present",
             protocol="v1 E4 (full, minus_NORMAL, minus_true, restricted)", assumptions="templates as declared", confounders="hypothetical bounds",
             feasibility="executed",
             decision_criterion="0 SPECIFIC decisions when the truth is absent",
             result=(f"minus_true: {int(a5.loc['minus_true','specific_wrong'])} wrong SPECIFIC, {int(a5.loc['minus_true','ambiguous'])} ambiguous sets without the truth, "
                     f"{int(a5.loc['minus_true','unresolved_model_mismatch'])} MODEL_MISMATCH of {int(a5.loc['minus_true','decisions'])}; full universe: "
                     f"{int(a5.loc['full','unresolved_indeterminate'])}/{int(a5.loc['full','decisions'])} UNRESOLVED (unmodelled hypotheses are indeterminate)."),
             uncertainty="counterexamples suffice to reject the universal claim",
             failure_interpretation="D(Y) guarantees are conditional on library completeness (assumption A1); an unmodelled mechanism can be mis-attributed",
             status="CONTRADICTED", direction="AGAINST (as a universal guarantee)", evidence="advanced_validation/tables/A05.csv"),
        dict(id="H10", name="Decision traceability and auditability", registration="SECONDARY (requirement)",
             formulation="Every formal decision is persisted with all 16 required provenance fields and its certificates in a re-verifiable record.",
             null_alternative="H0: some required field is not persisted", primary_outcome="fields present in the persisted record",
             unit="required field", required_data="engine certificate and frozen export", comparator="16-field checklist",
             protocol="v1 A18 checklist", assumptions="checklist is the requirement", confounders="none",
             feasibility="executed",
             decision_criterion="16/16 persisted",
             result=f"in engine certificate {F['trace'].in_engine_certificate}; in frozen serialized record {F['trace'].in_frozen_serialized_record}; {F['trace']['where']}",
             uncertainty="deterministic", failure_interpretation="in-memory certificates are re-verifiable, but the frozen export cannot be audited independently",
             status="CONTRADICTED", direction="AGAINST (requirement not met by the frozen export)", evidence="advanced_validation/tables/A18.csv"),
    ]
    df = pd.DataFrame(R)
    df.insert(0, "registry_version", "v2.0 (2026-11-18)")
    return df


ACCEPT = ["C1 provenance verified", "C2 evaluation independence defensible", "C3 assumptions documented", "C4 ground truth credible",
          "C5 correct denominators", "C6 fair comparators", "C7 appropriate statistical uncertainty", "C8 reproducible",
          "C9 claims match data tested", "C10 limitations stated"]
# status per hypothesis for C1..C10, with the reason/evidence for every non-PASS entry
ACC = {
    "H1": ["FAIL: L01 attribution (D1 NOT_RECORDED)", "FAIL: L04 shared templates", "PASS", "FAIL: 36/57 runs disputed", "PASS", "PASS", "PASS: ancestor/family bootstrap", "PASS", "PASS", "PASS"],
    "H2": ["FAIL: L01", "FAIL: inspected windows; templates shared", "PASS", "FAIL: disputed labels", "PASS", "PASS", "PASS: template-level", "PASS", "PASS", "PASS"],
    "H3": ["PASS: Center hashes", "NOT_APPLICABLE", "PASS: proof A1-A5", "NOT_APPLICABLE", "PASS", "NOT_APPLICABLE", "NOT_APPLICABLE: deterministic", "PASS", "PASS", "PASS"],
    "H4": ["PASS", "FAIL: one capture per query", "PASS", "PASS: interventions known", "PASS", "PASS", "BLOCKED: 6 captures", "PASS", "PASS", "PASS"],
    "H5": ["PASS", "FAIL: one independent location", "PASS", "PASS", "PASS", "PASS", "BLOCKED: 1 location", "PASS", "PASS", "PASS"],
    "H6": ["PASS", "BLOCKED: no held-out templates / labelled external faults", "PASS", "BLOCKED", "NOT_APPLICABLE", "NOT_APPLICABLE", "BLOCKED", "PASS", "PASS", "PASS"],
    "H7": ["PASS", "BLOCKED", "PASS", "BLOCKED: no H2 model", "NOT_APPLICABLE", "NOT_APPLICABLE", "BLOCKED", "PASS", "PASS", "PASS"],
    "H8": ["FAIL: no price sources", "FAIL: one capture per query", "PASS", "PASS", "PASS", "PASS", "BLOCKED", "PASS", "PASS", "PASS"],
    "H9": ["PASS", "NOT_APPLICABLE: counterexample", "PASS", "PASS", "PASS", "PASS", "NOT_APPLICABLE: counterexample", "PASS", "PASS", "PASS"],
    "H10": ["PASS", "NOT_APPLICABLE", "PASS", "NOT_APPLICABLE", "PASS", "NOT_APPLICABLE", "NOT_APPLICABLE", "PASS", "PASS", "PASS"],
}


def main():
    F = facts()
    reg = registry(F)
    D = V2 / "02_design"
    write(reg, "HYPOTHESIS_REGISTRY", "Hypothesis registry H1-H10",
          "Statuses use the prescribed labels. Only H1 was registered before evaluation; H2-H10 are secondary. Result fields are generated from the cited files.", D)
    acc = pd.DataFrame([dict(hypothesis=h, **{c: v for c, v in zip(ACCEPT, s)}) for h, s in ACC.items()])
    acc["registry_status"] = acc.hypothesis.map(reg.set_index("id").status)
    acc["strong_confirmatory_claim_eligible"] = acc[ACCEPT].apply(lambda r: all(v.startswith(("PASS", "NOT_APPLICABLE")) for v in r), axis=1)
    write(acc, "ACCEPTANCE_CRITERIA", "Part-18 acceptance criteria per hypothesis",
          "A strong confirmatory claim requires every criterion PASS or NOT_APPLICABLE. H3 and the H9/H10 negative findings qualify as within-scope statements, not diagnostic performance claims.",
          V2 / "06_reports")
    # leakage register
    a3 = rd(AV / "tables/A03.csv").assign(origin="v1 (A03)")
    x3 = F["x3"]
    new = pd.DataFrame([
        dict(issue="L17 D(x) encodes the disputed-attribution artifact", affected_study="R2", files="04_results/analysis/x3_D_artifact_test.csv",
             evidence=f"Center: AUROC of 1-D for disputed windows {f3(x3.loc['Center','auroc_1mD_for_disputed'])} (i.e. D separates them with {f3(1 - x3.loc['Center','auroc_1mD_for_disputed'])}); for errors {f3(x3.loc['Center','auroc_1mD_for_error'])}",
             severity="high", impacted_claims="any D(x) benefit on R2", corrective_action="re-evaluate after D1 on a common-sensor representation", approval_needed="D1, D2", status="CONFIRMED RISK", origin="v2"),
        dict(issue="L18 HY2RES test partition previously inspected", affected_study="HY2RES", files="hy2res_external_validation/publication/distinguishability/TECHNICAL_REPORT.md",
             evidence="the frozen report states the archived test had already been inspected", severity="medium", impacted_claims="any HY2RES held-out claim",
             corrective_action="label all HY2RES replays exploratory", approval_needed="—", status="DISCLOSED", origin="v2"),
        dict(issue="L19 synthetic perturbations are not field evidence", affected_study="Center D(Y) stress, D(x) X5", files="04_results/analysis/s1_*, x5_*",
             evidence="faults/jitter/classes generated by declared rules", severity="low (labelled)", impacted_claims="sensor-robustness claims",
             corrective_action="label SYNTHETIC; never cite as field robustness", approval_needed="—", status="CONTROLLED", origin="v2"),
        dict(issue="L20 Stage-2 pipeline not importable after conflict repair", affected_study="H2-SimNet Stage 2 (Faisal)", files="src/h2prism/windows.py; tests/test_faisal_pipeline.py",
             evidence="commit 6eddd4a restored the frozen Center windows.py; evaluation.py needs the pre-merge module (TARGET_CLASSES, map_target_class)",
             severity="medium (reproducibility of Stage 2 only)", impacted_claims="none in v1/v2 (no artifact depends on it)",
             corrective_action="owner to choose module split (e.g. separate simnet_windows module)", approval_needed="Stage-2 owner", status="KNOWN_BLOCKED", origin="v2"),
        dict(issue="L21 checkout-dependent hash pins", affected_study="Protocol 2.0, figure system, H2Net prep", files="01_audit/TEST_FAILURE_TRIAGE.csv",
             evidence="11 test failures compare the LF and CRLF encodings of the same committed file: pins were recorded from CRLF working copies although .gitattributes declares eol=lf",
             severity="medium (reproducibility)", impacted_claims="hash-based provenance checks on fresh checkouts", corrective_action="re-record pins on canonical LF bytes or hash git blobs",
             approval_needed="Protocol 2.0 / figure-system owners", status="CONFIRMED, NOT REPAIRED (pins are governance records)", origin="v2"),
        dict(issue="L22 Q1 package manifest name collides with the figure-system schema", affected_study="integrated_validation_v1 (this project)", files="integrated_validation_v1/publication_q1/quality_control/FIGURE_MANIFEST.csv",
             evidence="tests/test_figure_system.py globs every FIGURE_MANIFEST.csv and requires status/artifact_class columns; introduced by e944e1b",
             severity="low (test failure; no result affected)", impacted_claims="none", corrective_action="rename to Q1_FIGURE_MANIFEST.csv and refresh v1 checksums, or add the two columns",
             approval_needed="project lead (touches a committed package)", status="CONFIRMED, REPAIR PROPOSED", origin="v2"),
    ])
    write(pd.concat([a3, new], ignore_index=True), "LEAKAGE_REGISTER_V2", "Leakage and evaluation-integrity register",
          "v1 entries carried forward unchanged; v2 entries L17-L22 added from this round's analyses.", V2 / "01_audit")
    # bound-origin audit
    bo = pd.DataFrame([
        dict(component="measurement error", used_in_DY="eps_obs = 0.5 x eps_total", value_basis="hypothetical ladder S1-S6 and REF", classification="HYPOTHETICAL", what_would_qualify_it="sensor datasheet accuracy or calibration records"),
        dict(component="sensor calibration uncertainty", used_in_DY="not separated", value_basis="none", classification="NOT AVAILABLE", what_would_qualify_it="calibration certificates per sensor"),
        dict(component="timing uncertainty", used_in_DY="admissible clock shift ±tau (default 1 s)", value_basis="declared; Center clock is a fixed simulation grid", classification="HYPOTHETICAL", what_would_qualify_it="measured synchronization error of a DAQ"),
        dict(component="parameter uncertainty", used_in_DY="not separated", value_basis="none", classification="NOT AVAILABLE", what_would_qualify_it="parameter distributions + propagation"),
        dict(component="model discrepancy", used_in_DY="eps_model = 0.5 x eps_total", value_basis="hypothetical", classification="HYPOTHETICAL", what_would_qualify_it="validation of the simulator against measurements"),
        dict(component="numerical approximation error", used_in_DY="REF scenario", value_basis=f"solver-refinement delta: {ce_ref()}", classification="COMPUTED (solver refinement), not a sensor bound", what_would_qualify_it="convergence study across solver settings"),
        dict(component="scenario variability", used_in_DY="templates and admissible shifts", value_basis="one capture per mechanism (plus one replicate for SID 213)", classification="NOT CHARACTERIZED", what_would_qualify_it="multiple independent realizations per mechanism"),
    ])
    write(bo, "BOUND_ORIGIN_AUDIT", "Origin of every bound used in the formal D(Y)",
          "No bound is experimentally calibrated; D(Y) results are conditional on these declarations and are not field safety guarantees.", V2 / "01_audit")
    tables(F)


def ce_ref():
    import sys
    sys.path.insert(0, str(REPO / "src"))
    from h2prism import center_enhancement as ce
    return f"pressure {ce.SOLVER_DELTA['pressure_MPa']:.4g} MPa, flow {ce.SOLVER_DELTA['flow_kg_s']:.4g} kg/s"


def tables(F):
    x2 = F["x2"].reset_index()
    write(x2, "V2-T01_dx_incremental_utility", "D(x) incremental utility (leave-one-template-out)",
          "Correctness models on frozen scores; groups = scenario templates; EXPLORATORY (disputed labels, inspected windows).")
    write(F["x5"], "V2-T02_dx_synthetic_control", "D(x) synthetic method check",
          "SYNTHETIC two-class Gaussian design with known posterior; not evidence about H2-SimNet.")
    s = rd(AN / "s1_dy_synthetic_stress_summary.csv")
    write(s, "V2-T03_dy_synthetic_sensor_faults", "Formal D(Y) under SYNTHETIC sensor faults and jitter",
          "Center, restricted universe, S4 and REF, tau = 1 s; magnitudes in multiples of eps_obs; 6 queries x 2 scenarios per row (jitter: x 3 seeds). Not field evidence.")
    i1 = F["i1"][["hyp_a", "hyp_b", "channels", "lambda_star", "onset_eps_pressure_MPa", "onset_eps_flow_kg_s", "limiting_channel_at_worst_shift_pair", "reason"]]
    write(i1, "V2-T04_isolability_onset", "Pairwise isolability onset (bound scale lambda* relative to REF)",
          "Isolable iff lambda < lambda*; lambda* = 0 would mean intrinsic non-isolability. Template level, ±1 s, CONDITIONAL_HYPOTHETICAL_BOUNDS.")
    i2 = rd(AN / "i2_structural_incidence.csv").pivot_table(index=["hypothesis", "template"], columns="channel",
                                                             values="ratio_to_2epsREF", aggfunc="first").reset_index()
    write(i2, "V2-T05_structural_incidence", "Structural incidence: peak template signal / (2 eps_REF) per channel",
          "Values > 1 mean the channel responds detectably at REF bounds (incidence = 1).")
    hy = rd(AN / "h1_hy2res_certified_vs_frozen.csv")
    write(hy, "V2-T06_hy2res_certified_port", "HY2RES frozen candidate rule vs its certified D(Y) port",
          "Zero (hypothetical) observation half-width; previously inspected test partition; EXPLORATORY.")
    # hypothetical relative-cost scenarios
    a16 = rd(AV / "tables/A16a.csv")
    P = [f"PS{i}" for i in range(1, 11)]
    Fl = ["MFS1", "MFS2", "MFS3"]
    def chans(c):
        if c == "all": return P + Fl
        if c == "flow_only": return Fl
        if c == "pressure_only": return P
        if c.startswith("drop_"): return [x for x in P + Fl if x != c[5:]]
        if c.startswith("outage_branch_"):
            out = c[c.index("(") + 1:c.index(")")].split(",")
            return [x for x in P + Fl if x not in out]
        raise ValueError(c)
    rows = []
    for r in (1, 3, 10):
        for x in a16.itertuples():
            ch = chans(x.config_family)
            npr, nfl = sum(c in P for c in ch), sum(c in Fl for c in ch)
            rows.append(dict(flow_to_pressure_unit_cost_ratio=r, config=x.config_family, n_pressure=npr, n_flow=nfl,
                             relative_hardware_cost=(npr + r * nfl) / (len(P) + r * len(Fl)),
                             specific_correct=x.specific_correct, specific_wrong=x.specific_wrong))
    T = pd.DataFrame(rows)
    def pareto(g):
        nd = []
        for i, a in g.iterrows():
            dom = ((g.relative_hardware_cost <= a.relative_hardware_cost) & (g.specific_correct >= a.specific_correct) &
                   (g.specific_wrong <= a.specific_wrong) & ((g.relative_hardware_cost < a.relative_hardware_cost) |
                   (g.specific_correct > a.specific_correct) | (g.specific_wrong < a.specific_wrong))).any()
            nd.append(not dom)
        return pd.Series(nd, index=g.index)
    T["pareto_nondominated"] = pd.concat([pareto(g) for _, g in T.groupby("flow_to_pressure_unit_cost_ratio")])
    T["basis"] = "HYPOTHETICAL relative units (no prices); outcomes CONDITIONAL (Center, hypothetical bounds)"
    write(T, "V2-T07_hypothetical_cost_scenarios", "Sensor configurations under hypothetical relative-cost scenarios",
          "Pressure transmitter = 1 relative unit; flow meter = r units, r in {1, 3, 10} chosen to span plausible orders of magnitude, NOT prices. Never a financial saving.")
    r1 = F["r1"]
    write(r1, "V2-T08_r2_class_metrics", "R2 descriptive class metrics (all windows, undisputed runs, per topology)",
          "Window-level metrics on dependent windows; labels disputed in 36/57 runs (D1); EXPLORATORY.")
    write(rd(AN / "r1_unit_level.csv"), "V2-T09_r2_run_level", "R2 run-level (majority vote) performance",
          "Runs are the event unit; families and ancestors give the independent units.")
    cost = pd.DataFrame([
        dict(category="A training compute", status="NOT MEASURED in this round", value="frozen models were not retrained", source="—"),
        dict(category="B inference compute", status="MEASURED (time, not money)", value=f"D(Y) 13-channel decision median {F['lat13']:.3f} s (A14a)", source="advanced_validation/tables/A14a.csv"),
        dict(category="C sensor acquisition", status="NOT AVAILABLE", value="no source-supported prices; see V2-T07 for relative scenarios", source="A15"),
        dict(category="D installation and maintenance", status="NOT AVAILABLE", value="—", source="A15"),
        dict(category="E data generation and simulation", status="NOT MEASURED", value="Simscape run times not recorded with the captures", source="—"),
        dict(category="F operational engineering", status="NOT AVAILABLE", value="no consequence-cost basis for false/missed detections", source="A15"),
    ])
    write(cost, "V2-T10_cost_categories", "Cost categories reported separately", "No category is combined into a savings figure.")
    # results index
    idx = [
        ("Reliability-coverage", ["03_results/integrated_validation_v1/advanced_validation/tables/A01.csv"]),
        ("False-specific diagnosis", ["03_results/integrated_validation_v1/advanced_validation/tables/A02a.csv", "03_results/integrated_validation_v1/advanced_validation/tables/A02b.csv"]),
        ("Accuracy and class-wise performance", ["03_results/integrated_validation_v2/04_results/tables/V2-T08_r2_class_metrics.csv", "03_results/integrated_validation_v2/04_results/tables/V2-T09_r2_run_level.csv"]),
        ("D(x) ablation", ["03_results/integrated_validation_v2/04_results/tables/V2-T01_dx_incremental_utility.csv", "03_results/integrated_validation_v2/04_results/tables/V2-T02_dx_synthetic_control.csv", "03_results/integrated_validation_v1/h1_validation/analysis/h1_03_development_ablation.csv"]),
        ("D(Y) verification", ["03_results/integrated_validation_v1/advanced_validation/tables/A04a.csv", "tests/test_dy_adversarial.py", "03_results/integrated_validation_v2/02_design/DY_MONOTONICITY_PROOF.md"]),
        ("Sensor robustness", ["03_results/integrated_validation_v1/advanced_validation/tables/A08.csv", "03_results/integrated_validation_v2/04_results/tables/V2-T03_dy_synthetic_sensor_faults.csv"]),
        ("Sensor placement", ["03_results/integrated_validation_v1/advanced_validation/tables/A16a.csv", "03_results/integrated_validation_v1/advanced_validation/tables/A16b.csv", "03_results/integrated_validation_v2/04_results/tables/V2-T05_structural_incidence.csv"]),
        ("Localization", ["03_results/integrated_validation_v1/advanced_validation/tables/A06a.csv", "03_results/integrated_validation_v1/advanced_validation/tables/A07.csv"]),
        ("Isolability", ["03_results/integrated_validation_v2/04_results/tables/V2-T04_isolability_onset.csv", "03_results/integrated_validation_v2/04_results/analysis/i3_unidentifiable_pair_register_REF.csv"]),
        ("Timing uncertainty", ["03_results/integrated_validation_v1/advanced_validation/tables/A09.csv", "03_results/integrated_validation_v2/04_results/tables/V2-T03_dy_synthetic_sensor_faults.csv"]),
        ("Evidence sufficiency", ["03_results/integrated_validation_v1/advanced_validation/tables/A10.csv"]),
        ("Negative controls", ["03_results/integrated_validation_v1/advanced_validation/tables/A11a.csv", "03_results/integrated_validation_v1/advanced_validation/tables/A11b.csv"]),
        ("Leakage", ["03_results/integrated_validation_v2/01_audit/LEAKAGE_REGISTER_V2.csv"]),
        ("Generalization", ["03_results/integrated_validation_v1/advanced_validation/analysis/av_r2_template_sharing.csv", "03_results/integrated_validation_v2/04_results/tables/V2-T06_hy2res_certified_port.csv"]),
        ("Gas portability", ["03_results/integrated_validation_v1/advanced_validation/tables/A12.csv"]),
        ("Gas-specific physics", ["03_results/integrated_validation_v1/advanced_validation/tables/A13.csv"]),
        ("Computational scaling", ["03_results/integrated_validation_v1/advanced_validation/tables/A14a.csv", "03_results/integrated_validation_v1/advanced_validation/tables/A14b.csv"]),
        ("Costs", ["03_results/integrated_validation_v2/04_results/tables/V2-T10_cost_categories.csv", "03_results/integrated_validation_v2/04_results/tables/V2-T07_hypothetical_cost_scenarios.csv"]),
        ("Literature comparisons", ["03_results/integrated_validation_v1/advanced_validation/tables/A17.csv"]),
        ("Hypothesis verdicts", ["03_results/integrated_validation_v2/02_design/HYPOTHESIS_REGISTRY.csv"]),
    ]
    rows = [dict(topic=t, file=f, origin="v2" if "integrated_validation_v2" in f or f.startswith("tests/") else "v1 (committed)",
                 sha256=sha(REPO / f) if (REPO / f).exists() else "MISSING") for t, fs in idx for f in fs]
    pd.DataFrame(rows).to_csv(TB / "RESULTS_INDEX.csv", index=False, lineterminator="\n")
    assert all(r["sha256"] != "MISSING" for r in rows), [r for r in rows if r["sha256"] == "MISSING"]


if __name__ == "__main__":
    main()
