"""Render the three Study B figures from the audit and evaluation results."""
import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

NAVY, BLUE, TEAL, SLATE, RED, WHITE = (
    "#10263E", "#356CB1", "#007F86", "#64748B", "#A33F43", "#F6F5F0"
)


def save(figure, out, name):
    for ext in ("svg", "pdf", "png"):
        figure.savefig(out / f"{name}.{ext}", dpi=360, bbox_inches="tight")
    plt.close(figure)


def render(out, protocol, metrics, predictions):
    plt.rcParams.update({"text.color": NAVY, "axes.labelcolor": NAVY,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "figure.facecolor": WHITE, "axes.facecolor": WHITE,
                         "font.size": 10, "svg.fonttype": "none"})
    with (out / "experiment_registry.csv").open(encoding="utf-8", newline="") as stream:
        registry = {int(row["run"]): row for row in csv.DictReader(stream)}
    partition = {int(n): split for n, split in protocol["partition"].items()}

    fig, (ax, detail) = plt.subplots(2, 1, figsize=(10, 5.2),
                                     gridspec_kw={"height_ratios": [1, 2]}, layout="constrained")
    for run in registry:
        color = {"development": TEAL, "test": BLUE}.get(partition.get(run), SLATE)
        ax.scatter(run, 0, color=color, s=36)
    ax.set(yticks=[], xticks=range(1, 30), xlabel="Experiment", ylim=(-.5, .5))
    ax.spines.left.set_visible(False)
    ax.set_title("Experimental inventory and grouped evaluation", loc="left", weight="bold")
    ax.legend(handles=[Line2D([], [], marker="o", color=c, linestyle="", label=l)
                      for l, c in [("Outside scope", SLATE), ("Development", TEAL), ("Held out", BLUE)]],
              loc="upper left", frameon=False, ncol=3)
    for i, run in enumerate(partition):
        row = registry[run]
        color = TEAL if partition[run] == "development" else BLUE
        detail.text(.02, 8-i, f"{run:02d}", color=color, weight="bold")
        detail.text(.14, 8-i, protocol["groups"][str(run)])
        detail.text(.36, 8-i, row["material_1"] + " / " + row["material_2"])
        detail.text(.61, 8-i, f'{row["p1_bar"]} / {row["p2_bar"]} bar')
        detail.text(.81, 8-i, f'{row["half_cycle_min"]} min')
    for x, label in zip((.02, .14, .36, .61, .81),
                        ("Run", "Recording group", "Materials", "p1 / p2", "Half-cycle")):
        detail.text(x, 9, label, weight="bold")
    detail.set(xlim=(0, 1), ylim=(.6, 10))
    detail.set_axis_off()
    detail.set_title("Dual-stage subset · P-2 (barg) and MFC-3 (ln/min)", loc="left")
    save(fig, out, "figure_1_design")

    channels = protocol["targets"]
    units = {row["channel"]: row["unit"] for row in metrics}
    cases = protocol["figure_cases"]
    fig, axes = plt.subplots(2, len(cases), figsize=(11, 5.5), squeeze=False,
                             sharex="col", layout="constrained")
    for col, run in enumerate(cases):
        t, actual, b0, b1 = predictions[run]
        # Do not draw curves across invalid intervals.
        gaps = np.flatnonzero(np.diff(t) > protocol["interval_s"][1]) + 1
        for i, key in enumerate(channels):
            ax = axes[i, col]
            for signal, color, line, label in [(actual, NAVY, "-", "Measured"),
                                               (b0, SLATE, "--", "B0 persistence"),
                                               (b1, TEAL, ":", "B1 ridge")]:
                for j, segment in enumerate(np.split(np.arange(len(t)), gaps)):
                    ax.plot((t[segment]-t[0])/60, signal[segment, i], color=color,
                            lw=1, ls=line, label=label if j == 0 else None)
            ax.set_ylabel(f"{key} ({units[key]})")
            ax.grid(axis="y", color=SLATE, alpha=.18)
        row = registry[run]
        axes[0, col].set_title(f'Run {run} · {row["material_1"]} · {row["p2_bar"]} bar outlet')
        axes[-1, col].set_xlabel("Minutes from first scored observation")
    axes[0, 0].legend(loc="upper right", frameon=False, fontsize=8)
    fig.suptitle("Held-out experimental responses", weight="bold")
    save(fig, out, "figure_2_responses")

    render_performance(out, channels, units, registry, metrics)


def render_performance(out, channels, units, registry, metrics):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), layout="constrained")
    for axis, key in zip(axes, channels):
        group = [row for row in metrics if row["channel"] == key]
        for i, row in enumerate(group):
            axis.plot([row["b0_mae"], row["b1_mae"]], [i, i], color=SLATE, lw=1)
        for field, color, mark, label in [("b0_mae", BLUE, "o", "B0 persistence"),
                                          ("b1_mae", TEAL, "D", "B1 ridge")]:
            axis.scatter([r[field] for r in group], range(len(group)), color=color,
                         marker=mark, label=label)
        labels = []
        for entry in group:
            r = registry[entry["run"]]
            labels.append(f'{entry["run"]} · {r["material_1"]} · {r["p1_bar"]}/{r["p2_bar"]} bar')
        axis.set(yticks=range(len(group)), yticklabels=labels, xlabel=f"MAE ({units[key]})")
        axis.invert_yaxis()
        axis.set_title(key, loc="left", weight="bold")
        axis.grid(axis="x", color=SLATE, alpha=.18)
    axes[0].legend(frameon=False, loc="upper right")
    fig.suptitle("Held-out reference error by operating condition", weight="bold")
    save(fig, out, "figure_3_performance")

