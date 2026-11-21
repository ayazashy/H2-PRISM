"""08 - FigureGuild asset index for candidate figures and tables (read-only).

Dimensions come from 01_COMPLETE_FIGURE_INVENTORY.csv / 02_COMPLETE_TABLE_INVENTORY.csv. Provisional roles and
priorities are reviewer judgements recorded in CANDIDATES (justified in 04/05 and 07). Legibility estimate: Q1-style
figures (v1 Q1/H1/AV, v2) use 10 pt tick labels at 400 dpi (~55.6 px em on a 3840 px canvas). Rendered at width W px
of the 840 x 600 Results area, the label em is 55.6 * W / png_width; reported in px and as % of the 600 px height.
"""
from pathlib import Path

import pandas as pd

INV = Path(__file__).resolve().parents[1]
CANVAS_W, CANVAS_H = 840, 600
EM_400DPI_10PT = 10 / 72 * 400
Q1_STYLE = ("Q1", "H1", "AV", "V2")

# asset_id: (priority, provisional_role, candidate stage(s), note)
CANDIDATES = {
    "Q1_C15": ("A", "large dominant / half-width", "D(Y) decision semantics", "three abstention situations: frozen, full universe, restricted"),
    "Q1_C14": ("A", "half-width", "D(Y) decision behaviour", "decision grid by query x bound scenario; wrong SPECIFIC visible"),
    "AV-F05": ("A", "compact supporting", "formal integrity", "monotonicity transition matrix; 0 forbidden transitions"),
    "AV-F04": ("A", "half-width", "library completeness (limitation)", "removing the true hypothesis -> wrong SPECIFIC"),
    "V2-F03": ("A", "half-width / full-width", "isolability", "lambda* onset; Normal vs SID 215 bound-limited"),
    "V2-F04": ("B", "half-width", "isolability / sensors", "incidence: SID 215 below 2 eps_REF on every channel"),
    "AV-F07": ("B", "half-width", "isolability / sensors", "pairwise separability matrices by sensor set (not accuracy)"),
    "Q1_C01": ("B", "half-width", "observability", "each outlet excites a different sensor group; SID 215 flow-blind"),
    "AV-F08": ("A", "half-width", "sensor robustness", "masks: flow-only doubles wrong SPECIFIC; MFS3 loss -> ambiguity"),
    "V2-F02": ("B", "half-width", "sensor robustness (SYNTHETIC)", "faults never add wrong decisions but raise selective risk"),
    "AV-F09": ("B", "half-width", "timing", "delay beyond clock bound -> abstention; wrong decisions persist"),
    "AV-F13": ("B", "compact supporting", "engineering trade-off", "sensor count vs decision quality (no prices)"),
    "AV-F12": ("B", "compact supporting / half-width", "computation", "measured runtime scaling, ~0.36 s per 13-channel decision"),
    "H1-F01": ("A", "half-width", "registered H1", "registered coverage targets unattainable -> NOT_ESTIMABLE"),
    "H1-F02a": ("B", "half-width", "exploratory selective risk", "risk vs coverage inside shared region (exploratory)"),
    "H1-F02b": ("B", "half-width", "exploratory selective risk", "paired differences; s_C - s_C-D intervals include 0"),
    "AV-F02": ("A", "half-width", "label-defect attribution", "wrong SPECIFIC split by disputed vs consistent attribution"),
    "V2-F01": ("A", "half-width", "D(x) incremental value (negative)", "adding D worsens out-of-template log-loss; synthetic check"),
    "Q1_I05": ("B", "half-width", "R2 classification by topology", "confusion by held-out topology; errors in two topologies"),
    "Q1_I06": ("B", "compact supporting", "independence units", "thousands of windows, few independent templates"),
    "Q1_I08": ("C", "half-width", "registered three-outcome policy", "0/11,198 wrong SPECIFIC at 0.60 - Center excluded; qualify"),
    "AV-F11": ("C", "compact supporting", "negative control", "false LEAK calls on NORMAL windows; one NORMAL template"),
    "V2-F05": ("B", "half-width", "cross-domain portability", "HY2RES rule through engine: no singleton survives certification"),
    "Q1_H10": ("C", "compact supporting", "abstention cause (HY2RES)", "unresolved decisions = out-of-support tank pressure"),
    "Q1_H11": ("C", "compact supporting", "abstention cause (HY2RES)", "abstention tracks out-of-support fraction over time"),
    "Q1_I02": ("C", "compact supporting", "reference prediction context", "Ridge advantage is a fraction of one recorded step"),
    "Q1_I07": ("C", "compact supporting", "D(Y) qualification across studies", "inputs for formal D(Y) available only on Center"),
    "AV-F14": ("B", "compact supporting", "gas qualification", "no diagnostic transfer for any gas"),
    "V2-F06": ("B", "half-width / full-width", "evidence synthesis", "acceptance criteria x hypotheses; only H3 fully supported"),
    "Q1_I09": ("C", "half-width", "evidence synthesis", "claim-to-evidence matrix by study"),
    "AV-F16": ("C", "half-width", "evidence synthesis", "claims vs evidence level (v1); partly superseded by V2-F06"),
    "Q1_I01": ("C", "full-width schematic", "context / architecture", "evidence architecture schematic (not a result)"),
    "Q1_C07": ("C", "compact supporting", "mechanism recognition", "recognition does not survive self-template removal"),
    "Q1_C13b": ("C", "half-width (dense)", "exclusion thresholds", "flow-only exclusion onsets vs REF"),
}
TABLES = {
    "V2_validation:HYPOTHESIS_REGISTRY": None,
    "AV_advanced:A04a": ("A", "compact table", "formal integrity", "5 x 5; all PASS, 0 violations"),
    "AV_advanced:A05": ("B", "compact table (subset)", "library completeness", "4 variants; select 6 columns"),
    "Q1_tables:T07b_dy_decision_reasons": ("A", "compact table", "D(Y) decision semantics", "4 x 4"),
    "H1_validation:H1-T02": ("B", "compact table", "registered H1", "matched-coverage feasibility, 4 rows"),
    "V2_validation:V2-T01_dx_incremental_utility": ("A", "compact table", "D(x) negative result", "4 models"),
    "V2_validation:V2-T09_r2_run_level": ("B", "compact table", "label-defect attribution", "3 rows"),
    "V2_validation:V2-T06_hy2res_certified_port": ("B", "compact table", "portability", "7 rows"),
    "AV_advanced:A14b": ("B", "compact table", "computation", "6 scaling exponents"),
    "AV_advanced:A16b": ("B", "compact table", "sensor placement", "minimum sensor sets, 4 scenarios"),
    "AV_advanced:A13": ("C", "compact table", "gas qualification", "4 compositions"),
    "Q1_tables:T09b_rq3_three_outcome": ("C", "compact table", "registered RQ3", "4 classes"),
    "V2_validation:V2-T10_cost_categories": ("C", "compact table", "cost", "6 categories; no prices"),
}


