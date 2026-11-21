from dataclasses import replace
from decimal import Decimal, localcontext
from fractions import Fraction as Q
import math

import numpy as np
import pytest

from h2prism.certified_evidence import ConsistencyStatus, diagnose
from h2prism.gas_physics import Pipe, TabulatedGas
from h2prism.joint_network import JointNetwork, solve_retention
from h2prism.phase3 import CASES, benchmark
from h2prism.phase4 import closed_pair_enclosure, comparison, physical, replay
from h2prism.pressure_reference import CapillaryReference


@pytest.mark.parametrize("case", CASES)
def test_matched_joint_sets_and_replay(case):
    record, _ = comparison(case)
    assert record["joint_sets_identical"]
    assert replay(record)
    if case == "joint_gap":
        assert record["outer_membership"]["NORMAL"] == "RETAINED"
        assert record["joint_membership"]["NORMAL"] == "EXCLUDED"
        assert record["decision"]["reason"] == "MODEL_MISMATCH"
    if case == "spatial_alias":
        assert record["localization"]["level"] == "L1"
    if case == "unsupported":
        assert record["localization"]["level"] == "L0"
    if case == "unique":
        assert record["localization"]["level"] == "L2"
        assert record["evidence_gate_ablation"]["diagnosis"] == "UNRESOLVED"


def test_rational_split_proof_and_search_budget():
    # Both inequalities cannot hold. Each is violated in a different region.
    tests = [(Q(-2, 5), Q(1)), (Q(3, 5), Q(-1))]
    point, proof = solve_retention((Q(0), Q(1)), tests, 20)
    assert point is None and len(proof.cells) > 1 and proof.covers()
    assert not replace(proof, cells=proof.cells[:-1]).covers()
    assert not replace(proof, cells=(replace(proof.cells[0], violated=("-1",)), *proof.cells[1:])).covers()
    assert solve_retention((Q(0), Q(1)), tests, 0) == (None, None)


def test_joint_witness_is_stronger_than_midpoint():
    measurement, models, _, _ = benchmark("normal")
    # An admissible nonzero shared external rate is deliberately off midpoint.
    channel = replace(measurement.channels[1], values=(100000, 100031.25, 100062.5))
    m = replace(measurement, channels=(measurement.channels[0], channel, *measurement.channels[2:]))
    model = models[0]
    assert diagnose(m, (model,)).certificate.indeterminate == ("NORMAL",)
    joint = replace(model, adapter=JointNetwork(model.adapter))
    assert diagnose(m, (joint,)).certificate.feasible == ("NORMAL",)
    assert diagnose(m, (replace(joint, adapter=JointNetwork(model.adapter, 0)),)).certificate.indeterminate


def test_unverified_measurement_and_changed_replay_fail_closed():
    record, _ = comparison("unique")
    record["decision"]["certificate"]["measurement"]["channels"][0]["unit"] = "bar"
    assert not replay(record)
    measurement, models, _, _ = benchmark("unique")
    channel = replace(measurement.channels[0], absolute_errors=())
    m = replace(measurement, channels=(channel, *measurement.channels[1:]))
    joint = tuple(replace(h, adapter=JointNetwork(h.adapter)) for h in models)
    assert all(r.status is ConsistencyStatus.INDETERMINATE for r in diagnose(m, joint).certificate.results)


def test_constant_property_laminar_reference_and_units():
    constant = lambda x: np.full((2, 2), x)
    gas = TabulatedGas(4124, [299, 301], [100000, 220000], constant(1),
                       constant(14300), constant(9e-6), constant(0.18))
    ref = CapillaryReference(gas)
    pipe = Pipe("a", "b", 20, 0.001, 0)
    p_a, p_b = 210000, 110000
    expected = math.pi * pipe.diameter ** 4 * (p_a**2 - p_b**2) / (256 * pipe.length * 9e-6 * 4124 * 300)
    assert ref.rate(pipe, p_a, p_b)["kg_s"] == pytest.approx(expected, rel=1e-12)
    assert ref.rate(pipe, p_b, p_a)["kg_s"] == pytest.approx(-expected, rel=1e-12)
    assert ref.rate(pipe, p_a, p_a)["kg_s"] == 0
    with pytest.raises(ValueError, match="pressure outside"):
        ref.rate(pipe, 210, 110)
    with pytest.raises(ValueError, match="screening"):
        ref.rate(replace(pipe, length=1), p_a, p_b)


def test_physical_benchmark_conservation_regimes_and_spatial_symmetry():
    data = physical()
    assert data["certification"].startswith("NONE")
    assert set(data["leak_checks"][p]["regime"] for p in ("100000", "170000", "220000")) == {
        "CLOSED", "UNCHOKED", "CHOKED"}
    for branches in data["results"].values():
        for state in branches.values():
            assert abs(state["balance_residual_kg_s"]) < 1e-16
            assert state["inventory_kg"] == pytest.approx(0.001 * state["density_kg_m3"])
    assert data["sensor_identifiability"]["total_inlet_is_symmetric"]
    assert data["sensor_identifiability"]["local_pressures_differ"]
    for levels in data["refinement"].values():
        assert levels[1]["max_pressure_delta_from_finest_pa"] <= levels[0]["max_pressure_delta_from_finest_pa"]


def test_exact_continuous_pair_encloses_independent_high_precision_solution():
    bounds = closed_pair_enclosure(200000, 100000, Q(1, 2), 1)
    with localcontext() as context:
        context.prec = 65
        as_decimal = lambda f: Decimal(f.numerator) / Decimal(f.denominator)
        pressure = Decimal(150000) + Decimal(50000) * Decimal("-0.5").exp()
        assert as_decimal(bounds[0][0]) <= pressure <= as_decimal(bounds[0][1])
        assert as_decimal(bounds[1][0]) <= Decimal(300000) - pressure <= as_decimal(bounds[1][1])
    assert bounds[0][0] + bounds[1][1] == 300000
    assert closed_pair_enclosure(100000, 200000, Q(1, 2), 1) == bounds[::-1]
    with pytest.raises(ValueError, match="verification domain"):
        closed_pair_enclosure(200000, 100000, 1, 2)
