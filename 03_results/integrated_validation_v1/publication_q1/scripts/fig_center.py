"""Center (controlled simulation) Q1 figures. One function per figure; every number is read from
verified tables of the frozen baseline or the accepted Center evidence enhancement."""
import json

import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter

from q1fig import finish
from q1style import C, DECISION, Q1, REPO, STATUS, figure, title, xgrid, ygrid

MOD = "fig_center"
ENH = REPO / "03_results/validation/center_evidence_enhancement"
PUB = REPO / "03_results/validation/publication_final_v1/tables"
TRACE = Q1 / "data/center_trace_windows.csv"

QID = {"SID213": "Q213", "ALT": "Q213-alt", "SID312": "Q312", "SID215": "Q215",
       "PRESSURE": "QP55", "TIMING": "QT59"}
QDESC = {"SID213": "withdrawal at outlet SID 213", "ALT": "withdrawal at SID 213, alternate (+5 kPa) profile",
         "SID312": "withdrawal at outlet SID 312", "SID215": "withdrawal at outlet SID 215",
         "PRESSURE": "pressure-command change at SID 55", "TIMING": "one-second command-issuance shift at SID 59"}
HID = {"WITHDRAWAL_SID213": "H213", "WITHDRAWAL_SID312": "H312", "WITHDRAWAL_SID215": "H215",
       "WITHDRAWAL_SID222": "H222", "NORMAL_OPERATION": "HN", "PRESSURE_COMMAND_SID55": "HP55",
       "COMMAND_ISSUANCE_SHIFT_SID59": "HT59", "COMPRESSOR_FAULT": "HCF", "ACTUATOR_DELAY": "HAD"}
HDESC = {"H213": "withdrawal at SID 213", "H312": "withdrawal at SID 312", "H215": "withdrawal at SID 215",
         "H222": "withdrawal at SID 222 (no adapter)", "HN": "normal operation",
         "HP55": "pressure-command change at SID 55", "HT59": "command-issuance shift at SID 59",
         "HCF": "compressor fault (no adapter)", "HAD": "actuator delay (no adapter)"}
TABLE_H = {"Normal": "HN", "W·SID 213": "H213", "W·SID 312": "H312", "W·SID 215": "H215",
           "Pressure cmd SID 55": "HP55", "Timing SID 59": "HT59"}
SCEN = ["S1", "S2", "S3", "S4", "S5", "S6", "REF"]
WQ = ["SID213", "ALT", "SID312", "SID215"]
LIMIT_DY = ("Conditional hypothetical bounds — not calibrated uncertainty. One controlled simulation source family "
            "with an air-like gas model; no field or hydrogen-material claim.")


def load():
    d = {"trace": pd.read_csv(TRACE),
         "signal": pd.read_csv(ENH / "analysis/channel_signal.csv"),
         "pairs": pd.read_csv(ENH / "analysis/pair_contrasts.csv"),
         "dy": json.loads((ENH / "analysis/dy_decisions.json").read_text(encoding="utf-8")),
         "c02": pd.read_csv(ENH / "tables/TAB_C02.csv"),
         "c03": pd.read_csv(ENH / "tables/TAB_C03.csv"),
         "c05": pd.read_csv(ENH / "tables/TAB_C05.csv"),
         "c06": pd.read_csv(ENH / "tables/TAB_C06.csv"),
         "t03": pd.read_csv(PUB / "TAB_03.csv"), "t04": pd.read_csv(PUB / "TAB_04.csv"),
         "t05": pd.read_csv(PUB / "TAB_05.csv"), "t13": pd.read_csv(PUB / "TAB_13.csv")}
    return d


def meta(fid, stem, fn, ttl, q, sources, cap, lim=LIMIT_DY, ver="values read from source tables"):
    return dict(id=fid, stem=f"{fid}_{stem}", function=fn, module=MOD, title=ttl, question=q,
                sources=sources, caption=cap, limitation=lim, study="Center", verification=ver)


def sci(ax, axis="y"):
    ax.ticklabel_format(axis=axis, style="sci", scilimits=(-3, 3), useMathText=True)


def logfmt(v, _):
    if v <= 0:
        return ""
    e = int(np.round(np.log10(v)))
    return f"$10^{{{e}}}$" if np.isclose(v, 10.0 ** e) else ""


def logx(ax):
    ax.set_xscale("log")
    ax.xaxis.set_major_locator(LogLocator(base=10, numticks=12))
    ax.xaxis.set_major_formatter(FuncFormatter(logfmt))
    ax.xaxis.set_minor_formatter(NullFormatter())


# ----------------------------------------------------------------------------- observability / traces
def plot_center_branch_observability(data, output_dir):
    s = data["signal"]
    s = s[s["query"].isin(["SID213", "SID312", "SID215"])]
    fig = figure()
    title(fig, "Each outlet withdrawal excites a different sensor group")
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 2.6])
    marks = {"SID213": ("o", C["navy"]), "SID312": ("s", C["teal"]), "SID215": ("^", C["burgundy"])}
    for k, (unit, chans, lab) in enumerate([("kg/s", ["MFS1", "MFS2", "MFS3"], "Peak |Δ| flow (kg/s)"),
                                            ("MPa", [f"PS{i}" for i in (1, 2, 4, 6, 8, 9, 10, 3)],
                                             "Peak |Δ| pressure (MPa)")]):
        ax = fig.add_subplot(gs[0, k])
        x = np.arange(len(chans))
        for j, (q, (m, c)) in enumerate(marks.items()):
            v = s[s["query"] == q].set_index("channel").loc[chans, "peak_abs"].to_numpy()
            ax.scatter(x + (j - 1) * 0.18, v, marker=m, s=46, color=c, edgecolor=C["text"], lw=0.5, zorder=3,
                       label=f"{QID[q]}: {QDESC[q]}")
        ax.set_yscale("log")
        ax.set_xticks(x, [c if c != "PS3" else "PS3 (= PS10)" for c in chans])
        ax.set_ylabel(lab)
        ygrid(ax)
        ax.set_title("Branch flow meters" if unit == "kg/s" else "Pressure sensors (PS5, PS7 show no response)",
                     fontsize=12)
    fig.legend(*ax.get_legend_handles_labels(), loc="outside lower center", ncol=3, fontsize=10)
    f3, f1 = (s.set_index(["query", "channel"]).peak_abs.loc[k] for k in [("SID213", "MFS3"), ("SID312", "MFS1")])
    f215 = s[(s["query"] == "SID215") & s.channel.str.startswith("MFS")].peak_abs.max()
    p215 = s[(s["query"] == "SID215") & s.channel.str.startswith("PS")].peak_abs.max()
    cap = (f"Peak absolute intervention − control difference per sensor for the three outlet withdrawals "
           f"(30 s prefix window). SID 213 excites branch meter MFS3 ({f3:.3f} kg/s) and SID 312 excites MFS1 "
           f"({f1:.3f} kg/s). SID 215 has no branch flow meter: its largest flow response is {f215:.1e} kg/s, and it "
           f"appears mainly in pressure (largest {p215:.4f} MPa, PS4/PS8). PS3 duplicates PS10 bitwise; PS5 and PS7 "
           f"(command channel) do not respond to withdrawals. Logarithmic axes; units are kept in separate panels.")
    return finish(fig, meta("Q1_C01", "center_branch_observability", "plot_center_branch_observability",
                            "Sensor observability of each outlet withdrawal",
                            "Which sensors can observe a withdrawal at each outlet?",
                            ["03_results/validation/center_evidence_enhancement/analysis/channel_signal.csv"], cap,
                            "Sensor layout of one simulated Center model; not a field sensor network."), output_dir)


