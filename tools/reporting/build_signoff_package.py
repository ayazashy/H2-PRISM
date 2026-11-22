#!/usr/bin/env python3
"""
Owner sign-off package for the current result artifacts (A13 lifecycle). Writes, never approves:

  06_audit_preparation/publication_signoff/
    SIGNOFF_PACKAGE.md                one row per artifact: source run(s), lifecycle state, numerical-validity evidence,
                                      allowed claim scope, required approvers, limitations, exact blockers
    templates/<artifact_id>.yaml      UNSIGNED approval template with the artifact's CURRENT binding hashes; a reviewer
                                      fills decision / name / role / date / statement and saves it under
                                      06_audit_preparation/publication_approvals/<artifact_id>/

Bindings come from the builders' own functions (figure_binding / table_binding), so a template signed unchanged
matches exactly what the next build renders; any later change to data, spec, caption or renderer makes it stale.
Usage: python tools/reporting/build_signoff_package.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_research_figures as brf  # noqa: E402
import build_research_tables as brt  # noqa: E402
import publication as pub  # noqa: E402

REPO = HERE.parents[1]
CONFIGS = [REPO / "configs" / "reporting_dataset_figures.yaml", REPO / "configs" / "reporting_figures.yaml"]
OUT = REPO / "06_audit_preparation" / "publication_signoff"
EVIDENCE = {  # numerical-validity evidence that exists in the repository for each artifact
    "fig1_dataset_and_design": "tests/test_figure_system.py::test_dataset_design_bars_equal_source_counts; dataset preflight",
    "fig2_rq1_risk_coverage": "tests/test_figure_system.py (risk-coverage correspondence; topology panels never crop); 42/42 R2 recomputations",
    "fig3_rq1_incremental_value": "rq1.csv all NOT_ESTIMABLE; 03_results/diagnostics/PRIMARY_a10530f1fcf2/rq1_pooled_reasons.csv",
    "fig4_rq2_three_outcome": "derived tables reproduce registered rq2.csv (DERIVED_MANIFEST cross_checks); tests/test_figure_system.py Fig. 4 tests",
    "fig5_error_structure": "confusion counts equal R2 confusion_matrix.csv (42/42 recomputations incl. confusion)",
    "fig6_robustness": "sensitivity_summary.csv from 7 VALID runs + 1 RUN_INCOMPLETE; RESULTS_INDEX.csv",
}


def _rows():
    for cfg_p in CONFIGS:
        cfg = yaml.safe_load(cfg_p.read_text(encoding="utf-8"))
        for spec in cfg.get("figures", []):
            yield "figure", spec, brf.figure_binding(REPO, spec)
        for spec in cfg.get("tables", []):
            yield "table", spec, brt.table_binding(REPO, spec)


def main() -> int:
    policy = pub.load_policy(REPO)
    (OUT / "templates").mkdir(parents=True, exist_ok=True)
    lines = ["# Publication sign-off package (generated; NOT an approval)", "",
             "Each artifact leaves `preliminary/` only when every required role signs an approval bound to the hashes in its",
             "template (`templates/<artifact>.yaml`). Copy the template to",
             "`06_audit_preparation/publication_approvals/<artifact>/<reviewer>.yaml`, set `decision`",
             "(APPROVED_FOR_PUBLICATION / SCIENTIFICALLY_VALIDATED / REJECTED), `reviewer.name`, `reviewer.role`, `date` and",
             "`statement`, and rebuild with `python tools/reporting/build_results.py`. Do not edit `binding`.", "",
             "| Artifact | Source run(s) | Lifecycle now | Allowed scope | Required approvers | Numerical-validity evidence | Blockers |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for kind, spec, (b, ok, why, invalid) in _rows():
        st = pub.evaluate(REPO, b, ok, why, invalid)
        scopes = policy.get("artifact_scopes", {}).get(spec["id"], [])
        need = sorted({f"{r} ({', '.join(policy['roles'][r])})" for s in scopes for r in policy["required_roles"].get(s, [])})
        tmpl = pub.approval_template(b, scopes[0] if scopes else "NOT_PUBLISHABLE",
                                     [spec.get("caption", "").strip()], [spec.get("limitations", "")])
        (OUT / "templates" / f"{spec['id']}.yaml").write_text(
            "# UNSIGNED TEMPLATE - not an approval. See SIGNOFF_PACKAGE.md.\n" + yaml.safe_dump(tmpl, sort_keys=False, width=120),
            encoding="utf-8")
        ev = EVIDENCE.get(spec["id"], "values copied verbatim from the source table (tests/test_reporting_outputs.py::test_values_preserved_in_tables)")
        runs = ", ".join(k[:12] for k in b.source_run_keys)
        lines.append(f"| `{spec['id']}` | {runs} | {st.lifecycle} | {', '.join(scopes) or '-'} | {'; '.join(need) or '-'} | {ev} | "
                     f"{' / '.join(st.blockers).replace('|', '/')} |")
    (OUT / "SIGNOFF_PACKAGE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
