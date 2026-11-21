"""MHC (Study B, experimental hydrogen compressor) Q1 figures. One function per figure.

Inputs: the accepted Study B evidence-enhancement outputs (bit-identical frozen replay and analysis tables).
Pressure (P-2, barg) and flow (MFC-3, ln/min) are always drawn in separate figures or panels.
"""
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch

from q1fig import finish
from q1style import C, MODEL, REPO, figure, title, xgrid, ygrid

MOD = "fig_mhc"
B = REPO / "study_b/evidence_enhancement/results"
RUNS = (24, 28, 29)
NAME = {"P-2": "P-2 Stage II hydrogen pressure", "MFC-3": "MFC-3 outlet hydrogen flow"}
UNIT = {"P-2": "barg", "MFC-3": "ln/min"}
LIM = ("One MHC apparatus, three held-out runs (serially dependent rows); the recording increment is the observed data "
       "grid, not instrument accuracy; reference prediction only — no event labels, no diagnosis.")


def meta(fid, stem, fn, ttl, q, sources, cap, lim=LIM, ver="values read from accepted Study B tables"):
    return dict(id=fid, stem=f"{fid}_{stem}", function=fn, module=MOD, title=ttl, question=q, sources=sources,
                caption=cap, limitation=lim, study="MHC", verification=ver)


def load():
    an = B / "analysis"
    d = {k: pd.read_csv(an / f"{k}.csv") for k in ("run_metrics", "error_quantiles", "concentration_curves",
                                                     "error_vs_change", "resolution", "controller_role", "tail_shares")}
    d["pred"] = pd.read_csv(B / "replay/replayed_predictions.csv.gz")
    d["b01"] = pd.read_csv(B / "tables/TAB_B01.csv")
    d["amani"] = json.loads((an / "analysis_manifest.json").read_text(encoding="utf-8"))
    rm = json.loads((B / "replay/replay_manifest.json").read_text(encoding="utf-8"))
    dates = rm["dates"]
    d["dates"] = json.loads(dates.replace("'", '"')) if isinstance(dates, str) else dates
    return d


def _box(ax, x, y, w, h, text, fc, ec, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.04", fc=fc, ec=ec, lw=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=11, color=C["text"],
            fontweight="bold" if bold else "normal")


def slug(ch):
    return ch.replace("-", "").lower()


def plot_mhc_measurement_context(d, out):
    fig = figure()
    title(fig, "MHC dual-stage metal-hydride compressor: evaluated channels")
    ax = fig.add_subplot()
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis("off")
    nodes = [(0.2, "H$_2$ inlet\nMFC-1", C["white"], C["slate"], False), (2.2, "Stage I\nP-1", C["white"], C["slate"], False),
             (4.2, "Transition\nMFC-2", C["white"], C["slate"], False),
             (6.2, "Stage II\nP-2 (predicted)", "#E6F2F3", C["teal"], True),
             (8.2, "Outlet\nMFC-3 (predicted)", "#E6F2F3", C["teal"], True)]
    for x, t, fc, ec, b in nodes:
        _box(ax, x, 1.6, 1.6, 1.0, t, fc, ec, b)
    for x in (1.8, 3.8, 5.8, 7.8):
        ax.add_patch(FancyArrowPatch((x, 2.1), (x + 0.4, 2.1), arrowstyle="-|>", mutation_scale=14, color=C["text"], lw=1.2))
    ax.text(5.0, 0.95, "Conceptual order from the workbook channel names; no piping geometry, valve or sensor position is "
            "implied.", ha="center", fontsize=10, color=C["slate"])
    ax.text(9.0, 3.05, "back-pressure control\n(protocol notes)", ha="center", fontsize=10, color=C["teal"])
    b = d["b01"]
    el = b[b.eligible == "yes"]
    cap = (f"Hydrogen path of the MHC v1.2 apparatus as named in the workbook channel headers ('MFC1-H2 Inlet', 'P-1 H2 "
           f"Stage I', 'MFC2-H2 Transition', 'P-2 H2 Stage II', 'MFC3-H2 Outlet'). Study B predicts P-2 (barg) and MFC-3 "
           f"(ln/min) one step ahead. {len(el)} of {len(b)} workbooks are dual-stage compression runs and eligible: "
           f"{int((el.partition == 'development').sum())} development and {int((el.partition == 'test').sum())} held-out "
           "test runs. MFC-3 is described in the protocol notes as the outlet back-pressure controller.")
    return finish(fig, meta("Q1_B01", "mhc_measurement_context", "plot_mhc_measurement_context",
                            "Measurement context", "Which physical channels are predicted in Study B?",
                            ["study_b/evidence_enhancement/results/tables/TAB_B01.csv (workbook headers and notes)"], cap,
                            lim="Conceptual schematic only."), out)


