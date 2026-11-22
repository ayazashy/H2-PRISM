from dataclasses import replace
from fractions import Fraction as Q
from hashlib import sha256

import pytest

from h2prism.data.loader import RAW_DATASET_DIR
from h2prism.phase2 import MODEL, MODEL_DIR, PARQUET
from h2prism.phase5 import (
    EvidenceBasis, ablations, available_source_bounds, clock_index, independent_eligibility,
    physical_eligibility, physical_matrix, reconcile_source,
)
from h2prism.phase3 import source_report
from h2prism.steady_enclosure import Isotherm, junction_bracket


def test_exact_quadrature_and_ratio_bounds_against_affine_p_squared():
    table = Isotherm(("100000", "175000", "220000"), ("1", "1", "1"),
                     ("1/100000",) * 3, "4000", "300")
    a, b = 105000, 220000
    expected = Q(b*b-a*a, 24)
    lower, upper = table.integrals(a, b, 7)
    assert lower <= expected <= upper
    ratio = Q(99, 100), Q(101, 100)
    lo, hi = junction_bracket(table, b, a, ratio, panels=4)
    # The exact root decreases with the outlet/inlet conductance ratio.
    root_squared = lambda r: (b*b + r*a*a)/(1+r)
    assert lo**2 <= root_squared(ratio[1]) <= root_squared(ratio[0]) <= hi**2
    with pytest.raises(ValueError, match="domain"):
        junction_bracket(table, 230000, a, (1, 1), panels=1)
    with pytest.raises(ValueError, match="domain"):
        replace(table, viscosity_pa_s=("0",)*3).integrals(a, b)
    with pytest.raises(ValueError, match="domain"):
        junction_bracket(table, b, a, (1, 0))


def test_measured_values_do_not_default_model_discrepancy_to_zero():
    bounds = available_source_bounds()
    assert len(physical_eligibility(bounds, MODEL)) == 11
    valid_pressure = replace(bounds[0], interval=(-1, 1), basis=EvidenceBasis.CALIBRATED,
                             reference="reference calibration fixture")
    reasons = physical_eligibility((valid_pressure, *bounds[1:]), MODEL)
    assert "pressure:MISSING" not in reasons
    assert "model_discrepancy:MISSING" in reasons
    for update, code in [
        ({"interval": (2, 1)}, "INVALID"),
        ({"interval": (0, float("inf"))}, "INVALID"),
        ({"domain": "other domain"}, "INVALID"),
        ({"unit": "MPa"}, "INVALID"),
        ({"basis": "made up"}, "INVALID"),
        ({"basis": EvidenceBasis.ASSUMED}, "UNVERIFIED"),
    ]:
        assert f"pressure:{code}" in physical_eligibility((replace(valid_pressure, **update), *bounds[1:]), MODEL)
    with pytest.raises(ValueError, match="duplicate"):
        physical_eligibility(bounds + (bounds[0],), MODEL)


def test_no_clock_snapping_or_alias_duplicates():
    assert list(clock_index(("0.80", "4.0000")).intersection(clock_index(("0", "1", "4")))) == [Q(4)]
    assert len(clock_index(("0", "3.99999999999999")).intersection(clock_index(("0", "4")))) == 1
    with pytest.raises(ValueError, match="clock"):
        clock_index(("0", "0.0"))


def test_archival_source_reconciliation_and_redacted_probe_record(tmp_path):
    if not (RAW_DATASET_DIR / PARQUET).exists() or not (RAW_DATASET_DIR / MODEL_DIR / "normality_gest_center.csv").exists():
        pytest.skip("official archive unavailable")
    r = reconcile_source()
    assert r["source_rows"] == 25001 and r["release_rows"] == 20000
    assert r["exact_shared_timestamps"] == 5000
    assert r["byte_identical_solver_csv_aliases"] and len(r["signals"]) == 13
    assert not r["source_run_executed"] and r["release_transformation"] == "UNKNOWN"
    probe = tmp_path / "console.txt"
    probe.write_text("MATLAB startup service error 5202\nfixture-sensitive-value", encoding="utf-8")
    report = source_report(probe)
    assert report["matlab_probe"]["log_sha256"] == sha256(probe.read_bytes()).hexdigest()
    assert "5202" in report["matlab_probe"]["outcome"]
    assert "fixture-sensitive-value" not in str(report)
    assert all(c["reference_mass_flow_direction"] == "UNKNOWN"
               for c in report["source_port_graph"]["components"])


def test_no_independent_assignment_from_archive_labels():
    evaluation = independent_eligibility()
    assert evaluation["eligible_confirmatory_families"] == 0
    assert sum(row["scenarios"] for row in evaluation["provisional_scenario_counts"]) == len(evaluation["candidate_manifest"])
    assert len({row["scenario"] for row in evaluation["candidate_manifest"]}) == len(evaluation["candidate_manifest"])
    assert not any(row["eligible_independent"] for row in evaluation["candidate_manifest"])
    assert evaluation["protocol"]["empirical_metrics"] is None


def test_physical_model_scope_and_quadrature_refinement():
    matrix = physical_matrix()
    assert all(row["verification"] == "PASSED" and row["validation"] == "UNVALIDATED"
               for row in matrix["validation_matrix"])
    reach = matrix["reachability"]
    widths = [row["width_pa"] for row in reach["nominal_refinement"]]
    assert widths[0] > widths[1] > widths[2]
    assert reach["leaky_and_source_exclusion"] == "INDETERMINATE"


def test_equivalence_replay_and_uncertainty_expansion():
    report = ablations()
    assert report["summary"] == {
        "joint_set_agreement": 10, "certificates_replayed": 10, "ungated_specific_gate_withheld_examples": 1,
        "full_policy_specific": 3, "empirical_accuracy": None,
    }
    assert len(report["pressure_sweep"]) == 12
    for case in ("unique", "severe", "spatial_alias"):
        rows = [r for r in report["pressure_sweep"] if r["case"] == case]
        assert all(row["truth"] in row["feasible"] for row in rows)
        assert all(set(right["excluded"]) <= set(left["excluded"]) for left, right in zip(rows, rows[1:]))
        # The severe fixture has a two-step pressure change larger than 1 kPa.
        assert rows[-1]["localization"]["level"] == ("L2" if case == "severe" else "L0")