def plot_center_controlled_response(data, output_dir):
    t = data["trace"]
    t = t[t.pair == "ALT"]
    fig = figure()
    title(fig, "A controlled withdrawal appears in branch flow, barely in pressure")
    axs = fig.subplots(2, 1, sharex=True)
    out = {}
    for ax, sen, lab, col in [(axs[0], "MFS3", "Δ MFS3 (kg/s)", C["teal"]), (axs[1], "PS1", "Δ PS1 (MPa)", C["navy"])]:
        g = t[t.sensor == sen]
        dlt = g.intervention - g.control
        ax.plot(g.time_s, dlt, color=col, lw=1.4, drawstyle="steps-post")
        ax.axvline(1000, color=C["slate"], ls="--", lw=1.0)
        ax.set_ylabel(lab)
        ygrid(ax)
        out[sen] = dlt.abs().max()
    sci(axs[1])
    axs[0].annotate("outlet area step (1000 s)", xy=(1000, out["MFS3"] * 0.5), xytext=(1040, out["MFS3"] * 0.5),
                    fontsize=10, color=C["text"], va="center",
                    arrowprops=dict(arrowstyle="-", color=C["slate"], lw=0.8))
    axs[1].set_xlabel("Simulation time (s)")
    cap = (f"Intervention minus matched control for the alternate-profile withdrawal at outlet SID 213 (both runs share "
           f"the +5 kPa reservoir profile; the outlet area steps 0.0010 → 0.0011 m² at 1000 s in the intervention only). "
           f"Exact recorded samples at 0.2 s, 900–1300 s. Branch flow MFS3 changes by up to {out['MFS3']:.3f} kg/s, "
           f"junction pressure PS1 by at most {out['PS1']:.2e} MPa.")
    return finish(fig, meta("Q1_C02", "center_controlled_response", "plot_center_controlled_response",
                            "Controlled withdrawal response", "How does a controlled outlet withdrawal appear in "
                            "the measured channels?", ["publication_q1/data/center_trace_windows.csv (hash-verified "
                                                       "accepted captures, alternate_profile pair)"], cap,
                            "One matched simulation pair; difference traces, not detection performance.",
                            "trace values extracted by the hash-verifying frozen loader"), output_dir)


def plot_center_timing_alignment(data, output_dir):
    t = data["trace"]
    t = t[(t.pair == "TIMING") & (t.time_s <= 40) & (t.time_s >= 15)]
    fig = figure()
    title(fig, "A one-second command shift moves the pressure response by one second")
    axs = fig.subplots(1, 2, sharex=True)
    for ax, sen, lab in [(axs[0], "PS7", "PS7 command channel (MPa)"), (axs[1], "PS1", "PS1 junction pressure (MPa)")]:
        g = t[t.sensor == sen]
        ax.plot(g.time_s, g.control, color=C["navy"], lw=1.6, label="Control (step at recorded knot)",
                drawstyle="steps-post")
        ax.plot(g.time_s, g.intervention, color=C["ochre"], lw=1.6, ls="--", label="Shifted command (+1 s)",
                drawstyle="steps-post")
        ax.set_ylabel(lab)
        ax.set_xlabel("Simulation time (s)")
        ygrid(ax)
    g7 = t[t.sensor == "PS7"]
    t_c = g7.time_s[g7.control.diff() > 0].iloc[0]
    t_i = g7.time_s[g7.intervention.diff() > 0].iloc[0]
    step = g7.control.max() - g7.control.min()
    fig.legend(*axs[0].get_legend_handles_labels(), loc="outside lower center", ncol=2)
    cap = (f"Command-issuance timing pair. The PS7 command channel steps by {step:.2f} MPa at {t_c:.1f} s in the "
           f"control and at {t_i:.1f} s in the intervention; PS1 follows each command. Exact recorded samples, "
           f"15–40 s. Event alignment of these traces is retrospective and does not measure actuator lag.")
    return finish(fig, meta("Q1_C03", "center_timing_alignment", "plot_center_timing_alignment",
                            "Command timing shift", "How does a one-second command-issuance shift appear?",
                            ["publication_q1/data/center_trace_windows.csv (timing pair)",
                             "03_results/validation/publication_final_v1/tables/TAB_06.csv"], cap,
                            "Command timing is distinct from actuator response; one simulated pair.",
                            "trace values extracted by the hash-verifying frozen loader"), output_dir)


# ----------------------------------------------------------------------------- archive benchmark
def plot_center_archive_recall(data, output_dir):
    d = data["t03"]
    models = ["xgboost", "random_forest", "logistic", "linear_svm", "rbf_svm"]
    names = {"xgboost": "XGBoost", "random_forest": "Random forest", "logistic": "Logistic regression",
             "linear_svm": "Linear SVM", "rbf_svm": "RBF SVM"}
    var = {"full": ("o", C["navy"], "All sensors"), "pressure": ("s", C["blue"], "Pressure only"),
           "flow": ("^", C["teal"], "Flow only"), "defaults_sensitivity": ("D", C["ochre"], "Default hyperparameters")}
    cases = int(d.cases.unique()[0])
    fig = figure()
    title(fig, "Archive leak recall never exceeds a constant 'LEAK' rule")
    ax = fig.add_subplot()
    for j, (v, (m, c, lab)) in enumerate(var.items()):
        g = d[d.variant == v].set_index("model")
        y = [i + (j - 1.5) * 0.17 for i, mo in enumerate(models) if mo in g.index]
        x = [g.loc[mo, "hits"] for mo in models if mo in g.index]
        ax.scatter(x, y, marker=m, s=50, color=c, edgecolor=C["text"], lw=0.5, zorder=3, label=lab)
    ax.axvline(cases, color=C["burgundy"], ls="--", lw=1.2, label=f"Constant 'LEAK' rule ({cases}/{cases})")
    ax.set_yticks(range(len(models)), [names[m] for m in models])
    ax.invert_yaxis()
    ax.set_xlim(-1, cases + 2)
    ax.set_xlabel(f"Held-out scenarios recalled as LEAK (of {cases})")
    xgrid(ax)
    fig.legend(*ax.get_legend_handles_labels(), loc="outside right center")
    best = d.groupby("model").recall.max()
    cap = (f"Oracle-onset event-window benchmark on the historical archive. All {cases} scored held-out scenarios carry "
           f"LEAK annotations, so a constant 'LEAK' rule recalls {cases}/{cases}. XGBoost reaches {cases}/{cases} in every "
           f"sensor variant (ties the constant rule); the best random forest recall is {best['random_forest']:.3f}. "
           f"Multiclass accuracy is not reported because only one class is present.")
    return finish(fig, meta("Q1_C04", "center_archive_recall", "plot_center_archive_recall",
                            "Archive benchmark recall", "Does archive machine-learning recall exceed a trivial rule?",
                            ["03_results/validation/publication_final_v1/tables/TAB_03.csv"], cap,
                            "Single-class held-out set: recall cannot show discrimination."), output_dir)


