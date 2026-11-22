"""Build the logical figure and table inventories from the raw discovery files and the repository's own records.

Figures: files sharing folder + stem form one logical figure (PNG/SVG/PDF variants). Findings and limitations are quoted
from the repository's caption files (Q1/H1/AV/V2 captions/*.md, *.caption.md, the Center ATLAS.md, figure-system
manifest captions) - never retyped. Package-level context (experiment, data, hypothesis, default evidence status) comes
from PACKAGES below; lifecycle status from manifests, PUBLICATION_MANIFEST and the v1 historical FIGURE_INVENTORY.
Writes 01_COMPLETE_FIGURE_INVENTORY.csv and 02_COMPLETE_TABLE_INVENTORY.csv. Read-only with respect to all sources.
"""
import re
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
INV = REPO / "03_results/poster_inventory"
D = INV / "data"

# prefix -> (gallery_group, experiment/study, data source, hypothesis/RQ, default evidence status, default limitation)
PACKAGES = [
    ("03_results/integrated_validation_v2/", "V2_validation", "integrated_validation_v2 (this project)",
     "R2 frozen predictions; Center captures; HY2RES CSV; synthetic designs", "H2/H4/H5/H6/H9/H10", "EXPLORATORY / SYNTHETIC / CONDITIONAL",
     "see figure caption; registry 02_design/HYPOTHESIS_REGISTRY.csv"),
    ("03_results/integrated_validation_v1/advanced_validation/", "AV_advanced", "integrated_validation_v1 advanced validation",
     "R2 frozen run; Center captures (hypothetical bounds)", "H1-H10 (v1 numbering)", "EXPLORATORY / CONDITIONAL", ""),
    ("03_results/integrated_validation_v1/h1_validation/", "H1_validation", "integrated_validation_v1 H1 validation",
     "R2 frozen run a10530f1 (predictions, decisions)", "H1 / RQ1", "EXPLORATORY_POST_HOC (registered RQ1 NOT_ESTIMABLE)", ""),
    ("03_results/integrated_validation_v1/publication_q1/figures/Q1_C", "Q1_Center", "Q1 redesign of Center studies",
     "12 Center captures, one air-like source family", "RQ3 / mechanism, location, D(Y)", "DESCRIPTIVE / CONDITIONAL", ""),
    ("03_results/integrated_validation_v1/publication_q1/figures/Q1_B", "Q1_MHC", "Q1 redesign of MHC Study B",
     "MHC Zenodo release; 3 held-out runs", "reference prediction (not diagnosis)", "DESCRIPTIVE", ""),
    ("03_results/integrated_validation_v1/publication_q1/figures/Q1_H", "Q1_HY2RES", "Q1 redesign of HY2RES Study C",
     "HY2RES pilot CSV; previously inspected test", "reference prediction; operating state", "DESCRIPTIVE", ""),
    ("03_results/integrated_validation_v1/publication_q1/figures/Q1_I", "Q1_Integrated", "Q1 integrated cross-study figures",
     "R2, Center, MHC, HY2RES", "cross-study synthesis", "DESCRIPTIVE / SCHEMATIC", ""),
    ("03_results/figures/primary/a10530f1fcf2_s4228b6c8_b200fcdac/final", "R2_figsys_final", "R2 registered run, figure system (approved final)",
     "R2 PRIMARY run a10530f1", "RQ1/RQ2", "DESCRIPTIVE (approved for publication)", ""),
    ("03_results/figures/primary/", "R2_figsys_other", "R2 registered run, figure system (preliminary/superseded runs)",
     "R2 runs", "RQ1/RQ2", "DESCRIPTIVE", ""),
    ("03_results/figures/dataset_design/", "R2_dataset_design", "H2-SimNet dataset design", "dataset audit tables", "design", "SCHEMATIC/DESCRIPTIVE", ""),
    ("03_results/figures/fig", "Stage2_pipeline", "Stage-2 pipeline (Faisal), superseded by R2", "Stage-2 outputs", "RQ1/RQ2 (pre-registration)", "SUPERSEDED", ""),
    ("03_results/ILLUSTRATIVE_DEMO_NOT_RESULTS/", "Illustrative_demo", "illustrative demo", "invented values", "none", "NOT_RESULTS", "invented values"),
    ("03_results/validation/publication_final_v1/poster", "Center_atlas_poster", "Center atlas poster exports", "Center captures; archive replay", "Center", "DESCRIPTIVE", ""),
    ("03_results/validation/publication_final_v1/", "Center_atlas", "Center publication atlas (frozen baseline)", "Center captures; archive replay", "Center", "DESCRIPTIVE", ""),
    ("03_results/validation/center_evidence_enhancement/", "Center_enhancement", "Center evidence enhancement", "Center captures", "RQ3 / D(Y)", "DESCRIPTIVE / CONDITIONAL", ""),
    ("03_results/validation/final_research/", "Center_working", "Center working figures", "Center captures", "Center", "SUPERSEDED", ""),
    ("03_results/validation/phase", "Engineering_verification", "Center solver/convergence verification", "Center captures", "simulation verification", "ENGINEERING_VERIFICATION", "not Results evidence"),
    ("03_results/hy2res_external_validation/publication/distinguishability", "HY2RES_distinguishability", "HY2RES state distinguishability", "HY2RES CSV", "operating state", "EXPLORATORY", ""),
    ("03_results/hy2res_external_validation/publication/", "HY2RES_publication", "HY2RES Study C publication", "HY2RES CSV", "reference prediction", "DESCRIPTIVE", ""),
    ("03_results/hy2res_external_validation/evidence_enhancement/", "HY2RES_enhancement", "HY2RES evidence enhancement", "HY2RES CSV", "reference prediction; abstention", "DESCRIPTIVE", ""),
    ("03_results/hy2res_external_validation/figures/", "HY2RES_early", "HY2RES early figures", "HY2RES CSV", "reference prediction", "SUPERSEDED", ""),
    ("study_b/evidence_enhancement/", "MHC_enhancement", "MHC Study B evidence enhancement", "MHC release", "reference prediction", "DESCRIPTIVE", ""),
    ("study_b/figures/", "MHC_original", "MHC Study B original figures", "MHC release", "reference prediction", "DESCRIPTIVE", ""),
    ("03_results/tables/primary/a10530f1fcf2_s4228b6c8_b200fcdac/final", "R2_tables_final", "R2 registered run tables (approved final)",
     "R2 PRIMARY run a10530f1", "RQ1/RQ2", "DESCRIPTIVE (approved for publication)", ""),
    ("03_results/tables/", "R2_tables_other", "R2 run tables (preliminary/superseded/dataset design)", "R2 runs", "RQ1/RQ2", "DESCRIPTIVE", ""),
    ("study_b/tables", "MHC_original", "MHC Study B original tables", "MHC release", "reference prediction", "DESCRIPTIVE", ""),
    ("03_results/integrated_validation_v1/publication_q1/", "Q1_tables", "Q1 integrated publication tables",
     "R2, Center, MHC, HY2RES", "cross-study", "DESCRIPTIVE", ""),
    ("03_results/", "Other_results", "other result folders", "", "", "RECORDED", ""),
    ("assets/", "Planning_documents", "project planning PDFs", "none", "none", "NOT_RESULTS", "planning documents, not results"),
]