def plot_mhc_run_partition(d, out):
    b = d["b01"].copy()
    b["valid_pairs"] = pd.to_numeric(b.valid_pairs, errors="coerce").fillna(0)
    fig = figure()
    title(fig, "Twenty-nine workbooks: eight dual-stage runs are eligible, three are held out")
    ax = fig.add_subplot()
    colr = {"development": (C["blue"], None), "test": (C["teal"], "//"), "outside scope": (C["grid"], None)}
    for _, r in b.iterrows():
        c, h = colr[r.partition]
        ax.bar(r.run, r.valid_pairs, color=c, hatch=h, edgecolor=C["white"], width=0.8, zorder=3)
        if r.partition == "outside scope":
            ax.scatter(r.run, 150, marker="x", s=30, color=C["slate"], zorder=4)
    ax.set_xticks(b.run)
    ax.tick_params(axis="x", labelsize=9)
    ax.set_xlabel("MHC workbook (run number)")
    ax.set_ylabel("Valid one-step prediction pairs")
    ygrid(ax)
    fig.legend(handles=[Patch(facecolor=C["blue"], label="Development (dual-stage)"),
                        Patch(facecolor=C["teal"], hatch="//", edgecolor=C["white"], label="Held-out test (dual-stage)"),
                        Line2D([], [], marker="x", ls="", color=C["slate"], label="Outside scope (other operation)")],
               loc="outside lower center", ncol=3)
    ops = b[b.partition == "outside scope"].operation.value_counts()
    cap = ("Eligibility and partition of all 29 MHC v1.2 workbooks (frozen Study B values; valid pairs recounted by the "
           f"bit-identical replay). Outside scope: {', '.join(f'{k.lower()} ({v})' for k, v in ops.items())}. Held-out test "
           f"runs 24, 28 and 29 contribute {int(b[b.partition == 'test'].valid_pairs.sum()):,} pairs per channel.")
    return finish(fig, meta("Q1_B02", "mhc_run_partition", "plot_mhc_run_partition", "Run eligibility and partition",
                            "Which experimental runs are evaluated, and how are they partitioned?",
                            ["study_b/evidence_enhancement/results/tables/TAB_B01.csv"], cap), out)


