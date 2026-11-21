"""Portability and canonicalisation tests for h2prism.dataset_manifest. SYNTHETIC file trees only."""

import numpy as np
import pandas as pd
import pytest

from h2prism.dataset_manifest import (CLEAN, MISFILED, NOISY_VARIANT, RELEASE, SOLVER, assign_scenarios,
                                      build_file_inventory, canonical_file, compare_realizations, discover_files,
                                      norm_path, parse_location, sensor_fingerprint, shared_pre_event_rows,
                                      union_find, weak_strong_partner)

SENS = [f"PS{i}" for i in range(1, 13)] + [f"MFS{i}" for i in range(1, 5)]
LAB = ["label_anomaly", "Leak", "CompressorFault", "CompressorDelay", "leak_G3", "leak_G4", "leak_G5", "leak_G6"]


def frame(seed, n=50, onset=20, noise=0.0, leak_loc="leak_G4", base=None):
    rng = np.random.default_rng(seed)
    X = base.copy() if base is not None else np.cumsum(rng.normal(size=(n, 16)), axis=0)
    X = X + noise * np.random.default_rng(seed + 100).normal(size=X.shape)
    df = pd.DataFrame(X, columns=SENS)
    for c in LAB:
        df[c] = 0
    if onset is not None:
        df.loc[onset:, ["label_anomaly", "Leak", leak_loc]] = 1
    df.index = pd.Index(np.arange(n, dtype=float), name="Timestamp")
    return df


@pytest.fixture
def tree(tmp_path):
    root = tmp_path / "raw"
    base = frame(1)[SENS].to_numpy()
    paths = {
        "H2-SimNet-Dataset/H2-SimNet-clean/anomalous-scenarios/parquet/anom_gestup/assestment_transient/leakG4.parquet": frame(1, base=base),
        "H2-SimNet-Dataset/anomalous-scenarios/parquet/anom_gestup/assestment_transient/leakG4.parquet": frame(1, base=base, noise=0.01),
        "H2-SimNet-Dataset/H2-SimNet-clean/anomalous-scenarios/parquet/anom_gestcent/constant_segment/leakG4_weak.parquet": frame(2),
        "H2-SimNet-Dataset/H2-SimNet-clean/anomalous-scenarios/parquet/anom_gestcent/constant_segment/leakG4_strong.parquet": frame(3),
        "H2-SimNet-Dataset/H2-SimNet-clean/normality-scenarios/parquet/normality_gest_up.parquet": frame(4, onset=None),
    }
    for rel, df in paths.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(p)
    # CSV twin of the clean upstream leakG4 with shuffled column order and no time
    df = paths[list(paths)[0]].reset_index(drop=True)
    cols = list(reversed(df.columns))
    p = root / "H2-SimNet-Dataset/H2-SimNet-clean/anomalous-scenarios/csv/anom_gestup/assestment_transient/leakG4.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    df[cols].to_csv(p, index=False)
    # misfiled byte copy at archive root of the noisy release file
    src = root / list(paths)[1]
    dst = root / "H2-SimNet-Dataset/H2-SimNet-clean/anomalous-scenarios/parquet/leakG4.parquet"
    dst.write_bytes(src.read_bytes())
    # noisy variant and a solver export without labels/time index
    nv = root / "H2-SimNet-Dataset/H2-SimNet-clean/anomalous-scenarios/parquet/anom_gestcent/constant_segment/leakG4_weak_noisy.parquet"
    frame(2, noise=0.01).to_parquet(nv)
    se = root / "H2-SimNet-Dataset/MATLAB_SIMSCAPE_Simulation/normality_scenarios/normality_gest_up.csv"
    se.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"Timestamp": np.arange(0, 45, 0.9), "PS1": np.arange(50) * 0.1}).to_csv(se, index=False)
    return root


def test_norm_path_windows_and_posix():
    assert norm_path(r"H2\a\\b\c.csv") == "H2/a/b/c.csv"
    assert norm_path("./H2//a/./b.csv") == "H2/a/b.csv"
    assert norm_path("H2/a/b.csv") == norm_path(r"H2\a\b.csv")


def test_parse_location_both_separators():
    a = parse_location(r"H2-SimNet-Dataset\anomalous-scenarios\csv\anom_gestdown\constant_segment\leakG5_strong.csv")
    b = parse_location("H2-SimNet-Dataset/anomalous-scenarios/csv/anom_gestdown/constant_segment/leakG5_strong.csv")
    assert a == b and a.topology == "Downstream" and a.tree == "release" and a.fmt == "csv"
    n = parse_location("H2-SimNet-Dataset/H2-SimNet-clean/x/leakG5G6_overlapped_noisy.parquet")
    assert n.topology == "UNLOCATED" and n.noisy_suffix and n.run_stem == "leakG5G6_overlapped"
    assert parse_location("H2-SimNet-Dataset/normality-scenarios/parquet/normality_gest_center.parquet").topology == "Center"


