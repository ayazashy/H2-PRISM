"""HY2RES (Study C, operational hydrogen system) Q1 figures. One function per figure.

Inputs: the frozen HY2RES publication package (test predictions, segment registry, channel schema, held-out table)
and the accepted Study C evidence-enhancement analysis tables. Population denominators are stated per figure.
"""
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch, Patch

from q1fig import finish
from q1style import C, REPO, figure, title, xgrid, ygrid

MOD = "fig_hy2res"
H = REPO / "03_results/hy2res_external_validation"
E = H / "evidence_enhancement/results/analysis"
LIM = ("One residential hydrogen system (HY2RES, April 2024); operating-state labels are power-defined, not fault "
       "labels; reference prediction and evidence validity only — no diagnosis, localisation or transfer claim.")
PARTS = ["development", "validation", "embargo", "test"]
PCOL = {"development": C["blue"], "validation": C["teal"], "embargo": C["slate"], "test": C["ochre"]}
MOD_STY = {"persistence": dict(color=C["navy"], ls="-", marker="o", label="Persistence"),
           "contextual": dict(color=C["ochre"], ls="--", marker="s", label="Contextual Ridge")}


def meta(fid, stem, fn, ttl, q, sources, cap, lim=LIM, ver="values read from the frozen HY2RES package"):
    return dict(id=fid, stem=f"{fid}_{stem}", function=fn, module=MOD, title=ttl, question=q, sources=sources,
                caption=cap, limitation=lim, study="HY2RES", verification=ver)


def load():
    d = {k: pd.read_csv(E / f"{k}.csv") for k in ("chronology", "development_bounds", "distinguishability",
                                                    "quantization_comparison", "recording_grid", "state_outcomes",
                                                    "step_contribution", "support_combinations", "support_attribution",
                                                    "time_bins", "unresolved_taxonomy")}
    d["pred"] = pd.read_csv(H / "test_predictions.csv.gz")
    d["seg"] = pd.read_csv(H / "segment_registry.csv")
    d["schema"] = pd.read_csv(H / "publication/CHANNEL_SCHEMA.csv")
    d["held"] = pd.read_csv(H / "publication/TABLE_2_HELD_OUT.csv")
    return d


def plot_hy2res_channel_architecture(d, out):
    s = d["schema"].set_index("column")
    groups = [("Hydrogen production and storage", ["h2_flow", "h2_total", "pres_buf", "pres_comp"], C["teal"]),
              ("Fuel cell", ["P_pila", "pres_pila", "h2_flow_pila"], C["blue"]),
              ("Electrical power and battery", ["P_elec", "P_comp", "P_pur", "P_pan", "P_viv", "P_car", "P_des", "P_exp",
                                                "P_imp", "SOC"], C["navy"]),
              ("Context and markers", ["Temperature", "datetime", "Breaks"], C["slate"]),
              ("Undefined in the record (excluded)", ["P_con", "P_perdidas", "h2_inc"], C["burgundy"])]
    targets = {"pres_buf": "target", "pres_comp": "target", "h2_flow": "target", "pres_pila": "constant target",
               "h2_flow_pila": "constant target"}
    fig = figure(h=6.0)
    title(fig, "HY2RES record: 23 published columns grouped by role")
    ax = fig.add_subplot()
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    xs = [0.1, 2.1, 4.1, 6.1, 8.1]
    for (name, cols, col), x in zip(groups, xs):
        ax.add_patch(FancyBboxPatch((x, 0.3), 1.8, 9.2, boxstyle="round,pad=0.02,rounding_size=0.05", fc=C["white"],
                                    ec=col, lw=1.4))
        ax.text(x + 0.9, 9.0, name.replace(" and ", "\nand ").replace(" (", "\n("), ha="center", va="center", fontsize=10.5,
                fontweight="bold", color=col)
        ytop = 7.9
        for c in cols:
            tag = targets.get(c, "")
            miss = int(s.loc[c, "missing_values"]) if c in s.index else 0
            label = c + (f" [{tag}]" if tag else "") + (f"\n{miss:,} missing" if miss else "")
            ax.text(x + 0.9, ytop, label, ha="center", va="top", fontsize=9.5,
                    color=C["text"], fontweight="bold" if tag else "normal")
            ytop -= 0.36 * (label.count("\n") + 1) + 0.2
    cap = ("Columns of the official HY2RES_202404.csv (Zenodo 15166733 v1; 300,768 rows at a 5 s PLC clock), grouped by "
           "published definition. Bold entries are the Study C prediction targets: buffer pressure pres_buf (bar), tank "
           "pressure pres_comp (bar; not identified as compressor-discharge pressure) and electrolyzer flow h2_flow (NL/h, "
           "over the preceding interval); the two fuel-cell targets are constant in the test period. Three columns have no "
           "published definition and are excluded. Missing counts from CHANNEL_SCHEMA.csv.")
    return finish(fig, meta("Q1_H01", "hy2res_channel_architecture", "plot_hy2res_channel_architecture",
                            "Measurement architecture", "Which measured quantities does the HY2RES record contain, and which are predicted?",
                            ["03_results/hy2res_external_validation/publication/CHANNEL_SCHEMA.csv"], cap,
                            lim="Grouping by published definitions; no plant topology is implied."), out)