def _traces(d, out, ch, fid):
    pr = d["pred"][d["pred"].channel == ch]
    win = {str(k): v for k, v in d["amani"]["representative_windows"].items()}
    fig = figure()
    title(fig, f"{NAME[ch]}: observed values and one-step predictions")
    axs = fig.subplots(1, 3)
    n = 0
    for ax, run in zip(axs, RUNS):
        s, e = win[str(run)]
        date = d["dates"][str(run)][0]
        t0 = datetime.fromisoformat(f"{date}T{s}").replace(tzinfo=timezone.utc).timestamp()
        t1 = datetime.fromisoformat(f"{date}T{e}").replace(tzinfo=timezone.utc).timestamp()
        w = pr[(pr.run == run) & (pr.target_time_s >= t0) & (pr.target_time_s <= t1)]
        n += len(w)
        t = (w.target_time_s - t0) / 60
        ax.plot(t, w.y_true, color=C["text"], lw=1.8, label="Observed", drawstyle="steps-post")
        ax.plot(t, w.persistence, color=MODEL["persistence"]["color"], lw=1.0, ls="-", label="Persistence",
                drawstyle="steps-post")
        ax.plot(t, w.ridge, color=MODEL["ridge"]["color"], lw=1.0, ls="--", label="Ridge")
        ax.set_title(f"Run {run} ({s[:5]}–{e[:5]})", fontsize=12)
        ax.set_xlabel("Minutes from window start")
        ygrid(ax)
    axs[0].set_ylabel(f"{ch} ({UNIT[ch]})")
    fig.legend(*axs[0].get_legend_handles_labels(), loc="outside lower center", ncol=3)
    cap = (f"{NAME[ch]} in the three held-out runs over the representative cycles declared in the analysis manifest "
           f"({n:,} displayed observations), with the frozen persistence and Ridge one-step predictions. Persistence repeats "
           "the previous recorded value; Ridge is the frozen two-input linear reference. Times are workbook clock times.")
    return finish(fig, meta(fid, f"mhc_{slug(ch)}_prediction_traces", f"plot_mhc_{slug(ch)}_traces",
                            f"{ch} prediction traces", f"How do the reference predictions follow measured {ch}?",
                            ["study_b/evidence_enhancement/results/replay/replayed_predictions.csv.gz",
                             "analysis/analysis_manifest.json (representative_windows)"], cap), out)


def plot_mhc_p2_traces(d, out):
    return _traces(d, out, "P-2", "Q1_B03")


def plot_mhc_mfc3_traces(d, out):
    return _traces(d, out, "MFC-3", "Q1_B04")


def _per_run(d, out, ch, fid):
    r = d["run_metrics"]
    r = r[r.channel == ch].set_index("run").loc[list(RUNS)]
    fig = figure()
    title(fig, f"{ch}: persistence has lower MAE in every held-out run")
    axs = fig.subplots(1, 2)
    for ax, met, lab in [(axs[0], "mae", "MAE"), (axs[1], "rmse", "RMSE")]:
        y = np.arange(len(RUNS))
        for j, m in enumerate(("persistence", "ridge")):
            st = MODEL[m]
            ax.scatter(r[f"{m}_{met}"], y + (j - 0.5) * 0.2, marker=st["marker"], s=70, color=st["color"],
                       edgecolor=C["text"], lw=0.5, zorder=3, label=st["label"])
        ax.set_yticks(y, [f"Run {k}" for k in RUNS])
        ax.invert_yaxis()
        ax.set_xlabel(f"{lab} ({UNIT[ch]})")
        xgrid(ax)
    fig.legend(*axs[0].get_legend_handles_labels(), loc="outside lower center", ncol=2)
    dm = "; ".join(f"run {k}: {r.loc[k, 'delta_mae']:+.4f} / {r.loc[k, 'delta_rmse']:+.5f}" for k in RUNS)
    cap = (f"Run-level MAE and RMSE of the two frozen references for {NAME[ch]} ({UNIT[ch]}; units never combined). "
           f"Ridge − persistence ΔMAE / ΔRMSE: {dm}. The largest relative RMSE change is "
           f"{r.rel_delta_rmse.abs().max():.2%} of the persistence RMSE.")
    return finish(fig, meta(fid, f"mhc_{slug(ch)}_per_run", f"plot_mhc_{slug(ch)}_per_run",
                            f"{ch} per-run performance", f"Is the {ch} model ranking stable across held-out runs?",
                            ["study_b/evidence_enhancement/results/analysis/run_metrics.csv"], cap), out)


def plot_mhc_p2_per_run(d, out):
    return _per_run(d, out, "P-2", "Q1_B05")


def plot_mhc_mfc3_per_run(d, out):
    return _per_run(d, out, "MFC-3", "Q1_B06")


