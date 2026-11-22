#!/usr/bin/env python3
"""
Physics-grounded assessment of window representations on the CLEAN and NOISY signals (EXPLORATORY_DIAGNOSTIC).
No classifier is fitted, no predictions are used, nothing is selected: every registered representation family is
measured with the same fixed metrics, and the numbers describe signal physics only.

Families (src/h2prism/feature_representations.py; W = 60 s windows, 30 s stride, baseline B = 1800 s):
  ABS    absolute window mean of each position-matched canonical channel
  GRAD   pressure difference across a pipe between position-matched sensors at its two ends (diagram registry)
  CBD    causal baseline deviation (window mean - median of the preceding B s)
  CRC    causal robust change (CBD / (1.4826 MAD of the preceding B s)). On CLEAN signals the baseline MAD is ~0
         (noise-free), so CRC is degenerate there; CRC is therefore assessed on the NOISY realization only and is
         already in robust-noise units (noise_sd := 1 by construction).
  SLOPE  within-window least-squares slope
Metrics (all in units of the representation's own noise SD = SD over NORMAL windows of r(noisy) - r(clean)):
  cross_model_normal_offset   max pairwise |median steady r| between the three models' NORMAL runs (steady 2000-19000 s)
  normal_false_alarm_share    share of steady NORMAL windows (noisy) with |r| > 3 noise SD   (CBD/CRC/SLOPE only)
  weak_state_diff             low-visibility leak runs: median |r(run) - r(own NORMAL)| late after onset (clean)
  weak_onset_change           max |r(t) - r(pre-onset)| (ABS/GRAD/SLOPE) or max |r| (CBD/CRC) within 600 s of onset
  weak_change_persistence_s   time after onset while |r| stays > 3 noise SD (CBD/CRC)
  strong_state_diff           visible leak runs: median |r(run) - r(own NORMAL)| late after onset (clean)
  pattern_cosine_across_models  for each event stem simulated in all three models: cosine similarity of the
                                noise-normalised onset-change vector (ABS, canonical channels) between models
Writes 03_results/diagnostics/feature_representation/{PIPE_SENSOR_PAIRS.csv, REPRESENTATION_METRICS.csv,
REPRESENTATION_SUMMARY.csv, PATTERN_TRANSFER.csv, NOISE_AUTOCORRELATION.csv, SUMMARY.json}.
Usage: python tools/experiments/assess_feature_representations.py
"""

from __future__ import annotations

import json
import warnings
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools" / "dataset"))

from h2prism import feature_representations as fr  # noqa: E402
from h2prism.independence import ancestor  # noqa: E402

import trace_slx_sensors as tss  # noqa: E402

OUT = REPO / "03_results" / "diagnostics" / "feature_representation"
MAN = REPO / "06_audit_preparation" / "protocol2" / "CANDIDATE_MANIFEST_V03.csv"
PMAP = REPO / "06_audit_preparation" / "protocol2" / "CANDIDATE_SENSOR_POSITION_MAP_V01.csv"
OBS = REPO / "03_results" / "diagnostics" / "arm_h_failures" / "EVENT_OBSERVABILITY.csv"
RAW = REPO / "data" / "raw"
MODEL_TOPO = {"center": "Center", "down": "Downstream", "up": "Upstream"}
STEADY = (2000, 19000)
B = fr.B_DEFAULT