def plot_hy2res_partition_timeline(d, out):
    ch = d["chronology"]
    ch = ch[ch.channel == "pres_buf"].set_index("partition")
    seg = d["seg"].copy()
    seg["start"] = pd.to_datetime(seg.start_timestamp)
    fig = figure()
    title(fig, "Chronological partition and causal segmentation of the record")
    ax = fig.add_subplot()
    day = lambda t: (pd.to_datetime(t) - pd.Timestamp("2024-03-27")) / pd.Timedelta(days=1)  # noqa: E731
    spans = {"development": [(ch.loc["development", "start"], ch.loc["development", "end"])],
             "validation": [(ch.loc["validation", "start"], ch.loc["validation", "end"])],
             "embargo": [(ch.loc["development", "end"], ch.loc["validation", "start"]),
                         (ch.loc["validation", "end"], ch.loc["test", "start"])],
             "test": [(ch.loc["test", "start"], ch.loc["test", "end"])]}
    for i, p in enumerate(PARTS):
        r = ch.loc[p]
        for a, b in spans[p]:
            ax.barh(i, max(day(b) - day(a), 0.08), left=day(a), color=PCOL[p], height=0.5, zorder=3,
                    hatch="//" if p == "embargo" else None, edgecolor=C["white"] if p != "embargo" else C["text"], lw=0.4)
        ax.text(day(spans[p][-1][1]) + 0.25, i, f"{int(r.rows):,} rows · {int(r.segments):,} segments", va="center",
                fontsize=10)
    days = (seg.start - pd.Timestamp("2024-03-27")) / pd.Timedelta(days=1)
    ax.scatter(days, np.full(len(days), 4.0), marker="|", s=40, color=C["text"], lw=0.5, zorder=3)
    ax.set_yticks(range(5), [p.capitalize() for p in PARTS] + ["Segment starts"])
    ax.invert_yaxis()
    ax.set_xlim(-0.3, 23)
    ax.set_xlabel("Days since 27 March 2024 00:00 (record clock; timezone unspecified)")
    xgrid(ax)
    cap = (f"Frozen chronological partition: development ({ch.loc['development', 'start']} – {ch.loc['development', 'end']}), "
           f"validation, a one-hour embargo on each side, and the held-out test period from {ch.loc['test', 'start']}. "
           f"Causal segments ({len(seg):,} in total) break at OPEN/CLOSE markers and at any step other than 5 s; models use "
           "only same-segment lag-1 inputs, with no interpolation. No development segment is shared with the test period.")
    return finish(fig, meta("Q1_H02", "hy2res_partition_timeline", "plot_hy2res_partition_timeline",
                            "Partition and causal segmentation", "How is the record partitioned and segmented to keep prediction causal?",
                            ["evidence_enhancement/results/analysis/chronology.csv", "03_results/hy2res_external_validation/segment_registry.csv"],
                            cap), out)


def _seg(d, tgt):
    p = d["pred"]
    g = p[(p.segment_id == 2382) & (p.target == tgt)].copy()
    g["t"] = (pd.to_datetime(g.timestamp) - pd.to_datetime(g.timestamp).min()).dt.total_seconds() / 60
    return g


