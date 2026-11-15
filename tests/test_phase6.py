from fractions import Fraction as Q
import hashlib

import pandas as pd
import pytest

from h2prism.data.loader import RAW_DATASET_DIR
from h2prism.phase2 import MODEL, MODEL_DIR, PARQUET, SID
from h2prism.phase5 import clock_index, physical_eligibility
from h2prism.phase6 import (
    aligned_residuals, archival_alignment, execution_gate, external_candidates, flow_roles,
    source_uncertainty, summarize_residuals,
)
from h2prism.phase3 import source_report


def test_alignment_rejects_near_matches_and_preserves_residual_sign():
    raw = pd.DataFrame({name: [10., 20., 30.] for name in SID}, index=clock_index(("0", "4", "8")))
    release = pd.DataFrame({name: [11., 22., 28.] for name in SID},
                           index=clock_index(("0", "4.00000001", "8")))
    result = aligned_residuals(raw, release)
    assert list(result.index) == [Q(0), Q(8)]
    stats = summarize_residuals(result)
    assert stats["PS1"]["maximum_timestamp_s"] == "8"
    assert stats["PS1"]["signed_residual_at_maximum"] == -2
    assert stats["MFS3"]["finite_pairs"] == 2


def test_startup_result_has_no_runtime_solver_evidence(tmp_path):
    path = tmp_path / "console.txt"
    path.write_text("Unable to communicate with required MathWorks services (error 5202).\nsensitive-text",
                    encoding="utf-8")
    blocked = execution_gate(path, 1)
    assert blocked["console_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert not blocked["source_model_loaded"] and not blocked["simulation_executed"]
    assert blocked["actual_solver_configuration"] is None and blocked["raw_export"] is None
    assert "sensitive-text" not in str(blocked)
    with pytest.raises(ValueError, match="failed 5202"):
        execution_gate(path, 0)
    path.write_text("Other or unknown failure", encoding="utf-8")
    with pytest.raises(ValueError, match="failed 5202"):
        execution_gate(path, 1)


def test_source_uncertainty_is_traceable_and_not_a_bound():
    records = source_uncertainty()
    assert len({record.reference for record in records}) == 11
    assert all(record.interval is None for record in records)
    assert len(physical_eligibility(records, MODEL)) == 11


def test_archive_and_static_physics_do_not_establish_conservation():
    if not (RAW_DATASET_DIR / PARQUET).exists() or not (RAW_DATASET_DIR / MODEL_DIR / "normality_gest_center.csv").exists():
        pytest.skip("official archive unavailable")
    report, residuals = archival_alignment()
    assert len(residuals) == 5000 and len(report["channels"]) == 13
    assert report["channels"]["PS1"]["maximum_absolute"] == pytest.approx(0.08970295647)
    assert report["channels"]["MFS3"]["maximum_absolute"] == pytest.approx(0.05302821566)
    assert not report["fresh_reproduction"]
    assert report["publication"]["exact_center_processing_chain"] == "UNVERIFIED"
    physics = flow_roles(source_report(None)["source_port_graph"])
    assert not physics["mass_balance_closed"]
    assert physics["roles"]["MFS2"]["static_role"] == "INTERNAL_STORAGE_CONNECTED_BRANCH"
    assert physics["roles"]["MFS1"]["static_role"] == "RESERVOIR_CONNECTED_BRANCH"
    assert physics["roles"]["MFS3"]["static_role"] == "RESERVOIR_CONNECTED_BRANCH"
    assert all(role["signed_control_volume_term"] is None for role in physics["roles"].values())


def test_external_screen_keeps_candidates_unqualified():
    for entry in external_candidates():
        assert entry["tier"] == "T4_CANDIDATE"
        assert all(entry[key] for key in ("availability", "measurements", "labels", "ground_truth", "licensing"))
