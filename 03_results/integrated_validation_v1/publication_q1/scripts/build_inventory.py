"""Inventory every tracked historical PNG/SVG figure and map it to its Q1 replacement.

Reads only: ``git ls-files`` and the image bytes. Historical figures are never modified.
Writes quality_control/FIGURE_INVENTORY.csv and .md.
Usage (repository root): python <this script>
"""
import hashlib
import re
import subprocess
from pathlib import Path

import pandas as pd
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
ROOT = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[4]

# family prefix -> (study, family label, eligibility default, generic defect)
FAMILIES = [
    ("03_results/ILLUSTRATIVE_DEMO_NOT_RESULTS/", "none", "Illustrative demo", "INELIGIBLE",
     "Invented illustrative values; not results"),
    ("03_results/figures/primary/", "R2 primary protocol", "R2 primary-protocol figures", "ELIGIBLE",
     "Superseded run variants co-exist; mixed preliminary/final status"),
    ("03_results/figures/dataset_design/", "R2 primary protocol", "R2 dataset design", "ELIGIBLE",
     "Superseded/unapproved variant co-exists"),
    ("03_results/figures/fig", "Stage-2 archive", "Stage-2 working figures", "SUPERSEDED",
     "Stage-2 pipeline outputs superseded by R2 primary protocol"),
    ("03_results/validation/publication_final_v1/poster/", "Center", "Center poster renders", "SUPERSEDED",
     "Poster duplicates of publication figures"),
    ("03_results/validation/publication_final_v1/figures/", "Center", "Center publication atlas", "ELIGIBLE",
     "Multi-panel layouts; text rendered as paths"),
    ("03_results/validation/center_evidence_enhancement/", "Center", "Center evidence enhancement", "ELIGIBLE",
     "#F4F4E9 background; sans-serif fonts; footnotes inside the canvas"),
    ("03_results/validation/final_research/", "Center", "Center final-research working figures", "SUPERSEDED",
     "Working figures superseded by the enhancement analysis"),
    ("03_results/validation/phase1", "Center", "Center phase working figures", "RETAINED_HISTORICAL",
     "Engineering verification figures (solver/convergence); not Results evidence"),
    ("study_b/evidence_enhancement/", "MHC", "MHC evidence enhancement", "ELIGIBLE",
     "#F4F4E9 background; sans-serif fonts; footnotes inside the canvas"),
    ("study_b/figures/", "MHC", "MHC original figures", "ELIGIBLE", "Multi-panel layouts"),
    ("03_results/hy2res_external_validation/evidence_enhancement/", "HY2RES", "HY2RES evidence enhancement", "ELIGIBLE",
     "#F4F4E9 background; sans-serif fonts; footnotes inside the canvas"),
    ("03_results/hy2res_external_validation/publication/distinguishability/", "HY2RES", "HY2RES distinguishability",
     "ELIGIBLE", "DejaVu Sans; multi-panel"),
    ("03_results/hy2res_external_validation/publication/", "HY2RES", "HY2RES publication", "ELIGIBLE",
     "DejaVu Sans; multi-panel"),
    ("03_results/hy2res_external_validation/figures/", "HY2RES", "HY2RES first-pass figures", "SUPERSEDED",
     "Superseded by the HY2RES publication package"),
]