def plot_hy2res_pressure_traces(d, out):
    fig = figure()
    title(fig, "Held-out pressures move on a 0.1 bar grid; both references track them")
    axs = fig.subplots(1, 2)
    for ax, tgt, lab in [(axs[0], "pres_buf", "Buffer pressure pres_buf (bar)"), (axs[1], "pres_comp", "Tank pressure pres_comp (bar)")]:
        g = _seg(d, tgt)
        ax.plot(g.t, g.y_true, color=C["text"], lw=1.8, drawstyle="steps-post", label="Observed")
        ax.plot(g.t, g.persistence_prediction, color=C["blue"], lw=0.9, ls=":", drawstyle="steps-post",
                label="Persistence (previous value)")
        ax.plot(g.t, g.contextual_prediction, color=MOD_STY["contextual"]["color"], lw=1.2, ls="--", label="Contextual Ridge")
        ax.set_ylabel(lab)
        ax.set_xlabel("Minutes from 12:36:44, 12 April 2024")
        ygrid(ax)
    fig.legend(*axs[0].get_legend_handles_labels(), loc="outside lower center", ncol=3)
    g = _seg(d, "pres_buf")
    cap = (f"Held-out test segment 2382 ({len(g)} five-second steps, 12:36:44–12:46:59 on 12 April 2024; the interval "
           "chosen by chronology and segment length in the original publication script). Observed values change in "
           "single 0.1 bar steps; persistence repeats the previous value and the contextual Ridge reference responds "
           "smoothly. Buffer and tank pressure are drawn on separate axes.")
    return finish(fig, meta("Q1_H03", "hy2res_pressure_traces", "plot_hy2res_pressure_traces", "Held-out pressure traces",
                            "How do the references follow held-out pressure?",
                            ["03_results/hy2res_external_validation/test_predictions.csv.gz (segment 2382)"], cap), out)


def plot_hy2res_flow_trace(d, out):
    g = _seg(d, "h2_flow")
    fig = figure()
    title(fig, "Held-out electrolyzer hydrogen flow and one-step predictions")
    ax = fig.add_subplot()
    ax.plot(g.t, g.y_true, color=C["text"], lw=1.8, drawstyle="steps-post", label="Observed")
    ax.plot(g.t, g.persistence_prediction, color=MOD_STY["persistence"]["color"], lw=1.0, drawstyle="steps-post", label="Persistence")
    ax.plot(g.t, g.contextual_prediction, color=MOD_STY["contextual"]["color"], lw=1.2, ls="--", label="Contextual Ridge")
    ax.set_ylabel("h2_flow (NL/h, over the preceding interval)")
    ax.set_xlabel("Minutes from 12:36:44, 12 April 2024")
    ygrid(ax)
    fig.legend(loc="outside lower center", ncol=3)
    cap = (f"Electrolyzer hydrogen flow in the same held-out segment 2382 ({len(g)} steps). h2_flow is a normalised "
           "volumetric production over the preceding sample interval and is not quantised at 0.1 (TAB_H01).")
    return finish(fig, meta("Q1_H04", "hy2res_flow_trace", "plot_hy2res_flow_trace", "Held-out flow trace",
                            "How do the references follow held-out hydrogen flow?",
                            ["03_results/hy2res_external_validation/test_predictions.csv.gz (segment 2382)"], cap), out)


def plot_hy2res_state_error(d, out):
    h = d["held"]
    h = h[h.target.isin(["pres_buf", "pres_comp", "h2_flow"]) & h.state.isin(["electrolyzer_active", "multiple_active"])]
    fig = figure()
    title(fig, "Relative error change of contextual Ridge depends on target and operating state")
    axs = fig.subplots(1, 2, sharey=True)
    lab = {"pres_buf": "Buffer pressure", "pres_comp": "Tank pressure", "h2_flow": "Hydrogen flow"}
    for ax, met, xl in [(axs[0], "mae_change_pct", "MAE change, Ridge vs persistence (%)"),
                        (axs[1], "rmse_change_pct", "RMSE change, Ridge vs persistence (%)")]:
        for j, (st, mk, c) in enumerate([("electrolyzer_active", "o", C["teal"]), ("multiple_active", "^", C["burgundy"])]):
            g = h[h.state == st].set_index("target").loc[list(lab)]
            ax.scatter(g[met], np.arange(3) + (j - 0.5) * 0.2, marker=mk, s=70, color=c, edgecolor=C["text"], lw=0.5,
                       zorder=3, label=f"{st.replace('_', ' ')} (scored rows {int(g.scored.iloc[0]):,})")
        ax.axvline(0, color=C["text"], lw=0.8)
        ax.set_xlabel(xl)
        xgrid(ax)
    axs[0].set_yticks(range(3), list(lab.values()))
    axs[0].invert_yaxis()
    fig.legend(*axs[0].get_legend_handles_labels(), loc="outside lower center", ncol=2, title="Power-defined operating state")
    f = h[(h.target == "h2_flow") & (h.state == "multiple_active")].iloc[0]
    cap = ("Relative change (Ridge − persistence) / persistence of MAE and RMSE on the frozen held-out test mask, per target "
           "and power-defined operating state (states with scored rows). Negative favours Ridge. In the minority "
           f"compressor-powered state the flow RMSE rises from {f.persistence_rmse:.4f} to {f.contextual_ridge_rmse:.4f} NL/h "
           f"({f.rmse_change_pct:+.0f} %). Unknown-power rows (412–413) are not scored.")
    return finish(fig, meta("Q1_H05", "hy2res_state_dependent_error", "plot_hy2res_state_error",
                            "State-dependent reference error", "Does the reference comparison change with the operating state?",
                            ["03_results/hy2res_external_validation/publication/TABLE_2_HELD_OUT.csv"], cap), out)