def plot_center_detection_tradeoff(data, output_dir):
    d = data["t04"]
    d = d[d["mode"] == "clean"].set_index("model")
    names = {"xgboost": "XGBoost", "random_forest": "Random forest", "logistic": "Logistic", "linear_svm": "Linear SVM",
             "rbf_svm": "RBF SVM", "majority": "Majority", "always_event": "Always event"}
    mk = {"xgboost": "o", "random_forest": "s", "logistic": "^", "linear_svm": "v", "rbf_svm": "D",
          "majority": "X", "always_event": "P"}
    events = int(d.events.iloc[0])
    fig = figure()
    title(fig, "Fewer missed events come with more false alarms in the 120 s replay")
    ax = fig.add_subplot()
    for m in names:
        r = d.loc[m]
        trivial = m in ("majority", "always_event")
        ax.scatter(r.false_episodes_per_inactive_hour, r.missed_events, marker=mk[m], s=70,
                   color=C["slate"] if trivial else C["navy"], edgecolor=C["text"], lw=0.5, zorder=3,
                   label=names[m])
    tr = d.loc["majority"]
    ax.annotate("Majority and always-event rules\n(identical, overlapping)", xy=(tr.false_episodes_per_inactive_hour,
                tr.missed_events), xytext=(tr.false_episodes_per_inactive_hour - 0.32, tr.missed_events - 9),
                fontsize=10, arrowprops=dict(arrowstyle="-", color=C["slate"], lw=0.8))
    ax.set_xlabel("False alarm episodes per inactive archive hour")
    ax.set_ylabel(f"Missed events (of {events})")
    ax.set_ylim(-2, events + 4)
    ygrid(ax)
    xgrid(ax)
    fig.legend(*ax.get_legend_handles_labels(), loc="outside right center", title="Model")
    rf = d.loc["random_forest"]
    cap = (f"Clean cumulative replay of the frozen 120 s decision cadence ({int(d.scenarios.iloc[0])} scenarios, "
           f"{events} events, {d.inactive_hours.iloc[0]:.2f} inactive hours). Random forest misses "
           f"{int(rf.missed_events)} events at {rf.false_episodes_per_inactive_hour:.3f} false episodes per hour; the "
           f"trivial rules (grey) miss all {events} new-alert detections. Lower-left is better on both axes.")
    return finish(fig, meta("Q1_C05", "center_detection_tradeoff", "plot_center_detection_tradeoff",
                            "Detection completeness versus false alarms",
                            "What false-alarm burden accompanies event detection in the archive replay?",
                            ["03_results/validation/publication_final_v1/tables/TAB_04.csv"], cap,
                            "Archive replay of simulated scenarios; not a field detection rate."), output_dir)


def plot_center_sensor_stress(data, output_dir):
    d = data["t05"]
    modes = ["clean", "white", "correlated", "bias", "drift", "stuck", "delay"]
    models = {"reference": ("o", C["navy"], "Reference"), "cusum": ("s", C["teal"], "CUSUM"),
              "accumulator": ("^", C["ochre"], "Accumulator"), "two_stage": ("D", C["burgundy"], "Two-stage")}
    events = int(d.events.iloc[0])
    fig = figure()
    title(fig, "Only noise stresses change detector behaviour; bias, drift and delay do not")
    axs = fig.subplots(1, 2, sharey=True)
    for j, (m, (mk, c, lab)) in enumerate(models.items()):
        g = d[d.model == m].set_index("mode").loc[modes]
        y = np.arange(len(modes)) + (j - 1.5) * 0.16
        axs[0].scatter(g.missed_events, y, marker=mk, color=c, s=44, edgecolor=C["text"], lw=0.5, zorder=3, label=lab)
        axs[1].scatter(g.false_episodes_per_inactive_hour, y, marker=mk, color=c, s=44, edgecolor=C["text"], lw=0.5,
                       zorder=3)
    axs[0].set_yticks(range(len(modes)), [m.capitalize() for m in modes])
    axs[0].invert_yaxis()
    axs[0].set_xlabel(f"Missed events (of {events})")
    axs[1].set_xlabel("False episodes per inactive hour")
    for ax in axs:
        xgrid(ax)
    fig.legend(*axs[0].get_legend_handles_labels(), loc="outside lower center", ncol=4, title="One-second detector")
    cu = d[(d.model == "cusum") & (d["mode"] == "correlated")].iloc[0]
    cap = (f"One-second causal replay under hypothetical sensor perturbations (white and correlated noise, bias, drift, "
           f"stuck, delay). Correlated noise drives CUSUM to {cu.false_episodes_per_inactive_hour:.2f} false episodes "
           f"per hour, and the reference detector raises a persistent alarm (no new-alert detections) under white and "
           f"correlated noise. Each metric keeps its own scale.")
    return finish(fig, meta("Q1_C06", "center_sensor_stress", "plot_center_sensor_stress",
                            "Detector behaviour under sensor stress",
                            "How do hypothetical sensor stresses change detection and false alarms?",
                            ["03_results/validation/publication_final_v1/tables/TAB_05.csv"], cap,
                            "Perturbations are hypothetical, without industrial calibration."), output_dir)