# stem -> (scientific question, source data, units, Q1 replacement IDs)
STEMS = {
    "fig3_confusion_matrix": ("(demo) confusion matrix", "invented", "-", ""),
    "fig4_risk_coverage_curve": ("(demo) risk-coverage", "invented", "-", ""),
    "fig5_calibration_reliability": ("(demo) calibration", "invented", "-", ""),
    "fig6_distinguishability_separation": ("(demo) separation", "invented", "-", ""),
    "fig1_dataset_and_design": ("How is the R2 dataset partitioned?", "03_results/primary_protocol", "counts", "Q1_I01"),
    "fig2_rq1_risk_coverage": ("RQ1: risk versus coverage by topology", "primary_protocol/*/coverage_risk.csv", "fraction", "Q1_I09;Q1_I10"),
    "fig3_rq1_incremental_value": ("RQ1: incremental value of distinguishability", "primary_protocol/*/rq1.csv", "risk difference", "Q1_I09"),
    "fig4_rq2_three_outcome": ("RQ2/RQ3: SPECIFIC/AMBIGUOUS/UNRESOLVED shares", "primary_protocol/*/rq2.csv", "fraction", "Q1_I12"),
    "fig5_error_structure": ("Where do R2 errors occur?", "primary_protocol/*/confusion_matrix.csv", "counts", "Q1_I13"),
    "fig6_robustness": ("Protocol 2.0 arm robustness", "ablation/ARM_SUMMARY.csv", "accuracy", "Q1_I11"),
    "fig1_family_distribution": ("Stage-2 family counts", "stage-2 pipeline", "counts", ""),
    "fig2_pipeline_telemetry": ("Stage-2 pipeline telemetry", "stage-2 pipeline", "counts", ""),
    "fig3_confusion_matrix_stage2": ("Stage-2 confusion", "stage-2 pipeline", "counts", "Q1_I13"),
    "fig4_risk_coverage_stage2": ("Stage-2 risk-coverage", "stage-2 pipeline", "fraction", "Q1_I09"),
    "fig5_calibration_reliability_stage2": ("Stage-2 calibration", "stage-2 pipeline", "fraction", ""),
    "fig6_distinguishability_stage2": ("Stage-2 distinguishability", "stage-2 pipeline", "-", ""),
    "FIG_01_controlled_response": ("How does a controlled withdrawal appear in PS1 and MFS3?", "Center captures (alternate profile)", "MPa; kg/s", "Q1_C02"),
    "FIG_02_timing_alignment": ("How does a one-second command shift appear?", "Center captures (timing pair); TAB_06", "MPa", "Q1_C03"),
    "FIG_03_archive_ml": ("Does archive ML recall exceed a constant rule?", "publication_final_v1/tables/TAB_03.csv", "recall", "Q1_C04"),
    "FIG_04_detection": ("Detection delay versus false-alarm burden", "TAB_04.csv", "s; episodes/h", "Q1_C05"),
    "FIG_05_robustness": ("Detector behaviour under hypothetical sensor stresses", "TAB_05.csv", "duty; s", "Q1_C06"),
    "FIG_06_location_geometry": ("Location contrasts by sensor group", "TAB_07.csv", "normalized RMS", "Q1_C10;Q1_C11"),
    "FIG_07_mechanism_evidence": ("Mechanism ranking under references/ablations", "TAB_08-10.csv", "normalized RMS", "Q1_C07;Q1_C08"),
    "FIG_08_formal_decisions": ("Formal decision outcomes", "TAB_13.csv", "counts", "Q1_C15"),
    "FIG_C01_intervention_observability": ("Which outlet can each sensor observe?", "center enhancement channel_signal.csv", "-", "Q1_C01"),
    "FIG_C02_mechanism_recognition_loto": ("Does recognition survive self-template removal?", "recognition.json; TAB_C02", "counts", "Q1_C07;Q1_I04"),
    "FIG_C03_mechanism_ranking_evidence": ("How close are competing mechanisms?", "recognition.json", "normalized RMS", "Q1_C08"),
    "FIG_C04_location_ranking": ("Can the configured outlet be ranked?", "location.json; TAB_C04", "rank", "Q1_C09;Q1_I05"),
    "FIG_C05_sensor_group_location_sensitivity": ("Which sensor group carries location separation?", "pair_contrasts.csv", "ratio", "Q1_C10;Q1_I06"),
    "FIG_C06_pressure_vs_flow_contrast": ("Where does information lie in native units?", "channel_signal.csv", "MPa; kg/s", "Q1_C11"),
    "FIG_C07_conditional_exclusion_map": ("Which rivals are excluded under declared bounds?", "dy_decisions.json", "status", "Q1_C12a;Q1_C12b;Q1_C12c"),
    "FIG_C08_exclusion_thresholds": ("What precision separates hypotheses?", "dy_thresholds.csv", "MPa; kg/s", "Q1_C13a;Q1_C13b"),
    "FIG_C09_decision_transitions_restricted": ("How do decisions change with assumptions?", "dy_decisions.json", "decision", "Q1_C14;Q1_I08"),
    "FIG_C10_evidence_breakdown": ("Why did D(Y) abstain?", "dy_decisions.json; TAB_C07", "counts", "Q1_C15;Q1_I07"),
    "FIG_C11_capability_map": ("What is established for Center?", "TAB_C08", "evidence level", "Q1_I14"),
    "formal_decisions": ("Formal decisions (working)", "final_research", "counts", "Q1_C15"),
    "observed_signature_matrix": ("Observed signatures (working)", "final_research", "normalized RMS", "Q1_C11"),
    "rival_responses": ("Rival responses (working)", "final_research", "MPa", "Q1_C08"),
    "subset_separability": ("Subset separability (working)", "final_research", "normalized RMS", "Q1_C10"),
    "shared_knot_discrepancies": ("Solver verification: shared-knot discrepancy", "phase10", "MPa", ""),
    "convergence_mass": ("Solver verification: mass convergence", "phase11", "kg", ""),
    "pressure_step": ("Solver verification: pressure step", "phase11", "MPa", ""),
    "baseline_mass": ("Solver verification: baseline mass", "phase11", "kg", ""),
    "conservation": ("Paired-run conservation check", "phase12", "kg", ""),
    "mfs_comparison": ("Paired-run MFS comparison", "phase12", "kg/s", "Q1_C02"),
    "outlet_response": ("Paired-run outlet response", "phase12", "kg/s", "Q1_C02"),
    "ps_comparison": ("Paired-run PS comparison", "phase12", "MPa", "Q1_C02"),
    "FIG_B01_measurement_context": ("Which MHC channels are predicted?", "MHC source notes", "-", "Q1_B01"),
    "FIG_B02_P2_prediction_traces": ("How do P-2 predictions track data?", "replayed_predictions.csv.gz", "bar", "Q1_B02"),
    "FIG_B02_MFC3_prediction_traces": ("How do MFC-3 predictions track data?", "replayed_predictions.csv.gz", "NL/min", "Q1_B03"),
    "FIG_B03_P2_per_run_performance": ("Is the P-2 ranking stable across runs?", "run_metrics.csv", "bar", "Q1_B04"),
    "FIG_B03_MFC3_per_run_performance": ("Is the MFC-3 ranking stable across runs?", "run_metrics.csv", "NL/min", "Q1_B05"),
    "FIG_B04_P2_error_ecdf": ("P-2 central versus tail errors", "replayed_predictions.csv.gz", "bar", "Q1_B06"),
    "FIG_B04_MFC3_error_ecdf": ("MFC-3 central versus tail errors", "replayed_predictions.csv.gz", "NL/min", "Q1_B07"),
    "FIG_B05_P2_error_concentration": ("Do rare P-2 errors dominate RMSE?", "concentration_curves.csv", "fraction", "Q1_B08"),
    "FIG_B05_MFC3_error_concentration": ("Do rare MFC-3 errors dominate RMSE?", "concentration_curves.csv", "fraction", "Q1_B08"),
    "FIG_B06_P2_error_vs_change": ("Where does Ridge gain/lose on P-2?", "error_vs_change.csv", "bar", "Q1_B09"),
    "FIG_B06_MFC3_error_vs_change": ("Where does Ridge gain/lose on MFC-3?", "error_vs_change.csv", "NL/min", "Q1_B10"),
    "FIG_B07_resolution_vs_error": ("Are differences physically resolvable?", "resolution.csv", "recording increments", "Q1_B11;Q1_I03"),
    "FIG_B08_MFC3_control_role": ("Is MFC-3 a controlled release?", "controller_role.csv", "NL/min", "Q1_B12"),
    "FIG_B09_evidence_matrix": ("What does MHC support?", "TAB_B08", "evidence level", "Q1_I14"),
    "figure_1_design": ("MHC study design", "study_b protocol", "-", "Q1_B01"),
    "figure_2_responses": ("MHC response traces", "MHC replay", "bar; NL/min", "Q1_B02;Q1_B03"),
    "figure_3_performance": ("MHC benchmark metrics", "study_b results", "bar; NL/min", "Q1_B04;Q1_B05;Q1_I02"),
    "FIG_H01_pressure_quantization": ("What is the pressure recording grid?", "recording_grid.csv", "bar", "Q1_H05"),
    "FIG_H02_error_in_increments": ("How large are errors relative to the grid?", "quantization_comparison.csv", "increments", "Q1_H06;Q1_I03"),
    "FIG_H03_error_tradeoff": ("Why does RMSE improve while MAE worsens?", "step_contribution.csv", "bar^2", "Q1_H07"),
    "FIG_H04_tank_pressure_drift": ("How does tank pressure drift?", "chronology.csv; development_bounds.csv", "bar", "Q1_H08"),
    "FIG_H05_support_violations": ("Which channels breach support?", "support_attribution.csv", "rows", "Q1_H09"),
    "FIG_H06_unresolved_mechanisms": ("Why so many abstentions?", "unresolved_taxonomy.csv", "rows", "Q1_H10"),
    "FIG_H07_decision_validity_over_time": ("Does abstention follow the breach over time?", "time_bins.csv", "fraction", "Q1_H11"),
    "FIG_H08_state_decision_matrix": ("Which states get which outcome?", "state_outcomes.csv", "rows", "Q1_H12"),
    "FIG_H09_positive_flow_distinguishability": ("Does separation survive without zero flow?", "distinguishability.csv", "probability", "Q1_H13"),
    "FIG_H10_evidence_matrix": ("What does HY2RES support?", "TAB_H09", "evidence level", "Q1_I14"),
    "FIG_01_MEASUREMENT_ARCHITECTURE": ("Which HY2RES channels exist?", "CHANNEL_SCHEMA.csv", "-", "Q1_H01"),
    "FIG_02_CAUSAL_VALIDITY": ("How is the record segmented and partitioned?", "segment_registry.csv; validity_mask", "rows", "Q1_H02"),
    "FIG_03_HELD_OUT_TRACES": ("How do references track held-out pressure?", "test_predictions.csv.gz (segment 2382)", "bar", "Q1_H03"),
    "FIG_04_ERROR_COMPARISON": ("State-dependent reference error", "TABLE_2_HELD_OUT.csv", "bar; NL/h", "Q1_H04;Q1_I02"),
    "FIG_05_OPERATING_STATE": ("Operating-state outcomes", "state_outcomes", "rows", "Q1_H12"),
    "FIG_06_EVIDENCE_QUALIFICATION": ("HY2RES evidence qualification", "publication tables", "evidence level", "Q1_I07;Q1_I14"),
    "FIG_07_EXPLORATORY_STATE_OVERLAP": ("Exploratory state overlap", "distinguishability", "probability", "Q1_H13"),
    "FIG_01_STATE_SIGNATURES": ("State signatures", "distinguishability", "bar; NL/h", "Q1_H13"),
    "FIG_02_EMPIRICAL_DECISIONS": ("Empirical state decisions", "distinguishability", "rows", "Q1_H12"),
    "CONTACT_SHEET": ("Contact sheet (collage)", "publication figures", "-", ""),
    "F1_hy2res_operational_timeline": ("Operational timeline", "HY2RES", "bar", "Q1_H02"),
    "F2_hy2res_test_reference_traces": ("Test reference traces", "HY2RES", "bar", "Q1_H03"),
    "F3_hy2res_error_coverage_regimes": ("Error and coverage by regime", "HY2RES", "bar", "Q1_H04"),
    "F3_review_error_tradeoffs": ("Error trade-offs (review)", "HY2RES", "bar", "Q1_H07"),
}