def _ecdf(d, out, ch, fid):
    pr = d["pred"][d["pred"].channel == ch]
    q = d["error_quantiles"]
    q = q[(q.run == "all 3 runs") & (q.channel == ch)].set_index("model")
    fig = figure()
    title(fig, f"{ch}: persistence is exactly right on most rows; the tails coincide")
    ax = fig.add_subplot()
    floor = 1e-4 if ch == "P-2" else 1e-5
    for m in ("persistence", "ridge"):
        e = np.sort(np.abs(pr.y_true - pr[m]).to_numpy())
        ax.step(np.maximum(e, floor), np.arange(1, len(e) + 1) / len(e), where="post", color=MODEL[m]["color"],
                ls=MODEL[m]["ls"], lw=1.6, label=f"{MODEL[m]['label']} (exact-zero share {q.loc[m, 'zero_error_fraction']:.3f})")
    ax.set_xscale("log")
    ax.set_xlabel(f"Absolute one-step error ({UNIT[ch]}; exact zeros drawn at {floor:g})")
    ax.set_ylabel("Cumulative share of rows")
    ax.set_ylim(0, 1.01)
    ygrid(ax)
    xgrid(ax)
    fig.legend(loc="outside lower center", ncol=2)
    cap = (f"Empirical cumulative distribution of absolute errors for {NAME[ch]}, pooled over the three held-out runs "
           f"({int(q.loc['persistence', 'n']):,} rows; serially dependent). Persistence is exactly right on "
           f"{q.loc['persistence', 'zero_error_fraction']:.1%} of rows; Ridge never is (continuous output). Median error: "
           f"persistence {q.loc['persistence', 'p50']:.3g}, Ridge {q.loc['ridge', 'p50']:.3g}; p99: "
           f"{q.loc['persistence', 'p99']:.3g} vs {q.loc['ridge', 'p99']:.3g} {UNIT[ch]}.")
    return finish(fig, meta(fid, f"mhc_{slug(ch)}_error_ecdf", f"plot_mhc_{slug(ch)}_ecdf",
                            f"{ch} error distribution", f"How do central and tail {ch} errors differ between the references?",
                            ["study_b/evidence_enhancement/results/replay/replayed_predictions.csv.gz",
                             "analysis/error_quantiles.csv"], cap,
                            ver="ECDF recomputed from the replayed predictions; quantiles from error_quantiles.csv"), out)


def plot_mhc_p2_ecdf(d, out):
    return _ecdf(d, out, "P-2", "Q1_B07")


def plot_mhc_mfc3_ecdf(d, out):
    return _ecdf(d, out, "MFC-3", "Q1_B08")


def plot_mhc_error_concentration(d, out):
    c = d["concentration_curves"]
    t = d["tail_shares"]
    fig = figure()
    title(fig, "Squared error is concentrated in a few rows for both references")
    axs = fig.subplots(1, 2, sharey=True)
    for ax, ch in zip(axs, ("P-2", "MFC-3")):
        for m in ("persistence", "ridge"):
            g = c[(c.channel == ch) & (c.model == m)]
            ax.plot(g.fraction, g.cumulative_share, color=MODEL[m]["color"], ls=MODEL[m]["ls"], lw=1.6, label=MODEL[m]["label"])
        ax.set_xscale("log")
        ax.set_title(f"{ch} ({UNIT[ch]})", fontsize=12)
        ax.set_xlabel("Fraction of rows with the largest squared errors")
        ygrid(ax)
        xgrid(ax)
    axs[0].set_ylabel("Cumulative share of total squared error")
    fig.legend(*axs[0].get_legend_handles_labels(), loc="outside lower center", ncol=2)
    p1 = t[(t.channel == "MFC-3") & (t.model == "persistence") & np.isclose(t.tail_fraction, 0.01)]
    cap = ("Concentration curves of squared error, pooled over the three held-out runs: the share of total SSE carried "
           "by the given fraction of largest-error rows (dimensionless; channels in separate panels). The two references' "
           f"curves almost coincide. For MFC-3 the top 1 % of rows carry {p1.tail_share.min():.1%}–{p1.tail_share.max():.1%} "
           "of persistence SSE per run (TAB_B05), so RMSE comparisons are decided by rare large steps.")
    return finish(fig, meta("Q1_B09", "mhc_error_concentration", "plot_mhc_error_concentration",
                            "Error-tail concentration", "Do rare large errors dominate RMSE?",
                            ["study_b/evidence_enhancement/results/analysis/concentration_curves.csv", "tail_shares.csv"],
                            cap), out)


