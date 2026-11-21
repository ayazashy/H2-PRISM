"""Center evidence enhancement: self-template-excluded recognition, categorical
location ranking, sensor-group identifiability and conditional D(Y) bounds.

Additive analysis on the 12 accepted Center captures. It reuses the frozen B3
kernel (``nres.rank``) and the frozen consistency engine
(``certified_evidence.diagnose``) without modifying either. Every uncertainty
result is ``CONDITIONAL_HYPOTHETICAL_BOUNDS``: the bounds are declared design
assumptions, never qualified sensor or model specifications.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd

from .certified_evidence import (Channel, ConsistencyResult, ConsistencyStatus, HypothesisModel,
                                 IntervalSeparation, MeasurementContract, diagnose)
from .data_contracts import SensorRecord
from .mechanism_screen import LOCATIONS, MECHANISMS, NORMAL, WITHDRAWAL, screen
from .nres import load_pairs, rank
from .phase2 import SID

LABEL = "CONDITIONAL_HYPOTHETICAL_BOUNDS"
STEP_S = 0.2
WINDOW_S = 30
N = round(WINDOW_S / STEP_S) + 1          # 151 samples, frozen focal prefix
PAD = 10                                  # frozen library padding (samples)
CLOCK_BOUNDS_S = (1.0, 0.0)               # frozen focal ±1 s, plus exact-clock sensitivity
GROUPS = ("all", "pressure", "flow", "omit_MFS3")

# Primary data object of every query and template (the capture whose intervention it encodes).
QUERY_PRIMARY = {"SID213": "A:outlet_opening", "SID312": "sid312:outlet_opening",
                 "SID215": "sid215:outlet_opening", "PRESSURE": "pressure_rival:outlet_opening",
                 "TIMING": "timing:outlet_opening", "ALT": "alternate_profile:outlet_opening",
                 "NOMINAL": "A:normal", "QUIET": "constructed:zero"}
QUERY_REFERENCE = {"SID213": "A:normal", "SID312": "sid312:normal", "SID215": "sid215:normal",
                   "PRESSURE": "pressure_rival:normal", "TIMING": "timing:normal",
                   "ALT": "alternate_profile:normal", "NOMINAL": "A:normal (value at 24.8 s)",
                   "QUIET": "none"}
TEMPLATE_PRIMARY = {"SID213": "A:outlet_opening", "SID312": "sid312:outlet_opening",
                    "SID215": "sid215:outlet_opening", "PRESSURE": "pressure_rival:outlet_opening",
                    "TIMING": "timing:outlet_opening", "ALT": "alternate_profile:outlet_opening",
                    "NORMAL_ZERO": "constructed:zero", "NORMAL_TRANSIENT": "sid312:normal"}
TRUTH = {"SID213": WITHDRAWAL, "SID312": WITHDRAWAL, "SID215": WITHDRAWAL, "ALT": WITHDRAWAL,
         "PRESSURE": "PRESSURE_COMMAND_CHANGE", "TIMING": "COMMAND_ISSUANCE_SHIFT",
         "NOMINAL": NORMAL, "QUIET": NORMAL}
TRUE_SITE = {"SID213": "SID213", "SID312": "SID312", "SID215": "SID215", "ALT": "SID213"}
REGISTRY = dict(MECHANISMS, ALT=WITHDRAWAL)
TEMPLATE_SITE = {"SID213": "SID213", "SID312": "SID312", "SID215": "SID215", "ALT": "SID213"}
NEAR_DUPLICATE_FRACTION = 0.01            # predeclared: template reproduces query within 1 % of its B3 signal

# D(Y) hypotheses in matched-residual space. Templates realise the prediction set.
DY_HYPOTHESES = {"NORMAL_OPERATION": ("NORMAL_ZERO",),
                 "WITHDRAWAL_SID213": ("SID213", "ALT"), "WITHDRAWAL_SID312": ("SID312",),
                 "WITHDRAWAL_SID215": ("SID215",), "PRESSURE_COMMAND_SID55": ("PRESSURE",),
                 "COMMAND_ISSUANCE_SHIFT_SID59": ("TIMING",)}
DY_TRUE = {"SID213": "WITHDRAWAL_SID213", "SID312": "WITHDRAWAL_SID312", "SID215": "WITHDRAWAL_SID215",
           "ALT": "WITHDRAWAL_SID213", "PRESSURE": "PRESSURE_COMMAND_SID55",
           "TIMING": "COMMAND_ISSUANCE_SHIFT_SID59"}
# Declared in the frozen universe or the original four-class contract, with no adapter.
DY_UNMODELLED = ("WITHDRAWAL_SID222", "COMPRESSOR_FAULT", "ACTUATOR_DELAY")
DY_QUERIES = ("SID213", "SID312", "SID215", "ALT", "PRESSURE", "TIMING")
# Paired hypothetical total half-width ladder, eps_total = eps_obs + eps_model.
LADDER = (("S1", 1e-6, 1e-5), ("S2", 1e-5, 1e-4), ("S3", 1e-4, 1e-3), ("S4", 1e-3, 1e-2),
          ("S5", 1e-2, 1e-1), ("S6", 1e-1, 1.0))
# Observed solver-refinement deltas (0.4 -> 0.2 s) from final_research/research_evidence.json.
# Reported as a scale reference only; they are not an enclosure.
SOLVER_DELTA = {"pressure_MPa": 0.034447880819561405, "flow_kg_s": 0.01822308612894652}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


TEXT_SUFFIXES = (".csv", ".json", ".md", ".svg")


def normalize_lf(root: Path) -> None:
    """Rewrite text outputs with LF endings so checksums survive the repository's eol=lf rule."""
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix in TEXT_SUFFIXES:
            data = path.read_bytes()
            if b"\r\n" in data:
                path.write_bytes(data.replace(b"\r\n", b"\n"))