def test_inventory_independent_of_order_and_separator(tree):
    files = discover_files(tree)
    a = assign_scenarios(build_file_inventory(tree, files))
    b = assign_scenarios(build_file_inventory(tree, [f.replace("/", "\\") for f in reversed(files)]))
    pd.testing.assert_frame_equal(a, b)
    assert list(a["file"]) == sorted(a["file"])


def test_realization_typing_and_misfiled_copy(tree):
    inv = assign_scenarios(build_file_inventory(tree)).set_index("file")
    mis = inv.loc["H2-SimNet-Dataset/H2-SimNet-clean/anomalous-scenarios/parquet/leakG4.parquet"]
    assert mis["realization_type"] == MISFILED
    assert mis["candidate_Scenario_ID"] == "CS_UPSTREAM_ASSESTMENT_TRANSIENT_LEAKG4"
    rt = dict(zip(inv.index, inv["realization_type"]))
    assert rt["H2-SimNet-Dataset/anomalous-scenarios/parquet/anom_gestup/assestment_transient/leakG4.parquet"] == RELEASE
    assert rt["H2-SimNet-Dataset/MATLAB_SIMSCAPE_Simulation/normality_scenarios/normality_gest_up.csv"] == SOLVER
    assert NOISY_VARIANT in set(rt.values()) and CLEAN in set(rt.values())


def test_csv_parquet_equivalence_and_column_order(tree):
    inv = assign_scenarios(build_file_inventory(tree)).set_index("file")
    pq_ = "H2-SimNet-Dataset/H2-SimNet-clean/anomalous-scenarios/parquet/anom_gestup/assestment_transient/leakG4.parquet"
    csv = pq_.replace("/parquet/", "/csv/").replace(".parquet", ".csv")
    assert inv.loc[pq_, "sensor_fingerprint_6dp"] == inv.loc[csv, "sensor_fingerprint_6dp"]
    assert inv.loc[pq_, "time_source"] == "INDEX_Timestamp" and inv.loc[csv, "time_source"] == "NONE"
    c = compare_realizations(pd.read_parquet(tree / pq_), pd.read_csv(tree / csv))
    assert c["numerically_equal_atol"] and c["labels_identical"]


def test_canonical_file_parquet_precedence(tree):
    inv = assign_scenarios(build_file_inventory(tree))
    f = canonical_file(inv, "CS_UPSTREAM_ASSESTMENT_TRANSIENT_LEAKG4", CLEAN)
    assert f.endswith(".parquet") and "H2-SimNet-clean/anomalous-scenarios/parquet/anom_gestup" in f
    assert canonical_file(inv, "CS_UPSTREAM_ASSESTMENT_TRANSIENT_LEAKG4", SOLVER) is None


def test_missing_metadata_and_timestamp_column(tree):
    inv = assign_scenarios(build_file_inventory(tree)).set_index("file")
    se = inv.loc["H2-SimNet-Dataset/MATLAB_SIMSCAPE_Simulation/normality_scenarios/normality_gest_up.csv"]
    assert se["has_labels"] == False  # noqa: E712
    assert se["time_source"] == "COLUMN_Timestamp" and se["dt_unique"] == "0.9"
    assert "PS2" in se["missing_sensors"]


def test_noise_added_realization_detected(tree):
    a = pd.read_parquet(tree / "H2-SimNet-Dataset/H2-SimNet-clean/anomalous-scenarios/parquet/anom_gestup/assestment_transient/leakG4.parquet")
    b = pd.read_parquet(tree / "H2-SimNet-Dataset/anomalous-scenarios/parquet/anom_gestup/assestment_transient/leakG4.parquet")
    c = compare_realizations(a, b)
    assert c["labels_identical"] and not c["numerically_equal_atol"]
    assert abs(c["median_lag1_autocorr"]) < 0.5 and c["max_abs_mean_diff"] < 0.01


def test_fingerprint_column_order_invariant():
    df = frame(5)
    assert sensor_fingerprint(df) == sensor_fingerprint(df[list(reversed(df.columns))])


def test_shared_pre_event_rows():
    base = frame(6)[SENS].to_numpy()
    a = frame(6, base=base, onset=30)
    b = frame(6, base=base, onset=20)
    b.iloc[10:, :16] += 1.0
    cut, lead, _ = shared_pre_event_rows(a, b)
    assert cut == 20 and lead == 10


def test_union_find_and_weak_strong():
    m = union_find(["c", "a", "b", "d"], [("b", "a"), ("c", "b")])
    assert m["a"] == m["b"] == m["c"] == "a" and m["d"] == "d"
    assert weak_strong_partner("CS_X_LEAKG4_WEAK") == "CS_X_LEAKG4_STRONG"
    assert weak_strong_partner("CS_X_LEAKG3") is None
