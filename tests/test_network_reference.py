from dataclasses import replace
from fractions import Fraction as Q
from itertools import product

import pytest

from h2prism.certified_evidence import DecisionStatus, diagnose
from h2prism.gas_physics import orifice_mass_flow
from h2prism.network_reference import choked_factor, localize, nodal_rates
from h2prism.phase3 import REGIONS, benchmark, build, digest, replay
from h2prism.physical_reference import BoundStatus


@pytest.mark.parametrize("case, status, level", [
    ("normal", "SPECIFIC", "L0"), ("unique", "SPECIFIC", "L2"),
    ("reduced", "AMBIGUOUS", "L0"), ("flow_only", "AMBIGUOUS", "L0"),
    ("wide", "AMBIGUOUS", "L0"), ("spatial_alias", "AMBIGUOUS", "L1"),
    ("unsupported", "UNRESOLVED", "L0"), ("mismatch", "UNRESOLVED", "L0"),
    ("joint_gap", "UNRESOLVED", "L0"), ("severe", "SPECIFIC", "L2"),
])
def test_localization_and_replay(case, status, level):
    payload, _ = build(case)
    assert payload["decision"]["status"] == status
    assert payload["localization"]["level"] == level
    assert replay(payload)
    if case == "mismatch":
        assert len(payload["decision"]["certificate"]["excluded"]) == 4
    if case == "spatial_alias":
        assert payload["localization"]["candidates"] == ["LEAK_A", "LEAK_B"]


def test_internal_flows_cancel_and_reverse():
    measurement, models, _, _ = benchmark("normal")
    net = models[0].adapter.network.topology
    assert nodal_rates(net, (6, -2, -2, -2), (2, 2, 2)) == (0, 0, 0, 0)
    reversed_rates = nodal_rates(net, (6, -2, -2, -1), (-2, 2, 2))
    assert reversed_rates == (4, -4, 0, 1)
    assert sum(reversed_rates) == 1
    network = models[0].adapter.network
    zero = replace(network, storage=tuple(replace(s, external_rate=replace(s.external_rate, interval=(0, 0)))
                                         for s in network.storage),
                   transfers=tuple(replace(t, rate=replace(t.rate, interval=(0, 0))) for t in network.transfers))
    assert zero.evaluate(measurement, None)[3] == [(100,) * 4] * 3


def test_choked_law_mass_and_refinement():
    measurement, models, _, _ = benchmark("unique")
    adapter = models[1].adapter
    network, region = adapter.network, adapter.region
    factor = choked_factor(network.gas, 300)
    assert factor == Q(1, 200)
    at_initial = Q(100000) * factor * Q(1, 1024) * Q(3, 4)
    assert float(at_initial) == pytest.approx(
        orifice_mass_flow(100000, 10000, 300, 1 / 1024, network.gas, 0.75))
    assert orifice_mass_flow(100000, 100000, 300, 1 / 1024, network.gas) == 0
    assert orifice_mass_flow(100000, 80000, 300, 1 / 1024, network.gas) < float(at_initial / Q(3, 4))
    high = region.ambient_pressure_pa
    assert high < 100000 / 8 ** 0.5
    _, _, _, path = network.evaluate(measurement, region)
    assert sum(path[0]) - sum(path[1]) == at_initial
    assert sum(path[1]) - sum(path[2]) == at_initial * path[1][1] / 100
    half = replace(network, step_s=0.5)
    finer = replace(measurement, timestamps_s=(0, 0.5, 1, 1.5, 2))
    assert half.evaluate(finer, region)[3][-1][1] > path[-1][1]
    with pytest.raises(ValueError, match="unchoked"):
        network.evaluate(measurement, replace(region, ambient_pressure_pa=100000))
    sealed = replace(region, area=replace(region.area, interval=(0, 0)))
    assert network.evaluate(measurement, sealed)[3] == network.evaluate(measurement, None)[3]


def test_outer_enclosure_contains_independent_corner_solutions():
    measurement, models, _, _ = benchmark("unique")
    adapter = models[1].adapter
    network, region = adapter.network, adapter.region
    bounds, _, _, _ = network.evaluate(measurement, region)
    for area, cd, ext in product(region.area.interval, region.discharge_coefficient.interval,
                                 network.storage[1].external_rate.interval):
        # Closed form of the recurrence for two steps with fixed parameters.
        k = 1 - Q(5) * Q(area) * Q(cd)
        added = Q(ext) + 2
        values = [100000, 1000 * (k * 100 + added), 1000 * (k * k * 100 + (1 + k) * added)]
        assert all(a <= y <= b for y, (a, b) in zip(values, bounds[3:6]))


@pytest.mark.parametrize("edit", ("gas", "region", "clock", "bounds", "topology", "mapping"))
def test_invalid_domain_stays_indeterminate(edit):
    measurement, models, _, _ = benchmark("unique")
    adapter = models[1].adapter
    network, region = adapter.network, adapter.region
    if edit == "gas":
        network = replace(network, gas=replace(network.gas, Z=0.99))
    elif edit == "region":
        region = replace(region, storage_node="B")
    elif edit == "clock":
        network = replace(network, step_s=0.5)
    elif edit == "bounds":
        region = replace(region, area=replace(region.area, interval=None, status=BoundStatus.UNKNOWN))
    elif edit == "topology":
        network = replace(network, topology=replace(network.topology, edges=()))
    else:
        network = replace(network, sensors=network.sensors[1:])
    altered = (*models[:1], replace(models[1], adapter=replace(adapter, network=network, region=region)), *models[2:])
    decision = diagnose(measurement, altered)
    assert decision.status is DecisionStatus.UNRESOLVED
    assert "LEAK_A" in decision.certificate.indeterminate
    assert localize(decision, REGIONS).level == "L0"


def test_joint_evidence_blocks_baseline_specific():
    payload, _ = build("joint_gap")
    assert payload["conventional"]["retained"] == ["NORMAL"]
    assert payload["decision"]["certificate"]["indeterminate"] == ["NORMAL"]
    assert payload["decision"]["status"] == "UNRESOLVED"


def test_changed_configuration_fails_replay_even_with_recomputed_digest():
    payload, _ = build("unique")
    payload["models"]["NORMAL"]["network"]["storage"][0]["volume_m3"] = 31
    payload["sha256"] = digest({k: v for k, v in payload.items() if k != "sha256"})
    assert not replay(payload)


def test_missing_required_channel_blocks_specific():
    measurement, models, _, _ = benchmark("unique")
    decision = diagnose(replace(measurement, channels=measurement.channels[1:]), models)
    assert decision.status is DecisionStatus.UNRESOLVED
    assert "MISSING_SENSOR" in decision.certificate.measurement_issues
