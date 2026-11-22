"""
Claim-level scientific validation and publication approval for H2-PRISM figures and tables (A13 lifecycle).

The preliminary watermark is a CONSEQUENCE of the artifact's lifecycle state, never an editable string. The state is
computed at build time from:
  1. the source run's technical validation  (03_results/validation/<run>_<key12>.json == VALID; dataset artifacts:
     every preflight check passed),
  2. approval records  <root>/06_audit_preparation/publication_approvals/<artifact_id>/*.yaml, each bound to
     - the SHA-256 of every source input,
     - the artifact spec (data selection, caption, limitations; evidence_status excluded),
     - the renderer source (plot function + style module, or table renderer),
     - the source run keys,
  3. configs/publication_policy.yaml (who may approve which claim scope, per artifact).

Lifecycle (adapted to the existing registry; dest directory / watermark in brackets):
  INVALID                     source run invalid, synthetic in official tree, or a valid REJECTED review  [refused]
  EXECUTION_COMPLETED         run completed, technical validation missing or failed            [preliminary + watermark]
  SCIENTIFIC_REVIEW_PENDING   technically validated; required approvals missing or stale       [preliminary + watermark]
  SCIENTIFICALLY_VALIDATED    every required role validated the claim; not yet cleared to publish [preliminary + watermark]
  APPROVED_FOR_PUBLICATION    every required role approved publication for this exact version   [final, no watermark]
Any change to inputs, spec, caption or renderer makes an approval STALE (never silently reused).
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import inspect
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml

DECISIONS = ("APPROVED_FOR_PUBLICATION", "SCIENTIFICALLY_VALIDATED", "REJECTED")
LIFECYCLE = ("INVALID", "EXECUTION_COMPLETED", "SCIENTIFIC_REVIEW_PENDING", "SCIENTIFICALLY_VALIDATED", "APPROVED_FOR_PUBLICATION")
REPO = Path(__file__).resolve().parents[2]


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def spec_sha256(spec: Dict) -> str:
    """Canonical hash of everything that defines the artifact's claim: selection, columns, caption, limitations."""
    s = {k: v for k, v in spec.items() if k not in ("evidence_status",)}
    return sha_bytes(json.dumps(s, sort_keys=True, default=str).encode("utf-8"))


def renderer_sha256(*objs) -> str:
    parts = []
    for o in objs:
        parts.append(inspect.getsource(o) if not isinstance(o, (str, bytes, Path)) else Path(o).read_text(encoding="utf-8"))
    return sha_bytes("\n".join(parts).encode("utf-8"))


def load_policy(root: Path) -> Dict:
    for p in (Path(root) / "configs" / "publication_policy.yaml", REPO / "configs" / "publication_policy.yaml"):
        if p.exists():
            return yaml.safe_load(p.read_text(encoding="utf-8"))
    raise FileNotFoundError("configs/publication_policy.yaml not found")


def approvals_dir(root: Path) -> Path:
    return Path(root) / "06_audit_preparation" / "publication_approvals"


@dataclass
class Binding:
    artifact_id: str
    input_sha256: Dict[str, str]
    spec_sha256: str
    renderer_sha256: str
    source_run_keys: List[str]

    def as_dict(self) -> Dict:
        return {"input_sha256": dict(sorted(self.input_sha256.items())), "spec_sha256": self.spec_sha256,
                "renderer_sha256": self.renderer_sha256, "source_run_keys": sorted(self.source_run_keys)}


@dataclass
class Status:
    lifecycle: str
    dest: str
    watermark: str
    blockers: List[str] = field(default_factory=list)
    approval_ids: List[str] = field(default_factory=list)
    claim_scope: str = ""


def technical_validation(root: Path, run_dir: Optional[str], run_key: Optional[str], artifact_class: Optional[str],
                         dataset_prov: Optional[Dict] = None) -> tuple:
    """(ok, reason). Model-output artifacts need the lifecycle validator's VALID record for their source run."""
    if artifact_class == "DATASET_DESCRIPTIVE":
        if dataset_prov and dataset_prov.get("preflight_checks") and \
                dataset_prov.get("preflight_checks_passed") == dataset_prov.get("preflight_checks"):
            return True, ""
        return False, "dataset preflight record missing or incomplete"
    if not run_dir or not run_key:
        return False, "source run unknown"
    v = Path(root) / "03_results" / "validation" / f"{run_dir}_{str(run_key)[:12]}.json"
    if not v.exists():
        return False, f"technical validation record missing ({v.name}); run tools/reporting/build_results.py"
    st = json.loads(v.read_text(encoding="utf-8")).get("status")
    return (st == "VALID"), ("" if st == "VALID" else f"technical validation status {st}")


