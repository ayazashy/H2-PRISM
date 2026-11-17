from h2prism.phase13_pilot import MODEL_HASH, preflight


def test_empty_pilot_cannot_authorize_execution():
    r = preflight({"records": [], "regions": ["213", "312", "215"]})
    assert not r["execution_authorized"]
    assert r["status"] == "BLOCKED"


def test_fault_label_cannot_promote_a_pinned_source():
    r = preflight({"records": [{"scenario_id": "relabelled", "event_class": "FAULT",
                               "model_sha256": MODEL_HASH}], "regions": ["213"]})
    assert "relabelled: BLOCKED is not an independent qualified generator" in r["issues"]
