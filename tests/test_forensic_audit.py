"""Unit tests for the forensic-audit helpers (tools/experiments/forensic_audit.py)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "experiments"))
import forensic_audit as fa  # noqa: E402


def test_root_reason_prefers_the_blocking_cause_over_the_first_token():
    """Regression for FA-11: the runner's decision_reasons keeps the first token (a consequence)."""
    code = ("SPECIFIC_REJECTED_SINGLE_CANDIDATE;SCORE_BELOW_THRESHOLD;"
            "FLAG_BLOCKS_SPECIFIC:LOW_SCENARIO_DIVERSITY+TOP_CLASS_FEW_INDEPENDENT_RUNS")
    assert fa.root_reason(code) == "SPECIFIC_BLOCKED_BY_SUPPORT_FLAG"
    assert fa.root_reason("FLAG:OUT_OF_SUPPORT") == "UNRESOLVED_BY_SUPPORT_FLAG"
    assert fa.root_reason("SPECIFIC_REJECTED_SINGLE_CANDIDATE;SCORE_BELOW_THRESHOLD") == "SCORE_BELOW_MATCHED_COVERAGE_CUT"
    assert fa.root_reason("ACCEPTED") == "ACCEPTED"
    assert fa.root_reason("") == "OTHER"


def test_scenario_ancestor_drops_only_the_topology_token():
    """FA-03: replicas of one scenario in different topologies share an ancestor; distinct scenarios do not."""
    a = fa.ancestor("CS_DOWNSTREAM_CONSTANT_SEGMENT_BROKENC1_STRONG")
    assert a == fa.ancestor("CS_UPSTREAM_CONSTANT_SEGMENT_BROKENC1_STRONG") == "CONSTANT_SEGMENT_BROKENC1_STRONG"
    assert fa.ancestor("CS_CENTER_CONSTANT_SEGMENT_LEAKG3") != fa.ancestor("CS_CENTER_START_TRANSIENT_LEAKG3")


def test_expected_model_mapping_covers_every_topology():
    assert set(fa.EXPECTED_MODEL) == {"Center", "Downstream", "Upstream"}
    assert len(set(fa.EXPECTED_MODEL.values())) == 3