def plot_hy2res_quantization(d, out):
    s = d["step_contribution"]
    g = d["recording_grid"].set_index("channel")
    fig = figure()
    title(fig, "Pressure targets change in single 0.1 bar steps or not at all")
    ax = fig.add_subplot()
    cls = ["0 (unchanged)", "±1 increment", "±2 increments", "≥3 increments"]
    for j, (ch, mk, c) in enumerate([("pres_buf", "o", C["teal"]), ("pres_comp", "s", C["navy"])]):
        v = s[s.channel == ch].set_index("step_class").loc[cls]
        ax.bar(np.arange(4) + (j - 0.5) * 0.36, v.share_rows, width=0.34, color=c, hatch=None if j == 0 else "//",
               edgecolor=C["white"], zorder=3, label=f"{ch} (n = {int(v.n.sum()):,})")
        for i, (sh, n) in enumerate(zip(v.share_rows, v.n)):
            ax.text(i + (j - 0.5) * 0.36, sh + 0.015, f"{int(n):,}", ha="center", fontsize=9)
    ax.set_xticks(range(4), [f"{c}" for c in cls])
    ax.set_ylabel("Share of scored test rows")
    ax.set_xlabel("Recorded one-step change y_t − y_(t−1), in 0.1 bar increments")
    ax.set_ylim(0, 1.08)
    ygrid(ax)
    fig.legend(loc="outside right center", title="Target")
    cap = (f"Distribution of recorded one-step changes on the shared 43,168-row held-out mask. Both pressures lie 100 % on a "
           f"0.1 bar grid over the full source ({int(g.loc['pres_buf', 'distinct_values'])} and "
           f"{int(g.loc['pres_comp', 'distinct_values'])} distinct values; TAB_H01). Buffer pressure is unchanged on 96.0 % of "
           "rows and tank pressure on 74.4 %; otherwise the change is exactly one increment (one tank row changes by two). "
           "0.1 bar is the recording increment, not documented instrument resolution or accuracy.")
    return finish(fig, meta("Q1_H06", "hy2res_pressure_quantization", "plot_hy2res_quantization", "Pressure quantization",
                            "On what grid are the pressure targets recorded?",
                            ["evidence_enhancement/results/analysis/step_contribution.csv", "recording_grid.csv"], cap), out)


def plot_hy2res_error_increments(d, out):
    q = d["quantization_comparison"].set_index("channel")
    fig = figure()
    title(fig, "Pressure errors are a fraction of one recording increment")
    axs = fig.subplots(1, 2, sharey=True)
    for ax, met, xl in [(axs[0], "mae", "MAE (0.1 bar increments)"), (axs[1], "rmse", "RMSE (0.1 bar increments)")]:
        for j, (m, col) in enumerate([("persistence", f"persistence_{met}_incr"), ("contextual", f"ridge_{met}_incr")]):
            st = MOD_STY[m]
            ax.scatter(q.loc[["pres_buf", "pres_comp"], col], np.arange(2) + (j - 0.5) * 0.2, marker=st["marker"], s=80,
                       color=st["color"], edgecolor=C["text"], lw=0.5, zorder=3, label=st["label"])
        ax.set_xlabel(xl)
        ax.set_xlim(0, None)
        xgrid(ax)
    axs[0].set_yticks([0, 1], ["Buffer pressure", "Tank pressure"])
    axs[0].invert_yaxis()
    fig.legend(*axs[0].get_legend_handles_labels(), loc="outside lower center", ncol=2)
    cap = (f"Held-out MAE and RMSE divided by the 0.1 bar recording increment (43,168 rows, 409 segments). ΔMAE (Ridge − "
           f"persistence): buffer {q.loc['pres_buf', 'delta_mae'] / 0.1:+.4f}, tank {q.loc['pres_comp', 'delta_mae'] / 0.1:+.4f} "
           f"increments; ΔRMSE: {q.loc['pres_buf', 'delta_rmse'] / 0.1:+.4f} and {q.loc['pres_comp', 'delta_rmse'] / 0.1:+.4f}. "
           "All differences are below 0.1 of one recorded step. Persistence is exactly right on "
           f"{q.loc['pres_buf', 'persistence_exact_rate']:.1%} (buffer) and {q.loc['pres_comp', 'persistence_exact_rate']:.1%} (tank) of rows.")
    return finish(fig, meta("Q1_H07", "hy2res_error_in_increments", "plot_hy2res_error_increments", "Errors in recording increments",
                            "How large are the pressure errors relative to the recording grid?",
                            ["evidence_enhancement/results/analysis/quantization_comparison.csv"], cap), out)


