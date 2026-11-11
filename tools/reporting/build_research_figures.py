#!/usr/bin/env python3
"""
H2-PRISM research figure builder (A5/A13). Repository-native: visual identity from
``h2prism.visualization.theme`` (via ``_style``); routing and provenance from the A13 ``_common`` helpers.

Consumes saved, machine-readable tables ONLY (runner outputs, dataset-design tables). It never refits models,
selects thresholds, resamples families or computes experimental statistics: plotted values are input values.
Display-only transformations are declared in each figure's ``metric_definition`` (row shares of a confusion
matrix, flag rates n_flagged / n_windows, sums of recorded counts across rows).

Figure kinds
  multi-panel scientific figures (selected in 05_documentation/FIGURE_SPECIFICATION.md):
    dataset_design      runs/families per class and topology, windows, window timing, LOTO design
    risk_coverage_panels pooled + per-held-out-topology risk-coverage with registered targets and attainability
    incremental_value   RQ1 paired effects, per-topology primary contrast, tie-order sensitivity
    three_outcome       RQ2 outcome shares, SPECIFIC correctness / ambiguity inclusion, reasons, support flags
    error_structure     confusion matrix, per-class scores with independent support, calibration reliability
    robustness          primary contrast across registered analyses (populations annotated)
  single-panel (backward compatible): risk_coverage, reliability

Routing (cannot be overridden by the figure config):
  evidence_status VALIDATED/FROZEN (model outputs) or VERIFIED (structural dataset tables) -> <out>/final/
  any other evidence_status                                     -> <out>/preliminary/ + watermark
  synthetic / preflight / fixture inputs                        -> <out>/illustrative/ + watermark,
                                                                   and REFUSED when <out> is inside 03_results/
A panel whose recorded rows are all NOT_ESTIMABLE (or whose selection is empty in an existing run table when
``empty_means_not_estimable``) shows an explicit non-estimability note, never an invented value.
Exports PNG (dpi from config), PDF and SVG; FIGURE_MANIFEST.csv (copy: FIGURE_BUILD_MANIFEST.csv) records
full provenance. Numerical reproducibility is exact; export bytes are deterministic for a fixed environment.

Usage:
  python tools/reporting/build_research_figures.py --config configs/reporting_dataset_figures.yaml --out-dir 03_results/research_figures/dataset_design
  python tools/reporting/build_research_figures.py --config configs/reporting_figures.yaml --out-dir 03_results/research_figures/primary
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _style as st  # noqa: E402
from _common import ReportingInputError, classify, load_input, load_config, sha256_path  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
NE = "NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL"
EXPERIMENT_CLASSES = ("PRIMARY_EXPERIMENT", "ROBUSTNESS_EXPERIMENT", "SENSITIVITY_EXPERIMENT")


# ----------------------------------------------------------------------------- helpers
def _est(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["status"] == "ESTIMABLE"] if "status" in df.columns else df


def _ne_count(df: pd.DataFrame) -> int:
    return int((df["status"] != "ESTIMABLE").sum()) if "status" in df.columns else 0


def _note(ax, text: str) -> None:
    """Explicit non-estimability / no-data note inside a panel (nothing is plotted)."""
    ax.text(0.5, 0.5, text, transform=ax.transAxes, ha="center", va="center", fontsize=8, color=st.MUTED,
            bbox=dict(boxstyle="round,pad=0.5", facecolor=st.LIGHT, edgecolor="#D1D5DB"))
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)


def _legend(ax, **kw) -> None:
    if ax.get_legend_handles_labels()[0]:
        ax.legend(**kw)


def _display_target(targets_estimable, registered) -> Tuple[object, str]:
    """Label-free display rule: the primary target if estimable, else the highest estimable registered target."""
    est = [t for t in registered if t in set(targets_estimable)]
    if not est:
        return None, "no registered target is estimable"
    t = registered[0] if registered[0] in est else max(est)
    return t, ("primary target" if t == registered[0] else f"primary target {registered[0]:.2f} not estimable; showing {t:.2f}")


REGISTERED_TARGETS = (0.8, 0.6, 0.9)


# ----------------------------------------------------------------------------- single-panel (legacy) kinds
def plot_risk_coverage(d: Dict[str, pd.DataFrame], spec):
    df = d["main"]
    e = _est(df)
    e = e[np.isfinite(e["coverage"].astype(float)) & np.isfinite(e["selective_risk"].astype(float))]
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    for m in sorted(e["method"].unique(), key=lambda x: st.METHOD_ORDER.index(x) if x in st.METHOD_ORDER else 99):
        s = st.method_style(m)
        g = e[e["method"] == m].sort_values("coverage")
        ax.plot(g["coverage"], g["selective_risk"], color=s["color"], ls=s["linestyle"], marker=s["marker"], label=s["label"])
    ax.set_xlabel("Coverage (fraction of eligible windows issued SPECIFIC)")
    ax.set_ylabel("Selective risk (error rate among SPECIFIC)")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, max(0.05, float(e["selective_risk"].max()) * 1.15) if len(e) else 1)
    _legend(ax, loc="upper left")
    ax.set_title(spec.get("title", ""))
    return fig, len(e), _ne_count(df)


def plot_reliability(d: Dict[str, pd.DataFrame], spec):
    df = d["main"].dropna(subset=["mean_confidence", "accuracy"])
    fig, ax = plt.subplots(figsize=(3.6, 3.6))
    ax.plot([0, 1], [0, 1], ls="--", lw=1, color=st.MUTED, label="Perfect calibration")
    ax.plot(df["mean_confidence"], df["accuracy"], marker="o", color=st.COLORS["primary"], label="Observed")
    ax.set_xlabel("Mean top-label confidence")
    ax.set_ylabel("Empirical accuracy")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    _legend(ax, loc="upper left")
    ax.set_title(spec.get("title", ""))
    return fig, len(df), 0


# ----------------------------------------------------------------------------- multi-panel scientific figures
def plot_dataset_design(d, spec):
    cls, tim, fol = d["classes"], d["timing"], d["folds"]
    fig, axs = plt.subplots(2, 2, figsize=(7.2, 5.6), gridspec_kw={"hspace": 0.55, "wspace": 0.35})
    a, b, c, e = axs.ravel()
    topo = cls[cls.topology != "ALL"]
    tops = sorted(topo.topology.unique())
    classes = [x for x in st.CLASS_ORDER if x in set(topo["class"])]
    w = 0.8 / max(len(tops), 1)
    for j, t in enumerate(tops):
        g = topo[topo.topology == t].set_index("class").reindex(classes)
        bars = a.bar(np.arange(len(classes)) + (j - (len(tops) - 1) / 2) * w, g["n_runs"], w,
                     color=[st.class_style(k)["color"] for k in classes], edgecolor="white",
                     hatch=st.TOPOLOGY_HATCHES[j % 3], label=t)
        a.bar_label(bars, labels=[f"{int(r)}/{int(f)}" for r, f in zip(g["n_runs"], g["n_families"])], fontsize=5.5, padding=1,
                    rotation=90)
    a.set_xticks(np.arange(len(classes)), [st.CLASS_SHORT[k] for k in classes])
    a.set_ylabel("Eligible runs")
    a.set_ylim(0, float(topo.n_runs.max()) * 1.45)
    a.legend(title="Topology (hatch)", fontsize=6.5, title_fontsize=6.5, loc="upper right",
             handles=[plt.Rectangle((0, 0), 1, 1, facecolor="white", edgecolor=st.INK, hatch=h) for h in st.TOPOLOGY_HATCHES[:len(tops)]],
             labels=tops)
    a.set_title("Runs per class and topology (runs/families)")
    tot = cls[cls.topology == "ALL"].set_index("class").reindex(classes)
    share = tot.n_windows / tot.n_windows.sum()
    bars = b.bar(np.arange(len(classes)), tot.n_windows, 0.6, color=[st.class_style(k)["color"] for k in classes],
                 hatch=[st.class_style(k)["hatch"] for k in classes], edgecolor="white", log=True)
    b.bar_label(bars, labels=[f"{int(n)}\n({s:.1%})" for n, s in zip(tot.n_windows, share)], fontsize=6, padding=1)
    b.set_yscale("log")
    b.set_ylim(1, float(tot.n_windows.max()) * 12)
    b.set_xticks(np.arange(len(classes)), [st.CLASS_SHORT[k] for k in classes])
    b.set_ylabel("Eligible 60 s windows (log)")
    b.set_title("Windows per class (not independent)")
    t2 = tim.set_index("class").reindex([k for k in classes if k in set(tim["class"])]).reset_index()
    for i, r in t2.iterrows():
        sty = st.class_style(r["class"])
        c.plot([r["min_s"], r["max_s"]], [i, i], color=sty["color"], lw=1)
        c.add_patch(plt.Rectangle((r["q25_s"], i - 0.22), r["q75_s"] - r["q25_s"], 0.44, facecolor=sty["color"], alpha=0.35,
                                  hatch=sty["hatch"], edgecolor=sty["color"]))
        c.plot([r["median_s"]], [i], marker="|", markersize=12, color=sty["color"])
    c.set_yticks(range(len(t2)), [st.CLASS_SHORT[k] for k in t2["class"]])
    c.set_xlabel("Window start within run (s)")
    c.set_xlim(0, None)
    c.set_title("Window timing (range, IQR, median)")
    folds = sorted(fol.outer_fold_id.unique())
    ftops = sorted(fol.topology.unique())
    for i, f in enumerate(folds):
        for j, t in enumerate(ftops):
            r = fol[(fol.outer_fold_id == f) & (fol.topology == t)].iloc[0]
            test = r["split_role"] == "test"
            e.add_patch(plt.Rectangle((j, -i - 1), 0.95, 0.85, facecolor=st.COLORS["secondary"] if test else st.LIGHT,
                                      edgecolor=st.INK, lw=1.2 if test else 0.4))
            e.text(j + 0.475, -i - 0.575, f"{'TEST' if test else 'train'}\n{int(r['n_runs'])} runs\n{int(r['n_families'])} families",
                   ha="center", va="center", fontsize=6, color="white" if test else st.INK)
    e.set_xlim(0, len(ftops))
    e.set_ylim(-len(folds) - 0.05, 0.05)
    e.set_xticks([j + 0.475 for j in range(len(ftops))], ftops, fontsize=7)
    e.set_yticks([-i - 0.575 for i in range(len(folds))], [f"Fold {f}" for f in folds])
    e.tick_params(length=0)
    e.grid(False)
    for sp in e.spines.values():
        sp.set_visible(False)
    e.set_title("Leave-one-topology-out design")
    for ax, l in zip((a, b, c, e), "abcd"):
        st.panel_label(ax, l)
    fig.suptitle(spec.get("title", ""), fontsize=11, fontweight="bold", y=1.0)
    return fig, len(cls) + len(tim) + len(fol), 0


def _rc_panel(ax, curve, targets, scope, methods, n_folds=None, tgt_list=None):
    e = _est(curve[curve.scope == scope])
    e = e[e.method.isin(methods)]
    if not len(e):
        _note(ax, f"{scope}: no attainable coverage\nunder the primary safeguards")
        return 0
    for m in [x for x in st.METHOD_ORDER if x in methods]:
        g = e[e.method == m].sort_values("coverage")
        if not len(g):
            continue
        s = st.method_style(m)
        ax.plot(g["coverage"], g["selective_risk"], color=s["color"], ls=s["linestyle"], marker=s["marker"], ms=3.2, lw=1.4,
                label=s["label"])
    attain = float(e.coverage.max())
    ax.axvspan(attain, 1.0, color=st.LIGHT, zorder=0, lw=0)
    ymax = max(0.05, float(e.selective_risk.max()) * 1.25)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, ymax)
    est_targets = set()
    if targets is not None and scope == "pooled":
        tp = targets[targets.method.isin(methods)]
        if "folds_estimable" in tp.columns and len(tp):  # pooled operating point only if estimable in EVERY held-out fold
            tp = tp[tp.folds_estimable == (n_folds or tp.folds_estimable.max())]
        est_targets = set(round(float(t), 2) for t in tp.target)
        for m in tp.method.unique():
            s = st.method_style(m)
            g = tp[tp.method == m]
            ax.plot(g["coverage"], g["selective_risk"], ls="none", marker=s["marker"], ms=7, mfc="white", mec=s["color"], mew=1.4)
    for t in (tgt_list or REGISTERED_TARGETS):  # the targets recorded by the run (passed in), else the registered ones
        ax.axvline(t, color=st.MUTED, lw=0.7, ls=(0, (2, 2)), zorder=1)
        if scope == "pooled":  # every registered target is labelled; unattainable ones say so instead of disappearing
            ax.text(t + 0.006, 0.985, f"target {t:.2f}" + ("" if round(t, 2) in est_targets else "\nnot estimable"),
                    transform=ax.get_xaxis_transform(),
                    ha="left", va="top", fontsize=6, color=st.INK if round(t, 2) in est_targets else st.MUTED)
    nt = curve[(curve.scope == scope) & curve.n_total.notna()].n_total if "n_total" in curve.columns else []
    if len(nt):
        ax.text(0.98, 0.02, f"n = {int(nt.max()):,} eligible windows", transform=ax.transAxes, fontsize=6.5, va="bottom", ha="right", color=st.MUTED)
    return len(e)


def plot_risk_coverage_panels(d, spec):
    curve, targets = d["curve"], d.get("targets")
    methods = spec.get("methods", ["s_C", "s_C_minus_D", "confidence"])
    tops = sorted(s for s in curve.scope.unique() if s != "pooled")
    fig = plt.figure(figsize=(7.4, 5.4))
    gs = fig.add_gridspec(2, max(len(tops), 1), height_ratios=[1.35, 1], hspace=0.75, wspace=0.3)
    a = fig.add_subplot(gs[0, :])
    n_folds = len(tops) or None
    tgt_list = sorted(set(round(float(x), 2) for x in targets.target)) if targets is not None and len(targets) else None
    n = _rc_panel(a, curve, targets, "pooled", methods, n_folds, tgt_list)
    a.set_xlabel("Coverage (fraction of eligible windows issued SPECIFIC)")
    a.set_ylabel("Selective risk")
    a.set_title("Pooled over held-out topologies")
    h, l = a.get_legend_handles_labels()
    h += [plt.Line2D([], [], ls="none", marker="o", mfc="white", mec=st.INK, ms=6),
          plt.Rectangle((0, 0), 1, 1, facecolor=st.LIGHT, edgecolor="none")]
    l += ["registered target, realized coverage", "not attainable (safeguards)"]
    a.legend(h, l, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=3, fontsize=6.5, frameon=False)
    st.panel_label(a, "a")
    axs = []
    for j, t in enumerate(tops):
        ax = fig.add_subplot(gs[1, j], sharey=axs[0] if axs else None)
        n += _rc_panel(ax, curve, None, t, methods, tgt_list=tgt_list)
        ax.set_title(f"Held-out {t}", fontsize=9)
        ax.set_xlabel("Coverage")
        if j == 0:
            ax.set_ylabel("Selective risk")
        st.panel_label(ax, "bcdefg"[j])
        axs.append(ax)
    if axs:  # shared y-axis: one limit that shows EVERY panel's values (the last panel must not crop the others)
        e = _est(curve[curve.scope.isin(tops)])
        e = e[e.method.isin(methods)]
        if len(e):
            axs[0].set_ylim(0, max(0.05, float(e.selective_risk.max()) * 1.25))
    fig.suptitle(spec.get("title", ""), fontsize=11, fontweight="bold", y=1.0)
    return fig, n, _ne_count(curve)


def plot_incremental_value(d, spec):
    rq1, topo, tie = d["rq1"], d.get("by_topology"), d.get("tie")
    fig = plt.figure(figsize=(7.4, 5.6))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.35, 1], hspace=0.5, wspace=0.45)
    a = fig.add_subplot(gs[:, 0])
    rows = rq1.sort_values(["comparison_b", "target"], key=lambda s: s.map(lambda x: st.METHOD_ORDER.index(x) if x in st.METHOD_ORDER else x)
                           if s.name == "comparison_b" else s, kind="mergesort").reset_index(drop=True)
    n_plot = 0
    for i, r in rows.iterrows():
        s = st.method_style(r["comparison_b"])
        if r["status"] == "ESTIMABLE":
            a.errorbar(r["difference"], i, xerr=[[r["difference"] - r["ci_low"]], [r["ci_high"] - r["difference"]]],
                       fmt=s["marker"], color=s["color"], ms=4.5, capsize=2.5, lw=1.2,
                       mfc=s["color"] if r["comparison_b"] == "s_C_minus_D" else "white")
            n_plot += 1
        else:
            a.text(0.5, i, "not estimable", fontsize=6, color=st.MUTED, va="center", ha="center", transform=a.get_yaxis_transform())
    a.axvline(0, color=st.MUTED, lw=0.9, ls="--")
    for k, (comp, g) in enumerate(rows.groupby("comparison_b", sort=False)):  # alternate bands group each comparator
        if k % 2 == 0:
            a.axhspan(g.index.min() - 0.5, g.index.max() + 0.5, color=st.LIGHT, zorder=0, lw=0)
    a.set_yticks(range(len(rows)), [f"vs {st.method_style(b)['label'].split(' — ')[0]} @ {t:.2f}" for b, t in zip(rows.comparison_b, rows.target)],
                 fontsize=6.5)
    for lab, b_ in zip(a.get_yticklabels(), rows.comparison_b):
        if b_ == "s_C_minus_D":
            lab.set_fontweight("bold")
    a.set_ylim(len(rows) - 0.5, -0.5)
    a.legend([plt.Line2D([], [], ls="none", marker="s", color=st.method_style("s_C_minus_D")["color"]),
              plt.Line2D([], [], ls="none", marker="o", mfc="white", color=st.INK)],
             ["primary contrast (vs no-D ablation)", "secondary comparators"], loc="upper center", bbox_to_anchor=(0.5, -0.16),
             ncol=1, fontsize=6.5, frameon=False)
    a.set_xlabel("Δ selective risk (s_C − comparator); bars: 95% family bootstrap")
    a.set_title("Paired effects at matched coverage")
    st.panel_label(a, "a")
    b = fig.add_subplot(gs[0, 1])
    if topo is not None and len(topo) and np.isfinite(topo["difference"].astype(float)).any():
        tt = topo[np.isfinite(topo["difference"].astype(float))]
        for k, (t, g) in enumerate(tt.groupby("topology")):
            b.plot(g["target"] + (k - 1) * 0.008, g["difference"], ls="none", marker=st.TOPOLOGY_MARKERS[k % 4], color=st.INK,
                   mfc=("white", st.INK, st.MUTED, "white")[k % 4], label=f"held-out {t}")
        b.axhline(0, color=st.MUTED, lw=0.9, ls="--")
        b.set_xlabel("Requested coverage")
        b.set_ylabel("Δ risk (s_C − s_C−D)")
        _legend(b, fontsize=6.5)
    else:
        _note(b, "per-topology primary contrast:\nnot estimable")
    b.set_title("Primary contrast by topology", fontsize=9)
    st.panel_label(b, "b")
    c = fig.add_subplot(gs[1, 1])
    if tie is not None and len(tie) and "difference" in tie.columns:
        for k, (t, g) in enumerate(sorted(tie.groupby("target"))):
            c.plot(np.full(len(g), t), g["difference"], ls="none", marker="o", ms=3, color=st.COLORS["secondary"], alpha=0.6,
                   label="alternative tie salts" if k == 0 else None)
            c.plot([t], [g["primary_difference"].iloc[0]], ls="none", marker="D", color=st.COLORS["primary"],
                   label="registered salt" if k == 0 else None)
        c.axhline(0, color=st.MUTED, lw=0.9, ls="--")
        c.set_xlabel("Requested coverage")
        c.set_ylabel("Δ risk (s_C − s_C−D)")
        _legend(c, fontsize=6.5)
    else:
        _note(c, "tie-order sensitivity:\nnot estimable")
    c.set_title("Tie-order sensitivity (PA-1)", fontsize=9)
    st.panel_label(c, "c")
    fig.suptitle(spec.get("title", ""), fontsize=11, fontweight="bold", y=1.0)
    return fig, n_plot, _ne_count(rq1)


def plot_three_outcome(d, spec):
    rq2, reasons, flags = d["rq2"], d.get("reasons"), d.get("flags")
    t, why = _display_target(rq2.target.unique(), REGISTERED_TARGETS)
    fig, axs = plt.subplots(2, 2, figsize=(7.4, 5.8), gridspec_kw={"hspace": 0.6, "wspace": 0.45})
    a, b, c, e = axs.ravel()
    g = rq2[rq2.target == t].set_index("class").reindex([k for k in st.CLASS_ORDER if k in set(rq2["class"])]).dropna(subset=["n"])
    left = np.zeros(len(g))
    for col, (colr, hatch, lab) in st.OUTCOMES.items():
        a.barh(np.arange(len(g)), g[col], left=left, color=colr, hatch=hatch, edgecolor="white", label=lab)
        left += g[col].to_numpy(float)
    a.set_yticks(np.arange(len(g)), [f"{st.CLASS_SHORT[k]}\n{int(n)} w · {int(f)} fam" for k, n, f in zip(g.index, g["n"], g["n_families"])],
                 fontsize=6.5)
    a.set_xlim(0, 1)
    a.set_xlabel("Share of eligible windows")
    a.legend(fontsize=6, loc="lower center", bbox_to_anchor=(0.5, 1.12), ncol=3, frameon=False)
    a.set_title(f"Decision outcomes @ coverage {t:.2f}", fontsize=9, pad=18)
    st.panel_label(a, "a")
    y = np.arange(len(g))
    b.plot(g["specific_correct"], y + 0.1, ls="none", marker="o", color=st.COLORS["primary"], label="SPECIFIC correct")
    b.plot(g["ambiguity_inclusion"], y - 0.1, ls="none", marker="s", mfc="white", color=st.COLORS["accent_warm"],
           label="true class in AMBIGUITY_SET")
    b.set_yticks(y, [st.CLASS_SHORT[k] for k in g.index], fontsize=7)
    b.set_xlim(-0.02, 1.02)
    b.set_xlabel("Share (undefined if no such decision)")
    b.legend(fontsize=6, loc="upper center", bbox_to_anchor=(0.5, -0.32), ncol=2, frameon=False)
    b.set_title("Correctness vs inclusion", fontsize=9)
    st.panel_label(b, "b")
    if reasons is not None and len(reasons):
        r = reasons[reasons.target == t]
        r = r[r.policy_outcome != "SPECIFIC"]
        p = r.groupby(["class", "reason"])["n"].sum().unstack("reason").fillna(0)
        p = p.reindex([k for k in st.CLASS_ORDER if k in p.index])
        share = p.div(p.sum(axis=1).replace(0, np.nan), axis=0).fillna(0)
        left = np.zeros(len(share))
        # reasons use colours NOT used for the three outcomes in panel (a) (primary / accent_warm / gray_medium)
        pal = [st.COLORS[k] for k in ("secondary", "purple", "gray_dark", "secondary", "purple", "gray_dark")]
        for i, col in enumerate(share.columns):
            c.barh(np.arange(len(share)), share[col], left=left, color=pal[i % len(pal)], hatch=("", "//", "..", "xx", "\\\\", "++")[i % 6],
                   edgecolor="white", label=col)
            left += share[col].to_numpy(float)
        c.set_yticks(np.arange(len(share)), [st.CLASS_SHORT[k] for k in share.index], fontsize=7)
        c.set_xlim(0, 1)
        c.set_xlabel("Share of non-SPECIFIC decisions")
        c.legend(fontsize=5.5, loc="upper center", bbox_to_anchor=(0.5, -0.3), ncol=2, frameon=False)
    else:
        _note(c, "no recorded reasons")
    c.set_title("Why not SPECIFIC (first reason)", fontsize=9)
    st.panel_label(c, "c")
    if flags is not None and len(flags):
        fg = flags.groupby(["flag", "class"])[["n_flagged", "n_windows"]].sum()
        rate = (fg.n_flagged / fg.n_windows.replace(0, np.nan)).unstack("class").fillna(0)
        rate = rate.loc[(rate > 0).any(axis=1)] if (rate > 0).any().any() else rate
        cl = [k for k in st.CLASS_ORDER if k in rate.columns]
        w = 0.8 / max(len(cl), 1)
        for i, k in enumerate(cl):
            sty = st.class_style(k)
            e.barh(np.arange(len(rate)) + (i - (len(cl) - 1) / 2) * w, rate[k], w, color=sty["color"], hatch=sty["hatch"],
                   edgecolor="white", label=sty["label"])
        import textwrap
        e.set_yticks(np.arange(len(rate)), [textwrap.fill(f.replace("_", " ").lower(), 16) for f in rate.index], fontsize=6)
        e.set_xlim(0, 1)
        e.set_xlabel("Share of held-out windows flagged")
        _legend(e, fontsize=5.5, loc="lower right")
    else:
        _note(e, "no support-flag summary")
    e.set_title("D(x) support flags", fontsize=9)
    st.panel_label(e, "d")
    fig.suptitle(spec.get("title", ""), fontsize=11, fontweight="bold", y=1.045)
    fig.text(0.5, 1.0, f"Displayed coverage target {t:.2f} ({why}; label-free display rule)", ha="center", va="bottom", fontsize=7.5, color=st.MUTED)
    return fig, len(g), 0


def plot_error_structure(d, spec):
    cm, cmet, rel = d["confusion"], d["class_metrics"], d.get("reliability")
    fig = plt.figure(figsize=(7.4, 5.4))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.15, 1], hspace=0.55, wspace=0.62)
    a = fig.add_subplot(gs[:, 0])
    classes = [k for k in st.CLASS_ORDER if k in set(cm.true_class)]
    m = cm.pivot_table(index="true_class", columns="predicted_class", values="n", aggfunc="sum").reindex(index=classes, columns=classes).fillna(0)
    share = m.div(m.sum(axis=1).replace(0, np.nan), axis=0)
    im = a.imshow(share.to_numpy(float), cmap="Blues", vmin=0, vmax=1, aspect="auto")
    for i in range(len(classes)):
        for j in range(len(classes)):
            v = share.iat[i, j]
            a.text(j, i, f"{v:.0%}\n(n={int(m.iat[i, j])})" if np.isfinite(v) else "–", ha="center", va="center", fontsize=6.5,
                   fontweight="bold", color="white" if np.isfinite(v) and v > 0.5 else st.INK)
    a.set_xticks(range(len(classes)), [st.CLASS_SHORT[k] for k in classes], rotation=30, ha="right")
    a.set_yticks(range(len(classes)), [st.CLASS_SHORT[k] for k in classes])
    a.set_xlabel("Predicted (calibrated top label)")
    a.set_ylabel("True class")
    a.grid(False)
    fig.colorbar(im, ax=a, fraction=0.05, pad=0.03, label="Row share of windows", shrink=0.8)
    a.set_title("Classifier confusion (pooled)")
    st.panel_label(a, "a")
    b = fig.add_subplot(gs[0, 1])
    g = cmet.set_index("class").reindex(classes)
    for i, (met, mk) in enumerate((("precision", "o"), ("recall", "s"), ("f1", "^"))):
        b.plot(g[met].astype(float), np.arange(len(g)) + (i - 1) * 0.18, ls="none", marker=mk, ms=4.5,
               color=(st.COLORS["primary"], st.COLORS["secondary"], st.COLORS["accent_warm"])[i], label=met.upper() if met == "f1" else met)
    b.set_yticks(np.arange(len(g)), [f"{st.CLASS_SHORT[k]}\n{int(r)} runs · {int(f)} fam" for k, r, f in zip(g.index, g.n_runs, g.n_families)],
                 fontsize=6)
    b.set_xlim(-0.02, 1.02)
    b.set_xlabel("Window-level score")
    b.legend(fontsize=6, loc="upper center", bbox_to_anchor=(0.5, -0.3), ncol=3, frameon=False)
    b.set_title("Per-class scores (independent support)", fontsize=9)
    st.panel_label(b, "b")
    c = fig.add_subplot(gs[1, 1])
    if rel is not None and len(rel):
        c.plot([0, 1], [0, 1], ls="--", lw=0.9, color=st.MUTED)
        for kind, mk, colr in (("raw", "s", st.MUTED), ("cal", "o", st.COLORS["primary"])):
            r = rel[rel.probability == kind].dropna(subset=["mean_confidence", "accuracy"])
            c.plot(r["mean_confidence"], r["accuracy"], marker=mk, ms=3.5, color=colr, mfc="white" if kind == "raw" else colr,
                   label="uncalibrated" if kind == "raw" else "calibrated")
        c.set_xlim(0, 1)
        c.set_ylim(0, 1.02)
        c.set_xlabel("Mean top-label confidence")
        c.set_ylabel("Accuracy")
        _legend(c, fontsize=6, loc="upper left")
    else:
        _note(c, "no reliability bins")
    c.set_title("Reliability (10 bins)", fontsize=9)
    st.panel_label(c, "c")
    fig.suptitle(spec.get("title", ""), fontsize=11, fontweight="bold", y=1.0)
    return fig, len(cm) + len(cmet), 0


def plot_robustness(d, spec):
    s = d["summary"]
    targets = [t for t in (0.8, 0.6) if t in set(s.target.dropna())] or sorted(s.target.dropna().unique())[:2]
    fig, axs = plt.subplots(1, max(len(targets), 1), figsize=(7.4, 3.9), sharey=True, gridspec_kw={"wspace": 0.12})
    axs = np.atleast_1d(axs)
    order = ["primary"] + [a for a in dict.fromkeys(s.analysis) if a != "primary"]
    n_plot = 0
    for ax, t, l in zip(axs, targets, "ab"):
        for i, an in enumerate(order):
            r = s[(s.analysis == an) & ((s.target == t) | s.target.isna())]
            r = r.iloc[0] if len(r) else None
            if r is not None and r.get("status") == "ESTIMABLE":
                same = str(r.get("population_note", "same windows")).startswith("same")
                ax.errorbar(r["difference"], i, xerr=[[r["difference"] - r["ci_low"]], [r["ci_high"] - r["difference"]]],
                            fmt="D" if an == "primary" else "o", ms=5 if an == "primary" else 4, capsize=2.5,
                            color=st.COLORS["primary"] if an == "primary" else st.COLORS["secondary"],
                            mfc=(st.COLORS["primary"] if an == "primary" else st.COLORS["secondary"]) if same else "white")
                n_plot += 1
            else:
                lab = ("not run" if r is None or r.get("status") == "NOT_RUN" else
                       "run incomplete" if r.get("status") == "RUN_INCOMPLETE" else "not estimable")
                ax.text(0.5, i, lab, transform=ax.get_yaxis_transform(), fontsize=6, color=st.MUTED, ha="center", va="center")
        ax.axvline(0, color=st.MUTED, lw=0.9, ls="--")
        ax.set_title(f"Target coverage {t:.2f}", fontsize=9)
        ax.set_xlabel("Δ selective risk (s_C − s_C−D)")
        st.panel_label(ax, l)
    axs[0].set_yticks(range(len(order)), order, fontsize=7)
    axs[0].invert_yaxis()
    pop = dict(zip(s.analysis, s.population_note)) if "population_note" in s.columns else {}
    for i, an in enumerate(order):  # which population each row evaluates (prevents invalid direct comparison)
        note = str(pop.get(an, ""))
        short = "different population" if note.startswith("different") else ("different units" if "units" in note else "same windows")
        axs[-1].text(1.02, i, short, transform=axs[-1].get_yaxis_transform(), fontsize=6, va="center",
                     color=st.INK if short == "same windows" else st.COLORS["accent_warm"])
    fig.suptitle(spec.get("title", ""), fontsize=11, fontweight="bold", y=1.02)
    fig.text(0.0, -0.02, "Open markers: analysis evaluates a different window population or independence units; compare direction, "
                         "not magnitude.", fontsize=6, color=st.MUTED, transform=fig.transFigure, va="top")
    return fig, n_plot, int((s.status != "ESTIMABLE").sum())


KINDS = {  # kind -> (function, {input key: required columns})
    "risk_coverage": (plot_risk_coverage, {"main": ["method", "coverage", "selective_risk"]}),
    "reliability": (plot_reliability, {"main": ["mean_confidence", "accuracy", "n"]}),
    "dataset_design": (plot_dataset_design, {"classes": ["class", "topology", "n_runs", "n_families", "n_windows"],
                                             "timing": ["class", "n_windows", "min_s", "q25_s", "median_s", "q75_s", "max_s"],
                                             "folds": ["outer_fold_id", "topology", "split_role", "n_runs", "n_families"]}),
    "risk_coverage_panels": (plot_risk_coverage_panels, {"curve": ["scope", "method", "status", "coverage", "selective_risk"],
                                                         "targets": ["method", "target", "coverage", "selective_risk"]}),
    "incremental_value": (plot_incremental_value, {"rq1": ["comparison_b", "target", "status", "difference", "ci_low", "ci_high"],
                                                   "by_topology": ["topology", "target", "difference"],
                                                   "tie": ["target", "difference", "primary_difference"]}),
    "three_outcome": (plot_three_outcome, {"rq2": ["class", "target", "n", "n_families", "specific", "ambiguity_set", "unresolved",
                                                   "specific_correct", "ambiguity_inclusion"],
                                           "reasons": ["class", "target", "policy_outcome", "reason", "n"],
                                           "flags": ["flag", "class", "n_flagged", "n_windows"]}),
    "error_structure": (plot_error_structure, {"confusion": ["true_class", "predicted_class", "n"],
                                               "class_metrics": ["class", "precision", "recall", "f1", "n_runs", "n_families"],
                                               "reliability": ["probability", "mean_confidence", "accuracy", "n"]}),
    "robustness": (plot_robustness, {"summary": ["analysis", "target", "status", "difference", "ci_low", "ci_high"]}),
}


# ----------------------------------------------------------------------------- provenance
def _git_commit(root: Path) -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    except Exception:  # noqa: BLE001
        return "UNKNOWN"


def _run_provenance(input_path: Path) -> Dict[str, object]:
    for name in ("run_manifest.json", "provenance.json"):
        p = input_path.parent / name
        if p.exists():
            m = json.loads(p.read_text(encoding="utf-8"))
            return {"run_id": m.get("run_key", m.get("run_id", "UNKNOWN")), "artifact_class": m.get("artifact_class", "UNKNOWN"),
                    "protocol_config_sha256": m.get("config_sha256", "UNKNOWN"),
                    "effective_config_sha256": m.get("effective_config_sha256", m.get("config_sha256", "UNKNOWN")),
                    "manifest_sha256": (m.get("input_sha256") or {}).get("manifest", "UNKNOWN"),
                    "run_git_commit": m.get("git_commit", "UNKNOWN"), "run_status": m.get("status", "UNKNOWN"),
                    "run_authorized": bool(m.get("authorization"))}
    return {k: "UNKNOWN" for k in ("run_id", "artifact_class", "protocol_config_sha256", "effective_config_sha256", "manifest_sha256",
                                   "run_git_commit", "run_status")}


def _rel(p: Path, root: Path) -> str:
    try:
        return Path(p).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:  # outside the repository (tests, scratch): absolute path; official outputs are always relative
        return Path(p).resolve().as_posix()


def _is_official(out_dir: Path) -> bool:
    res = (REPO / "03_results").resolve()
    o = Path(out_dir).resolve()
    return str(o).startswith(str(res)) and "ILLUSTRATIVE_DEMO_NOT_RESULTS" not in o.parts


def _inputs(spec: Dict) -> Dict[str, Dict]:
    if "inputs" in spec:
        return {k: (v if isinstance(v, dict) else {"input": v}) for k, v in spec["inputs"].items()}
    return {"main": {"input": spec["input"], "filter": spec.get("filter")}}


MANIFEST_FIELDS = ["figure_id", "title", "group", "kind", "status", "reason", "research_question", "output_file", "output_sha256",
                   "input_file", "input_sha256", "run_id", "artifact_class", "run_status", "protocol_config_sha256",
                   "effective_config_sha256", "manifest_sha256", "run_git_commit", "build_git_commit", "config_file", "config_sha256",
                   "script", "function", "command", "units", "metric_definition", "limitations", "non_estimable", "n_rows_input",
                   "n_rows_plotted", "n_rows_not_estimable", "source_experiment", "evidence_status", "caption", "environment",
                   "generated_at_utc"]


def build(config_path: Path, out_dir: Path, root: Path) -> pd.DataFrame:
    st.apply()
    cfg, cfg_hash = load_config(config_path)
    rows: List[Dict] = []
    errors: List[str] = []
    official = _is_official(out_dir)
    build_commit = _git_commit(root)
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    env = f"python {platform.python_version()}; matplotlib {matplotlib.__version__}; pandas {pd.__version__}; numpy {np.__version__}"
    cmd = f"python tools/reporting/build_research_figures.py --config {_rel(config_path, root)} --out-dir {_rel(out_dir, root)}"
    for spec in cfg.get("figures", []):
        kind = spec.get("kind")
        if kind not in KINDS:
            errors.append(f"[{spec.get('id')}] unsupported kind {kind}")
            continue
        fn, reqs = KINDS[kind]
        ins = _inputs(spec)
        primary_key = next(iter(reqs)) if next(iter(reqs)) in ins else next(iter(ins))  # defined by the kind, not YAML order
        ins = {primary_key: ins[primary_key], **{k: v for k, v in ins.items() if k != primary_key}}
        base = {"figure_id": spec.get("id"), "title": spec.get("title", ""), "group": spec.get("group", ""), "kind": kind,
                "research_question": spec.get("research_question", ""), "input_file": ";".join(v["input"] for v in ins.values()),
                "config_file": _rel(config_path, root), "config_sha256": cfg_hash, "script": "tools/reporting/build_research_figures.py",
                "function": fn.__name__, "command": cmd, "units": spec.get("units", ""), "metric_definition": spec.get("metric_definition", ""),
                "limitations": spec.get("limitations", ""), "source_experiment": spec.get("source_experiment", "UNSPECIFIED"),
                "evidence_status": spec.get("evidence_status", "UNDECLARED"), "caption": spec.get("caption", ""),
                "build_git_commit": build_commit, "environment": env, "generated_at_utc": stamp}
        dfs, missing, n_ne_sel = {}, [], 0
        for key, sub in ins.items():
            sp = {"id": f"{spec.get('id')}:{key}", "input": sub["input"], "filter": sub.get("filter"),
                  "required_columns": reqs.get(key, [])}
            try:
                dfs[key] = load_input(root, sp)
            except ReportingInputError as exc:
                secondary = key != primary_key
                if "no rows" in str(exc) and (root / sub["input"]).exists() and (spec.get("empty_means_not_estimable") or secondary):
                    n_ne_sel += 1  # an existing run table with nothing estimable for this selection: shown as such, never filled
                    if not secondary:
                        dfs[key] = pd.DataFrame([{"selection": json.dumps(sub.get("filter") or {}), "status": NE}])
                else:  # missing file, missing columns, bad filter column: always an error
                    missing.append(str(exc))
        if missing:
            errors.extend(missing)
            rows.append({**base, "status": "NOT_BUILT_MISSING_EVIDENCE", "reason": "; ".join(missing)})
            continue
        prov = _run_provenance(root / ins[primary_key]["input"])
        main = dfs[primary_key]
        if "artifact_class" not in main.columns and prov["artifact_class"] != "UNKNOWN":
            main = main.assign(artifact_class=prov["artifact_class"])
        dest, wm = classify(spec, main)
        if official and dest == "illustrative":
            msg = f"[{spec['id']}] synthetic/illustrative input refused for official output directory {_rel(out_dir, root)}"
            errors.append(msg)
            rows.append({**base, **prov, "status": "REFUSED_SYNTHETIC_IN_OFFICIAL_RESULTS", "reason": msg})
            continue
        if official and prov.get("run_status") not in ("COMPLETED",):  # partial / unknown runs never reach official outputs
            msg = f"[{spec['id']}] source run status {prov.get('run_status')} refused for official output (COMPLETED required)"
            errors.append(msg)
            rows.append({**base, **prov, "status": "REFUSED_INCOMPLETE_RUN", "reason": msg})
            continue
        if official and prov.get("artifact_class") in EXPERIMENT_CLASSES and not prov.get("run_authorized"):
            msg = f"[{spec['id']}] experiment run without a recorded authorization refused for official output"
            errors.append(msg)
            rows.append({**base, **prov, "status": "REFUSED_UNAUTHORIZED_RUN", "reason": msg})
            continue
        all_ne = "status" in main.columns and len(main) > 0 and (main["status"] != "ESTIMABLE").all() and kind not in ("robustness",)
        if all_ne:
            fig, ax = plt.subplots(figsize=(6.4, 2.4))
            _note(ax, "NOT ESTIMABLE UNDER THE PRIMARY PROTOCOL\n(no value exists for this selection; nothing is plotted)")
            ax.set_title(spec.get("title", ""))
            n_plot, n_ne = 0, len(main)
        else:
            fig, n_plot, n_ne = fn(dfs, spec)
        if wm:
            fig.text(0.5, 0.5, wm, ha="center", va="center", rotation=25, fontsize=13, color=st.COLORS["accent_danger"], alpha=0.3,
                     transform=fig.transFigure)
        rid = str(prov["run_id"])
        rid = rid[:12] if len(rid) > 32 else rid
        fig.canvas.draw()  # place the source line below every drawn element
        bb = fig.get_tightbbox(fig.canvas.get_renderer())
        fig.text(bb.x0 / fig.get_figwidth(), bb.y0 / fig.get_figheight() - 0.012,
                 f"Source: {base['input_file']} | run {rid} | {spec.get('source_experiment', '')}",
                 fontsize=5, color=st.MUTED, transform=fig.transFigure, va="top")
        d = out_dir / dest
        d.mkdir(parents=True, exist_ok=True)
        stem = d / spec["id"]
        fig.savefig(stem.with_suffix(".png"), dpi=int(cfg.get("dpi", 300)), metadata=st.PNG_META)
        fig.savefig(stem.with_suffix(".pdf"), metadata=st.PDF_META)
        fig.savefig(stem.with_suffix(".svg"), metadata=st.SVG_META)
        plt.close(fig)
        in_hash = ";".join(sha256_path(root / v["input"]) for v in ins.values() if (root / v["input"]).exists())
        n_in = sum(len(x) for x in dfs.values())
        for ext in (".png", ".pdf", ".svg"):
            rows.append({**base, **prov, "status": f"BUILT_{dest.upper()}", "reason": wm,
                         "output_file": _rel(stem.with_suffix(ext), root), "output_sha256": sha256_path(stem.with_suffix(ext)),
                         "input_sha256": in_hash, "non_estimable": bool(all_ne), "n_rows_input": n_in,
                         "n_rows_plotted": int(n_plot), "n_rows_not_estimable": int(n_ne) + n_ne_sel})
    man = pd.DataFrame(rows).reindex(columns=MANIFEST_FIELDS)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in ("FIGURE_MANIFEST.csv", "FIGURE_BUILD_MANIFEST.csv"):
        man.to_csv(out_dir / name, index=False, lineterminator="\n")
    if errors and cfg.get("fail_on_missing", True):
        raise ReportingInputError("; ".join(errors))
    return man


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="H2-PRISM research figure builder (A13)")
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--root", type=Path, default=REPO)
    a = ap.parse_args(argv)
    try:
        build(a.config, a.out_dir, a.root)
    except ReportingInputError as exc:
        print(f"FAILED (mandatory evidence absent or invalid): {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