# ----------------------------------------------------------------------------- data

@dataclass(frozen=True)
class CenterData:
    clock: np.ndarray
    names: tuple
    kinds: tuple
    templates: dict          # name -> (array, anchor index), frozen mechanism-screen construction
    queries: dict            # name -> (array, anchor index)
    scale: np.ndarray
    hashes: dict
    controls: dict


def load(base: Path) -> CenterData:
    """Rebuild the frozen mechanism-screen templates and focal queries exactly."""
    t, schema, pairs, hashes = load_pairs(base)       # verifies every raw MAT hash
    names = tuple(s.name for s in schema)
    kinds = tuple(s.kind for s in schema)
    scale = np.sqrt(np.mean(pairs["SID213"][0].values[t < 1000] ** 2, axis=0))
    a25, late = np.searchsorted(t, 25), np.searchsorted(t, 1000)
    contrasts = {k: b.values - a.values for k, (a, b) in pairs.items()}
    normal = pairs["SID312"][0].values
    templates = {k: (contrasts[k], a25 if k == "TIMING" else late)
                 for k in (*LOCATIONS, "PRESSURE", "TIMING")}
    templates["NORMAL_ZERO"] = (np.zeros_like(normal), late)
    templates["NORMAL_TRANSIENT"] = (normal - normal[a25 - 1], a25)
    templates["ALT"] = (contrasts["ALT"], late)                       # replicate realisation of SID 213
    nominal = pairs["SID213"][0].values
    queries = {k: (contrasts[k], np.searchsorted(t, 26 if k == "TIMING" else 1000))
               for k in ("SID213", "SID312", "SID215", "PRESSURE", "ALT", "TIMING")}
    queries["NOMINAL"] = (nominal - nominal[a25 - 1], np.searchsorted(t, 25))
    queries["QUIET"] = (np.zeros_like(nominal), late)
    controls = {k: v[0].values for k, v in pairs.items()}
    return CenterData(t, names, kinds, templates, queries, scale, hashes, controls)


def group_index(data: CenterData, group: str) -> np.ndarray:
    if group == "all":
        return np.arange(len(data.names))
    if group == "pressure":
        return np.array([i for i, k in enumerate(data.kinds) if k == "pressure"])
    if group == "flow":
        return np.array([i for i, k in enumerate(data.kinds) if k == "mass_flow"])
    if group.startswith("omit_"):
        drop = group[5:]
        if drop not in data.names:
            raise ValueError(f"unknown channel {drop}")
        return np.array([i for i, n in enumerate(data.names) if n != drop])
    raise ValueError(f"unknown group {group}")


def query_window(data: CenterData, query: str, idx) -> np.ndarray:
    values, j = data.queries[query]
    return values[j:j + N, idx]


def library(data: CenterData, names, idx) -> dict:
    """Frozen screen slicing: template window with PAD samples either side, anchor PAD."""
    return {k: (data.templates[k][0][data.templates[k][1] - PAD:data.templates[k][1] + N + PAD, idx], PAD)
            for k in names}


