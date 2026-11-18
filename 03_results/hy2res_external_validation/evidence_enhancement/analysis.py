"""Study C evidence enhancement: quantization, chronological drift, support validity,
unresolved-decision decomposition and operating-state evidence for HY2RES.

Additive and descriptive. Reads the verified official source CSV and the frozen
Study C artifacts (archived predictions, validity mask, split manifest). The
empirical candidate-set rule is replicated line-for-line from
``publication/distinguishability/build_distinguishability.py`` and must reproduce
its published counts before any new attribution is computed. Nothing is fitted,
tuned or re-thresholded; the inspected test period is described, not re-validated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE.parent                                   # 03_results/hy2res_external_validation
OFFICIAL_MD5 = "9a3c3e3b1668596854b43bfd790d3e0e"
OFFICIAL_BYTES = 38_621_947
FEATURES = ["pres_buf", "pres_comp", "h2_flow"]
UNITS = {"pres_buf": "bar", "pres_comp": "bar", "h2_flow": "NL/h"}
NAMES = {"pres_buf": "Buffer pressure", "pres_comp": "Tank pressure", "h2_flow": "Electrolyzer H2 flow"}
STATES = ["electrolyzer_active", "multiple_active"]
PRECEDENCE = ["pres_comp", "pres_buf", "h2_flow"]       # documented order for exclusive attribution
TIME_BIN = "6h"                                          # declared before any binned result was viewed
# Published counts the replicated rule must reproduce (TECHNICAL_REPORT.md, frozen script output).
FROZEN_RULE = {("electrolyzer_active", "Electrolyzer only"): 10762, ("electrolyzer_active", "Ambiguous"): 1126,
               ("electrolyzer_active", "Unresolved"): 31279, ("multiple_active", "Ambiguous"): 201,
               ("multiple_active", "Unresolved"): 616, ("unknown", "Unresolved"): 413}
FROZEN_OUT_OF_RANGE_OR_NONFINITE = 32002


def verify_source(path: Path) -> dict:
    data = path.read_bytes()
    md5, sha = hashlib.md5(data).hexdigest(), hashlib.sha256(data).hexdigest()
    if len(data) != OFFICIAL_BYTES or md5 != OFFICIAL_MD5:
        raise SystemExit(f"Gate A failed: {len(data)} bytes, MD5 {md5}")
    return dict(path_name=path.name, bytes=len(data), md5=md5, sha256=sha)


# ---------------------------------------------------------------- frozen rule replica

def frozen_rule(raw: pd.DataFrame, audit: pd.DataFrame):
    """Line-for-line replica of build_distinguishability.py (decision part), returning row detail."""
    t = pd.to_datetime(raw.datetime)
    segments = audit.segment_id
    assert t.equals(pd.to_datetime(audit.timestamp).rename("datetime"))
    same = segments.eq(segments.shift())
    assert t.diff()[same].dt.total_seconds().eq(5).all()
    p = raw[["P_elec", "P_comp", "P_pila"]].shift().where(same, axis=0)
    known = np.isfinite(p).all(axis=1)
    powered = p.gt(0)
    label = pd.Series(np.where(~known, "unknown", np.where(powered.sum(axis=1) > 1, "multiple_active",
                                                            "electrolyzer_active")))
    assert label.equals(audit.operating_regime_at_forecast_origin.rename(None))
    frame = raw[FEATURES].shift().where(same, axis=0)
    frame = frame.assign(label=label, segment=segments, role=audit.split_role, time=t)
    usable = np.isfinite(frame[FEATURES]).all(axis=1)
    dev = frame[frame.role.eq("development") & usable & known].copy()
    test = frame[frame.role.eq("test")].copy()

    def cell(f):
        cats = []
        for feature in FEATURES:
            values = dev[feature]
            if feature == "h2_flow":
                values = values[values.gt(0)]
            edges = np.unique(values.quantile([.25, .5, .75]).values)
            code = np.searchsorted(edges, f[feature], side="left")
            if feature == "h2_flow":
                code = np.where(f[feature].eq(0), -1, code)
            cats.append(code)
        return list(zip(*cats))

    dev["cell"] = cell(dev)
    counts = dev.groupby(["cell", "label"]).segment.nunique().unstack(fill_value=0)
    admitted = {k: tuple(s for s in STATES if row.get(s, 0) >= 2) for k, row in counts.iterrows()}
    lo, hi = dev[FEATURES].min(), dev[FEATURES].max()
    inside = test[FEATURES].ge(lo).all(axis=1) & test[FEATURES].le(hi).all(axis=1)
    test["cell"] = cell(test)
    test["candidates"] = [admitted.get(k, ()) if ok else () for k, ok in zip(test.cell, inside)]
    test["decision"] = test.candidates.map(lambda c: {(STATES[0],): "Electrolyzer only", (STATES[1],): "Both powered",
                                                      tuple(STATES): "Ambiguous", (): "Unresolved"}[c])
    test["inside"] = inside
    bounds = pd.DataFrame({"dev_min": lo, "dev_max": hi})
    return frame, dev, test, bounds, admitted, usable, known


def attribute(test: pd.DataFrame, bounds: pd.DataFrame) -> pd.DataFrame:
    """Additive explanatory reasons; the frozen decision column is left untouched."""
    out = test.copy()
    for f in FEATURES:
        v = out[f]
        out[f"{f}_nonfinite"] = ~np.isfinite(v)
        out[f"{f}_below"] = np.isfinite(v) & (v < bounds.loc[f, "dev_min"])
        out[f"{f}_above"] = np.isfinite(v) & (v > bounds.loc[f, "dev_max"])
        out[f"{f}_outside"] = out[f"{f}_below"] | out[f"{f}_above"]
        out[f"{f}_excess"] = np.where(out[f"{f}_above"], v - bounds.loc[f, "dev_max"],
                                      np.where(out[f"{f}_below"], v - bounds.loc[f, "dev_min"], 0.0))
    out["any_nonfinite"] = out[[f"{f}_nonfinite" for f in FEATURES]].any(axis=1)
    out["n_channels_outside"] = out[[f"{f}_outside" for f in FEATURES]].sum(axis=1)

    def primary(r):
        if r.decision != "Unresolved":
            return "—"
        if r.any_nonfinite:
            return "INVALID_INPUT (nonfinite origin measurement)"
        for f in PRECEDENCE:
            if getattr(r, f"{f}_outside"):
                return f"OUT_OF_SUPPORT ({f})"
        return "EMPTY_CELL (no state with >=2 development segments)"
    out["primary_reason"] = [primary(r) for r in out.itertuples()]
    out["reason_class"] = out.primary_reason.str.split(" ").str[0]
    return out


# ------------------------------------------------------------------------- analyses

def grid_table(raw: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for f in ["pres_buf", "pres_comp", "h2_flow"]:
        v = raw[f].dropna().to_numpy()
        u = np.unique(v)
        d = np.diff(u)
        tenths = np.isclose(np.rint(v * 10) / 10, v, rtol=0, atol=1e-9)
        rows.append(dict(channel=f, unit=UNITS[f], valid_rows=int(len(v)), missing_rows=int(raw[f].isna().sum()),
                         distinct_values=int(len(u)), minimum=float(u.min()), maximum=float(u.max()),
                         smallest_positive_step=float(np.round(d[d > 1e-12].min(), 9)),
                         modal_step=float(pd.Series(np.round(d, 9)).mode().iloc[0]) if len(d) else np.nan,
                         on_0p1_grid_fraction=float(tenths.mean()), off_grid_rows=int((~tenths).sum()),
                         decimals_observed=int(max(len(s.split(".")[1]) if "." in s else 0
                                                   for s in raw[f].dropna().astype(str).unique()[:20000]))))
    return pd.DataFrame(rows)


def reconcile_benchmark(pred: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Recompute overall and per-state MAE/RMSE from archived predictions; compare to TABLE_2_HELD_OUT."""
    frozen = pd.read_csv(ARCHIVE / "publication/TABLE_2_HELD_OUT.csv")
    rows = []
    for target, g in pred.groupby("target"):
        g = g.dropna(subset=["y_true", "persistence_prediction", "contextual_prediction"])
        for state, h in [("overall", g)] + list(g.groupby("operating_regime")):
            ep, er = h.y_true - h.persistence_prediction, h.y_true - h.contextual_prediction
            f = frozen[(frozen.target == target) & (frozen.state == state)]
            vals = dict(persistence_mae=ep.abs().mean(), persistence_rmse=np.sqrt((ep ** 2).mean()),
                        contextual_ridge_mae=er.abs().mean(), contextual_ridge_rmse=np.sqrt((er ** 2).mean()))
            for k, v in vals.items():
                ref = float(f[k].iloc[0]) if len(f) and pd.notna(f[k].iloc[0]) else np.nan
                rows.append(dict(target=target, state=state, metric=k, n=len(h), frozen=ref, recomputed=float(v),
                                 abs_diff=abs(float(v) - ref) if ref == ref else np.nan,
                                 passed=bool(ref == ref and abs(float(v) - ref) <= 1e-12 * max(1, abs(ref)))))
    gate = pd.DataFrame(rows)
    return gate, frozen


