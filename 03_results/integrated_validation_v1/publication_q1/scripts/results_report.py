"""Assemble the integrated Results chapter, figure index and table index from the generated artifacts.

Numbers enter the text only through the generated figure captions and tables (themselves computed from
verified sources), so the chapter cannot drift from the data.
Usage (repository root): python 03_results/integrated_validation_v1/publication_q1/scripts/results_report.py
"""
import re
from pathlib import Path

import pandas as pd

Q1 = Path(__file__).resolve().parents[1]
ROOT = Q1.parent
H1 = ROOT / "h1_validation"

SECTIONS = [
    ("1. Evidence architecture", None,
     "How do the four evidence sources contribute to the three evidence layers?",
     "All accepted study packages and the registered R2 run.", "Qualification review; no pooling across studies.",
     "—", "Each study contributes to different layers; only Center reaches Layer III, and only conditionally.",
     "Evidence levels differ by study; the matrix is a qualification summary, not a measurement.",
     ["Q1_I01"], ["T01_source_qualification"]),
    ("2.1 Center — observability and controlled response", "Center",
     "Which sensors observe a controlled withdrawal, and how large are the responses?",
     "Hash-verified Center captures; channel_signal.csv.", "Intervention − matched control differences in native units.",
     "Matched control run of the same capture pair.",
     "Each outlet excites a different sensor group; SID 215 is visible only in pressure. Responses are flow-dominated.",
     "One controlled simulation family with an air-like gas model.",
     ["Q1_C01", "Q1_C02", "Q1_C03"], []),
    ("2.2 Center — archive benchmark, detection and sensor stress", "Center",
     "What do the historical event-window benchmark and detection replays show?",
     "publication_final_v1 TAB_03–TAB_05.", "Re-plot of frozen tables.", "Constant 'LEAK' rule; majority and always-event rules.",
     "Recall cannot show discrimination because all held-out scenarios are LEAK; detectors trade missed events for false alarms; only noise stresses change detector behaviour.",
     "Archive replay of simulated scenarios; hypothetical perturbations.", ["Q1_C04", "Q1_C05", "Q1_C06"], []),
    ("2.3 Center — mechanism recognition", "Center",
     "Does mechanism recognition survive removal of the query's own template?",
     "TAB_C02, TAB_C07.", "Nearest B3 template with and without self-templates (LOTO).", "Frozen library with self-templates.",
     "Recognition is largely a self-match: 3/5 supported queries agree without self-templates, with near-tie margins.",
     "Seven queries, one source family.", ["Q1_C07", "Q1_C08", "Q1_I04"], ["T05_center_mechanism_recognition"]),
    ("2.4 Center — categorical localization and sensor dependence", "Center",
     "Can the configured outlet be ranked, and which sensors carry the separation?",
     "TAB_C03, pair_contrasts.csv.", "Categorical rank among candidate outlets; contrasts by sensor group.", "Leave-own-template-out.",
     "Only the outlet with an independent replicate (SID 213) is ranked first; separation is carried by branch flow, and SID 215 is flow-blind.",
     "Two supported queries for one outlet; no localization distance or accuracy.",
     ["Q1_C09", "Q1_C10", "Q1_C11"], ["T06a_center_location_ranking", "T06b_center_sensor_dependence"]),
    ("2.5 Center — formal D(Y) under conditional hypothetical bounds", "Center",
     "Which hypotheses does formal D(Y) exclude, at what precision, and how do decisions depend on the declared universe?",
     "dy_decisions.json, TAB_C05, TAB_C06.", "Closed-form exclusion and feasibility onsets; engine decisions per bound scenario.",
     "Full declared universe vs restricted (modelled) universe.",
     "The full universe never decides; the restricted universe decides and is wrong whenever the true mechanism is unmodelled.",
     "Conditional hypothetical bounds — not calibrated uncertainty; repeated views of six captures.",
     ["Q1_C12a", "Q1_C12b", "Q1_C12c", "Q1_C12d", "Q1_C13a", "Q1_C13b", "Q1_C14", "Q1_C15"],
     ["T07a_dy_conditional_decisions", "T07b_dy_decision_reasons"]),
    ("3.1 MHC — measurement context and partition", "MHC",
     "Which channels and runs are evaluated?", "MHC v1.2 workbooks (TAB_B01).", "Eligibility from the frozen Study B protocol.", "—",
     "Eight dual-stage runs are eligible; three are held out.", "One apparatus.", ["Q1_B01", "Q1_B02"], []),
    ("3.2 MHC — reference prediction", "MHC",
     "Is the learned Ridge reference better than persistence on held-out runs?",
     "Bit-identical frozen replay.", "MAE and RMSE per run and pooled; units never combined.", "Persistence (previous value).",
     "Persistence wins MAE in every run; Ridge's RMSE gains are tiny and not consistent for MFC-3.",
     "Three held-out runs; serially dependent rows.",
     ["Q1_B03", "Q1_B04", "Q1_B05", "Q1_B06"], ["T02_prediction_benchmark"]),
    ("3.3 MHC — error structure", "MHC",
     "Why do MAE and RMSE rank the references differently?", "Replayed predictions; error tables.",
     "Error ECDF, concentration curves, error by observed change.", "Persistence.",
     "Persistence is exact on most rows; RMSE is decided by rare large steps that both references miss alike.",
     "Change bins use the outcome (retrospective).", ["Q1_B07", "Q1_B08", "Q1_B09", "Q1_B10", "Q1_B11"], []),
    ("3.4 MHC — recording resolution and controller role", "MHC",
     "Are differences resolvable on the recording grid, and how must MFC-3 be interpreted?",
     "resolution.csv, controller_role.csv.", "Errors in recording increments; P-2 conditioned on MFC-3 flow.", "One recording increment.",
     "Differences are at most about one recorded step; MFC-3 behaves as a controlled back-pressure release.",
     "Increment is recorded quantization, not instrument accuracy; set point not recorded.",
     ["Q1_B12", "Q1_B13"], ["T03_error_resolution"]),
    ("4.1 HY2RES — measurement architecture and causal segmentation", "HY2RES",
     "What does the record contain, and how is causal prediction ensured?", "CHANNEL_SCHEMA, segment registry, chronology.",
     "Published definitions; chronological partition with embargo; same-segment lag-1 inputs.", "—",
     "Three targets; no development segment is shared with the test period.", "Timezone unspecified.", ["Q1_H01", "Q1_H02"], []),
    ("4.2 HY2RES — reference prediction", "HY2RES",
     "How do the references follow held-out pressure and flow, and does this depend on the operating state?",
     "Frozen test predictions; TABLE_2_HELD_OUT.", "Trace display; per-state relative error change.", "Persistence.",
     "Pressures move on a 0.1 bar grid; Ridge's relative advantage depends on target and state and reverses for flow in the minority state.",
     "One system, one test period.", ["Q1_H03", "Q1_H04", "Q1_H05"], []),
    ("4.3 HY2RES — quantization and error trade-off", "HY2RES",
     "How large are the errors relative to the recording grid, and why does RMSE favour Ridge?",
     "quantization_comparison, step_contribution.", "Errors in increments; ΔSSE by recorded step class.", "Persistence.",
     "All pressure differences are below 0.1 of a recorded step; Ridge partly anticipates single-step transitions.",
     "Increment ≠ instrument accuracy.", ["Q1_H06", "Q1_H07", "Q1_H08"], []),
    ("4.4 HY2RES — drift and operating support", "HY2RES",
     "Does the test period stay inside the development support?", "chronology, support_attribution.",
     "Per-partition distributions; channel-level support violations.", "Development min–max.",
     "Tank pressure drifts above the development maximum; it is the only channel that breaches support.",
     "Physical cause of the drift not established.", ["Q1_H09", "Q1_H14"], []),
    ("4.5 HY2RES — abstention and evidence validity", "HY2RES",
     "Why does the frozen state rule abstain, and does abstention follow the breach over time?",
     "unresolved_taxonomy, time_bins.", "Exclusive reason reconstruction; 6 h bins.", "—",
     "Abstention is almost entirely out-of-support tank pressure, distinct from ambiguity and invalid input.",
     "Descriptive association.", ["Q1_H10", "Q1_H11"], ["T04a_operating_support_unresolved"]),
    ("4.6 HY2RES — operating-state recognition", "HY2RES",
     "Does the rule recognise the minority operating state, and do the channels separate the states?",
     "state_outcomes, distinguishability.", "Outcome counts per state; empirical rank probabilities.", "Constant majority rule.",
     "Zero specific calls on the minority state; separation is zero versus positive flow, not state recognition.",
     "Power-defined states, not fault labels.", ["Q1_H12", "Q1_H13"], ["T04b_operating_state_outcomes"]),
    ("5. Cross-study comparison", None,
     "What do the studies jointly show about references, measurement grids and classification evidence?",
     "MHC, HY2RES and R2 tables.", "Errors in recording increments; R2 confusion and independence units.", "Persistence; registered classifier.",
     "Learned references gain at most a fraction of one recorded step; R2 classification errors concentrate in the topologies affected by the attribution defect and rest on 17 scenario templates.",
     "Studies are not pooled.", ["Q1_I02", "Q1_I03", "Q1_I05", "Q1_I06", "Q1_I07"], []),
    ("6.1 RQ1 / H1 — incremental decision value of distinguishability", None,
     "At matched coverage, does the distinguishability assessment reduce selective risk?",
     "Registered R2; H1 analysis (h1_validation).", "Registered SAP; exploratory shared-coverage reanalysis.", "s_C−D; conventional confidence.",
     "Registered verdict NOT_ESTIMABLE; exploratory contrast inconclusive; see H1_RESULTS.md for the full analysis.",
     "All windows inspected; attribution defect; 17 ancestors.", ["H1-F01", "H1-F02a", "H1-F02b", "H1-F03"],
     ["T08a_rq1_registered", "T08b_rq1_exploratory_shared_coverage"]),
    ("6.2 RQ2 — information beyond confidence", None,
     "Does D(x) add decision-relevant information beyond confidence, margin and entropy?",
     "Protocol 2.0 development ablation; R2 score rankings.", "Group-balanced risk at the development-fixed operating point; AUROC.",
     "Confidence, margin, −entropy.", "No incremental value of D(x) where estimable.", "Development-only, exploratory.",
     ["H1-F04a", "H1-F04b"], ["T09a_rq2_ablation"]),
    ("6.3 RQ3 — validity of specific, ambiguous and unresolved decisions", None,
     "Are the three outcomes valid and informative?", "R2 registered decisions; Center D(Y).",
     "Per-class outcome shares; error destination; universe dependence.", "Conventional confidence abstention.",
     "No wrong SPECIFIC where evaluable; ambiguity sets contain the truth; D(Y) false specificity arises only from incomplete libraries.",
     "Thin classes; conditional bounds.", ["Q1_I08", "H1-F05", "H1-F06"], ["T09b_rq3_three_outcome"]),
    ("7. Claim-to-evidence qualification", None,
     "What is established, and at which evidence level?", "T10 (all claim tables).", "Qualification in the project vocabulary.", "—",
     "Reference prediction is validated within scope; diagnostic, localization and transfer claims are blocked by evidence.",
     "Qualification, not new measurement.", ["Q1_I09", "H1-F07"], ["T10_claim_evidence"]),
]


