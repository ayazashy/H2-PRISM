"""Claim-level validation and publication lifecycle (tools/reporting/publication.py).

The watermark must disappear ONLY as a consequence of valid, scoped, hash-bound approval by an authorized named
reviewer; every other situation keeps (or refuses) the artifact. Fixtures are tiny research-class runs in tmp_path.
"""

import json
import shutil
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "reporting"))
import build_research_figures as brf  # noqa: E402
import build_research_tables as brt  # noqa: E402
import publication as pub  # noqa: E402
from _common import ReportingInputError  # noqa: E402

KEY = "f" * 64


def _root(tmp_path, run_dir="PRIMARY", tech="VALID", status="NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL"):
    root = tmp_path / "r"
    run = root / "03_results" / "primary_protocol" / run_dir
    run.mkdir(parents=True)
    (run / "run_manifest.json").write_text(json.dumps({"artifact_class": "PRIMARY_EXPERIMENT", "status": "COMPLETED", "run_key": KEY,
                                                       "authorization": {"scope": "PRIMARY_EXPERIMENT"}}))
    pd.DataFrame({"method": ["s_C", "confidence"], "target": [0.8, 0.8], "status": [status, status],
                  "coverage": [0.5, 0.5], "selective_risk": [0.1, 0.2]}).to_csv(run / "t.csv", index=False)
    if tech:
        v = root / "03_results" / "validation"
        v.mkdir(parents=True)
        (v / f"{run_dir}_{KEY[:12]}.json").write_text(json.dumps({"status": tech}))
    pol = yaml.safe_load((ROOT / "configs" / "publication_policy.yaml").read_text(encoding="utf-8"))
    pol["artifact_scopes"] = {"tabA": ["DESCRIPTIVE", "CONFIRMATORY"], "tabB": ["DESCRIPTIVE"], "figA": ["DESCRIPTIVE"]}
    (root / "configs").mkdir()
    (root / "configs" / "publication_policy.yaml").write_text(yaml.safe_dump(pol))
    return root, f"03_results/primary_protocol/{run_dir}/t.csv"


def _cfg(root, inp, caption="cap"):
    cfg = {"dpi": 40, "fail_on_missing": True,
           "figures": [{"id": "figA", "kind": "risk_coverage", "input": inp, "evidence_status": "PENDING", "caption": caption}],
           "tables": [{"id": "tabA", "input": inp, "columns": ["method", "target", "status", "coverage", "selective_risk"],
                       "evidence_status": "PENDING", "caption": caption},
                      {"id": "tabB", "input": inp, "columns": ["method", "status"], "evidence_status": "PENDING", "caption": caption}]}
    p = root / "cfg.yaml"
    p.write_text(yaml.safe_dump(cfg))
    return p, cfg


def _approve(root, spec, kind="table", name="Ahmed Zayed", role="science_owner", scope="DESCRIPTIVE",
             decision="APPROVED_FOR_PUBLICATION", tag="a"):
    b = (brt.table_binding(root, spec) if kind == "table" else brf.figure_binding(root, spec))[0]
    rec = {"approval_id": f"{spec['id']}_{tag}", "artifact_id": spec["id"], "claim_scope": scope, "decision": decision,
           "reviewer": {"name": name, "role": role}, "date": "2026-11-12", "statement": "reviewed values, population, caption",
           "approved_claims": ["descriptive"], "binding": b.as_dict()}
    d = root / "06_audit_preparation" / "publication_approvals" / spec["id"]
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{tag}.yaml").write_text(yaml.safe_dump(rec))
    return rec


def _tab(root, cfg_p, out="tab"):
    return brt.build(cfg_p, root / out, root).drop_duplicates("table_id").set_index("table_id")


