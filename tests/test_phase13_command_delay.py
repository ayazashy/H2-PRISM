from zipfile import ZipFile

import pytest

from h2prism.phase12 import paired_design_xml


def test_command_timing_twin_allows_only_saved_step_time(tmp_path):
    def model(path, time, pressure):
        with ZipFile(path, "w") as z:
            z.writestr("simulink/systems/system_root.xml",
                       f'<System><Block Name="PS Step" SID="59"><P Name="step_time">{time}</P>'
                       f'<P Name="final_value">{pressure}</P></Block></System>')
            z.writestr("simulink/configSet0.json", "{}")

    a, b = tmp_path / "control.slx", tmp_path / "delay.slx"
    spec = {"step_delay": {"control_s":"25", "intervention_s":"26"}}
    model(a,25,6.4)
    model(b,26,6.4)
    assert paired_design_xml((a,b),spec) == ["PS Step.step_time"]
    model(b,26,6.3)
    with pytest.raises(ValueError, match="unintended twin"):
        paired_design_xml((a,b),spec)
    model(b,27,6.4)
    with pytest.raises(ValueError, match="step_time delta"):
        paired_design_xml((a,b),spec)