# ------------------------------------------------------------- self-template exclusion

def excluded_templates(query: str, candidates) -> list:
    """Predeclared rule: drop templates whose primary capture is the query's primary capture."""
    return [k for k in candidates if TEMPLATE_PRIMARY[k] == QUERY_PRIMARY[query]]


def frozen_library_names() -> tuple:
    return (*LOCATIONS, "PRESSURE", "TIMING", "NORMAL_ZERO", "NORMAL_TRANSIENT")


def collapse_ranks(rows, registry):
    """Best template per mechanism; ties are preserved by returning equal-score groups."""
    best = {}
    for r in rows:
        m = registry[r["candidate"]]
        if m not in best or r["rms"] < best[m]["rms"]:
            best[m] = dict(r, mechanism=m)
    return sorted(best.values(), key=lambda r: (r["rms"], r["mechanism"]))


def tied(a: float, b: float) -> bool:
    return abs(a - b) <= 1e-12 * max(1.0, abs(a), abs(b))


def recognition(data: CenterData, query: str, condition: str, group: str = "all", bound: float = 1.0):
    """Rank mechanisms with the frozen B3 kernel under one library condition."""
    idx = group_index(data, group)
    pool = list(frozen_library_names())
    if condition in ("loto", "loto_replicate"):
        if condition == "loto_replicate":
            pool.append("ALT")
        removed = excluded_templates(query, pool)
        pool = [k for k in pool if k not in removed]
    elif condition == "frozen":
        removed = []
    else:
        raise ValueError(condition)
    q = query_window(data, query, idx)
    lib = library(data, pool, idx)
    result = rank(q, lib, STEP_S, bound, data.scale[idx])
    rows = result["ranks"]
    mech = collapse_ranks(rows, REGISTRY)
    truth = TRUTH[query]
    represented = truth in {REGISTRY[k] for k in pool}
    zero = rank(q, library(data, ["NORMAL_ZERO"], idx), STEP_S, bound, data.scale[idx])["ranks"][0]["rms"]
    near = [r["candidate"] for r in rows
            if r["candidate"] != "NORMAL_ZERO" and zero > 0 and r["rms"] <= NEAR_DUPLICATE_FRACTION * zero]
    top = mech[0]
    tie = len(mech) > 1 and tied(mech[0]["rms"], mech[1]["rms"])
    if not represented:
        status = "UNSUPPORTED"
    elif tie:
        status = "TIE"
    else:
        status = "CORRECT" if top["mechanism"] == truth else "INCORRECT"
    locs = [k for k in LOCATIONS if k in pool]
    gate = _safe_screen(q, lib, REGISTRY, locs, STEP_S, bound, data.scale[idx]) if locs else None
    return dict(query=query, condition=condition, group=group, clock_bound_s=bound,
                truth=truth, n_templates=len(pool), templates=pool, removed=removed,
                mechanisms_available=sorted({REGISTRY[k] for k in pool}),
                truth_represented=represented, predicted=top["mechanism"], predicted_template=top["candidate"],
                score=top["rms"], runner_up=mech[1]["mechanism"] if len(mech) > 1 else None,
                runner_up_score=mech[1]["rms"] if len(mech) > 1 else None,
                margin=(mech[1]["rms"] - mech[0]["rms"]) if len(mech) > 1 else None,
                truth_score=next((m["rms"] for m in mech if m["mechanism"] == truth), None),
                truth_rank=next((i + 1 for i, m in enumerate(mech) if m["mechanism"] == truth), None),
                status=status, near_duplicates=near, zero_reference_rms=zero,
                gate_eligible=None if gate is None else gate["eligible"],
                gate_reason=None if gate is None else gate["reason"],
                mechanism_scores={m["mechanism"]: m["rms"] for m in mech},
                template_scores={r["candidate"]: r["rms"] for r in rows})


def _safe_screen(*args):
    try:
        return screen(*args)
    except ValueError:
        return None