def quantization_comparison(pred: pd.DataFrame, step: float = 0.1):
    rows, steps = [], []
    for target in ("pres_buf", "pres_comp"):
        g = pred[pred.target == target].dropna(subset=["y_true", "persistence_prediction", "contextual_prediction"])
        ep, er = g.y_true - g.persistence_prediction, g.y_true - g.contextual_prediction
        k = np.rint((g.y_true - g.persistence_prediction) / step).astype(int)     # recorded target step, in increments
        exact = int((ep == 0).sum())
        m = dict(pm=ep.abs().mean(), rm=er.abs().mean(), pr=np.sqrt((ep ** 2).mean()), rr=np.sqrt((er ** 2).mean()))
        rows.append(dict(channel=target, unit="bar", recording_increment=step, n=len(g), segments=int(g.segment_id.nunique()),
                         persistence_exact_hits=exact, persistence_exact_rate=exact / len(g),
                         nonzero_step_rows=int((k != 0).sum()), nonzero_step_rate=float((k != 0).mean()),
                         persistence_mae=m["pm"], ridge_mae=m["rm"], delta_mae=m["rm"] - m["pm"],
                         rel_delta_mae=(m["rm"] - m["pm"]) / m["pm"], persistence_rmse=m["pr"], ridge_rmse=m["rr"],
                         delta_rmse=m["rr"] - m["pr"], rel_delta_rmse=(m["rr"] - m["pr"]) / m["pr"],
                         persistence_mae_incr=m["pm"] / step, ridge_mae_incr=m["rm"] / step,
                         persistence_rmse_incr=m["pr"] / step, ridge_rmse_incr=m["rr"] / step,
                         delta_mae_incr=(m["rm"] - m["pm"]) / step, delta_rmse_incr=(m["rr"] - m["pr"]) / step,
                         persistence_signed_mean=float((g.persistence_prediction - g.y_true).mean()),
                         ridge_signed_mean=float((g.contextual_prediction - g.y_true).mean()),
                         ridge_on_grid_fraction=float(np.isclose(np.rint(g.contextual_prediction / step) * step,
                                                                 g.contextual_prediction, rtol=0, atol=1e-9).mean()),
                         ridge_equals_recorded_value=float((g.contextual_prediction == g.y_true).mean())))
        tot_p, tot_r = (ep ** 2).sum(), (er ** 2).sum()
        cls = np.where(k == 0, "0 (unchanged)", np.where(k.abs() == 1, "±1 increment",
                       np.where(k.abs() == 2, "±2 increments", "≥3 increments")))
        for c in ["0 (unchanged)", "±1 increment", "±2 increments", "≥3 increments"]:
            s = cls == c
            sp, sr = float((ep[s] ** 2).sum()), float((er[s] ** 2).sum())
            steps.append(dict(channel=target, step_class=c, n=int(s.sum()), share_rows=float(s.mean()),
                              persistence_mae=float(ep[s].abs().mean()) if s.any() else np.nan,
                              ridge_mae=float(er[s].abs().mean()) if s.any() else np.nan,
                              persistence_sse=sp, ridge_sse=sr, persistence_sse_share=sp / tot_p,
                              ridge_sse_share=sr / tot_r, delta_sse=sr - sp,
                              delta_sse_share_of_net=(sr - sp) / (tot_r - tot_p)))
    return pd.DataFrame(rows), pd.DataFrame(steps)