def plot_hy2res_error_tradeoff(d, out):
    s = d["step_contribution"]
    cls = ["0 (unchanged)", "±1 increment", "±2 increments"]
    fig = figure()
    title(fig, "Ridge's RMSE gain comes from single-step rows, paid for on unchanged rows")
    ax = fig.add_subplot()
    for j, (ch, c, h) in enumerate([("pres_buf", C["teal"], None), ("pres_comp", C["navy"], "//")]):
        v = s[s.channel == ch].set_index("step_class").loc[cls]
        ax.barh(np.arange(3) + (j - 0.5) * 0.36, v.delta_sse, height=0.34, color=c, hatch=h, edgecolor=C["white"], zorder=3,
                label=f"{ch} (net ΔSSE {v.delta_sse.sum():+.2f} bar²)")
    ax.axvline(0, color=C["text"], lw=0.8)
    ax.set_yticks(range(3), cls)
    ax.invert_yaxis()
    ax.set_xlabel("ΔSSE, Ridge − persistence (bar²); negative favours Ridge")
    xgrid(ax)
    fig.legend(loc="outside lower center", ncol=2)
    t = s[s.channel == "pres_comp"].set_index("step_class")
    cap = (f"Squared-error difference by recorded step class on the held-out mask. Tank pressure: Ridge gains "
           f"{t.loc['±1 increment', 'delta_sse']:.1f} bar² on single-step rows and loses {t.loc['0 (unchanged)', 'delta_sse']:+.1f} bar² "
           "on unchanged rows. Ridge predictions are not rounded to the grid. The RMSE improvement therefore reflects partial "
           "anticipation of single-increment transitions, not physically resolved accuracy.")
    return finish(fig, meta("Q1_H08", "hy2res_error_tradeoff", "plot_hy2res_error_tradeoff", "Error trade-off by step class",
                            "Why does Ridge improve RMSE while worsening buffer MAE?",
                            ["evidence_enhancement/results/analysis/step_contribution.csv"], cap), out)


def plot_hy2res_drift(d, out):
    ch = d["chronology"]
    b = d["development_bounds"].set_index("channel")
    fig = figure()
    title(fig, "Tank pressure drifts above the development range in the test period")
    axs = fig.subplots(1, 2)
    for ax, c, lab in [(axs[0], "pres_comp", "Tank pressure pres_comp (bar)"), (axs[1], "pres_buf", "Buffer pressure pres_buf (bar)")]:
        g = ch[ch.channel == c].set_index("partition").loc[PARTS]
        y = np.arange(4)
        ax.hlines(y, g.minimum, g.maximum, color=C["grid"], lw=6, zorder=1)
        ax.hlines(y, g.p05, g.p95, color=[PCOL[p] for p in PARTS], lw=6, zorder=2)
        ax.scatter(g["median"], y, marker="D", s=50, color=C["white"], edgecolor=C["text"], zorder=3)
        ax.axvline(b.loc[c, "dev_max"], color=C["burgundy"], ls="--", lw=1.2)
        ax.text(b.loc[c, "dev_max"], 3.55, f" development max {b.loc[c, 'dev_max']:g}", color=C["burgundy"], fontsize=10, va="center")
        ax.set_yticks(y, [p.capitalize() for p in PARTS])
        ax.set_ylim(3.8, -0.5)
        ax.set_xlabel(lab)
        xgrid(ax)
    g = ch[ch.channel == "pres_comp"].set_index("partition")
    cap = (f"Per-partition distributions of the raw source values (thin grey: min–max; coloured: 5th–95th percentile; "
           f"diamond: median). Tank-pressure medians rise from {g.loc['development', 'median']:g} bar (development) to "
           f"{g.loc['validation', 'median']:g} (validation) and {g.loc['test', 'median']:g} (test); {g.loc['test', 'above_dev_max_rate']:.1%} "
           f"of test rows exceed the development maximum {b.loc['pres_comp', 'dev_max']:g} bar. Buffer pressure stays inside its "
           "development range. Validation contained no out-of-range rows, so development-only checks could not reveal the drift.")
    return finish(fig, meta("Q1_H09", "hy2res_tank_pressure_drift", "plot_hy2res_drift", "Tank-pressure drift",
                            "Does the test period stay inside the development operating range?",
                            ["evidence_enhancement/results/analysis/chronology.csv", "development_bounds.csv"], cap), out)