def location_ranking(data: CenterData, query: str, condition: str, group: str = "all", bound: float = 1.0):
    """Rank categorical outlet SIDs using only withdrawal templates admissible for the query."""
    idx = group_index(data, group)
    pool = list(LOCATIONS) + (["ALT"] if condition == "loto_replicate" else [])
    removed = excluded_templates(query, pool) if condition != "frozen" else []
    pool = [k for k in pool if k not in removed]
    q = query_window(data, query, idx)
    rows = rank(q, library(data, pool, idx), STEP_S, bound, data.scale[idx])["ranks"]
    site = {}
    for r in rows:
        s = TEMPLATE_SITE[r["candidate"]]
        if s not in site or r["rms"] < site[s]:
            site[s] = r["rms"]
    order = sorted(site.items(), key=lambda kv: (kv[1], kv[0]))
    truth = TRUE_SITE[query]
    represented = truth in site
    ranks = {s: i + 1 for i, (s, _) in enumerate(order)}
    tie = len(order) > 1 and tied(order[0][1], order[1][1])
    return dict(query=query, condition=condition, group=group, clock_bound_s=bound, true_site=truth,
                candidates=[s for s, _ in order], candidate_templates=pool, removed=removed,
                site_scores=dict(order), site_ranks=ranks, truth_represented=represented,
                top1=order[0][0], top1_correct=represented and not tie and order[0][0] == truth,
                top2_includes_truth=represented and truth in [s for s, _ in order[:2]],
                true_rank=ranks.get(truth), margin=(order[1][1] - order[0][1]) if len(order) > 1 else None,
                tie=tie, status=("UNSUPPORTED" if not represented else "TIE" if tie else
                                 "CORRECT" if order[0][0] == truth else "INCORRECT"))


def pair_contrasts(data: CenterData, bound: float = 1.0):
    """Template-vs-template contrasts for the withdrawal realisations, per group, both units."""
    rows = []
    sites = ("SID213", "SID312", "SID215", "ALT")
    for i, a in enumerate(sites):
        for b in sites[i + 1:]:
            va, ia = data.templates[a]
            vb, ib = data.templates[b]
            for group in GROUPS:
                idx = group_index(data, group)
                q = va[ia:ia + N, idx]
                result = rank(q, library(data, [b], idx), STEP_S, bound, data.scale[idx])["ranks"][0]
                radius = int(round(bound / STEP_S))
                native = {}
                for kind, unit in (("pressure", "MPa"), ("mass_flow", "kg/s")):
                    sel = [j for j, k in enumerate(np.array(data.kinds)[idx]) if k == kind]
                    if not sel:
                        native[unit] = None
                        continue
                    cols = idx[sel]
                    native[unit] = min(float(np.abs(va[ia:ia + N, cols] - vb[ib + k:ib + k + N, cols]).max())
                                       for k in range(-radius, radius + 1))
                contrib = np.array(result["per_channel_squared_contribution"])
                kinds = np.array(data.kinds)[idx]
                rows.append(dict(a=a, b=b, group=group, clock_bound_s=bound, b3_rms=result["rms"],
                                 selected_shift_s=result["selected_shift_s"],
                                 pressure_share=float(contrib[kinds == "pressure"].sum() / contrib.sum())
                                 if contrib.sum() > 0 else None,
                                 flow_share=float(contrib[kinds == "mass_flow"].sum() / contrib.sum())
                                 if contrib.sum() > 0 else None,
                                 max_abs_pressure_MPa=native["MPa"], max_abs_flow_kg_s=native["kg/s"],
                                 channels=",".join(np.array(data.names)[idx])))
    return rows


def channel_signal(data: CenterData):
    """Native-unit 30 s peak magnitude of every query residual, per channel."""
    rows = []
    for q in ("SID213", "SID312", "SID215", "ALT", "PRESSURE", "TIMING"):
        v, j = data.queries[q]
        for c, (name, kind) in enumerate(zip(data.names, data.kinds)):
            rows.append(dict(query=q, channel=name, unit="MPa" if kind == "pressure" else "kg/s",
                             peak_abs=float(np.abs(v[j:j + N, c]).max()), scale=float(data.scale[c])))
    return rows


# ----------------------------------------------------------------- conditional D(Y)

