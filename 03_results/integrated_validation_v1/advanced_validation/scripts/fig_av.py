"""Advanced-validation figures AV-F01..AV-F16 (Q1 style; one function per figure; numbers from analysis/tables).

Usage (repository root): python 03_results/integrated_validation_v1/advanced_validation/scripts/fig_av.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

AV = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AV.parent / "publication_q1/scripts"))
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

from q1fig import finish  # noqa: E402
from q1style import C, figure, setup, title, xgrid, ygrid  # noqa: E402

A, T, B = AV / "analysis", AV / "tables", AV / "benchmarks"
H1A = AV.parent / "h1_validation/analysis"
OUT = AV / "figures"
MOD = "fig_av"
EXPL = "EXPLORATORY — post hoc on windows inspected in R2"
COND = "CONDITIONAL HYPOTHETICAL BOUNDS — not calibrated uncertainty"
LIM_R2 = ("Simulated H2-SimNet topologies; inspected outer-test windows; 17 independent scenario templates; 91.7 % of "
          "classifier errors in runs with disputed attribution (D1 pending).")
LIM_C = ("Center controlled simulation (air-like gas model, one source family); six captures viewed under several "
         "declared conditions — counts, not rates; hypothetical bounds.")
MSTY = {"A_classifier_no_abstention": dict(color=C["slate"], marker="X", label="A: classifier, no abstention"),
        "confidence_no_evidence_guard": dict(color=C["burgundy"], marker="D", ls=":", label="B: confidence abstention (conventional)"),
        "confidence": dict(color=C["ochre"], marker="^", ls="-.", label="Confidence + evidence guard"),
        "margin": dict(color=C["ochre"], marker="v", ls=(0, (1, 1)), label="Margin + evidence guard"),
        "neg_entropy": dict(color=C["ochre"], marker="<", ls=(0, (3, 1, 1, 1)), label="−Entropy + evidence guard"),
        "D_only": dict(color=C["blue"], marker="P", ls="--", label="D(x) only + evidence guard"),
        "s_C_minus_D": dict(color=C["navy"], marker="s", ls="--", label="s_C−D (meta-score without D(x))"),
        "s_C": dict(color=C["teal"], marker="o", ls="-", label="s_C (H₂-PRISM evidence policy)")}
OUTC = [("SPECIFIC_CORRECT", "SPECIFIC, correct", C["teal"], None), ("SPECIFIC_WRONG", "SPECIFIC, wrong", C["burgundy"], "xx"),
        ("AMBIGUOUS_TRUTH_IN", "AMBIGUOUS, truth in set", C["ochre"], None),
        ("AMBIGUOUS_TRUTH_OUT", "AMBIGUOUS, truth not in set", C["ochre"], "\\\\"),
        ("UNRESOLVED_MODEL_MISMATCH", "UNRESOLVED: all supported excluded", C["slate"], "///"),
        ("UNRESOLVED_INDETERMINATE_HYPOTHESES", "UNRESOLVED: indeterminate hypotheses", C["navy"], None)]


def meta(fid, stem, fn, ttl, q, sources, cap, lim, ver="values read from advanced_validation analysis outputs"):
    return dict(id=fid, stem=f"{fid}_{stem}", function=fn, module=MOD, title=ttl, question=q, sources=sources, caption=cap,
                limitation=lim, study="Advanced", verification=ver, caption_dir=AV / "captions",
                script_dir="advanced_validation/scripts")


def load():
    d = pd.read_csv(A / "dy_experiment_runs.csv", keep_default_na=False, na_values=[""])
    d["selected"] = d.selected.fillna("")
    return {"acc": pd.read_csv(A / "av_r2_wrong_specific_accounting.csv"), "cls": pd.read_csv(A / "av_r2_wrong_specific_by_class.csv"),
            "neg": pd.read_csv(A / "av_r2_negative_control_normal.csv"), "runs": d,
            "summ": pd.read_csv(A / "dy_outcome_summary.csv"), "iso": pd.read_csv(A / "dy_pairwise_isolability.csv"),
            "minset": pd.read_csv(A / "dy_minimum_sensor_sets.csv"), "loc": pd.read_csv(A / "localization_cases.csv"),
            "ev": pd.read_csv(A / "dy_evidence_availability.csv"), "dy": pd.read_csv(B / "dy_scaling.csv"),
            "dx": pd.read_csv(B / "dx_scaling.csv"), "hw": pd.read_csv(B / "hardware.csv", index_col=0)["value"],
            "a16": pd.read_csv(T / "A16a.csv"), "a19": pd.read_csv(T / "A19.csv"), "a12": pd.read_csv(T / "A12.csv"),
            "a13": pd.read_csv(T / "A13.csv"), "a07": pd.read_csv(T / "A07.csv")}


def stamp(ax, text):
    ax.text(0.0, 1.02, text, transform=ax.transAxes, fontsize=10, color=C["burgundy"], fontstyle="italic", va="bottom")


def stacked(ax, rows, labels, total=None):
    for i, cnt in enumerate(rows):
        left, tot = 0, total or sum(cnt.get(k, 0) for k, *_ in OUTC)
        for k, name, col, h in OUTC:
            v = cnt.get(k, 0)
            if v:
                ax.barh(i, v / tot, left=left, color=col, hatch=h, edgecolor=C["white"], height=0.6, zorder=3)
                if v / tot >= 0.06:
                    ax.text(left + v / tot / 2, i, str(int(v)), ha="center", va="center", fontsize=9.5,
                            bbox=dict(facecolor=C["white"], edgecolor="none", pad=1.0))
                left += v / tot
    ax.set_yticks(range(len(labels)), labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    xgrid(ax)


def outcome_legend(fig, used=None, ncol=3):
    hs = [Patch(facecolor=c, hatch=h, edgecolor=C["white"], label=n) for k, n, c, h in OUTC if used is None or k in used]
    fig.legend(handles=hs, loc="outside lower center", ncol=ncol, fontsize=9.5)


def plot_av_reliability_coverage(d, out):
    a = d["acc"]
    fig = figure()
    title(fig, "Selective risk across attainable coverage, with the no-abstention reference")
    ax = fig.add_subplot()
    for m, st in MSTY.items():
        g = a[a.method == m].sort_values("coverage_requested")
        if m == "A_classifier_no_abstention":
            ax.scatter(g.coverage, g.wrong_specific_risk, s=90, color=st["color"], marker=st["marker"], zorder=4, label=st["label"])
        else:
            ax.plot(g.coverage, g.wrong_specific_risk, color=st["color"], marker=st["marker"], ls=st["ls"], lw=1.4, ms=6,
                    label=st["label"], zorder=3)
    ax.axvspan(0.258, 0.995, color=C["grid"], zorder=1, lw=0)
    ax.text(0.62, 0.47, "not attainable in every outer fold\n(Center maximum 0.258)", ha="center", fontsize=10, color=C["slate"])
    ax.set_xlim(0, 1.03)
    ax.set_ylim(-0.02, 0.5)
    ax.set_xlabel("Specific-diagnosis coverage (pooled over three outer folds; 27,993 windows)")
    ax.set_ylabel("Wrong-specific risk (wrong / SPECIFIC)")
    ygrid(ax)
    stamp(ax, EXPL)
    fig.legend(loc="outside right center", fontsize=9.5)
    a0 = a[a.method == "A_classifier_no_abstention"].iloc[0]
    cap = (f"Wrong-specific risk of each registered selection score at the five fixed coverage points inside the shared "
           f"attainable region, and of the frozen classifier without abstention (all {int(a0.n_specific):,} windows: risk "
           f"{a0.wrong_specific_risk:.3f}). Grey: coverage not attainable in every outer fold under the registered flags. No "
           "curve is extrapolated. Values and denominators in A01/A02a.")
    return finish(fig, meta("AV-F01", "reliability_coverage", "plot_av_reliability_coverage", "Matched reliability–coverage frontier",
                            "How does wrong-specific risk change with coverage for each comparable policy?",
                            ["advanced_validation/analysis/av_r2_wrong_specific_accounting.csv"], cap, LIM_R2), out)


def plot_av_false_specific_equal_coverage(d, out):
    a = d["acc"]
    order = ["confidence_no_evidence_guard", "confidence", "margin", "neg_entropy", "D_only", "s_C_minus_D", "s_C"]
    fig = figure()
    title(fig, "Wrong specific diagnoses at equal coverage, split by run attribution")
    axs = fig.subplots(1, 2, sharey=True)
    for ax, c in zip(axs, (0.10, 0.25)):
        g = a[np.isclose(a.coverage_requested, c)].set_index("method").loc[order]
        y = np.arange(len(order))
        ax.barh(y, g.wrong_in_disputed_runs, color=C["burgundy"], hatch="xx", edgecolor=C["white"], height=0.6, zorder=3,
                label="in runs with disputed attribution")
        ax.barh(y, g.wrong_in_undisputed_runs, left=g.wrong_in_disputed_runs, color=C["ochre"], edgecolor=C["white"], height=0.6,
                zorder=3, label="in runs with consistent attribution")
        for i, r in enumerate(g.itertuples()):
            ax.text(r.n_wrong_specific + 40, i, f"{r.n_wrong_specific:,}/{r.n_specific:,} ({r.wrong_specific_risk:.3f})",
                    va="center", fontsize=9)
        ax.set_title(f"coverage {c:.2f} ({int(g.n_specific.iloc[0]):,} SPECIFIC each)", fontsize=12)
        ax.set_xlim(0, 4200)
        ax.set_xlabel("Wrong SPECIFIC decisions")
        xgrid(ax)
    axs[0].set_yticks(range(len(order)), [MSTY[m]["label"] for m in order])
    axs[0].invert_yaxis()
    fig.legend(*axs[0].get_legend_handles_labels(), loc="outside lower center", ncol=2, title=EXPL)
    s = a[(a.method == "s_C") & np.isclose(a.coverage_requested, 0.25)].iloc[0]
    cap = ("Counts of wrong SPECIFIC decisions with denominator and risk at two fixed coverage points (identical SPECIFIC counts "
           f"per method). Every wrong SPECIFIC decision of s_C ({int(s.n_wrong_specific)} at 0.25) lies in runs whose topology "
           "attribution is disputed; the guarded conventional scores add 650 errors from the one undisputed Downstream NORMAL run, "
           "which the evidence policy withholds. Counts are comparable only because population and coverage are identical.")
    return finish(fig, meta("AV-F02", "false_specific_equal_coverage", "plot_av_false_specific_equal_coverage",
                            "False-specific risk at equal coverage", "At equal coverage, how many wrong SPECIFIC decisions does each policy make, and where?",
                            ["advanced_validation/analysis/av_r2_wrong_specific_accounting.csv"], cap, LIM_R2), out)


def plot_av_error_attribution(d, out):
    c = d["cls"]
    order = ["A_classifier_no_abstention", "confidence_no_evidence_guard", "confidence", "D_only", "s_C_minus_D", "s_C"]
    cls = ["NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"]
    fig = figure()
    title(fig, "Where wrong SPECIFIC decisions fall by true class")
    ax = fig.add_subplot()
    for i, m in enumerate(order):
        cov = 1.0 if m.startswith("A_") else 0.25
        g = c[(c.method == m) & np.isclose(c.coverage_requested, cov)].set_index("true_class")
        for j, k in enumerate(cls):
            r = g.loc[k]
            risk = r.wrong_specific_risk
            shade = 0 if np.isnan(risk) else risk
            ax.add_patch(Rectangle((j, i), 0.96, 0.9, facecolor=tuple(np.array([1, 1, 1]) + (np.array([0.643, 0.290, 0.290]) - 1) * shade),
                                   edgecolor=C["grid"], lw=0.6))
            ax.text(j + 0.48, i + 0.45, f"{int(r.n_wrong_specific):,} / {int(r.n_specific):,}", ha="center", va="center", fontsize=10,
                    bbox=dict(facecolor=C["white"], edgecolor="none", pad=1.0))
    ax.set_xlim(0, 4)
    ax.set_ylim(len(order), 0)
    ax.set_xticks(np.arange(4) + 0.48, ["Normal", "Leak", "Compressor fault", "Compressor delay"])
    ax.xaxis.tick_top()
    ax.set_yticks(np.arange(len(order)) + 0.45, [MSTY[m]["label"] + (" (coverage 1.0)" if m.startswith("A_") else " (0.25)") for m in order])
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_xlabel(EXPL + "; cell shade = wrong-specific risk; cell text = wrong / SPECIFIC", fontsize=10,
                  color=C["burgundy"], fontstyle="italic")
    cap = ("Wrong / SPECIFIC decisions per true class for the classifier without abstention (all windows) and for each policy at "
           "coverage 0.25. LEAK errors (LEAK → NORMAL in Center) dominate every policy; the NORMAL errors of the conventional "
           "scores (NORMAL → LEAK) come from one template. Class supports: NORMAL 1,995, LEAK 21,921, FAULT 3,984, DELAY 93 windows "
           "from 1, 13, 2 and 1 scenario templates.")
    return finish(fig, meta("AV-F03", "error_attribution_by_class", "plot_av_error_attribution", "Classification error attribution",
                            "Which event classes produce the wrong SPECIFIC decisions?",
                            ["advanced_validation/analysis/av_r2_wrong_specific_by_class.csv"], cap, LIM_R2), out)


def _counts(g):
    return g.outcome.value_counts().to_dict()


def plot_av_library_completeness(d, out):
    r = d["runs"]
    r = r[r.experiment == "E4_library"]
    variants = [("full", "Full declared universe (9 hypotheses, 3 without adapter)"), ("restricted", "Restricted: modelled hypotheses only"),
                ("minus_NORMAL", "Restricted minus the normal-operation rival"), ("minus_true", "Restricted minus the true hypothesis")]
    fig = figure()
    title(fig, "Removing the true hypothesis turns abstention into wrong SPECIFIC decisions")
    ax = fig.add_subplot()
    stacked(ax, [_counts(r[r.config == v]) for v, _ in variants], [lab for _, lab in variants])
    ax.set_xlabel("Share of 42 decisions (6 queries × 7 declared bound scenarios, all sensors, ±1 s)")
    stamp(ax, COND)
    outcome_legend(fig)
    s = d["summ"].set_index(["experiment", "config_family"])
    mt, rs = s.loc[("E4_library", "minus_true")], s.loc[("E4_library", "restricted")]
    cap = (f"Formal D(Y) outcomes for four hypothesis libraries. Full declared universe: all UNRESOLVED. Restricted: "
           f"{int(rs.specific_correct)} correct and {int(rs.specific_wrong)} wrong SPECIFIC. Removing the normal-operation rival "
           f"removes both wrong decisions (they selected that rival). Removing the true hypothesis of the two supported queries "
           f"gives {int(mt.specific_wrong)} wrong SPECIFIC and {int(mt.ambiguous)} ambiguity sets without the truth; the rest "
           "abstain as MODEL_MISMATCH. False specificity is unavoidable when the truth is absent and a rival remains consistent.")
    return finish(fig, meta("AV-F04", "library_completeness", "plot_av_library_completeness", "Hypothesis-library completeness and false specificity",
                            "How does library completeness change formal decisions?", ["advanced_validation/analysis/dy_experiment_runs.csv (E4)"],
                            cap, LIM_C), out)


def plot_av_status_transitions(d, out):
    r = d["runs"]
    e1 = r[r.experiment == "E1_sensors"]
    base = e1[e1.config == "all"].set_index(["query", "scenario"]).status_json
    S = ["FEASIBLE", "EXCLUDED", "INDETERMINATE"]
    M = np.zeros((3, 3), int)
    for _, x in e1[e1.config != "all"].iterrows():
        b = {h: s for h, (s, _) in json.loads(base.loc[(x["query"], x.scenario)]).items()}
        a = {h: s for h, (s, _) in json.loads(x.status_json).items()}
        for h in b:
            if h in a:
                M[S.index(b[h]), S.index(a[h])] += 1
    allowed = {(0, 0), (1, 0), (1, 1), (1, 2), (2, 2), (2, 0)}
    fig = figure()
    title(fig, "Removing sensors never creates a formal exclusion or removes a feasible hypothesis")
    ax = fig.add_subplot()
    for i in range(3):
        for j in range(3):
            ok = (i, j) in allowed
            ax.add_patch(Rectangle((j, i), 0.96, 0.92, facecolor=C["white"] if ok else "#F3E3E3", hatch=None if ok else "//",
                                   edgecolor=C["text"] if not ok else C["grid"], lw=0.8))
            ax.text(j + 0.48, i + 0.46, f"{M[i, j]:,}", ha="center", va="center", fontsize=13,
                    color=C["text"], fontweight="bold" if M[i, j] else "normal",
                    bbox=dict(facecolor=C["white"], edgecolor="none", pad=1.5))
    ax.set_xlim(0, 3)
    ax.set_ylim(3, 0)
    ax.set_xticks(np.arange(3) + 0.48, [f"{s.capitalize()}\nafter removal" for s in S])
    ax.set_yticks(np.arange(3) + 0.46, [f"{s.capitalize()}\nwith all 13 channels" for s in S])
    ax.xaxis.tick_top()
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    fig.legend(handles=[Patch(facecolor="#F3E3E3", hatch="//", edgecolor=C["text"], label="Forbidden transition (would violate monotonicity)")],
               loc="outside lower center")
    I = pd.read_csv(A / "dy_invariant_checks.csv")
    cap = (f"Hypothesis-status transitions between the all-channel run and each of the 78 reduced sensor configurations "
           f"({int(M.sum()):,} hypothesis checks, 6 queries × 4 bound scenarios). Forbidden cells (hatched) are all zero. Across all "
           f"invariant tests — sensor removal, clock-bound widening and bound widening on the frozen grid — "
           f"{int(I.hypotheses_compared.sum()):,} paired hypothesis checks show {int(I.violations.sum())} violations (A04a).")
    return finish(fig, meta("AV-F05", "dy_status_transitions", "plot_av_status_transitions", "Formal D(Y) decision-state transitions",
                            "Does the formal engine respect evidence monotonicity when information is removed?",
                            ["advanced_validation/analysis/dy_experiment_runs.csv", "dy_invariant_checks.csv"], cap,
                            "Mathematical property of the engine on fixed models and frozen bounds; not a physical validation."), out)


def plot_av_localization(d, out):
    a = d["a07"]
    fig = figure()
    title(fig, "Selective localization: at matched coverage neither policy assigns a wrong outlet")
    ax = fig.add_subplot()
    y = np.arange(len(a))
    corr = a.location_specific - a.wrong_location
    ax.barh(y, corr / a.cases, color=C["teal"], height=0.55, zorder=3, label="Correct outlet issued")
    ax.barh(y, a.wrong_location / a.cases, left=corr / a.cases, color=C["burgundy"], hatch="xx", edgecolor=C["white"], height=0.55,
            zorder=3, label="Wrong outlet issued")
    ax.barh(y, 1 - a.location_specific / a.cases, left=a.location_specific / a.cases, color=C["grid"], height=0.55, zorder=3,
            label="No outlet issued (abstain or non-location decision)")
    for i, r in enumerate(a.itertuples()):
        ax.text(1.01, i, f"{r.location_specific}/{r.cases} issued; {r.wrong_location} wrong", va="center", fontsize=10)
    ax.set_yticks(y, ["Nearest template, no abstention", "Nearest template, top-2 by margin", "Formal D(Y), restricted universe"])
    ax.invert_yaxis()
    ax.set_xlim(0, 1.32)
    ax.set_xlabel("Share of withdrawal cases")
    xgrid(ax)
    stamp(ax, "EXPLORATORY H-Loc — 4 withdrawal queries, 1 outlet with independent support")
    fig.legend(loc="outside lower center", ncol=3)
    cap = ("Location decisions for the four withdrawal queries (SID 213, its alternate-profile replicate, SID 312, SID 215). The "
           "nearest-template rule always names an outlet and is wrong for SID 312 and SID 215, whose own outlet has no independent "
           "template. Matched to the formal policy's coverage (0.5), a margin-ranked nearest-template rule and formal D(Y) both name "
           "only SID 213, correctly. Only one outlet has independent support, so no localization rate generalises.")
    return finish(fig, meta("AV-F06", "selective_localization", "plot_av_localization", "Localization ranking and eligibility",
                            "Does evidence qualification reduce wrong outlet assignments at matched coverage?",
                            ["advanced_validation/tables/A07.csv", "advanced_validation/analysis/localization_cases.csv"], cap, LIM_C), out)


def plot_av_isolability(d, out):
    iso = d["iso"]
    hyps = ["HN", "H213", "H312", "H215", "HP55", "HT59"]
    names = {"HN": "Normal", "H213": "W·213", "H312": "W·312", "H215": "W·215", "HP55": "P-cmd 55", "HT59": "Timing 59"}
    cfgs = [("all", "All 13 channels"), ("pressure_only", "Pressure only (10)"), ("flow_only", "Flow only (3)")]
    fig = figure()
    title(fig, "Which hypothesis pairs can be formally separated depends on the sensors")
    axs = fig.subplots(1, 3)
    for ax, (cfg, lab) in zip(axs, cfgs):
        g = iso[(iso.scenario == "REF") & (iso.config == cfg)]
        for _, r in g.iterrows():
            i, j = hyps.index(r.hyp_a), hyps.index(r.hyp_b)
            for (x, y) in ((j, i), (i, j)):
                ax.add_patch(Rectangle((x, y), 0.94, 0.94, facecolor=C["teal"] if r.isolable else "#F3E3E3",
                                       hatch=None if r.isolable else "//", edgecolor=C["white"] if r.isolable else C["burgundy"], lw=0.6))
        for k in range(6):
            ax.add_patch(Rectangle((k, k), 0.94, 0.94, facecolor=C["grid"], edgecolor=C["white"]))
        ax.set_xlim(0, 6)
        ax.set_ylim(6, 0)
        ax.set_aspect("equal")
        ax.set_xticks(np.arange(6) + 0.47, [names[h] for h in hyps], rotation=45, ha="left", fontsize=9)
        ax.xaxis.tick_top()
        ax.set_yticks(np.arange(6) + 0.47, [names[h] for h in hyps] if cfg == "all" else [""] * 6, fontsize=9.5)
        ax.tick_params(length=0)
        ax.set_xlabel(f"{lab}: {int(g.isolable.sum())}/15 pairs separable", fontsize=11)
        for sp in ax.spines.values():
            sp.set_visible(False)
    fig.legend(handles=[Patch(facecolor=C["teal"], label="Formally separable (no observation fits both)"),
                        Patch(facecolor="#F3E3E3", hatch="//", edgecolor=C["burgundy"], label="Not separable at these bounds")],
               loc="outside lower center", ncol=2)
    m = d["minset"].set_index("scenario").loc["REF"]
    cap = ("Template-level pairwise isolability at the REF bounds (0.0344 MPa, 0.0182 kg/s total) with ±1 s alignment: a pair is "
           "separable if, for every pair of admissible shifts, some coordinate differs by more than twice the bound. Normal operation "
           f"and the SID 215 withdrawal are not separable even with all channels. Exhaustive search: {int(m.min_channels)} channels "
           f"({m.minimal_sets}) preserve all {int(m.isolable_pairs_full_set)} separable pairs (A16b). Conditional on declared bounds.")
    return finish(fig, meta("AV-F07", "pairwise_isolability", "plot_av_isolability", "Sensor-dependent pairwise isolability",
                            "Which event pairs are distinguishable under each sensor configuration?",
                            ["advanced_validation/analysis/dy_pairwise_isolability.csv", "dy_minimum_sensor_sets.csv"], cap, LIM_C), out)


def plot_av_missing_sensor(d, out):
    r = d["runs"]
    r = r[r.experiment == "E1_sensors"].copy()
    r["fam"] = r.config.str.replace(r"_\d\d$", "", regex=True)
    rows = [("all", "All 13 channels"), ("drop_PS1", "Without PS1 (any one PS behaves alike)"), ("drop_MFS1", "Without MFS1"),
            ("drop_MFS3", "Without MFS3"), ("outage_branch_SID213(MFS3,PS1)", "SID 213 branch outage (MFS3, PS1)"),
            ("outage_branch_SID215(PS4,PS8,PS9)", "SID 215 branch outage (PS4, PS8, PS9)"), ("pressure_only", "Pressure only (10)"),
            ("flow_only", "Flow only (3)"), ("random_drop3", "Random: 3 of 13 removed (20 masks)"),
            ("random_drop4", "Random: 4 removed (20 masks)"), ("random_drop7", "Random: 7 removed (20 masks)")]
    fig = figure(h=6.2)
    title(fig, "Losing pressure sensing increases false specificity; losing MFS3 forces ambiguity")
    ax = fig.add_subplot()
    stacked(ax, [_counts(r[r.fam == k]) for k, _ in rows], [lab for _, lab in rows])
    ax.set_xlabel("Share of decisions (24 per configuration; 480 per random family)")
    stamp(ax, COND)
    outcome_legend(fig)
    s = d["summ"].set_index("config_family")
    cap = (f"Formal D(Y) outcomes under predeclared sensor losses (restricted universe, ±1 s, S3, S4, S5, REF). Flow-only sensing "
           f"raises wrong SPECIFIC from {int(s.loc['all', 'specific_wrong'])} to {int(s.loc['flow_only', 'specific_wrong'])} of 24; "
           f"without MFS3 the correct SPECIFIC decisions drop from {int(s.loc['all', 'specific_correct'])} to "
           f"{int(s.loc['drop_MFS3', 'specific_correct'])} and become ambiguity sets. Removing any single pressure sensor other than "
           "those of the SID 215 branch changes nothing. Ambiguity sets without the truth (hatched ochre) are not safe outcomes.")
    return finish(fig, meta("AV-F08", "missing_sensor_robustness", "plot_av_missing_sensor", "Missing-sensor robustness",
                            "What happens to formal decisions when pressure or flow sensors are lost?",
                            ["advanced_validation/analysis/dy_experiment_runs.csv (E1)"], cap, LIM_C), out)


def plot_av_timing(d, out):
    r = d["runs"]
    fig = figure()
    title(fig, "Delay beyond the admissible clock bound leads to abstention, not to new certainty")
    axs = fig.subplots(1, 2, sharex=False)
    e2 = r[r.experiment == "E2_clock_bound"]
    taus = sorted(e2.bound.unique())
    stacked(axs[0], [_counts(e2[e2.bound == t]) for t in taus], [f"τ = {t:g} s" for t in taus])
    axs[0].set_title("Widened admissible clock bound, no delay", fontsize=12)
    e3 = r[r.experiment == "E3_delay"].copy()
    e3["dly"] = (e3.lag * 0.2).round(1)
    labs, rows = [], []
    for dl in (0, 1, 2, 5, 10):
        for tau in sorted(e3[e3.dly == dl].bound.unique()):
            labs.append(f"delay {dl:g} s, τ = {tau:g} s")
            rows.append(_counts(e3[(e3.dly == dl) & (e3.bound == tau)]))
    stacked(axs[1], rows, labs)
    axs[1].set_title("Fixed observation delay", fontsize=12)
    for ax in axs:
        ax.set_xlabel("Share of 24 decisions")
    outcome_legend(fig, used={"SPECIFIC_CORRECT", "SPECIFIC_WRONG", "UNRESOLVED_MODEL_MISMATCH"})
    cap = ("Left: widening the admissible clock-shift set from 0 to 10 s leaves every decision unchanged (no new exclusions, as "
           "required). Right: an observation delay of 2 s or more with τ = 1 s removes every correct SPECIFIC decision "
           "(UNRESOLVED: all supported hypotheses excluded); declaring τ equal to the delay restores them. The two wrong SPECIFIC "
           "decisions (SID 215 → normal operation) are delay-invariant because the normal-operation template is constant. "
           "Jitter was not tested (no jitter model).")
    return finish(fig, meta("AV-F09", "timing_robustness", "plot_av_timing", "Timing-alignment robustness",
                            "How do formal decisions respond to clock uncertainty and to observation delay?",
                            ["advanced_validation/analysis/dy_experiment_runs.csv (E2, E3)"], cap, LIM_C), out)


def plot_av_evidence_availability(d, out):
    r = d["runs"]
    r = r[r.experiment == "E1_sensors"]
    ns = sorted(r.n_channels.unique(), reverse=True)
    fig = figure()
    title(fig, "Evidence availability versus formal decision outcome")
    ax = fig.add_subplot()
    stacked(ax, [_counts(r[r.n_channels == n]) for n in ns],
            [f"{n} channels ({r[r.n_channels == n].config.nunique()} config., {len(r[r.n_channels == n])} decisions)" for n in ns])
    ax.set_xlabel("Share of decisions")
    stamp(ax, COND)
    outcome_legend(fig)
    cap = ("All predeclared sensor configurations grouped by the number of available channels (an objective information axis; "
           "configurations with the same count differ in which channels remain, see AV-F08). Correct SPECIFIC decisions become "
           "rarer and ambiguity more frequent as channels are removed, but wrong SPECIFIC decisions do not fall monotonically: "
           "the 3-channel flow-only set has the highest wrong-specific share. Channel identity matters more than count.")
    return finish(fig, meta("AV-F10", "evidence_availability", "plot_av_evidence_availability", "Evidence availability versus decision outcomes",
                            "Does less evidence lead to abstention or to false certainty?",
                            ["advanced_validation/analysis/dy_experiment_runs.csv (E1)", "dy_evidence_availability.csv"], cap, LIM_C), out)


def plot_av_negative_control(d, out):
    n = d["neg"]
    order = ["A_classifier_no_abstention", "confidence_no_evidence_guard", "confidence", "D_only", "s_C_minus_D", "s_C"]
    fig = figure()
    title(fig, "False leak attribution on normal operation (R2 negative control)")
    ax = fig.add_subplot()
    y = np.arange(len(order))
    for j, c in enumerate((0.10, 0.25)):
        g = n[np.isclose(n.coverage_requested, c) | ((n.method == "A_classifier_no_abstention") & np.isclose(n.coverage_requested, 1.0))]
        g = g.drop_duplicates("method").set_index("method").loc[order]
        ax.barh(y + (j - 0.5) * 0.36, g.false_leak_calls, height=0.34, color=[C["burgundy"], C["navy"]][j],
                hatch=[None, "//"][j], edgecolor=C["white"], zorder=3, label=f"coverage {c:.2f} (A: all windows)")
        for i, r in enumerate(g.itertuples()):
            ax.text(r.false_leak_calls + 8, i + (j - 0.5) * 0.36, f"{r.false_leak_calls} of {r.normal_specific} SPECIFIC", va="center", fontsize=8.5)
    ax.set_yticks(y, [MSTY[m]["label"] for m in order])
    ax.invert_yaxis()
    ax.set_xlim(0, 800)
    ax.set_xlabel(f"False LEAK calls among SPECIFIC decisions on true NORMAL windows (of {int(n.normal_windows.iloc[0]):,})")
    xgrid(ax)
    stamp(ax, EXPL + " — all NORMAL windows come from ONE scenario template")
    fig.legend(loc="outside lower center", ncol=2)
    cap = ("Wrong LEAK attributions on the 1,995 NORMAL windows (one normal-operation template simulated in three topologies). "
           "The classifier without abstention calls 662 of them LEAK; conventional confidence abstention still issues 655 at "
           "coverage 0.25; the evidence policies (s_C, s_C−D) issue none. On Center, the nearest-mechanism rule assigns the "
           "command-timing intervention to withdrawal once its own template is removed, whereas formal D(Y) issues no withdrawal "
           "decision for either operational intervention (A11b). One template cannot support a rate.")
    return finish(fig, meta("AV-F11", "negative_control_false_leak", "plot_av_negative_control", "Negative-control false leak attribution",
                            "Do the policies mistake normal operation for a leak?",
                            ["advanced_validation/analysis/av_r2_negative_control_normal.csv", "advanced_validation/tables/A11b.csv"],
                            cap, LIM_R2), out)


def plot_av_scaling(d, out):
    dy, dx, hw = d["dy"], d["dx"], d["hw"]
    fig = figure()
    title(fig, "Measured runtime scaling of the implemented algorithms")
    axs = fig.subplots(2, 3)
    panels = [(dy, "M_channels", "Channels M (formal D(Y))"), (dy, "H_hypotheses", "Hypotheses H (formal D(Y))"),
              (dy, "T_window_samples", "Window samples T (formal D(Y))"), (dy, "S_shifts", "Clock shifts S (formal D(Y))"),
              (dx, "N_reference_windows", "Reference windows N (D(x), synthetic)"), (dx, "K_neighbours", "Neighbours K (D(x), synthetic)")]
    for ax, (df, dim, lab) in zip(axs.flat, panels):
        g = df[df.dimension == dim]
        ax.errorbar(g.value, g.median_s * 1e3, yerr=[np.zeros(len(g)), (g.p95_s - g.median_s) * 1e3], fmt="o-", color=C["teal"] if df is dy else C["blue"],
                    ms=4, lw=1.2, capsize=2)
        ax.set_xlabel(lab, fontsize=10)
        ax.set_ylabel("ms (median; bar to p95)" if ax in (axs[0, 0], axs[1, 0]) else "")
        ax.set_ylim(0, None)
        ygrid(ax)
    fits = pd.read_csv(B / "scaling_fits.csv").set_index("dimension")
    cap = (f"Wall-clock time on {hw['cpu_model']} ({hw['logical_cpus']} logical CPUs, {hw['ram_GB']} GB, Python {hw['python']}, "
           "NumPy " + hw["numpy"] + "), single process, one dimension varied at a time (others at 13 channels, 6 hypotheses, 151 samples, "
           f"±1 s). Formal D(Y): log–log slopes {fits.loc['M_channels', 'loglog_slope']:.2f} (M), "
           f"{fits.loc['H_hypotheses', 'loglog_slope']:.2f} (H), {fits.loc['T_window_samples', 'loglog_slope']:.2f} (T) and "
           f"{fits.loc['S_shifts', 'loglog_slope']:.2f} (S, early exit). D(x) on synthetic arrays: "
           f"{fits.loc['N_reference_windows', 'loglog_slope']:.2f} in N over 1k–20k. Slopes describe this implementation over the "
           "measured range only; they are not complexity proofs.")
    return finish(fig, meta("AV-F12", "computational_scaling", "plot_av_scaling", "Actual computational scaling",
                            "How does runtime scale with sensors, hypotheses, window length, shifts and reference size?",
                            ["advanced_validation/benchmarks/dy_scaling.csv", "dx_scaling.csv", "scaling_fits.csv", "hardware.csv"],
                            cap, "One laptop-class CPU; Python allocations only for memory; synthetic arrays for D(x)."), out)


def plot_av_sensor_tradeoff(d, out):
    s = d["a16"]
    fig = figure()
    title(fig, "Sensor count versus formal decision quality (no prices available)")
    ax = fig.add_subplot()
    for r in s.itertuples():
        nd = r.pareto_nondominated in (True, "True", "yes")
        ax.scatter(r.n_channels, r.specific_correct, marker="o", s=90 if nd else 45, color=C["teal"] if nd else C["white"],
                   edgecolor=C["teal"], lw=1.4, zorder=3)
        ax.scatter(r.n_channels, r.specific_wrong, marker="X", s=80 if nd else 40, color=C["burgundy"] if nd else C["white"],
                   edgecolor=C["burgundy"], lw=1.2, zorder=3)
    for lab, xy, txt in [("flow only", (3, 8), (3.3, 9.4)), ("pressure only", (10, 2), (8.6, 3.4)),
                         ("all 13", (13, 8), (12.9, 9.6)), ("without MFS1", (12, 8), (10.2, 9.6))]:
        ax.annotate(lab, xy=xy, xytext=txt, fontsize=10, arrowprops=dict(arrowstyle="-", color=C["slate"], lw=0.7))
    ax.set_xlabel("Number of available channels")
    ax.set_ylabel("Decisions (of 24)")
    ax.set_ylim(-0.5, 10.5)
    ax.set_xlim(2, 14)
    ygrid(ax)
    stamp(ax, COND)
    fig.legend(handles=[Line2D([], [], marker="o", ls="", color=C["teal"], ms=9, label="Correct SPECIFIC"),
                        Line2D([], [], marker="X", ls="", color=C["burgundy"], ms=9, label="Wrong SPECIFIC"),
                        Line2D([], [], marker="o", ls="", color=C["white"], mec=C["slate"], ms=7, label="Open marker: Pareto-dominated")],
               loc="outside lower center", ncol=3)
    m = d["minset"].set_index("scenario").loc["REF"]
    cap = ("Structured sensor configurations of the Center network: correct and wrong SPECIFIC formal decisions (24 per "
           "configuration) against the number of channels, the only measured cost axis (no source-supported sensor prices exist, A15). "
           "Filled markers: Pareto-nondominated on (fewer channels, more correct, fewer wrong). 'Without MFS1' avoids the two wrong "
           "decisions only by returning ambiguity sets without the truth. Template-level isolability needs "
           f"{int(m.min_channels)} channels ({m.minimal_sets}) at REF bounds (A16b).")
    return finish(fig, meta("AV-F13", "sensor_count_tradeoff", "plot_av_sensor_tradeoff", "Sensor count–risk–coverage trade-off",
                            "Which sensor arrangements keep decision quality with fewer channels?",
                            ["advanced_validation/tables/A16a.csv", "A16b.csv"], cap, LIM_C + " No monetary cost is estimated."), out)


def _status_matrix(fig, ax, rows, cols, cell, legend):
    sty = {"Y": ("o", C["teal"]), "P": ("D", C["ochre"]), "N": ("X", C["burgundy"]), "-": ("s", C["slate"])}
    for i, r in enumerate(rows):
        for j, c in enumerate(cols):
            code, txt = cell(r, c)
            m, col = sty[code]
            ax.scatter(j, i, marker=m, s=110, color=col, edgecolor=C["text"], lw=0.5, zorder=3)
            if txt:
                ax.text(j + 0.13, i, txt, va="center", fontsize=8.5)
    ax.set_xticks(range(len(cols)), cols)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(rows)), rows)
    ax.set_ylim(len(rows) - 0.5, -0.6)
    ax.set_xlim(-0.5, len(cols) - 0.2)
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    for j in range(len(cols)):
        ax.axvline(j, color=C["grid"], lw=0.8, zorder=1)
    fig.legend(handles=[Line2D([], [], marker=sty[k][0], ls="", color=sty[k][1], ms=8, label=l) for k, l in legend],
               loc="outside lower center", ncol=len(legend))


def plot_av_gas_matrix(d, out):
    rows = ["Air-like legacy (Center)", "Natural gas", "H2/CH4 blends", "Pure H2"]
    cols = ["Property basis", "Level A: software", "Level B: simulation transfer", "Level C: experimental transfer"]
    M = {("Air-like legacy (Center)", 0): ("N", "unphysical γ = 5.75"), ("Air-like legacy (Center)", 1): ("Y", "engine runs"),
         ("Natural gas", 0): ("N", "no provider"), ("Natural gas", 1): ("N", "refused"),
         ("H2/CH4 blends", 0): ("P", "GERG probe; flash fails"), ("H2/CH4 blends", 1): ("N", "refused by interface"),
         ("Pure H2", 0): ("Y", "Leachman EOS tables"), ("Pure H2", 1): ("Y", "provider resolves")}
    fig = figure()
    title(fig, "Gas-composition readiness: no diagnostic transfer exists for any gas")
    ax = fig.add_subplot()
    _status_matrix(fig, ax, rows, cols, lambda r, c: M.get((r, cols.index(c)), ("N", "none")),
                   [("Y", "Available / verified"), ("P", "Probe only"), ("N", "Absent or refused")])
    cap = ("Qualification of gas compositions (A13). Pure-H2 property tables reproduce the Leachman equation of state (CoolProp "
           "7.2.0) within 250–400 K × 0.1–10 MPa, and the composition interface refuses every blend. No gas-specific transient "
           "network model has been built (H2Net v1 blocked), so no simulation (Level B) or experimental (Level C) diagnostic transfer "
           "result exists. The legacy Center model is air-like with an unphysical heat-capacity ratio.")
    return finish(fig, meta("AV-F14", "gas_qualification_matrix", "plot_av_gas_matrix", "Gas-composition qualification matrix",
                            "Which gas compositions can H₂-PRISM currently handle, and at which level?",
                            ["advanced_validation/tables/A13.csv"], cap, "Status summary; no new physical result.",
                            ver="status from A13 and the cited repository files"), out)


def plot_av_portability(d, out):
    a = d["a12"]
    cols = ["Center", "MHC", "HY2RES"]

    center_specific = {"Timestamp processing / causal windowing", "Reference prediction", "Source provenance"}

    def cell(r, c):
        v = str(a.set_index("component").loc[r, c])
        if c == "Center":
            return ("P", "") if r in center_specific else ("Y", "")
        if v in ("—", "not executed", "none (recording grid analysed)"):
            return "N", ""
        if "shared" in v:
            return "Y", ""
        return "P", ""
    fig = figure(h=6.0)
    title(fig, "The formal engine runs only on Center; MHC and HY2RES use their own code")
    ax = fig.add_subplot()
    _status_matrix(fig, ax, list(a.component), cols, cell,
                   [("Y", "Shared engine or shared module executed"), ("P", "Study-specific reimplementation"), ("N", "Absent")])
    cap = ("Component-by-component code paths (A12). Import inspection shows that the MHC and HY2RES pipelines import no module "
           "of the h2prism package; formal D(Y) (certified_evidence.diagnose) has been executed only on Center. Only the "
           "presentation layer (Q1 figure style) is shared. Diagnostic portability across the three studies is therefore not "
           "demonstrated; code reuse alone would not demonstrate it either.")
    return finish(fig, meta("AV-F15", "software_portability", "plot_av_portability", "Actual cross-study software portability",
                            "Is the same diagnostic engine actually executed across Center, MHC and HY2RES?",
                            ["advanced_validation/tables/A12.csv"], cap, "Code inspection; not a performance result.",
                            ver="status from A12 (import inspection)"), out)


def plot_av_claims(d, out):
    a = d["a19"]
    levels = ["VERIFIED", "MEASURED", "CONDITIONALLY", "LEVEL 2", "EXPLORATORY", "INCONCLUSIVE", "NOT SUPPORTED",
              "NOT ESTIMABLE", "NOT DEMONSTRATED", "NOT ESTABLISHED", "NOT QUANTIFIABLE", "BLOCKED"]
    col = {"VERIFIED": C["teal"], "MEASURED": C["teal"], "CONDITIONALLY": C["blue"], "LEVEL 2": C["blue"], "EXPLORATORY": C["ochre"],
           "INCONCLUSIVE": C["ochre"]}
    fig = figure(h=6.6)
    title(fig, "Advanced-validation claims versus evidence level")
    ax = fig.add_subplot()
    xs = ["Verified / measured", "Conditional", "Exploratory / inconclusive", "Negative / not estimable", "Blocked / not established"]

    def bucket(s):
        s = s.upper()
        if "VERIFIED" in s or "MEASURED" in s:
            return 0
        if "CONDITIONALLY" in s or "LEVEL 2" in s:
            return 1
        if "EXPLORATORY" in s or "INCONCLUSIVE" in s:
            return 2
        if "NOT SUPPORTED" in s or "NOT ESTIMABLE" in s:
            return 3
        return 4
    mk = ["o", "D", "^", "X", "s"]
    cc = [C["teal"], C["blue"], C["ochre"], C["burgundy"], C["slate"]]
    for i, r in enumerate(a.itertuples()):
        b = bucket(r.evidence_level)
        ax.scatter(b, i, marker=mk[b], s=110, color=cc[b], edgecolor=C["text"], lw=0.5, zorder=3)
    ax.set_xticks(range(5), [x.replace(" / ", "\n/ ") for x in xs], fontsize=9.5)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(a)), a.claim, fontsize=9.5)
    ax.set_ylim(len(a) - 0.5, -0.6)
    ax.set_xlim(-0.5, 4.5)
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    for j in range(5):
        ax.axvline(j, color=C["grid"], lw=0.8, zorder=1)
    cap = "Each advanced-validation claim placed at its evidence level; exact wording, evidence and limiting factors in A19."
    return finish(fig, meta("AV-F16", "claims_evidence", "plot_av_claims", "Scientific claims versus evidence level",
                            "Which advanced-validation claims are established, conditional, exploratory or blocked?",
                            ["advanced_validation/tables/A19.csv"], cap, "Qualification summary; no new numbers."), out)


FIGURES = [plot_av_reliability_coverage, plot_av_false_specific_equal_coverage, plot_av_error_attribution,
           plot_av_library_completeness, plot_av_status_transitions, plot_av_localization, plot_av_isolability,
           plot_av_missing_sensor, plot_av_timing, plot_av_evidence_availability, plot_av_negative_control, plot_av_scaling,
           plot_av_sensor_tradeoff, plot_av_gas_matrix, plot_av_portability, plot_av_claims]


def main(only=""):
    setup()
    d = load()
    rows = []
    for fn in FIGURES:
        if only in fn.__name__:
            r = fn(d, OUT)
            print(f"{r['figure_id']:<8} {r['qa_status']:<9} {r['qa_issues'][:400]}")
            rows.append(r)
    qc = AV / "quality_control"
    qc.mkdir(exist_ok=True)
    man = qc / "AV_FIGURE_MANIFEST.csv"
    new = pd.DataFrame(rows)
    if only and man.exists():
        old = pd.read_csv(man, dtype=str, keep_default_na=False)
        new = pd.concat([old[~old.figure_id.isin(new.figure_id)], new.astype(str)], ignore_index=True)
    new.sort_values("figure_id").to_csv(man, index=False, lineterminator="\n")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
