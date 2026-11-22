import pytest

from h2prism.publication_atlas import deadline_curve, digest, verify


def test_frozen_inputs_reject_mutation(tmp_path):
    path = tmp_path / "source.csv"
    path.write_text("value\n1\n")
    manifest = {"sha256": {"repository": {}, "workspace": {path.name: digest(path)}}}
    assert verify(tmp_path, tmp_path, manifest) == 1
    path.write_text("value\n2\n")
    with pytest.raises(ValueError, match="frozen checksum differs"):
        verify(tmp_path, tmp_path, manifest)


def test_detection_curve_includes_missed_events():
    times, fractions = deadline_curve([7, 2], 4)
    assert list(times) == [0, 2, 7]
    assert list(fractions) == [0, 0.25, 0.5]


@pytest.mark.parametrize("delays,total", [([-1], 1), ([float("nan")], 1), ([3], 0), ([3, 5], 1)])
def test_detection_curve_rejects_invalid_populations(delays, total):
    with pytest.raises(ValueError, match="invalid event latency"):
        deadline_curve(delays, total)
