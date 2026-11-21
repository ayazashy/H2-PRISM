#!/usr/bin/env python3
"""
Registered protocol 2.0 ablation program: one development-only config per arm + the experiment matrix.

Writes 06_audit_preparation/protocol2/arms/<ARM_ID>.yaml (status DEVELOPMENT_ARM_REGISTERED) and
06_audit_preparation/protocol2/ABLATION_MATRIX.{csv,md}. Every arm = the pinned protocol 1.1 config + COMMON evaluation
settings + exactly its own intervention (G1/G2 are the only prespecified combinations; 8 arms in total, fixed here
before any arm is run). No arm is run by this script; each needs an authorization scoped
DEVELOPMENT_EXPERIMENT:<ARM_ID> bound to the arm config's SHA-256.
Usage: python tools/dataset/build_ablation_arms.py
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[2]
BASE = REPO / "06_audit_preparation" / "FINAL_EXPERIMENT_CONFIG.yaml"
P2 = REPO / "06_audit_preparation" / "protocol2"
COMMON_CHANNELS = ["PS1", "PS2", "PS3", "PS4", "PS5", "PS6", "PS7", "PS8", "PS9", "PS10", "MFS1", "MFS2", "MFS3"]


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def interventions():
    man, folds = P2 / "CANDIDATE_MANIFEST_V03.csv", P2 / "CANDIDATE_OUTER_FOLDS_V03.csv"
    topo = {"dataset.manifest": {"file": man.relative_to(REPO).as_posix(), "sha256": _sha(man)},
            "dataset.topology_column": "topology_source_model",
            "splits.outer": {"file": folds.relative_to(REPO).as_posix(), "sha256": _sha(folds), "design": "leave_one_topology_out"},
            "splits.inner": {"scheme": "LOTO_within_train", "note": "derived by the runner"}}
    return {"B": topo, "C": {"features.channels": COMMON_CHANNELS},
            "D": {"distinguishability.support_unit": "independence_group"},
            "E": {"policy_primary.evidence_conflict": "ambiguity_pair"},
            "F": {"distinguishability.statistic": "evidence_margin", "distinguishability.evidence_min_units": 2}}


COMMON = {  # identical in EVERY arm (evaluation rules, not interventions)
    "combined_scores.on_undefined": "not_estimable",
    "thresholds.target_rule": {"grid": [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3], "margin": 0.05, "min_target": 0.3},
}

ARMS = [  # arm_id, interventions, question, targeted failure mechanism, prespecified acceptance criterion
    ("A_P11_DEV", [], "What do the development-stage metrics of protocol 1.1 look like under the common evaluation rules?",
     "reference", "reference arm: no criterion; every other arm is compared with it fold by fold"),
    ("B_TOPOLOGY", ["B"], "Does attributing runs to their source simulation model remove the configuration-swap failure?",
     "FA-01 swapped Center/Downstream event folders",
     "dev AUROC of confidence for correctness >= 0.5 in every development topology AND share of errors with confidence >= 0.9 lower than A"),
    ("C_COMMON_SENSORS", ["C"], "Does restricting inputs to sensors present in every model remove the padded-channel fingerprint without losing performance?",
     "FA-02 zero-variance padded channels",
     "no padded channel among model inputs (structural) AND dev group-balanced accuracy not lower than A by more than 0.05"),
    ("D_GROUP_SUPPORT", ["D"], "Does counting support by scenario independence group remove pseudo-independent support, and at what coverage cost?",
     "FA-03 cross-topology replicas counted as independent",
     "pseudo-independent support = 0 (structural) AND dev group-balanced selective risk not higher than A; coverage change reported, not optimised"),
    ("E_EVIDENCE_CONFLICT", ["E"], "Does withholding SPECIFIC when classifier and evidence disagree reduce wrong SPECIFIC decisions without hiding the true class?",
     "FA-05 policy never checks D top class against the label",
     "dev group-balanced selective risk lower than A at the same dev-fixed target AND ambiguity-set inclusion >= 0.9 where sets are issued"),
    ("F_EVIDENCE_MARGIN", ["F"], "Does the signed, group-balanced evidence margin E_h discriminate correctness better than D(x), and does it add value to s_C?",
     "FA-04/FA-09 D(x) saturation and anti-information under shift",
     "dev AUROC(E) > AUROC(D_only of A) by >= 0.05 in every development topology where defined AND AUROC(s_C) - AUROC(s_C_minus_D) > 0"),
    ("G1_DATA_CORRECTIONS", ["B", "C"], "Combined data-level corrections (topology attribution + common sensors).",
     "FA-01 + FA-02", "same as B and C jointly (combination effect, not one-factor attribution)"),
    ("G2_FULL_CANDIDATE", ["B", "C", "D", "E", "F"], "The complete candidate protocol 2.0 at development stage.",
     "all", "every component criterion holds jointly AND the primary metric is not worse than A; otherwise report which component fails"),
]


def _apply(cfg, changes):
    for k, v in changes.items():
        a, b = k.split(".", 1)
        cfg.setdefault(a, {})[b] = copy.deepcopy(v)


def build() -> pd.DataFrame:
    base = yaml.safe_load(BASE.read_text(encoding="utf-8"))
    iv = interventions()
    out = P2 / "arms"
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for arm_id, comps, question, mech, accept in ARMS:
        c = copy.deepcopy(base)
        _apply(c, COMMON)
        for comp in comps:
            _apply(c, iv[comp])
        c["status"] = "DEVELOPMENT_ARM_REGISTERED"
        c["arm_id"] = arm_id
        c["version"] = f"protocol-2.0-ablation:{arm_id}"
        c["derived_from"] = {"file": BASE.relative_to(REPO).as_posix(), "sha256": _sha(BASE)}
        p = out / f"{arm_id}.yaml"
        p.write_text(f"# Registered DEVELOPMENT-ONLY ablation arm {arm_id} (tools/dataset/build_ablation_arms.py).\n"
                     "# Runs only with: run_primary_protocol.py --develop --authorization <file scoped DEVELOPMENT_EXPERIMENT:"
                     f"{arm_id}>.\n" + yaml.safe_dump(c, sort_keys=False), encoding="utf-8")
        rows.append({"arm_id": arm_id, "components": "+".join(comps) or "none (protocol 1.1)", "scientific_question": question,
                     "targeted_failure": mech, "acceptance_criterion": accept,
                     "primary_metric": "group-balanced selective risk of s_C at the development-fixed target (per development topology)",
                     "population": "all 51 eligible runs / 27,993 windows; development data of each outer fold (inner topology-held-out predictions)",
                     "grouping": "outer and inner leave-one-topology-out; independence groups for scenario-level metrics",
                     "evidence_status": "EXPLORATORY_DEVELOPMENT (all windows were inspected as R2 outer-test data; never confirmatory)",
                     "one_factor": "yes" if len(comps) <= 1 else "no (prespecified combination)",
                     "requires_dataset_decision": "yes (uses candidate manifest v0.3; exploratory only until R-18 option B)" if "B" in comps else "no",
                     "config_file": p.relative_to(REPO).as_posix(), "config_sha256": _sha(p),
                     "authorization_scope": f"DEVELOPMENT_EXPERIMENT:{arm_id}", "run_dir": f"03_results/ablation_runs/{arm_id}"})
    m = pd.DataFrame(rows)
    m.to_csv(P2 / "ABLATION_MATRIX.csv", index=False, lineterminator="\n")
    lines = ["# Protocol 2.0 ablation matrix (registered before any arm is run)", "",
             "- Common to every arm: " + json.dumps(COMMON) + ".",
             "- Metrics are fixed in `src/h2prism/evaluation_metrics.py`. Arms run development-only (`--develop`), so no outer-test topology is scored.",
             "- All results are EXPLORATORY: every window was an R2 outer-test window. Confirmation requires the independent data in "
             "`02_methodology/INDEPENDENT_CONFIRMATION_DATA_SPEC.md`.", "",
             "| Arm | Components | Question | Targeted failure | Acceptance criterion | Needs dataset decision |", "| --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        lines.append(f"| `{r['arm_id']}` | {r['components']} | {r['scientific_question']} | {r['targeted_failure']} | "
                     f"{r['acceptance_criterion']} | {r['requires_dataset_decision']} |")
    (P2 / "ABLATION_MATRIX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return m


if __name__ == "__main__":
    m = build()
    print(m[["arm_id", "components", "config_sha256"]].assign(config_sha256=lambda d: d.config_sha256.str[:12]).to_string(index=False))
