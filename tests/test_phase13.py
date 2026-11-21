from zipfile import ZipFile

import numpy as np
import pytest

from h2prism.phase10 import sha256
from h2prism.phase11 import write_json
from h2prism.phase12 import CASES, approve, paired_design_xml, prepare, specification
from h2prism.phase13 import SOURCE, signature


def write_twin(path, offset, area):
    with ZipFile(path, "w") as model:
        model.writestr("simulink/configSet0.json", '{"FixedStep": "0.2"}')
        model.writestr("simulink/systems/system_root.xml", f"""
        <System>
          <Block Name="Phase13 Command Offset"><P Name="final_value">{offset}</P></Block>
          <Block Name="Phase12 Outlet Area"><P Name="final_value">{area}</P></Block>
        </System>""")


@pytest.mark.parametrize(("role", "offsets", "areas", "allowed"), [
    ("internal_pressure", ("0", "-0.17"), ("0.001", "0.001"), "Phase13 Command Offset"),
    ("boundary_pressure", ("0.005", "0.005"), ("0.001", "0.0011"), "Phase12 Outlet Area"),
])
def test_only_intended_command_delta_is_accepted(tmp_path, role, offsets, areas, allowed):
    spec = {"overlay": {"role": role, "normal_final": offsets[0], "intervention_final": offsets[1]}}
    files = (tmp_path / "normal.slx", tmp_path / "intervention.slx")
    for file, offset, area in zip(files, offsets, areas):
        write_twin(file, offset, area)
    assert paired_design_xml(files, spec) == [allowed+".final_value"]
    if role == "internal_pressure":
        write_twin(files[1], offsets[1], "0.0011")
    else:
        write_twin(files[1], "0.006", areas[1])
    with pytest.raises(ValueError, match="unintended twin XML difference"):
        paired_design_xml(files, spec)


def test_signature_uses_only_pre_event_control_scale():
    clock = np.array([998., 999., 1000., 1001.])
    a = {"PS1": np.array([2., 2., 5., 10.])}
    b = {"PS1": np.array([2., 2., 6., 9.])}
    np.testing.assert_array_equal(signature(clock, a, b)["PS1"], [0., 0., .5, -.5])


def test_pressure_twin_approval_requires_constant_outlet(tmp_path):
    if not SOURCE.is_file():
        pytest.skip("local Center archive unavailable")
    spec = specification()
    spec["area"]["intervention_final"] = spec["area"]["normal_final"]
    assert specification()["area"]["intervention_final"] == "0.0011"
    spec["overlay"] = {"role": "internal_pressure", "normal_final": "0", "intervention_final": "-0.17"}
    root = tmp_path / "pressure"
    prepare(root, SOURCE, spec)
    for case, offset in zip(CASES, ("0", "-0.17")):
        folder = root / case
        twin = folder / "Center_phase12.slx"
        write_twin(twin, offset, "0.001")
        write_json(folder / "preflight.json", {
            "case": case, "source_sha256": spec["source_sha256"], "derived_sha256": sha256(twin),
            "compile_status": "PASSED", "solver": spec["solver"], "location": spec["location"],
            "existing_block_links_parameters_and_connections_unchanged": True,
            "command_final_area_m2": "0.001", "version": "fixture", "products": [],
        })
    approve(root, spec)
    assert (root / "approval.json").is_file()