# ----------------------------------------------------------------------------- recognition and location
def plot_center_mechanism_recognition(data, output_dir):
    d = data["c02"]
    order = ["SID213", "ALT", "SID312", "SID215", "PRESSURE", "TIMING", "NOMINAL"]
    qlab = {**QID, "NOMINAL": "QN"}
    col = {"CORRECT": (C["teal"], None), "INCORRECT": (C["burgundy"], "xx"), "UNSUPPORTED": (C["white"], "////")}
    fig = figure()
    title(fig, "Mechanism recognition does not survive self-template removal")
    ax = fig.add_subplot()
    for i, q in enumerate(order):
        for j, cond in enumerate(["frozen", "loto"]):
            r = d[(d["query"] == q) & (d.condition == cond)].iloc[0]
            fc, h = col[r.status]
            ax.add_patch(Rectangle((j, i), 0.96, 0.9, facecolor=fc, hatch=h, edgecolor=C["text"], lw=0.6))
            near = " (near-duplicate)" if cond == "loto" and r.near_duplicate != "—" else ""
            txt = f"{r.predicted}{near}"
            ax.text(j + 0.48, i + 0.45, txt, ha="center", va="center", fontsize=10,
                    color=C["white"] if r.status == "CORRECT" else C["text"],
                    bbox=None if r.status == "CORRECT" else dict(facecolor=C["white"], edgecolor=C["text"], lw=0.5,
                                                                 pad=2))
    ax.set_xlim(0, 2)
    ax.set_ylim(len(order), 0)
    ax.set_xticks([0.48, 1.48], ["Frozen library\n(own template present)", "Own template excluded"])
    ax.set_yticks(np.arange(len(order)) + 0.45, [f"{qlab[q]}: configured {d[d['query'] == q].true_mechanism.iloc[0]}"
                                                for q in order])
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.legend(handles=[Patch(facecolor=C["teal"], edgecolor=C["text"], label="Correct"),
                       Patch(facecolor=C["burgundy"], hatch="xx", edgecolor=C["text"], label="Incorrect"),
                       Patch(facecolor=C["white"], hatch="////", edgecolor=C["text"],
                             label="Unsupported (own mechanism absent)")],
              loc="upper left", bbox_to_anchor=(1.01, 1.0))
    lo = d[(d.condition == "loto") & d["query"].isin(order[:6])]
    sup = lo[lo.status != "UNSUPPORTED"]
    agree = int((sup.status == "CORRECT").sum())
    cap = (f"Nearest-mechanism label (normalized B3 RMS, all sensors, 30 s prefix, ±1 s shift) for each controlled query. "
           f"With its own template present every query is labelled correctly at distance 0 by construction. With the "
           f"own template excluded, {agree}/{len(sup)} supported controlled queries agree (QN, the nominal run, is "
           f"matched to a near-duplicate nominal transient), {int((lo.status == 'UNSUPPORTED').sum())} are unsupported, "
           f"and Q213-alt matches only because a near-duplicate SID 213 template exists. Counts from one source family.")
    return finish(fig, meta("Q1_C07", "center_mechanism_recognition", "plot_center_mechanism_recognition",
                            "Mechanism recognition with and without self-templates",
                            "Does mechanism recognition survive removal of the query's own template?",
                            ["03_results/validation/center_evidence_enhancement/tables/TAB_C02.csv"], cap,
                            "Seven queries from one simulation family; counts, not rates."), output_dir)


def plot_center_mechanism_margins(data, output_dir):
    d = data["c02"]
    d = d[(d.condition == "loto") & d["query"].isin(["SID213", "ALT", "SID312", "SID215", "PRESSURE", "TIMING"])]
    st = {"CORRECT": ("o", C["teal"], "Correct"), "INCORRECT": ("X", C["burgundy"], "Incorrect"),
          "UNSUPPORTED": ("s", C["white"], "Unsupported")}
    fig = figure()
    title(fig, "Without self-templates, mechanism margins are near ties")
    ax = fig.add_subplot()
    order = ["SID213", "ALT", "SID312", "SID215", "PRESSURE", "TIMING"]
    for i, q in enumerate(order):
        r = d[d["query"] == q].iloc[0]
        m, c, lab = st[r.status]
        ax.scatter(r.margin, i, marker=m, s=80, color=c, edgecolor=C["text"], lw=0.8, zorder=3, label=lab)
        ax.text(r.margin * 1.35, i, f"{r.predicted} ahead of {r.runner_up}", va="center", fontsize=10)
    logx(ax)
    ax.set_xlim(5e-6, 1)
    ax.set_yticks(range(len(order)), [QID[q] for q in order])
    ax.invert_yaxis()
    ax.set_xlabel("Score margin, runner-up minus best (normalized B3 RMS)")
    xgrid(ax)
    h, lab = ax.get_legend_handles_labels()
    u = dict(zip(lab, h))
    fig.legend(u.values(), u.keys(), loc="outside lower center", ncol=3)
    m213 = d[d["query"] == "SID213"].margin.iloc[0]
    m312 = d[d["query"] == "SID312"].margin.iloc[0]
    cap = (f"Margin between the best and runner-up mechanism with the query's own template excluded (logarithmic axis). "
           f"Q213 falls behind the zero residual 'Normal' by {m213:.1e}; Q312 is correct only by {m312:.1e}. Labels "
           f"next to the markers name the leading and runner-up mechanisms.")
    return finish(fig, meta("Q1_C08", "center_mechanism_margins", "plot_center_mechanism_margins",
                            "Mechanism ranking margins", "How close are competing mechanisms once self-templates "
                            "are removed?", ["03_results/validation/center_evidence_enhancement/tables/TAB_C02.csv"], cap,
                            "Dimensionless normalized scores; margins are not probabilities."), output_dir)


def plot_center_location_ranking(data, output_dir):
    d = data["c03"]
    rows = [("SID213", "loto"), ("SID213", "loto_replicate"), ("ALT", "loto"), ("SID312", "loto"), ("SID215", "loto")]
    cl = {"loto": "own template excluded", "loto_replicate": "+ independent SID 213 replicate"}
    sids = {"213": ("o", C["navy"]), "312": ("s", C["teal"]), "215": ("^", C["ochre"])}
    fig = figure()
    title(fig, "Location ranks only where an independent same-outlet template exists")
    ax = fig.add_subplot()
    for i, (q, cnd) in enumerate(rows):
        r = d[(d["query"] == q) & (d.condition == cnd)].iloc[0]
        for sid, (m, c) in sids.items():
            v = r[f"score_SID{sid}"]
            if v == "—":
                continue
            true = str(r.true_SID) == sid
            off = {"213": -0.16, "312": 0.0, "215": 0.16}[sid]
            ax.scatter(float(v), i + off, marker=m, s=90 if true else 55, color=c if true else C["white"],
                       edgecolor=c, lw=1.6, zorder=3)
        ax.text(1.4e-1, i, "ranked: top-1 correct" if r.status == "CORRECT" else "unsupported: true outlet absent",
                va="center", fontsize=10, color=C["teal"] if r.status == "CORRECT" else C["burgundy"])
    logx(ax)
    ax.set_xlim(1e-5, 1.4)
    ax.set_yticks(range(len(rows)), [f"{QID[q]} ({cl[c]})" for q, c in rows])
    ax.invert_yaxis()
    ax.set_xlabel("Distance to candidate outlet template (normalized B3 RMS, lower = closer)")
    xgrid(ax)
    hs = [Line2D([], [], marker=m, ls="", color=c, mec=c, ms=8, label=f"Candidate SID {s}") for s, (m, c) in sids.items()]
    hs += [Line2D([], [], marker="o", ls="", color=C["slate"], ms=9, label="Filled: configured outlet"),
           Line2D([], [], marker="o", ls="", color=C["white"], mec=C["slate"], mew=1.5, ms=7, label="Open: rival outlet")]
    fig.legend(handles=hs, loc="outside lower center", ncol=5, fontsize=10)
    cap = ("Categorical location ranking for the withdrawal queries (all sensors, 30 s prefix, ±1 s). Q213 and Q213-alt are "
           "ranked correctly (SID 213 first) only because a second SID 213 capture exists; the two captures differ only "
           "by a +0.005 MPa reservoir overlay. Q312 and Q215 have no independent same-outlet template and cannot be "
           "ranked. This is a categorical rank, not a localization distance or accuracy.")
    return finish(fig, meta("Q1_C09", "center_location_ranking", "plot_center_location_ranking",
                            "Categorical location ranking", "Can the configured outlet be ranked first?",
                            ["03_results/validation/center_evidence_enhancement/tables/TAB_C03.csv"], cap,
                            "Two supported queries for one outlet; no localization accuracy is estimable."), output_dir)


