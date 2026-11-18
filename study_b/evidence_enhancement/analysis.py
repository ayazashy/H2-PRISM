"""Observation-level error analysis of the replayed frozen Study B benchmark.

Reads only ``replayed_predictions.csv.gz`` and ``replay_manifest.json`` written by
``replay.py`` (which refuses to write predictions unless the frozen gate passed).
All bins are fixed from measurement increments before any error statistic is computed.
No model is fitted; nothing is selected on outcomes.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

CHANNELS = ("P-2", "MFC-3")
UNIT = {"P-2": "barg", "MFC-3": "ln/min"}
MODELS = ("persistence", "ridge")
TAILS = (0.001, 0.01, 0.05)
QUANTILES = (0.5, 0.9, 0.95, 0.99)


def observed_increment(values: np.ndarray) -> float:
    """Smallest positive difference between distinct recorded values (rounded to 1e-6)."""
    u = np.unique(np.round(values, 6))
    d = np.diff(u)
    return float(np.round(d[d > 1e-9].min(), 6))


def change_bins(increment: float):
    """Predeclared decades of the observed increment: 0 | 1 | (1,10] | (10,100] | >100 increments."""
    edges = [(0.0, 0.0, "no change"), (increment, increment, "1 increment"),
             (2 * increment, 10 * increment, "2–10 increments"),
             (11 * increment, 100 * increment, "11–100 increments"),
             (101 * increment, np.inf, ">100 increments")]
    return edges


def assign_bin(steps: np.ndarray):
    """steps = |Δy| / increment, rounded to the nearest integer (values are on the recording grid)."""
    k = np.rint(steps)
    out = np.full(k.shape, ">100 increments", dtype=object)
    out[k <= 100] = "11–100 increments"
    out[k <= 10] = "2–10 increments"
    out[k == 1] = "1 increment"
    out[k == 0] = "no change"
    return out


def tail_share(sq: np.ndarray, fraction: float):
    """Share of total squared error carried by the ceil(fraction·n) largest squared errors."""
    s = np.sort(sq)[::-1]
    k = int(np.ceil(fraction * len(s)))
    return k, float(s[:k].sum() / s.sum()) if s.sum() > 0 else np.nan


def representative_windows(notes: dict) -> dict:
    """Source-declared 'Representative Cycle' start/end clock times from the workbook protocol block."""
    out = {}
    for run, lines in notes.items():
        text = " ".join(lines)
        s = re.search(r"Start:\s*(\d{2}:\d{2}:\d{2})", text)
        e = re.search(r"End:\s*(\d{2}:\d{2}:\d{2})", text)
        out[int(run)] = (s.group(1) if s else None, e.group(1) if e else None)
    return out


def analyse(replay_dir: Path, out: Path):
    out.mkdir(parents=True, exist_ok=False)
    d = pd.read_csv(replay_dir / "replayed_predictions.csv.gz")
    meta = json.loads((replay_dir / "replay_manifest.json").read_text(encoding="utf-8"))
    if not meta.get("gate_passed"):
        raise SystemExit("replay gate not passed: analysis blocked")
    d["e_persistence"] = d.y_true - d.persistence
    d["e_ridge"] = d.y_true - d.ridge
    d["dy"] = d.y_true - d.y_prev

    # 1. Resolution (fixed before error statistics).
    res = {}
    for ch in CHANNELS:
        g = d[d.channel == ch]
        inc = observed_increment(np.concatenate([g.y_true.values, g.y_prev.values]))
        res[ch] = dict(channel=ch, unit=UNIT[ch], observed_increment=inc,
                       distinct_values=int(len(np.unique(np.round(np.r_[g.y_true, g.y_prev], 6)))),
                       on_grid_fraction=float(np.mean(np.isclose(np.rint(g.y_true / inc) * inc, g.y_true, atol=1e-6))),
                       zero_value_fraction=float((g.y_true == 0).mean()),
                       zero_change_fraction=float((g.dy == 0).mean()))
    bins_declared = {ch: [(a, b if np.isfinite(b) else "inf", lab) for a, b, lab in change_bins(res[ch]["observed_increment"])]
                     for ch in CHANNELS}
    d["bin"] = ""
    for ch in CHANNELS:
        m = d.channel == ch
        d.loc[m, "bin"] = assign_bin(np.abs(d.loc[m, "dy"].values) / res[ch]["observed_increment"])

    # 2. Run-level metrics and squared-error accounting.
    runs = []
    for (run, ch), g in d.groupby(["run", "channel"]):
        row = dict(run=run, channel=ch, unit=UNIT[ch], n=len(g))
        for m in MODELS:
            e = g["e_" + m]
            row[f"{m}_mae"] = float(e.abs().mean())
            row[f"{m}_rmse"] = float(np.sqrt((e ** 2).mean()))
            row[f"{m}_sse"] = float((e ** 2).sum())
            row[f"{m}_exact_hits"] = float((e == 0).mean())
        row["delta_mae"] = row["ridge_mae"] - row["persistence_mae"]
        row["rel_delta_mae"] = row["delta_mae"] / row["persistence_mae"]
        row["delta_rmse"] = row["ridge_rmse"] - row["persistence_rmse"]
        row["rel_delta_rmse"] = row["delta_rmse"] / row["persistence_rmse"]
        row["delta_sse"] = row["ridge_sse"] - row["persistence_sse"]
        runs.append(row)
    runs = pd.DataFrame(runs)
    for ch in CHANNELS:
        m = runs.channel == ch
        for model in MODELS:
            runs.loc[m, f"{model}_sse_share"] = runs.loc[m, f"{model}_sse"] / runs.loc[m, f"{model}_sse"].sum()
        runs.loc[m, "delta_sse_share"] = runs.loc[m, "delta_sse"] / runs.loc[m, "delta_sse"].sum()

    # 3. Quantiles of absolute error (per run and pooled over the three runs).
    q = []
    for scope, frame in [("run", d)]:
        for (run, ch), g in list(frame.groupby(["run", "channel"])) + [((("all 3 runs"), ch), d[d.channel == ch])
                                                                        for ch in CHANNELS]:
            for m in MODELS:
                a = g["e_" + m].abs().values
                q.append(dict(run=run, channel=ch, unit=UNIT[ch], model=m, n=len(a), mean=float(a.mean()),
                              **{f"p{int(p * 100)}": float(np.quantile(a, p, method="inverted_cdf")) for p in QUANTILES},
                              max=float(a.max()), signed_mean=float(g["e_" + m].mean()),
                              zero_error_fraction=float((a == 0).mean())))
    q = pd.DataFrame(q)

    # 4. Tail concentration (each model ranked by its own squared errors).
    tails = []
    for (run, ch), g in list(d.groupby(["run", "channel"])) + [(("all 3 runs", ch), d[d.channel == ch]) for ch in CHANNELS]:
        for m in MODELS:
            sq = (g["e_" + m] ** 2).values
            for f in TAILS:
                k, share = tail_share(sq, f)
                tails.append(dict(run=run, channel=ch, unit=UNIT[ch], model=m, tail_fraction=f, tail_count=k,
                                  n=len(sq), total_sse=float(sq.sum()), tail_share=share))
    tails = pd.DataFrame(tails)
    # Paired attribution of the Ridge–persistence squared-error difference to the persistence tail.
    paired = []
    for ch in CHANNELS:
        g = d[d.channel == ch]
        dsse = (g.e_ridge ** 2 - g.e_persistence ** 2).values
        a = g.e_persistence.abs().values
        for f in TAILS:
            k = int(np.ceil(f * len(a)))
            top = np.argsort(-a, kind="stable")[:k]
            mask = np.zeros(len(a), bool)
            mask[top] = True
            paired.append(dict(channel=ch, unit=UNIT[ch] + "²", tail_fraction=f, tail_count=k,
                               delta_sse_total=float(dsse.sum()), delta_sse_in_tail=float(dsse[mask].sum()),
                               delta_sse_outside=float(dsse[~mask].sum())))
    paired = pd.DataFrame(paired)
    # Concentration curves for figures (fraction of rows vs cumulative share), pooled per channel.
    curves = []
    for ch in CHANNELS:
        g = d[d.channel == ch]
        for m in MODELS:
            s = np.sort((g["e_" + m] ** 2).values)[::-1]
            c = np.cumsum(s) / s.sum()
            idx = np.unique(np.r_[np.geomspace(1, len(s), 400).astype(int) - 1, len(s) - 1])
            curves += [dict(channel=ch, model=m, fraction=(i + 1) / len(s), cumulative_share=float(c[i])) for i in idx]
    curves = pd.DataFrame(curves)

    # 5. Error versus observed change (retrospective characterisation).
    ch_rows = []
    order = ["no change", "1 increment", "2–10 increments", "11–100 increments", ">100 increments"]
    for ch in CHANNELS:
        inc = res[ch]["observed_increment"]
        g = d[d.channel == ch]
        for scope, frame in [("all 3 runs", g)] + [(r, h) for r, h in g.groupby("run")]:
            for lab in order:
                h = frame[frame.bin == lab]
                lo, hi = {"no change": (0, 0), "1 increment": (inc, inc), "2–10 increments": (2 * inc, 10 * inc),
                          "11–100 increments": (11 * inc, 100 * inc), ">100 increments": (101 * inc, np.inf)}[lab]
                row = dict(run=scope, channel=ch, unit=UNIT[ch], bin=lab, abs_change_min=lo, abs_change_max=hi,
                           n=len(h), runs_supporting=int(h.run.nunique()) if len(h) else 0)
                for m in MODELS:
                    e = h["e_" + m]
                    row[f"{m}_mae"] = float(e.abs().mean()) if len(h) else np.nan
                    row[f"{m}_rmse"] = float(np.sqrt((e ** 2).mean())) if len(h) else np.nan
                    row[f"{m}_sse"] = float((e ** 2).sum()) if len(h) else 0.0
                row["delta_mae"] = row["ridge_mae"] - row["persistence_mae"]
                row["rel_delta_mae"] = row["delta_mae"] / row["persistence_mae"] if row["persistence_mae"] else np.nan
                row["delta_sse"] = row["ridge_sse"] - row["persistence_sse"]
                ch_rows.append(row)
    change = pd.DataFrame(ch_rows)

    # 6. Resolution-aware comparison.
    for ch in CHANNELS:
        g = d[d.channel == ch]
        inc = res[ch]["observed_increment"]
        for m in MODELS:
            e = g["e_" + m]
            res[ch][f"{m}_exact_match"] = float((e == 0).mean())
            res[ch][f"{m}_mae_increments"] = float(e.abs().mean() / inc)
            res[ch][f"{m}_rmse_increments"] = float(np.sqrt((e ** 2).mean()) / inc)
        res[ch]["ridge_off_grid_fraction"] = float(np.mean(~np.isclose(np.rint(g.ridge / inc) * inc, g.ridge, atol=1e-9)))
        res[ch]["run_mean_delta_mae_increments"] = float(runs[runs.channel == ch].delta_mae.mean() / inc)
        res[ch]["ridge_abs_correction_median"] = float((g.ridge - g.persistence).abs().median())
        res[ch]["ridge_abs_correction_p99"] = float((g.ridge - g.persistence).abs().quantile(.99))
    resolution = pd.DataFrame(res.values())

    # 7. Controller-role evidence: P-2 state when MFC-3 is zero versus flowing.
    p = d[d.channel == "P-2"].set_index(["run", "seconds_counter"]).y_true.rename("P2")
    f = d[d.channel == "MFC-3"].set_index(["run", "seconds_counter"]).y_true.rename("F3")
    j = pd.concat([p, f], axis=1).reset_index()
    setpoint = {24: 180, 28: 140, 29: 180}
    control = []
    for r, g in j.groupby("run"):
        on = g.F3 > 0
        control.append(dict(run=r, nominal_outlet_bar=setpoint[r], rows=len(g), mfc3_flowing_fraction=float(on.mean()),
                            p2_when_flowing_p05=float(np.quantile(g.P2[on], .05)), p2_when_flowing_median=float(g.P2[on].median()),
                            p2_when_flowing_p95=float(np.quantile(g.P2[on], .95)),
                            p2_when_zero_median=float(g.P2[~on].median()), p2_when_zero_max=float(g.P2[~on].max())))
    control = pd.DataFrame(control)

    windows = representative_windows(meta["source_notes"])
    manifest = dict(analysis="mhc_evidence_enhancement_v1", source_sha256=meta["source_sha256"],
                    replay_gate_passed=meta["gate_passed"], change_bins=bins_declared, tail_fractions=TAILS,
                    quantile_method="inverted_cdf (an observed value)", representative_windows=windows,
                    nominal_outlet_setpoints_bar=setpoint,
                    independent_units="3 held-out runs on 2 recording dates; rows are serially dependent")
    for name, frame in (("run_metrics", runs), ("error_quantiles", q), ("tail_shares", tails),
                        ("tail_paired_attribution", paired), ("concentration_curves", curves),
                        ("error_vs_change", change), ("resolution", resolution), ("controller_role", control)):
        frame.to_csv(out / f"{name}.csv", index=False, lineterminator="\n")
    (out / "analysis_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False, default=str) + "\n",
                                                encoding="utf-8", newline="\n")
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--replay", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    analyse(a.replay, a.output)
    print("analysis complete")


if __name__ == "__main__":
    main()