def test_pending_without_approval_keeps_watermark(tmp_path):
    root, inp = _root(tmp_path)
    p, _ = _cfg(root, inp)
    m = _tab(root, p)
    assert m.loc["tabA", "lifecycle_status"] == "SCIENTIFIC_REVIEW_PENDING"
    assert "PRELIMINARY" in (root / "tab" / "preliminary" / "tabA.md").read_text(encoding="utf-8")
    assert not (root / "tab" / "final").exists()


def test_valid_scoped_approval_publishes_without_watermark_and_isolated(tmp_path):
    root, inp = _root(tmp_path)
    p, cfg = _cfg(root, inp)
    _approve(root, cfg["tables"][0])
    m = _tab(root, p)
    assert m.loc["tabA", "lifecycle_status"] == "APPROVED_FOR_PUBLICATION" and m.loc["tabA", "status"] == "BUILT_FINAL"
    md = (root / "tab" / "final" / "tabA.md").read_text(encoding="utf-8")
    assert "PRELIMINARY" not in md and "cap" in md  # caption kept, watermark gone
    assert m.loc["tabB", "lifecycle_status"] == "SCIENTIFIC_REVIEW_PENDING"  # per-artifact isolation


def test_genuine_not_estimable_result_can_be_published(tmp_path):
    root, inp = _root(tmp_path, status="NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL")
    p, cfg = _cfg(root, inp)
    _approve(root, cfg["tables"][0])
    assert _tab(root, p).loc["tabA", "lifecycle_status"] == "APPROVED_FOR_PUBLICATION"


@pytest.mark.parametrize("name,role,frag", [("Mallory", "science_owner", "not an authorized"),
                                            ("Ahmed Zayed", "methods_owner", "not an authorized"),
                                            ("Ahmed Zayed", "nonexistent_role", "not an authorized")])
def test_forged_or_mismatched_reviewer_is_rejected(tmp_path, name, role, frag):
    root, inp = _root(tmp_path)
    p, cfg = _cfg(root, inp)
    _approve(root, cfg["tables"][0], name=name, role=role)
    m = _tab(root, p)
    assert m.loc["tabA", "lifecycle_status"] == "SCIENTIFIC_REVIEW_PENDING" and frag in m.loc["tabA", "publication_blockers"]


def test_stale_approval_after_source_change_is_not_reused(tmp_path):
    root, inp = _root(tmp_path)
    p, cfg = _cfg(root, inp)
    _approve(root, cfg["tables"][0])
    df = pd.read_csv(root / inp)
    df.loc[0, "selective_risk"] = 0.11  # any change to the evidence invalidates the approval
    df.to_csv(root / inp, index=False)
    m = _tab(root, p)
    assert m.loc["tabA", "lifecycle_status"] == "SCIENTIFIC_REVIEW_PENDING" and "STALE: input_sha256" in m.loc["tabA", "publication_blockers"]


def test_caption_change_makes_approval_stale(tmp_path):
    root, inp = _root(tmp_path)
    p, cfg = _cfg(root, inp, caption="cap")
    _approve(root, cfg["tables"][0])
    p2, _ = _cfg(root, inp, caption="a stronger claim")
    m = _tab(root, p2)
    assert "STALE: spec_sha256" in m.loc["tabA", "publication_blockers"]


def test_tampered_binding_hash_is_rejected(tmp_path):
    root, inp = _root(tmp_path)
    p, cfg = _cfg(root, inp)
    rec = _approve(root, cfg["tables"][0])
    rec["binding"]["input_sha256"][inp] = "0" * 64
    (root / "06_audit_preparation" / "publication_approvals" / "tabA" / "a.yaml").write_text(yaml.safe_dump(rec))
    assert _tab(root, p).loc["tabA", "lifecycle_status"] == "SCIENTIFIC_REVIEW_PENDING"


def test_missing_technical_validation_blocks_publication(tmp_path):
    root, inp = _root(tmp_path, tech=None)
    p, cfg = _cfg(root, inp)
    _approve(root, cfg["tables"][0])
    m = _tab(root, p)
    assert m.loc["tabA", "lifecycle_status"] == "EXECUTION_COMPLETED" and not (root / "tab" / "final").exists()


