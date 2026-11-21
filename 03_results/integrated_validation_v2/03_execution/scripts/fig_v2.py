"""v2 figures V2-F01..V2-F06 (Q1 style, reusing the v1 q1style/q1fig/q1qa modules; all values read from v2 outputs).

Writes 05_figures/*.png|svg, 05_figures/captions/*.md and 05_figures/V2_FIGURE_MANIFEST.csv.
Usage (repository root): python 03_results/integrated_validation_v2/03_execution/scripts/fig_v2.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

V2 = Path(__file__).resolve().parents[2]
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "03_results/integrated_validation_v1/publication_q1/scripts"))
sys.path.insert(0, str(REPO / "03_results/integrated_validation_v1/advanced_validation/scripts"))
from matplotlib.colors import LinearSegmentedColormap, Normalize  # noqa: E402
from matplotlib.cm import ScalarMappable  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

from fig_av import OUTC, stacked, stamp  # noqa: E402
from q1fig import finish  # noqa: E402
from q1style import C, figure, setup, title, xgrid, ygrid  # noqa: E402

AN, TB = V2 / "04_results/analysis", V2 / "04_results/tables"
OUT = V2 / "05_figures"
MOD = "fig_v2"
EXPL = "EXPLORATORY — inspected R2 windows; labels disputed (D1)"
SYN = "SYNTHETIC perturbations — not field evidence"
COND = "CONDITIONAL HYPOTHETICAL BOUNDS — not calibrated uncertainty"
HYPS = ["HN", "H213", "H312", "H215", "HP55", "HT59"]
HLAB = {"HN": "Normal", "H213": "SID 213", "H312": "SID 312", "H215": "SID 215", "HP55": "Pressure cmd 55", "HT59": "Timing 59"}
DIV = LinearSegmentedColormap.from_list("v2div", [C["burgundy"], "#F3E3E3", C["white"], "#D7ECEE", C["teal"]])


def meta(fid, stem, fn, ttl, q, sources, cap, lim):
    return dict(id=fid, stem=f"{fid}_{stem}", function=fn, module=MOD, title=ttl, question=q, sources=sources, caption=cap,
                limitation=lim, study="v2", verification="values read from integrated_validation_v2 outputs",
                caption_dir=OUT / "captions", script_dir="integrated_validation_v2/03_execution/scripts")


def rel(p):
    return Path(p).resolve().relative_to(REPO).as_posix()


def f01():
    per = pd.read_csv(AN / "x2_incremental_utility_per_template.csv")
    syn = pd.read_csv(AN / "x5_synthetic_dx_control.csv")
    fig = figure()
    title(fig, "Does D(x) add information beyond classifier confidence?")
    a, b = fig.subplots(1, 2, width_ratios=[1.15, 1])
    cols = [("d_logloss_add_D_to_conf", "Add D to\nconfidence"), ("d_logloss_add_D_to_full", "Add D to confidence\n+ margin + entropy")]
    rng = np.random.default_rng(0)
    for i, (c, lab) in enumerate(cols):
        v = per[c].to_numpy()
        x = i + rng.uniform(-0.12, 0.12, len(v))
        a.scatter(x, v, s=28, color=C["navy"], zorder=3, label="Held-out template" if i == 0 else None)
        m = float(np.median(v))
        a.plot([i - 0.25, i + 0.25], [m, m], color=C["burgundy"], lw=2.2, zorder=4, label="Median" if i == 0 else None)
        a.text(i + 0.3, m, f"median {m:+.3f}\n{int((v > 0).sum())}/{len(v)} worse", va="center", fontsize=9.5)
    a.axhline(0, color=C["text"], lw=0.8)
    a.set_xticks([0, 1], [l for _, l in cols])
    a.set_xlim(-0.5, 1.95)
    a.set_ylabel("Δ out-of-template log-loss (positive = worse)")
    ygrid(a)
    a.set_yscale("symlog", linthresh=0.1)
    a.set_ylim(top=8)
    a.legend(loc="upper left", fontsize=9)
    a.set_title("(a) R2 correctness models, leave-one-template-out", loc="left", fontsize=11.5, pad=20)
    stamp(a, EXPL)
    sty = {"a_calibrated_bayes": (C["teal"], "o", "-", "Calibrated (Bayes)"),
           "b_overconfident_T0.2": (C["ochre"], "s", "--", "Overconfident (T = 0.2)"),
           "c_blind_to_feature_1": (C["navy"], "^", "-.", "Blind to one informative feature")}
    for k, (col, mk, ls, lab) in sty.items():
        g = syn[syn.classifier == k].sort_values("separation")
        b.plot(g.separation, g.delta_logloss, color=col, marker=mk, ls=ls, label=lab, lw=1.6, ms=7)
    b.axhline(0, color=C["text"], lw=0.8)
    b.set_xlabel("Class separation (synthetic units)")
    b.set_ylabel("Δ log-loss when D is added (negative = better)")
    b.set_xticks(sorted(syn.separation.unique()))
    ygrid(b)
    b.legend(loc="lower left", fontsize=9)
    b.set_title("(b) Synthetic method check", loc="left", fontsize=11.5, pad=20)
    stamp(b, "SYNTHETIC — known posterior")
    return finish(fig, meta("V2-F01", "dx_incremental_value", "f01", "D(x) incremental-value analysis",
                            "Does D(x) improve out-of-template prediction of classifier correctness beyond confidence features?",
                            [rel(AN / "x2_incremental_utility_per_template.csv"), rel(AN / "x5_synthetic_dx_control.csv")],
                            "(a) Each point is one held-out scenario template (16 eligible). Adding D to the correctness model increased out-of-template log-loss for most templates. (b) In a synthetic design with a known posterior, D adds information only when the classifier is blind to an informative feature; calibration or overconfidence alone leaves Δ near zero.",
                            "R2 labels are disputed in 36/57 runs; templates are the independent units; synthetic panel is a method check only."), OUT)


def f02():
    s = pd.read_csv(AN / "s1_dy_synthetic_stress_runs.csv")
    s["lvl"] = s.level.map(lambda v: f"{v:g}")
    order = [("none", "0"), ("stuck", "0"), ("bias", "0.5"), ("bias", "2"), ("bias", "10"), ("drift", "0.5"), ("drift", "2"),
             ("drift", "10"), ("noise", "0.5"), ("noise", "2"), ("jitter", "0.2"), ("jitter", "0.5")]
    lab = {"none": "No perturbation", "stuck": "Stuck at first sample", "bias": "Bias {} ε_obs", "drift": "Linear drift to {} ε_obs",
           "noise": "Gaussian noise σ = {} ε_obs", "jitter": "Jitter, p = {} (±1 sample)"}
    rows, labels = [], []
    for f, l in order:
        g = s[(s.fault == f) & (s.lvl == l)]
        rows.append(g.outcome.value_counts().to_dict())
        labels.append(lab[f].format(l) + f"  (n = {len(g)})")
    fig = figure(9.6, 5.4)
    title(fig, "Formal D(Y) under synthetic sensor faults and timestamp jitter")
    ax = fig.subplots()
    stacked(ax, rows, labels)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Share of decisions (pooled over channels MFS3, PS1, PS4; scenarios S4 and REF; 6 queries)")
    xgrid(ax)
    used = {k for r in rows for k in r}
    ax.legend(handles=[Patch(facecolor=c, hatch=h, edgecolor=C["white"], label=n) for k, n, c, h in OUTC if k in used],
              loc="upper center", bbox_to_anchor=(0.45, -0.13), ncols=3, fontsize=9.5)
    stamp(ax, SYN + " · " + COND)
    return finish(fig, meta("V2-F02", "dy_synthetic_sensor_faults", "f02", "Sensor-failure robustness (synthetic)",
                            "Do injected sensor faults or timestamp jitter make the formal engine issue more wrong SPECIFIC decisions?",
                            [rel(AN / "s1_dy_synthetic_stress_runs.csv")],
                            "Outcome shares per perturbation. No fault setting raised the count of wrong SPECIFIC decisions above the unperturbed baseline, but at 2 ε_obs bias or drift the correct SPECIFIC decisions are lost first, so the wrong share among SPECIFIC decisions rises; at larger magnitudes every decision becomes UNRESOLVED (all hypotheses excluded). ±1-sample jitter left every outcome unchanged at τ = 1 s.",
                            "Synthetic perturbations of six Center captures under hypothetical bounds; magnitudes are relative to ε_obs, not sensor specifications."), OUT)


def f03():
    i1 = pd.read_csv(AN / "i1_isolability_onset.csv")
    pairs = list(dict.fromkeys(zip(i1.hyp_a, i1.hyp_b)))
    sty = {"all": (C["navy"], "o", "All 13 channels"), "pressure_only": (C["ochre"], "s", "Pressure only (10)"),
           "flow_only": (C["teal"], "^", "Flow only (3)")}
    off = {"all": -0.22, "pressure_only": 0.0, "flow_only": 0.22}
    fig = figure(9.6, 5.4)
    title(fig, "Pairwise isolability onset relative to the reference bounds")
    ax = fig.subplots()
    for cfg, (col, mk, lab) in sty.items():
        g = i1[i1.channels == cfg].set_index(["hyp_a", "hyp_b"])
        ax.scatter([g.loc[p].lambda_star for p in pairs], [k + off[cfg] for k in range(len(pairs))], color=col, marker=mk,
                   s=36, zorder=3, label=lab)
    ax.axvline(1, color=C["burgundy"], lw=1.4, ls="--", zorder=2)
    ax.text(1.08, -0.9, "REF bounds (λ = 1)", color=C["burgundy"], fontsize=9.5, va="center")
    ax.axvspan(1e-3, 1, color="#F3E3E3", zorder=0)
    ax.text(1.3e-3, -0.9, "not isolable at REF", fontsize=9.5, color=C["burgundy"], va="center")
    ax.set_xscale("log")
    ax.set_xlim(1e-3, 60)
    ax.set_ylim(len(pairs) - 0.4, -1.4)
    ax.set_yticks(range(len(pairs)), [f"{HLAB[a]} vs {HLAB[b]}" for a, b in pairs])
    ax.set_xlabel("λ* — largest bound scale (× REF) at which no observation fits both hypotheses")
    xgrid(ax)
    ax.legend(loc="lower right", fontsize=9.5, frameon=True)
    stamp(ax, COND)
    return finish(fig, meta("V2-F03", "isolability_onset", "f03", "Pairwise isolability matrix",
                            "For each hypothesis pair, how much tighter than REF must the bounds be for no observation to fit both?",
                            [rel(AN / "i1_isolability_onset.csv")],
                            "λ* is the largest bound scale, in units of the REF solver-refinement delta, at which the pair is template-isolable over all ±1 s shifts (isolable iff λ < λ*). Normal vs SID 215 needs bounds about 0.08 × REF even with all channels: a bound limitation, not intrinsic identity (λ* > 0). Pressure-only sensing cannot separate the withdrawals at REF.",
                            "Template-level analysis of one capture per mechanism under hypothetical bounds; says nothing about field sensors."), OUT)


def f04():
    i2 = pd.read_csv(AN / "i2_structural_incidence.csv")
    chans = list(dict.fromkeys(i2.channel))
    rows = list(dict.fromkeys(zip(i2.hypothesis, i2.template)))
    fig = figure(9.6, 5.4)
    title(fig, "Structural incidence: template signal relative to the REF bound")
    ax = fig.subplots()
    bins = [(0, 0.1, "< 0.1", "#F3E3E3"), (0.1, 1, "0.1–1", "#E5E7EB"), (1, 10, "1–10", "#D7ECEE"), (10, np.inf, "> 10", C["teal"])]
    for r, (h, t) in enumerate(rows):
        for c, ch in enumerate(chans):
            v = float(i2[(i2.hypothesis == h) & (i2.template == t) & (i2.channel == ch)].ratio_to_2epsREF.iloc[0])
            fc = next(b[3] for b in bins if b[0] <= v < b[1])
            ax.add_patch(Rectangle((c, r), 1, 1, facecolor=fc, edgecolor=C["white"], lw=1.2))
            if v > 1:
                ax.text(c + 0.5, r + 0.5, f"{v:.1f}", ha="center", va="center", fontsize=8.5, fontweight="bold",
                        color=C["white"] if v >= 10 else C["text"])
    ax.set_xlim(0, len(chans))
    ax.set_ylim(len(rows), 0)
    ax.set_xticks(np.arange(len(chans)) + 0.5, chans)
    ax.set_yticks(np.arange(len(rows)) + 0.5, [f"{HLAB[h]} ({t})" for h, t in rows])
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.legend(handles=[Patch(facecolor=b[3], edgecolor=C["grid"], label=b[2]) for b in bins], title="peak |template| / (2 ε_REF)",
              loc="upper center", bbox_to_anchor=(0.5, -0.08), ncols=4, fontsize=9.5)
    stamp(ax, COND + " · labelled cells exceed 2 ε_REF")
    return finish(fig, meta("V2-F04", "structural_incidence", "f04", "Sensor–hypothesis incidence",
                            "Which channels respond to each mechanism by more than the REF bound?",
                            [rel(AN / "i2_structural_incidence.csv")],
                            "Peak absolute template residual per channel divided by 2 ε_REF. The SID 215 withdrawal exceeds 2 ε_REF on no channel, which explains why it cannot be told apart from normal operation at REF; the SID 213 and SID 312 withdrawals are carried by their branch flow meters (MFS3, MFS1).",
                            "Peak magnitude is a necessary but not sufficient condition for isolability (shifts and rival templates matter: see V2-F03)."), OUT)


def f05():
    h = pd.read_csv(AN / "h1_hy2res_certified_vs_frozen.csv")
    lab = {"electrolyzer_active": "Electrolyzer only", "multiple_active": "Electrolyzer + compressor", "unknown": "Unknown power"}
    cats = [("SPECIFIC", "SPECIFIC", C["teal"], None), ("AMBIGUOUS", "AMBIGUOUS", C["ochre"], None),
            ("UNRESOLVED|INDETERMINATE_HYPOTHESES", "UNRESOLVED: rival not excludable", C["navy"], None),
            ("UNRESOLVED|MODEL_MISMATCH", "UNRESOLVED: outside admitted regions", C["slate"], "///"),
            ("UNRESOLVED|INVALID_MEASUREMENT", "UNRESOLVED: invalid measurement", C["white"], "...")]
    fmap = {"Electrolyzer only": "SPECIFIC", "Both powered": "SPECIFIC", "Ambiguous": "AMBIGUOUS"}
    fig = figure(9.6, 5.4)
    title(fig, "HY2RES: frozen candidate rule versus its certified D(Y) port")
    ax = fig.subplots()
    ylab, y = [], 0
    for state in ["electrolyzer_active", "multiple_active", "unknown"]:
        g = h[h.label == state]
        tot = g.rows.sum()
        frozen = {}
        for r in g.itertuples():
            k = fmap.get(r.frozen_decision)
            if k is None:
                k = "UNRESOLVED|" + r.certified_reason if r.certified_reason in ("INVALID_MEASUREMENT", "MODEL_MISMATCH") else "UNRESOLVED|INDETERMINATE_HYPOTHESES"
            frozen[k] = frozen.get(k, 0) + r.rows
        cert = {}
        for r in g.itertuples():
            k = r.certified_status if r.certified_status != "UNRESOLVED" else f"UNRESOLVED|{r.certified_reason}"
            cert[k] = cert.get(k, 0) + r.rows
        for name, d in (("frozen rule", frozen), ("certified port", cert)):
            left = 0
            for k, _, col, hh in cats:
                v = d.get(k, 0)
                if v:
                    ax.barh(y, v / tot, left=left, color=col, hatch=hh, edgecolor=C["text"] if col == C["white"] else C["white"], height=0.62, zorder=3)
                    if v / tot >= 0.07:
                        ax.text(left + v / tot / 2, y, f"{v:,}", ha="center", va="center", fontsize=9.5,
                                bbox=dict(facecolor=C["white"], edgecolor="none", pad=1.0))
                    left += v / tot
            ylab.append(f"{lab[state]} — {name}  (n = {tot:,})")
            y += 1
    ax.set_yticks(range(len(ylab)), ylab)
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.set_xlabel("Share of test rows within the reference power state")
    xgrid(ax)
    ax.legend(handles=[Patch(facecolor=c, hatch=hh, edgecolor=C["text"] if c == C["white"] else C["white"], label=n) for _, n, c, hh in cats],
              loc="upper center", bbox_to_anchor=(0.4, -0.13), ncols=3, fontsize=9.5)
    stamp(ax, "EXPLORATORY — previously inspected test partition · zero (hypothetical) observation half-width")
    return finish(fig, meta("V2-F05", "hy2res_certified_port", "f05", "Cross-domain software portability (Level A)",
                            "When the frozen HY2RES operating-state rule is run through the formal engine, which of its decisions survive certification?",
                            [rel(AN / "h1_hy2res_certified_vs_frozen.csv"), rel(AN / "h2_hy2res_equivalence_summary.csv")],
                            "The port reproduces every ambiguous and unresolved decision of the frozen rule, but none of its 10,762 singleton calls: the rival state is never excluded by a single-channel certificate, so they become UNRESOLVED. No certified decision is wrong. Frozen-rule UNRESOLVED rows are split by the reason the certified port records for the same rows.",
                            "Level A software portability only: no measurement uncertainty is declared, labels describe electrical power, and the partition was inspected before."), OUT)


def f06():
    acc = pd.read_csv(V2 / "06_reports/ACCEPTANCE_CRITERIA.csv")
    reg = pd.read_csv(V2 / "02_design/HYPOTHESIS_REGISTRY.csv").set_index("id")
    crit = [c for c in acc.columns if c[:1] == "C" and c[1].isdigit()]
    col = {"PASS": (C["teal"], None), "FAIL": (C["burgundy"], "xx"), "BLOCKED": (C["ochre"], "\\\\"), "NOT_APPLICABLE": (C["white"], "..")}
    fig = figure(9.6, 5.4)
    title(fig, "Hypothesis evidence summary against the acceptance criteria")
    ax = fig.subplots()
    for i, r in enumerate(acc.itertuples(index=False)):
        for j, c in enumerate(crit):
            v = getattr(r, c.replace(" ", "_")) if hasattr(r, c.replace(" ", "_")) else acc.iloc[i][c]
            key = v.split(":")[0]
            fc, hh = col[key]
            ax.add_patch(Rectangle((j, i), 1, 1, facecolor=fc, hatch=hh, edgecolor=C["text"] if fc == C["white"] else C["white"], lw=1.0))
        ax.text(len(crit) + 0.15, i + 0.5, reg.loc[r.hypothesis, "status"].replace("_", " "), va="center", fontsize=9.5)
    ax.set_xlim(0, len(crit) + 4.3)
    ax.set_ylim(len(acc), 0)
    ax.set_xticks(np.arange(len(crit)) + 0.5, [c.split(" ")[0] for c in crit])
    ax.set_yticks(np.arange(len(acc)) + 0.5, [f"{h} {reg.loc[h, 'name']}" for h in acc.hypothesis])
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.text(len(crit) + 0.15, -0.25, "Registry status", fontsize=10, fontweight="bold")
    ax.legend(handles=[Patch(facecolor=fc, hatch=hh, edgecolor=C["text"] if fc == C["white"] else C["white"], label=k.replace("_", " ").title())
                       for k, (fc, hh) in col.items()], loc="upper center", bbox_to_anchor=(0.36, -0.07), ncols=4, fontsize=9.5)
    return finish(fig, meta("V2-F06", "hypothesis_evidence_summary", "f06", "Hypothesis evidence summary",
                            "Which acceptance criteria does each hypothesis meet, and what status follows?",
                            [rel(V2 / "06_reports/ACCEPTANCE_CRITERIA.csv"), rel(V2 / "02_design/HYPOTHESIS_REGISTRY.csv")],
                            "C1 provenance, C2 independence, C3 assumptions, C4 ground truth, C5 denominators, C6 comparators, C7 uncertainty, C8 reproducibility, C9 claim–data match, C10 limitations. Only H3, a mathematical/software property, meets every applicable criterion; H9 and H10 are contradicted by direct counterexamples.",
                            "Criterion statuses are judgements recorded with their reasons in ACCEPTANCE_CRITERIA.csv; the figure is a summary, not new evidence."), OUT)


def main():
    setup()
    OUT.mkdir(parents=True, exist_ok=True)
    recs = [f() for f in (f01, f02, f03, f04, f05, f06)]
    m = pd.DataFrame(recs)
    m.to_csv(OUT / "V2_FIGURE_MANIFEST.csv", index=False, lineterminator="\n")
    print(m[["figure_id", "width_px", "height_px", "qa_status", "qa_issues"]].to_string())


if __name__ == "__main__":
    main()