def pkg(path):
    for row in PACKAGES:
        if path.startswith(row[0]):
            return row
    return ("", "Other", "unclassified", "", "", "UNKNOWN", "")


def caption_text(path):
    """Return (caption, limitation) quoted from the figure's caption source."""
    if not isinstance(path, str) or not path:
        return "", ""
    p = REPO / path
    if not p.exists():
        return "", ""
    t = p.read_text(encoding="utf-8", errors="replace")
    cap = re.search(r"\*\*Caption\.\*\*\s*(.+)", t)
    lim = re.search(r"\*\*Interpretation limit\.\*\*\s*(.+)", t)
    if cap:
        return cap.group(1).strip(), (lim.group(1).strip() if lim else "")
    body = " ".join(l.strip() for l in t.splitlines() if l.strip() and not l.startswith("#"))
    return body[:900], ""


def atlas_captions():
    t = (REPO / "03_results/validation/publication_final_v1/ATLAS.md").read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r"## (FIG_\d+_\w+) — ([^\n]+)\n\n([^\n]+)", t):
        out[m.group(1)] = (m.group(2), m.group(3))
    return out


def lifecycle(r):
    if r.group == "Illustrative_demo":
        return "OBSOLETE (invented values)"
    if r.group == "Planning_documents":
        return "NOT_RESULTS"
    if isinstance(r.man_qa, str) and r.man_package in ("Q1", "H1", "AV", "V2"):
        return "FINAL (curated package, QA " + r.man_qa + ")"
    if r.in_pub:
        return "FINAL (R2 PUBLICATION_MANIFEST, approved)"
    a = r.v1_action
    if a == "RETAINED_UNCHANGED_SUPERSEDED":
        return "SUPERSEDED"
    if a == "REDESIGNED":
        return "SUPERSEDED_BY_REDESIGN (original retained)"
    if a == "RETAINED_UNCHANGED":
        return "RETAINED (engineering verification)"
    if "preliminary" in r.folder:
        return "PRELIMINARY"
    if "superseded" in r.folder:
        return "SUPERSEDED"
    return "UNCATALOGUED (no manifest or inventory entry)"