# Final replacement IDs (the figure set as built; supersedes the planning IDs above).
FINAL = {
    "fig1_dataset_and_design": "Q1_I06", "fig2_rq1_risk_coverage": "H1-F01;H1-F02a", "fig3_rq1_incremental_value": "H1-F02b",
    "fig4_rq2_three_outcome": "Q1_I08", "fig5_error_structure": "Q1_I05", "fig6_robustness": "H1-F04a",
    "fig3_confusion_matrix_stage2": "Q1_I05", "fig4_risk_coverage_stage2": "H1-F02a",
    "FIG_C02_mechanism_recognition_loto": "Q1_C07;Q1_I04", "FIG_C04_location_ranking": "Q1_C09",
    "FIG_C05_sensor_group_location_sensitivity": "Q1_C10", "FIG_C07_conditional_exclusion_map": "Q1_C12a;Q1_C12b;Q1_C12c;Q1_C12d",
    "FIG_C09_decision_transitions_restricted": "Q1_C14;H1-F06", "FIG_C10_evidence_breakdown": "Q1_C15",
    "FIG_C11_capability_map": "Q1_I09", "FIG_B01_measurement_context": "Q1_B01",
    "FIG_B02_P2_prediction_traces": "Q1_B03", "FIG_B02_MFC3_prediction_traces": "Q1_B04",
    "FIG_B03_P2_per_run_performance": "Q1_B05", "FIG_B03_MFC3_per_run_performance": "Q1_B06",
    "FIG_B04_P2_error_ecdf": "Q1_B07", "FIG_B04_MFC3_error_ecdf": "Q1_B08", "FIG_B05_P2_error_concentration": "Q1_B09",
    "FIG_B05_MFC3_error_concentration": "Q1_B09", "FIG_B06_P2_error_vs_change": "Q1_B10", "FIG_B06_MFC3_error_vs_change": "Q1_B11",
    "FIG_B07_resolution_vs_error": "Q1_B12;Q1_I02;Q1_I03", "FIG_B08_MFC3_control_role": "Q1_B13", "FIG_B09_evidence_matrix": "Q1_I09",
    "figure_1_design": "Q1_B01;Q1_B02", "figure_2_responses": "Q1_B03;Q1_B04", "figure_3_performance": "Q1_B05;Q1_B06;Q1_I02",
    "FIG_H01_pressure_quantization": "Q1_H06", "FIG_H02_error_in_increments": "Q1_H07;Q1_I02", "FIG_H03_error_tradeoff": "Q1_H08",
    "FIG_H04_tank_pressure_drift": "Q1_H09", "FIG_H05_support_violations": "Q1_H14", "FIG_H06_unresolved_mechanisms": "Q1_H10",
    "FIG_H07_decision_validity_over_time": "Q1_H11", "FIG_H08_state_decision_matrix": "Q1_H12",
    "FIG_H09_positive_flow_distinguishability": "Q1_H13", "FIG_H10_evidence_matrix": "Q1_I09",
    "FIG_01_MEASUREMENT_ARCHITECTURE": "Q1_H01", "FIG_02_CAUSAL_VALIDITY": "Q1_H02", "FIG_03_HELD_OUT_TRACES": "Q1_H03;Q1_H04",
    "FIG_04_ERROR_COMPARISON": "Q1_H05;Q1_I02", "FIG_05_OPERATING_STATE": "Q1_H12", "FIG_06_EVIDENCE_QUALIFICATION": "Q1_I07;Q1_I09",
    "FIG_07_EXPLORATORY_STATE_OVERLAP": "Q1_H13", "FIG_01_STATE_SIGNATURES": "Q1_H13", "FIG_02_EMPIRICAL_DECISIONS": "Q1_H12",
    "F1_hy2res_operational_timeline": "Q1_H02", "F2_hy2res_test_reference_traces": "Q1_H03", "F3_hy2res_error_coverage_regimes": "Q1_H05",
    "F3_review_error_tradeoffs": "Q1_H08",
}


