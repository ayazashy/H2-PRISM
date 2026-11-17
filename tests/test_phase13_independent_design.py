from h2prism.phase13_independent_design import REQUIRED, PARTITIONS, LABELS, admission


def test_empty_manifest_blocks_coverage():
    assert admission([],["213"])["status"] == "BLOCKED"


def test_root_or_checkpoint_crossing_blocks_manifest():
    records = []
    for part in PARTITIONS:
        for label in LABELS:
            key = part+label
            records.append(dict.fromkeys(REQUIRED,key) |
                           dict(partition=part,event_class=label,onset_clock=1,end_clock=2,location_truth="213"))
    assert admission(records,["213"])["status"] == "STRUCTURAL_CHECKS_PASSED"
    records[0]["parent_checkpoint"] = "shared"
    records[-1]["parent_checkpoint"] = "shared"
    assert "parent_checkpoint crosses partitions: shared" in admission(records,["213"])["issues"]