def main():
    F = pd.read_csv(INV / "01_COMPLETE_FIGURE_INVENTORY.csv").set_index("asset_id")
    rows = []
    for aid, (pri, role, stage, note) in CANDIDATES.items():
        r = F.loc[aid]
        w = r.png_width_px
        est = r.man_package in Q1_STYLE
        em = lambda width: round(EM_400DPI_10PT * width / w, 1) if est and w == w else None
        rows.append(dict(asset_id=aid, kind="figure", priority=pri, provisional_role=role, candidate_stage=stage, note=note,
                         title=r.title, png=r.png, svg=r.svg, pdf=r.pdf, formats=r.formats, png_px=f"{int(w)}x{int(r.png_height_px)}",
                         aspect_w_over_h=r.aspect_w_over_h, canvas_aspect=round(CANVAS_W / CANVAS_H, 3),
                         height_at_full_width_px=round(CANVAS_W / r.aspect_w_over_h), height_at_half_width_px=round(410 / r.aspect_w_over_h),
                         tick_em_px_full_width=em(CANVAS_W), tick_em_px_half_width=em(410), tick_em_px_third_width=em(270),
                         tick_em_pct_of_area_height_half=(round(100 * em(410) / CANVAS_H, 2) if em(410) else None),
                         background="#FFFFFF (Q1 style; differs from poster #F4F4E9)" if est else "see inventory",
                         font="Times New Roman (live SVG text)" if est else "see inventory",
                         lifecycle=r.lifecycle, evidence_status=r.evidence_status))
    T = pd.read_csv(INV / "02_COMPLETE_TABLE_INVENTORY.csv").set_index("table_id")
    for tid, v in TABLES.items():
        if tid not in T.index:
            continue
        pri, role, stage, note = v or ("A", "compact table (subset)", "hypothesis verdicts", "10 hypotheses; show id, name, status only")
        t = T.loc[tid]
        rows.append(dict(asset_id=tid, kind="table", priority=pri, provisional_role=role, candidate_stage=stage, note=note,
                         title=t.title, png=None, svg=None, pdf=None, formats="CSV/MD", png_px=f"{t.rows:g} rows x {t.columns:g} cols",
                         csv=t.csv, md=t.md, lifecycle=t.lifecycle, evidence_status=t.evidence_status))
    out = pd.DataFrame(rows)
    out.to_csv(INV / "08_FIGUREGUILD_ASSET_INDEX.csv", index=False, lineterminator="\n")
    print(out[["asset_id", "priority", "png_px", "aspect_w_over_h", "tick_em_px_half_width"]].to_string())


if __name__ == "__main__":
    main()
