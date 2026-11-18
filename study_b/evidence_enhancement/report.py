"""Tables (CSV + Markdown) and standalone figures (PNG + SVG + caption) for the
Study B evidence enhancement. Reads only replay and analysis outputs plus frozen
Study B tables; performs no fitting or scoring.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import textwrap
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
C = dict(bg="#F4F4E9", navy="#10263E", teal="#007F86", blue="#356CB1", slate="#64748B",
         red="#A33F43", grid="#D9DFDE", text="#1F2933")
MODEL_STYLE = {"persistence": dict(color=C["slate"], ls="--", label="Persistence (B0)"),
               "ridge": dict(color=C["teal"], ls="-", label="Ridge (B1)")}
UNIT = {"P-2": "barg", "MFC-3": "ln/min"}
NAME = {"P-2": "P-2 Stage II pressure", "MFC-3": "MFC-3 outlet hydrogen flow"}
SLUG = {"P-2": "P2", "MFC-3": "MFC3"}


def style():
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["IBM Plex Sans", "Segoe UI", "DejaVu Sans"],
        "font.size": 11, "figure.facecolor": C["bg"], "axes.facecolor": C["bg"], "savefig.facecolor": C["bg"],
        "axes.edgecolor": C["slate"], "axes.labelcolor": C["text"], "text.color": C["text"],
        "xtick.color": C["text"], "ytick.color": C["text"], "axes.spines.top": False,
        "axes.spines.right": False, "axes.linewidth": .8, "grid.color": C["grid"], "grid.linewidth": .6,
        "legend.frameon": False, "svg.fonttype": "none", "axes.titlesize": 12.5, "axes.titleweight": "semibold",
        "axes.titlelocation": "left", "axes.labelsize": 11.5})
    return plt


def footnote(fig, text):
    fig.text(0.012, 0.014, textwrap.fill(text, 160), ha="left", va="bottom", fontsize=8.6, color=C["slate"],
             linespacing=1.25)


def save(plt, fig, out, name, caption, question, sources, function):
    fig.savefig(out / f"{name}.png", dpi=400)
    fig.savefig(out / f"{name}.svg")
    (out / f"{name}.caption.md").write_text(
        f"**{name}.** {caption}\n\nScientific question: {question}\n\nSource data: "
        + ", ".join(f"`{s}`" for s in sources) + f"\n\nReproduction function: `report.{function}`\n",
        encoding="utf-8", newline="\n")
    plt.close(fig)


def md_table(df):
    def fmt(v):
        if isinstance(v, float):
            return "—" if np.isnan(v) else f"{v:.6g}"
        return str(v).replace("|", "/")
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    lines += ["| " + " | ".join(fmt(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(lines)


def export(df, out, name, title, note):
    df.to_csv(out / f"{name}.csv", index=False, lineterminator="\n")
    text = f"### {name} — {title}\n\n{note}\n\n{md_table(df)}\n"
    (out / f"{name}.md").write_text(text, encoding="utf-8", newline="\n")
    return text


# --------------------------------------------------------------------------- tables

CONFLICTS = {
    24: "Operator note: Stage I exceeded the 90 bar safety-valve set pressure in transition; 'some hydrogen might have "
        "been released'; experiment stopped after a repeat (not a qualified event label)",
    25: "Starts from fully absorbed Stage I inherited from excluded capacity run 5; note 'valves opened a little too late'",
    22: "Note: 'outlet valve opened too late'",
    23: "Note: 'outlet valve opened too late'",
    26: "Note refers to 'Experiments 67 and 68 ... recorded in one go' (numbering inconsistent with 26/27); "
        "'valves opened too late'",
    27: "Header says 'Cycle time 15 min'; overview half-cycle 10 min and logged switch-overs 10 min apart; "
        "note 'error in back pressure control, pressure too low'; recorded directly after 26",
    28: "'Starting the compressor from an undefined state'",
    29: "'Starting the compressor from an undefined state'",
}


def table_b01(replay_meta):
    rows = []
    with (STUDY / "tables/table_1_eligibility.csv").open(encoding="utf-8-sig", newline="") as s:
        for r in csv.DictReader(s):
            run = int(r["run"])
            eligible = r["eligible"] == "True"
            rows.append(dict(
                run=run, recording_date=r["date"], stage=r["stage"], operation=r["operation"],
                eligible="yes" if eligible else "no", partition=r["role"],
                valid_pairs=int(replay_meta["eligible_pairs"].get(str(run), 0)) if eligible else 0,
                pressure_unit=r["pressure_unit"] or "—", flow_unit=r["flow_unit"] or "—",
                initial_state=(r["initial_state"] or "—")[:160], metadata_conflicts=CONFLICTS.get(run, "—"),
                exclusion_reason=r["exclusion"] or "—",
                dependence=("same apparatus; " + ({"12 May": "recorded with 23", "18 July": "26→27 recorded in one go",
                                                     "22 July": "28 and 29 same day"}.get(r["recording_group"], "")
                                                    if eligible else "")).strip("; ")))
    return pd.DataFrame(rows)


def table_b02(gate):
    g = gate.pivot_table(index=["run", "channel", "model", "n_replayed"], columns="metric",
                         values=["frozen", "replayed", "abs_diff"], aggfunc="first").reset_index()
    g.columns = ["run", "channel", "model", "n", "frozen_mae", "frozen_rmse", "replayed_mae", "replayed_rmse",
                 "abs_diff_mae", "abs_diff_rmse"][:4] + [f"{a}_{b}" for a, b in g.columns[4:]]
    g = g.rename(columns={"abs_diff_mae": "abs_diff_mae", "abs_diff_rmse": "abs_diff_rmse"})
    passed = gate.groupby(["run", "channel", "model"]).passed.all().reset_index()
    g = g.merge(passed, on=["run", "channel", "model"])
    g["verification"] = np.where(g.passed, "PASS (bit-identical)", "FAIL")
    return g.drop(columns="passed")[["run", "channel", "model", "n", "frozen_mae", "replayed_mae", "frozen_rmse",
                                     "replayed_rmse", "abs_diff_mae", "abs_diff_rmse", "verification"]]


def table_b03(runs):
    rows = []
    for r in runs.itertuples():
        interp = ("Persistence lower MAE; Ridge lower RMSE" if r.delta_mae > 0 and r.delta_rmse < 0 else
                  "Persistence lower MAE and RMSE" if r.delta_mae > 0 else "Ridge lower MAE")
        rows.append(dict(run=r.run, channel=r.channel, unit=r.unit, scored_rows=r.n,
                         persistence_mae=r.persistence_mae, ridge_mae=r.ridge_mae, delta_mae=r.delta_mae,
                         rel_delta_mae=r.rel_delta_mae, persistence_rmse=r.persistence_rmse, ridge_rmse=r.ridge_rmse,
                         delta_rmse=r.delta_rmse, rel_delta_rmse=r.rel_delta_rmse, delta_sse=r.delta_sse,
                         share_of_channel_delta_sse=r.delta_sse_share, interpretation=interp))
    return pd.DataFrame(rows)


# -------------------------------------------------------------------------- figures

def fig_b01(plt, out):
    fig = plt.figure(figsize=(9.6, 5.4))
    ax = fig.add_axes([0.02, 0.12, 0.96, 0.8])
    ax.set_xlim(0, 100), ax.set_ylim(0, 50), ax.axis("off")
    ax.set_title("Two-stage metal-hydride compressor: evaluated channels (conceptual sequence)", pad=4)
    y = 30
    boxes = [(7, 12, "H₂ supply\n(inlet\nregulator)", C["grid"]), (36, 13, "Stage I\nhydride tank", "white"),
             (66, 13, "Stage II\nhydride tank", "white"), (93, 9, "Outlet", C["grid"])]
    for x, w, label, fc in boxes:
        ax.add_patch(plt.Rectangle((x - w / 2, y - 6), w, 12, fc=fc, ec=C["navy"], lw=1.3))
        ax.text(x, y, label, ha="center", va="center", fontsize=10)
    ax.plot([13, 29.5], [y, y], color=C["slate"], lw=1.2)
    ax.plot([42.5, 59.5], [y, y], color=C["slate"], lw=1.2)
    ax.plot([72.5, 87.5], [y, y], color=C["slate"], lw=1.2)
    for x, lab, col, note in ((20.5, "MFC-1", C["slate"], "inlet flow"), (51, "MFC-2", C["slate"], "transition flow"),
                              (80, "MFC-3", C["red"], "outlet flow;\nback-pressure control")):
        ax.add_patch(plt.Circle((x, y), 2.4, fc="white", ec=col, lw=1.6))
        ax.text(x, y, "F", ha="center", va="center", fontsize=9.5, weight="semibold", color=col)
        ax.text(x, y + 4.2, lab, ha="center", va="bottom", fontsize=10, color=col, weight="semibold")
        ax.text(x, y - 4.2, note, ha="center", va="top", fontsize=8.8, color=C["slate"])
    for x, lab, col in ((36, "P-1", C["slate"]), (66, "P-2", C["teal"])):
        ax.plot([x, x], [y + 6, y + 11], color=col, lw=1.2)
        ax.add_patch(plt.Circle((x, y + 13.2), 2.2, fc="white", ec=col, lw=1.6))
        ax.text(x, y + 13.2, "P", ha="center", va="center", fontsize=9.5, weight="semibold", color=col)
        ax.text(x + 3, y + 13.2, lab + (" (target)" if lab == "P-2" else ""), va="center", fontsize=10, color=col,
                weight="semibold" if lab == "P-2" else "normal")
    ax.text(51, 10, "Evaluated targets: P-2 (barg) and MFC-3 (ln/min), one-step-ahead from their own current values. "
                    "Heat-transfer-fluid loops (P-4/P-5, MF-1/MF-2) not used.", ha="center", fontsize=9.5)
    footnote(fig, "Conceptual order from workbook channel names ('MFC1-H2 Inlet', 'MFC2-H2 Transition', 'MFC3-H2 Outlet', "
                  "'P-1 H2 Stage I', 'P-2 H2 Stage II') and dual-stage notes ('back pressure is controlled by MFC-3'). "
                  "No piping geometry, valves or sensor positions are implied. Source: MHC v1.2 (CC BY 4.0).")
    save(plt, fig, out, "FIG_B01_measurement_context",
         "Conceptual order of the hydrogen path and the two evaluated channels. MFC-3 is the outlet mass-flow "
         "controller that holds Stage II back pressure; P-2 is the Stage II hydrogen pressure.",
         "What physical system and channels are evaluated?", ["workbook channel headers and protocol notes"], "fig_b01")


def window_rows(d, run, start, end, date):
    t0 = datetime.fromisoformat(f"{date}T{start}").replace(tzinfo=timezone.utc).timestamp()
    t1 = datetime.fromisoformat(f"{date}T{end}").replace(tzinfo=timezone.utc).timestamp()
    return d[(d.run == run) & (d.target_time_s >= t0) & (d.target_time_s <= t1)], t0


def fig_b02(plt, out, d, windows, dates, ch):
    runs = (24, 28, 29)
    fig, axes = plt.subplots(2, 3, figsize=(9.6, 5.4), sharex="col", gridspec_kw=dict(height_ratios=[2.2, 1]))
    total = 0
    for j, run in enumerate(runs):
        start, end = windows[str(run)]
        w, t0 = window_rows(d[d.channel == ch], run, start, end, dates[str(run)][0])
        total += len(w)
        t = (w.target_time_s - t0) / 60
        a, b = axes[0, j], axes[1, j]
        a.plot(t, w.y_true, color=C["navy"], lw=1.6, label="Observed")
        a.plot(t, w.persistence, **{**MODEL_STYLE["persistence"], "lw": 1.0})
        a.plot(t, w.ridge, **{**MODEL_STYLE["ridge"], "lw": 1.0})
        b.plot(t, w.y_true - w.ridge, color=C["teal"], lw=1.0)
        b.plot(t, w.y_true - w.persistence, color=C["navy"], lw=.7, ls=(0, (2, 2)))
        b.axhline(0, color=C["grid"], lw=.8)
        a.set_title(f"Run {run} · {start[:5]}–{end[:5]} (n = {len(w):,})", fontsize=10.5)
        a.grid(axis="y"), b.grid(axis="y")
        b.set_xlabel("Minutes from representative-cycle start")
        if j == 0:
            a.set_ylabel(f"{ch} ({UNIT[ch]})")
            b.set_ylabel(f"Error ({UNIT[ch]})")
    axes[0, 0].legend(loc="upper left", fontsize=8.5)
    fig.suptitle(f"{NAME[ch]}: observed values and one-step predictions, source-declared representative cycles",
                 x=0.012, ha="left", fontsize=12.5, weight="semibold")
    plt.subplots_adjust(left=0.08, right=0.99, top=0.86, bottom=0.2, hspace=0.12, wspace=0.18)
    footnote(fig, "Windows are the 'Representative Cycle' Start/End times written in each workbook's protocol block "
                  "(selected before scoring). Runs are plotted separately; no trace crosses runs. Ridge and persistence "
                  "overlap at this scale because one-step corrections are a few hundredths of a unit.")
    save(plt, fig, out, f"FIG_B02_{SLUG[ch]}_prediction_traces",
         f"{NAME[ch]} with persistence and frozen Ridge predictions over each held-out run's source-declared "
         f"representative cycle ({total:,} displayed observations), and the corresponding one-step errors.",
         "How do the predictions track the measured signal?", ["replayed_predictions.csv.gz",
                                                                "workbook protocol block"], "fig_b02")


def fig_b03(plt, out, runs, ch):
    r = runs[runs.channel == ch].sort_values("run")
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 5.4))
    for ax, metric in zip(axes, ("mae", "rmse")):
        for i, row in enumerate(r.itertuples()):
            p, q = getattr(row, f"persistence_{metric}"), getattr(row, f"ridge_{metric}")
            ax.plot([p, q], [i, i], color=C["grid"], lw=3, zorder=1)
            ax.scatter(p, i, s=90, color=C["slate"], marker="s", zorder=3)
            ax.scatter(q, i, s=90, color=C["teal"], marker="o", zorder=3)
            rel = getattr(row, f"rel_delta_{metric}")
            ax.text(max(p, q) * 1.02 + (0.002 if ch == "P-2" else 0.0005), i,
                    f"{q - p:+.4g} ({rel:+.2%})", va="center", fontsize=9.5,
                    color=C["red"] if q > p else C["teal"])
        ax.set_yticks(range(len(r)), [f"Run {x.run}\nn = {x.n:,}" for x in r.itertuples()])
        ax.invert_yaxis()
        lo = min(r[f"persistence_{metric}"].min(), r[f"ridge_{metric}"].min())
        hi = max(r[f"persistence_{metric}"].max(), r[f"ridge_{metric}"].max())
        ax.set_xlim(0, hi * 1.75)
        ax.set_xlabel(f"{metric.upper()} ({UNIT[ch]})")
        ax.grid(axis="x"), ax.set_axisbelow(True)
        ax.set_title(f"({'a' if metric == 'mae' else 'b'}) {metric.upper()} per held-out run", fontsize=11.5)
    h = [plt.Line2D([], [], marker="s", ls="", color=C["slate"], ms=8, label="Persistence (B0)"),
         plt.Line2D([], [], marker="o", ls="", color=C["teal"], ms=8, label="Ridge (B1)")]
    fig.legend(handles=h, loc="upper right", ncol=2, fontsize=9.5)
    fig.suptitle(f"{NAME[ch]}: model ranking by run", x=0.012, ha="left", fontsize=12.5, weight="semibold")
    plt.subplots_adjust(left=0.1, right=0.97, top=0.84, bottom=0.17, wspace=0.35)
    footnote(fig, "Axes start at zero. Labels give Ridge − Persistence (relative change). Three held-out workbooks from "
                  "two recording dates on one apparatus; no significance test is meaningful at n = 3.")
    save(plt, fig, out, f"FIG_B03_{SLUG[ch]}_per_run_performance",
         f"Per-run MAE and RMSE for {NAME[ch]}. Persistence has the lower MAE in every run; Ridge's RMSE is "
         "slightly lower in most runs.", "Is the model ranking stable across held-out runs?",
         ["run_metrics.csv"], "fig_b03")


def fig_b04(plt, out, d, ch):
    g = d[d.channel == ch]
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    floor = {"P-2": 1e-4, "MFC-3": 1e-4}[ch]
    for m in ("persistence", "ridge"):
        a = np.sort(np.abs(g["e_" + m].values))
        f = np.arange(1, len(a) + 1) / len(a)
        zero = (a == 0).mean()
        ax.step(np.maximum(a, floor), f, where="post", **{**MODEL_STYLE[m], "lw": 1.8})
        if zero:
            ax.scatter([floor], [zero], color=MODEL_STYLE[m]["color"], s=50, zorder=4)
            ax.annotate(f"{zero:.1%} exactly zero", (floor, zero), xytext=(10, -14), textcoords="offset points",
                        fontsize=9.5, color=MODEL_STYLE[m]["color"])
    inc = {"P-2": 0.2, "MFC-3": 0.01}[ch]
    ax.axvline(inc, color=C["navy"], lw=1, ls=":")
    ax.text(inc * 1.08, 0.05, f"recording increment {inc:g} {UNIT[ch]}", fontsize=9.5, color=C["navy"])
    ax.axhline(0.99, color=C["grid"], lw=1)
    ax.text(floor * 1.2, 0.995, "99th percentile", fontsize=8.5, color=C["slate"], va="bottom")
    ax.set_xscale("log"), ax.set_ylim(0, 1.03)
    ax.set_xlabel(f"Absolute one-step error ({UNIT[ch]}; zeros drawn at {floor:g})")
    ax.set_ylabel("Cumulative fraction of scored rows")
    ax.grid(), ax.set_axisbelow(True), ax.legend(loc="center right")
    ax.set_title(f"{NAME[ch]}: absolute-error distributions (n = {len(g):,} rows, 3 held-out runs)")
    plt.subplots_adjust(left=0.09, right=0.97, top=0.9, bottom=0.17)
    footnote(fig, "Empirical CDFs of all scored rows pooled over runs 24, 28 and 29 (serially dependent rows, three "
                  "independent workbooks). No smoothing.")
    save(plt, fig, out, f"FIG_B04_{SLUG[ch]}_error_ecdf",
         f"Absolute-error ECDFs for {NAME[ch]}. Persistence is exactly right on most rows because the signal is "
         "unchanged on the recording grid; Ridge is never exactly right but is marginally smaller in the far tail.",
         "How do central and tail errors compare?", ["replayed_predictions.csv.gz"], "fig_b04")


def fig_b05(plt, out, curves, tails, ch):
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    for m in ("persistence", "ridge"):
        c = curves[(curves.channel == ch) & (curves.model == m)]
        ax.plot(c.fraction, c.cumulative_share, **{**MODEL_STYLE[m], "lw": 1.8})
    t = tails[(tails.run == "all 3 runs") & (tails.channel == ch)]
    for f in (0.001, 0.01, 0.05):
        ax.axvline(f, color=C["grid"], lw=1)
        v = t[(t.tail_fraction == f)]
        p, r = v[v.model == "persistence"].tail_share.iloc[0], v[v.model == "ridge"].tail_share.iloc[0]
        ax.text(f * 1.08, 0.04, f"top {f:.1%}\nB0 {p:.1%} · B1 {r:.1%}", fontsize=9, color=C["navy"])
    ax.set_xscale("log"), ax.set_ylim(0, 1.02), ax.set_xlim(1 / 15885, 1)
    ax.set_xlabel("Fraction of rows, largest squared errors first (log scale)")
    ax.set_ylabel("Cumulative share of total squared error")
    ax.grid(axis="y"), ax.set_axisbelow(True), ax.legend(loc="upper left")
    ax.set_title(f"{NAME[ch]}: concentration of squared error (n = 15,885 rows, 3 runs)")
    plt.subplots_adjust(left=0.09, right=0.97, top=0.9, bottom=0.17)
    footnote(fig, "Each model ranked by its own squared errors; denominator = that model's total squared error over all "
                  "scored rows of the three held-out runs.")
    save(plt, fig, out, f"FIG_B05_{SLUG[ch]}_error_concentration",
         f"Cumulative squared-error share for {NAME[ch]}. The two curves nearly coincide: both models' RMSE is set by the "
         "same rare large steps.", "Are RMSE differences driven by rare large errors?",
         ["concentration_curves.csv", "tail_shares.csv"], "fig_b05")


def fig_b06(plt, out, change, ch):
    c = change[(change.run == "all 3 runs") & (change.channel == ch) & (change.n > 0)].reset_index(drop=True)
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 5.4), gridspec_kw=dict(width_ratios=[1.2, 1]))
    x = np.arange(len(c))
    a = axes[0]
    for m, dx in (("persistence", -0.08), ("ridge", 0.08)):
        v = c[f"{m}_mae"].values
        a.scatter(x + dx, np.where(v > 0, v, np.nan), s=70, color=MODEL_STYLE[m]["color"],
                  marker="s" if m == "persistence" else "o", label=MODEL_STYLE[m]["label"], zorder=3)
        for xi, vi in zip(x + dx, v):
            if vi == 0:
                a.scatter([xi], [1.2e-3], s=70, facecolor="white", edgecolor=C["slate"], marker="s", zorder=3)
                a.annotate("persistence\nexactly 0", (xi, 1.2e-3), xytext=(10, 6), textcoords="offset points",
                           fontsize=8.5, color=C["slate"])
    a.set_yscale("log"), a.set_ylim(8e-4, max(c.persistence_mae.max(), c.ridge_mae.max()) * 2)
    a.set_xticks(x, [f"{b.replace(' increments', chr(10) + 'increments').replace(' increment', chr(10) + 'increment')}"
                     f"\nn = {n:,}" for b, n in zip(c.bin, c.n)], fontsize=8.6)
    a.set_ylabel(f"MAE ({UNIT[ch]})"), a.grid(axis="y"), a.set_axisbelow(True), a.legend(loc="upper left", fontsize=9)
    a.set_title("(a) MAE by observed change", fontsize=11.5)
    b = axes[1]
    v = c.delta_sse.values
    b.barh(x, v, color=[C["red"] if t > 0 else C["teal"] for t in v], height=.55)
    for xi, vi in zip(x, v):
        b.text(vi + (0.4 if vi >= 0 else -0.4), xi, f"{vi:+.3g}", va="center", ha="left" if vi >= 0 else "right",
               fontsize=9)
    b.axvline(0, color=C["navy"], lw=1)
    b.set_yticks(x, c.bin, fontsize=8.6), b.invert_yaxis()
    lim = np.abs(v).max() * 1.45
    b.set_xlim(-lim, lim)
    b.set_xlabel(f"Ridge − Persistence squared error ({UNIT[ch]}²)")
    b.set_title("(b) Where Ridge gains (−) and loses (+)", fontsize=11.5)
    fig.suptitle(f"{NAME[ch]}: error versus observed one-step change (retrospective)", x=0.012, ha="left",
                 fontsize=12.5, weight="semibold")
    plt.subplots_adjust(left=0.08, right=0.97, top=0.86, bottom=0.24, wspace=0.42)
    footnote(fig, "Bins are fixed decades of the observed recording increment (0.2 barg; 0.01 ln/min), declared before any "
                  "error was computed. |Δy| uses the outcome itself, so this characterises errors after the fact and is not "
                  "a deployable gating rule.")
    save(plt, fig, out, f"FIG_B06_{SLUG[ch]}_error_vs_change",
         f"Error of each model by the size of the observed one-step change of {NAME[ch]}, pooled over the three held-out "
         "runs, and the Ridge − Persistence squared-error difference per bin.",
         "Under which observed change magnitudes do the models differ?", ["error_vs_change.csv"], "fig_b06")


def fig_b07(plt, out, res, runs):
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 5.4), sharey=True)
    labels = ["Recording increment (observed)", "Persistence MAE", "Ridge MAE", "Median |Ridge correction|",
              "Run-mean |ΔMAE| (Ridge − B0)", "Run-mean |ΔRMSE| (Ridge − B0)"]
    for ax, ch in zip(axes, ("P-2", "MFC-3")):
        r = res[res.channel == ch].iloc[0]
        rr = runs[runs.channel == ch]
        inc = r.observed_increment
        vals = [inc, r.persistence_mae_increments * inc, r.ridge_mae_increments * inc,
                r.ridge_abs_correction_median, abs(rr.delta_mae.mean()), abs(rr.delta_rmse.mean())]
        cols = [C["navy"], C["slate"], C["teal"], C["blue"], C["red"], C["red"]]
        for i, (v, col) in enumerate(zip(vals, cols)):
            ax.plot([1e-4, v], [i, i], color=C["grid"], lw=1, zorder=1)
            ax.scatter(v, i, s=80, color=col, zorder=3)
            ax.text(v * 1.35, i, f"{v:.3g} ({v / inc:.2g} incr.)", va="center", fontsize=9, color=col)
        ax.axvline(inc, color=C["navy"], lw=1, ls=":")
        ax.set_xscale("log"), ax.set_xlim(1e-4, 20)
        ax.set_xlabel(f"{UNIT[ch]} (log scale)")
        ax.set_title(f"({'a' if ch == 'P-2' else 'b'}) {NAME[ch]}", fontsize=11.5)
        ax.grid(axis="x"), ax.set_axisbelow(True)
    axes[0].set_yticks(range(len(labels)), labels), axes[0].invert_yaxis()
    fig.suptitle("Recorded increments versus prediction-error scales", x=0.012, ha="left", fontsize=12.5,
                 weight="semibold")
    plt.subplots_adjust(left=0.24, right=0.98, top=0.86, bottom=0.2, wspace=0.08)
    footnote(fig, "The increment is the smallest step between distinct recorded values (observed quantization), not a "
                  "manufacturer resolution or certified accuracy; no instrument specification is provided in the workbooks.")
    save(plt, fig, out, "FIG_B07_resolution_vs_error",
         "Recorded numerical increment against the error scales of both models. For P-2 the run-mean MAE difference is "
         "0.073 of one recorded increment; for MFC-3 it is about one increment.",
         "How do recorded increments compare with the errors?", ["resolution.csv", "run_metrics.csv"], "fig_b07")


def fig_b08(plt, out, d, windows, dates, control):
    run = 29
    start, end = windows[str(run)]
    fig, axes = plt.subplots(2, 1, figsize=(9.6, 5.4), sharex=True, gridspec_kw=dict(height_ratios=[1.4, 1]))
    p, t0 = window_rows(d[d.channel == "P-2"], run, start, end, dates[str(run)][0])
    f, _ = window_rows(d[d.channel == "MFC-3"], run, start, end, dates[str(run)][0])
    tp, tf = (p.target_time_s - t0) / 60, (f.target_time_s - t0) / 60
    flowing = f.y_true.values > 0
    for ax in axes:
        ymin, ymax = 0, 1
        edges = np.flatnonzero(np.diff(np.r_[0, flowing.astype(int), 0]))
        for s, e in zip(edges[::2], edges[1::2]):
            ax.axvspan(tf.values[s], tf.values[min(e, len(tf) - 1)], color=C["teal"], alpha=0.12, lw=0)
    axes[0].plot(tp, p.y_true, color=C["navy"], lw=1.4)
    axes[0].axhline(180, color=C["red"], lw=1, ls=":")
    axes[0].text(tp.values[0] + 0.3, 168, "nominal final outlet pressure 180 bar (overview sheet)", ha="left",
                 va="top", fontsize=9, color=C["red"])
    axes[0].set_ylabel("P-2 (barg)"), axes[0].grid(axis="y")
    axes[1].plot(tf, f.y_true, color=C["teal"], lw=1.2)
    axes[1].set_ylabel("MFC-3 (ln/min)"), axes[1].grid(axis="y")
    axes[1].set_xlabel(f"Minutes from representative-cycle start (run {run}, {start[:5]}–{end[:5]})")
    c = control.set_index("run")
    txt = "; ".join(f"run {r}: flowing {c.loc[r, 'mfc3_flowing_fraction']:.0%}, P-2 max while zero "
                    f"{c.loc[r, 'p2_when_zero_max']:g}" for r in c.index)
    axes[0].set_title("While MFC-3 reads zero, P-2 never exceeds the outlet set pressure: MFC-3 is the release path",
                      fontsize=12)
    plt.subplots_adjust(left=0.09, right=0.98, top=0.9, bottom=0.2, hspace=0.12)
    footnote(fig, "Shaded = MFC-3 > 0. All held-out runs (" + txt + " barg). The controller setpoint and valve command "
                  "are not recorded, so the control law cannot be modelled; only the measured flow is available.")
    save(plt, fig, out, "FIG_B08_MFC3_control_role",
         "Representative cycle of run 29: P-2 and MFC-3. While MFC-3 reads zero, P-2 stays at or below the nominal "
         "outlet pressure (+1 barg at most in every held-out run); the large releases coincide with P-2 at the set "
         "pressure and hold it there. Small MFC-3 flows also occur at lower P-2 after the switch-over, so MFC-3 is a "
         "controlled outlet flow, not a passive process measurement.", "Why does MFC-3's control role matter?",
         ["replayed_predictions.csv.gz", "controller_role.csv"], "fig_b08")


def fig_b09(plt, out):
    rows = ["Causal one-step prediction", "Run-level benchmark", "Reference prediction error",
            "Operating-condition variation", "Measurement resolution", "Competing event hypotheses",
            "Fault classification", "Formal D(Y)", "Localization", "Independent equipment transfer"]
    cols = ["Implemented", "Numerically\nverified", "Descriptively\nsupported", "Validated\nwithin scope",
            "Not established /\nblocked"]
    status = {0: [0, 1, 3], 1: [0, 1, 3], 2: [0, 1, 2], 3: [2], 4: [1, 2], 5: [4], 6: [4], 7: [4], 8: [4], 9: [4]}
    notes = {0: "bit-identical replay", 1: "3 runs, 2 dates", 2: "tail-driven RMSE gain", 3: "confounded settings",
             4: "observed grid only", 5: "operator notes only", 6: "no labels", 7: "no qualified bounds",
             8: "no location truth", 9: "one apparatus"}
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    for i in range(len(rows)):
        for j in range(len(cols)):
            on = j in status[i]
            fc = (C["red"] if j == 4 else C["navy"] if j == 3 else C["teal"]) if on else C["bg"]
            ax.add_patch(plt.Rectangle((j - .45, i - .38), .9, .76, fc=fc, ec=C["grid"], lw=1))
        ax.text(len(cols) - .35, i, notes[i], va="center", fontsize=9.5, color=C["slate"])
    ax.set_xlim(-.6, len(cols) + 1.5), ax.set_ylim(len(rows) - .5, -.6)
    ax.set_xticks(range(len(cols)), cols, fontsize=9.5), ax.xaxis.tick_top()
    ax.set_yticks(range(len(rows)), rows)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.tick_params(length=0)
    plt.subplots_adjust(left=0.27, right=0.98, top=0.86, bottom=0.08)
    footnote(fig, "'Validated within scope' = the frozen held-out comparison on three MHC workbooks; no diagnostic "
                  "capability is validated.")
    save(plt, fig, out, "FIG_B09_evidence_matrix", "Evidence status of H₂-PRISM capabilities supported by Study B.",
         "Which H₂-PRISM capabilities does MHC support?", ["TAB_B08"], "fig_b09")


# --------------------------------------------------------------------------- driver

def build(replay: Path, analysis: Path, out: Path):
    plt = style()
    tables, figures = out / "tables", out / "figures"
    tables.mkdir(parents=True, exist_ok=True), figures.mkdir(parents=True, exist_ok=True)
    meta = json.loads((replay / "replay_manifest.json").read_text(encoding="utf-8"))
    amani = json.loads((analysis / "analysis_manifest.json").read_text(encoding="utf-8"))
    gate = pd.read_csv(replay / "gate_frozen_replay.csv")
    d = pd.read_csv(replay / "replayed_predictions.csv.gz")
    d["e_persistence"], d["e_ridge"] = d.y_true - d.persistence, d.y_true - d.ridge
    runs = pd.read_csv(analysis / "run_metrics.csv")
    quant = pd.read_csv(analysis / "error_quantiles.csv")
    tails = pd.read_csv(analysis / "tail_shares.csv")
    paired = pd.read_csv(analysis / "tail_paired_attribution.csv")
    curves = pd.read_csv(analysis / "concentration_curves.csv")
    change = pd.read_csv(analysis / "error_vs_change.csv")
    res = pd.read_csv(analysis / "resolution.csv")
    control = pd.read_csv(analysis / "controller_role.csv")
    windows = {str(k): v for k, v in amani["representative_windows"].items()}
    dates = meta["dates"]

    md = [export(table_b01(meta), tables, "TAB_B01", "Experimental eligibility",
                 "All 29 workbooks. Eligibility, partition and units are the frozen Study B values; valid pairs are "
                 "recounted by the replay. Metadata conflicts quote the workbook protocol notes; none is corrected."),
          export(table_b02(gate), tables, "TAB_B02", "Frozen replay verification",
                 "Tolerance declared before comparison: persistence exact; Ridge |Δ| ≤ 1e-12 or relative ≤ 1e-9. "
                 "All 24 values are bit-identical."),
          export(table_b03(runs), tables, "TAB_B03", "Run-level prediction comparison",
                 "Units are never combined. ΔSSE share = run's share of the channel's total Ridge − Persistence squared-error "
                 "difference (negative total)."),
          export(quant.rename(columns={"p50": "median"}), tables, "TAB_B04", "Absolute-error quantiles",
                 "Quantiles use the inverted-CDF rule (an observed value). Rows are serially dependent; 'all 3 runs' "
                 "pools 15,885 rows from three workbooks."),
          export(tails, tables, "TAB_B05", "Squared-error tail attribution",
                 "Tail = the ceil(fraction × n) largest squared errors of that model; share = tail SSE / model total SSE."),
          export(paired, tables, "TAB_B05b", "Ridge − Persistence squared-error difference inside the persistence tail",
                 "Rows ranked by |persistence error|; pooled over the three held-out runs."),
          export(change[["run", "channel", "unit", "bin", "abs_change_min", "abs_change_max", "n", "runs_supporting",
                         "persistence_mae", "ridge_mae", "persistence_rmse", "ridge_rmse", "delta_mae", "rel_delta_mae",
                         "delta_sse"]], tables, "TAB_B06", "Error versus observed one-step change",
                 "Retrospective: |Δy| is outcome-derived. Bins are decades of the observed increment fixed before scoring."),
          export(res.assign(instrument_resolution="not documented in source", manufacturer_accuracy="not documented in source"),
                 tables, "TAB_B07", "Measurement resolution",
                 "Observed increment = smallest step between distinct recorded values; it is displayed/recorded quantization, "
                 "not certified accuracy."),
          ]
    b08 = pd.DataFrame([
        ("Causal one-step prediction", "decision-time inputs only", "frozen benchmark + bit-identical replay",
         "15,885 rows/channel, 3 runs", "VALIDATED WITHIN SCOPE", "Causal reference prediction on MHC dual-stage runs",
         "Generality beyond this apparatus"),
        ("Reference error behaviour", "observation-level residuals", "replayed predictions",
         "Ridge RMSE gain from rare large steps; MAE loss on unchanged rows", "DESCRIPTIVELY SUPPORTED",
         "Metric-dependent ranking explained", "Practical superiority of Ridge"),
        ("Measurement resolution", "instrument specs", "recorded values only",
         "P-2 0.2 barg grid; MFC-3 0.01 ln/min grid", "NUMERICALLY VERIFIED (observed grid)",
         "ΔMAE is 0.07 (P-2) and ~1 (MFC-3) recorded increment", "Certified accuracy statements"),
        ("Controller role of MFC-3", "control signals", "workbook notes + coupled P-2/MFC-3 data",
         "P-2 ≤ outlet set pressure + 1 barg whenever MFC-3 = 0 (3/3 runs)", "DESCRIPTIVELY SUPPORTED",
         "MFC-3 is a controlled outlet (release) flow", "Modelling the control law (setpoint not recorded)"),
        ("Operating-condition dependence", "controlled factorial design", "3 runs, confounded settings",
         "Run 29 carries 82 % of P-2 ΔSSE", "DESCRIPTIVELY SUPPORTED", "Run-level variation exists",
         "Attribution to material, pressure or cycle time"),
        ("Competing event hypotheses", "qualified event mechanisms", "operator notes (valve timing, safety valve, "
         "back-pressure error)", "notes only", "NOT ESTABLISHED", "Notes recorded as metadata", "Event labels"),
        ("Fault classification / localization", "independent labels, locations", "none", "—", "BLOCKED BY EVIDENCE",
         "None", "Any accuracy or localization metric"),
        ("Formal D(Y)", "qualified observation and model bounds", "none", "—", "BLOCKED BY EVIDENCE", "None",
         "Exclusion or certified diagnosis"),
        ("Independent equipment transfer", "other apparatus", "one apparatus", "—", "NOT ESTABLISHED", "None",
         "Industrial generalization"),
    ], columns=["capability", "data_requirement", "available_evidence", "numerical_finding", "qualification_status",
                "claim_allowed", "claim_prohibited"])
    md.append(export(b08, tables, "TAB_B08", "H₂-PRISM evidence qualification", "Evidence vocabulary as in the project."))
    (out / "tables_bundle.md").write_text("\n\n".join(md), encoding="utf-8", newline="\n")

    fig_b01(plt, figures)
    for ch in ("P-2", "MFC-3"):
        fig_b02(plt, figures, d, windows, dates, ch)
        fig_b03(plt, figures, runs, ch)
        fig_b04(plt, figures, d, ch)
        fig_b05(plt, figures, curves, tails, ch)
        fig_b06(plt, figures, change, ch)
    fig_b07(plt, figures, res, runs)
    fig_b08(plt, figures, d, windows, dates, control)
    fig_b09(plt, figures)

    for p in sorted(out.rglob("*")):
        if p.is_file() and p.suffix in (".csv", ".md", ".svg", ".json"):
            b = p.read_bytes()
            if b"\r\n" in b:
                p.write_bytes(b.replace(b"\r\n", b"\n"))
    rows = [dict(path=p.relative_to(out).as_posix(), sha256=hashlib.sha256(p.read_bytes()).hexdigest())
            for p in sorted(out.rglob("*")) if p.is_file() and p.name != "SHA256SUMS.csv"]
    pd.DataFrame(rows).to_csv(out / "SHA256SUMS.csv", index=False, lineterminator="\n")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--replay", type=Path, required=True)
    p.add_argument("--analysis", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    build(a.replay, a.analysis, a.output)
    print("report complete")


if __name__ == "__main__":
    main()
