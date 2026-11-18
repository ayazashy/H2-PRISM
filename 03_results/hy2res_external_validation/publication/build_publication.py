"""Verify frozen Study C evidence and export publication tables and figures."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd
from PIL import Image

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=True)
archive = HERE.parent
data_path = archive.parents[1] / "data/external_validation_data/HY2RES_202404.csv"
assert hashlib.md5(data_path.read_bytes()).hexdigest() == "9a3c3e3b1668596854b43bfd790d3e0e"
raw = pd.read_csv(data_path, sep=";")
mask = pd.read_csv(archive / "validity_mask.csv.gz")
pred = pd.read_csv(archive / "test_predictions.csv.gz")
metrics = pd.read_csv(archive / "per_channel_reference_metrics.csv")
schema = pd.read_csv(archive / "schema_audit.csv")
protocol = json.loads((archive / "protocol.json").read_text(encoding="utf-8"))
time = pd.to_datetime(raw.datetime)
step = time.diff().dt.total_seconds()
markers = raw.Breaks.fillna("").str.strip().str.upper()
boundary = step.ne(5) | markers.eq("OPEN") | markers.shift().eq("CLOSE")
segment = boundary.cumsum() - 1
assert raw.shape == (300768, 23) and time.is_monotonic_increasing
assert step.eq(0).sum() == 21 and segment.nunique() == 2793
assert markers.eq("OPEN").sum() == markers.eq("CLOSE").sum() == 20
np.testing.assert_array_equal(mask.segment_id, segment)
np.testing.assert_array_equal(pd.to_datetime(mask.timestamp), time)
np.testing.assert_array_equal(mask.source_row_number, np.arange(1, len(raw) + 1))
role = np.full(len(raw), "embargo", dtype=object)
dev, val = (pd.Timestamp(protocol[key]) for key in ("development_cutoff", "validation_cutoff"))
hour = pd.Timedelta(hours=1)
role[time.le(dev)] = "development"
role[time.gt(dev + hour) & time.le(val)] = "validation"
role[time.gt(val + hour)] = "test"
np.testing.assert_array_equal(role, mask.split_role)
test = role == "test"
targets = ["pres_buf", "pres_comp", "h2_flow", "pres_pila", "h2_flow_pila"]
names = ["Buffer pressure", "Tank pressure", "Electrolyzer H₂ flow", "Fuel-cell pressure", "Fuel-cell H₂ flow"]
units = ["bar", "bar", "NL/h", "bar", "NL/h"]
powers = ["P_elec", "P_comp", "P_pila"]
lag = [raw[targets + powers].shift(k).where(segment.eq(segment.shift(k)), axis=0) for k in (1, 2, 3)]
history = np.isfinite(pd.concat(lag, axis=1)).all(axis=1)
np.testing.assert_array_equal(history, mask.causal_lags_and_predictors_finite)
power = lag[0][powers]
active = power.gt(0)
known = np.isfinite(power).all(axis=1)
n_active = active.sum(axis=1)
state = pd.Series(np.select(
    [~known, n_active.eq(0), n_active.gt(1), active.P_elec, active.P_comp],
    ["unknown", "all_off", "multiple_active", "electrolyzer_active", "compressor_active"],
    default="fuel_cell_active",
))
np.testing.assert_array_equal(state, mask.operating_regime_at_forecast_origin)
methods = {"persistence": "persistence_prediction", "contextual_ridge": "contextual_prediction"}
availability, rows, tail, segments, distributions = [], [], [], [], []
for target, unit in zip(targets, units):
    observed = np.isfinite(raw[target])
    persistence = np.isfinite(lag[0][target])
    shared = observed & history
    np.testing.assert_array_equal(observed, mask[f"{target}_target_observed"])
    np.testing.assert_array_equal(shared, mask[f"{target}_prediction_eligible"])
    p = pred[pred.target.eq(target)].reset_index(drop=True)
    keep = test & shared
    np.testing.assert_array_equal(pd.to_datetime(p.timestamp), time[keep])
    np.testing.assert_array_equal(p.segment_id, segment[keep])
    np.testing.assert_array_equal(p.operating_regime, state[keep])
    np.testing.assert_allclose(p.y_true, raw.loc[keep, target])
    np.testing.assert_allclose(p.persistence_prediction, lag[0].loc[keep, target])
    np.testing.assert_allclose(p.selected_prediction, p.contextual_prediction)
    assert len(p) == 43168 and p.segment_id.nunique() == 409
    unavailable = test & observed & ~history
    insufficient = segment.groupby(segment).cumcount().lt(3)
    availability.append(dict(
        target=target, unit=unit, source_rows=len(raw), test_rows=int(test.sum()),
        observed_targets=int((test & observed).sum()), missing_targets=int((test & ~observed).sum()),
        persistence_reference_available=int((test & persistence).sum()),
        ridge_reference_available=int((test & history).sum()),
        persistence_scorable=int((test & observed & persistence).sum()),
        ridge_scorable=int(keep.sum()), common_scored=int(keep.sum()),
        common_segments=int(p.segment_id.nunique()),
        insufficient_contiguous_history=int((unavailable & insufficient).sum()),
        nonfinite_lagged_predictor_with_history=int((unavailable & ~insufficient).sum()),
        common_coverage=float(keep.sum() / (test & observed).sum()),
    ))
    for regime in ["overall", *sorted(state[test & observed].unique())]:
        group = p if regime == "overall" else p[p.operating_regime.eq(regime)]
        regime_mask = test if regime == "overall" else test & state.eq(regime)
        denom = int((regime_mask & observed).sum())
        row = dict(target=target, unit=unit, state=regime, observed_targets=denom,
                   scored=len(group), segments=group.segment_id.nunique(),
                   common_coverage=len(group) / denom, constant_target=raw[target].nunique() == 1)
        for method, col in methods.items():
            error = (group[col] - group.y_true).to_numpy()
            mae = np.abs(error).mean() if len(error) else np.nan
            rmse = np.sqrt(np.square(error).mean()) if len(error) else np.nan
            ref = metrics[metrics.target.eq(target) & metrics.operating_regime.eq(regime)
                          & metrics.method.eq(method)].iloc[0]
            np.testing.assert_allclose(
                [mae, rmse, denom, len(group), row["segments"], row["common_coverage"]],
                [ref.mae, ref.rmse, ref.observed_target_rows, ref.scored_rows,
                 ref.segments_scored, ref.reference_coverage], rtol=1e-10, atol=1e-12,
            )
            row.update({f"{method}_mae": mae, f"{method}_rmse": rmse})
        for metric in ("mae", "rmse"):
            base = row[f"persistence_{metric}"]
            row[f"{metric}_change_pct"] = (
                100 * (row[f"contextual_ridge_{metric}"] / base - 1) if base > 0 else np.nan
            )
        rows.append(row)
    if target not in targets[:3]:
        assert raw[target].eq(0).all()
        continue
    for subset, group in [("overall", p), ("observed_zero", p[p.y_true.eq(0)]),
                          ("observed_nonzero", p[p.y_true.ne(0)])]:
        if group.empty:
            continue
        for method, col in methods.items():
            error = (group[col] - group.y_true).abs().to_numpy()
            sq = np.sort(error ** 2)
            top = max(1, int(np.ceil(0.01 * len(sq))))
            tail.append(dict(target=target, unit=unit, subset=subset, method=method, n=len(error),
                             exact_zero_errors=int((error == 0).sum()), mae=error.mean(),
                             median=np.median(error), p95=np.quantile(error, .95),
                             p99=np.quantile(error, .99), maximum=error.max(),
                             rmse=np.sqrt(sq.mean()), top_one_percent_n=top,
                             top_one_percent_sse_share=sq[-top:].sum() / sq.sum() if sq.sum() else np.nan))
    for seg, group in p.groupby("segment_id"):
        row = dict(target=target, unit=unit, segment_id=seg, n=len(group))
        for method, col in methods.items():
            error = group[col] - group.y_true
            row.update({f"{method}_mae": error.abs().mean(),
                        f"{method}_rmse": np.sqrt(error.pow(2).mean())})
        segments.append(row)

# Exploratory contemporaneous pressure–flow response at the forecast origin.
# Power exclusively defines the state labels. No classifier or fitted threshold is used.
states = ["electrolyzer_active", "multiple_active"]
labels = ["Electrolyzer only", "Multiple active"]
for target, unit in zip(targets[:3], units[:3]):
    origin = lag[0][target]
    medians = []
    for regime in states:
        eligible = test & history & state.eq(regime)
        values = origin[eligible]
        q = values.quantile([.05, .25, .5, .75, .95])
        medians.append(q.loc[.5])
        distributions.append(dict(target=target, unit=unit, state=regime, n=len(values),
                                  segments=segment[eligible].nunique(), min=values.min(),
                                  p05=q.loc[.05], p25=q.loc[.25], median=q.loc[.5],
                                  p75=q.loc[.75], p95=q.loc[.95], max=values.max()))

availability = pd.DataFrame(availability)
results = pd.DataFrame(rows)
tail = pd.DataFrame(tail)
segments = pd.DataFrame(segments)
distributions = pd.DataFrame(distributions)
for frame, filename in [
    (availability, "TABLE_1_VALIDITY.csv"), (results, "TABLE_2_HELD_OUT.csv"),
    (schema, "CHANNEL_SCHEMA.csv"), (tail, "ERROR_TAILS.csv"),
    (segments, "SEGMENT_ERRORS.csv"), (distributions, "STATE_PRESSURE_FLOW.csv"),
]:
    frame.to_csv(out / filename, index=False, lineterminator="\n")
print("Verified source, segmentation, role/lag masks, prediction-to-source alignment, and 40 metric rows")
print(availability.to_string(index=False))

BG, NAVY, TEAL, BLUE, SLATE, RED, GRID, DARK = (
    "#F4F4E9", "#10263E", "#007F86", "#356CB1", "#64748B", "#A33F43", "#D9DFDE", "#1F2933"
)
plt.rcParams.update({
    "font.family": ["DejaVu Sans"], "font.size": 10, "svg.fonttype": "none",
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "axes.labelcolor": DARK, "axes.edgecolor": SLATE, "text.color": DARK,
    "axes.spines.top": False, "axes.spines.right": False, "grid.color": GRID,
})
figure_files = []

def canvas(title, subtitle):
    fig = plt.figure(figsize=(12.8, 7.2))
    fig.text(.065, .94, title, size=21, weight="bold", color=NAVY)
    fig.text(.065, .892, subtitle, size=10.5, color=SLATE)
    return fig

def panel(ax, title):
    ax.set_title(title, loc="left", color=NAVY, weight="bold", pad=10)

def save(fig, slug, caption):
    fig.text(.065, .045, caption, size=9.2, color=NAVY, linespacing=1.5)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for axis in fig.axes:
        bounds = axis.get_tightbbox(renderer)
        if bounds is not None:
            assert bounds.x0 >= 0 and bounds.x1 <= fig.bbox.width, slug
    png = out / f"{slug}.png"
    svg = png.with_suffix(".svg")
    fig.savefig(png, dpi=400)
    fig.savefig(svg, metadata={"Date": None})
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n",
                   encoding="utf-8")
    plt.close(fig)
    figure_files.append(png)

def diagram(fig):
    ax = fig.add_axes([.06, .14, .89, .68])
    ax.set(xlim=(0, 100), ylim=(0, 100))
    ax.axis("off")
    return ax

def box(ax, x, y, w, h, title, body="", color=NAVY):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=.25,rounding_size=1",
                               facecolor="#FAFAF3", edgecolor=color, linewidth=1.2))
    ax.text(x+w/2, y+h*(.64 if body else .5), title, ha="center", va="center",
            fontsize=11, weight="bold", color=color)
    if body:
        ax.text(x+w/2, y+h*.28, body, ha="center", va="center", fontsize=9, linespacing=1.4)

def arrow(ax, x, y, u, v, color=NAVY, style="-"):
    ax.annotate("", (u, v), xytext=(x, y),
                arrowprops=dict(arrowstyle="->", color=color, linewidth=1.5, linestyle=style))

fig = canvas("HY2RES pilot-system measurements", "Conceptual topology from the publisher’s equipment description")
ax = diagram(fig)
for x, title, body in [(1, "Electrolyzer", "Power [W]"), (21, "Buffer", "Pressure [bar]"),
                       (41, "Compressor", "Power [W]"), (61, "High-pressure tank", "Pressure [bar]"),
                       (81, "Fuel cell", "Pressure [bar] · power [W]")]:
    box(ax, x, 43, 18, 18, title, body)
for x in (19, 39, 59, 79):
    arrow(ax, x, 52, x+2, 52, TEAL)
box(ax, 1, 76, 18, 13, "Photovoltaics")
arrow(ax, 10, 76, 10, 61, BLUE, "--")
ax.text(11.4, 68, "Electrical supply", color=BLUE, va="center")
ax.plot([30, 30, 90], [43, 21, 21], color=TEAL, linewidth=1.5)
arrow(ax, 90, 21, 90, 43, TEAL)
ax.text(60, 16, "Alternative H₂ supply from buffer", ha="center", color=TEAL)
ax.text(20, 37, "H₂ production [NL/h]", ha="center", color=TEAL)
ax.text(90, 69, "H₂ consumption [NL/h]", ha="center", color=TEAL)
for x in (30, 70, 94):
    ax.scatter(x, 60, s=160, facecolor=BG, edgecolor=NAVY, zorder=3)
    ax.text(x, 60, "P", ha="center", va="center", fontsize=8, zorder=4)
save(fig, "FIG_01_MEASUREMENT_ARCHITECTURE",
     "Conceptual equipment relationships and recorded variables (Zenodo 15166733). P denotes a parameter measured on the equipment.\nExact instrument positions, piping geometry, and event locations are outside the source record.")

fig = canvas("Causal preparation and reference validity", "Source timing, verified lags, and common scoring support")
grid = fig.add_gridspec(2, 2, left=.145, right=.965, bottom=.18, top=.82, hspace=.65, wspace=.36)
ax = fig.add_subplot(grid[0, :])
panel(ax, "(a) Recording intervals and timestamp exceptions")
for y, selector, color, marker in [(1, markers.eq("OPEN"), TEAL, "^"), (1, markers.eq("CLOSE"), NAVY, "v"),
                                  (0, step.ne(5) & step.gt(0), SLATE, "|"), (-1, step.eq(0), RED, "o")]:
    ax.scatter(time[selector], np.full(selector.sum(), y), marker=marker, s=16, color=color)
registry = pd.read_csv(archive / "segment_registry.csv")
start, end = (mdates.date2num(pd.to_datetime(registry[key])) for key in ("start_timestamp", "end_timestamp"))
ax.hlines(np.full(len(start), 2), start, end, color=TEAL, linewidth=1.6)
ax.set(yticks=[-1,0,1,2], yticklabels=["Duplicate", "Irregular", "OPEN ▲ / CLOSE ▼", "5 s continuity"], ylim=(-1.7,2.7))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
ax.grid(axis="x")
ax = fig.add_subplot(grid[1, 0])
panel(ax, "(b) One-step causal window")
ax.axvspan(0, 5.5, color=RED, alpha=.07)
ax.axvline(0, color=TEAL, linestyle=":")
ax.hlines(0, -10, 5, color=SLATE)
ax.scatter([-10,-5,0], [0]*3, color=TEAL, s=50)
ax.scatter([5], [0], color=RED, marker="D", s=45)
ax.set(xlim=(-12,7), ylim=(-.6,.8), xticks=[-10,-5,0,5], yticks=[], xlabel="Seconds relative to forecast origin")
ax.text(-6, .32, "Measured context", ha="center", color=TEAL)
ax.text(4.8, .32, "Future target", ha="center", color=RED)
ax = fig.add_subplot(grid[1, 1])
panel(ax, "(c) Test eligibility · electrolyzer flow")
record = availability.set_index("target").loc["h2_flow"]
values = [record.test_rows, record.observed_targets, record.persistence_scorable, record.common_scored]
ax.barh(range(4), values, color=[SLATE, NAVY, BLUE, TEAL], height=.56)
ax.set(yticks=range(4), yticklabels=["Source", "Finite target", "Persistence scorable", "Shared and scored"],
       xlim=(0,51500), xlabel="Rows")
ax.invert_yaxis()
for y, count in enumerate(values):
    ax.text(count+650, y, f"{count:,}", va="center", fontsize=9)
save(fig, "FIG_02_CAUSAL_VALIDITY",
     "300,768 source rows; 2,793 segments; 21 duplicate intervals. Test flow: one missing target and "
     f"{record.insufficient_contiguous_history:,} rows lacking contiguous history.\n"
     f"A further {record.nonfinite_lagged_predictor_with_history:,} had a nonfinite lagged input despite sufficient contiguous history. "
     "Model-specific availability is reconstructed from source measurements.")

fig = canvas("Held-out pressure–flow references", "Measured series and archived forecasts on a fixed, continuous test interval")
axes = fig.subplots(3, 2, gridspec_kw={"width_ratios": [2.1,1]})
fig.subplots_adjust(left=.095, right=.965, bottom=.17, top=.81, hspace=.58, wspace=.34)
interval = pred[pred.segment_id.eq(2382)].copy()
interval["timestamp"] = pd.to_datetime(interval.timestamp)
for i, (target, name, unit) in enumerate(zip(targets[:3], names[:3], units[:3])):
    g = interval[interval.target.eq(target)]
    assert g.timestamp.diff().dropna().dt.total_seconds().eq(5).all()
    left, right = axes[i]
    panel(left, f"({chr(97+i)}) {name} [{unit}]")
    for col, label, color, style in [("y_true","Measured",NAVY,"-"),
                                     ("persistence_prediction","Persistence",BLUE,"--"),
                                     ("contextual_prediction","Ridge",TEAL,"-.")]:
        left.plot(g.timestamp, g[col], color=color, linestyle=style, label=label, linewidth=1.3)
        if col != "y_true":
            right.plot(g.timestamp, g[col]-g.y_true, color=color, linestyle=style, linewidth=1.15)
    panel(right, f"Forecast − measured [{unit}]")
    right.axhline(0, color=SLATE, linewidth=.8)
    for axis in (left,right):
        axis.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        axis.grid(axis="y")
axes[0,0].legend(loc="upper left", ncols=3, frameon=False, fontsize=8)
for axis in axes[-1]:
    axis.set_xlabel("Source time on 12 April 2024")
save(fig, "FIG_03_HELD_OUT_TRACES",
     "Segment 2382, 12:36:44–12:46:59 on 12 April 2024 (timezone unspecified). Original interval selected by chronology and segment length.\n"
     "Forecast horizon: next verified 5 s sample. The displayed rows show positive measured production flow.")

fig = canvas("Held-out MAE and RMSE", "Paired comparison on 43,168 rows and 409 segments per target")
axes = fig.subplots(1,3)
fig.subplots_adjust(left=.075, right=.965, top=.79, bottom=.22, wspace=.33)
for i, (ax, target, name, unit) in enumerate(zip(axes, targets[:3], names[:3], units[:3])):
    row = results[results.target.eq(target) & results.state.eq("overall")].iloc[0]
    panel(ax, f"({chr(97+i)}) {name}")
    peak = max(row.persistence_rmse, row.contextual_ridge_rmse)
    for x, metric in enumerate(("mae","rmse")):
        for offset, method, color, marker, label in [
            (-.18,"persistence",BLUE,"o","Persistence"), (.18,"contextual_ridge",TEAL,"s","Ridge")
        ]:
            value = row[f"{method}_{metric}"]
            ax.scatter(x+offset, value, color=color, marker=marker, s=48, label=label if not x else None)
            ax.annotate(f"{value:.5g}", (x+offset,value), (0, 10),
                        textcoords="offset points", ha="center", fontsize=8, color=color)
        change = row[f"{metric}_change_pct"]
        ax.text(x, peak*1.22, f"{change:+.1f}%", ha="center",
                color=RED if change > 0 else TEAL, weight="bold")
    ax.set(xlim=(-.45,1.45), ylim=(-peak*.10,peak*1.38), xticks=[0,1],
           xticklabels=["MAE","RMSE"], ylabel=unit)
    ax.axhline(0, color=SLATE, linewidth=.7)
    ax.grid(axis="y")
handles, legend = axes[0].get_legend_handles_labels()
fig.legend(handles, legend, loc="lower center", bbox_to_anchor=(.5,.13), ncols=2, frameon=False)
save(fig, "FIG_04_ERROR_COMPARISON",
     "Percentages give ridge relative to persistence. Panels use separate physical scales. Both fuel-cell targets were constant zero;\n"
     "their scores remain in Table 2. The comparison is descriptive for the frozen held-out record.")

fig = canvas("Operating-state dependence", "Power-state labels use recorded equipment power at the forecast origin")
axes = fig.subplots(1,3, gridspec_kw={"width_ratios":[1.05,1,1]})
fig.subplots_adjust(left=.145,right=.96,top=.79,bottom=.24,wspace=.44)
strata = results[results.target.eq("h2_flow")].set_index("state").loc[[*states,"unknown"]]
loc = np.arange(3)
panel(axes[0], "(a) Scored support")
axes[0].barh(loc, strata.scored, color=[TEAL,SLATE,SLATE], height=.48)
axes[0].set(yticks=loc, yticklabels=labels+["Unknown"], xlim=(0,59000), xlabel="Rows")
axes[0].invert_yaxis()
for y, row in enumerate(strata.itertuples()):
    axes[0].text(1200 if y else 3400, y, f"{row.scored:,} / {row.segments} segments",
                 va="center", color="white" if y==0 else NAVY, fontsize=8.5)
for ax, metric, title in zip(axes[1:], ["mae","rmse"], ["(b) Flow MAE","(c) Flow RMSE"]):
    panel(ax, title)
    for shift, method, color, marker, label in [(-.12,"persistence",BLUE,"o","Persistence"),
                                                  (.12,"contextual_ridge",TEAL,"s","Ridge")]:
        values = strata[f"{method}_{metric}"].iloc[:2]
        ax.scatter(np.arange(2)+shift, values, color=color, marker=marker, s=55, label=label)
        for x,value in enumerate(values):
            ax.annotate(f"{value:.3f}",(x+shift,value),(0,9),textcoords="offset points",
                        ha="center",color=RED if x==1 and shift>0 else color,fontsize=8.5)
    ax.set(xlim=(-.41,1.41), ylim=(0,1.53*strata[[f"persistence_{metric}",f"contextual_ridge_{metric}"]].max().max()),
           xticks=[0,1], xticklabels=["Electrolyzer\nonly","Multiple\nactive"], ylabel="NL/h")
    ax.grid(axis="y")
axes[1].legend(loc="upper left", frameon=False, fontsize=8)
save(fig, "FIG_05_OPERATING_STATE",
     "Positive lagged equipment power defines the strata. Unknown power state yielded zero eligible rows. Segment counts can overlap across states.\n"
     "Multiple-active flow RMSE rose 4.80× with ridge; the 801 rows occupy 12 segments from one pilot record.")

fig = canvas("What the HY2RES evidence supports", "The three-layer H₂-PRISM framework applied to Study C")
ax = diagram(fig)
for x, title, body in [
    (1,"I · Causal signal representation","Checksum-matched measurements\nVerified 5 s lags and segments\nExplicit missingness and eligibility"),
    (35,"II · Diagnostic evidence assessment","Persistence and ridge references\nMixed MAE and RMSE results\nState dependence and overlap"),
    (69,"III · Qualified diagnostic decision","Formal D(Y): indeterminate\nFault diagnosis: not established\nLeak localization: not established"),
]:
    box(ax,x,46,30,33,title,body,SLATE if x==69 else NAVY)
arrow(ax,31,62,35,62,TEAL)
ax.plot([65,69],[62,62],color=SLATE,linestyle=":")
ax.text(67,67,"×",ha="center",color=RED,fontsize=16)
ax.text(50,25,"Observed reference errors describe forecast behavior within this record.",
        ha="center",size=13,weight="bold",color=NAVY)
ax.text(50,14,"Mechanism-specific conclusions require qualified hypothesis predictions and observation bounds.",
        ha="center",size=10.5,color=SLATE)
save(fig, "FIG_06_EVIDENCE_QUALIFICATION",
     "Operational state comparisons are exploratory. The source provides neither qualified incident/location truth nor certified hypothesis bounds.")

fig = canvas("Pressure–flow overlap across power states", "Exploratory comparisons at the forecast origin · no model fitting")
axes = fig.subplots(1,3)
fig.subplots_adjust(left=.155,right=.965,top=.78,bottom=.24,wspace=.53)
for i,(ax,target,name,unit) in enumerate(zip(axes,targets[:3],names[:3],units[:3])):
    panel(ax,f"({chr(97+i)}) {name}")
    for y,regime in enumerate(states):
        r = distributions[distributions.target.eq(target)&distributions.state.eq(regime)].iloc[0]
        color = BLUE if y==0 else TEAL
        ax.hlines(y,r["min"],r["max"],color=color,linestyle=":",linewidth=1)
        ax.hlines(y,r.p05,r.p95,color=color,linewidth=2)
        ax.hlines(y,r.p25,r.p75,color=color,linewidth=7)
        ax.scatter(r["median"],y,marker="o" if y==0 else "s",color=BG,edgecolor=color,s=38,zorder=3)
    ax.set(yticks=[0,1],yticklabels=labels if i==0 else ["",""],ylim=(1.55,-.55),xlabel=unit)
    ax.grid(axis="x")
save(fig, "FIG_07_EXPLORATORY_STATE_OVERLAP",
     "Markers show medians, thick lines the interquartile range, thin lines the central 90%, and dotted lines the observed range.\n"
     "Lagged powers define labels only. Pressure and flow are the compared observations. Rows are serially dependent and state supports are unequal.")

# Downsample only the contact-sheet thumbnails. Individual PNGs retain the full 400 dpi.
sheet = Image.new("RGB", (3840, 4320), BG)
for i, file in enumerate(figure_files):
    with Image.open(file) as image:
        sheet.paste(image.resize((1920,1080), Image.Resampling.LANCZOS), ((i%2)*1920,(i//2)*1080))
sheet.save(out / "CONTACT_SHEET.png", dpi=(400,400))
print(f"Exported {len(figure_files)} PNG/SVG pairs and contact sheet")