def pipe_pairs(pm: pd.DataFrame) -> pd.DataFrame:
    """Pipes whose two ends both carry a position-matched pressure sensor, identical (pipe SID, sensor blocks) in all
    three anomalous source models."""
    canon = dict(zip(pm.canonical_block_sid.astype(int), pm.canonical_channel))
    per_model = {}
    for (kind, topo), rel in tss.MODELS.items():
        if kind != "anomalous":
            continue
        m = tss.Model(tss.SIM / rel)
        sens_on_net = {}
        for sid, b in m.blocks.items():
            if b["cls"] == "pressure_temperature_sensor" and int(sid) in canon:
                n = m.net_of.get(f"{sid}#lconn:1")
                if n:
                    sens_on_net.setdefault(n, []).append(canon[int(sid)])
        pairs = set()
        for sid, b in m.blocks.items():
            if b["cls"] != "pipe":
                continue
            na, nb = m.net_of.get(f"{sid}#lconn:1"), m.net_of.get(f"{sid}#rconn:1")
            for a in sens_on_net.get(na, []):
                for c in sens_on_net.get(nb, []):
                    pairs.add((sid, float(b["params"].get("length", "nan")), a, c))
        per_model[topo] = pairs
    common = set.intersection(*per_model.values())
    return pd.DataFrame(sorted(common), columns=["pipe_sid", "length_m", "sensor_A_end", "sensor_B_end"])


def series_for(run_file: str, topo: str, src: dict, chans, pairs) -> dict:
    df = pd.read_parquet(RAW / run_file)
    out = {}
    for c in chans:
        out[("ABS", c)] = df[src[(c, topo)]]
    for r in pairs.itertuples():
        out[("GRAD", f"{r.sensor_A_end}-{r.sensor_B_end}")] = df[src[(r.sensor_A_end, topo)]] - df[src[(r.sensor_B_end, topo)]]
    return out


def reps(series: dict, starts) -> dict:
    out = {}
    for (fam, name), x in series.items():
        out[(fam, name)] = fr.absolute_mean(x, starts)
        if fam == "ABS":
            out[("CBD", name)] = fr.causal_baseline_deviation(x, starts)
            out[("CRC", name)] = fr.causal_robust_change(x, starts)
            out[("SLOPE", name)] = fr.window_slope(x, starts)
    return out