def test_invalid_archived_run_is_refused_even_with_approval(tmp_path):
    root, inp = _root(tmp_path, run_dir="PRIMARY_db9acd23ef58_INVALID_CALIBRATION")
    p, cfg = _cfg(root, inp)
    _approve(root, cfg["tables"][0])
    with pytest.raises(ReportingInputError, match="INVALID"):
        _tab(root, p)


def test_scope_rules_confirmatory_needs_both_owners_and_allowed_scope(tmp_path):
    root, inp = _root(tmp_path)
    p, cfg = _cfg(root, inp)
    _approve(root, cfg["tables"][0], scope="CONFIRMATORY", tag="c1")
    assert _tab(root, p).loc["tabA", "lifecycle_status"] == "SCIENTIFIC_REVIEW_PENDING"  # methods_owner missing
    _approve(root, cfg["tables"][0], scope="CONFIRMATORY", name="Faisal", role="methods_owner", tag="c2")
    m = _tab(root, p, out="tab2")
    assert m.loc["tabA", "lifecycle_status"] == "APPROVED_FOR_PUBLICATION" and m.loc["tabA", "claim_scope"] == "CONFIRMATORY"
    _approve(root, cfg["tables"][1], scope="CONFIRMATORY", tag="c3")  # tabB allows DESCRIPTIVE only
    assert "not allowed" in _tab(root, p, out="tab3").loc["tabB", "publication_blockers"]


def test_validated_but_not_cleared_keeps_distinct_watermark(tmp_path):
    root, inp = _root(tmp_path)
    p, cfg = _cfg(root, inp)
    _approve(root, cfg["tables"][0], decision="SCIENTIFICALLY_VALIDATED")
    m = _tab(root, p)
    assert m.loc["tabA", "lifecycle_status"] == "SCIENTIFICALLY_VALIDATED"
    assert "NOT APPROVED FOR PUBLICATION" in (root / "tab" / "preliminary" / "tabA.md").read_text(encoding="utf-8")


def test_rejected_claim_is_refused(tmp_path):
    root, inp = _root(tmp_path)
    p, cfg = _cfg(root, inp)
    _approve(root, cfg["tables"][0], decision="REJECTED")
    with pytest.raises(ReportingInputError, match="INVALID"):
        _tab(root, p)


def test_figure_publication_and_regeneration_consistency(tmp_path):
    root, inp = _root(tmp_path, status="ESTIMABLE")
    p, cfg = _cfg(root, inp)
    pend = brf.build(p, root / "f0", root).iloc[0]
    assert pend["lifecycle_status"] == "SCIENTIFIC_REVIEW_PENDING" and "PRELIMINARY" in pend["reason"]
    _approve(root, cfg["figures"][0], kind="figure")
    m1 = brf.build(p, root / "f1", root)
    m2 = brf.build(p, root / "f2", root)
    assert set(m1.lifecycle_status) == {"APPROVED_FOR_PUBLICATION"} and (root / "f1" / "final" / "figA.png").exists()
    assert m1.reason.fillna("").eq("").all()  # no watermark text
    assert m1.output_sha256.tolist() == m2.output_sha256.tolist()  # deterministic regeneration
    p0 = (root / "f0" / "preliminary" / "figA.png").read_bytes()
    assert p0 != (root / "f1" / "final" / "figA.png").read_bytes()  # the watermark was actually drawn before


def test_official_build_has_no_evidence_status_override():
    import build_results as bres
    import inspect
    assert "evidence_status" not in inspect.signature(bres.run).parameters
    src = (ROOT / "tools" / "reporting" / "build_results.py").read_text(encoding="utf-8")
    assert "--evidence-status" not in src.replace("Publication state is NOT a command-line option", "")
