from pathlib import Path
from zipfile import ZipFile

import pytest

from h2prism.data.loader import RAW_DATASET_DIR
from h2prism.phase2 import MODEL, MODEL_DIR
from h2prism.phase10 import sha256
from h2prism.phase11 import write_json
from h2prism.phase12 import ANOMALOUS, CASES, approve, paired_xml, prepare, prepare_retry, source_evidence, specification


def twin(path, area, unrelated="0", json_solver="0.2"):
    with ZipFile(path, "w") as stream:
        stream.writestr("simulink/systems/system_root.xml", f"""
        <System><Block Name="Phase12 Outlet Area"><InstanceData>
        <P Name="final_value">{area}</P></InstanceData></Block>
        <Block Name="Unrelated"><P Name="gain">{unrelated}</P></Block></System>""")
        stream.writestr("simulink/configSet0.json", '{"FixedStep": "' + json_solver + '"}')


def test_only_intended_twin_delta_passes(tmp_path):
    a, b = [tmp_path / name for name in ("normal.slx", "opening.slx")]
    twin(a, "1e-3")
    twin(b, ".0011")
    assert paired_xml(a, b) == ["Phase12 Outlet Area.final_value"]
    twin(b, ".0011", json_solver="0.4")
    with pytest.raises(ValueError, match="unintended twin configuration"):
        paired_xml(a, b)
    twin(b, ".0011", "7")
    with pytest.raises(ValueError, match="unintended"):
        paired_xml(a, b)
    twin(b, ".001")
    with pytest.raises(ValueError, match="area command"):
        paired_xml(a, b)


def test_prepare_rejects_changed_source_before_creating_cases(tmp_path):
    source = tmp_path / "changed.slx"
    source.write_bytes(b"changed")
    out = tmp_path / "cases"
    with pytest.raises(ValueError, match="checksum"):
        prepare(out, source)
    assert not out.exists()


def test_design_separates_archived_and_engineered_ground_truth():
    design = specification()
    assert design["classification"] == "NEW CONTROLLED SIMULATION"
    assert design["archived_anomalous_status"] == "BLOCKED"
    assert design["status"] == "CONDITIONAL"
    assert design["area"]["initial_value"] == design["area"]["normal_final"]
    assert float(design["area"]["normal_final"]) < float(design["area"]["intervention_final"])


def test_pinned_outlet_evidence_from_both_archives():
    normal = RAW_DATASET_DIR / MODEL_DIR / f"{MODEL}.slx"
    anomalous = RAW_DATASET_DIR / Path(ANOMALOUS)
    if not normal.exists() or not anomalous.exists():
        pytest.skip("source archives unavailable")
    evidence = source_evidence(normal, anomalous)
    assert evidence["sid_563"]["initial_value"] == evidence["sid_563"]["final_value"] == "1e-10"
    assert evidence["boundary_200"]["pressure_spec"].endswith(".atmospheric")
    assert evidence["difference_matrix"]["gas_properties"]["4"]["status"] == "UNCHANGED_ROOT_PARAMETERS"
    assert evidence["difference_matrix"]["restriction_and_actuation"]["213"]["status"] == "CHANGED"

def test_receipt_rejects_drift_from_frozen_design(tmp_path):
    normal = RAW_DATASET_DIR / MODEL_DIR / f"{MODEL}.slx"
    if not normal.exists():
        pytest.skip("local source unavailable")
    pair = tmp_path / "pair"
    prepare(pair, normal)
    spec = specification()
    for case, area in zip(CASES, ("0.001", "0.0011")):
        folder = pair / case
        path = folder / "Center_phase12.slx"
        twin(path, area)
        write_json(folder / "preflight.json", {
            "case": case, "source_sha256": spec["source_sha256"], "derived_sha256": sha256(path),
            "compile_status": "PASSED", "solver": spec["solver"], "location": spec["location"],
            "existing_block_links_parameters_and_connections_unchanged": True,
            "command_final_area_m2": area, "version": "fixture", "products": []})
    design = pair / "normal" / "design.json"
    original = design.read_text()
    design.write_text(original.replace('"1000"', '"1001"'))
    with pytest.raises(ValueError, match="unexpected prepared specification"):
        approve(pair)
    assert not (pair / "approval.json").exists()
    design.write_text(original)
    approve(pair)
    assert (pair / "approval.json").is_file()
    crashed = pair / "normal" / "center_raw.mat"
    crashed.write_bytes(b"interrupted output")
    diary = pair / "normal" / "execution.log"
    diary.write_bytes(b"crash trace")
    with pytest.raises(ValueError, match="outside"):
        prepare_retry(pair, pair / "nested")
    fresh = tmp_path / "retry"
    prepare_retry(pair, fresh)
    assert not (fresh / "normal" / crashed.name).exists()
    assert not (fresh / "normal" / diary.name).exists()
    for case in CASES:
        assert sha256(pair / case / "Center_phase12.slx") == sha256(fresh / case / "Center_phase12.slx")
    assert crashed.read_bytes() == b"interrupted output"
    assert diary.read_bytes() == b"crash trace"
    with pytest.raises(FileExistsError):
        prepare_retry(pair, fresh)