@dataclass(frozen=True)
class TemplateEnvelopeAdapter:
    """Prediction set = union over declared templates and integer clock shifts of
    template(t + s) +/- eps_model (per channel kind, native units).

    Exclusion uses the engine's own certificate form: one coordinate whose full
    predicted hull (over all templates and shifts, widened by eps_model) is disjoint
    from the observation interval. Feasibility uses an exact shift witness. Any other
    case is INDETERMINATE. All comparisons are exact rationals of the float inputs.
    """

    windows: tuple            # tuple of (label, ndarray[n_shift, N, n_channel])
    kinds: tuple
    eps_model: dict           # kind -> eps (float)

    def check(self, model: HypothesisModel, measurement: MeasurementContract) -> ConsistencyResult:
        assumptions = model.assumptions + (LABEL,)
        coords = measurement.coordinates()
        obs = measurement.intervals()           # sensor-major order, matching coordinates()
        n_t = len(measurement.timestamps_s)
        stack = np.concatenate([w for _, w in self.windows])      # (S, N, C)
        if stack.shape[1] != n_t or stack.shape[2] != len(measurement.sensors):
            return ConsistencyResult(model.name, ConsistencyStatus.INDETERMINATE,
                                     "INVALID_MODEL_CONTRACT", assumptions)
        em = [Fraction(self.eps_model[k]) for k in self.kinds]
        # Float arrays only preselect candidates; every decision is confirmed in exact rationals.
        o_lo_f = np.array([[float(obs[c * n_t + i][0]) for c in range(stack.shape[2])] for i in range(n_t)])
        o_hi_f = np.array([[float(obs[c * n_t + i][1]) for c in range(stack.shape[2])] for i in range(n_t)])
        em_f = np.array([float(e) for e in em])
        lo_f, hi_f = stack.min(axis=0), stack.max(axis=0)          # selections, exact in float
        gap = np.maximum(o_lo_f - (hi_f + em_f), (lo_f - em_f) - o_hi_f)
        tol = 1e-9 * np.maximum(1.0, np.abs(stack).max())
        for i, c in zip(*np.nonzero(gap > -tol)):
            lo, hi = Fraction(float(lo_f[i, c])) - em[c], Fraction(float(hi_f[i, c])) + em[c]
            o_lo, o_hi = obs[c * n_t + i]
            if hi < o_lo or lo > o_hi:
                proof = IntervalSeparation(coords[c * n_t + i], (str(lo), str(hi)), (str(o_lo), str(o_hi)))
                return ConsistencyResult(model.name, ConsistencyStatus.EXCLUDED,
                                         "DISJOINT_TEMPLATE_HULL", assumptions, separation=proof)
        labels = [(label, round((s - (w.shape[0] - 1) // 2) * STEP_S, 6))
                  for label, w in self.windows for s in range(w.shape[0])]
        for (label, s), traj in zip(labels, stack):
            viol = np.maximum(o_lo_f - (traj + em_f), (traj - em_f) - o_hi_f)
            if viol.max() > tol:
                continue
            if all(obs[c * n_t + i][0] <= Fraction(float(traj[i, c])) + em[c] and
                   Fraction(float(traj[i, c])) - em[c] <= obs[c * n_t + i][1]
                   for c in range(stack.shape[2]) for i in range(n_t)):
                return ConsistencyResult(model.name, ConsistencyStatus.FEASIBLE, "VERIFIED_SHIFT_WITNESS",
                                         assumptions, witness=(label, f"shift_s={s}"))
        return ConsistencyResult(model.name, ConsistencyStatus.INDETERMINATE,
                                 "NO_SINGLE_COORDINATE_SEPARATION_NO_WITNESS", assumptions)


def shifted_windows(data: CenterData, template: str, idx, bound: float) -> np.ndarray:
    v, i = data.templates[template]
    r = int(round(bound / STEP_S))
    return np.stack([v[i + k:i + k + N, idx] for k in range(-r, r + 1)])


def measurement(data: CenterData, query: str, idx, eps_obs: dict) -> MeasurementContract:
    values, j = data.queries[query]
    times = tuple(float(x) for x in data.clock[j:j + N])
    sensors = tuple(SensorRecord(data.names[c], "Center", "node" if data.kinds[c] == "pressure" else "edge",
                                 str(SID[data.names[c]]), data.kinds[c],
                                 "MPa" if data.kinds[c] == "pressure" else "kg/s", STEP_S) for c in idx)
    channels = tuple(Channel(s.sensor_id, s.unit, times, "Saved accepted Center MAT clock",
                             tuple(float(x) for x in values[j:j + N, c]),
                             tuple(float(eps_obs[data.kinds[c]]) for _ in times)) for s, c in zip(sensors, idx))
    return MeasurementContract(sensors, times, channels, f"{query} matched residual",
                               "Center source family", f"center-capture:{query}",
                               f"{LABEL}: declared hypothetical observation half-widths", 1e-9)


def dy_models(data: CenterData, query: str, idx, eps_model: dict, bound: float, universe: str):
    kinds = tuple(data.kinds[c] for c in idx)
    models = []
    for name, templates in DY_HYPOTHESES.items():
        usable = [t for t in templates if TEMPLATE_PRIMARY[t] != QUERY_PRIMARY[query]]
        if usable:
            adapter = TemplateEnvelopeAdapter(tuple((t, shifted_windows(data, t, idx, bound)) for t in usable),
                                              kinds, eps_model)
            models.append(HypothesisModel(name, adapter, (f"templates={'+'.join(usable)}",
                                                          f"clock_shift=+/-{bound}s")))
        elif universe == "full":
            models.append(HypothesisModel(name, None, ("UNSUPPORTED_AFTER_SELF_TEMPLATE_EXCLUSION",)))
    if universe == "full":
        models += [HypothesisModel(name, None, ("DECLARED_WITHOUT_ADAPTER",)) for name in DY_UNMODELLED]
    return tuple(models)


def dy_decision(data, query, group, eps_total: dict, bound, universe, split=0.5):
    idx = group_index(data, group)
    eo = {k: eps_total[k] * split for k in eps_total}
    em = {k: eps_total[k] - eo[k] for k in eps_total}
    meas = measurement(data, query, idx, eo)
    decision = diagnose(meas, dy_models(data, query, idx, em, bound, universe))
    cert = decision.certificate
    return dict(query=query, group=group, universe=universe, clock_bound_s=bound,
                eps_P_MPa=eps_total.get("pressure"), eps_F_kg_s=eps_total.get("mass_flow"),
                eps_obs_fraction=split, decision=decision.status.value, reason=decision.reason,
                selected=decision.hypothesis, consistent=list(cert.feasible), excluded=list(cert.excluded),
                indeterminate=list(cert.indeterminate),
                indeterminate_reasons={r.hypothesis: r.reason for r in cert.results
                                       if r.status is ConsistencyStatus.INDETERMINATE},
                measurement_issues=list(cert.measurement_issues), true_hypothesis=DY_TRUE[query],
                true_supported=any(t for t in DY_HYPOTHESES[DY_TRUE[query]]
                                   if TEMPLATE_PRIMARY[t] != QUERY_PRIMARY[query]),
                label=LABEL)


def thresholds(data: CenterData, query: str, hypothesis: str, group: str, bound: float):
    """Exact exclusion onset E and feasibility onset F per channel kind (native units).

    For a declared total half-width eps_k (= eps_obs + eps_model) on kind k:
      excluded  iff  some kind k has  eps_k < E_k,  E_k = max_c dist(y_c, [min_s h_c, max_s h_c])
      feasible  iff  some shift s has  eps_k >= M_k(s) for every kind,  M_k(s) = max_c |y_c - h_c(s)|.
    Both conditions are monotone in eps (exclusion non-increasing, feasibility non-decreasing),
    so E_k and F_k = min_s M_k(s) (single-kind groups) are exact onsets, not search results.
    """
    idx = group_index(data, group)
    usable = [t for t in DY_HYPOTHESES[hypothesis] if TEMPLATE_PRIMARY[t] != QUERY_PRIMARY[query]]
    if not usable:
        return None
    y = query_window(data, query, idx)
    stack = np.concatenate([shifted_windows(data, t, idx, bound) for t in usable])
    kinds = np.array([data.kinds[c] for c in idx])
    out = {}
    for kind in ("pressure", "mass_flow"):
        cols = np.flatnonzero(kinds == kind)
        if not len(cols):
            out[kind] = None
            continue
        lo, hi = stack[:, :, cols].min(axis=0), stack[:, :, cols].max(axis=0)
        yy = y[:, cols]
        # exact rational evaluation at the arg-max candidates (float preselect, exact confirm)
        gap = np.maximum(lo - yy, yy - hi)
        flat = np.argsort(gap, axis=None)[-8:]
        e = max(max(Fraction(float(lo.flat[f])) - Fraction(float(yy.flat[f])),
                    Fraction(float(yy.flat[f])) - Fraction(float(hi.flat[f]))) for f in flat)
        per_shift = []
        for s in range(stack.shape[0]):
            d = np.abs(yy - stack[s][:, cols])
            top = np.argsort(d, axis=None)[-8:]
            per_shift.append(max(abs(Fraction(float(yy.flat[f])) - Fraction(float(stack[s][:, cols].flat[f])))
                                 for f in top))
        out[kind] = dict(E=max(e, Fraction(0)), F=min(per_shift), M=per_shift)
    return out


# ----------------------------------------------------------------------------- driver

def run(base: Path, out: Path, repo: Path) -> dict:
    out.mkdir(parents=True, exist_ok=False)
    data = load(base)
    manifest = dict(
        experiment="center_evidence_enhancement_v1", label=LABEL,
        baseline_commit="6fee8a0a58a0773ad0ac6f0d5eb1f71ae4d984ed", baseline_tag="h2prism-center-baseline-v1",
        capture_raw_sha256=data.hashes, kernel="nres.rank (frozen B3) via mechanism_screen.screen",
        kernel_sha256={n: sha256_file(repo / "src/h2prism" / n) for n in
                       ("nres.py", "mechanism_screen.py", "certified_evidence.py")},
        window=dict(prefix_s=WINDOW_S, samples=N, step_s=STEP_S, anchors="controlled (retrospective) 1000 s; "
                    "TIMING 26 s; NOMINAL 25 s"),
        clock_bounds_s=CLOCK_BOUNDS_S, groups=GROUPS, near_duplicate_fraction=NEAR_DUPLICATE_FRACTION,
        exclusion_rule="drop templates whose primary capture equals the query's primary capture",
        independent_source_families=1, verified_independent_families=0,
        dy_hypotheses=DY_HYPOTHESES, dy_unmodelled=DY_UNMODELLED, ladder=LADDER,
        solver_refinement_reference=SOLVER_DELTA,
        environment=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__,
                         platform=platform.platform()),
        stop_conditions=["raw capture hash mismatch", "frozen focal margins not reproduced",
                         "engine status disagrees with closed-form threshold prediction"])
    # Gate: reproduce frozen focal mechanism margins (TAB_10) before any new analysis.
    frozen = pd.read_csv(repo / "03_results/validation/publication_final_v1/tables/TAB_10.csv")
    repro = []
    for q in ("SID213", "SID312", "SID215", "PRESSURE", "ALT", "TIMING", "NOMINAL", "QUIET"):
        r = recognition(data, q, "frozen")
        f = frozen[frozen["query"] == q].iloc[0]
        repro.append(dict(query=q, frozen_margin=float(f["mechanism_margin"]), reproduced_margin=r["margin"],
                          frozen_mechanism=f["mechanism"], reproduced_mechanism=r["predicted"],
                          match=bool(np.isclose(r["margin"], f["mechanism_margin"], rtol=1e-5, atol=0)
                                     and r["predicted"] == f["mechanism"])))
    if not all(r["match"] for r in repro):
        raise RuntimeError("frozen focal margins not reproduced")
    pd.DataFrame(repro).to_csv(out / "gate_frozen_reproduction.csv", index=False)

    rec = [recognition(data, q, c, g, b) for q in QUERY_PRIMARY for c in ("frozen", "loto", "loto_replicate")
           for g in GROUPS for b in CLOCK_BOUNDS_S]
    loc = [location_ranking(data, q, c, g, b) for q in TRUE_SITE for c in ("frozen", "loto", "loto_replicate")
           for g in GROUPS for b in CLOCK_BOUNDS_S]
    pd.DataFrame(rec).to_json(out / "recognition.json", orient="records", indent=1)
    pd.DataFrame(loc).to_json(out / "location.json", orient="records", indent=1)
    pd.DataFrame(pair_contrasts(data)).to_csv(out / "pair_contrasts.csv", index=False)
    pd.DataFrame(channel_signal(data)).to_csv(out / "channel_signal.csv", index=False)

    # Exact thresholds for every supported (query, hypothesis) pair.
    thr = []
    for q in DY_QUERIES:
        for h in DY_HYPOTHESES:
            for g in GROUPS:
                for b in CLOCK_BOUNDS_S:
                    t = thresholds(data, q, h, g, b)
                    base_row = dict(query=q, hypothesis=h, group=g, clock_bound_s=b,
                                    is_true=h == DY_TRUE[q], label=LABEL)
                    if t is None:
                        thr.append(dict(base_row, supported=False))
                        continue
                    row = dict(base_row, supported=True)
                    for kind, key in (("pressure", "P_MPa"), ("mass_flow", "F_kg_s")):
                        if t[kind] is not None:
                            row[f"E_{key}"] = float(t[kind]["E"])
                            row[f"Fz_{key}"] = float(t[kind]["F"])
                            row[f"E_{key}_exact"] = str(t[kind]["E"])
                    if t["pressure"] and t["mass_flow"]:
                        # joint feasibility needs one common shift: Pareto pairs (M_P(s), M_F(s))
                        row["joint_feasibility_pairs"] = json.dumps(
                            [[float(a), float(c)] for a, c in zip(t["pressure"]["M"], t["mass_flow"]["M"])])
                    thr.append(row)
    thr = pd.DataFrame(thr)
    thr.to_csv(out / "dy_thresholds.csv", index=False)

    # Engine runs on the declared ladder plus the solver-delta reference scenario.
    scenarios = [(n, p, f) for n, p, f in LADDER] + [("REF", SOLVER_DELTA["pressure_MPa"], SOLVER_DELTA["flow_kg_s"])]
    dec = []
    for q in DY_QUERIES:
        for g in GROUPS:
            for b in CLOCK_BOUNDS_S:
                for name, p, f in scenarios:
                    for u in ("full", "restricted"):
                        row = dy_decision(data, q, g, {"pressure": p, "mass_flow": f}, b, u)
                        row["scenario"] = name
                        dec.append(row)
    # Split invariance check: all bound on observation vs all on model, same total.
    split = []
    for q in DY_QUERIES:
        for name, p, f in scenarios:
            a = dy_decision(data, q, "all", {"pressure": p, "mass_flow": f}, 1.0, "restricted", 0.5)
            c = dy_decision(data, q, "all", {"pressure": p, "mass_flow": f}, 1.0, "restricted", 1.0)
            split.append(dict(query=q, scenario=name, same=(a["decision"], a["excluded"], a["consistent"]) ==
                              (c["decision"], c["excluded"], c["consistent"])))
    pd.DataFrame(split).to_csv(out / "gate_split_invariance.csv", index=False)
    dec = pd.DataFrame(dec)
    # Closed-form agreement gate.
    agree = []
    for r in dec.itertuples():
        for h in DY_HYPOTHESES:
            t = thr[(thr["query"] == r.query) & (thr.hypothesis == h) & (thr.group == r.group) &
                    (thr.clock_bound_s == r.clock_bound_s)].iloc[0]
            if not t.supported:
                continue
            excl = any(pd.notna(t.get(f"E_{k}")) and eps < t[f"E_{k}"]
                       for k, eps in (("P_MPa", r.eps_P_MPa), ("F_kg_s", r.eps_F_kg_s)))
            if pd.notna(t.get("joint_feasibility_pairs")):
                feas = any(r.eps_P_MPa >= a and r.eps_F_kg_s >= c for a, c in json.loads(t.joint_feasibility_pairs))
            elif pd.notna(t.get("Fz_P_MPa")):
                feas = r.eps_P_MPa >= t.Fz_P_MPa
            else:
                feas = r.eps_F_kg_s >= t.Fz_F_kg_s
            predicted = "EXCLUDED" if excl else "FEASIBLE" if feas else "INDETERMINATE"
            observed = ("EXCLUDED" if h in r.excluded else "FEASIBLE" if h in r.consistent else "INDETERMINATE")
            agree.append(dict(query=r.query, group=r.group, scenario=r.scenario, universe=r.universe,
                              clock_bound_s=r.clock_bound_s, hypothesis=h, predicted=predicted,
                              engine=observed, match=predicted == observed))
    agree = pd.DataFrame(agree)
    agree.to_csv(out / "gate_engine_vs_closed_form.csv", index=False)
    dec.to_json(out / "dy_decisions.json", orient="records", indent=1)
    gates = dict(frozen_reproduction=all(r["match"] for r in repro),
                 engine_vs_closed_form=bool(agree["match"].all()), n_engine_checks=int(len(agree)),
                 split_invariance=bool(pd.DataFrame(split)["same"].all()))
    manifest["gates"] = gates
    (out / "execution_manifest.json").write_text(json.dumps(manifest, indent=2, default=str), encoding="utf8")
    normalize_lf(out)
    return gates


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace", type=Path, default=os.environ.get("H2PRISM_CENTER_WORKSPACE"),
                   help="Center capture workspace (contains work/ and outputs/); or H2PRISM_CENTER_WORKSPACE")
    p.add_argument("--output", type=Path, required=True, help="fresh output directory")
    p.add_argument("--repository", type=Path, default=Path("."))
    a = p.parse_args()
    if a.workspace is None or not Path(a.workspace).is_dir():
        raise SystemExit("Center capture workspace not found; pass --workspace or set H2PRISM_CENTER_WORKSPACE")
    print(json.dumps(run(Path(a.workspace), a.output, a.repository), indent=2))


if __name__ == "__main__":
    main()