def chronology(raw: pd.DataFrame, audit: pd.DataFrame, bounds: pd.DataFrame) -> pd.DataFrame:
    t = pd.to_datetime(raw.datetime)
    rows = []
    for role in ("development", "validation", "embargo", "test"):
        m = audit.split_role.eq(role).to_numpy()
        seg = audit.segment_id[m]
        for f in FEATURES:
            v = raw.loc[m, f]
            fin = v[np.isfinite(v)]
            q = fin.quantile([0, .01, .05, .5, .95, .99, 1]).to_numpy()
            rows.append(dict(partition=role, channel=f, unit=UNITS[f], start=str(t[m].min()), end=str(t[m].max()),
                             rows=int(m.sum()), valid_rows=int(len(fin)), missing_rows=int(len(v) - len(fin)),
                             segments=int(seg.nunique()), minimum=q[0], p01=q[1], p05=q[2], median=q[3], p95=q[4],
                             p99=q[5], maximum=q[6], dev_rule_min=bounds.loc[f, "dev_min"],
                             dev_rule_max=bounds.loc[f, "dev_max"],
                             above_dev_max_rate=float((fin > bounds.loc[f, "dev_max"]).mean()),
                             below_dev_min_rate=float((fin < bounds.loc[f, "dev_min"]).mean())))
    return pd.DataFrame(rows)


