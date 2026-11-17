"""Evidence-backed H₂-SimNet dependency reconstruction and retrospective split design."""
from __future__ import annotations

import hashlib
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from .data.loader import WORKSPACE_ROOT, RAW_DATASET_DIR, load_scenario
from .independence import independence_groups
from .phase2 import checked_file
from .simnet_study import archive_path, ONTOLOGY

LEDGER = "06_audit_preparation/pre_experiment_review/FAMILY_RELATIONSHIP_EVIDENCE.csv"
EXPOSURE = "03_results/diagnostics/forensics/source_model_attribution.csv"
FORENSICS = "03_results/diagnostics/forensics/FORENSICS_MANIFEST.json"
CONFIRMED = "CONFIRMED_DEPENDENCE"
POTENTIAL = "POTENTIAL_DEPENDENCE"
ROLES = ("HELD_OUT", "MODEL_VALIDATION", "DEVELOPMENT")


def digest(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def edge(a, b, status, relation, reference, detail):
    a, b = sorted((a, b))
    return {"a": a, "b": b, "status": status, "relationship": relation,
            "reference": reference, "detail": detail}


def groups(nodes, edges, include_potential=False):
    nodes = tuple(nodes)
    components = {name: name for name in nodes}

    def root(name):
        while components[name] != name:
            name = components[name]
        return name

    for relation in edges:
        if relation["status"] == CONFIRMED or (include_potential and relation["status"] == POTENTIAL):
            a, b = root(relation["a"]), root(relation["b"])
            components[max(a, b)] = min(a, b)
    members = defaultdict(list)
    for name in sorted(nodes):
        members[root(name)].append(name)
    return {"DEP_" + digest(member)[:16]: member for member in members.values()}


def linked_groups(rows, columns, status, relationship):
    result = []
    for column in columns:
        for token, matches in rows.groupby(column, sort=True):
            if not token:
                continue
            for a, b in itertools.combinations(sorted(set(matches.Scenario_ID)), 2):
                result.append(edge(a, b, status, relationship, f"V03 manifest:{column}", token))
    return result


def build_graph(manifest, verify_trajectories=True):
    if not manifest.Scenario_ID.is_unique:
        raise ValueError("duplicate candidate scenario ID")
    names = set(manifest.Scenario_ID)
    linked = []
    source = defaultdict(set)
    for row in manifest.itertuples(index=False):
        for sha in (row.sha256_clean, row.sha256_noise_added):
            if sha:
                source[sha].add(row.Scenario_ID)
    for sha, matches in sorted(source.items()):
        for a, b in itertools.combinations(sorted(matches), 2):
            linked.append(edge(a, b, CONFIRMED, "SAME_SOURCE_DIGEST", "V03 asset checksums", sha))
    archived = pd.read_csv(WORKSPACE_ROOT / LEDGER, dtype=str, keep_default_na=False)
    for link in archived.itertuples(index=False):
        if link.scenario_a not in names or link.scenario_b not in names:
            raise ValueError(f"unknown scenario in relationship ledger: {link.edge_id}")
        confirmed = link.relationship in {"MISFILED_BYTE_IDENTICAL_COPY", "WEAK_STRONG_SAME_INJECTION",
                                           "SAME_REALIZATION_FORMAT_TWIN",
                                           "CLEAN_VS_NOISE_ADDED_SAME_RUN"}
        # Self edges document file variants; they never create another generating unit.
        linked.append(edge(link.scenario_a, link.scenario_b, CONFIRMED if confirmed else POTENTIAL,
                           link.relationship, f"{LEDGER}#{link.edge_id}",
                           {"confidence": link.confidence, "method": link.method, "evidence": link.evidence,
                            "handling": link.handling, "runtime_parent_identity": "UNVERIFIED"}))
    reconstructed = independence_groups(manifest.Scenario_ID, manifest.Scenario_Family_ID)
    if any(reconstructed[row.Scenario_ID] != row.independence_group for row in manifest.itertuples(index=False)):
        raise ValueError("cross-topology grouping does not reproduce the frozen manifest")
    # Replicated scenario definitions and family tags are conservative design
    # evidence. They do not establish a duplicate trajectory or a common parent.
    linked.extend(linked_groups(manifest, ("independence_group", "family_extended_sensitivity"),
                                POTENTIAL, "DECLARED_RELATED_DESIGN_OR_EXTENDED_FAMILY"))

    fingerprints = defaultdict(list)
    unchecked = []
    noise_checked = 0
    if verify_trajectories:
        for row in manifest.itertuples(index=False):
            try:
                rel = Path(row.file_noise_added).relative_to("H2-SimNet-Dataset")
                if rel.is_absolute() or ".." in rel.parts:
                    raise ValueError("invalid paired archive-relative path")
                checked_file(RAW_DATASET_DIR / rel, row.sha256_noise_added)
                noise_checked += 1
                frame = load_scenario(archive_path(row))
                channels = sorted(c for c in frame if c.startswith(("PS", "MFS")))
                array = frame[channels].to_numpy(dtype="<f8", copy=True)
                array[array == 0] = 0  # neutralize signed zero for identity comparisons
                signature = hashlib.sha256(json.dumps(channels).encode() + array.tobytes()).hexdigest()
                fingerprints[signature].append(row.Scenario_ID)
            except (OSError, ValueError) as error:
                unchecked.append({"scenario": row.Scenario_ID, "reason": str(error)})
        for sha, matches in sorted(fingerprints.items()):
            for a, b in itertools.combinations(sorted(matches), 2):
                linked.append(edge(a, b, CONFIRMED, "IDENTICAL_CLEAN_SENSOR_TRAJECTORY",
                                   "Phase 9 hash of named float64 sensor channels in row order", sha))
    linked.sort(key=lambda item: (item["a"], item["b"], item["reference"], item["relationship"]))
    node_meta = {r.Scenario_ID: {"class": r.label_mapped, "topology": r.topology_source_model,
                                "topology_release": r.topology_release, "clean": r.file_clean,
                                "clean_sha256": r.sha256_clean, "noise_added": r.file_noise_added,
                                "noise_added_sha256": r.sha256_noise_added,
                                "archived_labels": r.raw_label_columns, "physical_parent": None}
                 for r in manifest.sort_values("Scenario_ID").itertuples(index=False)}
    graph = {
        "nodes": node_meta, "edges": linked, "confirmed_components": groups(names, linked),
        "conservative_components": groups(names, linked, True),
        "trajectory_cases_checked": sum(map(len, fingerprints.values())), "trajectory_cases_unchecked": unchecked,
        "noise_assets_checked": noise_checked,
        "unsupported_independent_units": "No parent history or untouched generating record established",
        "unknown_relationships": "Unlisted pairs are UNKNOWN_RELATIONSHIP, not independent",
        "rules": "Union transitive confirmed edges; retrospective split policy also unions potential evidence. "
                 "Do not merge by topology or event class alone.",
        "sources": {LEDGER: hashlib.sha256((WORKSPACE_ROOT / LEDGER).read_bytes()).hexdigest()},
    }
    graph["sha256"] = digest(graph)
    return graph


def split_issues(graph, assignments):
    issues = []
    if not set(assignments) <= set(graph["nodes"]):
        issues.append("UNKNOWN_SCENARIO")
    for group, members in graph["conservative_components"].items():
        if len({assignments[name] for name in members if name in assignments}) > 1:
            issues.append(f"DEPENDENCE_CROSSES_PARTITIONS:{group}")
    return sorted(issues)


def historical_exposure(manifest):
    metadata = json.loads((WORKSPACE_ROOT / FORENSICS).read_text(encoding="utf-8"))
    path = WORKSPACE_ROOT / EXPOSURE
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    if sha != metadata["outputs"][path.name]:
        raise ValueError("forensic case-attribution digest mismatch")
    recorded = set(pd.read_csv(path, usecols=["Scenario_ID"]).Scenario_ID)
    return {"reference": EXPOSURE, "sha256": sha, "inspection_cases": sorted(recorded & set(manifest.Scenario_ID)),
            "confirmatory_status": "NO_PRISTINE_HOLDOUT_ESTABLISHED",
            "caveat": "Historical attribution establishes archive inspection, not exposure to each individual diagnostic outcome."}


def crossing_legacy(manifest, folds, graph):
    answer = []
    index = manifest.set_index("Scenario_ID")
    for fold, items in folds.groupby("outer_fold_id", sort=True):
        assignment = dict(zip(items.Scenario_ID, items.split_role))
        for group_id, runs in manifest.groupby("independence_group", sort=True):
            names = set(runs.Scenario_ID) & assignment.keys()
            if len({assignment[name] for name in names}) < 2:
                continue
            crossing = [e for e in graph["edges"] if e["a"] in names and e["b"] in names and
                        assignment[e["a"]] != assignment[e["b"]]]
            answer.append({"fold": fold, "group": group_id,
                           "members": [{"scenario": name, "partition": assignment[name],
                                        "topology": index.at[name, "topology_source_model"],
                                        "event": index.at[name, "label_mapped"]} for name in sorted(names)],
                           "relationships": crossing,
                           "confirmed_crossing": any(e["status"] == CONFIRMED for e in crossing),
                           "resolution": "keep the conservative component together or obtain producing-run evidence"})
    return answer


def support(graph, members, selected):
    by_class = Counter()
    rows = Counter()
    topologies = Counter()
    for group in members:
        nodes = [graph["nodes"][name] for name in members[group] if name in selected]
        by_class.update({row["class"] for row in nodes})
        rows.update(row["class"] for row in nodes)
        topologies.update(row["topology"] for row in nodes)
    return {"runs": sum(rows.values()), "components": sum(bool(set(members[g]) & selected) for g in members),
            "runs_by_class": dict(rows), "components_by_class": {k: by_class[k] for k in ONTOLOGY},
            "runs_by_topology": dict(topologies)}


def candidate_splits(graph, eligible, manifest_sha256):
    """Generate group-disjoint proposals. Optimize class support before balance."""
    eligible = set(eligible)
    available = {g: [name for name in members if name in eligible]
                 for g, members in graph["conservative_components"].items()}
    available = {g: v for g, v in available.items() if v}
    classes = {g: {graph["nodes"][name]["class"] for name in names}
               for g, names in available.items()}
    frequency = Counter(c for values in classes.values() for c in values)
    topology = {g: {graph["nodes"][name]["topology"] for name in names} for g, names in available.items()}

    def proposal(strategy, by_group):
        assignment = {name: by_group[g] for g in by_group for name in available[g]}
        checks = split_issues(graph, assignment)
        if checks:
            raise ValueError(f"generated unsafe split: {checks}")
        return {"version": "simnet-ancestry-split/1", "strategy": strategy, "status": "PROPOSED",
                "claim": "RETROSPECTIVE_DESCRIPTIVE_ONLY", "manifest_sha256": manifest_sha256,
                "scoring_representatives": "Predeclare one per held-out conservative component before scoring",
                "graph_sha256": graph["sha256"], "group_roles": by_group, "assignments": assignment,
                "support": {r: support(graph, available, {n for n, role in assignment.items() if role == r})
                            for r in sorted(set(by_group.values()))}, "leakage_issues": checks}

    answers = []
    if len(available) >= 3:
        by_group, counts = {}, {r: Counter() for r in ROLES}
        role_topologies = {r: set() for r in ROLES}
        for g in sorted(available, key=lambda x: (min(frequency[c] for c in classes[x]), -len(classes[x]), x)):
            role = max(ROLES, key=lambda r: (sum(1/frequency[c] for c in classes[g] if not counts[r][c]),
                                             len(topology[g] - role_topologies[r]), -sum(counts[r].values())))
            by_group[g] = role
            counts[role].update(classes[g])
            role_topologies[role].update(topology[g])
        if set(by_group.values()) == set(ROLES):
            answers.append(proposal("DETERMINISTIC_THREE_WAY", by_group))
    if len(available) >= 4:
        normal = next((g for g in sorted(available) if "NORMAL" in classes[g]), None)
        leak = next((g for g in sorted(available) if g != normal and "LEAK" in classes[g]), None)
        if normal and leak:
            remaining = sorted(set(available) - {normal, leak})
            answers.append(proposal("NORMAL_LEAK_DESCRIPTIVE_HOLDOUT", {
                normal: "HELD_OUT", leak: "HELD_OUT", remaining[0]: "MODEL_VALIDATION",
                **{g: "DEVELOPMENT" for g in remaining[1:]},
            }))
    if len(available) >= 2:
        answers.extend(proposal("LEAVE_ONE_COMPONENT_OUT", {
            g: "HELD_OUT" if g == held else "DEVELOPMENT" for g in available
        }) for held in sorted(available))
    return answers
