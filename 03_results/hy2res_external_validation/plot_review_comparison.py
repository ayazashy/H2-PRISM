"""Plot the frozen HY2RES test comparison from its archived metric table."""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

root = Path(__file__).resolve().parent
metrics = pd.read_csv(root / "per_channel_reference_metrics.csv")
channels = ["pres_buf", "pres_comp", "h2_flow"]
names = ["Buffer pressure", "Tank pressure", "Electrolyzer H₂ flow"]
navy, teal = "#16324F", "#087F8C"

plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none", "pdf.fonttype": 42})
fig, axes = plt.subplots(1, 2, figsize=(12, 5), layout="constrained")
fig.suptitle("HY2RES held-out reference prediction", fontsize=17, color=navy, weight="bold")
positions = np.arange(len(channels))
for axis, regimes, title in zip(
    axes,
    [("overall",), ("electrolyzer_active", "multiple_active")],
    ["A   Overall error", "B   Error by lagged power state"],
):
    for group, regime in enumerate(regimes):
        frame = metrics[metrics.operating_regime.eq(regime)]
        ratios = frame.pivot(index="target", columns="method", values=["mae", "rmse"]).loc[channels]
        count = int(frame.scored_rows.iloc[0])
        for index, (metric, color, marker) in enumerate([("mae", navy, "o"), ("rmse", teal, "s")]):
            ratio = ratios[metric].contextual_ridge / ratios[metric].persistence
            offset = (group * 2 + index - (len(regimes) * 2 - 1) / 2) * 0.15
            stage = {"overall": "", "electrolyzer_active": "Electrolyzer only · ",
                     "multiple_active": "Multiple active · "}[regime]
            axis.scatter(ratio, positions + offset, color=color, marker=marker,
                         facecolors=color if group == 0 else "white", s=46,
                         label=f"{stage}{metric.upper()} (n={count:,})", zorder=3)
    axis.axvline(1, color="#64748B", linestyle="--", linewidth=1)
    axis.set(xscale="log", xlim=(0.7, 7), yticks=positions, yticklabels=names,
             ylim=(2.5, -0.5), xlabel="Ridge error / persistence error")
    axis.set_xticks([0.75, 1, 1.5, 2, 3, 5], ["0.75", "1", "1.5", "2", "3", "5"])
    axis.minorticks_off()
    axis.set_title(title, loc="left", weight="bold", color=navy)
    axis.grid(axis="x", color="#DCE4EC")
    axis.legend(loc="upper right", fontsize=8, frameon=False)
    axis.spines[["top", "right"]].set_visible(False)

fig.supxlabel(
    "Per target: 43,168 scored rows across 409 segments (97.2% of observed targets).\n"
    "Fuel-cell targets were constant at zero. Unknown power state yielded no eligible rows.",
    fontsize=10, color=navy,
)
for suffix in ("svg", "pdf", "png"):
    path = root / "figures" / f"F3_review_error_tradeoffs.{suffix}"
    fig.savefig(path, dpi=300)
    if suffix == "svg":
        lines = path.read_text(encoding="utf-8").splitlines()
        path.write_text("\n".join(line.rstrip() for line in lines) + "\n", encoding="utf-8")
