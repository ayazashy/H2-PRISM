"""Advanced formal D(Y) experiments on the accepted Center captures (CONDITIONAL_HYPOTHETICAL_BOUNDS).

Uses the frozen engine (h2prism.certified_evidence.diagnose) and the accepted Center construction
(h2prism.center_enhancement: hash-verified loader, templates, TemplateEnvelopeAdapter, hypotheses, bound ladder)
without modifying either. Experiments (all predeclared in protocols/AV_PROTOCOL.md before running):

  E1 sensor configurations   all, pressure-only, flow-only, 13 single-channel removals, 3 outlet-branch outages,
                             20 fixed random masks each removing 3, 4 and 7 of the 13 channels (seed 20261118)
  E2 admissible clock bound  tau in {0, 1, 2, 5, 10} s, no observation delay
  E3 fixed observation delay d in {0, 1, 2, 5, 10} s (observed signal lags the process), tau = 1 s; and tau = max(1, d)
  E4 hypothesis-library      restricted; restricted minus NORMAL_OPERATION; restricted minus the true hypothesis;
                             full declared universe
Scenarios: E1-E3 use S3, S4, S5 and REF of the frozen ladder; E4 uses S1-S6 and REF. eps split 0.5/0.5 (frozen).

Every EXCLUDED certificate is re-verified independently (disjoint predicted/observed interval on a declared
coordinate whose observed interval equals the measurement's), and every FEASIBLE witness is re-verified by
recomputing the shifted template trajectory against the observation intervals in exact rationals.
Usage: python av_dy_experiments.py --workspace <Center workspace> [--workers 6]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd

AV = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "src"))
from h2prism import center_enhancement as ce  # noqa: E402
from h2prism.certified_evidence import (Channel, ConsistencyStatus, MeasurementContract,  # noqa: E402
                                        diagnose)

SEED = 20261118
SCEN_MAIN = ("S3", "S4", "S5", "REF")
LADDER = {s: (p, f) for s, p, f in ce.LADDER}
LADDER["REF"] = (ce.SOLVER_DELTA["pressure_MPa"], ce.SOLVER_DELTA["flow_kg_s"])
BRANCH = {"branch_SID213(MFS3,PS1)": ("MFS3", "PS1"), "branch_SID312(MFS1)": ("MFS1",),
          "branch_SID215(PS4,PS8,PS9)": ("PS4", "PS8", "PS9")}
_D = None


def _init(ws):
    global _D
    _D = ce.load(Path(ws))


def measurement(data, query, idx, eps_obs, lag):
    values, j = data.queries[query]
    j0 = j - lag
    times = tuple(float(x) for x in data.clock[j:j + ce.N])
    sensors = tuple(ce.SensorRecord(data.names[c], "Center", "node" if data.kinds[c] == "pressure" else "edge",
                                    str(ce.SID[data.names[c]]), data.kinds[c],
                                    "MPa" if data.kinds[c] == "pressure" else "kg/s", ce.STEP_S) for c in idx)
    chans = tuple(Channel(s.sensor_id, s.unit, times, "Saved accepted Center MAT clock",
                          tuple(float(x) for x in values[j0:j0 + ce.N, c]),
                          tuple(float(eps_obs[data.kinds[c]]) for _ in times)) for s, c in zip(sensors, idx))
    return MeasurementContract(sensors, times, chans, f"{query} matched residual (lag {lag})", "Center source family",
                               f"center-capture:{query}", f"{ce.LABEL}: declared hypothetical observation half-widths",
                               1e-9)


def verify(dec, models):
    """Independent re-verification of every certificate in a decision."""
    meas = dec.certificate.measurement
    coords, iv = meas.coordinates(), meas.intervals()
    n_t = len(meas.timestamps_s)
    ok_ex = tot_ex = ok_fe = tot_fe = 0
    adapters = {m.name: m.adapter for m in models}
    for r in dec.certificate.results:
        if r.status is ConsistencyStatus.EXCLUDED:
            tot_ex += 1
            p = r.separation
            k = coords.index(p.coordinate)
            lo, hi = map(Fraction, p.predicted)
            if tuple(map(Fraction, p.observed)) == iv[k] and (hi < iv[k][0] or lo > iv[k][1]):
                ok_ex += 1
        elif r.status is ConsistencyStatus.FEASIBLE:
            tot_fe += 1
            label, shift = r.witness[0], float(r.witness[1].split("=")[1])
            ad = adapters[r.hypothesis]
            w = dict(ad.windows)[label]
            s = int(round(shift / ce.STEP_S)) + (w.shape[0] - 1) // 2
            traj = w[s]
            em = [Fraction(ad.eps_model[k]) for k in ad.kinds]
            good = all(iv[c * n_t + i][0] <= Fraction(float(traj[i, c])) + em[c] and
                       Fraction(float(traj[i, c])) - em[c] <= iv[c * n_t + i][1]
                       for c in range(traj.shape[1]) for i in range(n_t))
            ok_fe += good
    return ok_ex, tot_ex, ok_fe, tot_fe


def run_task(task):
    d = _D
    idx = np.array([d.names.index(n) for n in task["channels"]])
    p, f = LADDER[task["scenario"]]
    eps = {"pressure": p, "mass_flow": f}
    eo = {k: v * 0.5 for k, v in eps.items()}
    em = {k: eps[k] - eo[k] for k in eps}
    t0 = time.perf_counter()
    meas = measurement(d, task["query"], idx, eo, task["lag"])
    models = ce.dy_models(d, task["query"], idx, em, task["bound"], "full" if task["universe"] == "full" else "restricted")
    drop = set(task.get("drop", ()))
    if task["universe"] == "minus_true":
        drop.add(ce.DY_TRUE[task["query"]])
    models = tuple(m for m in models if m.name not in drop)
    dec = diagnose(meas, models)
    dt = time.perf_counter() - t0
    cert = dec.certificate
    truth = ce.DY_TRUE[task["query"]]
    ok_ex, tot_ex, ok_fe, tot_fe = verify(dec, models)
    status = {r.hypothesis: (r.status.value, r.reason) for r in cert.results}
    if dec.status.value == "SPECIFIC":
        outcome = "SPECIFIC_CORRECT" if dec.hypothesis == truth else "SPECIFIC_WRONG"
    elif dec.status.value == "AMBIGUOUS":
        outcome = "AMBIGUOUS_TRUTH_IN" if truth in cert.feasible else "AMBIGUOUS_TRUTH_OUT"
    else:
        outcome = f"UNRESOLVED_{dec.reason}"
    return {**{k: v for k, v in task.items() if k != "channels"}, "channels": "|".join(task["channels"]),
            "n_channels": len(task["channels"]), "eps_P_MPa": p, "eps_F_kg_s": f, "decision": dec.status.value,
            "reason": dec.reason, "selected": dec.hypothesis or "", "truth": truth,
            "truth_in_library": any(m.name == truth and m.adapter is not None for m in models),
            "outcome": outcome, "n_models": len(models), "n_feasible": len(cert.feasible),
            "n_excluded": len(cert.excluded), "n_indeterminate": len(cert.indeterminate),
            "truth_retained": truth in cert.feasible or truth in cert.indeterminate,
            "status_json": json.dumps(status, sort_keys=True), "runtime_s": dt,
            "excl_cert_verified": ok_ex, "excl_cert_total": tot_ex, "witness_verified": ok_fe, "witness_total": tot_fe}


def tasks():
    names = ("PS1", "PS2", "PS3", "PS4", "PS5", "PS6", "PS7", "PS8", "PS9", "PS10", "MFS1", "MFS2", "MFS3")
    pressure, flow = names[:10], names[10:]
    configs = [("all", names), ("pressure_only", pressure), ("flow_only", flow)]
    configs += [(f"drop_{n}", tuple(x for x in names if x != n)) for n in names]
    configs += [(f"outage_{b}", tuple(x for x in names if x not in drop)) for b, drop in BRANCH.items()]
    rng = np.random.default_rng(SEED)
    for k in (3, 4, 7):
        for r in range(20):
            drop = set(rng.choice(names, size=k, replace=False))
            configs.append((f"random_drop{k}_{r:02d}", tuple(x for x in names if x not in drop)))
    T = []
    for cfg, ch in configs:
        for q in ce.DY_QUERIES:
            for s in SCEN_MAIN:
                T.append(dict(experiment="E1_sensors", config=cfg, channels=ch, query=q, scenario=s, bound=1.0, lag=0,
                              universe="restricted"))
    for tau in (0.0, 1.0, 2.0, 5.0, 10.0):
        for q in ce.DY_QUERIES:
            for s in SCEN_MAIN:
                T.append(dict(experiment="E2_clock_bound", config=f"tau_{tau:g}s", channels=names, query=q, scenario=s,
                              bound=tau, lag=0, universe="restricted"))
    for dly in (0, 1, 2, 5, 10):
        for tau in sorted({1.0, max(1.0, float(dly))}):
            for q in ce.DY_QUERIES:
                for s in SCEN_MAIN:
                    T.append(dict(experiment="E3_delay", config=f"delay_{dly}s_tau_{tau:g}s", channels=names, query=q,
                                  scenario=s, bound=tau, lag=int(round(dly / ce.STEP_S)), universe="restricted"))
    for uni, drop in (("restricted", ()), ("restricted", ("NORMAL_OPERATION",)), ("minus_true", ()), ("full", ())):
        tag = uni if not drop else "minus_NORMAL"
        for q in ce.DY_QUERIES:
            for s in ("S1", "S2", "S3", "S4", "S5", "S6", "REF"):
                T.append(dict(experiment="E4_library", config=tag, channels=names, query=q, scenario=s, bound=1.0,
                              lag=0, universe=uni, drop=drop))
    return T


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", default=os.environ.get("H2PRISM_CENTER_WORKSPACE"))
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    T = tasks()
    t0 = time.perf_counter()
    with ProcessPoolExecutor(a.workers, initializer=_init, initargs=(a.workspace,)) as ex:
        rows = list(ex.map(run_task, T, chunksize=4))
    df = pd.DataFrame(rows)
    df["drop"] = df["drop"].apply(lambda x: "|".join(x) if isinstance(x, (tuple, list)) else "")
    out = AV / "analysis"
    out.mkdir(parents=True, exist_ok=True)
    df.drop(columns=["runtime_s"]).to_csv(out / "dy_experiment_runs.csv", index=False, lineterminator="\n")
    df[["experiment", "config", "query", "scenario", "n_channels", "bound", "n_models", "runtime_s"]].to_csv(
        AV / "benchmarks/dy_decision_runtime_from_experiments.csv", index=False, lineterminator="\n")
    print(len(df), "decisions in", round(time.perf_counter() - t0, 1), "s")


if __name__ == "__main__":
    main()
