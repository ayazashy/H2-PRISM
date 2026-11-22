import numpy as np
import pytest

from h2prism.final_research import SOURCE, rival_specs, signature_rows
from h2prism.phase10 import CAPTURE


def test_source_traced_metered_and_unmetered_paths():
    if not SOURCE.exists():
        pytest.skip('official local source unavailable')
    designs = rival_specs(SOURCE)
    metered, unmetered = designs['sid312'], designs['sid215']
    assert metered['location']['flow_sensor_sid'] == '311'
    assert metered['location']['reservoir_sid'] == '316'
    assert unmetered['location']['flow_sensor_sid'] == ''
    assert unmetered['location']['reservoir_sid'] == '217'
    assert float(unmetered['area']['source_max']) < float(unmetered['area']['initial_value'])
    assert float(unmetered['area']['max']) >= float(unmetered['area']['intervention_final'])


def test_signature_distance_respects_subset_and_undefined_cosine():
    t = np.arange(1000,1005,dtype=float)
    normal = {key:np.zeros(len(t)) for key in CAPTURE}
    opening = {**normal,'MFS3':np.ones(len(t))}
    rows = signature_rows(t,{'normal':normal,'opening':opening},1000)
    result = {(row['duration_s'],row['subset']):row for row in rows}
    assert result[(1,'MFS3_only')]['relative_rms_distance'] == 1
    assert result[(1,'MFS3_only')]['cosine'] is None
    assert result[(1,'pressure_only')]['relative_rms_distance'] == 0