def plot_center_sensor_group_separation(data, output_dir):
    p = data["pairs"]
    p = p[(p.clock_bound_s == 1.0) & (p.a != "ALT") & (p.b != "ALT")]
    pairs = [("SID213", "SID312"), ("SID213", "SID215"), ("SID312", "SID215")]
    grp = {"all": ("o", C["navy"], "All sensors"), "flow": ("^", C["teal"], "Flow only"),
           "omit_MFS3": ("D", C["ochre"], "All without MFS3"), "pressure": ("s", C["blue"], "Pressure only")}
    fig = figure()
    title(fig, "Outlet separation in the B3 score is carried by branch flow")
    ax = fig.add_subplot()
    for j, (g, (m, c, lab)) in enumerate(grp.items()):
        for i, (a, b) in enumerate(pairs):
            v = p[(p.a == a) & (p.b == b) & (p.group == g)].b3_rms.iloc[0]
            ax.scatter(v, i + (j - 1.5) * 0.14, marker=m, s=60, color=c, edgecolor=C["text"], lw=0.5, zorder=3,
                       label=lab if i == 0 else None)
    logx(ax)
    ax.set_yticks(range(3), [f"SID {a[3:]} vs SID {b[3:]}" for a, b in pairs])
    ax.invert_yaxis()
    ax.set_xlabel("Template contrast between outlets (normalized B3 RMS)")
    xgrid(ax)
    fig.legend(loc="outside right center", title="Sensor group")
    sh = p[(p.group == "all")].set_index(["a", "b"]).flow_share
    cap = (f"B3 contrast between withdrawal templates for each outlet pair and sensor group (±1 s, 30 s prefix). The flow "
           f"share of the all-sensor contrast is ≥ {sh.loc[pairs].min():.3f} for every pair. Pressure-only contrasts are "
           f"two to three decades smaller, and withholding MFS3 collapses the SID 213 vs SID 215 contrast, because SID 215 "
           f"is flow-blind.")
    return finish(fig, meta("Q1_C10", "center_sensor_group_separation", "plot_center_sensor_group_separation",
                            "Sensor-group dependence of outlet separation",
                            "Which sensor group carries the separation between outlets?",
                            ["03_results/validation/center_evidence_enhancement/analysis/pair_contrasts.csv"], cap,
                            "B3 normalizes by absolute channel level; equal channel weights."), output_dir)


def plot_center_native_contrast(data, output_dir):
    p = data["pairs"]
    p = p[(p.clock_bound_s == 1.0) & (p.group == "all") & (p.a != "ALT") & (p.b != "ALT")]
    lab = [f"SID {a[3:]} vs SID {b[3:]}" for a, b in zip(p.a, p.b)]
    fig = figure()
    title(fig, "In native units, outlet pressure contrasts are about 10⁻³ MPa")
    axs = fig.subplots(1, 2, sharey=True)
    y = np.arange(len(p))
    axs[0].barh(y, p.max_abs_pressure_MPa, color=C["navy"], height=0.55, zorder=3)
    axs[1].barh(y, p.max_abs_flow_kg_s, color=C["teal"], height=0.55, hatch="//", edgecolor=C["white"], zorder=3)
    axs[0].set_yticks(y, lab)
    axs[0].invert_yaxis()
    axs[0].set_xlabel("Largest pressure contrast (MPa)")
    axs[1].set_xlabel("Largest flow contrast (kg/s)")
    sci(axs[0], "x")
    for ax in axs:
        xgrid(ax)
    cap = (f"Largest absolute template difference between outlet withdrawals at the best shift within ±1 s, in native "
           f"units: pressure {p.max_abs_pressure_MPa.min():.2e}–{p.max_abs_pressure_MPa.max():.2e} MPa; flow "
           f"{p.max_abs_flow_kg_s.min():.3f}–{p.max_abs_flow_kg_s.max():.3f} kg/s. Units are not combined.")
    return finish(fig, meta("Q1_C11", "center_native_contrast", "plot_center_native_contrast",
                            "Native-unit outlet contrasts",
                            "How large are outlet contrasts in physical units?",
                            ["03_results/validation/center_evidence_enhancement/analysis/pair_contrasts.csv"], cap,
                            "Template contrasts in one simulated model; no instrument accuracy is implied."), output_dir)


# ----------------------------------------------------------------------------- formal D(Y)
def dy_status_table(dy):
    """Full status matrix (every query x hypothesis x scenario x universe x group x clock)."""
    rows = []
    for r in dy:
        for kind in ("consistent", "excluded", "indeterminate"):
            for h in r[kind]:
                st = kind.upper()
                if kind == "indeterminate" and r["indeterminate_reasons"].get(h) == "UNSUPPORTED_HYPOTHESIS":
                    st = "UNSUPPORTED"
                rows.append(dict(query=r["query"], query_id=QID[r["query"]], hypothesis=h, hypothesis_id=HID[h],
                                 configured=h == r["true_hypothesis"], universe=r["universe"], group=r["group"],
                                 clock_bound_s=r["clock_bound_s"], scenario=r["scenario"], eps_P_MPa=r["eps_P_MPa"],
                                 eps_F_kg_s=r["eps_F_kg_s"], status=st, label=r["label"]))
    return pd.DataFrame(rows)


def export_dy_tables(data, table_dir):
    m = dy_status_table(data["dy"])
    m.to_csv(table_dir / "TS01_center_dy_status_matrix.csv", index=False, lineterminator="\n")
    ids = pd.DataFrame([dict(id=v, kind="query", source_key=k, description=QDESC[k]) for k, v in QID.items()] +
                       [dict(id=v, kind="hypothesis", source_key=k, description=HDESC[v]) for k, v in HID.items()])
    ids.to_csv(table_dir / "TS02_center_dy_id_map.csv", index=False, lineterminator="\n")
    return m


