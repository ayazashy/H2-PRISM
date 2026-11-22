"""Gas-composition interface: pure-H2 tables serve pure H2 only; blends and out-of-range states are refused."""

import sys
from pathlib import Path

import pytest

from h2prism.gas_composition import (CompositionNotSupported, GasComposition, MixtureProviderUnavailable,
                                     PureHydrogenTableProvider, resolve_provider)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "simulation"))


def _providers():
    from h2net_v1_reference import load_h2_tables
    return [PureHydrogenTableProvider(load_h2_tables), MixtureProviderUnavailable()]


def test_composition_validation():
    assert GasComposition.of(H2=1.0).is_pure("H2")
    for bad in ({"H2": 0.5, "CH4": 0.4}, {"H2": 1.2, "CH4": -0.2}, {"XE": 1.0}):
        with pytest.raises(ValueError):
            GasComposition.of(**bad)
    assert GasComposition.of(H2=0.9, CH4=0.1).as_record()["mole_fractions"] == {"CH4": 0.1, "H2": 0.9}


def test_pure_h2_is_served_by_the_hash_verified_tables():
    gas = resolve_provider(GasComposition.of(H2=1.0), _providers()).gas_for(GasComposition.of(H2=1.0))
    assert "CoolProp" in gas.source and abs(gas.R - 4124.2) < 1.0
    assert 0.99 < gas.z(1e6, 300.0) < 1.02


@pytest.mark.parametrize("x_ch4", [1e-4, 0.02, 0.1, 0.2])
def test_blends_are_refused_never_extrapolated_from_pure_h2_tables(x_ch4):
    comp = GasComposition.of(H2=1 - x_ch4, CH4=x_ch4)
    prov = _providers()
    with pytest.raises(CompositionNotSupported, match="no valid property provider"):
        resolve_provider(comp, prov)
    with pytest.raises(CompositionNotSupported, match="pure H2"):
        prov[0].gas_for(comp)


def test_out_of_table_conditions_are_refused():
    gas = _providers()[0].gas_for(GasComposition.of(H2=1.0))
    with pytest.raises(ValueError, match="no extrapolation"):
        gas.props(1e6, 5000.0)
    with pytest.raises(ValueError, match="no extrapolation"):
        gas.props(1e9, 300.0)


def test_mixture_provider_states_its_blocker():
    m = MixtureProviderUnavailable()
    assert m.status == "NOT_AVAILABLE" and not m.supports(GasComposition.of(H2=0.9, CH4=0.1))
    with pytest.raises(CompositionNotSupported, match="GERG-2008"):
        m.gas_for(GasComposition.of(H2=0.9, CH4=0.1))