def support_attribution(att: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    n, unres = len(att), att.decision.eq("Unresolved")
    rows = []
    for f in FEATURES:
        for cond in ("below", "above", "outside", "nonfinite"):
            m = att[f"{f}_{cond}"]
            others = [g for g in FEATURES if g != f]
            rows.append(dict(channel=f, condition=cond, rows=int(m.sum()), fraction_of_test=float(m.mean()),
                             fraction_of_unresolved=float((m & unres).sum() / unres.sum()),
                             overlap_with_other_channel_outside=int((m & att[[f"{g}_outside" for g in others]].any(axis=1)).sum()),
                             segments=int(att.segment[m].nunique()),
                             primary_reason_rows=int(att.primary_reason.eq(f"OUT_OF_SUPPORT ({f})").sum()) if cond == "outside" else np.nan,
                             max_excess=float(att.loc[m, f"{f}_excess"].abs().max()) if m.any() and cond != "nonfinite" else np.nan))
    combos = att[unres].assign(
        combo=lambda d: d.apply(lambda r: " + ".join([f for f in FEATURES if r[f"{f}_outside"]] +
                                                      (["nonfinite"] if r.any_nonfinite else [])) or "none", axis=1))
    combo = combos.groupby("combo").agg(rows=("combo", "size"), segments=("segment", "nunique")).reset_index()
    combo["fraction_of_unresolved"] = combo.rows / unres.sum()
    return pd.DataFrame(rows), combo.sort_values("rows", ascending=False)


def taxonomy(att: pd.DataFrame) -> pd.DataFrame:
    n = len(att)
    unres = att.decision.eq("Unresolved").sum()
    g = att.groupby(["decision", "primary_reason"]).agg(rows=("decision", "size"), segments=("segment", "nunique"),
                                                         electrolyzer_only=("label", lambda s: int((s == STATES[0]).sum())),
                                                         compressor_powered=("label", lambda s: int((s == STATES[1]).sum())),
                                                         unknown_power=("label", lambda s: int((s == "unknown").sum()))).reset_index()
    g["pct_of_test_rows"] = g.rows / n
    g["pct_of_unresolved"] = np.where(g.decision == "Unresolved", g.rows / unres, np.nan)
    return g


def state_outcomes(att: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for s in STATES + ["unknown"]:
        g = att[att.label == s]
        spec = g.decision.isin(["Electrolyzer only", "Both powered"])
        correct = ((g.decision == "Electrolyzer only") & (s == STATES[0])) | ((g.decision == "Both powered") & (s == STATES[1]))
        rows.append(dict(state=s, rows=len(g), segments=int(g.segment.nunique()), specific=int(spec.sum()),
                         specific_correct=int(correct.sum()), ambiguous=int((g.decision == "Ambiguous").sum()),
                         unresolved=int((g.decision == "Unresolved").sum()),
                         unresolved_out_of_support=int(g.primary_reason.str.startswith("OUT_OF_SUPPORT").sum()),
                         unresolved_invalid=int(g.primary_reason.str.startswith("INVALID").sum()),
                         unresolved_empty_cell=int(g.primary_reason.str.startswith("EMPTY").sum()),
                         majority_baseline_agree=len(g) if s == STATES[0] else 0))
    return pd.DataFrame(rows)


def rank_probability(a: np.ndarray, b: np.ndarray) -> float:
    """P(B > A) + 0.5 P(B = A) via mid-ranks (same convention as the frozen script)."""
    scores = pd.Series(np.r_[a, b]).rank().to_numpy()[len(a):]
    return float((scores.sum() - len(b) * (len(b) + 1) / 2) / (len(a) * len(b)))


def distinguishability(att: pd.DataFrame) -> pd.DataFrame:
    valid = att[np.isfinite(att[FEATURES]).all(axis=1) & att.label.isin(STATES)]
    rows = []
    for f in FEATURES:
        for rule in ("all rows", "positive flow only"):
            g = valid if rule == "all rows" else valid[valid.h2_flow > 0]
            a, b = [g[g.label == s][f].to_numpy() for s in STATES]
            rows.append(dict(pair="compressor-powered vs electrolyzer only", channel=f, unit=UNITS[f],
                             flow_rule=rule, n_electrolyzer_only=len(a), n_compressor=len(b),
                             segments_electrolyzer_only=int(g[g.label == STATES[0]].segment.nunique()),
                             segments_compressor=int(g[g.label == STATES[1]].segment.nunique()),
                             rank_probability=rank_probability(a, b) if len(a) and len(b) else np.nan,
                             exact_value_overlap=float(pd.concat([pd.Series(a).value_counts(normalize=True),
                                                                  pd.Series(b).value_counts(normalize=True)], axis=1)
                                                       .fillna(0).min(axis=1).sum()) if len(a) and len(b) else np.nan,
                             compressor_min=float(b.min()) if len(b) else np.nan,
                             compressor_max=float(b.max()) if len(b) else np.nan))
    return pd.DataFrame(rows)


def time_bins(att: pd.DataFrame) -> pd.DataFrame:
    g = att.set_index("time").groupby(pd.Grouper(freq=TIME_BIN))
    out = g.agg(rows=("decision", "size"), unresolved=("decision", lambda s: int((s == "Unresolved").sum())),
                out_of_support=("primary_reason", lambda s: int(s.str.startswith("OUT_OF_SUPPORT").sum())),
                tank_median=("pres_comp", "median"), segments=("segment", "nunique")).reset_index()
    out = out[out.rows > 0]
    out["unresolved_fraction"] = out.unresolved / out.rows
    out["out_of_support_fraction"] = out.out_of_support / out.rows
    return out


# ---------------------------------------------------------------------------- driver

def run(source: Path, out: Path):
    out.mkdir(parents=True, exist_ok=False)
    src = verify_source(source)
    raw = pd.read_csv(source, sep=";")
    audit = pd.read_csv(ARCHIVE / "validity_mask.csv.gz")
    pred = pd.read_csv(ARCHIVE / "test_predictions.csv.gz")
    frame, dev, test, bounds, admitted, usable, known = frozen_rule(raw, audit)
    crosstab = test.groupby(["label", "decision"]).size()
    gate_c = [dict(label=l, decision=d, frozen=v, reproduced=int(crosstab.get((l, d), 0)),
                   passed=int(crosstab.get((l, d), 0)) == v) for (l, d), v in FROZEN_RULE.items()]
    extra = [(l, d) for (l, d) in crosstab.index if (l, d) not in FROZEN_RULE and crosstab[(l, d)] > 0]
    gate_c.append(dict(label="all", decision="out of range or nonfinite", frozen=FROZEN_OUT_OF_RANGE_OR_NONFINITE,
                       reproduced=int((~test.inside).sum()), passed=int((~test.inside).sum()) == FROZEN_OUT_OF_RANGE_OR_NONFINITE))
    gate_c = pd.DataFrame(gate_c)
    if not gate_c.passed.all() or extra:
        gate_c.to_csv(out / "gate_decision_reproduction.csv", index=False, lineterminator="\n")
        raise SystemExit("Gate C failed: frozen decisions not reproduced; dependent analyses blocked")
    gate_b, _ = reconcile_benchmark(pred)
    if not gate_b.passed.all():
        raise SystemExit("Gate B failed: archived metrics do not reconcile")
    att = attribute(test, bounds)
    # Temporal integrity: test strictly after development, rule uses only lagged same-segment values.
    gate_d = dict(dev_last=str(frame[frame.role == "development"].time.max()), test_first=str(test.time.min()),
                  ordered=bool(frame[frame.role == "development"].time.max() < test.time.min()),
                  shared_dev_test_segments=int(len(set(dev.segment) & set(test.segment))))
    q, steps = quantization_comparison(pred)
    tables = dict(gate_benchmark_reconciliation=gate_b, gate_decision_reproduction=gate_c,
                  recording_grid=grid_table(raw), quantization_comparison=q, step_contribution=steps,
                  chronology=chronology(raw, audit, bounds), development_bounds=bounds.reset_index(names="channel"),
                  support_attribution=support_attribution(att)[0], support_combinations=support_attribution(att)[1],
                  unresolved_taxonomy=taxonomy(att), state_outcomes=state_outcomes(att),
                  distinguishability=distinguishability(att), time_bins=time_bins(att))
    for name, t in tables.items():
        t.to_csv(out / f"{name}.csv", index=False, lineterminator="\n")
    cols = ["time", "segment", "label", *FEATURES, "decision", "primary_reason", "n_channels_outside",
            *[f"{f}_{c}" for f in FEATURES for c in ("below", "above", "nonfinite")]]
    att[cols].to_csv(out / "test_decision_attribution.csv.gz", index=False, lineterminator="\n",
                     compression={"method": "gzip", "mtime": 0})
    # Full chronology series for the drift figure (tank pressure, segment ids) — derived, not raw copies.
    manifest = dict(analysis="hy2res_evidence_enhancement_v1", source=src, frozen_commit="6a926de43f3283d9a995fbe0d8381a06c015344f",
                    frozen_rule_script="publication/distinguishability/build_distinguishability.py",
                    precedence=PRECEDENCE, time_bin=TIME_BIN, gates=dict(A=True, B=bool(gate_b.passed.all()),
                    C=bool(gate_c.passed.all()), D=gate_d),
                    environment=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__))
    (out / "analysis_manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8",
                                                newline="\n")
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=os.environ.get("HY2RES_SOURCE_CSV"),
                   help="verified HY2RES_202404.csv (or set HY2RES_SOURCE_CSV)")
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.source is None:
        raise SystemExit("pass --source or set HY2RES_SOURCE_CSV")
    print(json.dumps(run(Path(a.source), a.output)["gates"], indent=2))


if __name__ == "__main__":
    main()