def main():
    raw = pd.read_csv(D / "figure_files_raw.csv")
    atlas = atlas_captions()
    rows = []
    for (folder, stem), g in raw.groupby(["folder", "stem"], sort=True):
        by = {r.format: r for r in g.itertuples()}
        png, svg, pdf = by.get("PNG"), by.get("SVG"), by.get("PDF")
        ref = png or svg or pdf
        man = next((r for r in g.itertuples() if isinstance(r.man_package, str)), None)
        inv = next((r for r in g.itertuples() if isinstance(r.v1inv_action, str)), None)
        prefix, group, experiment, data, hyp, evid, deflim = pkg(ref.path)
        cap_src = man.man_caption if man is not None else ""
        if not cap_src:
            for c in (f"{folder}/{stem}.caption.md",):
                if (REPO / c).exists():
                    cap_src = c
        caption, limitation = caption_text(cap_src) if cap_src and str(cap_src).endswith(".md") else (str(cap_src or ""), "")
        if not caption and stem in atlas:
            caption = atlas[stem][1]
        title = (man.man_title if man is not None else "") or (atlas.get(stem, ("",))[0]) or (inv.v1inv_scientific_question if inv is not None else "") or stem
        asset = man.man_figure_id if man is not None and isinstance(man.man_figure_id, str) else f"{group}:{stem}"
        rows.append(dict(
            asset_id=asset, gallery_group=group, title=title, folder=folder, stem=stem,
            formats="/".join(sorted(by)), png=png.path if png else None, svg=svg.path if svg else None, pdf=pdf.path if pdf else None,
            png_width_px=png.width if png else None, png_height_px=png.height if png else None, png_dpi=png.dpi if png else None,
            aspect_w_over_h=ref.aspect_w_over_h, vector_size=(f"{svg.width:g}x{svg.height:g} {svg.size_unit}" if svg is not None and svg.width == svg.width and svg.width else ""),
            svg_live_text_elements=svg.svg_text_elements if svg else None, svg_embeds_raster=svg.svg_embeds_raster if svg else None,
            experiment=experiment, source_data=(man.man_sources if man is not None and isinstance(man.man_sources, str) else data),
            hypothesis_or_rq=hyp, scientific_question=(man.man_question if man is not None and isinstance(man.man_question, str) else
                                                        (inv.v1inv_scientific_question if inv is not None else "")),
            finding_quoted_from_caption=caption, limitation_quoted=limitation or (inv.v1inv_known_defects if inv is not None else deflim),
            evidence_status=evid, man_package=man.man_package if man is not None else "", man_qa=man.man_qa_status if man is not None else None,
            in_pub=bool(g.in_publication_manifest.any()), v1_action=inv.v1inv_action if inv is not None else None,
            superior_version=(inv.v1inv_q1_replacement if inv is not None and isinstance(inv.v1inv_q1_replacement, str) else ""),
            duplication_note=(inv.v1inv_duplication if inv is not None and isinstance(inv.v1inv_duplication, str) else ""),
            caption_source=cap_src or ("ATLAS.md" if stem in atlas else ""), png_sha256=png.sha256 if png else None))
    F = pd.DataFrame(rows)
    F["lifecycle"] = [lifecycle(r) for r in F.rename(columns={"man_qa": "man_qa"}).assign(group=F.gallery_group).itertuples()]
    F["verification"] = F.apply(lambda r: "hash recorded in package manifest; QA " + str(r.man_qa) if r.man_package else
                                ("approved, hash in PUBLICATION_MANIFEST" if r.in_pub else
                                 ("hash recorded in v1 FIGURE_INVENTORY" if isinstance(r.v1_action, str) else "no recorded provenance")), axis=1)
    F.to_csv(INV / "01_COMPLETE_FIGURE_INVENTORY.csv", index=False, lineterminator="\n")
    print(len(F), "logical figures"); print(F.lifecycle.value_counts().to_string()); print(F.gallery_group.value_counts().to_string())

    # ---------------- tables: merge CSV/MD twins of publication tables and analysis outputs ----------------
    T = pd.read_csv(D / "table_files_raw.csv")
    T = T[T.role.isin(["PUBLICATION_TABLE", "ANALYSIS_OUTPUT", "REGISTER_OR_AUDIT"])].copy()
    T["stem"] = T.path.str.replace(r"\.(csv|md|tsv)$", "", regex=True)
    trows = []
    for stem, g in T.groupby("stem"):
        csv = g[g.format == "CSV"]
        md = g[g.format == "MD"]
        base = csv.iloc[0] if len(csv) else md.iloc[0]
        prefix, group, experiment, data, hyp, evid, deflim = pkg(base.path)
        title = ""
        if len(md):
            first = (REPO / md.iloc[0].path).read_text(encoding="utf-8", errors="replace").splitlines()
            title = next((l.lstrip("# ").strip() for l in first if l.startswith("#")), "")
        status = ("FINAL (R2 PUBLICATION_MANIFEST)" if "b200fcdac/final" in base.path else
                  "PRELIMINARY/SUPERSEDED" if any(k in base.path for k in ("preliminary", "superseded")) else
                  "FINAL (curated package)" if any(k in base.path for k in ("integrated_validation", "publication_final_v1",
                                                                             "evidence_enhancement", "/publication/")) else "RECORDED")
        trows.append(dict(table_id=f"{group}:{Path(stem).name}", gallery_group=group, title=title, csv=csv.iloc[0].path if len(csv) else None,
                          md=md.iloc[0].path if len(md) else None, role=base.role,
                          rows=base.rows, columns=base.columns, header=base.header, experiment=experiment, evidence_status=evid,
                          lifecycle=status))
    TT = pd.DataFrame(trows)
    TT.to_csv(INV / "02_COMPLETE_TABLE_INVENTORY.csv", index=False, lineterminator="\n")
    print(len(TT), "logical tables"); print(TT.groupby(["gallery_group", "lifecycle"]).size().to_string())


if __name__ == "__main__":
    main()
