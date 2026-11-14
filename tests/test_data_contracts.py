"""Data, topology and sensor contracts: structural validity, missing != zero, grouped-partition integrity."""

import numpy as np

from h2prism import data_contracts as dc

NET = dc.NetworkRecord("N1", ("S", "J1", "D1"), (("P1", "S", "J1"), ("P2", "J1", "D1")), "H2NET_V1_CANDIDATE",
                       {"version": "gas_composition/0.1", "mole_fractions": {"H2": 1.0}})
NETS = {"N1": NET}


def _run(rid, group, label="LEAK", onset=10.0, ancestry=()):
    return dc.RunRecord(rid, "N1", group, label, onset, {"mole_fractions": {"H2": 1.0}},
                        {"generator": "g", "file_sha256": "ab"}, tuple(ancestry))


def test_valid_records_pass():
    s = dc.SensorRecord("PT-J1", "N1", "node", "J1", "pressure", "MPa", 0.1)
    assert dc.validate_network(NET) == [] and dc.validate_sensors([s], NETS) == [] and dc.validate_run(_run("r1", "g1"), NETS) == []


def test_sensor_identity_location_and_units_are_enforced():
    bad = [dc.SensorRecord("PT-X", "N1", "node", "J9", "pressure", "MPa", 0.1),
           dc.SensorRecord("FT-1", "N1", "edge", "P1", "mass_flow", "MPa", 0.1),
           dc.SensorRecord("FT-1", "N1", "edge", "P1", "mass_flow", "kg/s", 0.0)]
    v = dc.validate_sensors(bad, NETS)
    assert any("J9" in m for m in v) and any("unit" in m for m in v) and any("duplicate" in m for m in v)
    assert any("sampling" in m for m in v)


def test_runs_need_onset_provenance_and_known_network():
    assert any("onset" in m for m in dc.validate_run(_run("r", "g", onset=None), NETS))
    assert any("NORMAL has no onset" in m for m in dc.validate_run(_run("r", "g", label="NORMAL"), NETS))
    r = dc.RunRecord("r", "N9", "g", "NORMAL", None, {"H2": 1}, {"generator": "g"})
    v = dc.validate_run(r, NETS)
    assert any("unknown network" in m for m in v) and any("file_sha256" in m for m in v)


def test_missing_is_not_zero():
    vals = np.array([1.0, 0.0, np.nan, 0.0])
    avail = np.array([True, False, False, True])
    assert dc.missing_is_not_zero(vals, avail) == [1]        # zero at an unavailable sample; NaN is correct; 0 when available is a reading


def test_partition_integrity_detects_group_and_ancestry_leakage():
    runs = [_run("a", "g1"), _run("b", "g1"), _run("c", "g2", ancestry=["a"]), _run("d", "g3")]
    part = {"a": "TRAIN", "b": "TEST", "c": "TEST"}
    v = dc.check_partition_integrity(runs, part)
    assert any("g1 spans" in m for m in v) and any("ancestor a" in m for m in v) and any("d: not assigned" in m for m in v)
    ok = {"a": "TRAIN", "b": "TRAIN", "c": "TRAIN", "d": "TEST"}
    assert dc.check_partition_integrity(runs, ok) == []


def test_shared_non_run_ancestry_cannot_cross_partitions():
    """Two scenario families with the same deterministic initial state (ancestor 'IS:abc', not itself a run) must not be
    split across partitions even when their independence groups differ."""
    runs = [_run("a", "fam1", ancestry=["IS:abc"]), _run("b", "fam2", ancestry=["IS:abc"]), _run("c", "fam3", ancestry=["IS:def"])]
    bad = dc.check_partition_integrity(runs, {"a": "TRAIN", "b": "CONFIRMATION", "c": "TRAIN"})
    assert any("shared ancestor IS:abc" in m for m in bad)
    assert dc.check_partition_integrity(runs, {"a": "TRAIN", "b": "TRAIN", "c": "CONFIRMATION"}) == []