def _vs_change(d, out, ch, fid):
    e = d["error_vs_change"]
    e = e[(e.run == "all 3 runs") & (e.channel == ch) & (e.n > 0)]
    fig = figure()
    title(fig, f"{ch}: Ridge loses on unchanged rows and gains on larger recorded steps")
    axs = fig.subplots(1, 2, sharey=True)
    y = np.arange(len(e))
    axs[0].barh(y, e.delta_mae, color=[C["burgundy"] if v > 0 else C["teal"] for v in e.delta_mae], height=0.55, zorder=3)
    axs[1].barh(y, e.delta_sse, color=[C["burgundy"] if v > 0 else C["teal"] for v in e.delta_sse], height=0.55,
                hatch="//", edgecolor=C["white"], zorder=3)
    from matplotlib.ticker import MaxNLocator
    for ax in axs:
        ax.axvline(0, color=C["text"], lw=0.8)
        ax.xaxis.set_major_locator(MaxNLocator(5))
        xgrid(ax)
    axs[0].set_yticks(y, [f"{b}\n(n = {n:,})" for b, n in zip(e.bin, e.n)])
    axs[0].invert_yaxis()
    axs[0].set_xlabel(f"ΔMAE, Ridge − persistence ({UNIT[ch]})")
    axs[1].set_xlabel(f"ΔSSE, Ridge − persistence ({UNIT[ch]}²)")
    cap = (f"Ridge − persistence differences for {NAME[ch]} by observed one-step change |Δy| in recording increments "
           f"(bins fixed before scoring; pooled held-out runs). Positive (burgundy) favours persistence, negative (teal) "
           f"favours Ridge. Total ΔSSE {e.delta_sse.sum():+.2f} {UNIT[ch]}²: Ridge's small RMSE gain comes from rows with "
           "recorded changes, while its MAE loss accumulates on unchanged rows. Retrospective: |Δy| uses the outcome.")
    return finish(fig, meta(fid, f"mhc_{slug(ch)}_error_vs_change", f"plot_mhc_{slug(ch)}_vs_change",
                            f"{ch} error versus observed change", f"Where does Ridge gain or lose against persistence on {ch}?",
                            ["study_b/evidence_enhancement/results/analysis/error_vs_change.csv"], cap), out)


def plot_mhc_p2_vs_change(d, out):
    return _vs_change(d, out, "P-2", "Q1_B10")


def plot_mhc_mfc3_vs_change(d, out):
    return _vs_change(d, out, "MFC-3", "Q1_B11")


def plot_mhc_resolution(d, out):
    r = d["resolution"].set_index("channel")
    fig = figure()
    title(fig, "In recording increments, the MAE differences are at most about one step")
    ax = fig.add_subplot()
    chans = ["P-2", "MFC-3"]
    items = [("persistence_mae_increments", "Persistence MAE", MODEL["persistence"]),
             ("ridge_mae_increments", "Ridge MAE", MODEL["ridge"]),
             ("run_mean_delta_mae_increments", "Run-mean ΔMAE (Ridge − persistence)", dict(color=C["burgundy"], marker="D"))]
    for j, (col, lab, st) in enumerate(items):
        ax.scatter(r.loc[chans, col], np.arange(2) + (j - 1) * 0.18, marker=st["marker"], s=80, color=st["color"],
                   edgecolor=C["text"], lw=0.5, zorder=3, label=lab)
    ax.axvline(1, color=C["slate"], ls="--", lw=1)
    ax.text(1.05, -0.42, "one recording increment", fontsize=10, color=C["slate"])
    ax.set_yticks([0, 1], [f"{c}\n(increment {r.loc[c, 'observed_increment']:g} {r.loc[c, 'unit']})" for c in chans])
    ax.set_ylim(1.5, -0.6)
    ax.set_xlabel("Error in observed recording increments (dimensionless)")
    xgrid(ax)
    fig.legend(loc="outside lower center", ncol=3)
    cap = (f"Errors divided by each channel's observed recording increment (smallest step between distinct recorded "
           f"values: P-2 {r.loc['P-2', 'observed_increment']:g} barg, MFC-3 {r.loc['MFC-3', 'observed_increment']:g} ln/min; "
           f"all values on grid). Run-mean ΔMAE is {r.loc['P-2', 'run_mean_delta_mae_increments']:.3f} increments for P-2 "
           f"and {r.loc['MFC-3', 'run_mean_delta_mae_increments']:.2f} for MFC-3. Persistence exact-match share: "
           f"{r.loc['P-2', 'persistence_exact_match']:.3f} and {r.loc['MFC-3', 'persistence_exact_match']:.3f}. The increment "
           "is recorded quantization, not instrument resolution or accuracy (neither is documented in the source).")
    return finish(fig, meta("Q1_B12", "mhc_recording_resolution", "plot_mhc_resolution", "Errors in recording increments",
                            "Are the model differences resolvable on the recording grid?",
                            ["study_b/evidence_enhancement/results/analysis/resolution.csv"], cap), out)


