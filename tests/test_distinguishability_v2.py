"""
Constructed counterexamples for Distinguishability v2 (02_methodology/DISTINGUISHABILITY_V2.md, section 7).

Each test states the invariant and WHY that outcome is required before asserting it. Synthetic data only.
Group = one independent scenario; its windows are consecutive in time (30 s stride, 60 s windows) and therefore
overlap; features are the group's centre plus white noise unless a test says otherwise.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from h2prism.distinguishability import DConfig, EmpiricalSupport
from h2prism.distinguishability_v2 import (AMBIGUITY_SET, CONFLICT, DEGENERATE, DET_DETECTED, DET_NOT, DET_UNDEF,
                                           HYP_NOT_SUPPORTED, INSUFFICIENT, INVALID, NOT_SEPARATED, SEPARATED, SPECIFIC,
                                           SUPPORTED, UNRESOLVED, UNSUPPORTED, UNTESTABLE, DistinguishabilityV2,
                                           V2Config, decide, matched_selection)
from h2prism.position_map import apply_position_map

P = 6


def make_ref(spec, n=40, sd=1.0, seed=0, p=P):
    """spec: list of (group_id, class, centre_vector_or_scalar)."""
    rng = np.random.default_rng(seed)
    X, y, g, t = [], [], [], []
    for gid, cls, ctr in spec:
        c = np.full(p, ctr, float) if np.isscalar(ctr) else np.asarray(ctr, float)
        X.append(c + rng.normal(0, sd, (n, p)))
        y += [cls] * n
        g += [gid] * n
        t += list(np.arange(n) * 30.0)
    return np.vstack(X), np.array(y, object), np.array(g, object), np.array(t)


def fit(spec, classes, cfg=V2Config(), **kw):
    X, y, g, t = make_ref(spec, **kw)
    return DistinguishabilityV2(cfg).fit(X, y, g, t, classes), (X, y, g, t)


def q(vec, p=P):
    return np.full((1, p), vec, float) if np.isscalar(vec) else np.atleast_2d(np.asarray(vec, float))


NL = ["NORMAL", "LEAK"]
SEP_SPEC = [("N1", "NORMAL", 0), ("N2", "NORMAL", 0.3), ("N3", "NORMAL", -0.3),
            ("L1", "LEAK", 12), ("L2", "LEAK", 12.3), ("L3", "LEAK", 11.7)]


# 1 ------------------------------------------------------------------------------------------------------------------
def test_01_confident_wrong_classifier_is_not_issued():
    """x sits among three NORMAL scenarios, far from LEAK; classifier says LEAK with confidence 0.99.
    Required: no SPECIFIC (neither LEAK nor a switched NORMAL); the contradiction is surfaced as an ambiguity set that
    contains both hypotheses, because evidence is a warning, not proof."""
    m, _ = fit(SEP_SPEC, NL)
    ev = m.compute(q(0.1), ["NEW"])
    d = decide(m, ev, ["LEAK"]).iloc[0]
    assert d.outcome == AMBIGUITY_SET and set(d.set.split("|")) == {"NORMAL", "LEAK"}
    assert d.reason in ("EVENT_PREDICTED_BUT_NOT_DETECTABLE", CONFLICT)


# 2 ------------------------------------------------------------------------------------------------------------------
def test_02_agreement_from_one_duplicated_scenario_is_not_evidence():
    """Class LEAK has ONE scenario whose windows surround x (200 near-duplicates); NORMAL has three scenarios far away.
    Original D(x) sees 25 LEAK neighbours (D = 1). v2 must refuse: one scenario cannot corroborate LEAK (m = 2), so
    LEAK is INSUFFICIENT_EVIDENCE, its distance is undefined (NaN, not 0) and the decision is UNRESOLVED."""
    spec = [("L1", "LEAK", 5.0), ("N1", "NORMAL", -10), ("N2", "NORMAL", -10.2), ("N3", "NORMAL", -9.8)]
    X, y, g, t = make_ref(spec, n=200, sd=0.2)
    m = DistinguishabilityV2().fit(X, y, g, t, NL)
    ev = m.compute(q(5.0), ["NEW"]).iloc[0]
    assert ev["state_LEAK"] == INSUFFICIENT and np.isnan(ev["D_LEAK"])
    d = decide(m, m.compute(q(5.0), ["NEW"]), ["LEAK"]).iloc[0]
    assert d.outcome == UNRESOLVED and d.reason == HYP_NOT_SUPPORTED
    es = EmpiricalSupport(DConfig(k=25, exclude_query_family=False)).fit(X, y, g, g, NL)
    assert float(es.compute(q(5.0)).D.iloc[0]) == pytest.approx(1.0)   # the original statistic claims full agreement


# 3 ------------------------------------------------------------------------------------------------------------------
def test_03_genuinely_overlapping_hypotheses_are_not_separated():
    """NORMAL and LEAK scenarios are drawn from the SAME distribution. Expected M = 0 with spread of order one
    resolution unit, so with tau = 1 most queries must be NOT_SEPARATED and receive an ambiguity set with both."""
    spec = [(f"N{i}", "NORMAL", 0) for i in range(3)] + [(f"L{i}", "LEAK", 0) for i in range(3)]
    m, _ = fit(spec, NL, cfg=V2Config(tau=1.0), seed=3)
    rng = np.random.default_rng(9)
    Q = rng.normal(0, 1, (200, P))
    ev = m.compute(Q, ["NEW"] * 200)
    st = [m.margin(r, "LEAK")[1] for _, r in ev.iterrows()]
    assert np.mean([s == NOT_SEPARATED for s in st]) >= 0.8
    d = decide(m, ev, ["LEAK"] * 200)
    assert not (d.outcome == SPECIFIC).any() or (d.outcome == SPECIFIC).mean() < 0.2


# 4 ------------------------------------------------------------------------------------------------------------------
def test_04_distinct_hypotheses_are_separated_and_issued():
    """Class centres 12 resolution units apart: a query at the LEAK centre must be SEPARATED with M >> tau, and a
    classifier label LEAK must be SPECIFIC-eligible."""
    m, _ = fit(SEP_SPEC, NL)
    ev = m.compute(q(12.0), ["NEW"])
    mm, st = m.margin(ev.iloc[0], "LEAK")
    assert st == SEPARATED and mm > 5
    assert decide(m, ev, ["LEAK"]).iloc[0].outcome == SPECIFIC


# 5 ------------------------------------------------------------------------------------------------------------------
def test_05_visible_leak_predicted_normal_is_flagged():
    """x is a clearly visible leak (at the LEAK centre); the classifier says NORMAL. With three NORMAL scenarios the
    detectability test is defined and must say DETECTED; the decision must be an ambiguity set {NORMAL, LEAK}, never a
    SPECIFIC NORMAL and never a switched SPECIFIC LEAK."""
    m, _ = fit(SEP_SPEC, NL)
    ev = m.compute(q(12.0), ["NEW"])
    assert ev.iloc[0].detectability == DET_DETECTED
    d = decide(m, ev, ["NORMAL"]).iloc[0]
    assert d.outcome == AMBIGUITY_SET and set(d.set.split("|")) == {"NORMAL", "LEAK"}


# 6 ------------------------------------------------------------------------------------------------------------------
def test_06_weak_leak_overlapping_normal_is_not_detectable():
    """Weak-leak scenarios sit at the NORMAL operating point (as found for the G4/G5 weak runs). A LEAK prediction for a
    window there must be reported as NOT_DETECTED against NORMAL and must not be SPECIFIC."""
    spec = [("N1", "NORMAL", 0), ("N2", "NORMAL", 0.1), ("N3", "NORMAL", -0.1),
            ("W1", "LEAK", 0.05), ("W2", "LEAK", -0.05)]
    m, _ = fit(spec, NL)
    ev = m.compute(q(0.0), ["NEW"])
    assert ev.iloc[0].detectability == DET_NOT
    d = decide(m, ev, ["LEAK"]).iloc[0]
    assert d.outcome == AMBIGUITY_SET and set(d.set.split("|")) == {"NORMAL", "LEAK"}


# 7 ------------------------------------------------------------------------------------------------------------------
def test_07_cross_topology_offset_larger_than_event_signature_is_out_of_support():
    """Reference topology: NORMAL at 0, LEAK at +3 (small signature). The query is a NORMAL window of another
    configuration whose operating point is shifted by +40 (offset >> signature). It is nearer LEAK than NORMAL, so the
    original D(x) votes LEAK with D = 1; v2 must flag OUT_OF_SUPPORT and stay UNRESOLVED instead of issuing LEAK."""
    spec = [("N1", "NORMAL", 0), ("N2", "NORMAL", 0.2), ("N3", "NORMAL", -0.2),
            ("L1", "LEAK", 3), ("L2", "LEAK", 3.2), ("L3", "LEAK", 2.8)]
    m, (X, y, g, t) = fit(spec, NL)
    ev = m.compute(q(40.0), ["NEW"])
    assert bool(ev.iloc[0].out_of_support)
    assert decide(m, ev, ["LEAK"]).iloc[0].outcome == UNRESOLVED
    es = EmpiricalSupport(DConfig(k=25, exclude_query_family=False)).fit(X, y, g, g, NL)
    r = es.compute(q(40.0)).iloc[0]
    assert r.top_class == "LEAK" and float(r.D) == pytest.approx(1.0)


# 8 ------------------------------------------------------------------------------------------------------------------
def test_08_missing_support_for_a_competitor_is_not_evidence_against_it():
    """NORMAL has ONE scenario (as in the current data), LEAK three. For a LEAK prediction there is no eligible competitor:
    the margin is UNTESTABLE (undefined), NORMAL is INSUFFICIENT_EVIDENCE (not UNSUPPORTED, not 'far'), detectability is
    UNDEFINED (never NOT_DETECTED), and the decision is UNRESOLVED. A class with zero scenarios is UNSUPPORTED."""
    spec = [("N1", "NORMAL", 0), ("L1", "LEAK", 12), ("L2", "LEAK", 12.2), ("L3", "LEAK", 11.8)]
    m, _ = fit(spec, ["NORMAL", "LEAK", "COMPRESSOR_FAULT"])
    ev = m.compute(q(12.0), ["NEW"])
    r = ev.iloc[0]
    assert r.state_NORMAL == INSUFFICIENT and np.isnan(r.D_NORMAL)
    assert r.state_COMPRESSOR_FAULT == UNSUPPORTED and r.n_groups_COMPRESSOR_FAULT == 0
    assert r.detectability == DET_UNDEF
    mm, st = m.margin(r, "LEAK")
    assert st == UNTESTABLE and np.isnan(mm)
    assert decide(m, ev, ["LEAK"]).iloc[0].outcome == UNRESOLVED


def test_08b_own_group_never_counts_as_support():
    """A query from scenario N1 must not be supported by N1 itself (replicas share the independence group)."""
    spec = [("N1", "NORMAL", 0), ("N2", "NORMAL", 0.2), ("L1", "LEAK", 12), ("L2", "LEAK", 12.1)]
    m, _ = fit(spec, NL)
    r = m.compute(q(0.0), ["N1"]).iloc[0]
    assert r.n_groups_NORMAL == 1 and r.state_NORMAL == INSUFFICIENT


# 9 ------------------------------------------------------------------------------------------------------------------
def test_09_out_of_distribution_is_unresolved():
    """A query far from every reference scenario (beyond the leave-one-group-out 99th percentile) is OUT_OF_SUPPORT
    regardless of classifier confidence."""
    m, _ = fit(SEP_SPEC, NL)
    ev = m.compute(q(-80.0), ["NEW"])
    assert bool(ev.iloc[0].out_of_support)
    assert decide(m, ev, ["NORMAL"]).iloc[0].outcome == UNRESOLVED


# 10 -----------------------------------------------------------------------------------------------------------------
def test_10_disagreement_never_switches_the_specific_label():
    """Evidence separates LEAK from the classifier's NORMAL... but detectability is switched off by giving only two
    NORMAL scenarios (detectability needs m + 1 = 3), so the pure separability conflict path is exercised.
    Required: CONFLICT -> ambiguity set {NORMAL, LEAK}; a SPECIFIC LEAK would replace one unverified diagnosis by another."""
    spec = [("N1", "NORMAL", 0), ("N2", "NORMAL", 0.2), ("L1", "LEAK", 12), ("L2", "LEAK", 12.2)]
    m, _ = fit(spec, NL)
    ev = m.compute(q(12.0), ["NEW"])
    assert ev.iloc[0].detectability == DET_UNDEF
    d = decide(m, ev, ["NORMAL"]).iloc[0]
    assert d.separability_state == CONFLICT and d.outcome == AMBIGUITY_SET
    assert set(d.set.split("|")) == {"NORMAL", "LEAK"} and d.outcome != SPECIFIC


# 11 -----------------------------------------------------------------------------------------------------------------
def test_11_temporal_autocorrelation_and_duplication():
    """(a) Windows of one scenario are autocorrelated (random walk). The resolution s uses only non-overlapping windows,
    so it must exceed the naive nearest-neighbour distance that includes the overlapping neighbour.
    (b) Adding exact duplicate windows to a scenario must leave every class distance and margin unchanged: a scenario
    counts once, however many windows it has."""
    rng = np.random.default_rng(1)
    X, y, g, t = [], [], [], []
    for gid, cls, ctr in [("N1", "NORMAL", 0), ("N2", "NORMAL", 1), ("N3", "NORMAL", -1),
                          ("L1", "LEAK", 15), ("L2", "LEAK", 16)]:
        walk = ctr + np.cumsum(rng.normal(0, 0.3, (60, P)), 0)
        X.append(walk); y += [cls] * 60; g += [gid] * 60; t += list(np.arange(60) * 30.0)
    X, y, g, t = np.vstack(X), np.array(y, object), np.array(g, object), np.array(t)
    m = DistinguishabilityV2().fit(X, y, g, t, NL)
    Z = m.Z_
    naive = []
    for gg in set(g):
        d = np.sqrt(((Z[g == gg][:, None] - Z[g == gg][None]) ** 2).sum(-1)) / np.sqrt(m.p_)
        np.fill_diagonal(d, np.inf)
        naive += list(d.min(1))
    assert m.s_ > np.median(naive)
    ev1 = m.compute(q(5.0), ["NEW"])
    dup = np.flatnonzero(g == "L1")
    m2 = DistinguishabilityV2().fit(np.vstack([X, X[dup]]), np.concatenate([y, y[dup]]), np.concatenate([g, g[dup]]),
                                    np.concatenate([t, t[dup]]), NL)
    ev2 = m2.compute(q(5.0), ["NEW"])
    # scaling statistics change slightly with the duplicated rows; compare in the SAME scaling by refitting the scale
    m2.med_, m2.scale_, m2.Z_ = m.med_, m.scale_, np.vstack([m.Z_, m.Z_[dup]])
    m2.s_ = m.s_
    ev2 = m2.compute(q(5.0), ["NEW"])
    assert ev1.D_LEAK.iloc[0] == pytest.approx(ev2.D_LEAK.iloc[0])
    assert ev1.D_NORMAL.iloc[0] == pytest.approx(ev2.D_NORMAL.iloc[0])


# 12 -----------------------------------------------------------------------------------------------------------------
def test_12_non_equivalent_sensor_positions_are_not_pooled():
    """Topology B logs physical sensor P under the name PS6 and a different sensor Q (value 100) under PS5. Pooled by
    name, a B window in the same physical state as the A reference looks out of support; read through the position map,
    it is in support. The test asserts both, so pooling non-equivalent sensors is shown to manufacture a shift."""
    rng = np.random.default_rng(2)
    rows = []
    for gid, cls, ctr in [("N1", "NORMAL", 0), ("N2", "NORMAL", 0.2), ("N3", "NORMAL", -0.2),
                          ("L1", "LEAK", 10), ("L2", "LEAK", 10.2)]:
        for i in range(30):
            rows.append({"topology": "A", "g": gid, "y": cls, "t": i * 30.0,
                         "PS5__mean": ctr + rng.normal(0, 1), "PS6__mean": 50 + rng.normal(0, 1),
                         "PS1__mean": ctr + rng.normal(0, 1)})
    ref = pd.DataFrame(rows)
    qb = pd.DataFrame([{"topology": "B", "PS5__mean": 100.0, "PS6__mean": 0.0, "PS1__mean": 0.0}])
    feats = ["PS5__mean", "PS1__mean"]
    m = DistinguishabilityV2().fit(ref[feats].to_numpy(), ref.y, ref.g, ref.t, NL)
    assert bool(m.compute(qb[feats].to_numpy(), ["NEW"]).iloc[0].out_of_support)   # pooled by name
    pm = pd.DataFrame({"canonical_channel": ["PS5", "PS5", "PS1", "PS1"], "topology": ["A", "B", "A", "B"],
                       "source_channel": ["PS5", "PS6", "PS1", "PS1"]})
    refm = apply_position_map(ref, pm, ["mean"])
    qm = apply_position_map(qb, pm, ["mean"])
    m2 = DistinguishabilityV2().fit(refm[feats].to_numpy(), ref.y, ref.g, ref.t, NL)
    assert not bool(m2.compute(qm[feats].to_numpy(), ["NEW"]).iloc[0].out_of_support)   # position-matched


# 13 -----------------------------------------------------------------------------------------------------------------
def test_13_identical_class_conditional_evidence_gives_zero_margin():
    """LEAK scenarios are exact copies of NORMAL scenarios (same windows, different labels). For any query D_LEAK equals
    D_NORMAL exactly, so M = 0: NOT_SEPARATED, and the decision must contain both classes."""
    X, y, g, t = make_ref([("N1", "NORMAL", 0), ("N2", "NORMAL", 1), ("N3", "NORMAL", -1)])
    X2 = np.vstack([X, X])
    y2 = np.concatenate([y, np.array(["LEAK"] * len(y), object)])
    g2 = np.concatenate([g, np.array([f"L_{v}" for v in g], object)])
    m = DistinguishabilityV2().fit(X2, y2, g2, np.concatenate([t, t]), NL)
    ev = m.compute(q(0.3), ["NEW"])
    r = ev.iloc[0]
    assert r.D_NORMAL == pytest.approx(r.D_LEAK)
    mm, st = m.margin(r, "LEAK")
    assert mm == pytest.approx(0.0) and st == NOT_SEPARATED
    assert decide(m, ev, ["LEAK"]).iloc[0].outcome != SPECIFIC


# 14 -----------------------------------------------------------------------------------------------------------------
def test_14_degenerate_scales_ties_and_undefined_states():
    """(a) All features constant: fit must refuse (no evidence exists). (b) Constant columns are dropped and counted.
    (c) One window per scenario: no within-scenario resolution exists, so margins are DEGENERATE (undefined, not 0) and
    the decision is UNRESOLVED. (d) Non-finite query features: INVALID -> UNRESOLVED. (e) A group mixing classes is a
    data error. (f) Matched coverage that cannot be reached returns None (NOT_ESTIMABLE), never a forced selection."""
    Xc = np.ones((20, 3))
    with pytest.raises(ValueError):
        DistinguishabilityV2().fit(Xc, ["NORMAL"] * 20, ["N1"] * 20, np.arange(20) * 30.0, NL)
    X, y, g, t = make_ref(SEP_SPEC)
    Xk = np.hstack([X, np.full((len(X), 1), 7.0)])
    mk = DistinguishabilityV2().fit(Xk, y, g, t, NL)
    assert mk.n_dropped_ == 1
    one = [(f"N{i}", "NORMAL", i * 0.1) for i in range(3)] + [(f"L{i}", "LEAK", 10 + i * 0.1) for i in range(3)]
    X1, y1, g1, t1 = make_ref(one, n=1)
    m1 = DistinguishabilityV2().fit(X1, y1, g1, t1, NL)
    assert m1.s_ is None
    ev1 = m1.compute(q(10.0), ["NEW"])
    assert m1.margin(ev1.iloc[0], "LEAK")[1] == DEGENERATE
    assert decide(m1, ev1, ["LEAK"]).iloc[0].outcome == UNRESOLVED
    m, _ = fit(SEP_SPEC, NL)
    bad = q(12.0).copy(); bad[0, 0] = np.nan
    evb = m.compute(bad, ["NEW"])
    assert m.margin(evb.iloc[0], "LEAK")[1] == INVALID and decide(m, evb, ["LEAK"]).iloc[0].outcome == UNRESOLVED
    with pytest.raises(ValueError):
        DistinguishabilityV2().fit(X[:4], ["NORMAL", "LEAK", "NORMAL", "LEAK"], ["G"] * 4, np.arange(4) * 60.0, NL)
    mask, info = matched_selection([0.9, 0.8, 0.7, 0.6], [True, False, False, False], ["a", "b", "c", "d"], 0.6, "s")
    assert mask is None and info["n_eligible_for_specific"] == 1


def test_15_detectability_requires_independent_normal_scenarios():
    """With m = 2, detectability needs >= 3 NORMAL scenarios (leave-one-group-out must keep m). Two scenarios: UNDEFINED.
    It must never default to NOT_DETECTED (which would assert normality without evidence)."""
    m2, _ = fit([("N1", "NORMAL", 0), ("N2", "NORMAL", 0.2), ("L1", "LEAK", 9), ("L2", "LEAK", 9.1)], NL)
    assert m2.theta_det_ is None
    assert set(m2.compute(q(0.0), ["NEW"]).detectability) == {DET_UNDEF}
    m3, _ = fit(SEP_SPEC, NL)
    assert m3.theta_det_ is not None
    assert m3.compute(q(0.0), ["NEW"]).iloc[0].detectability == DET_NOT


def test_16_supported_state_requires_m_groups():
    """Sufficiency is counted in independent groups, not windows: 1 group with 500 windows < 2 groups with 5 each."""
    spec = [("N1", "NORMAL", 0), ("L1", "LEAK", 10), ("L2", "LEAK", 10.1)]
    X, y, g, t = make_ref(spec, n=5)
    big = np.flatnonzero(g == "N1")
    reps = np.repeat(big, 100)
    m = DistinguishabilityV2().fit(np.vstack([X, X[reps]]), np.concatenate([y, y[reps]]), np.concatenate([g, g[reps]]),
                                   np.concatenate([t, np.arange(len(reps)) * 30.0]), NL)
    r = m.compute(q(0.0), ["NEW"]).iloc[0]
    assert r.state_NORMAL == INSUFFICIENT and r.state_LEAK == SUPPORTED
