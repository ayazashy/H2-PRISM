import json
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import pytest

from h2prism.data.loader import RAW_DATASET_DIR
from h2prism.phase2 import MODEL, MODEL_DIR
from tools.simulation.verify_center_input_plan import PLAN, inspect_xml, verify

SLX = RAW_DATASET_DIR / MODEL_DIR / f"{MODEL}.slx"


@pytest.fixture
def xml():
    if not SLX.exists():
        pytest.skip("official Center SLX not installed")
    with ZipFile(SLX) as archive:
        return tuple(ET.fromstring(archive.read(f"simulink/systems/{name}.xml"))
                     for name in ("system_root", "system_12"))


def test_exact_center_input_plan(xml):
    result = verify(SLX)
    assert [(r["converter_sid"], r["from_sid"], r["unit"]) for r in result["reservoir_inputs"]] == [
        ("5", "3", "K"), ("6", "2", "bar")]
    step, ramp = result["native_physical_inputs"]
    assert step["parameters"]["step_time"] == ["25", "s"]
    assert ramp["parameters"]["slope"] == ["-0.00001", "MPa/s"]
    assert result["workspace_input_blocks_in_traced_systems"] == []


def test_missing_required_inputs_fail_closed(xml):
    root, subsystem = xml
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    line = next(line for line in root.findall("Line") if line.findtext("P[@Name='Dst']") == "239#lconn:2")
    root.remove(line)
    with pytest.raises(ValueError, match="Required connection"):
        inspect_xml(root, subsystem, plan)
    plan["reservoir_inputs"].pop()
    with pytest.raises(ValueError, match="Required Center input roles"):
        inspect_xml(root, subsystem, plan)


@pytest.mark.parametrize("kind", ("wrong_unit", "unsupported_driver", "workspace"))
def test_unsupported_mapping_is_rejected(xml, kind):
    root, subsystem = xml
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    if kind == "wrong_unit":
        root.find("Block[@SID='6']//P[@Name='Unit']").text = "Pa"
    elif kind == "unsupported_driver":
        next(line for line in root.findall("Line")
             if line.findtext("P[@Name='Dst']") == "5#in:1").find("P[@Name='Src']").text = "2#out:1"
    else:
        ET.SubElement(subsystem, "Block", BlockType="FromWorkspace", SID="new")
    with pytest.raises(ValueError, match="Unsupported|unsupported"):
        inspect_xml(root, subsystem, plan)


def test_changed_source_bytes_are_rejected(xml, tmp_path):
    copy = tmp_path / SLX.name
    copy.write_bytes(SLX.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="checksum changed"):
        verify(copy)
