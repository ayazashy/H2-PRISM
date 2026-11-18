"""H1 figures (H1-F01..H1-F07). One function per figure; all numbers read from h1_validation/analysis.

Usage (repository root): python 03_results/integrated_validation_v1/h1_validation/scripts/fig_h1.py
Writes figures/, captions/ and quality_control/H1_FIGURE_MANIFEST.csv under h1_validation/.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

H1 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(H1.parent / "publication_q1/scripts"))
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

from q1fig import finish  # noqa: E402
from q1style import C, figure, setup, title, xgrid, ygrid  # noqa: E402

A = H1 / "analysis"
OUT = H1 / "figures"
MOD = "fig_h1"
EXPL = "EXPLORATORY — post hoc on windows inspected in R2; not a test of the registered H1"
LIM = ("Simulated H2-SimNet topologies; all outer-test windows were inspected in R2; 91.7 % of classifier errors lie in "
       "runs whose source-model attribution is disputed (owner decision D1 pending). Not a confirmation of H1.")
STY = {"s_C": dict(color=C["teal"], marker="o", ls="-", label="s_C (evidence-guided, with D(x))"),
       "s_C_minus_D": dict(color=C["navy"], marker="s", ls="--", label="s_C−D (same, without D(x))"),
       "confidence": dict(color=C["ochre"], marker="^", ls="-.", label="Confidence (with evidence guard)"),
       "confidence_no_evidence_guard": dict(color=C["burgundy"], marker="D", ls=":",
                                            label="Confidence, conventional (no evidence guard)")}


def meta(fid, stem, fn, ttl, q, sources, cap, lim=LIM, ver="values read from h1_validation/analysis (verified 161/161)"):
    return dict(id=fid, stem=f"{fid}_{stem}", function=fn, module=MOD, title=ttl, question=q, sources=sources,
                caption=cap, limitation=lim, study="H1", verification=ver, caption_dir=H1 / "captions",
                script_dir="h1_validation/scripts")


def load():
    return {k: pd.read_csv(A / f) for k, f in {
        "feas": "h1_02_fold_feasibility.csv", "sel": "h1_04_selection_by_method.csv",
        "cmp": "h1_05_paired_comparisons.csv", "cap": "h1_05_error_capture.csv",
        "red": "h1_03_score_redundancy_test.csv", "abl": "h1_03_development_ablation.csv",
        "dy": "h1_07_dy_library_completeness.csv", "rq1": "h1_01_registered_rq1.csv"}.items()}


def stamp(ax, text=EXPL):
    ax.text(0.0, 1.02, text, transform=ax.transAxes, fontsize=10, color=C["burgundy"], va="bottom", ha="left",
            fontstyle="italic")


def plot_h1_attainable_coverage(d, out):
    f = d["feas"]
    p, w = f[f.variant == "primary"].set_index("held_out_topology"), f[f.variant == "warning_only"].set_index("held_out_topology")
    tops = ["Center", "Downstream", "Upstream"]
    fig = figure()
    title(fig, "Registered coverage targets lie beyond the attainable coverage")
    ax = fig.add_subplot()
    y = np.arange(3)
    ax.barh(y, p.loc[tops].max_attainable_coverage, height=0.5, color=C["blue"], zorder=3, label="Outer test, primary policy")
    ax.scatter(w.loc[tops].max_attainable_coverage, y, marker="|", s=420, color=C["navy"], lw=2, zorder=4,
               label="Outer test, warning-only variant")
    ax.scatter(p.loc[tops].dev_max_attainable_coverage, y, marker="o", s=60, facecolor=C["white"], edgecolor=C["slate"],
               lw=1.5, zorder=4, label="Development (threshold-transfer mode)")
    for t, ls, lab, ha in [(0.6, ":", "0.60 (secondary) ", "right"), (0.8, "--", "0.80 (primary) ", "right"),
                           (0.9, ":", " 0.90 (secondary)", "left")]:
        ax.axvline(t, color=C["burgundy"], ls=ls, lw=1.4 if t == 0.8 else 1.0, zorder=2)
        ax.text(t, 2.55, lab, ha=ha, va="bottom", fontsize=10, color=C["burgundy"])
    sh = p.max_attainable_coverage.min()
    ax.axvspan(0, sh, color=C["grid"], zorder=1, lw=0)
    ax.text(sh / 2, -0.62, f"shared region\n[0, {sh:.3f}]", ha="center", va="bottom", fontsize=10)
    ax.set_yticks(y, [f"{t} held out" for t in tops])
    ax.set_ylim(-0.7, 2.9)
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.set_xlabel("Maximum attainable specific-diagnosis coverage (eligible windows / all windows)")
    xgrid(ax)
    fig.legend(loc="outside lower center", ncol=3)
    cap = (f"Maximum attainable SPECIFIC coverage per outer fold of the registered run R2 "
           f"({int(p.n_windows.iloc[0]):,} windows per fold). Center reaches {p.loc['Center'].max_attainable_coverage:.3f}, "
           f"Downstream {p.loc['Downstream'].max_attainable_coverage:.3f} and Upstream "
           f"{p.loc['Upstream'].max_attainable_coverage:.3f}, so the primary target 0.80 is unattainable in every fold and "
           f"0.60 in Center; because a pooled result needs every fold, RQ1 is NOT_ESTIMABLE. Development maxima "
           f"(threshold-transfer mode) are {p.loc['Center'].dev_max_attainable_coverage:.3f}, "
           f"{p.loc['Downstream'].dev_max_attainable_coverage:.2g} and {p.loc['Upstream'].dev_max_attainable_coverage:.3f}. "
           "The binding constraint is the specific-blocking support flags (fewer than two independent families or "
           "scenarios among a window's 25 nearest development neighbours).")
    return finish(fig, meta("H1-F01", "attainable_coverage", "plot_h1_attainable_coverage",
                            "Attainable coverage versus registered targets",
                            "Could the registered matched-coverage comparison be estimated at all?",
                            ["h1_validation/analysis/h1_02_fold_feasibility.csv",
                             "03_results/primary_protocol/PRIMARY/estimability.csv"], cap,
                            lim="Registered result; no threshold or flag is relaxed."), out)


def plot_h1_selective_risk_shared(d, out):
    s = d["sel"]
    s = s[s.scope == "pooled"]
    sh = d["feas"].query("variant == 'primary'").max_attainable_coverage.min()
    fig = figure()
    title(fig, "Selective risk inside the shared attainable coverage region")
    ax = fig.add_subplot()
    for m, st in STY.items():
        g = s[s.method == m].sort_values("coverage")
        ax.plot(g.coverage, g.selective_risk, ms=7, lw=1.6, mec=C["text"], mew=0.5, zorder=3, **st)
    ax.axvline(sh, color=C["slate"], ls="--", lw=1.0)
    ax.text(sh - 0.003, 0.49, f"Center limit {sh:.3f}", ha="right", va="top", fontsize=10, color=C["slate"])
    ax.set_xlim(0.03, 0.27)
    ax.set_ylim(-0.02, 0.52)
    ax.set_xticks([0.05, 0.10, 0.15, 0.20, 0.25])
    ax.set_xlabel("Rank-matched specific coverage (pooled over three outer folds)")
    ax.set_ylabel("Empirical selective risk (errors / SPECIFIC)")
    ygrid(ax)
    stamp(ax)
    fig.legend(loc="outside right center")
    g25 = s[np.isclose(s.coverage, 0.25)].set_index("method")
    cap = ("Pooled empirical selective risk of the registered policy scores at the exploratory grid {0.05, …, 0.25} that "
           "the R2 diagnostics fixed before this analysis; 0.25 is the largest grid point inside the shared attainable "
           f"region. At 0.25 ({int(g25.loc['s_C'].n_selected):,} SPECIFIC calls each): s_C {g25.loc['s_C'].selective_risk:.3f}, "
           f"s_C−D {g25.loc['s_C_minus_D'].selective_risk:.3f}, guarded confidence {g25.loc['confidence'].selective_risk:.3f}, "
           f"conventional confidence {g25.loc['confidence_no_evidence_guard'].selective_risk:.3f}. Margin and −entropy are "
           "listed in H1-T04 and the analysis CSV. No point beyond the shared region is drawn; uncertainty is shown in H1-F02b.")
    return finish(fig, meta("H1-F02a", "selective_risk_shared_coverage", "plot_h1_selective_risk_shared",
                            "Selective risk at shared attainable coverage",
                            "Within the coverage attainable in every fold, how do the policies' selective risks compare?",
                            ["h1_validation/analysis/h1_04_selection_by_method.csv"], cap), out)


def plot_h1_paired_difference(d, out):
    c = d["cmp"]
    fig = figure()
    title(fig, "Paired risk differences: intervals for the registered contrast include zero")
    axs = fig.subplots(1, 2, sharey=True)
    for ax, mb, ttl in [(axs[0], "s_C_minus_D", "s_C − s_C−D (registered contrast)"),
                        (axs[1], "confidence_no_evidence_guard", "s_C − conventional confidence")]:
        g = c[c.method_b == mb].sort_values("coverage")
        x = g.coverage.to_numpy()
        ax.errorbar(x - 0.004, g.delta_R, yerr=[g.delta_R - g.family_ci_low, g.family_ci_high - g.delta_R], fmt="o",
                    color=C["teal"], ms=6, capsize=3, lw=1.2, label="Family units (39, registered method)")
        ax.errorbar(x + 0.004, g.delta_R, yerr=[g.delta_R - g.ancestor_ci_low, g.ancestor_ci_high - g.delta_R], fmt="s",
                    color=C["navy"], ms=5, capsize=3, lw=1.2, ls="none", label="Scenario-ancestor units (17)")
        ax.axhline(0, color=C["text"], lw=0.8)
        ax.set_title(ttl, fontsize=12)
        ax.set_xticks([0.05, 0.10, 0.15, 0.20, 0.25])
        ax.set_xlabel("Rank-matched coverage")
        ygrid(ax)
    axs[0].set_ylabel(r"$\Delta R$ = risk(s_C) − risk(comparator)")
    fig.legend(*axs[0].get_legend_handles_labels(), loc="outside lower center", ncol=2,
               title="95 % percentile bootstrap interval — EXPLORATORY, post hoc on inspected windows")
    g = c[c.method_b == "s_C_minus_D"]
    b = c[c.method_b == "confidence_no_evidence_guard"]
    cap = (f"Paired differences with 95 % percentile bootstrap intervals (2,000 replicates, seed 20261104). Left: the "
           f"registered contrast. Δ ranges from {g.delta_R.min():.3f} to {g.delta_R.max():.3f}, and every family- and "
           f"ancestor-level interval includes 0 (upper bounds ≥ 0). Discordant errors come from at most "
           f"{int(g.ancestors_discordant_errors.max())} scenario ancestors, and neither policy makes an error in runs with "
           f"undisputed attribution. Right: the full evidence policy against conventional confidence abstention without "
           f"the support guard; Δ from {b.delta_R.min():.3f} to {b.delta_R.max():.3f}, with ancestor-level intervals below "
           f"0 at {int((b.ancestor_ci_high < 0).sum())}/5 points. The family intervals reproduce the registered "
           "diagnostics exactly; the ancestor intervals treat the 17 scenario templates shared by all topologies as units.")
    return finish(fig, meta("H1-F02b", "paired_risk_difference", "plot_h1_paired_difference",
                            "Paired selective-risk differences with intervals",
                            "Is the observed risk reduction distinguishable from zero at the level of independent units?",
                            ["h1_validation/analysis/h1_05_paired_comparisons.csv",
                             "03_results/diagnostics/PRIMARY_a10530f1fcf2/exploratory_shared_coverage.csv"], cap), out)


def plot_h1_selection_swap(d, out):
    c = d["cmp"]
    g = c[c.method_b == "s_C_minus_D"].sort_values("coverage")
    fig = figure()
    title(fig, "D(x) swaps which windows are accepted; the swapped-out errors share few ancestors")
    ax = fig.add_subplot()
    y = np.arange(len(g))
    oa_c, oa_e = g.n_only_a - g.errors_only_a, g.errors_only_a
    ob_c, ob_e = g.n_only_b - g.errors_only_b, g.errors_only_b
    ax.barh(y, -ob_c, color=C["navy"], height=0.55, zorder=3, label="Correct")
    ax.barh(y, -ob_e, left=-ob_c, color=C["burgundy"], hatch="xx", edgecolor=C["white"], height=0.55, zorder=3,
            label="Error")
    ax.barh(y, oa_c, color=C["navy"], height=0.55, zorder=3)
    ax.barh(y, oa_e, left=oa_c, color=C["burgundy"], hatch="xx", edgecolor=C["white"], height=0.55, zorder=3)
    ax.axvline(0, color=C["text"], lw=0.8)
    lim = max((g.n_only_a).max(), (g.n_only_b).max()) * 1.25
    ax.set_xlim(-lim, lim)
    for i, r in enumerate(g.itertuples()):
        pl = lambda n, w: f"{n} {w}" + ("" if n == 1 else "s")  # noqa: E731
        ax.text(-lim * 0.98, i, f"{pl(r.errors_only_b, 'error')}\n{pl(r.ancestors_discordant_errors, 'ancestor')}",
                va="center", fontsize=9, color=C["text"])
        ax.text(lim * 0.98, i, pl(r.errors_only_a, "error"), va="center", ha="right", fontsize=9)
    ax.set_yticks(y, [f"{v:.2f}" for v in g.coverage])
    ax.invert_yaxis()
    ax.set_ylabel("Rank-matched coverage")
    ax.set_xlabel("Windows accepted by only one policy   (left: only s_C−D   |   right: only s_C)")
    ax.xaxis.set_major_formatter(lambda v, _: f"{abs(int(v)):,}")
    xgrid(ax)
    stamp(ax)
    fig.legend(loc="outside right center", title="Classifier top-1")
    cap = ("Windows selected by exactly one of the two registered policies at each grid point (identical SPECIFIC counts). "
           f"Adding D(x) exchanges {int(g.n_only_a.min()):,}–{int(g.n_only_a.max()):,} windows. The windows only s_C−D accepts "
           f"contain {int(g.errors_only_b.min())}–{int(g.errors_only_b.max())} errors; those only s_C accepts contain "
           f"{int(g.errors_only_a.min())}–{int(g.errors_only_a.max())}. All discordant errors come from 1–3 scenario ancestors, "
           "all in Center runs whose topology attribution is disputed; they are not independent replications.")
    return finish(fig, meta("H1-F03", "selection_swap", "plot_h1_selection_swap",
                            "Selection changes caused by D(x)",
                            "Which cases does the distinguishability component add or remove at matched coverage?",
                            ["h1_validation/analysis/h1_05_paired_comparisons.csv"], cap), out)


def plot_h1_development_ablation(d, out):
    a = d["abl"].set_index("arm_id")
    arms = [("A_P11_DEV", "A: protocol 1.1"), ("C_COMMON_SENSORS", "C: 13 common sensors"),
            ("G1_DATA_CORRECTIONS", "G1: topology + sensors"), ("G2_FULL_CANDIDATE", "G2: G1 + decision layer")]
    fig = figure()
    title(fig, "Development ablation: adding D(x) leaves selective risk unchanged")
    ax = fig.add_subplot()
    cols = [("s_C_group_balanced_risk_mean", "s_C"), ("s_C_minus_D_group_balanced_risk_mean", "s_C_minus_D"),
            ("confidence_group_balanced_risk_mean", "confidence")]
    for j, (col, key) in enumerate(cols):
        st = STY[key]
        for i, (arm, _) in enumerate(arms):
            ax.scatter(a.loc[arm, col], i + (j - 1) * 0.18, marker=st["marker"], s=70, color=st["color"],
                       edgecolor=C["text"], lw=0.5, zorder=3, label=st["label"].split(" (")[0] if i == 0 else None)
    def est(n):
        return f"(estimable in {n} development topolog{'y' if n == 1 else 'ies'})"
    ax.set_yticks(range(len(arms)), [f"{lab}\n{est(int(a.loc[arm, 's_C_estimable_dev_topologies']))}" for arm, lab in arms])
    ax.invert_yaxis()
    ax.set_xlim(-0.01, 0.12)
    ax.set_xlabel("Scenario-group-balanced selective risk at the development-fixed operating point")
    xgrid(ax)
    stamp(ax, "EXPLORATORY_DEVELOPMENT — development windows of each outer fold")
    fig.legend(loc="outside right center", title="Score")
    cap = ("Protocol 2.0 development ablation (means over outer folds; same 27,993 windows). In every arm where the "
           f"operating point is estimable, s_C, s_C−D and confidence have identical group-balanced risk (A, D, E: 0 vs 0 "
           f"floor on one topology; C: {a.loc['C_COMMON_SENSORS', 's_C_group_balanced_risk_mean']:.3f}; G1: "
           f"{a.loc['G1_DATA_CORRECTIONS', 's_C_group_balanced_risk_mean']:.3f}; G2: s_C and s_C−D "
           f"{a.loc['G2_FULL_CANDIDATE', 's_C_group_balanced_risk_mean']:.3f}, confidence "
           f"{a.loc['G2_FULL_CANDIDATE', 'confidence_group_balanced_risk_mean']:.3f}). Arms B and F have no estimable "
           "operating point and are omitted from the plot (listed in H1-T05a).")
    return finish(fig, meta("H1-F04a", "development_ablation", "plot_h1_development_ablation",
                            "Development ablation of D(x)",
                            "Does D(x) add decision value beyond confidence on development data?",
                            ["03_results/ablation/ARM_SUMMARY.csv"], cap,
                            lim="Development-only, exploratory; windows were inspected as R2 outer test."), out)


def plot_h1_score_ranking(d, out):
    r = d["red"]
    r = r[(r.scope == "guard_available") & (r.n_errors > 0)].set_index("held_out_topology")
    scores = [("s_C", "s_C"), ("s_C_minus_D", "s_C−D"), ("confidence", "Confidence"), ("margin", "Margin"),
              ("neg_entropy", "−Entropy"), ("D_only", "D(x) only")]
    fig = figure()
    title(fig, "How well each score ranks correct above wrong predictions (R2 outer test)")
    ax = fig.add_subplot()
    mk = {"Center": ("o", C["teal"]), "Downstream": ("s", C["ochre"])}
    for j, t in enumerate(r.index):
        m, c = mk[t]
        vals = [r.loc[t, f"auroc_correct_{k}"] for k, _ in scores]
        ax.scatter(vals, np.arange(len(scores)) + (j - 0.5) * 0.22, marker=m, s=70, color=c, edgecolor=C["text"],
                   lw=0.5, zorder=3, label=f"{t} held out ({int(r.loc[t, 'n'])} eligible windows, "
                                           f"{int(r.loc[t, 'n_errors'])} errors)")
    ax.axvline(0.5, color=C["slate"], ls="--", lw=1)
    ax.text(0.51, -0.75, "AUROC 0.5: no ranking information", ha="left", fontsize=10, color=C["slate"])
    ax.set_yticks(range(len(scores)), [lab for _, lab in scores])
    ax.set_ylim(len(scores) - 0.4, -1.0)
    ax.set_xlim(-0.02, 1.02)
    ax.set_xlabel("AUROC of the score for predicting a correct top-1 class")
    xgrid(ax)
    stamp(ax)
    fig.legend(loc="outside lower center", ncol=2)
    cap = ("Correctness AUROC of each registered selection score on the windows eligible for SPECIFIC. Downstream: "
           "confidence, margin and −entropy are perfectly anti-informative (AUROC 0: the 650 errors are the most confident "
           "windows), while both meta-model scores reach 1.0 with or without D(x). Center: adding D(x) moves the meta-model "
           f"from {r.loc['Center', 'auroc_correct_s_C_minus_D']:.3f} to {r.loc['Center', 'auroc_correct_s_C']:.3f}, the same "
           f"level as confidence ({r.loc['Center', 'auroc_correct_confidence']:.3f}). Upstream has no errors (not shown). "
           "Both topologies' errors are tied to the disputed attribution.")
    return finish(fig, meta("H1-F04b", "score_ranking_quality", "plot_h1_score_ranking",
                            "Score ranking quality on the outer test",
                            "Does D(x) carry ranking information that conventional scores lack?",
                            ["h1_validation/analysis/h1_03_score_redundancy_test.csv"], cap), out)


def plot_h1_error_abstention(d, out):
    cap_ = d["cap"].set_index("scope")
    s = d["sel"]
    tops = ["Center", "Downstream"]
    fig = figure()
    title(fig, "Where classifier errors go at coverage 0.25")
    ax = fig.add_subplot()
    rows = []
    for t in tops:
        tot = cap_.loc[t, "classifier_errors"]
        blk = cap_.loc[t, "errors_blocked_by_evidence_flags"]
        se = s[(s.scope == t) & (s.method == "s_C") & np.isclose(s.coverage, 0.25)].n_errors.iloc[0]
        be = s[(s.scope == t) & (s.method == "confidence_no_evidence_guard") & np.isclose(s.coverage, 0.25)].n_errors.iloc[0]
        rows.append((f"{t}: evidence policy s_C", [blk, tot - blk - se, se]))
        rows.append((f"{t}: conventional confidence", [0, tot - be, be]))
    parts = [("Blocked by evidence-support flags", C["slate"], "///"), ("Eligible, not accepted", C["blue"], None),
             ("Issued as SPECIFIC (wrong)", C["burgundy"], "xx")]
    for i, (lab, v) in enumerate(rows):
        left = 0
        tot = sum(v)
        for (name, col, h), x in zip(parts, v):
            if x:
                ax.barh(i, x / tot, left=left, color=col, hatch=h, edgecolor=C["white"], height=0.6, zorder=3,
                        label=name if name not in ax.get_legend_handles_labels()[1] else None)
                if x / tot >= 0.05:
                    ax.text(left + x / tot / 2, i, f"{int(x):,}", ha="center", va="center", fontsize=10, color=C["text"],
                            bbox=dict(facecolor=C["white"], edgecolor="none", pad=1.2))
                left += x / tot
    ax.set_yticks(range(len(rows)), [r[0] for r in rows])
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.set_xlabel("Share of that held-out topology's classifier errors")
    xgrid(ax)
    stamp(ax)
    fig.legend(loc="outside lower center", ncol=3)
    p = cap_.loc["pooled"]
    cap = (f"Fate of the classifier's top-1 errors at rank-matched coverage 0.25 (equal SPECIFIC counts per fold). The "
           f"evidence-support flags block {int(p.errors_blocked_by_evidence_flags):,} of {int(p.classifier_errors):,} errors "
           f"({p.share_errors_blocked:.1%}); the error rate is {p.error_rate_blocked:.3f} among blocked and "
           f"{p.error_rate_eligible:.3f} among eligible windows (base rate {p.base_error_rate:.3f}). Conventional confidence "
           "abstention issues far more of the same errors as SPECIFIC. Segments below 5 % are unlabelled; exact counts are "
           "in h1_05_error_capture.csv and h1_04_selection_by_method.csv. Upstream has no classifier errors. "
           f"{int(p.errors_in_disputed_runs):,} of the errors lie in runs with disputed topology attribution, so this shows "
           "the guard reacting to an attribution defect, not to independently labelled diagnostic difficulty.")
    return finish(fig, meta("H1-F05", "error_abstention", "plot_h1_error_abstention",
                            "Decision errors and abstention",
                            "Does evidence-based abstention preferentially withhold classifier errors?",
                            ["h1_validation/analysis/h1_05_error_capture.csv", "h1_04_selection_by_method.csv"], cap), out)


def plot_h1_library_completeness(d, out):
    y = d["dy"]
    y = y[y.clock_bound_s == 1.0]
    groups = [("all", "All sensors"), ("pressure", "Pressure only"), ("flow", "Flow only"), ("omit_MFS3", "All without MFS3")]
    cats = [("specific_correct", "SPECIFIC, correct", C["teal"], None), ("specific_wrong", "SPECIFIC, wrong", C["burgundy"], "xx"),
            ("ambiguous", "AMBIGUOUS", C["ochre"], "..."), ("unresolved", "UNRESOLVED", C["slate"], "///")]
    fig = figure()
    title(fig, "An incomplete hypothesis library turns abstentions into wrong SPECIFIC decisions")
    ax = fig.add_subplot()
    labels = []
    i = 0
    for uni, ulab in [("full", "Full declared universe"), ("restricted", "Restricted universe (adapters only)")]:
        for g, glab in groups:
            r = y[(y.universe == uni) & (y.group == g)].iloc[0]
            left = 0
            for k, name, col, h in cats:
                v = int(r[k])
                if v:
                    ax.barh(i, v, left=left, color=col, hatch=h, edgecolor=C["white"], height=0.62, zorder=3)
                    ax.text(left + v / 2, i, str(v), ha="center", va="center", fontsize=10,
                            bbox=dict(facecolor=C["white"], edgecolor="none", pad=1.0))
                    left += v
            labels.append(f"{ulab.split(' (')[0]} · {glab}")
            i += 1
    ax.axhline(3.5, color=C["text"], lw=0.8)
    ax.set_yticks(range(len(labels)), labels)
    ax.invert_yaxis()
    ax.set_xlabel("Decisions (6 queries × 7 declared bound scenarios = 42 per row, ±1 s clock)")
    xgrid(ax)
    fig.legend(handles=[Patch(facecolor=c, hatch=h, edgecolor=C["white"], label=n) for _, n, c, h in cats],
               loc="outside lower center", ncol=4)
    a = d["dy"]
    rr = a[a.universe == "restricted"]
    cap = ("Formal D(Y) decisions on the Center controlled captures under conditional hypothetical bounds. With the full "
           "declared universe every decision is UNRESOLVED, because three declared hypotheses have no adapter. Restricting "
           "the universe to modelled hypotheses yields SPECIFIC decisions: over both clock bounds and all sensor groups "
           f"{int(rr.specific_correct.sum())} are correct and {int(rr.specific_wrong.sum())} wrong, and every wrong decision "
           "has a true hypothesis that is absent from the library (asserted). Rows are repeated views of the same six "
           "captures, not independent trials. Conditional hypothetical bounds — not calibrated uncertainty.")
    return finish(fig, meta("H1-F06", "library_completeness_risk", "plot_h1_library_completeness",
                            "Hypothesis-library completeness risk",
                            "Does an incomplete hypothesis library cause false specific decisions?",
                            ["h1_validation/analysis/h1_07_dy_library_completeness.csv",
                             "03_results/validation/center_evidence_enhancement/analysis/dy_decisions.json"], cap,
                            lim="One controlled simulation family with an air-like gas model; hypothetical bounds."), out)


def plot_h1_evidence_map(d, out):
    rows = [("Registered H1 contrast (s_C vs s_C−D)", "Not estimable"),
            ("Reproduction of R2 selections and intervals", "Numerically verified"),
            ("D(x) value at development level", "Not supported"),
            ("s_C vs s_C−D at shared coverage ≤ 0.25", "Exploratory, inconclusive"),
            ("Evidence guard vs conventional confidence", "Exploratory, confounded"),
            ("Three-outcome policy (R2 folds 2–3)", "Descriptively demonstrated"),
            ("Formal D(Y) three outcomes (Center)", "Conditionally demonstrated"),
            ("Library incompleteness → false SPECIFIC", "Conditionally demonstrated"),
            ("Corrected-attribution replication", "Blocked: approval"),
            ("Independent H1 confirmation", "Blocked: new evidence")]
    cats = ["Numerically verified", "Descriptively demonstrated", "Conditionally demonstrated", "Exploratory, inconclusive",
            "Exploratory, confounded", "Not supported", "Not estimable", "Blocked: approval", "Blocked: new evidence"]
    col = {"Numerically verified": C["teal"], "Descriptively demonstrated": C["teal"], "Conditionally demonstrated": C["blue"],
           "Exploratory, inconclusive": C["ochre"], "Exploratory, confounded": C["ochre"], "Not supported": C["burgundy"],
           "Not estimable": C["burgundy"], "Blocked: approval": C["slate"], "Blocked: new evidence": C["slate"]}
    mk = {"Numerically verified": "o", "Descriptively demonstrated": "o", "Conditionally demonstrated": "D",
          "Exploratory, inconclusive": "^", "Exploratory, confounded": "^", "Not supported": "X", "Not estimable": "X",
          "Blocked: approval": "s", "Blocked: new evidence": "s"}
    fig = figure(h=6.2)
    title(fig, "H1 evidence and feasibility map")
    ax = fig.add_subplot()
    for i, (comp, cat) in enumerate(rows):
        j = cats.index(cat)
        ax.scatter(j, i, marker=mk[cat], s=110, color=col[cat], edgecolor=C["text"], lw=0.6, zorder=3)
    for j in range(len(cats)):
        ax.axvline(j, color=C["grid"], lw=0.8, zorder=1)
    ax.set_xticks(range(len(cats)), [c.replace(",", "").replace(":", "").replace(" ", "\n") for c in cats], fontsize=9.5)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(rows)), [r[0] for r in rows])
    ax.set_ylim(len(rows) - 0.5, -0.6)
    ax.set_xlim(-0.5, len(cats) - 0.5)
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    cap = ("Qualification of each H1 component (rows) in the project's evidence vocabulary (columns); values and sources "
           "in H1-T07. Only the reproduction of the frozen R2 results is numerically verified; the registered contrast "
           "remains NOT_ESTIMABLE; the shared-coverage comparisons are exploratory and confounded by the disputed "
           "attribution; the formal D(Y) results are conditional on hypothetical bounds; a corrected replication needs "
           "owner decision D1, and confirmation needs new independent scenarios.")
    return finish(fig, meta("H1-F07", "evidence_map", "plot_h1_evidence_map", "H1 evidence and feasibility map",
                            "Which components of the H1 argument are established, exploratory, not estimable or blocked?",
                            ["h1_validation/tables/H1-T07.csv"], cap, lim="Summary of the tables; no new numbers."), out)


FIGURES = [plot_h1_attainable_coverage, plot_h1_selective_risk_shared, plot_h1_paired_difference, plot_h1_selection_swap,
           plot_h1_development_ablation, plot_h1_score_ranking, plot_h1_error_abstention, plot_h1_library_completeness,
           plot_h1_evidence_map]


def main(only=""):
    setup()
    d = load()
    rows = []
    for fn in FIGURES:
        if only in fn.__name__:
            r = fn(d, OUT)
            print(f"{r['figure_id']:<9} {r['qa_status']:<9} {r['qa_issues'][:300]}")
            rows.append(r)
    qc = H1 / "quality_control"
    qc.mkdir(exist_ok=True)
    man = qc / "H1_FIGURE_MANIFEST.csv"
    new = pd.DataFrame(rows)
    if only and man.exists():
        old = pd.read_csv(man, dtype=str, keep_default_na=False)
        new = pd.concat([old[~old.figure_id.isin(new.figure_id)], new.astype(str)], ignore_index=True)
    new.sort_values("figure_id").to_csv(man, index=False, lineterminator="\n")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