def plot_hy2res_unresolved_reasons(d, out):
    u = d["unresolved_taxonomy"]
    u = u[u.decision == "Unresolved"].copy()
    u["reason"] = u.primary_reason.str.replace(r" \(.*\)", "", regex=True)
    fig = figure()
    title(fig, "Unresolved decisions are almost all out-of-support tank pressure")
    ax = fig.add_subplot()
    parts = [("electrolyzer_only", "Electrolyzer only", C["teal"], None), ("compressor_powered", "Compressor powered", C["burgundy"], "xx"),
             ("unknown_power", "Unknown power", C["slate"], "//")]
    y = np.arange(len(u))
    left = np.zeros(len(u))
    for col, lab, c, h in parts:
        v = u[col].to_numpy(float)
        ax.barh(y, v, left=left, color=c, hatch=h, edgecolor=C["white"], height=0.55, zorder=3, label=lab)
        left += v
    for i, (n, sg) in enumerate(zip(u.rows, u.segments)):
        ax.text(left[i] + 300, i, f"{int(n):,} rows · {int(sg)} segments", va="center", fontsize=10)
    ax.set_yticks(y, [r.replace("_", " ") for r in u.primary_reason])
    ax.invert_yaxis()
    ax.set_xlim(0, 42000)
    ax.xaxis.set_major_formatter(lambda v, _: f"{int(v):,}")
    ax.set_xlabel("Unresolved test rows")
    xgrid(ax)
    fig.legend(loc="outside lower center", ncol=3, title="Power-defined state at the forecast origin")
    tot = int(u.rows.sum())
    o = u[u.primary_reason.str.startswith("OUT_OF_SUPPORT")].iloc[0]
    cap = (f"Exclusive primary reason for each of the {tot:,} UNRESOLVED test rows (denominator 44,397 test rows). "
           f"OUT_OF_SUPPORT (tank pressure above the development maximum) accounts for {int(o.rows):,} ({o.pct_of_unresolved:.1%}); "
           "INVALID_INPUT (nonfinite origin measurement) and EMPTY_CELL (no state with two development segments) account for the "
           "rest. These are kept distinct from ambiguity. Reasons reproduce the frozen min–max guard exactly.")
    return finish(fig, meta("Q1_H10", "hy2res_unresolved_reasons", "plot_hy2res_unresolved_reasons", "Unresolved-reason decomposition",
                            "Why does the frozen state rule abstain on most test rows?",
                            ["evidence_enhancement/results/analysis/unresolved_taxonomy.csv"], cap), out)


