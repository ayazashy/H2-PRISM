"""Tables (CSV + Markdown) and standalone figures (PNG + SVG + caption) for the
Study C evidence enhancement. Reads analysis outputs, the verified source CSV and
frozen Study C artifacts. No fitting, scoring or threshold selection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE.parent
C = dict(bg="#F4F4E9", navy="#10263E", teal="#007F86", blue="#356CB1", slate="#64748B", red="#A33F43",
         grid="#D9DFDE", text="#1F2933", gold="#C9A227")
MODEL = {"persistence": dict(color=C["slate"], ls="--", label="Persistence"),
         "ridge": dict(color=C["teal"], ls="-", label="Contextual Ridge")}
NAME = {"pres_buf": "Buffer pressure", "pres_comp": "Tank pressure", "h2_flow": "Electrolyzer H₂ flow"}
STATE = {"electrolyzer_active": "Electrolyzer only", "multiple_active": "Electrolyzer + compressor",
         "unknown": "Unknown power"}


def style():
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["IBM Plex Sans", "Segoe UI", "DejaVu Sans"],
        "font.size": 11, "figure.facecolor": C["bg"], "axes.facecolor": C["bg"], "savefig.facecolor": C["bg"],
        "axes.edgecolor": C["slate"], "axes.labelcolor": C["text"], "text.color": C["text"],
        "xtick.color": C["text"], "ytick.color": C["text"], "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": .8, "grid.color": C["grid"], "grid.linewidth": .6, "legend.frameon": False,
        "svg.fonttype": "none", "svg.hashsalt": "h2prism", "axes.titlesize": 12.5, "axes.titleweight": "semibold",
        "axes.titlelocation": "left", "axes.labelsize": 11.5})
    return plt


def footnote(fig, text):
    fig.text(0.012, 0.014, textwrap.fill(text, 160), ha="left", va="bottom", fontsize=8.6, color=C["slate"],
             linespacing=1.25)


def save(plt, fig, out, name, caption, question, sources, fn):
    fig.savefig(out / f"{name}.png", dpi=400)
    fig.savefig(out / f"{name}.svg", metadata={"Date": None})
    (out / f"{name}.caption.md").write_text(
        f"**{name}.** {caption}\n\nScientific question: {question}\n\nSource data: "
        + ", ".join(f"`{s}`" for s in sources) + f"\n\nReproduction function: `report.{fn}`\n",
        encoding="utf-8", newline="\n")
    plt.close(fig)


def md_table(df):
    def fmt(v):
        if isinstance(v, float):
            return "—" if np.isnan(v) else f"{v:.6g}"
        return str(v).replace("|", "/")
    cols = list(df.columns)
    return "\n".join(["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"] +
                     ["| " + " | ".join(fmt(v) for v in r) + " |" for r in df.itertuples(index=False)])


def export(df, out, name, title, note):
    df.to_csv(out / f"{name}.csv", index=False, lineterminator="\n")
    text = f"### {name} — {title}\n\n{note}\n\n{md_table(df)}\n"
    (out / f"{name}.md").write_text(text, encoding="utf-8", newline="\n")
    return text


# --------------------------------------------------------------------------- figures

def fig_h01(plt, out, raw):
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 5.4))
    for ax, f in zip(axes, ("pres_buf", "pres_comp")):
        vc = raw[f].dropna().round(1).value_counts().sort_index()
        ax.vlines(vc.index, 0, vc.values, color=C["navy"], lw=0.9)
        ax.set_yscale("log"), ax.set_ylim(0.8, vc.max() * 2)
        ax.set_xlabel(f"Recorded {NAME[f].lower()} (bar)"), ax.set_ylabel("Rows (log scale)")
        ax.set_title(f"({'a' if f == 'pres_buf' else 'b'}) {NAME[f]}: {len(vc)} distinct levels, "
                     f"{vc.index.min():.1f}–{vc.index.max():.1f} bar", fontsize=11)
        ax.grid(axis="y"), ax.set_axisbelow(True)
        inset = ax.inset_axes([0.56, 0.64, 0.4, 0.27])
        inset.set_facecolor(C["bg"])
        lo = vc.idxmax()
        w = vc[(vc.index >= lo - 0.55) & (vc.index <= lo + 0.55)]
        inset.vlines(w.index, 0, w.values, color=C["teal"], lw=2)
        inset.set_xticks(w.index[::2]), inset.set_xticklabels([f"{x:.1f}" for x in w.index[::2]], fontsize=7)
        inset.tick_params(axis="y", labelsize=7), inset.set_title("0.1 bar spacing (zoom)", fontsize=8, loc="left")
    fig.suptitle("HY2RES pressures are recorded on a 0.1 bar grid", x=0.012, ha="left", fontsize=12.5,
                 weight="semibold")
    plt.subplots_adjust(left=0.08, right=0.98, top=0.85, bottom=0.2, wspace=0.28)
    footnote(fig, "All 300,767 finite source rows per channel; 100 % lie exactly on multiples of 0.1 bar (rtol = 0). "
                  "This is the recording increment of the published CSV, not an instrument resolution or accuracy, "
                  "which the source does not document.")
    save(plt, fig, out, "FIG_H01_pressure_quantization",
         "Counts of every recorded buffer- and tank-pressure level in the full HY2RES source. Both channels take only "
         "multiples of 0.1 bar.", "What are the observable pressure increments?", ["HY2RES_202404.csv", "recording_grid.csv"],
         "fig_h01")


def fig_h02(plt, out, pred):
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 5.4), sharey=True)
    for ax, f in zip(axes, ("pres_buf", "pres_comp")):
        g = pred[pred.target == f].dropna(subset=["y_true", "persistence_prediction", "contextual_prediction"])
        for m, col in (("persistence", "persistence_prediction"), ("ridge", "contextual_prediction")):
            a = np.sort(np.abs(g.y_true - g[col]).to_numpy() / 0.1)
            ax.step(np.maximum(a, 1e-3), np.arange(1, len(a) + 1) / len(a), where="post", **{**MODEL[m], "lw": 1.8})
            z = (a == 0).mean()
            if z:
                ax.scatter([1e-3], [z], color=MODEL[m]["color"], s=45, zorder=4)
                ax.annotate(f"{z:.1%} exactly 0", (1e-3, z), xytext=(8, -14), textcoords="offset points", fontsize=9,
                            color=MODEL[m]["color"])
        for k in (1, 2):
            ax.axvline(k, color=C["navy"], lw=.9, ls=":")
            ax.text(k * 0.93, 0.03 + 0.07 * (k - 1), f"{k} incr.", fontsize=9, color=C["navy"], ha="right")
        ax.set_xscale("log"), ax.set_xlim(1e-3, 5), ax.set_ylim(0, 1.03)
        ax.set_xlabel("|error| / 0.1 bar recording increment (zeros drawn at 0.001)")
        ax.set_title(f"({'a' if f == 'pres_buf' else 'b'}) {NAME[f]} (n = {len(g):,}, 409 segments)", fontsize=11)
        ax.grid(), ax.set_axisbelow(True)
    axes[0].set_ylabel("Cumulative fraction of scored rows"), axes[0].legend(loc="center right", fontsize=9.5)
    fig.suptitle("Prediction errors in units of the recording increment (frozen test predictions)", x=0.012, ha="left",
                 fontsize=12.5, weight="semibold")
    plt.subplots_adjust(left=0.08, right=0.98, top=0.86, bottom=0.2, wspace=0.08)
    footnote(fig, "Archived frozen predictions on the shared 43,168-row mask; dimensionless ratios to the observed recording "
                  "increment, not uncertainty-normalised errors. The test period was already inspected; descriptive only.")
    save(plt, fig, out, "FIG_H02_error_in_increments",
         "ECDFs of absolute 5-s-ahead pressure errors divided by the 0.1 bar recording increment. Persistence errors are "
         "exactly 0 or 1 increment; Ridge errors are continuous, never 0, and mostly below one increment.",
         "How large are errors relative to the recording grid?", ["test_predictions.csv.gz"], "fig_h02")


def fig_h03(plt, out, q, steps):
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 5.4), gridspec_kw=dict(width_ratios=[1, 1.15]))
    a = axes[0]
    rows = [(f, m) for f in ("pres_buf", "pres_comp") for m in ("MAE", "RMSE")]
    for i, (f, m) in enumerate(rows):
        r = q[q.channel == f].iloc[0]
        p = r[f"persistence_{m.lower()}_incr"]
        g = r[f"ridge_{m.lower()}_incr"]
        a.plot([p, g], [i, i], color=C["grid"], lw=3, zorder=1)
        a.scatter(p, i, marker="s", s=80, color=C["slate"], zorder=3)
        a.scatter(g, i, marker="o", s=80, color=C["teal"], zorder=3)
        d = g - p
        a.text(max(p, g) + 0.02, i, f"{d:+.3f} incr. ({r[f'rel_delta_{m.lower()}']:+.1%})", va="center", fontsize=9,
               color=C["red"] if d > 0 else C["teal"])
    a.set_yticks(range(4), [f"{NAME[f]}\n{m}" for f, m in rows]), a.invert_yaxis()
    a.set_xlim(0, 0.8), a.set_xlabel("Error / 0.1 bar increment"), a.grid(axis="x"), a.set_axisbelow(True)
    a.set_title("(a) Frozen MAE and RMSE (axis from 0)", fontsize=11)
    b = axes[1]
    labels, y = [], 0
    for f in ("pres_buf", "pres_comp"):
        s = steps[(steps.channel == f) & (steps.n > 0)]
        for r in s.itertuples():
            b.barh(y, r.delta_sse, color=C["red"] if r.delta_sse > 0 else C["teal"], height=.6)
            b.text(max(r.delta_sse, 0) + 1.5, y, f"{r.delta_sse:+.2f} bar²  (n = {r.n:,})", va="center",
                   ha="left", fontsize=9)
            labels.append(f"{NAME[f]} · {r.step_class}")
            y += 1
    b.axvline(0, color=C["navy"], lw=1), b.set_yticks(range(len(labels)), labels, fontsize=9), b.invert_yaxis()
    lim = steps.delta_sse.abs().max()
    b.set_xlim(-lim * 1.1, lim * 1.25), b.set_xlabel("Ridge − Persistence squared error (bar²)")
    b.set_title("(b) Ridge − Persistence SSE by recorded step", fontsize=11)
    fig.suptitle("Ridge lowers RMSE by anticipating single 0.1 bar steps and pays on unchanged rows", x=0.012,
                 ha="left", fontsize=12.5, weight="semibold")
    plt.subplots_adjust(left=0.13, right=0.98, top=0.86, bottom=0.2, wspace=0.95)
    footnote(fig, "Recorded step = (y_t − y_{t−1}) / 0.1 bar on the shared 43,168-row mask (409 segments). Only one tank row "
                  "changes by 2 increments; none by more. Descriptive, on the previously inspected test period.")
    save(plt, fig, out, "FIG_H03_error_tradeoff",
         "(a) Frozen persistence and Ridge MAE/RMSE in recording increments. (b) Ridge − Persistence squared error split "
         "by the recorded target step: Ridge gains on the ±1-increment rows and loses on the unchanged majority.",
         "Why does Ridge improve RMSE while worsening or barely changing MAE?",
         ["quantization_comparison.csv", "step_contribution.csv"], "fig_h03")


def fig_h04(plt, out, raw, audit, bounds):
    t = pd.to_datetime(raw.datetime)
    v = raw.pres_comp.to_numpy(dtype=float).copy()
    brk = audit.segment_id.ne(audit.segment_id.shift()).to_numpy()
    tt = t.to_numpy()
    xs = np.insert(tt.astype("datetime64[ns]").astype(float), np.flatnonzero(brk)[1:], np.nan)
    ys = np.insert(v, np.flatnonzero(brk)[1:], np.nan)
    xs = pd.to_datetime(xs)
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    roles = audit.split_role
    shades = {"development": None, "validation": C["blue"], "test": C["gold"]}
    for role, col in shades.items():
        m = roles.eq(role)
        if col:
            ax.axvspan(t[m].min(), t[m].max(), color=col, alpha=.10, lw=0)
        ax.text(t[m].min() + (t[m].max() - t[m].min()) / 2, 112.2, role, ha="center", fontsize=9.5, color=C["navy"])
    import matplotlib.dates as mdates
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    ax.plot(xs, ys, color=C["navy"], lw=.35)
    hi = bounds.loc["pres_comp", "dev_max"]
    ax.axhline(hi, color=C["red"], lw=1.1, ls="--")
    ax.text(t.min(), hi + 0.4, f"development maximum {hi:.1f} bar (support boundary of the frozen rule)", fontsize=9,
            color=C["red"])
    test = roles.eq("test")
    over = (raw.pres_comp > hi) & test
    ax.fill_between(t[test], hi, raw.pres_comp.where(over)[test], color=C["red"], alpha=.25, lw=0)
    ax.set_ylabel("Tank pressure pres_comp (bar)"), ax.set_xlabel("Source timestamp (2024, source clock)")
    ax.set_ylim(83, 113.5), ax.grid(axis="y"), ax.set_axisbelow(True)
    ax.set_title("Tank pressure rises over the record; the test period exceeds the development maximum")
    plt.subplots_adjust(left=0.08, right=0.98, top=0.9, bottom=0.21)
    footnote(fig, f"All 300,767 finite rows; lines are broken at each of the 2,793 causal segment boundaries (no bridging "
                  f"of gaps). Red fill: test source rows above the development maximum ({over.sum():,} of {test.sum():,}; "
                  "31,589 at the rule's lagged forecast origin). The 1,438 embargo rows at partition boundaries are not "
                  "shaded. Temporal association only; no physical cause is inferred.")
    save(plt, fig, out, "FIG_H04_tank_pressure_drift",
         "Chronological tank pressure with frozen partitions and the development-derived support boundary of the "
         "empirical rule. Validation stays inside development support; the test period oscillates above it.",
         "How does tank pressure evolve through development, validation and test?",
         ["HY2RES_202404.csv", "split_manifest.csv", "development_bounds.csv"], "fig_h04")


def fig_h05(plt, out, sup, n_test, n_unres):
    s = sup[sup.condition.isin(["below", "above", "nonfinite"])].copy()
    s["label"] = s.channel.map(NAME) + " · " + s.condition.map({"below": "below development min",
                                                                "above": "above development max",
                                                                "nonfinite": "nonfinite at origin"})
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    y = np.arange(len(s))
    ax.barh(y, s.rows, color=[C["red"] if c == "above" else C["slate"] if c == "nonfinite" else C["blue"]
                              for c in s.condition], height=.6)
    for yi, r in zip(y, s.itertuples()):
        ax.text(r.rows + 300, yi, f"{r.rows:,}  ({r.fraction_of_test:.1%} of test; {r.segments} segments)", va="center",
                fontsize=9)
    ax.set_yticks(y, s.label, fontsize=9.5), ax.invert_yaxis()
    ax.set_xlim(0, n_test * 1.4), ax.set_xlabel(f"Test rows (denominator = all {n_test:,} test rows; counts are non-exclusive)")
    ax.grid(axis="x"), ax.set_axisbelow(True)
    fig.suptitle("Only tank pressure breaches development support; the three nonfinite counts are the same 413 rows",
                 x=0.012, ha="left", fontsize=12.5, weight="semibold")
    plt.subplots_adjust(left=0.36, right=0.98, top=0.9, bottom=0.17)
    footnote(fig, f"Support = development min–max of each origin measurement used by the frozen rule. No row breaches more "
                  f"than one channel. The 413 nonfinite rows are segment-start rows without a lagged origin value. "
                  f"Unresolved total = {n_unres:,}.")
    save(plt, fig, out, "FIG_H05_support_violations",
         "Rows of the test period that violate each channel's development support, by direction, with segment counts.",
         "Which measurements invalidate the empirical operating reference?", ["support_attribution.csv"], "fig_h05")


def fig_h06(plt, out, tax, n_test):
    u = tax[tax.decision == "Unresolved"].sort_values("rows", ascending=False)
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    y = np.arange(len(u))
    cols = {"OUT_OF_SUPPORT": C["red"], "INVALID_INPUT": C["slate"], "EMPTY_CELL": C["blue"]}
    ax.barh(y, u.rows, color=[cols[r.split(" ")[0]] for r in u.primary_reason], height=.55)
    for yi, r in zip(y, u.itertuples()):
        ax.text(r.rows + 300, yi, f"{r.rows:,}  ({r.pct_of_unresolved:.2%} of unresolved; {r.segments} segments)",
                va="center", fontsize=9.5)
    ax.set_yticks(y, [textwrap.fill(r, 34) for r in u.primary_reason], fontsize=9.5), ax.invert_yaxis()
    tot = int(u.rows.sum())
    ax.set_xlim(0, tot * 1.9), ax.grid(axis="x"), ax.set_axisbelow(True)
    ax.set_xlabel(f"Unresolved test rows (sum = {tot:,} = frozen unresolved total; {tot / n_test:.1%} of {n_test:,} test rows)")
    fig.suptitle("Why the empirical rule abstains: out-of-support tank pressure, not state ambiguity", x=0.012,
                 ha="left", fontsize=12.5, weight="semibold")
    plt.subplots_adjust(left=0.33, right=0.98, top=0.9, bottom=0.17)
    footnote(fig, "Exclusive attribution; precedence: nonfinite input, then tank, buffer, flow support breach, then empty "
                  "cell. The frozen decision labels are unchanged; reasons are an additive explanation. AMBIGUOUS (1,327 rows) "
                  "is a separate outcome and is not counted here.")
    save(plt, fig, out, "FIG_H06_unresolved_mechanisms",
         "Decomposition of the 32,308 frozen UNRESOLVED decisions into mutually exclusive reasons that reconcile exactly "
         "to the frozen total.", "Why is the empirical policy unresolved so often?", ["unresolved_taxonomy.csv"], "fig_h06")


def fig_h07(plt, out, bins, bounds):
    fig, axes = plt.subplots(2, 1, figsize=(9.6, 5.4), sharex=True, gridspec_kw=dict(height_ratios=[1.3, 1]))
    x = pd.to_datetime(bins.time) + pd.Timedelta(hours=3)
    a = axes[0]
    a.plot(x, bins.unresolved_fraction, color=C["navy"], marker="o", lw=1.4, label="Unresolved fraction")
    a.plot(x, bins.out_of_support_fraction, color=C["red"], marker="s", lw=1.2, ls="--",
           label="Out-of-support fraction")
    for xi, n in zip(x, bins.rows):
        a.text(xi, 1.06, f"{n:,}", ha="center", fontsize=7.5, color=C["slate"])
    a.set_ylim(0, 1.13), a.set_ylabel("Fraction of rows in bin"), a.grid(axis="y"), a.legend(loc="lower left", fontsize=9)
    b = axes[1]
    b.plot(x, bins.tank_median, color=C["teal"], marker="o", lw=1.2)
    b.axhline(bounds.loc["pres_comp", "dev_max"], color=C["red"], ls="--", lw=1)
    b.set_ylabel("Tank median (bar)"), b.grid(axis="y")
    import matplotlib.dates as mdates
    b.xaxis.set_major_locator(mdates.HourLocator(byhour=[0, 12]))
    b.xaxis.set_major_formatter(mdates.DateFormatter("%d %b %H:%M"))
    b.set_xlabel("Test period, 6-hour bins (bin width fixed before plotting; row counts above panel)")
    a.set_title("Unresolved decisions track tank pressure above the development maximum, bin by bin")
    plt.subplots_adjust(left=0.09, right=0.98, top=0.9, bottom=0.2, hspace=0.12)
    footnote(fig, "Frozen decisions on the 44,397 test rows. Bin medians oscillate with a daily pattern around the 106.6 bar "
                  "development maximum (dashed). Descriptive temporal association, not a causal test.")
    save(plt, fig, out, "FIG_H07_decision_validity_over_time",
         "Unresolved and out-of-support fractions in fixed 6-hour test bins, with the bin median tank pressure.",
         "Does out-of-support behaviour coincide with unresolved decisions over time?", ["time_bins.csv"], "fig_h07")


def fig_h08(plt, out, so):
    cols = ["specific_correct", "ambiguous", "unresolved_out_of_support", "unresolved_empty_cell", "unresolved_invalid"]
    names = ["SPECIFIC\n(correct state)", "AMBIGUOUS", "UNRESOLVED\nout of support", "UNRESOLVED\nempty cell",
             "UNRESOLVED\ninvalid input"]
    m = so.set_index("state")[cols]
    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    data = m.to_numpy(dtype=float)
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("t", ["#E7F1F1", C["teal"]])
    ax.imshow(np.where(data > 0, np.log10(np.maximum(data, 1)), np.nan), cmap=cmap, aspect="auto", vmin=0, vmax=5)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            v = int(data[i, j])
            ax.text(j, i, f"{v:,}", ha="center", va="center", fontsize=13 if v else 11,
                    color=C["navy"] if v else C["slate"], weight="semibold" if v else "normal")
    ax.set_xticks(range(len(names)), names, fontsize=9.5)
    ax.set_yticks(range(len(m)), [f"{STATE[s]}\nn = {int(so.set_index('state').loc[s, 'rows']):,} rows, "
                                  f"{int(so.set_index('state').loc[s, 'segments'])} segments" for s in m.index], fontsize=9.5)
    ax.set_xticks(np.arange(-.5, data.shape[1]), minor=True), ax.set_yticks(np.arange(-.5, data.shape[0]), minor=True)
    ax.grid(which="minor", color=C["grid"], lw=1.2), ax.tick_params(which="minor", length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    fig.suptitle("Decisions by power-defined operating state: no specific recognition of the compressor-powered state",
                 x=0.012, ha="left", fontsize=12.5, weight="semibold")
    plt.subplots_adjust(left=0.27, right=0.98, top=0.9, bottom=0.2)
    footnote(fig, "Counts of test rows (cell shade proportional to log count). Power-derived labels describe electrical draw, not equipment "
                  "faults. A majority rule ('electrolyzer only' for every labelled row) agrees with 43,167 of 43,984 labels "
                  "and recognises 0 of 817 compressor-powered rows; the empirical rule's 10,762 specific calls are all of the "
                  "majority state.")
    save(plt, fig, out, "FIG_H08_state_decision_matrix",
         "Frozen empirical-rule outcomes by power-defined operating state, with unresolved rows split by reason.",
         "Which operating states receive specific, ambiguous or unresolved decisions?", ["state_outcomes.csv"], "fig_h08")


def fig_h09(plt, out, att, dist):
    v = att[np.isfinite(att[["pres_buf", "pres_comp", "h2_flow"]]).all(axis=1) & att.label.isin(
        ["electrolyzer_active", "multiple_active"])]
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 5.4), gridspec_kw=dict(width_ratios=[0.8, 2]))
    a, b = axes
    for i, (s, col) in enumerate((("electrolyzer_active", C["blue"]), ("multiple_active", C["teal"]))):
        g = v[v.label == s]
        z = (g.h2_flow == 0).mean()
        a.bar(i, z, color=col, width=.55)
        a.text(i, z + .02, f"{z:.1%}\n({int((g.h2_flow == 0).sum()):,} of {len(g):,})", ha="center", fontsize=9)
    a.set_xticks([0, 1], ["Electrolyzer\nonly", "Electrolyzer +\ncompressor"], fontsize=9.5)
    a.set_ylim(0, 1.15), a.set_ylabel("Fraction of rows with zero flow"), a.grid(axis="y")
    a.set_title("(a) Zero-flow mass", fontsize=11)
    pos = v[v.h2_flow > 0]
    bins = np.arange(np.floor(pos.h2_flow.min() / 5) * 5, pos.h2_flow.max() + 5, 2.5)
    for s, col, ls in (("electrolyzer_active", C["blue"], "--"), ("multiple_active", C["teal"], "-")):
        g = pos[pos.label == s].h2_flow
        b.hist(g, bins=bins, density=True, histtype="step", lw=1.8, color=col, ls=ls,
               label=f"{STATE[s]} (n = {len(g):,}, {pos[pos.label == s].segment.nunique()} segments)")
    d = dist[dist.channel == "h2_flow"].set_index("flow_rule").rank_probability
    b.set_xlabel("Positive electrolyzer H₂ flow at forecast origin (NL/h)"), b.set_ylabel("Density")
    b.legend(loc="upper left", fontsize=9), b.grid(axis="y"), b.set_axisbelow(True)
    b.set_title(f"(b) Positive flow only: rank probability {d['positive flow only']:.3f} "
                f"(all rows {d['all rows']:.3f})", fontsize=11)
    fig.suptitle("Flow separates the states mainly through zero versus positive production", x=0.012, ha="left",
                 fontsize=12.5, weight="semibold")
    plt.subplots_adjust(left=0.08, right=0.98, top=0.86, bottom=0.2, wspace=0.28)
    footnote(fig, "Rank probability = P(compressor-state value > electrolyzer-only value) + ½ P(tie), on test rows with finite "
                  "origin measurements; descriptive, not a classification accuracy. Power labels are operating states, not faults.")
    save(plt, fig, out, "FIG_H09_positive_flow_distinguishability",
         "Zero-flow mass and positive-flow distributions of the two power-defined states. Separation collapses from 0.945 "
         "to 0.554 once zero-flow rows are removed.", "Does state separation persist on positive-flow rows?",
         ["test_decision_attribution.csv.gz", "distinguishability.csv"], "fig_h09")


def fig_h10(plt, out):
    rows = ["Causal signal processing", "Reference prediction", "Recording-resolution interpretation",
            "Support-validity diagnosis", "Empirical state distinction", "Formal D(Y)", "Fault diagnosis",
            "Leak localization", "Independent transfer"]
    cols = ["Implemented", "Numerically\nverified", "Descriptively\nsupported", "Validated\nwithin scope",
            "Not established /\nblocked"]
    status = {0: [0, 1, 3], 1: [0, 1, 3], 2: [1, 2], 3: [0, 1, 2], 4: [2], 5: [4], 6: [4], 7: [4], 8: [4]}
    notes = {0: "segments, masks, lags", 1: "frozen metrics reconciled", 2: "0.1 bar grid", 3: "97.8 % tank breach",
             4: "flow zero/positive only", 5: "no qualified bounds", 6: "no fault labels", 7: "no location truth",
             8: "one pilot"}
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
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    plt.subplots_adjust(left=0.28, right=0.98, top=0.86, bottom=0.08)
    footnote(fig, "'Validated within scope' = chronologically held-out comparison on one pilot record whose historical "
                  "test-access seal is unverified.")
    save(plt, fig, out, "FIG_H10_evidence_matrix", "Evidence status of H₂-PRISM capabilities supported by HY2RES.",
         "Which capabilities does the enhanced HY2RES evidence support?", ["TAB_H09"], "fig_h10")


# ---------------------------------------------------------------------------- driver

def build(analysis: Path, source: Path, out: Path):
    plt = style()
    tables, figures = out / "tables", out / "figures"
    tables.mkdir(parents=True, exist_ok=True), figures.mkdir(parents=True, exist_ok=True)
    rd = lambda n: pd.read_csv(analysis / f"{n}.csv")
    grid, q, steps, chron = rd("recording_grid"), rd("quantization_comparison"), rd("step_contribution"), rd("chronology")
    bounds = rd("development_bounds").set_index("channel")
    sup, combos, tax, so, dist, bins = (rd("support_attribution"), rd("support_combinations"), rd("unresolved_taxonomy"),
                                        rd("state_outcomes"), rd("distinguishability"), rd("time_bins"))
    gate_b, gate_c = rd("gate_benchmark_reconciliation"), rd("gate_decision_reproduction")
    att = pd.read_csv(analysis / "test_decision_attribution.csv.gz")
    raw = pd.read_csv(source, sep=";", usecols=["datetime", "pres_buf", "pres_comp", "h2_flow"])
    audit = pd.read_csv(ARCHIVE / "validity_mask.csv.gz", usecols=["segment_id", "split_role"])
    pred = pd.read_csv(ARCHIVE / "test_predictions.csv.gz")
    seg = json.loads((ARCHIVE / "time_audit.json").read_text(encoding="utf-8")) if (ARCHIVE / "time_audit.json").exists() else {}
    n_test = int(so.rows.sum())
    n_unres = int(tax[tax.decision == "Unresolved"].rows.sum())

    md = []
    h01 = grid.assign(source="Zenodo 15166733 v1, HY2RES_202404.csv (MD5 9a3c3e3b…)",
                      interval_definition="5 s source clock; causal segments break at OPEN/CLOSE and non-5-s steps",
                      causal_segments=2793,
                      qualification=["0.1 bar recording grid; instrument resolution/accuracy undocumented"] * 2 +
                                    ["not quantised at 0.1; normalised volumetric production over preceding interval"])
    md.append(export(h01, tables, "TAB_H01", "Dataset and recording integrity",
                     "Full source (300,768 rows). Recording increment = smallest step between distinct recorded values."))
    md.append(export(q, tables, "TAB_H02", "Quantisation and frozen prediction comparison",
                     "Archived frozen predictions on the shared 43,168-row mask (409 segments). Increment units are "
                     "descriptive ratios to the 0.1 bar recording increment."))
    md.append(export(steps, tables, "TAB_H03", "Error contribution by recorded target step",
                     "Step class = (y_t − y_{t−1}) / 0.1 bar. Ridge predictions are not rounded."))
    md.append(export(chron, tables, "TAB_H04", "Chronological distributions by frozen partition",
                     "Raw source values per partition (origin lags not applied). dev_rule_min/max are the frozen rule's "
                     "support limits (development origin rows with finite inputs and known power)."))
    md.append(export(sup, tables, "TAB_H05", "Development-support failure attribution (test rows)",
                     f"Denominator {n_test:,} test rows; unresolved {n_unres:,}. Non-exclusive per channel/condition; "
                     "primary_reason_rows is the exclusive count."))
    md.append(export(combos, tables, "TAB_H05b", "Exact violation combinations among unresolved rows",
                     "Each unresolved row appears once."))
    md.append(export(tax, tables, "TAB_H06", "Decision taxonomy (frozen decision + additive reason)",
                     "Frozen decision labels are unchanged; primary_reason is reconstructed with documented precedence."))
    md.append(export(so, tables, "TAB_H07", "Operating-state decision outcomes",
                     "Power-defined labels at the forecast origin; not fault labels. majority_baseline_agree = rows a "
                     "constant 'electrolyzer only' rule would match."))
    md.append(export(dist, tables, "TAB_H08", "Empirical distinguishability (rank probability)",
                     "P(compressor-state value > electrolyzer-only value) + ½ P(tie); descriptive."))
    claims = pd.DataFrame([
        ("Source identity", "MD5/size of restored source", "38,621,947 bytes, MD5 9a3c3e3b…", "Layer I",
         "VERIFIED WITHIN SCOPE", "Exact official file", "Calibration or synchronisation"),
        ("Pressure recording grid", "TAB_H01", "both pressures 100 % on 0.1 bar grid", "Layer I",
         "NUMERICALLY VERIFIED", "Errors must be read against 0.1 bar", "Instrument accuracy"),
        ("Ridge vs persistence", "TAB_H02/H03", "buffer ΔMAE +0.015 incr., ΔRMSE −0.028 incr.; tank −0.005/−0.099",
         "Layer II", "DESCRIPTIVELY SUPPORTED", "Ridge partly anticipates single 0.1 bar steps",
         "Practical superiority; new held-out claim"),
        ("Tank-pressure drift", "TAB_H04, FIG_H04", "dev max 106.6 bar; 71.8 % of test source rows above",
         "Layer II", "DESCRIPTIVELY SUPPORTED", "Test period outside development support", "Physical cause"),
        ("Unresolved mechanism", "TAB_H06", "31,589 / 32,308 unresolved = tank out of support",
         "Layer II", "NUMERICALLY VERIFIED (reconciled)", "Abstention reflects domain shift, not state ambiguity",
         "That abstention is diagnostically correct"),
        ("Minority state", "TAB_H07", "0 of 817 compressor rows specific", "Layer II", "DESCRIPTIVELY SUPPORTED",
         "Rule cannot recognise the minority state", "Compressor fault detection"),
        ("Positive-flow distinction", "TAB_H08", "flow rank probability 0.945 → 0.554", "Layer II",
         "DESCRIPTIVELY SUPPORTED", "Separation is zero vs positive production", "Classification accuracy"),
        ("Formal D(Y)", "source scope", "no qualified bounds, fault library, labels or locations", "Layer III",
         "NOT ESTABLISHED", "Formal D(Y) not established for HY2RES", "Any exclusion or certified diagnosis"),
        ("Fault / leak / localization / transfer", "source scope", "no truth", "Layer III", "BLOCKED BY EVIDENCE",
         "None", "Any accuracy, localization or generalisation claim"),
    ], columns=["claim", "evidence", "numerical_result", "layer", "qualification", "establishes", "does_not_establish"])
    md.append(export(claims, tables, "TAB_H09", "Claims and evidence qualification", "Project evidence vocabulary."))
    md.append(export(gate_b, tables, "TAB_H00a", "Gate B — archived metric reconciliation",
                     "Recomputed from archived predictions; tolerance 1e-12 relative."))
    md.append(export(gate_c, tables, "TAB_H00b", "Gate C — frozen decision reproduction",
                     "Replica of the frozen rule against published counts."))
    (out / "tables_bundle.md").write_text("\n\n".join(md), encoding="utf-8", newline="\n")

    fig_h01(plt, figures, raw)
    fig_h02(plt, figures, pred)
    fig_h03(plt, figures, q, steps)
    fig_h04(plt, figures, raw, audit, bounds)
    fig_h05(plt, figures, sup, n_test, n_unres)
    fig_h06(plt, figures, tax, n_test)
    fig_h07(plt, figures, bins, bounds)
    fig_h08(plt, figures, so)
    fig_h09(plt, figures, att, dist)
    fig_h10(plt, figures)

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
    p.add_argument("--analysis", type=Path, required=True)
    p.add_argument("--source", type=Path, default=os.environ.get("HY2RES_SOURCE_CSV"))
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.source is None:
        raise SystemExit("pass --source or set HY2RES_SOURCE_CSV")
    build(a.analysis, Path(a.source), a.output)
    print("report complete")


if __name__ == "__main__":
    main()