def main() -> int:
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    man = pd.read_csv(MAN)
    e = man[man.eligible_primary.astype(bool)]
    pm = pd.read_csv(PMAP)
    src = {(r.canonical_channel, r.topology): r.source_channel for r in pm.itertuples()}
    chans = list(dict.fromkeys(pm.canonical_channel))
    pairs = pipe_pairs(pm)
    obs = pd.read_csv(OBS)
    weak = set(obs[obs.event_median_abs_z_top_channel < 2].Scenario_ID)
    OUT.mkdir(parents=True, exist_ok=True)
    pairs.to_csv(OUT / "PIPE_SENSOR_PAIRS.csv", index=False, lineterminator="\n")

    normal = e[e.label_mapped == "NORMAL"].set_index("topology_source_model")
    starts = None
    R = {}   # (scenario, realization) -> {(fam, name): array}
    for t, r in normal.iterrows():
        for real, col in (("clean", "file_clean"), ("noise_added", "file_noise_added")):
            s = series_for(getattr(r, col), t, src, chans, pairs)
            starts = fr.window_starts(next(iter(s.values())).index) if starts is None else starts
            R[(r.Scenario_ID, real)] = reps(s, starts)
    keys = list(R[(normal.iloc[0].Scenario_ID, "clean")].keys())
    steady = (starts >= STEADY[0]) & (starts < STEADY[1])
    noise = {k: (1.0 if k[0] == "CRC" else
                 float(np.nanmedian([np.nanstd(R[(r.Scenario_ID, "noise_added")][k] - R[(r.Scenario_ID, "clean")][k])
                                     for _, r in normal.iterrows()]))) for k in keys}

    def real_of(k):  # CRC is only meaningful on noisy data
        return "noise_added" if k[0] == "CRC" else "clean"

    rows = []
    for k in keys:
        ns = noise[k] if noise[k] > 0 else np.nan
        med = {t: np.nanmedian(R[(r.Scenario_ID, real_of(k))][k][steady]) for t, r in normal.iterrows()}
        off = max(abs(med[a] - med[b]) for a, b in combinations(med, 2)) / ns
        fa = (float(np.nanmean([np.mean(np.abs(R[(r.Scenario_ID, "noise_added")][k][steady]) > 3 * ns)
                                for _, r in normal.iterrows()])) if k[0] in ("CBD", "CRC", "SLOPE") else np.nan)
        rows.append({"family": k[0], "feature": k[1], "noise_sd": noise[k], "cross_model_normal_offset": off,
                     "normal_false_alarm_share": fa})
    M = pd.DataFrame(rows).set_index(["family", "feature"])

    # event runs (clean) against their own model's NORMAL run
    ev_rows, onset_vec = [], {}
    for r in e[e.label_mapped == "LEAK"].itertuples():
        t = r.topology_source_model
        df = pd.read_parquet(RAW / r.file_clean)
        t0 = float(df.index[df.label_anomaly == 1][0])
        rr = reps(series_for(r.file_clean, t, src, chans, pairs), starts)
        rn = reps(series_for(r.file_noise_added, t, src, chans, pairs), starts)
        for k in keys:
            if k[0] == "CRC":
                rr[k] = rn[k]
        nr = {k: R[(normal.loc[t].Scenario_ID, real_of(k))][k] for k in keys}
        late = (starts >= max(t0 + B + 600, STEADY[0])) & (starts < STEADY[1])
        near = (starts >= t0) & (starts < t0 + 600)
        pre_i = np.searchsorted(starts, t0 - 60) - 1
        vec = []
        for k in keys:
            ns = noise[k] if noise[k] > 0 else np.nan
            a = rr[k]
            state = float(np.nanmedian(np.abs(a[late] - nr[k][late])) / ns) if late.any() else np.nan
            if k[0] in ("CBD", "CRC"):
                change = float(np.nanmax(np.abs(a[near])) / ns) if near.any() else np.nan
                above = np.abs(a) > 3 * ns
                idx = np.flatnonzero(starts >= t0)
                persist = 0.0
                for i in idx:
                    if not above[i]:
                        break
                    persist = starts[i] - t0 + 60
            else:
                change = float(np.nanmax(np.abs(a[near] - a[pre_i])) / ns) if (near.any() and pre_i >= 0) else np.nan
                persist = np.nan
            if k[0] == "ABS" and k[1].startswith("PS"):
                vec.append((a[near].mean() - a[pre_i]) / ns if (near.any() and pre_i >= 0) else np.nan)
            ev_rows.append({"Scenario_ID": r.Scenario_ID, "independence_group": r.independence_group,
                            "low_visibility": r.Scenario_ID in weak, "family": k[0], "feature": k[1],
                            "state_diff": state, "onset_change": change, "persistence_s": persist})
        onset_vec[(ancestor(r.Scenario_ID), t)] = np.array(vec, float)
    EV = pd.DataFrame(ev_rows)

    agg = []
    for (fam, feat), g in EV.groupby(["family", "feature"]):
        w, s = g[g.low_visibility], g[~g.low_visibility]
        agg.append({"family": fam, "feature": feat, "weak_state_diff": w.state_diff.median(),
                    "weak_onset_change": w.onset_change.median(), "weak_change_persistence_s": w.persistence_s.median(),
                    "strong_state_diff": s.state_diff.median(), "strong_onset_change": s.onset_change.median()})
    A = M.join(pd.DataFrame(agg).set_index(["family", "feature"])).reset_index()
    A["offset_over_weak_state_diff"] = A.cross_model_normal_offset / A.weak_state_diff
    A.assign(evidence_status="EXPLORATORY_DIAGNOSTIC").to_csv(OUT / "REPRESENTATION_METRICS.csv", index=False,
                                                              lineterminator="\n", float_format="%.6g")
    S = A.groupby("family").agg(n_features=("feature", "size"), median_noise_sd=("noise_sd", "median"),
                                median_cross_model_offset=("cross_model_normal_offset", "median"),
                                median_normal_false_alarm=("normal_false_alarm_share", "median"),
                                median_weak_state_diff=("weak_state_diff", "median"),
                                median_weak_onset_change=("weak_onset_change", "median"),
                                median_weak_persistence_s=("weak_change_persistence_s", "median"),
                                median_strong_state_diff=("strong_state_diff", "median"),
                                median_offset_over_weak_state=("offset_over_weak_state_diff", "median")).reset_index()
    S.assign(evidence_status="EXPLORATORY_DIAGNOSTIC").to_csv(OUT / "REPRESENTATION_SUMMARY.csv", index=False,
                                                              lineterminator="\n", float_format="%.6g")

    pt = []
    for stem in sorted({a for a, _ in onset_vec}):
        vs = {t: v for (a, t), v in onset_vec.items() if a == stem}
        if len(vs) < 2:
            continue
        for a, b in combinations(sorted(vs), 2):
            x, y = vs[a], vs[b]
            ok = np.isfinite(x) & np.isfinite(y)
            cos = float(x[ok] @ y[ok] / (np.linalg.norm(x[ok]) * np.linalg.norm(y[ok]))) if ok.any() and np.linalg.norm(x[ok]) > 0 and np.linalg.norm(y[ok]) > 0 else np.nan
            pt.append({"stem": stem, "model_a": a, "model_b": b, "cosine_onset_change_pattern": cos,
                       "norm_a": float(np.linalg.norm(x[ok])), "norm_b": float(np.linalg.norm(y[ok]))})
    PT = pd.DataFrame(pt).assign(evidence_status="EXPLORATORY_DIAGNOSTIC")
    PT.to_csv(OUT / "PATTERN_TRANSFER.csv", index=False, lineterminator="\n", float_format="%.6g")

    # noise autocorrelation (white-noise assumption behind window-sigma = sigma / sqrt(60))
    ac = []
    for t, r in normal.iterrows():
        c, n = pd.read_parquet(RAW / r.file_clean), pd.read_parquet(RAW / r.file_noise_added)
        for ch in chans:
            z = (n[src[(ch, t)]] - c[src[(ch, t)]]).to_numpy(float)
            z = z - z.mean()
            rho = [float(np.corrcoef(z[:-k], z[k:])[0, 1]) for k in range(1, 60)]
            ac.append({"model": t, "channel": ch, "noise_sd": float(z.std()), "rho_1": rho[0], "rho_2": rho[1],
                       "rho_30": rho[29], "max_abs_rho_1_59": float(np.max(np.abs(rho))),
                       "variance_inflation_60s_mean": 1 + 2 * sum((1 - k / 60) * rho[k - 1] for k in range(1, 60))})
    AC = pd.DataFrame(ac).assign(evidence_status="EXPLORATORY_DIAGNOSTIC")
    AC.to_csv(OUT / "NOISE_AUTOCORRELATION.csv", index=False, lineterminator="\n", float_format="%.6g")
    (OUT / "SUMMARY.json").write_text(json.dumps({
        "evidence_status": "EXPLORATORY_DIAGNOSTIC", "model_fitted": False, "predictions_used": False,
        "window_s": fr.W_DEFAULT, "stride_s": fr.STRIDE_DEFAULT, "baseline_s": B, "steady_period_s": STEADY,
        "n_pipe_pairs": int(len(pairs)), "low_visibility_runs": sorted(weak),
        "noise_white": bool(AC.max_abs_rho_1_59.max() < 0.05),
        "variance_inflation_range": [float(AC.variance_inflation_60s_mean.min()), float(AC.variance_inflation_60s_mean.max())]},
        indent=2), encoding="utf-8")
    pd.set_option("display.width", 250)
    print(pairs.to_string(index=False))
    print(S.round(3).to_string(index=False))
    print(PT.groupby("stem").cosine_onset_change_pattern.agg(["min", "median"]).round(3).to_string())
    print(AC[["max_abs_rho_1_59", "variance_inflation_60s_mean"]].describe().round(3))
    return 0


if __name__ == "__main__":
    sys.exit(main())