def _valid_date(s) -> bool:
    try:
        _dt.date.fromisoformat(str(s))
        return True
    except ValueError:
        return False


def evaluate(root: Path, binding: Binding, tech_ok: bool, tech_reason: str, run_invalid: bool = False) -> Status:
    policy = load_policy(root)
    aid = binding.artifact_id
    allowed = policy.get("artifact_scopes", {}).get(aid, [])
    if run_invalid:
        return Status("INVALID", "refused", "INVALID - NOT A RESEARCH RESULT", ["source run invalid"])
    if not tech_ok:
        return Status("EXECUTION_COMPLETED", "preliminary", "PRELIMINARY (TECHNICAL VALIDATION PENDING) - NOT A VALIDATED RESULT",
                      [tech_reason])
    blockers, ids, by_scope = [], [], {}
    d = approvals_dir(root) / aid
    current = binding.as_dict()
    for f in sorted(d.glob("*.y*ml")) if d.exists() else []:
        try:
            a = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            blockers.append(f"{f.name}: unreadable approval file")
            continue
        rv = a.get("reviewer") or {}
        name, role, scope, dec = str(rv.get("name", "")), str(rv.get("role", "")), str(a.get("claim_scope", "")), str(a.get("decision", ""))
        problems = []
        if a.get("artifact_id") != aid:
            problems.append("artifact_id mismatch")
        if dec not in DECISIONS:
            problems.append(f"unknown decision {dec!r}")
        if scope not in allowed:
            problems.append(f"claim scope {scope!r} not allowed for {aid} (allowed {allowed})")
        if role not in policy.get("roles", {}) or name not in policy["roles"].get(role, []):
            problems.append(f"reviewer {name!r} is not an authorized {role!r}")
        if not _valid_date(a.get("date")):
            problems.append("missing or invalid date")
        if not str(a.get("statement", "")).strip():
            problems.append("missing review statement")
        stale = [k for k in current if (a.get("binding") or {}).get(k) != current[k]]
        if stale:
            problems.append("STALE: " + ", ".join(stale) + " changed since review")
        if problems:
            blockers.append(f"{f.name}: " + "; ".join(problems))
            continue
        ids.append(str(a.get("approval_id", f.stem)))
        by_scope.setdefault(scope, {}).setdefault(role, set()).add(dec)
    for scope, roles in by_scope.items():
        if any("REJECTED" in decs for decs in roles.values()):
            return Status("INVALID", "refused", "INVALID FOR THE STATED CLAIM", blockers + [f"{scope}: rejected by reviewer"], ids, scope)
    for scope in allowed:
        need = policy.get("required_roles", {}).get(scope, [])
        got = by_scope.get(scope, {})
        if need and all("APPROVED_FOR_PUBLICATION" in got.get(r, set()) for r in need):
            return Status("APPROVED_FOR_PUBLICATION", "final", "", blockers, ids, scope)
    for scope in allowed:
        need = policy.get("required_roles", {}).get(scope, [])
        got = by_scope.get(scope, {})
        if need and all(got.get(r) for r in need):
            missing = [r for r in need if "APPROVED_FOR_PUBLICATION" not in got.get(r, set())]
            return Status("SCIENTIFICALLY_VALIDATED", "preliminary", "SCIENTIFICALLY VALIDATED - NOT APPROVED FOR PUBLICATION",
                          blockers + [f"{scope}: publication approval missing from {missing}"], ids, scope)
    need_txt = "; ".join(f"{s}: {', '.join(policy.get('required_roles', {}).get(s, []))}" for s in allowed) or "artifact not in publication policy"
    return Status("SCIENTIFIC_REVIEW_PENDING", "preliminary", "PRELIMINARY (SCIENTIFIC REVIEW PENDING) - NOT A VALIDATED RESULT",
                  blockers + [f"required approvals: {need_txt}"], ids)


def approval_template(binding: Binding, claim_scope: str, claims: List[str], limitations: List[str]) -> Dict:
    """Unsigned template for an owner sign-off package (reviewer/decision/date/statement left for the reviewer)."""
    return {"approval_id": f"{binding.artifact_id}__{binding.spec_sha256[:8]}__REVIEWER",
            "artifact_id": binding.artifact_id, "claim_scope": claim_scope, "decision": "TO_BE_DECIDED_BY_REVIEWER",
            "approved_claims": claims, "limitations_acknowledged": limitations,
            "reviewer": {"name": "TO_BE_FILLED_BY_REVIEWER", "role": "TO_BE_FILLED_BY_REVIEWER"},
            "date": "YYYY-MM-DD", "statement": "", "binding": binding.as_dict()}
