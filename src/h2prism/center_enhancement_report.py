"""Tables (CSV + Markdown) and standalone figures (PNG + SVG) for the Center
evidence enhancement. Reads only the analysis outputs of ``center_enhancement``
and the frozen repository artifacts; performs no new scoring.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

from .center_enhancement import (DY_HYPOTHESES, DY_QUERIES, DY_TRUE, LABEL, LADDER, QUERY_PRIMARY, normalize_lf,
                                 SOLVER_DELTA, TRUTH, sha256_file)

C = dict(bg="#F4F4E9", navy="#10263E", teal="#007F86", blue="#356CB1", slate="#64748B",
         red="#A33F43", grid="#D9DFDE", text="#1F2933")
FONT = ["IBM Plex Sans", "Segoe UI", "DejaVu Sans"]
SHORT = {"NORMAL_OPERATION": "Normal", "CONTROLLED_WITHDRAWAL": "Withdrawal",
         "PRESSURE_COMMAND_CHANGE": "Pressure command", "COMMAND_ISSUANCE_SHIFT": "Timing shift",
         "WITHDRAWAL_SID213": "W·SID 213", "WITHDRAWAL_SID312": "W·SID 312", "WITHDRAWAL_SID215": "W·SID 215",
         "PRESSURE_COMMAND_SID55": "Pressure cmd SID 55", "COMMAND_ISSUANCE_SHIFT_SID59": "Timing SID 59",
         "UNSUPPORTED": "Unsupported"}
QLABEL = {"SID213": "SID 213 withdrawal", "SID312": "SID 312 withdrawal", "SID215": "SID 215 withdrawal",
          "ALT": "SID 213 withdrawal, alt. profile", "PRESSURE": "SID 55 pressure command",
          "TIMING": "SID 59 timing shift", "NOMINAL": "Nominal start-up", "QUIET": "Constructed zero"}
SCEN = {n: (p, f) for n, p, f in LADDER}
SCEN["REF"] = (SOLVER_DELTA["pressure_MPa"], SOLVER_DELTA["flow_kg_s"])
SCEN_ORDER = ["S1", "S2", "S3", "S4", "S5", "S6", "REF"]
QCODE = {"SID213": "Q SID 213", "SID312": "Q SID 312", "SID215": "Q SID 215", "ALT": "Q SID 213 alt", "PRESSURE": "Q SID 55 cmd", "TIMING": "Q SID 59 timing"}


# ------------------------------------------------------------------------- style

def style():
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": FONT, "font.size": 11,
        "figure.facecolor": C["bg"], "axes.facecolor": C["bg"], "savefig.facecolor": C["bg"],
        "axes.edgecolor": C["slate"], "axes.labelcolor": C["text"], "text.color": C["text"],
        "xtick.color": C["text"], "ytick.color": C["text"], "axes.grid": False,
        "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.8,
        "grid.color": C["grid"], "grid.linewidth": 0.6, "legend.frameon": False,
        "svg.fonttype": "none", "axes.titlesize": 13, "axes.titleweight": "semibold",
        "axes.titlelocation": "left", "axes.labelsize": 11.5})
    return plt


def save(fig, out: Path, name: str, caption: str, sources, question: str):
    fig.savefig(out / f"{name}.png", dpi=400)
    fig.savefig(out / f"{name}.svg")
    (out / f"{name}.caption.md").write_text(
        f"**{name}.** {caption}\n\nScientific question: {question}\n\nSource data: "
        + ", ".join(f"`{s}`" for s in sources) + "\n", encoding="utf8")
    import matplotlib.pyplot as plt
    plt.close(fig)


def footnote(fig, text):
    import textwrap
    fig.text(0.012, 0.014, textwrap.fill(text, 160), ha="left", va="bottom", fontsize=8.6, color=C["slate"],
             linespacing=1.25)


def md_table(df: pd.DataFrame) -> str:
    def fmt(v):
        if isinstance(v, float):
            if np.isnan(v):
                return "—"
            return f"{v:.6g}"
        if isinstance(v, (list, tuple)):
            return ", ".join(map(str, v)) if v else "∅"
        return str(v).replace("|", "/")
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    lines += ["| " + " | ".join(fmt(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(lines)


def export(df, tables: Path, name: str, title: str, note: str):
    df.to_csv(tables / f"{name}.csv", index=False)
    text = f"### {name} — {title}\n\n{note}\n\n{md_table(df)}\n"
    (tables / f"{name}.md").write_text(text, encoding="utf8")
    return text


# ------------------------------------------------------------------------ tables

def design_facts(workspace: Path) -> dict:
    folders = {"A": "phase12_sdi_retry_01", "sid312": "final_research_matrix/sid312",
               "sid215": "final_research_matrix/sid215", "pressure_rival": "phase13_02/pressure_rival",
               "alternate_profile": "phase13_02/alternate_profile", "timing": "phase13_command_delay_01"}
    facts = {}
    for key, rel in folders.items():
        for case in ("normal", "outlet_opening"):
            root = workspace / "work" / rel
            if key == "alternate_profile" and case == "outlet_opening":
                root = workspace / "work/phase13_alternate_retry_02"
            d = json.loads((root / case / "design.json").read_text(encoding="utf8"))
            facts[f"{key}:{case}"] = dict(path=(root / case).relative_to(workspace).as_posix(), design=d,
                                          design_sha256=sha256_file(root / case / "design.json"))
    return facts


def table_c01(manifest, facts):
    mech = {"A": ("Controlled atmospheric outlet withdrawal", "213"),
            "sid312": ("Controlled atmospheric outlet withdrawal", "312"),
            "sid215": ("Controlled atmospheric outlet withdrawal", "215"),
            "pressure_rival": ("Internal pressure-command reduction (−0.17 MPa)", "55 (producer 59)"),
            "alternate_profile": ("Controlled outlet withdrawal under +0.005 MPa reservoir overlay", "213"),
            "timing": ("Command-issuance step-time shift 25 s → 26 s", "59 → 55")}
    query = {"A": "SID213", "sid312": "SID312", "sid215": "SID215", "pressure_rival": "PRESSURE",
             "alternate_profile": "ALT", "timing": "TIMING"}
    rows = []
    for key, f in facts.items():
        pair, case = key.split(":")
        d = f["design"]
        m, sid = mech[pair]
        area = d["area"]
        if case == "normal":
            mechanism = "Matched control (no intervention)"
            role = "Matched reference for " + query[pair]
            if pair == "A":
                role += "; NOMINAL query source"
            if pair == "sid312":
                role += "; NORMAL_TRANSIENT template source"
            onset = "—"
        else:
            mechanism = m
            role = f"Query {query[pair]}; template {query[pair]} (excluded for its own query)"
            if pair == "alternate_profile":
                role = "Query ALT; replicate SID 213 template only in loto_replicate"
            onset = "26.0 s (command)" if pair == "timing" else "1000.0 s"
        overlay = d.get("overlay", {})
        rows.append(dict(
            capture=key, source_model="Normal_HNetwork_gest_center.slx (SHA-256 710711f4…), gas R = 0.287 kJ/(kg·K), air-like",
            intervention=mechanism, configured_SID=sid if case != "normal" else "—",
            outlet_area_m2=f"{area['initial_value']} → {area['intervention_final'] if case != 'normal' else area['normal_final']}",
            branch_flow_sensor_SID=d["location"].get("flow_sensor_sid") or "none on this branch",
            overlay=(f"{overlay.get('role')} SID {overlay.get('receiver_sid')}: "
                     f"{overlay.get('intervention_final' if case != 'normal' else 'normal_final')} MPa at {overlay.get('step_time')} s")
            if overlay else "none",
            onset=onset, duration_s=20000, samples=100001, step_s=0.2, sensors="PS1–PS10 (MPa), MFS1–MFS3 (kg/s)",
            raw_sha256=manifest["capture_raw_sha256"][key][:16] + "…", role=role,
            family="Center source family (1 of 1)", eligible="yes", exclusion="—"))
    rows.append(dict(capture="constructed:zero", source_model="none (constructed)", intervention="Constructed zero residual",
                     configured_SID="—", outlet_area_m2="—", branch_flow_sensor_SID="—", overlay="—", onset="—",
                     duration_s=None, samples=None, step_s=None, sensors="—", raw_sha256="—",
                     role="NORMAL_ZERO template; QUIET query", family="—",
                     eligible="template only", exclusion="QUIET is not a capture: excluded from recognition counts"))
    return pd.DataFrame(rows)


def table_c02(rec):
    s = rec[(rec.group == "all") & (rec.clock_bound_s == 1.0) & (rec.condition.isin(["frozen", "loto"]))].copy()
    s = s[s["query"] != "QUIET"]
    interp = {
        ("SID213", "loto"): "Withdrawal falls to rank 2 behind the zero residual (margin 7.4e-5): no transferable withdrawal signature from SID 312/215",
        ("SID312", "loto"): "Nearest template is the SID 215 withdrawal, but the margin over the zero residual is 1.9e-5: near tie",
        ("SID215", "loto"): "SID 215 residual is nearly null on flow and small in normalized pressure: closest to the zero residual",
        ("PRESSURE", "loto"): "Own mechanism unrepresented; nearest is timing; gate blocks routing",
        ("TIMING", "loto"): "Own mechanism unrepresented; nearest is withdrawal and the gate routes it (false route)",
        ("ALT", "loto"): "Matches the SID 213 template, a near-duplicate signature of the same outlet",
        ("NOMINAL", "loto"): "Matches a near-duplicate nominal transient from another control run: uninformative",
    }
    rows = []
    for r in s.itertuples():
        rows.append(dict(query=r.query, condition=r.condition, true_mechanism=SHORT[r.truth],
                         candidates=", ".join(SHORT[m] for m in r.mechanisms_available),
                         self_template_excluded="yes" if r.removed else ("n/a" if r.condition == "frozen" else "no own template"),
                         templates=r.n_templates, predicted=SHORT[r.predicted], best_template=r.predicted_template,
                         score=r.score, runner_up=SHORT.get(r.runner_up, r.runner_up), margin=r.margin,
                         true_rank=r.truth_rank, status=r.status, gate=r.gate_reason,
                         near_duplicate=", ".join(r.near_duplicates) or "—",
                         interpretation="Self-template included: distance 0 by construction" if r.condition == "frozen"
                         and r.score == 0 else interp.get((r.query, r.condition), "Frozen library")))
    return pd.DataFrame(rows)


def confusion(rec):
    s = rec[(rec.group == "all") & (rec.clock_bound_s == 1.0) & (rec.condition == "loto") & (rec["query"] != "QUIET")]
    cols = ["CONTROLLED_WITHDRAWAL", "NORMAL_OPERATION", "PRESSURE_COMMAND_CHANGE", "COMMAND_ISSUANCE_SHIFT"]
    rows = ["CONTROLLED_WITHDRAWAL", "NORMAL_OPERATION", "PRESSURE_COMMAND_CHANGE", "COMMAND_ISSUANCE_SHIFT"]
    m = pd.DataFrame(0, index=rows, columns=cols + ["UNSUPPORTED"])
    nearest = pd.DataFrame("", index=rows, columns=cols + ["UNSUPPORTED"])
    for r in s.itertuples():
        if r.status == "UNSUPPORTED":
            m.loc[r.truth, "UNSUPPORTED"] += 1
            nearest.loc[r.truth, "UNSUPPORTED"] += f"nearest: {SHORT[r.predicted]}"
        else:
            m.loc[r.truth, r.predicted] += 1
    return m, nearest


def table_c03(loc):
    s = loc[(loc.group == "all") & (loc.clock_bound_s == 1.0) & (loc.condition.isin(["loto", "loto_replicate"]))]
    rows = []
    for r in s.itertuples():
        rows.append(dict(query=r.query, condition=r.condition, true_SID=r.true_site.replace("SID", ""),
                         candidate_SIDs=", ".join(c.replace("SID", "") for c in r.candidates),
                         score_SID213=r.site_scores.get("SID213"), score_SID312=r.site_scores.get("SID312"),
                         score_SID215=r.site_scores.get("SID215"),
                         rank_SID213=r.site_ranks.get("SID213"), rank_SID312=r.site_ranks.get("SID312"),
                         rank_SID215=r.site_ranks.get("SID215"),
                         top1=r.top1.replace("SID", ""), top1_result="correct" if r.top1_correct else
                         ("unsupported" if r.status == "UNSUPPORTED" else "incorrect"),
                         top2_includes_true=("unsupported" if r.status == "UNSUPPORTED" else
                                             "yes" if r.top2_includes_truth else "no"),
                         margin=r.margin, status=r.status,
                         relevant_sensors={"SID213": "MFS3 (branch meter SID 218), PS1 (junction SID 50)",
                                           "SID312": "MFS1 (branch meter SID 311)",
                                           "SID215": "PS4/PS8, PS9 (no branch flow meter)"}[r.true_site],
                         independence="one source family; ALT↔SID 213 differ only by a +0.005 MPa reservoir overlay"))
    return pd.DataFrame(rows)


def table_c04(pairs, loc):
    rows = []
    sites = {"SID213", "SID312", "SID215"}
    base = {(r.a, r.b): r for r in pairs[(pairs.group == "all") & (pairs.clock_bound_s == 1.0)].itertuples()}
    for r in pairs[pairs.clock_bound_s == 1.0].itertuples():
        if not ({r.a, r.b} <= sites or "ALT" in (r.a, r.b)):
            continue
        b = base[(r.a, r.b)]
        rel = (r.b3_rms - b.b3_rms) / b.b3_rms if r.group != "all" else 0.0
        flow = r.max_abs_flow_kg_s if r.max_abs_flow_kg_s == r.max_abs_flow_kg_s else None
        if r.group == "pressure":
            kind = f"pressure-only view: {r.max_abs_pressure_MPa * 1e3:.3g} kPa largest contrast"
        elif flow is not None and flow > 0.1:
            kind = "flow-separated: a branch meter sees one outlet but not the other"
        elif r.group == "flow":
            kind = f"not separable by flow ({flow:.2g} kg/s): neither outlet has a meter in this group"
        else:
            kind = f"flow nearly blind ({flow:.2g} kg/s); contrast carried by {r.max_abs_pressure_MPa * 1e3:.3g} kPa of pressure"
        if {r.a, r.b} == {"SID213", "ALT"}:
            kind = "same outlet; differs only through reservoir overlay"
        rows.append(dict(pair=f"{r.a}–{r.b}", group=r.group, channels=r.channels,
                         pressure_contrast_MPa=r.max_abs_pressure_MPa, flow_contrast_kg_s=r.max_abs_flow_kg_s,
                         b3_combined=r.b3_rms, pressure_share_of_b3=r.pressure_share, flow_share_of_b3=r.flow_share,
                         relative_change_vs_all=rel, interpretation=kind))
    return pd.DataFrame(rows)


def table_c05(thr):
    s = thr[thr.supported & (thr.group.isin(["pressure", "flow"]))].copy()
    rows = []
    for r in s.itertuples():
        k = "P_MPa" if r.group == "pressure" else "F_kg_s"
        e, f = getattr(r, "E_" + k), getattr(r, "Fz_" + k)
        rows.append(dict(query=r.query, hypothesis=SHORT[r.hypothesis], role="true" if r.is_true else "rival",
                         applicability="adapter available (self-template excluded)", sensor_group=r.group,
                         unit="MPa" if r.group == "pressure" else "kg/s", clock_bound_s=r.clock_bound_s,
                         eps_obs_plus_eps_model="eps_total (only the sum enters; verified)",
                         exclusion_onset_E=e, feasibility_onset_F=f,
                         excluded_when=f"eps_total < {e:.9g}", consistent_when=f"eps_total ≥ {f:.9g}",
                         indeterminate_band=("empty" if np.isclose(e, f, rtol=1e-12, atol=0) else f"[{e:.9g}, {f:.9g})"),
                         threshold_type="exact (closed form, exact-rational confirmed)", qualification=LABEL,
                         limitation="hypothetical bounds; one source family"))
    for r in thr[~thr.supported & (thr.group == "all")].itertuples():
        rows.append(dict(query=r.query, hypothesis=SHORT[r.hypothesis], role="true" if r.is_true else "rival",
                         applicability="UNSUPPORTED: only template is the query's own capture", sensor_group="all",
                         unit="—", clock_bound_s=r.clock_bound_s, eps_obs_plus_eps_model="—",
                         exclusion_onset_E=np.nan, feasibility_onset_F=np.nan, excluded_when="never (no adapter)",
                         consistent_when="never (no adapter)", indeterminate_band="all bounds",
                         threshold_type="not identifiable", qualification=LABEL, limitation="no independent template"))
    return pd.DataFrame(rows)


def short_set(v):
    return ", ".join(SHORT.get(x, x) for x in v) if len(v) else "∅"


def table_c06(dec):
    s = dec[(dec.group == "all") & (dec.clock_bound_s == 1.0)].copy()
    rows = []
    for r in s.itertuples():
        correct = None
        if r.decision == "SPECIFIC":
            correct = "correct" if r.selected == r.true_hypothesis else "INCORRECT (true mechanism unrepresented)" \
                if not r.true_supported else "INCORRECT"
        elif r.decision == "AMBIGUOUS":
            correct = "true retained" if r.true_hypothesis in r.consistent else "true not in universe"
        else:
            correct = "abstained"
        if r.universe == "full":
            interp = "Unmodelled declared hypotheses stay indeterminate; SPECIFIC/AMBIGUOUS unreachable"
        elif r.reason == "MODEL_MISMATCH":
            interp = "Every supported hypothesis excluded: bounds tighter than template discrepancy"
        elif r.decision == "AMBIGUOUS":
            interp = "Bounds wide enough that several templates fit"
        elif r.decision == "SPECIFIC":
            interp = "One supported hypothesis survives; all supported rivals excluded"
        else:
            interp = "Some supported hypothesis neither excluded nor witnessed"
        rows.append(dict(query=r.query, universe=r.universe, scenario=r.scenario,
                         eps_P_MPa=r.eps_P_MPa, eps_F_kg_s=r.eps_F_kg_s,
                         consistent=short_set(r.consistent), excluded=short_set(r.excluded),
                         indeterminate=short_set(r.indeterminate), decision=r.decision, reason=r.reason,
                         selected=SHORT.get(r.selected, r.selected) if r.selected else "—",
                         correctness=correct, label=LABEL, interpretation=interp))
    return pd.DataFrame(rows)


def table_c07(rec, loc, dec):
    a = rec[(rec.group == "all") & (rec.clock_bound_s == 1.0) & (rec["query"] != "QUIET")]
    rows = []
    for cond, name in (("frozen", "Frozen B3 full library (self-templates present)"),
                       ("loto", "B3, own template excluded"),
                       ("loto_replicate", "B3, own template excluded + ALT replicate")):
        x = a[a.condition == cond]
        sup = x[x.status != "UNSUPPORTED"]
        rows.append(dict(method=name, output_type="nearest mechanism (ranking)", unit="normalized B3 RMS",
                         evaluated=f"{len(x)} queries", supported=len(sup),
                         agreement=f"{(sup.status == 'CORRECT').sum()}/{len(sup)}",
                         unsupported=int((x.status == "UNSUPPORTED").sum()),
                         note="all 7 match a self (5) or near-duplicate (2) template" if cond == "frozen" else ""))
    for g in ("all", "pressure", "flow", "omit_MFS3"):
        x = loc[(loc.group == g) & (loc.clock_bound_s == 1.0) & (loc.condition == "loto_replicate")]
        sup = x[x.status != "UNSUPPORTED"]
        rows.append(dict(method=f"B3 location ranking, {g}", output_type="ranked outlet SIDs",
                         unit="normalized B3 RMS", evaluated=f"{len(x)} withdrawal queries", supported=len(sup),
                         agreement=f"top-1 {int(sup.top1_correct.sum())}/{len(sup)}",
                         unsupported=int((x.status == "UNSUPPORTED").sum()),
                         note="supported queries share one outlet (SID 213)"))
    for u in ("full", "restricted"):
        x = dec[(dec.group == "all") & (dec.clock_bound_s == 1.0) & (dec.universe == u)]
        spec = x[x.decision == "SPECIFIC"]
        rows.append(dict(method=f"Conditional D(Y), {u} universe", output_type="set-valued decision",
                         unit="native bounds (MPa, kg/s)", evaluated=f"{len(x)} query×scenario cells",
                         supported=len(x), agreement=f"SPECIFIC correct {int((spec.selected == spec.true_hypothesis).sum())}"
                         f"/{len(spec)}", unsupported=0, note=LABEL))
    return pd.DataFrame(rows)


def table_c08(stats):
    s = stats
    rows = [
        ("The 12 accepted captures and 410 frozen files are unchanged", "baseline_freeze --verify (before and after)",
         "12 captures; 410 files matched", "VERIFIED", "integrity, not validity", "yes", "Frozen Center evidence re-verified byte for byte."),
        ("Center model is air-like", "source SLX gas block R", "R = 0.287 kJ/(kg·K), Z = 0.998386", "VERIFIED",
         "no hydrogen material claim possible", "yes", "Controlled simulation with an air-like gas model."),
        ("Mechanism recognition does not survive self-template removal", "TAB C-02",
         s["loto_mech"], "DESCRIPTIVE (one family)", "7 queries, 1 family", "yes",
         "Without self-templates, withdrawal at a new outlet is not recognised reliably."),
        ("Withdrawal signatures are outlet-specific", "TAB C-04, channel_signal.csv",
         "SID 213→MFS3 0.691 kg/s; SID 312→MFS1 0.647 kg/s; SID 215 flow ≤3.9e-4 kg/s", "DESCRIPTIVE",
         "sensor configuration of one model", "yes", "Each outlet excites a different branch sensor."),
        ("Categorical location ranking with an independent same-outlet template", "TAB C-03",
         s["loc"], "DESCRIPTIVE (2 queries, 1 outlet)", "near-duplicate template", "yes, with caveat",
         "SID 213 is ranked first when a replicate SID 213 template exists."),
        ("Flow-dependent B3 localization; pressure contrasts exist in native units", "TAB C-04",
         s["sensor"], "DESCRIPTIVE", "normalization by absolute level", "yes",
         "B3 ranking is carried by flow; pressure differences are 1–5.5 kPa."),
        ("Conditional correct SPECIFIC window", "TAB C-05/C-06", s["window"], LABEL,
         "hypothetical bounds; replicate template", "yes, labelled conditional",
         "Under declared bounds, SID 213 would be specific within a finite precision window."),
        ("Restricted universe can be confidently wrong", "TAB C-06", s["wrong"], LABEL,
         "true mechanism unrepresented", "yes", "Restricting to modelled hypotheses yields wrong SPECIFIC decisions."),
        ("Full declared universe never decides", "TAB C-06", s["full"], LABEL, "unmodelled FAULT/DELAY/SID 222",
         "yes", "Formal D(Y) abstains whenever declared hypotheses lack adapters."),
        ("Frozen 12/12 UNRESOLVED unchanged", "TAB_13, research_evidence.json",
         "12/12 UNRESOLVED, INVALID_UNCERTAINTY; all hypotheses adapter=None", "VERIFIED", "—", "yes",
         "Frozen formal outcome retained."),
        ("RQ1 (registered)", "03_results/primary_protocol/PRIMARY/rq1.csv", "NOT_ESTIMABLE at 0.60/0.80/0.90",
         "REGISTERED RESULT", "max Center coverage 0.258", "yes", "RQ1 was not estimable under the registered protocol."),
        ("H1", "PRIMARY + exploratory shared coverage", "all intervals vs s_C−D include 0", "NOT ESTABLISHED",
         "inspected partitions", "yes", "H1 is not established."),
        ("RQ2 (development)", "PROTOCOL_2_ABLATION_REPORT.md", "s_C = s_C−D = confidence at matched development coverage",
         "NEGATIVE (exploratory)", "13 groups", "yes", "No incremental value of D(x) was demonstrated."),
        ("Leak localization / fault diagnosis in hydrogen pipelines", "—", "—", "NOT ESTABLISHED", "no field truth",
         "no", "Not claimed."),
    ]
    return pd.DataFrame(rows, columns=["claim", "source_evidence", "numerical_result", "validation_level",
                                       "limitation", "poster", "recommended_wording"])


# ----------------------------------------------------------------------- figures

def fig_c01(plt, out, facts, signal):
    """Logical observability schematic from design records (no geometry)."""
    fig = plt.figure(figsize=(9.6, 5.4))
    ax = fig.add_axes([0.02, 0.1, 0.96, 0.86])
    ax.set_xlim(0, 100), ax.set_ylim(0, 60), ax.axis("off")
    ax.set_title("Controlled Center interventions and their branch instrumentation", pad=6)
    col = {"213": C["teal"], "312": C["blue"], "215": C["red"]}
    sites = [("213", "200", "218 · MFS3", "47, 48, 50 (PS1 at 50)", 46),
             ("312", "316", "311 · MFS1", "309, 49", 30),
             ("215", "217", "none", "109, 221, 453 (PS4 at 109)", 14)]
    ax.text(6, 55, "Upstream junction SIDs", fontsize=10.5, color=C["slate"])
    ax.text(40, 55, "Outlet restriction", fontsize=10.5, color=C["slate"])
    ax.text(58, 55, "Branch flow sensor", fontsize=10.5, color=C["slate"])
    ax.text(78, 55, "Atmospheric reservoir", fontsize=10.5, color=C["slate"])
    for sid, res, meter, junc, y in sites:
        ax.plot([30, 40], [y, y], color=C["slate"], lw=1.2)
        ax.plot([50, 80], [y, y], color=C["slate"], lw=1.2)
        ax.text(6, y, junc, va="center", fontsize=10.5)
        ax.add_patch(plt.Rectangle((40, y - 3), 10, 6, fc="white", ec=col[sid], lw=1.8))
        ax.text(45, y, f"SID {sid}", ha="center", va="center", fontsize=11, color=col[sid], weight="semibold")
        if meter != "none":
            ax.add_patch(plt.Circle((64, y), 2.2, fc="white", ec=C["navy"], lw=1.4))
            ax.text(64, y, "F", ha="center", va="center", fontsize=10, weight="semibold", color=C["navy"])
            ax.text(64, y - 4.5, meter, ha="center", va="top", fontsize=10)
        else:
            ax.text(64, y, "no flow sensor", ha="center", va="center", fontsize=10, color=C["red"],
                    bbox=dict(fc=C["bg"], ec="none"))
        ax.add_patch(plt.Rectangle((80, y - 2.5), 8, 5, fc=C["grid"], ec=C["slate"], lw=1))
        ax.text(84, y, f"SID {res}", ha="center", va="center", fontsize=10)
        ax.text(84, y - 4.2, "area 0.0010 → 0.0011 m²\nat 1000 s", ha="center", va="top", fontsize=8.6, color=C["slate"])
    ax.text(6, 2.5, "Operational rivals on the same source model: SID 55 pressure-source command −0.17 MPa at 1000 s;\n"
                    "SID 59 command step time shifted 25 s → 26 s (command issuance, not actuator lag).", fontsize=10)
    footnote(fig, "Logical connectivity from capture design records; no pipe lengths, coordinates or flow directions are implied. "
                  "One air-like Center source family (R = 0.287 kJ/(kg·K)).")
    save(fig, out, "FIG_C01_intervention_observability",
         "Controlled interventions on the Center simulation and the branch flow sensors that observe them. "
         "SID 213 and SID 312 each have a dedicated branch flow meter (MFS3, MFS1); SID 215 has none. "
         "This is a controlled simulation with known intervention points, not a verified industrial leak network.",
         ["work/*/design.json (hashes in baseline_manifest.json)"], "Q6/Q3 — what was tested and observed")


def fig_c02(plt, out, m):
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    data = m.values.astype(float)
    from matplotlib.colors import LinearSegmentedColormap
    seq = LinearSegmentedColormap.from_list("teal", ["#DCECEC", C["teal"]])
    ax.imshow(np.where(data > 0, data, np.nan), cmap=seq, vmin=1, vmax=max(2, data.max()), aspect="auto")
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            v = int(data[i, j])
            ax.text(j, i, str(v), ha="center", va="center", fontsize=15 if v else 11,
                    color=C["navy"] if v else C["slate"], weight="semibold" if v else "normal")
    ax.set_xticks(range(data.shape[1]), [SHORT[c] for c in m.columns], fontsize=11)
    ax.set_yticks(range(data.shape[0]), [SHORT[r] for r in m.index], fontsize=11)
    ax.set_xlabel("Nearest mechanism (B3, own template excluded)")
    ax.set_ylabel("Configured intervention")
    ax.set_xticks(np.arange(-.5, data.shape[1]), minor=True), ax.set_yticks(np.arange(-.5, data.shape[0]), minor=True)
    ax.grid(which="minor", color=C["grid"], lw=1.2), ax.tick_params(which="minor", length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title("Mechanism recognition without self-templates (n = 7 capture-derived queries)")
    plt.subplots_adjust(left=0.2, right=0.97, top=0.9, bottom=0.22)
    footnote(fig, "All sensors, 30 s prefix, ±1 s shift. One generating source family. Counts, not rates. "
                  "Unsupported: the query's mechanism has no remaining template (nearest: Timing → Withdrawal, Pressure → Timing).")
    save(fig, out, "FIG_C02_mechanism_recognition_loto",
         "Count confusion of configured intervention versus nearest mechanism with the query's own template removed. "
         "Of five supported queries, three agree: SID 312 withdrawal by a 1.9e-5 margin, the alternate-profile SID 213 and the "
         "nominal start-up, both through near-duplicate templates. SID 213 and SID 215 withdrawals are nearest to the zero residual. All queries come from one source family.",
         ["recognition.json"], "Q1/Q6 — does mechanism recognition survive self-template removal?")


def fig_c03(plt, out, rec):
    s = rec[(rec.group == "all") & (rec.clock_bound_s == 1.0) & (rec.condition == "loto") & (rec["query"] != "QUIET")]
    order = ["SID213", "SID312", "SID215", "ALT", "NOMINAL", "PRESSURE", "TIMING"]
    mk = {"CONTROLLED_WITHDRAWAL": ("o", C["teal"]), "NORMAL_OPERATION": ("s", C["slate"]),
          "PRESSURE_COMMAND_CHANGE": ("D", C["blue"]), "COMMAND_ISSUANCE_SHIFT": ("^", C["red"])}
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    for i, q in enumerate(order):
        r = s[s["query"] == q].iloc[0]
        for mech, score in r.mechanism_scores.items():
            m, c = mk[mech]
            truth = mech == r.truth
            ax.scatter(max(score, 1e-8), i, marker=m, s=110 if truth else 70, facecolor=c if truth else "white",
                       edgecolor=c, lw=1.6, zorder=3)
        if r.status == "UNSUPPORTED":
            ax.text(2.6, i, "own mechanism\nunrepresented", va="center", fontsize=9.5, color=C["red"])
        else:
            ax.text(2.6, i, f"{r.status.lower()}  ·  margin {r.margin:.2g}", va="center", fontsize=9.5,
                    color=C["navy"] if r.status == "CORRECT" else C["red"])
    ax.set_xscale("log"), ax.set_xlim(1e-8, 2)
    ax.set_yticks(range(len(order)), [QLABEL[q] for q in order]), ax.invert_yaxis()
    ax.grid(axis="x", which="major"), ax.set_axisbelow(True)
    ax.set_xlabel("B3 discrepancy (normalized RMS, dimensionless; values < 1e-8 drawn at 1e-8)")
    handles = [plt.Line2D([], [], marker=mk[k][0], ls="", mfc="white", mec=mk[k][1], mew=1.6, ms=8, label=SHORT[k]) for k in mk]
    handles.append(plt.Line2D([], [], marker="o", ls="", mfc=C["slate"], mec=C["slate"], ms=8, label="filled = configured mechanism"))
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.42, 1.0), ncol=5, fontsize=9.5)
    plt.subplots_adjust(left=0.24, right=0.76, top=0.86, bottom=0.17)
    footnote(fig, "Own template excluded; best template per mechanism; all sensors, 30 s prefix, ±1 s. One source family.")
    save(fig, out, "FIG_C03_mechanism_ranking_evidence",
         "Every admissible mechanism score per query after self-template exclusion. For SID 213 and SID 312 the nearest "
         "other-outlet withdrawal and the zero (normal) residual differ by only 0.26 % and 0.06 %; SID 215 lies 12.8x "
         "closer to the zero residual than to any other withdrawal. Withdrawal signatures do not transfer across outlets.",
         ["recognition.json"], "Q1 — how separated are competing mechanisms?")


def fig_c04(plt, out, loc):
    s = loc[(loc.group == "all") & (loc.clock_bound_s == 1.0) & (loc.condition == "loto_replicate")]
    order = ["SID213", "ALT", "SID312", "SID215"]
    cols = ["SID213", "SID312", "SID215"]
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    for i, q in enumerate(order):
        r = s[s["query"] == q].iloc[0]
        for j, c in enumerate(cols):
            truth = c == r.true_site
            if c in r.site_scores:
                rk = r.site_ranks[c]
                fc = {1: C["teal"], 2: "#9CC9CB", 3: "#DCECEC"}[rk]
                ax.add_patch(plt.Rectangle((j - .45, i - .4), .9, .8, fc=fc, ec=C["navy"] if truth else C["grid"],
                                           lw=2.4 if truth else 1))
                ax.text(j, i - .08, f"rank {rk}", ha="center", va="center", fontsize=12,
                        color="white" if rk == 1 else C["navy"], weight="semibold")
                ax.text(j, i + .2, f"{r.site_scores[c]:.3g}", ha="center", va="center", fontsize=10,
                        color="white" if rk == 1 else C["text"])
            else:
                ax.add_patch(plt.Rectangle((j - .45, i - .4), .9, .8, fc=C["bg"], ec=C["red"], lw=2, hatch="//"))
                ax.text(j, i, "no independent\ntemplate", ha="center", va="center", fontsize=9.5, color=C["red"],
                        bbox=dict(fc=C["bg"], ec="none", pad=2))
    ax.set_xlim(-.6, 2.6), ax.set_ylim(3.6, -.6)
    ax.set_xticks(range(3), [f"Outlet SID {c[3:]}" for c in cols])
    ax.set_yticks(range(4), [QLABEL[q] + ("\n(configured outlet unsupported)" if q in ("SID312", "SID215") else "") for q in order])
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)
    ax.set_title("Categorical outlet ranking with own template excluded (4 queries, 1 outlet supported)")
    footnote(fig, "Navy outline = configured outlet. Cell text = B3 normalized RMS. All sensors, 30 s, ±1 s. "
                  "Supported queries (SID 213, alt. profile) are near-duplicate signatures of one outlet; not independent trials.")
    plt.subplots_adjust(left=0.26, right=0.97, top=0.88, bottom=0.14)
    save(fig, out, "FIG_C04_location_ranking",
         "Rank of each candidate outlet for the four withdrawal queries after removing the query's own template. "
         "Only SID 213 has a second realisation (alternate reservoir profile); both SID 213 queries rank SID 213 first. "
         "SID 312 and SID 215 cannot be evaluated because their only template is their own capture.",
         ["location.json"], "Q2 — can the configured outlet be ranked?")


def fig_c05(plt, out, loc):
    s = loc[(loc.clock_bound_s == 1.0) & (loc.condition == "loto_replicate") & (loc["query"].isin(["SID213", "ALT"]))]
    groups = ["all", "pressure", "flow", "omit_MFS3"]
    names = {"all": "All 13", "pressure": "Pressure (10)", "flow": "Flow (3)", "omit_MFS3": "All − MFS3"}
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    for q, c, dy in (("SID213", C["teal"], -0.08), ("ALT", C["blue"], 0.08)):
        ratio = []
        for g in groups:
            r = s[(s["query"] == q) & (s.group == g)].iloc[0]
            sc = sorted(r.site_scores.values())
            ratio.append(sc[1] / sc[0])
        x = np.arange(len(groups)) + dy
        ax.plot(x, ratio, color=c, lw=1.4, marker="o", ms=8, label=QLABEL[q])
        if q == "SID213":
            for xi, v in zip(np.arange(len(groups)), ratio):
                ax.text(xi, v * 1.45, f"{v:,.0f}×", ha="center", fontsize=10.5, color=C["navy"])
    ax.axhline(1, color=C["red"], lw=1, ls="--")
    ax.text(3.45, 1.12, "tie", color=C["red"], fontsize=9.5, ha="right")
    ax.set_yscale("log"), ax.set_ylim(0.8, 1e5)
    ax.set_xticks(range(len(groups)), [names[g] for g in groups])
    ax.set_ylabel("Runner-up / correct outlet B3 distance (dimensionless)")
    ax.grid(axis="y"), ax.set_axisbelow(True), ax.legend(loc="upper right")
    ax.set_title("Location separation by sensor group (correct outlet SID 213 ranked first in all groups)")
    footnote(fig, "Ratio is invariant to the per-group channel-count averaging in B3. 30 s, ±1 s. "
                  "Both queries share one outlet and one source family.")
    save(fig, out, "FIG_C05_sensor_group_location_sensitivity",
         "Separation between the correct outlet and the runner-up for the two SID 213 queries under four sensor groups. "
         "SID 213 is ranked first in every group. Pressure alone separates it by ~570×, flow and all sensors by ~1,030×; "
         "withholding MFS3 lowers the absolute margin (0.028 → 0.0021) yet raises the ratio to ~2,680× because the "
         "near-duplicate replicate differs from SID 213 mainly on MFS3.",
         ["location.json"], "Q3 — which sensors carry the location information?")


def fig_c06(plt, out, pairs):
    s = pairs[(pairs.group == "all") & (pairs.clock_bound_s == 1.0)]
    keep = {("SID213", "SID312"): (10, 8), ("SID213", "SID215"): (10, -22), ("SID312", "SID215"): (-175, -24),
            ("SID213", "ALT"): (10, 6)}
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    for r in s.itertuples():
        if (r.a, r.b) not in keep:
            continue
        same = {r.a, r.b} == {"SID213", "ALT"}
        has215 = "SID215" in (r.a, r.b)
        c = C["slate"] if same else C["red"] if has215 else C["teal"]
        ax.scatter(r.max_abs_pressure_MPa, r.max_abs_flow_kg_s, s=90, color=c, zorder=3, marker="s" if same else "o")
        lab = ("SID 213 vs alt.-profile SID 213" if same else f"SID {r.a[3:]} vs SID {r.b[3:]}")
        lab += f"\n{r.max_abs_pressure_MPa * 1e3:.3g} kPa · {r.max_abs_flow_kg_s:.3g} kg/s"
        ax.annotate(lab, (r.max_abs_pressure_MPa, r.max_abs_flow_kg_s), xytext=keep[(r.a, r.b)],
                    textcoords="offset points", fontsize=9.3)
    ax.axvline(SOLVER_DELTA["pressure_MPa"], color=C["slate"], ls=":", lw=1)
    ax.axhline(SOLVER_DELTA["flow_kg_s"], color=C["slate"], ls=":", lw=1)
    ax.text(SOLVER_DELTA["pressure_MPa"] * 1.08, 2e-3, "solver-refinement\nΔ (not an enclosure)", fontsize=8.5,
            color=C["slate"])
    ax.set_xscale("log"), ax.set_yscale("log"), ax.set_xlim(1e-6, 0.2), ax.set_ylim(5e-7, 3)
    ax.set_xlabel("Largest pressure difference between templates (MPa, best shift within ±1 s)")
    ax.set_ylabel("Largest flow difference (kg/s)")
    ax.grid(which="major"), ax.set_axisbelow(True)
    ax.set_title("Where outlet-pair information lies: flow for 213/312, pressure only for 215")
    handles = [plt.Line2D([], [], marker="o", ls="", color=C["teal"], label="pairs without SID 215"),
               plt.Line2D([], [], marker="o", ls="", color=C["red"], label="pairs with SID 215"),
               plt.Line2D([], [], marker="s", ls="", color=C["slate"], label="same outlet, alternate profile")]
    ax.legend(handles=handles, loc="upper left", fontsize=9.5)
    plt.subplots_adjust(left=0.1, right=0.97, top=0.9, bottom=0.17)
    footnote(fig, "Alternate-profile pairs with SID 312/215 coincide with the SID 213 pairs and are omitted (see pair_contrasts.csv). Native units on separate axes; no pressure–flow sum. Conditional on the simulated sensor configuration.")
    save(fig, out, "FIG_C06_pressure_vs_flow_contrast",
         "Largest native-unit difference between withdrawal templates in pressure (x) and flow (y). "
         "SID 213 and SID 312 differ by ~0.65–0.69 kg/s through their branch meters; any pair involving SID 215 differs "
         "in flow only because the other outlet is metered, while SID 215 itself is visible only as 4.8–5.5 kPa of pressure.",
         ["pair_contrasts.csv"], "Q3 — pressure versus flow distinguishability")


def fig_c07(plt, out, dec):
    s = dec[(dec.group == "all") & (dec.clock_bound_s == 1.0) & (dec.universe == "restricted")]
    rows, cells = [], []
    for q in DY_QUERIES:
        for h in DY_HYPOTHESES:
            vals = []
            for sc in SCEN_ORDER:
                r = s[(s["query"] == q) & (s.scenario == sc)].iloc[0]
                vals.append(3 if h not in r.consistent + r.excluded + r.indeterminate else
                            0 if h in r.excluded else 2 if h in r.consistent else 1)
            rows.append((q, h)), cells.append(vals)
    a = np.array(cells)
    from matplotlib.colors import ListedColormap
    cmap = ListedColormap([C["navy"], "#C9A227", C["teal"], C["bg"]])
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    ax.imshow(a, cmap=cmap, vmin=-.5, vmax=3.5, aspect="auto", interpolation="nearest")
    for i, (q, h) in enumerate(rows):
        for j in range(a.shape[1]):
            if a[i, j] == 3:
                ax.add_patch(plt.Rectangle((j - .5, i - .5), 1, 1, fc="none", ec=C["red"], hatch="///", lw=0))
            if h == DY_TRUE[q] and a[i, j] != 3:
                ax.add_patch(plt.Rectangle((j - .5, i - .5), 1, 1, fc="none", ec="white", lw=1.6))
    ax.set_yticks(range(len(rows)), [f"{QCODE[q]} | {SHORT[h]}" for q, h in rows], fontsize=6.8)
    ax.set_xticks(range(len(SCEN_ORDER)),
                  [f"{k}\n{SCEN[k][0]:.0e} MPa\n{SCEN[k][1]:.0e} kg/s" if k != "REF" else
                   "REF\n0.034 MPa\n0.018 kg/s" for k in SCEN_ORDER], fontsize=8.5)
    for i in range(0, len(rows), len(DY_HYPOTHESES)):
        ax.axhline(i - .5, color=C["bg"], lw=2.5)
    ax.tick_params(length=0)
    ax.set_title("Conditional / Hypothetical Bounds — hypothesis status, restricted universe", fontsize=12)
    handles = [plt.Rectangle((0, 0), 1, 1, fc=C["navy"], label="excluded"),
               plt.Rectangle((0, 0), 1, 1, fc="#C9A227", label="indeterminate"),
               plt.Rectangle((0, 0), 1, 1, fc=C["teal"], label="consistent"),
               plt.Rectangle((0, 0), 1, 1, fc=C["bg"], ec=C["red"], hatch="///", label="unsupported (own template only)"),
               plt.Rectangle((0, 0), 1, 1, fc="none", ec=C["slate"], lw=1.6, label="white outline = configured")]
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.01, 1), fontsize=8.5)
    plt.subplots_adjust(left=0.24, right=0.74, top=0.92, bottom=0.2)
    footnote(fig, f"{LABEL}: eps_total = eps_obs + eps_model per kind, ±1 s clock, 30 s prefix. REF uses observed solver-refinement Δ "
                  "(not an enclosure). One source family.")
    save(fig, out, "FIG_C07_conditional_exclusion_map",
         "Status of every hypothesis for every residual query across declared hypothetical bound scenarios. "
         "Bounds are hypothetical design assumptions, not validated sensor or model specifications.",
         ["dy_decisions.json"], "Q4 — which rivals become excludable under declared bounds?")


def fig_c08(plt, out, thr):
    s = thr[thr.supported & (thr.clock_bound_s == 1.0)]
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 5.4), sharey=True)
    qs = ["SID213", "ALT", "SID312", "SID215", "PRESSURE", "TIMING"]
    for ax, g, key, unit, ref in ((axes[0], "pressure", "P_MPa", "MPa", SOLVER_DELTA["pressure_MPa"]),
                                  (axes[1], "flow", "F_kg_s", "kg/s", SOLVER_DELTA["flow_kg_s"])):
        x = s[s.group == g]
        for i, q in enumerate(qs):
            y = x[x["query"] == q]
            riv = y[~y.is_true]
            tru = y[y.is_true]
            minE = riv["E_" + key].min()
            ax.scatter(riv["E_" + key], [i] * len(riv), marker="|", s=220, color=C["navy"], lw=1.6, zorder=3)
            ax.scatter([minE], [i], marker="|", s=420, color=C["red"], lw=2.4, zorder=4)
            if len(tru):
                f = float(tru["Fz_" + key].iloc[0])
                ax.scatter([f], [i], marker="o", s=70, color=C["teal"], zorder=5)
                if f < minE:
                    ax.plot([f, minE], [i, i], color=C["teal"], lw=5, alpha=.35, solid_capstyle="butt")
                    ax.text(np.sqrt(f * minE), i + .36, f"correct-SPECIFIC window ×{minE / f:.0f}", ha="center",
                            va="center", fontsize=8.8, color=C["teal"])
        ax.axvline(ref, color=C["slate"], ls=":", lw=1)
        ax.set_xscale("log"), ax.set_xlabel(f"Total half-width eps ({unit})")
        ax.grid(axis="x"), ax.set_axisbelow(True)
        ax.set_title(f"({'a' if g == 'pressure' else 'b'}) {g}-only sensors", fontsize=12)
    axes[0].set_yticks(range(len(qs)), [QLABEL[q] + ("" if q in ("SID213", "ALT") else " *") for q in qs])
    axes[0].invert_yaxis(), axes[0].set_ylim(len(qs) - .4, -.6)
    axes[0].set_xlim(1e-6, 0.6), axes[1].set_xlim(1e-4, 2)
    handles = [plt.Line2D([], [], marker="|", ls="", color=C["navy"], ms=12, mew=1.6, label="rival exclusion onset E"),
               plt.Line2D([], [], marker="|", ls="", color=C["red"], ms=14, mew=2.4, label="smallest rival E"),
               plt.Line2D([], [], marker="o", ls="", color=C["teal"], label="configured hypothesis feasible from F"),
               plt.Line2D([], [], ls=":", color=C["slate"], label="solver-refinement Δ")]
    fig.legend(handles=handles, loc="lower center", ncol=4, fontsize=9.3, bbox_to_anchor=(0.6, 0.075))
    fig.suptitle("Conditional / Hypothetical Bounds", x=0.012, y=0.985, ha="left", fontsize=12, color=C["red"])
    plt.subplots_adjust(left=0.23, right=0.98, top=0.87, bottom=0.26, wspace=0.08)
    footnote(fig, "* configured mechanism has no independent template, so no correct SPECIFIC exists at any bound. "
                  "Exact closed-form onsets (rationals): excluded iff eps < E; consistent iff eps ≥ F; ±1 s clock, 30 s prefix. "
                  "Shaded = bounds giving a correct SPECIFIC. Dotted = observed 0.4→0.2 s solver Δ (not an enclosure).")
    save(fig, out, "FIG_C08_exclusion_thresholds",
         "Exclusion onset of every supported rival and feasibility onset of the configured hypothesis, separately for "
         "pressure-only (MPa) and flow-only (kg/s) sensing. A finite window where only the configured outlet survives "
         "exists for the two SID 213 queries (≈210× in pressure, ≈1,010× in flow).",
         ["dy_thresholds.csv"], "Q4 — what precision would separate the hypotheses?")


def fig_c09(plt, out, dec):
    s = dec[(dec.group == "all") & (dec.clock_bound_s == 1.0) & (dec.universe == "restricted")]
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    colors = {"SPECIFIC": C["teal"], "AMBIGUOUS": "#C9A227", "UNRESOLVED": C["slate"]}
    for i, q in enumerate(DY_QUERIES):
        for j, sc in enumerate(SCEN_ORDER):
            r = s[(s["query"] == q) & (s.scenario == sc)].iloc[0]
            wrong = r.decision == "SPECIFIC" and r.selected != r.true_hypothesis
            fc = C["red"] if wrong else colors[r.decision]
            ax.add_patch(plt.Rectangle((j - .45, i - .4), .9, .8, fc=fc, ec="none"))
            text = {"SPECIFIC": SHORT.get(r.selected, ""), "AMBIGUOUS": f"{len(r.consistent)} consistent",
                    "UNRESOLVED": "mismatch" if r.reason == "MODEL_MISMATCH" else "indeterminate"}[r.decision]
            ax.text(j, i - .1, r.decision.title(), ha="center", va="center", fontsize=9.5, color="white", weight="semibold")
            ax.text(j, i + .18, text, ha="center", va="center", fontsize=8.2, color="white")
    ax.set_xlim(-.6, len(SCEN_ORDER) - .4), ax.set_ylim(len(DY_QUERIES) - .4, -.6)
    ax.set_xticks(range(len(SCEN_ORDER)),
                  [f"{k}\n{SCEN[k][0]:.0e} MPa\n{SCEN[k][1]:.0e} kg/s" if k != "REF" else "REF\n0.034 MPa\n0.018 kg/s"
                   for k in SCEN_ORDER], fontsize=8.5)
    ax.set_yticks(range(len(DY_QUERIES)), [QLABEL[q] for q in DY_QUERIES])
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)
    ax.set_title("Conditional / Hypothetical Bounds — restricted-universe decisions (all sensors)")
    footnote(fig, "Red = SPECIFIC on a hypothesis other than the configured one (configured mechanism unrepresented). "
                  "Full declared universe: 42/42 cells in this view UNRESOLVED (336/336 over all groups and clock bounds).")
    plt.subplots_adjust(left=0.24, right=0.98, top=0.9, bottom=0.18)
    save(fig, out, "FIG_C09_decision_transitions_restricted",
         "Decision of the frozen engine on the restricted (modelled-hypothesis) universe as declared bounds widen. "
         "Too-tight bounds give MODEL_MISMATCH, a finite window gives the correct SPECIFIC for SID 213, wide bounds give "
         "AMBIGUOUS; unrepresented mechanisms produce wrong SPECIFIC decisions. This is a conditional sensitivity analysis, "
         "not validated full-universe performance.",
         ["dy_decisions.json"], "Q5 — how do decisions depend on evidence assumptions?")


def fig_c10(plt, out, frozen_reasons, dec):
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    full = dec[(dec.universe == "full") & (dec.group == "all") & (dec.clock_bound_s == 1.0)]
    reasons = {}
    for r in full.itertuples():
        for h, why in r.indeterminate_reasons.items():
            reasons[why] = reasons.get(why, 0) + 1
    tot_exc = int(full.excluded.apply(len).sum())
    tot_con = int(full.consistent.apply(len).sum())
    labels = ["Invalid uncertainty (empty error vector)", "All declared hypotheses without adapter",
              "Unsupported after self-exclusion", "Declared, no adapter (SID 222, FAULT, DELAY)",
              "Excluded (conditional)", "Consistent (conditional)", "Indeterminate, adapter present"]
    frozen = [frozen_reasons["observations"], frozen_reasons["observations"], 0, 0, 0, 0, 0]
    cond = [0, 0, reasons.get("UNSUPPORTED_HYPOTHESIS", 0) - 0, 0, tot_exc, tot_con,
            sum(v for k, v in reasons.items() if k not in ("UNSUPPORTED_HYPOTHESIS",))]
    # split unsupported into self-excluded vs declared-unmodelled
    n_unmod = sum(1 for r in full.itertuples() for h in r.indeterminate if h in ("WITHDRAWAL_SID222", "COMPRESSOR_FAULT", "ACTUATOR_DELAY"))
    cond[2] = reasons.get("UNSUPPORTED_HYPOTHESIS", 0) - n_unmod
    cond[3] = n_unmod
    y = np.arange(len(labels))
    ax.barh(y - .19, frozen, height=.36, color=C["slate"], label="Frozen formal result (12 observations)")
    ax.barh(y + .19, cond, height=.36, color=C["teal"], label="Conditional full universe (6 queries × 7 scenarios)")
    for yi, a, b in zip(y, frozen, cond):
        if a:
            ax.text(a + 2, yi - .19, str(a), va="center", fontsize=9.5)
        if b:
            ax.text(b + 2, yi + .19, str(b), va="center", fontsize=9.5)
    ax.set_yticks(y, labels), ax.invert_yaxis()
    ax.set_xlabel("Count (frozen: observations, each blocked by both reasons; conditional: hypothesis checks)")
    ax.legend(loc="lower right"), ax.grid(axis="x"), ax.set_axisbelow(True)
    ax.set_title("Why formal D(Y) abstains: frozen versus conditional evidence")
    plt.subplots_adjust(left=0.36, right=0.97, top=0.9, bottom=0.17)
    footnote(fig, "Frozen: 12/12 UNRESOLVED (INVALID_MEASUREMENT → INVALID_UNCERTAINTY) and every declared hypothesis had adapter=None. "
                  f"Conditional results are {LABEL}.")
    save(fig, out, "FIG_C10_evidence_breakdown",
         "Reason codes behind abstention. The frozen result had two independent blockers: no observation bounds and no "
         "hypothesis adapters. Supplying hypothetical bounds and template adapters removes the first and part of the second, "
         "but unmodelled declared hypotheses keep every full-universe decision UNRESOLVED.",
         ["research_evidence.json", "phase13_integrated_timing/report.md", "dy_decisions.json"],
         "Q5 — why did the original D(Y) remain unresolved?")


def fig_c11(plt, out):
    rows = ["Causal source reproduction", "Mechanism discrimination", "Categorical localization ranking",
            "Sensor-dependent identifiability", "Conditional D(Y)", "Qualified D(Y)", "Fault classification",
            "Physical-distance localization", "Independent transfer"]
    cols = ["Implemented", "Descriptively\nsupported", "Conditionally\nsupported", "Validated", "Blocked"]
    status = {0: [0, 1, 3], 1: [0, 1], 2: [0, 1], 3: [0, 1], 4: [0, 2], 5: [0, 4], 6: [4], 7: [4], 8: [4]}
    notes = {0: "within modelled system", 1: "only with self/near-duplicate templates", 2: "1 outlet, near-duplicate",
             3: "flow branch meters", 4: "hypothetical bounds", 5: "no qualified bounds", 6: "no FAULT/DELAY truth",
             7: "no geometry", 8: "1 source family"}
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    for i in range(len(rows)):
        for j in range(len(cols)):
            on = j in status[i]
            fc = (C["red"] if j == 4 else C["navy"] if j == 3 else C["teal"]) if on else C["bg"]
            ax.add_patch(plt.Rectangle((j - .45, i - .38), .9, .76, fc=fc, ec=C["grid"], lw=1))
        ax.text(len(cols) - .35, i, notes[i], va="center", fontsize=9.5, color=C["slate"])
    ax.set_xlim(-.6, len(cols) + 1.6), ax.set_ylim(len(rows) - .5, -.6)
    ax.set_xticks(range(len(cols)), cols, fontsize=10), ax.xaxis.tick_top()
    ax.set_yticks(range(len(rows)), rows)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)
    plt.subplots_adjust(left=0.27, right=0.98, top=0.86, bottom=0.08)
    footnote(fig, "‘Validated’ for source reproduction means numerical agreement with the archived solver (≈2.4e-7 MPa), "
                  "not physical validation.")
    save(fig, out, "FIG_C11_capability_map",
         "Evidence status of each Center capability after this enhancement. Only source reproduction carries a "
         "verification beyond description, and it is numerical, not physical.",
         ["TAB_C08"], "Q6 — final established scope")


# ------------------------------------------------------------------------ driver

def build(analysis: Path, repo: Path, workspace: Path, out: Path):
    plt = style()
    figures, tables = out / "figures", out / "tables"
    figures.mkdir(parents=True, exist_ok=True), tables.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((analysis / "execution_manifest.json").read_text(encoding="utf8"))
    rec = pd.read_json(analysis / "recognition.json")
    loc = pd.read_json(analysis / "location.json")
    pairs = pd.read_csv(analysis / "pair_contrasts.csv")
    thr = pd.read_csv(analysis / "dy_thresholds.csv")
    dec = pd.read_json(analysis / "dy_decisions.json")
    facts = design_facts(workspace)
    frozen = json.loads((repo / "03_results/validation/final_research/research_evidence.json").read_text(encoding="utf8"))
    n_hyp = len(frozen["formal_decision"]["diagnostic"]["certificate"]["results"])
    frozen_reasons = dict(observations=12, hypotheses_without_adapter=n_hyp)

    md = {}
    md["C01"] = export(table_c01(manifest, facts), tables, "TAB_C01", "Controlled capture qualification",
                       "All captures: ode14x, 0.2 s fixed step, 0–20,000 s, 13 sensors. One Center source family; "
                       "zero verified independent generating families. PS3 and PS10 are bitwise identical; PS5 and PS7 "
                       "show no response to any withdrawal.")
    c02 = table_c02(rec)
    md["C02"] = export(c02, tables, "TAB_C02", "Mechanism recognition (frozen vs own template excluded)",
                       "All sensors, 30 s prefix from the retrospective controlled anchor, ±1 s shared shift. "
                       "Scores are normalized B3 RMS (dimensionless).")
    cm, _ = confusion(rec)
    cm_df = cm.reset_index().rename(columns={"index": "configured"})
    cm_df["configured"] = cm_df["configured"].map(SHORT)
    cm_df.columns = ["configured"] + [SHORT[c] for c in cm.columns]
    md["C02b"] = export(cm_df, tables, "TAB_C02b", "Count confusion matrix, own template excluded (7 queries)",
                        "Counts from one source family; not rates. QUIET (constructed zero) is excluded.")
    md["C03"] = export(table_c03(loc), tables, "TAB_C03", "Categorical location ranking",
                       "loto = frozen withdrawal templates minus the query's own; loto_replicate adds the alternate-profile "
                       "SID 213 capture as a second SID 213 template. Unsupported = true outlet has no independent template.")
    md["C04"] = export(table_c04(pairs, loc), tables, "TAB_C04", "Sensor-group identifiability of outlet pairs",
                       "Native contrasts are the largest absolute template difference at the best shift within ±1 s, "
                       "reported separately in MPa and kg/s. B3 combines normalized channels with equal weights "
                       "(frozen scaling: pre-1000 s RMS of the SID 213 control per channel).")
    md["C05"] = export(table_c05(thr[thr.clock_bound_s == 1.0]), tables, "TAB_C05",
                       "Conditional D(Y) exclusion and feasibility onsets",
                       f"{LABEL}. Single-kind groups give exact one-dimensional onsets. ±1 s clock, 30 s prefix.")
    md["C06"] = export(table_c06(dec), tables, "TAB_C06", "Diagnostic outcomes by universe and bound scenario",
                       f"{LABEL}. All sensors, ±1 s. eps split equally between observation and model; the split "
                       "does not change any decision (gate_split_invariance.csv).")
    md["C07"] = export(table_c07(rec, loc, dec), tables, "TAB_C07", "Baseline comparison (unlike outputs kept separate)",
                       "Rankings, location ranks and set-valued decisions are different output types and are not pooled.")

    loto = rec[(rec.group == "all") & (rec.clock_bound_s == 1.0) & (rec.condition == "loto") & (rec["query"] != "QUIET")]
    sup = loto[loto.status != "UNSUPPORTED"]
    full = dec[(dec.universe == "full") & (dec.group == "all") & (dec.clock_bound_s == 1.0)]
    rest = dec[(dec.universe == "restricted") & (dec.group == "all") & (dec.clock_bound_s == 1.0)]
    wrong = rest[(rest.decision == "SPECIFIC") & (rest.selected != rest.true_hypothesis)]
    right = rest[(rest.decision == "SPECIFIC") & (rest.selected == rest.true_hypothesis)]
    stats = dict(
        loto_mech=f"{(sup.status == 'CORRECT').sum()}/{len(sup)} supported queries agree; "
                  f"{(loto.status == 'UNSUPPORTED').sum()} unsupported; frozen library 7/7 with self or near-duplicate templates",
        loc="SID 213 ranked 1st for 2/2 supported queries (all four sensor groups); SID 312 and SID 215 unsupported",
        sensor="B3 flow share ≥ 0.97 for every outlet pair; pressure contrasts 1.1–5.5 kPa; withholding MFS3 cuts the "
               "SID 213 margin 0.028→0.0021 while the correct/runner-up ratio rises 1,030×→2,676×; pressure alone 569×",
        window="pressure eps ∈ [2.5e-6, 5.1e-4) MPa; flow eps ∈ [6.8e-4, 0.69) kg/s",
        wrong=f"{len(wrong)} wrong vs {len(right)} correct SPECIFIC cells (all sensors, 7 scenarios × 6 queries)",
        full=f"{len(full)}/{len(full)} UNRESOLVED (INDETERMINATE_HYPOTHESES)")
    md["C08"] = export(table_c08(stats), tables, "TAB_C08", "Research claim qualification",
                       "Validation levels follow the project vocabulary. Registered RQ1/H1/RQ2 outcomes are preserved.")

    fig_c01(plt, figures, facts, None)
    fig_c02(plt, figures, cm)
    fig_c03(plt, figures, rec)
    fig_c04(plt, figures, loc)
    fig_c05(plt, figures, loc)
    fig_c06(plt, figures, pairs)
    fig_c07(plt, figures, dec)
    fig_c08(plt, figures, thr)
    fig_c09(plt, figures, dec)
    fig_c10(plt, figures, frozen_reasons, dec)
    fig_c11(plt, figures)
    (out / "tables_bundle.md").write_text("\n\n".join(md.values()), encoding="utf8")
    (out / "summary_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf8")
    normalize_lf(out)
    rows = [dict(path=p.relative_to(out).as_posix(), sha256=sha256_file(p)) for p in sorted(out.rglob("*"))
            if p.is_file() and p.name != "SHA256SUMS.csv"]
    pd.DataFrame(rows).to_csv(out / "SHA256SUMS.csv", index=False, lineterminator="\n")
    return stats


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--analysis", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--repository", type=Path, default=Path("."))
    p.add_argument("--workspace", type=Path, default=os.environ.get("H2PRISM_CENTER_WORKSPACE"))
    a = p.parse_args()
    if a.workspace is None:
        raise SystemExit("pass --workspace or set H2PRISM_CENTER_WORKSPACE")
    print(json.dumps(build(a.analysis, a.repository, Path(a.workspace), a.output), indent=2))


if __name__ == "__main__":
    main()