def plot_mhc_control_role(d, out):
    c = d["controller_role"].set_index("run").loc[list(RUNS)]
    fig = figure()
    title(fig, "Stage II pressure stays at the outlet set point while MFC-3 is closed")
    ax = fig.add_subplot()
    y = np.arange(len(RUNS))
    ax.hlines(y - 0.12, c.p2_when_flowing_p05, c.p2_when_flowing_p95, color=C["teal"], lw=3, zorder=2,
              label="P-2 while MFC-3 flows (5th–95th percentile)")
    ax.scatter(c.p2_when_flowing_median, y - 0.12, marker="o", s=60, color=C["teal"], edgecolor=C["text"], zorder=3,
               label="Median while MFC-3 flows")
    ax.scatter(c.p2_when_zero_median, y + 0.12, marker="s", s=60, color=C["navy"], edgecolor=C["text"], zorder=3,
               label="Median while MFC-3 = 0")
    ax.scatter(c.p2_when_zero_max, y + 0.12, marker="|", s=300, color=C["navy"], lw=2, zorder=3, label="Maximum while MFC-3 = 0")
    ax.scatter(c.nominal_outlet_bar, y, marker="D", s=70, color=C["burgundy"], zorder=4, label="Nominal outlet set pressure")
    ax.set_yticks(y, [f"Run {k}\n(MFC-3 flowing {c.loc[k, 'mfc3_flowing_fraction']:.0%} of rows)" for k in RUNS])
    ax.invert_yaxis()
    ax.set_xlabel("P-2 Stage II pressure (barg)")
    xgrid(ax)
    fig.legend(loc="outside right center", fontsize=9.5)
    cap = ("Stage II pressure P-2 conditioned on whether the outlet controller MFC-3 records flow, per held-out run. While "
           f"MFC-3 is zero, P-2 never exceeds the nominal outlet set pressure by more than "
           f"{(c.p2_when_zero_max - c.nominal_outlet_bar).max():.1f} bar (maxima {', '.join(f'{v:g}' for v in c.p2_when_zero_max)} "
           f"vs set points {', '.join(f'{v:g}' for v in c.nominal_outlet_bar)} barg). This is consistent with MFC-3 acting "
           "as a back-pressure release: MFC-3 is a controlled output, not an independent disturbance. The set-point "
           "signal itself is not recorded.")
    return finish(fig, meta("Q1_B13", "mhc_mfc3_control_role", "plot_mhc_control_role", "MFC-3 control role",
                            "Why must MFC-3 be interpreted as a controlled output?",
                            ["study_b/evidence_enhancement/results/analysis/controller_role.csv"], cap), out)


FIGURES = [plot_mhc_measurement_context, plot_mhc_run_partition, plot_mhc_p2_traces, plot_mhc_mfc3_traces,
           plot_mhc_p2_per_run, plot_mhc_mfc3_per_run, plot_mhc_p2_ecdf, plot_mhc_mfc3_ecdf, plot_mhc_error_concentration,
           plot_mhc_p2_vs_change, plot_mhc_mfc3_vs_change, plot_mhc_resolution, plot_mhc_control_role]