def _status_grid(data, output_dir, rows, ttl, fid, stem, fn, question, cap_lead, h=6.2):
    m = dy_status_table(data["dy"])
    sel = m[(m.universe == "full") & (m.group == "all") & (m.clock_bound_s == 1.0)]
    # supported hypotheses must have the same status in both universes
    other = m[(m.universe == "restricted") & (m.group == "all") & (m.clock_bound_s == 1.0)]
    chk = sel.merge(other, on=["query", "hypothesis", "scenario"], suffixes=("", "_r"))
    assert (chk.status == chk.status_r).all(), "status differs between universes"
    fig = figure(h=h)
    title(fig, ttl)
    ax = fig.add_subplot()
    xs = {s: (i + 1 if s != "REF" else i + 1.35) for i, s in enumerate(SCEN)}
    counts = {}
    for i, (q, hyp) in enumerate(rows):
        g = sel[(sel["query"] == q) & (sel.hypothesis == hyp)].set_index("scenario")
        assert len(g) == len(SCEN), (q, hyp)
        for s in SCEN:
            st = g.loc[s, "status"]
            counts[st] = counts.get(st, 0) + 1
            sty = STATUS[st]
            ax.add_patch(Rectangle((xs[s] - 0.46, i - 0.42), 0.92, 0.84, facecolor=sty["color"], hatch=sty["hatch"],
                                   edgecolor=C["text"] if st == "UNSUPPORTED" else C["white"], lw=0.6))
            if st == "CONSISTENT":
                ax.scatter(xs[s], i, marker="o", s=14, color=C["white"], zorder=4)
        if g.configured.iloc[0]:
            ax.scatter(0.38, i, marker="D", s=26, color=C["burgundy"], zorder=4)
    ax.set_xlim(0.1, xs["REF"] + 0.6)
    ax.set_ylim(len(rows) - 0.4, -0.6)
    ax.set_xticks([xs[s] for s in SCEN], SCEN)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(rows)), [f"{QID[q]} / {HID[h]}" for q, h in rows])
    ax.tick_params(length=0)
    ax.axvline((xs["S6"] + xs["REF"]) / 2, color=C["text"], lw=0.8)
    for s in ax.spines.values():
        s.set_visible(False)
    prev = None
    for i, (q, _) in enumerate(rows):
        if prev is not None and q != prev:
            ax.axhline(i - 0.5, color=C["slate"], lw=0.8)
        prev = q
    used = [s for s in STATUS if counts.get(s)]
    hs = [Patch(facecolor=STATUS[s]["color"], hatch=STATUS[s]["hatch"], edgecolor=C["text"], label=STATUS[s]["label"])
          for s in used]
    hs.append(Line2D([], [], marker="D", ls="", color=C["burgundy"], ms=6, label="Configured hypothesis"))
    fig.legend(handles=hs, loc="outside right center", title="Hypothesis status")
    ax.set_xlabel(r"Declared bound scenario ($\varepsilon_P$, $\varepsilon_F$ increase S1 → S6; REF = reference widths)", labelpad=8)
    ax.xaxis.set_label_position("top")
    s1 = sel.drop_duplicates("scenario").set_index("scenario")
    eps = "; ".join(f"{s}: {s1.loc[s, 'eps_P_MPa']:.3g} MPa, {s1.loc[s, 'eps_F_kg_s']:.3g} kg/s" for s in SCEN)
    cap = (f"{cap_lead} Rows are query/hypothesis pairs (IDs in TS02_center_dy_id_map.csv); columns are declared total "
           f"bound scenarios (ε_total = ε_obs + ε_model per kind; {eps}). Full declared universe, all sensors, ±1 s "
           f"clock. Cell counts: " + ", ".join(f"{STATUS[k]['label'].lower()} {v}" for k, v in counts.items()) +
           ". The complete matrix for every universe, sensor group and clock bound is in "
           "TS01_center_dy_status_matrix.csv. Conditional hypothetical bounds — not calibrated uncertainty.")
    return finish(fig, meta(fid, stem, fn, ttl, question,
                            ["03_results/validation/center_evidence_enhancement/analysis/dy_decisions.json",
                             "publication_q1/tables/TS01_center_dy_status_matrix.csv"], cap,
                            ver="status re-derived from dy_decisions.json; identical in both universes (asserted)"),
                  output_dir)


def plot_center_dy_withdrawal_rivals(data, output_dir):
    rows = [(q, h) for q in WQ for h in ("WITHDRAWAL_SID213", "WITHDRAWAL_SID312", "WITHDRAWAL_SID215")
            if not ((q, h) in [("SID312", "WITHDRAWAL_SID312"), ("SID215", "WITHDRAWAL_SID215")])]
    return _status_grid(data, output_dir, rows, "Withdrawal rivals are excluded at every bound except the widest", "Q1_C12a",
                        "center_dy_status_withdrawal_rivals", "plot_center_dy_withdrawal_rivals",
                        "Which withdrawal hypotheses does formal D(Y) exclude for each withdrawal query?",
                        "Status of withdrawal hypotheses for the four withdrawal queries.", h=5.6)


def plot_center_dy_operational_rivals(data, output_dir):
    rows = [(q, h) for q in WQ for h in ("NORMAL_OPERATION", "PRESSURE_COMMAND_SID55", "COMMAND_ISSUANCE_SHIFT_SID59")]
    return _status_grid(data, output_dir, rows, "Operational rivals stay excluded except Normal at wide bounds", "Q1_C12b",
                        "center_dy_status_operational_rivals", "plot_center_dy_operational_rivals",
                        "Are operational (non-withdrawal) hypotheses excluded for the withdrawal queries?",
                        "Status of the normal, pressure-command and timing hypotheses for the withdrawal queries.",
                        h=6.2)


def plot_center_dy_operational_queries(data, output_dir):
    hy = ["NORMAL_OPERATION", "WITHDRAWAL_SID213", "WITHDRAWAL_SID312", "WITHDRAWAL_SID215",
          "PRESSURE_COMMAND_SID55", "COMMAND_ISSUANCE_SHIFT_SID59"]
    rows = [(q, h) for q in ("PRESSURE", "TIMING") for h in hy
            if (q, h) not in [("PRESSURE", "PRESSURE_COMMAND_SID55"), ("TIMING", "COMMAND_ISSUANCE_SHIFT_SID59")]]
    return _status_grid(data, output_dir, rows, "Operational queries exclude all supported rivals", "Q1_C12c",
                        "center_dy_status_operational_queries", "plot_center_dy_operational_queries",
                        "Which supported hypotheses remain for the pressure-command and timing queries?",
                        "Status of all supported hypotheses for the two operational queries (their own mechanism has "
                        "no independent adapter and is shown in Q1_C12d).", h=5.6)