def plot_hy2res_validity_over_time(d, out):
    t = d["time_bins"].copy()
    t["time"] = pd.to_datetime(t.time)
    fig = figure()
    title(fig, "Abstention follows the out-of-support fraction over time")
    ax = fig.add_subplot()
    x = (t.time - t.time.min()) / pd.Timedelta(hours=1)
    ax.plot(x, t.unresolved_fraction, color=C["burgundy"], marker="o", lw=1.6, label="Unresolved fraction")
    ax.plot(x, t.out_of_support_fraction, color=C["navy"], marker="s", ls="--", lw=1.4, label="Out-of-support fraction")
    ax.set_ylim(-0.03, 1.05)
    ax.set_ylabel("Share of rows in the 6 h bin")
    ax.set_xlabel(f"Hours since {t.time.min():%d %B %Y %H:%M} (6 h bins)")
    ygrid(ax)
    ax2 = ax.twinx()
    ax2.spines["right"].set_visible(True)
    ax2.plot(x, t.tank_median, color=C["teal"], marker="^", ls=":", lw=1.4, label="Median tank pressure (bar)")
    ax2.axhline(d["development_bounds"].set_index("channel").loc["pres_comp", "dev_max"], color=C["teal"], lw=0.8)
    ax2.set_ylabel("Median tank pressure (bar)")
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    fig.legend(h1 + h2, l1 + l2, loc="outside lower center", ncol=3)
    cap = (f"Held-out test rows in {len(t)} six-hour bins: unresolved and out-of-support fractions (left axis) and median tank "
           "pressure (right axis; thin line = development maximum 106.6 bar). Bins whose median tank pressure is at or above "
           "107.0 bar are fully unresolved. Descriptive association only.")
    return finish(fig, meta("Q1_H11", "hy2res_validity_over_time", "plot_hy2res_validity_over_time", "Decision validity over time",
                            "Does abstention track the support breach over time?",
                            ["evidence_enhancement/results/analysis/time_bins.csv"], cap), out)


def plot_hy2res_state_outcomes(d, out):
    s = d["state_outcomes"].set_index("state")
    states = [("electrolyzer_active", "Electrolyzer only"), ("multiple_active", "Compressor powered"), ("unknown", "Unknown power")]
    cols = [("specific", "SPECIFIC (all agree with majority)", C["teal"], None), ("ambiguous", "AMBIGUOUS", C["ochre"], "..."),
            ("unresolved_out_of_support", "UNRESOLVED: out of support", C["navy"], None),
            ("unresolved_invalid", "UNRESOLVED: invalid input", C["slate"], "//"),
            ("unresolved_empty_cell", "UNRESOLVED: empty cell", C["burgundy"], "xx")]
    fig = figure()
    title(fig, "The state rule never makes a specific call on the minority state")
    ax = fig.add_subplot()
    for i, (st, lab) in enumerate(states):
        r = s.loc[st]
        left = 0
        for col, name, c, h in cols:
            v = r[col] / r.rows
            if v > 0:
                ax.barh(i, v, left=left, color=c, hatch=h, edgecolor=C["white"], height=0.55, zorder=3,
                        label=name if i == 0 or name not in ax.get_legend_handles_labels()[1] else None)
                if v > 0.05:
                    ax.text(left + v / 2, i, f"{int(r[col]):,}", ha="center", va="center", fontsize=10,
                            bbox=dict(facecolor=C["white"], edgecolor="none", pad=1.2))
                left += v
    ax.set_yticks(range(3), [f"{lab}\n({int(s.loc[st, 'rows']):,} rows, {int(s.loc[st, 'segments'])} segments)" for st, lab in states])
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.set_xlabel("Share of the state's test rows")
    xgrid(ax)
    h, l = ax.get_legend_handles_labels()
    u = dict(zip(l, h))
    fig.legend(u.values(), u.keys(), loc="outside lower center", ncol=3)
    m = s.loc["multiple_active"]
    cap = (f"Frozen state-rule outcomes per power-defined operating state (44,397 test rows). The compressor-powered minority "
           f"state ({int(m.rows)} rows) receives 0 SPECIFIC calls: {int(m.ambiguous)} ambiguous and {int(m.unresolved)} unresolved. "
           f"All {int(s.loc['electrolyzer_active', 'specific']):,} SPECIFIC calls agree with a constant 'electrolyzer only' baseline. "
           "Operating-state labels are not fault labels; this is not compressor-fault detection.")
    return finish(fig, meta("Q1_H12", "hy2res_state_outcomes", "plot_hy2res_state_outcomes", "Operating-state decision outcomes",
                            "Does the evidence rule recognise the minority operating state?",
                            ["evidence_enhancement/results/analysis/state_outcomes.csv"], cap), out)


