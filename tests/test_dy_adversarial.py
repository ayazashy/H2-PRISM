"""Adversarial and property tests for the formal D(Y) engine with the template-envelope adapter.

Guarantees under test (assumptions stated in 03_results/integrated_validation_v2/02_design/DY_MONOTONICITY_PROOF.md):
  * removing sensors, widening observation or model bounds, or widening the admissible shift set never turns a
    FEASIBLE hypothesis into EXCLUDED/INDETERMINATE and never creates a new EXCLUDED status;
  * invalid measurements never produce SPECIFIC; tampered certificates are rejected; closed-interval boundaries hold.
"""
from dataclasses import replace
from fractions import Fraction

import numpy as np
import pytest

from h2prism.center_enhancement import STEP_S, TemplateEnvelopeAdapter
from h2prism.certified_evidence import (Channel, ConsistencyResult, ConsistencyStatus, DecisionStatus, HypothesisModel,
                                        IntervalSeparation, MeasurementContract, diagnose)
from h2prism.data_contracts import SensorRecord

KIND = {"pressure": "MPa", "mass_flow": "kg/s"}


def contract(values, eps, kinds, times=None, ids=None):
    n = values.shape[0]
    times = tuple(round(i * STEP_S, 10) for i in range(n)) if times is None else times
    ids = ids or [f"S{c}" for c in range(values.shape[1])]
    sensors = tuple(SensorRecord(ids[c], "T", "node", ids[c], k, KIND[k], STEP_S) for c, k in enumerate(kinds))
    chans = tuple(Channel(ids[c], KIND[k], times, "test clock", tuple(float(v) for v in values[:, c]),
                          tuple(float(eps[k]) for _ in times)) for c, k in enumerate(kinds))
    return MeasurementContract(sensors, times, chans, "run", "group", "src", "test bounds", 1e-9)


def models(templates, kinds, eps_model, cols=None):
    out = []
    for name, stack in templates.items():
        s = stack if cols is None else stack[:, :, cols]
        out.append(HypothesisModel(name, TemplateEnvelopeAdapter(((name, s),), tuple(kinds), eps_model), ()))
    return tuple(out)


def status(dec):
    return {r.hypothesis: r.status for r in dec.certificate.results}


ALLOWED = {ConsistencyStatus.FEASIBLE: {ConsistencyStatus.FEASIBLE},
           ConsistencyStatus.EXCLUDED: set(ConsistencyStatus),
           ConsistencyStatus.INDETERMINATE: {ConsistencyStatus.INDETERMINATE, ConsistencyStatus.FEASIBLE}}


def random_case(rng, n=12, c=4, h=3, s=3):
    kinds = ["pressure", "pressure", "mass_flow", "mass_flow"][:c]
    base = rng.normal(size=(n, c))
    templates = {f"H{i}": np.stack([base + rng.normal(scale=rng.choice([0.01, 0.3]), size=(n, c)) for _ in range(s)])
                 for i in range(h)}
    obs = base + rng.normal(scale=0.05, size=(n, c))
    return kinds, templates, obs


@pytest.mark.parametrize("seed", range(40))
def test_monotone_in_bounds_sensors_and_shifts(seed):
    rng = np.random.default_rng(seed)
    kinds, T, y = random_case(rng)
    e1 = {"pressure": 0.05, "mass_flow": 0.05}
    e2 = {k: v * 3 for k, v in e1.items()}
    base = status(diagnose(contract(y, e1, kinds), models(T, kinds, e1)))
    wider = status(diagnose(contract(y, e2, kinds), models(T, kinds, e2)))
    cols = [0, 2]
    fewer = status(diagnose(contract(y[:, cols], e1, [kinds[i] for i in cols]),
                            models(T, [kinds[i] for i in cols], e1, cols)))
    more_shifts = {k: np.concatenate([v, v + rng.normal(scale=0.2, size=v.shape)]) for k, v in T.items()}
    shifted = status(diagnose(contract(y, e1, kinds), models(more_shifts, kinds, e1)))
    for after in (wider, fewer, shifted):
        for h, s in base.items():
            assert after[h] in ALLOWED[s], (h, s, after[h])


def test_invalid_measurements_never_specific():
    rng = np.random.default_rng(1)
    kinds, T, y = random_case(rng)
    e = {"pressure": 0.5, "mass_flow": 0.5}
    y_nan = y.copy()
    y_nan[3, 1] = np.nan
    bad = [contract(y_nan, e, kinds),
           contract(y, {"pressure": -1.0, "mass_flow": 0.5}, kinds),
           contract(y, e, kinds, ids=["S0", "S0", "S2", "S3"]),
           contract(y, e, kinds, times=tuple(round(i * STEP_S, 10) for i in range(len(y) - 1)) + (99.0,))]
    for m in bad:
        d = diagnose(m, models(T, kinds, e))
        assert d.status == DecisionStatus.UNRESOLVED and d.reason == "INVALID_MEASUREMENT"
        assert all(r.status == ConsistencyStatus.INDETERMINATE for r in d.certificate.results)


def test_closed_boundary_and_exact_zero_width():
    kinds = ["pressure"]
    y = np.zeros((5, 1))
    T = {"H": np.full((1, 5, 1), 0.3)}
    e = {"pressure": 0.15}
    assert diagnose(contract(y, e, kinds), models(T, kinds, e)).status == DecisionStatus.SPECIFIC     # |0-0.3| = 0.15 + 0.15
    e0 = {"pressure": 0.0}
    assert status(diagnose(contract(y, e0, kinds), models({"H": np.zeros((1, 5, 1))}, kinds, e0)))["H"] == ConsistencyStatus.FEASIBLE
    d = diagnose(contract(y + 1e-12, e0, kinds), models({"H": np.zeros((1, 5, 1))}, kinds, e0))
    assert d.certificate.results[0].status == ConsistencyStatus.EXCLUDED


def test_contradictory_sensors_yield_model_mismatch_not_specific():
    kinds = ["pressure", "pressure"]
    T = {"A": np.stack([np.column_stack([np.zeros(6), np.zeros(6)])]),
         "B": np.stack([np.column_stack([np.ones(6), np.ones(6)])])}
    y = np.column_stack([np.zeros(6), np.ones(6)])      # sensor 0 says A, sensor 1 says B
    e = {"pressure": 0.1}
    d = diagnose(contract(y, e, kinds), models(T, kinds, e))
    assert d.status == DecisionStatus.UNRESOLVED and d.reason == "MODEL_MISMATCH"


class _TamperedAdapter:
    def check(self, model, measurement):
        c = measurement.coordinates()[0]
        lo, hi = measurement.intervals()[0]
        return ConsistencyResult(model.name, ConsistencyStatus.EXCLUDED, "FORGED", (),
                                 separation=IntervalSeparation(c, (str(lo), str(hi)), (str(lo), str(hi))))


def test_forged_exclusion_certificate_is_rejected():
    kinds = ["pressure"]
    y = np.zeros((4, 1))
    e = {"pressure": 0.1}
    m = contract(y, e, kinds)
    d = diagnose(m, (HypothesisModel("X", _TamperedAdapter(), ()),) + models({"H": np.zeros((1, 4, 1))}, kinds, e))
    r = {x.hypothesis: x for x in d.certificate.results}
    assert r["X"].status == ConsistencyStatus.INDETERMINATE and r["X"].reason == "INVALID_ADAPTER_RESULT"
    assert d.status == DecisionStatus.UNRESOLVED       # an indeterminate rival blocks SPECIFIC