def plot_center_dy_unsupported(data, output_dir):
    m = dy_status_table(data["dy"])
    never = ["WITHDRAWAL_SID222", "COMPRESSOR_FAULT", "ACTUATOR_DELAY"]
    base = m[(m.universe == "full") & (m.group == "all") & (m.clock_bound_s == 1.0) & m.hypothesis.isin(never)]
    assert set(base.status) == {"UNSUPPORTED"}, "never-modelled hypotheses must be unsupported everywhere"
    rows = [("SID312", "WITHDRAWAL_SID312"), ("SID215", "WITHDRAWAL_SID215"), ("PRESSURE", "PRESSURE_COMMAND_SID55"),
            ("TIMING", "COMMAND_ISSUANCE_SHIFT_SID59")] + [("SID213", h) for h in never]
    return _status_grid(data, output_dir, rows, "Unrepresented hypotheses stay indeterminate at every bound", "Q1_C12d",
                        "center_dy_status_unsupported", "plot_center_dy_unsupported",
                        "Which hypotheses can D(Y) never evaluate, whatever the bound?",
                        "Unsupported cases: four configured hypotheses whose only template is the query itself, and "
                        "three declared hypotheses with no adapter (H222, HCF, HAD; shown for Q213 — their status is "
                        "identical for all six queries, asserted).", h=4.6)


def _threshold_plot(data, output_dir, kind):
    d = data["c05"]
    unit = "MPa" if kind == "pressure" else "kg/s"
    d = d[(d.sensor_group == kind) & (d.clock_bound_s == 1.0)]
    queries = ["SID213", "ALT", "SID312", "SID215"]
    rows = []
    for q in queries:
        g = d[d["query"] == q]
        for _, r in g.iterrows():
            rows.append(r)
    fig = figure(h=7.2)
    word = "Pressure" if kind == "pressure" else "Flow"
    title(fig, f"{word}-only precision needed to exclude each rival")
    ax = fig.add_subplot()
    dy = data["dy"]
    col = "eps_P_MPa" if kind == "pressure" else "eps_F_kg_s"
    eps = {r["scenario"]: r[col] for r in dy if r["query"] == "SID213" and r["group"] == "all"}
    for s, v in eps.items():
        ax.axvline(v, color=C["slate"] if s != "REF" else C["burgundy"], lw=0.8, ls=":" if s != "REF" else "--",
                   zorder=1)
        ax.text(v, -0.9, s, ha="center", va="bottom", fontsize=9, color=C["text"])
    labels = []
    for i, r in enumerate(rows):
        h = TABLE_H[r.hypothesis]
        labels.append(f"{QID[r['query']]} / {h}")
        if r.role == "true":
            e, f = float(r.exclusion_onset_E), float(r.feasibility_onset_F)
            ax.scatter(f, i, marker="D", s=60, color=C["teal"], edgecolor=C["text"], lw=0.6, zorder=3)
            ax.scatter(e, i, marker="|", s=90, color=C["teal"], lw=1.5, zorder=3)
        else:
            e = float(r.exclusion_onset_E)
            ax.scatter(e, i, marker="o", s=46, color=C["navy"], edgecolor=C["text"], lw=0.5, zorder=3)
    logx(ax)
    lo = 10 ** np.floor(np.log10(min(min(eps.values()), d.exclusion_onset_E.astype(float).min())))
    ax.set_xlim(lo / 2, 2.5 if kind == "flow" else 0.5)
    ax.set_ylim(len(rows) - 0.4, -1.2)
    ax.set_yticks(range(len(rows)), labels)
    prev = None
    for i, r in enumerate(rows):
        if prev is not None and r["query"] != prev:
            ax.axhline(i - 0.5, color=C["grid"], lw=0.8)
        prev = r["query"]
    ax.set_xlabel(rf"Total declared bound $\varepsilon_{{total}}$ ({unit}, logarithmic)")
    xgrid(ax)
    hs = [Line2D([], [], marker="o", ls="", color=C["navy"], ms=7, label=r"Rival: excluded when $\varepsilon_{total}$ < onset"),
          Line2D([], [], marker="D", ls="", color=C["teal"], ms=7, label=r"Configured: consistent when $\varepsilon_{total}$ ≥ onset"),
          Line2D([], [], color=C["slate"], ls=":", label="Bound scenarios S1–S6"),
          Line2D([], [], color=C["burgundy"], ls="--", label="REF")]
    fig.legend(handles=hs, loc="outside lower center", ncol=2)
    tr = d[(d.role == "true") & (d["query"] == "SID213")].iloc[0]
    riv = d[(d.role == "rival") & (d["query"] == "SID213")].exclusion_onset_E.astype(float).min()
    cap = (f"Exact {kind}-only exclusion onsets (closed form, exact-rational confirmed) for each supported hypothesis of "
           f"the withdrawal queries, ±1 s clock, 30 s prefix. A rival is excluded while ε_total lies below its onset; the "
           f"configured hypothesis becomes consistent at its feasibility onset (diamond; the tick marks its exclusion "
           f"onset). For Q213 the correct-SPECIFIC window is [{float(tr.feasibility_onset_F):.3g}, {riv:.3g}) {unit}. "
           f"Rows absent for Q312 and Q215 configured hypotheses are unsupported (no independent template). Values are "
           f"listed in TAB_C05.")
    return finish(fig, meta("Q1_C13a" if kind == "pressure" else "Q1_C13b", f"center_dy_thresholds_{kind}",
                            f"plot_center_dy_thresholds_{kind}", f"{word}-only exclusion onsets",
                            f"What {kind} precision would separate the hypotheses?",
                            ["03_results/validation/center_evidence_enhancement/tables/TAB_C05.csv"], cap), output_dir)


def plot_center_dy_thresholds_pressure(data, output_dir):
    return _threshold_plot(data, output_dir, "pressure")


def plot_center_dy_thresholds_flow(data, output_dir):
    return _threshold_plot(data, output_dir, "flow")