def classify(path):
    for prefix, study, fam, elig, defect in FAMILIES:
        if path.startswith(prefix):
            return study, fam, elig, defect
    return "unknown", "unknown", "REVIEW", ""


def inspect(path):
    p = REPO / path
    out = {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "width_px": "", "height_px": "",
           "dpi": "", "corner_rgb": "", "svg_fonts": ""}
    if path.endswith(".png"):
        with Image.open(p) as im:
            out["width_px"], out["height_px"] = im.size
            d = im.info.get("dpi")
            out["dpi"] = round(d[0]) if d else ""
            px = im.convert("RGB").getpixel((2, 2))
            out["corner_rgb"] = "#%02X%02X%02X" % px
    else:
        txt = p.read_text(encoding="utf-8", errors="replace")
        fams = sorted(set(re.findall(r"font-family[:=]\s*\"?([^;\"]+)", txt)))
        out["svg_fonts"] = " | ".join(f.strip() for f in fams) if fams else "text as paths"
    return out


def main():
    files = subprocess.run(["git", "ls-files", "*.png", "*.svg"], cwd=REPO, capture_output=True,
                           text=True, check=True).stdout.split()
    rows = []
    for f in sorted(files):
        study, fam, elig, defect = classify(f)
        stem = Path(f).stem
        q, src, units, repl = STEMS.get(stem, ("", "", "", ""))
        repl = FINAL.get(stem, repl)
        if study == "MHC":  # MHC native units are barg and ln/min
            units = units.replace("NL/min", "ln/min").replace("bar;", "barg;")
            units = "barg" if units == "bar" else units
        info = inspect(f)
        defects = [defect] if defect else []
        if info["corner_rgb"] and info["corner_rgb"] != "#FFFFFF":
            defects.append(f"non-white background {info['corner_rgb']}")
        if info["width_px"] and max(info["width_px"], info["height_px"]) < 3200:
            defects.append("long side < 3200 px")
        if stem == "CONTACT_SHEET":
            elig_f = "SUPERSEDED"
            defects.append("collage of figures; not a standalone scientific figure")
        elif "primary/" in f and "b200fcdac" not in f:
            elig_f = "SUPERSEDED"
            defects.append("superseded run key (current run: a10530f1fcf2_s4228b6c8_b200fcdac)")
        else:
            elig_f = elig
        if "/preliminary/" in f and elig_f == "ELIGIBLE":
            defects.append("preliminary render")
        dup = "duplicate render of the same figure" if "/poster/" in f or "superseded_unapproved" in f else ""
        rows.append({"path": f, "format": f.rsplit(".", 1)[1].upper(), "study": study, "family": fam,
                     "scientific_question": q, "source_data": src, "units": units,
                     "eligibility": elig_f, "q1_replacement": repl if elig_f != "INELIGIBLE" else "",
                     "action": {"ELIGIBLE": "REDESIGNED", "SUPERSEDED": "RETAINED_UNCHANGED_SUPERSEDED",
                                "RETAINED_HISTORICAL": "RETAINED_UNCHANGED",
                                "INELIGIBLE": "EXCLUDED_NOT_RESULTS"}.get(elig_f, "REVIEW"),
                     "duplication": dup, "known_defects": "; ".join(defects), **info})
    df = pd.DataFrame(rows)
    qc = ROOT / "quality_control"
    qc.mkdir(parents=True, exist_ok=True)
    df.to_csv(qc / "FIGURE_INVENTORY.csv", index=False, lineterminator="\n")
    lines = ["# Historical figure inventory", "",
             f"{len(df)} tracked PNG/SVG files inspected. Historical files are left unchanged; this table records "
             "the scientific question, source, defects and the Q1 replacement for each.", "",
             "## Summary by family", "", "| Study | Family | Files | Eligibility | Action |", "|---|---|---|---|---|"]
    g = df.groupby(["study", "family", "eligibility", "action"]).size().reset_index(name="n")
    for r in g.itertuples():
        lines.append(f"| {r.study} | {r.family} | {r.n} | {r.eligibility} | {r.action} |")
    lines += ["", "## Files", "", "| File | Question | Source | Defects | Replacement |", "|---|---|---|---|---|"]
    for r in df.itertuples():
        lines.append(f"| `{r.path}` | {r.scientific_question} | {r.source_data} | {r.known_defects} | {r.q1_replacement} |")
    (qc / "FIGURE_INVENTORY.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(df.groupby(["eligibility"]).size().to_string())


if __name__ == "__main__":
    main()
