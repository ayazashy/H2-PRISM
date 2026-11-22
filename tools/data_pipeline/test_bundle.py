"""Integrity, schema, and corruption tests for the public web replay bundle."""

from __future__ import annotations

import hashlib
import json
import math
import pathlib

import pytest


DATA_DIR = pathlib.Path(__file__).resolve().parents[2] / "apps" / "web" / "public" / "data"


def test_catalog_and_hashes_match_on_disk() -> None:
    catalog = json.loads((DATA_DIR / "catalog.json").read_text(encoding="utf-8"))
    assert catalog["schema_version"] == "1.0.0"
    assert catalog["supported_features"]["localization"] is False
    assert len(catalog["scenarios"]) >= 4

    seen_ids: set[str] = set()
    for entry in catalog["scenarios"]:
        assert entry["id"] not in seen_ids
        seen_ids.add(entry["id"])
        scen_path = DATA_DIR.parent / entry["data_path"]
        raw = scen_path.read_bytes()
        assert b"\r\n" not in raw, f"CRLF detected in {scen_path}"
        assert hashlib.sha256(raw).hexdigest() == entry["sha256"]

        scen = json.loads(raw.decode("utf-8"))
        ts = scen["time_seconds"]
        assert len(ts) >= 2
        assert all(math.isfinite(t) for t in ts)
        assert all(ts[i] > ts[i - 1] for i in range(1, len(ts)))
        assert scen["location_prediction"] is None

        for ch in scen["sensor_channels"]:
            assert len(ch["values"]) == len(ts)
            if ch["variable"] == "pressure":
                assert ch["pressure_reference"] in ("absolute", "gauge")
            for v in ch["values"]:
                assert v is None or math.isfinite(v)


def test_metrics_bundle_has_exact_denominators_and_not_estimable_note() -> None:
    catalog = json.loads((DATA_DIR / "catalog.json").read_text(encoding="utf-8"))
    m_entry = catalog["metrics_catalog"][0]
    m_path = DATA_DIR.parent / m_entry["data_path"]
    raw = m_path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == m_entry["sha256"]
    metrics = json.loads(raw.decode("utf-8"))

    assert metrics["cohort_n"] == 27993
    assert metrics["estimable_n"] == 18662
    assert metrics["rq1_status"] == "NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL"
    assert len(metrics["prohibited_claims"]) >= 5
    assert set(metrics["confusion_matrices_by_scope"].keys()) == {
        "pooled",
        "Center",
        "Downstream",
        "Upstream",
    }


def test_normal_center_masks_padded_absent_channels() -> None:
    scen = json.loads(
        (DATA_DIR / "scenarios" / "SCEN_NORMAL_GEST_CENTER.json").read_text(encoding="utf-8")
    )
    by_id = {ch["id"]: ch for ch in scen["sensor_channels"]}
    for absent in ("PS11", "PS12", "MFS4"):
        assert by_id[absent]["observable"] is False
        assert all(v is None for v in by_id[absent]["values"])