def plot_center_dy_restricted_decisions(data, output_dir):
    d = data["c06"]
    d = d[d.universe == "restricted"]
    order = ["SID213", "ALT", "SID312", "SID215", "PRESSURE", "TIMING"]
    fig = figure()
    title(fig, "A restricted hypothesis universe yields wrong SPECIFIC decisions")
    ax = fig.add_subplot()
    xs = {s: (i + 1 if s != "REF" else i + 1.35) for i, s in enumerate(SCEN)}
    n = {"correct": 0, "wrong": 0}
    for i, q in enumerate(order):
        g = d[d["query"] == q].set_index("scenario")
        for s in SCEN:
            r = g.loc[s]
            if r.decision == "SPECIFIC" and r.correctness == "correct":
                fc, h, txt = C["teal"], None, "SPECIFIC (correct)"
                n["correct"] += 1
            elif r.decision == "SPECIFIC":
                fc, h, txt = C["burgundy"], "xx", "SPECIFIC (wrong)"
                n["wrong"] += 1
            else:
                fc, h, txt = DECISION[r.decision]["color"], DECISION[r.decision]["hatch"], r.decision.capitalize()
            ax.add_patch(Rectangle((xs[s] - 0.46, i - 0.42), 0.92, 0.84, facecolor=fc, hatch=h, edgecolor=C["white"],
                                   lw=0.6))
            sel = TABLE_H.get(r.selected, "") if r.decision == "SPECIFIC" else ""
            if r.decision == "SPECIFIC":
                ax.text(xs[s], i, sel, ha="center", va="center", fontsize=10, color=C["text"],
                        bbox=dict(facecolor=C["white"], edgecolor="none", pad=1.5))
    ax.set_xlim(0.5, xs["REF"] + 0.6)
    ax.set_ylim(len(order) - 0.4, -0.6)
    ax.set_xticks([xs[s] for s in SCEN], SCEN)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(order)), [QID[q] for q in order])
    ax.tick_params(length=0)
    ax.axvline((xs["S6"] + xs["REF"]) / 2, color=C["text"], lw=0.8)
    for sp in ax.spines.values():
        sp.set_visible(False)
    full = data["c06"]
    full = full[full.universe == "full"]
    fig.legend(handles=[Patch(facecolor=C["teal"], edgecolor=C["white"], label="SPECIFIC, correct"),
                        Patch(facecolor=C["burgundy"], hatch="xx", edgecolor=C["white"], label="SPECIFIC, wrong"),
                        Patch(facecolor=DECISION["AMBIGUOUS"]["color"], hatch="...", edgecolor=C["white"],
                              label="AMBIGUOUS"),
                        Patch(facecolor=DECISION["UNRESOLVED"]["color"], hatch="///", edgecolor=C["white"],
                              label="UNRESOLVED (model mismatch)")],
               loc="outside lower center", ncol=4, title="Decision (label in cell: selected hypothesis)")
    cap = (f"Set-valued D(Y) decisions in the restricted universe (only hypotheses with adapters), all sensors, ±1 s. "
           f"{n['correct']} SPECIFIC decisions are correct (the two SID 213 queries) and {n['wrong']} are wrong: the "
           f"flow-blind SID 215 withdrawal is classed as normal operation (HN) once the flow bound exceeds its tiny flow "
           f"signal. In the full declared universe all {len(full)} cells are UNRESOLVED (INDETERMINATE_HYPOTHESES). "
           f"Conditional hypothetical bounds — not calibrated uncertainty.")
    return finish(fig, meta("Q1_C14", "center_dy_restricted_decisions", "plot_center_dy_restricted_decisions",
                            "Restricted-universe decisions", "How do D(Y) decisions behave when the declared universe "
                            "omits the true mechanism?",
                            ["03_results/validation/center_evidence_enhancement/tables/TAB_C06.csv"], cap,
                            ver="counts reconcile with TAB_C07 (SPECIFIC correct 8/10)"), output_dir)


def plot_center_dy_evidence_breakdown(data, output_dir):
    d = data["c06"]
    fr = data["t13"]
    cats = [("SPEC_OK", "SPECIFIC, correct", C["teal"], None),
            ("SPEC_WRONG", "SPECIFIC, wrong", C["burgundy"], "xx"),
            ("MULTIPLE_FEASIBLE", "AMBIGUOUS (multiple feasible)", C["ochre"], "..."),
            ("MODEL_MISMATCH", "UNRESOLVED: model mismatch", C["slate"], "///"),
            ("INDETERMINATE_HYPOTHESES", "UNRESOLVED: indeterminate hypotheses", C["navy"], None),
            ("FROZEN", "UNRESOLVED: frozen run, no qualified bounds", C["white"], "\\\\")]
    res = d[d.universe == "restricted"]
    rc = res.reason.value_counts().to_dict()
    spec = res[res.decision == "SPECIFIC"]
    rc.pop("UNIQUE_FEASIBLE", None)
    rc["SPEC_OK"] = int((spec.correctness == "correct").sum())
    rc["SPEC_WRONG"] = int((spec.correctness != "correct").sum())
    rows = {"Frozen baseline\n(12 captures)": {"FROZEN": int(fr.set_index("Decision").loc["UNRESOLVED", "Observations"])},
            "Conditional, full universe\n(42 cells)": d[d.universe == "full"].reason.value_counts().to_dict(),
            "Conditional, restricted\nuniverse (42 cells)": rc}
    fig = figure()
    title(fig, "Why formal D(Y) abstains: three distinct evidence situations")
    ax = fig.add_subplot()
    for i, (lab, cnt) in enumerate(rows.items()):
        left = 0
        for key, name, c, h in cats:
            v = cnt.get(key, 0)
            if v:
                ax.barh(i, v, left=left, color=c, hatch=h, edgecolor=C["text"] if c == C["white"] else C["white"],
                        height=0.6, zorder=3, lw=0.6)
                ax.text(left + v / 2, i, str(v), ha="center", va="center", fontsize=10, color=C["text"],
                        bbox=dict(facecolor=C["white"], edgecolor="none", pad=1.2))
                left += v
    ax.set_yticks(range(len(rows)), list(rows))
    ax.invert_yaxis()
    ax.set_xlabel("Number of decisions")
    xgrid(ax)
    fig.legend(handles=[Patch(facecolor=c, hatch=h, edgecolor=C["text"] if c == C["white"] else C["white"], label=n)
                        for _, n, c, h in cats],
               loc="outside lower center", ncol=3, fontsize=10)
    cap = (f"Decision reasons. The frozen baseline returned UNRESOLVED for all {sum(rows[list(rows)[0]].values())} "
           f"captures because no qualified bounds existed. Under conditional hypothetical bounds (6 queries × 7 bound "
           f"scenarios, all sensors, ±1 s) the full declared universe never decides because three declared hypotheses "
           f"have no adapter; the restricted universe decides, but includes wrong SPECIFIC decisions (Q1_C14).")
    return finish(fig, meta("Q1_C15", "center_dy_evidence_breakdown", "plot_center_dy_evidence_breakdown",
                            "D(Y) decision reasons", "Why does formal D(Y) abstain, and when does it decide?",
                            ["03_results/validation/center_evidence_enhancement/tables/TAB_C06.csv",
                             "03_results/validation/publication_final_v1/tables/TAB_13.csv"], cap), output_dir)


FIGURES = [plot_center_branch_observability, plot_center_controlled_response, plot_center_timing_alignment,
           plot_center_archive_recall, plot_center_detection_tradeoff, plot_center_sensor_stress,
           plot_center_mechanism_recognition, plot_center_mechanism_margins, plot_center_location_ranking,
           plot_center_sensor_group_separation, plot_center_native_contrast, plot_center_dy_withdrawal_rivals,
           plot_center_dy_operational_rivals, plot_center_dy_operational_queries, plot_center_dy_unsupported,
           plot_center_dy_thresholds_pressure, plot_center_dy_thresholds_flow, plot_center_dy_restricted_decisions,
           plot_center_dy_evidence_breakdown]