def caption(fid):
    for d in (Q1 / "captions", H1 / "captions"):
        for f in d.glob(f"{fid}_*.md"):
            t = f.read_text(encoding="utf-8")
            m = re.search(r"\*\*Caption\.\*\* (.*?)\n\n", t, re.S)
            ttl = t.splitlines()[0].split("— ", 1)[1]
            fig = ("figures" if d.parent == Q1 else "../h1_validation/figures") + f"/{f.stem}.png"
            capl = ("captions" if d.parent == Q1 else "../h1_validation/captions") + f"/{f.name}"
            return f"![{fid}]({fig})\n\n*{fid} — {ttl}.* {m.group(1)} ([caption]({capl}))\n"
    raise FileNotFoundError(fid)


def table(stem):
    return (Q1 / "tables" / f"{stem}.md").read_text(encoding="utf-8").replace("### ", "#### ")


def main():
    out = ["# H₂-PRISM integrated validation — Results\n",
           "Structure of every subsection: question → evidence → method → result → comparator → interpretation → "
           "limitation. Numbers appear in the figure captions and tables, which are generated from verified sources. "
           "H1 is analysed in depth in `../h1_validation/H1_RESULTS.md`.\n"]
    for head, _, q, ev, me, comp, interp, lim, figs, tabs in SECTIONS:
        out.append(f"## {head}\n")
        out.append(f"- **Question.** {q}\n- **Evidence.** {ev}\n- **Method.** {me}\n- **Comparator.** {comp}\n")
        out.append("**Results.**\n")
        out += [caption(f) for f in figs]
        out += [table(t) for t in tabs]
        out.append(f"**Interpretation.** {interp}\n\n**Limitation.** {lim}\n")
    (Q1 / "INTEGRATED_RESULTS.md").write_text("\n".join(out), encoding="utf-8", newline="\n")
    # figure index from both manifests
    m = pd.concat([pd.read_csv(Q1 / "quality_control/Q1_FIGURE_MANIFEST.csv"),
                   pd.read_csv(H1 / "quality_control/H1_FIGURE_MANIFEST.csv")], ignore_index=True)
    lines = ["# Figure index\n", f"{len(m)} standalone figures (PNG + SVG + caption + plotting function).\n",
             "| ID | Study | Title | Question | PNG | QA |", "|---|---|---|---|---|---|"]
    for r in m.itertuples():
        lines.append(f"| {r.figure_id} | {r.study} | {r.title} | {r.scientific_question} | `{r.png}` | {r.qa_status} |")
    (Q1 / "FIGURE_INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    tl = ["# Table index\n", "| Table | File (CSV) | Title |", "|---|---|---|"]
    for f in sorted((Q1 / "tables").glob("T[0-9]*.md")):
        tl.append(f"| {f.stem.split('_')[0]} | `tables/{f.stem}.csv` | {f.read_text(encoding='utf-8').splitlines()[0].split('— ', 1)[1]} |")
    for f in sorted((H1 / "tables").glob("H1-T*.md")):
        tl.append(f"| {f.stem} | `../h1_validation/tables/{f.stem}.csv` | {f.read_text(encoding='utf-8').splitlines()[0].split('— ', 1)[1]} |")
    tl.append("| TS01 | `tables/TS01_center_dy_status_matrix.csv` | Full Center D(Y) status matrix (every query × hypothesis × scenario × universe × group × clock) |")
    tl.append("| TS02 | `tables/TS02_center_dy_id_map.csv` | Compact query / hypothesis identifiers |")
    (Q1 / "TABLE_INDEX.md").write_text("\n".join(tl) + "\n", encoding="utf-8", newline="\n")
    print("figures indexed:", len(m))


if __name__ == "__main__":
    main()