def plot_hy2res_positive_flow(d, out):
    t = d["distinguishability"]
    fig = figure()
    title(fig, "Without zero-flow rows, pressure and flow no longer separate the states")
    ax = fig.add_subplot()
    chans = [("h2_flow", "Hydrogen flow"), ("pres_buf", "Buffer pressure"), ("pres_comp", "Tank pressure")]
    for j, (rule, mk, c) in enumerate([("all rows", "o", C["navy"]), ("positive flow only", "D", C["ochre"])]):
        g = t[t.flow_rule == rule].set_index("channel").loc[[c_ for c_, _ in chans]]
        ax.scatter(g.rank_probability, np.arange(3) + (j - 0.5) * 0.2, marker=mk, s=80, color=c, edgecolor=C["text"],
                   lw=0.5, zorder=3, label=f"{rule} ({int(g.n_electrolyzer_only.iloc[0]):,} vs {int(g.n_compressor.iloc[0])} rows)")
    ax.axvline(0.5, color=C["slate"], ls="--", lw=1)
    ax.text(0.505, -0.5, "0.5 = no separation", fontsize=10, color=C["slate"])
    ax.set_yticks(range(3), [lab for _, lab in chans])
    ax.set_ylim(2.5, -0.7)
    ax.set_xlim(0.4, 1.0)
    ax.set_xlabel("Rank probability P(compressor-state value > electrolyzer-only value) + ½ P(tie)")
    xgrid(ax)
    fig.legend(loc="outside lower center", ncol=2)
    f = t[t.channel == "h2_flow"].set_index("flow_rule").rank_probability
    cap = (f"Empirical rank probability between compressor-powered (12 segments) and electrolyzer-only test rows. Flow separates "
           f"the states with all rows ({f['all rows']:.3f}) only because most electrolyzer-only rows have zero flow; restricted to "
           f"positive flow it falls to {f['positive flow only']:.3f}; with positive flow all three channels lie between 0.46 and 0.56. This is evidence "
           "sufficiency, not state classification accuracy.")
    return finish(fig, meta("Q1_H13", "hy2res_positive_flow_distinguishability", "plot_hy2res_positive_flow",
                            "Positive-flow distinguishability", "Do the measured channels separate the operating states once zero flow is removed?",
                            ["evidence_enhancement/results/analysis/distinguishability.csv"], cap), out)


def plot_hy2res_support_breach(d, out):
    a = d["support_attribution"]
    a = a[a.condition.isin(["below", "above", "nonfinite"])]
    fig = figure()
    title(fig, "Only tank pressure breaches the development support")
    ax = fig.add_subplot()
    chans = ["pres_buf", "pres_comp", "h2_flow"]
    conds = [("below", "Below development minimum", C["blue"], None), ("above", "Above development maximum", C["burgundy"], "xx"),
             ("nonfinite", "Nonfinite input", C["slate"], "//")]
    for j, (cond, lab, c, h) in enumerate(conds):
        g = a[a.condition == cond].set_index("channel").loc[chans]
        ax.bar(np.arange(3) + (j - 1) * 0.26, g.rows, width=0.24, color=c, hatch=h, edgecolor=C["white"], zorder=3, label=lab)
        for i, v in enumerate(g.rows):
            ax.text(i + (j - 1) * 0.26, v * 1.15 + 1, f"{int(v):,}", ha="center", fontsize=9)
    ax.set_yscale("symlog", linthresh=10)
    ax.set_ylim(0, 2e5)
    ax.set_xticks(range(3), ["Buffer pressure", "Tank pressure", "Hydrogen flow"])
    ax.set_ylabel("Test rows (symmetric log scale)")
    ygrid(ax)
    fig.legend(loc="outside lower center", ncol=3)
    cap = ("Development-support violations per channel among the 44,397 test rows (non-exclusive per channel). Tank "
           "pressure exceeds the development maximum on 31,589 rows (299 segments, up to 4.1 bar above); no channel falls "
           "below its development minimum; buffer pressure and flow never leave their support. The 413 nonfinite rows are the "
           "same rows in every channel (segment-start origins).")
    return finish(fig, meta("Q1_H14", "hy2res_support_breach", "plot_hy2res_support_breach", "Support violations by channel",
                            "Which channels leave the development support in the test period?",
                            ["evidence_enhancement/results/analysis/support_attribution.csv"], cap), out)


FIGURES = [plot_hy2res_channel_architecture, plot_hy2res_partition_timeline, plot_hy2res_pressure_traces,
           plot_hy2res_flow_trace, plot_hy2res_state_error, plot_hy2res_quantization, plot_hy2res_error_increments,
           plot_hy2res_error_tradeoff, plot_hy2res_drift, plot_hy2res_unresolved_reasons, plot_hy2res_validity_over_time,
           plot_hy2res_state_outcomes, plot_hy2res_positive_flow, plot_hy2res_support_breach]
