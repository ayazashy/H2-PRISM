"""Scientific tests of the A13 figure/table system (selected figures: 05_documentation/FIGURE_SPECIFICATION.md).

Model-output figures are built from SYNTHETIC runner outputs in a temporary tree and must be routed to
illustrative/; they are never written into the repository's 03_results/. Tests check meaning, not only files:
plotted values are extracted from the Matplotlib artists and compared with the recorded source tables.
"""

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402
import yaml  # noqa: E402

from h2prism.experiments import primary_protocol as pp  # noqa: E402
from h2prism.experiments.synthetic_protocol_fixture import make_fixture  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "reporting"))
import build_dataset_design_tables as bdd  # noqa: E402
import build_research_figures as brf  # noqa: E402
import build_research_tables as brt  # noqa: E402
import build_sensitivity_summary as bss  # noqa: E402
from _common import ReportingInputError  # noqa: E402

RES_CFG = ROOT / "configs" / "reporting_figures.yaml"
DS_CFG = ROOT / "configs" / "reporting_dataset_figures.yaml"
PROV = ["figure_id", "title", "run_id", "input_file", "input_sha256", "script", "function", "command", "config_sha256",
        "build_git_commit", "protocol_config_sha256", "manifest_sha256", "generated_at_utc", "output_sha256", "units",
        "metric_definition", "limitations", "artifact_class", "environment", "caption"]


@pytest.fixture(scope="module")
def tree(tmp_path_factory):
    root = tmp_path_factory.mktemp("figs")
    fx = make_fixture(root / "fx")
    runs = root / "03_results" / "primary_protocol"
    pp.run(fx["config"], fx["root"], fx["raw"], runs / "PRIMARY", "synthetic")
    pp.run(fx["config"], fx["root"], fx["raw"], runs / "SENSITIVITY_k_10", "synthetic", sensitivity="k_10")
    pp.run(fx["config"], fx["root"], fx["raw"], runs / "SENSITIVITY_windows_60_60", "synthetic", sensitivity="windows_60_60")
    assert bss.main(["--runs", str(runs), "--out", str(runs / "SENSITIVITY_SUMMARY"), "--allow-synthetic"]) == 0
    bdd.build(fx["config"], fx["root"], fx["raw"], root / "03_results" / "dataset_design")
    return root


def _p(root, name):
    return root / "03_results" / "primary_protocol" / "PRIMARY" / name


def _dfs(root, spec):
    out = {}
    for k, v in brf._inputs(spec).items():
        df = pd.read_csv(root / v["input"])
        for c, val in (v.get("filter") or {}).items():
            df = df[df[c].astype(str).isin([str(x) for x in (val if isinstance(val, list) else [val])])]
        out[k] = df.reset_index(drop=True)
    return out


def _spec(cfg, fid):
    return next(f for f in yaml.safe_load(cfg.read_text(encoding="utf-8"))["figures"] if f["id"] == fid)


# ---------------------------------------------------------------- build, routing, provenance
def test_selected_result_figures_build_and_stay_illustrative(tree, tmp_path):
    man = brf.build(RES_CFG, tmp_path / "out", tree)
    ids = [f["id"] for f in yaml.safe_load(RES_CFG.read_text(encoding="utf-8"))["figures"]]
    assert set(man.figure_id) == set(ids) and 4 <= len(ids) <= 7  # a small, justified set
    assert set(man.status) == {"BUILT_ILLUSTRATIVE"} and set(man.artifact_class) == {"SYNTHETIC_TEST"}
    assert not (tmp_path / "out" / "final").exists() and not (tmp_path / "out" / "preliminary").exists()
    for f in man.output_file:
        assert Path(f).exists() and Path(f).stat().st_size > 5000, f
    assert set(Path(f).suffix for f in man.output_file) == {".png", ".pdf", ".svg"}


def test_manifest_provenance_complete_and_traceable(tree, tmp_path):
    man = brf.build(RES_CFG, tmp_path / "out", tree)
    assert set(PROV) <= set(man.columns)
    for c in ("figure_id", "title", "run_id", "input_sha256", "output_sha256", "command", "function", "units", "metric_definition"):
        assert man[c].notna().all() and (man[c].astype(str) != "").all(), c
    for r in man.itertuples():  # every recorded input hash equals the file on disk (plot-to-source correspondence)
        files, hashes = r.input_file.split(";"), r.input_sha256.split(";")
        assert [brf.sha256_path(tree / f) for f in files] == hashes
    assert (tmp_path / "out" / "FIGURE_MANIFEST.csv").exists()


def test_synthetic_inputs_refused_in_official_tree(tree, monkeypatch):
    monkeypatch.setattr(brf, "REPO", tree)  # the temp root's 03_results/ plays the official tree
    with pytest.raises(ReportingInputError, match="refused for official output"):
        brf.build(RES_CFG, tree / "03_results" / "figures" / "primary", tree)
    assert not (tree / "03_results" / "figures" / "primary" / "illustrative").exists()
    with pytest.raises(ReportingInputError, match="refused for official output"):
        brt.build(RES_CFG, tree / "03_results" / "tables" / "primary", tree)


def test_missing_run_fails_and_empty_selection_is_not_estimable(tree, tmp_path):
    spec = dict(_spec(RES_CFG, "fig4_rq2_three_outcome"))
    spec["inputs"] = {**spec["inputs"], "rq2": {"input": spec["inputs"]["rq2"]["input"], "filter": {"target": 0.123}}}
    cfg = tmp_path / "c.yaml"
    cfg.write_text(yaml.safe_dump({"dpi": 60, "figures": [spec]}))
    man = brf.build(cfg, tmp_path / "o", tree)
    assert man.non_estimable.all() and (man.n_rows_plotted == 0).all()
    spec["inputs"]["rq2"] = {"input": "03_results/primary_protocol/PRIMARY/absent.csv"}
    cfg.write_text(yaml.safe_dump({"dpi": 60, "figures": [spec]}))
    with pytest.raises(ReportingInputError, match="mandatory input missing"):
        brf.build(cfg, tmp_path / "o2", tree)


def test_reproducible_exports(tree, tmp_path):
    a = brf.build(RES_CFG, tmp_path / "a", tree)
    b = brf.build(RES_CFG, tmp_path / "b", tree)
    assert a.output_sha256.tolist() == b.output_sha256.tolist()


# ---------------------------------------------------------------- scientific correspondence
def test_risk_coverage_plots_exactly_the_attainable_pooled_points(tree):
    spec = _spec(RES_CFG, "fig2_rq1_risk_coverage")
    brf.st.apply()
    fig, n, _ = brf.plot_risk_coverage_panels(_dfs(tree, spec), spec)
    ax = fig.axes[0]
    curve = pd.read_csv(_p(tree, "risk_coverage_curve.csv"))
    pooled = curve[(curve.scope == "pooled") & (curve.variant == "primary") & (curve.status == "ESTIMABLE")]
    lines = {l.get_label(): l for l in ax.get_lines() if not l.get_label().startswith("_")}
    for m in spec["methods"]:
        exp = pooled[pooled.method == m].sort_values("coverage")
        got = lines[brf.st.method_style(m)["label"]]
        np.testing.assert_allclose(got.get_xdata(), exp.coverage)
        np.testing.assert_allclose(got.get_ydata(), exp.selective_risk)
    assert max(max(l.get_xdata()) for l in lines.values()) <= pooled.coverage.max() + 1e-12  # never extrapolated
    assert len(fig.axes) == 1 + curve[curve.scope != "pooled"].scope.nunique()  # one panel per held-out topology
    plt.close(fig)


def test_matched_coverage_markers_only_for_targets_estimable_in_every_fold(tree):
    spec = _spec(RES_CFG, "fig2_rq1_risk_coverage")
    fig, _, _ = brf.plot_risk_coverage_panels(_dfs(tree, spec), spec)
    cr = pd.read_csv(_p(tree, "coverage_risk.csv"))
    ok = cr[(cr.variant == "primary") & (cr["mode"] == "rank_matched") & cr.method.isin(spec["methods"])]
    ok = ok[ok.folds_estimable == ok.folds_estimable.max()]
    markers = [l for l in fig.axes[0].get_lines() if l.get_label().startswith("_") and l.get_linestyle() == "None"]
    xs = sorted(float(x) for l in markers for x in l.get_xdata())
    np.testing.assert_allclose(xs, sorted(ok.coverage))
    plt.close(fig)


def test_incremental_value_points_equal_rq1_and_non_estimable_are_labelled(tree):
    spec = _spec(RES_CFG, "fig3_rq1_incremental_value")
    d = _dfs(tree, spec)
    fig, n, n_ne = brf.plot_incremental_value(d, spec)
    est = d["rq1"][d["rq1"].status == "ESTIMABLE"]
    xs = sorted(float(c.lines[0].get_xdata()[0]) for c in fig.axes[0].containers)  # data markers, not error-bar caps
    np.testing.assert_allclose(xs, sorted(est.difference))
    labels = [t for t in fig.axes[0].texts if t.get_text() == "not estimable"]
    assert len(labels) == n_ne == int((d["rq1"].status != "ESTIMABLE").sum())
    assert set(d["rq1"].comparison_b) == {"s_C_minus_D", "confidence", "margin", "neg_entropy", "D_only"}  # nothing omitted
    plt.close(fig)


def test_three_outcome_shares_match_rq2_and_sum_to_one(tree):
    spec = _spec(RES_CFG, "fig4_rq2_three_outcome")
    d = _dfs(tree, spec)
    fig, _, _ = brf.plot_three_outcome(d, spec)
    t, _ = brf._display_target(d["rq2"].target.unique(), brf.REGISTERED_TARGETS)
    g = d["rq2"][d["rq2"].target == t].set_index("class")
    widths = {}
    for p in fig.axes[0].patches:
        widths.setdefault(round(p.get_y() + p.get_height() / 2, 6), []).append(p.get_width())
    order = [c for c in brf.st.CLASS_ORDER if c in g.index]
    for i, c in enumerate(order):
        w = widths[round(float(i), 6)]
        np.testing.assert_allclose(w, g.loc[c, ["specific", "ambiguity_set", "unresolved"]].astype(float).to_numpy())
        assert abs(sum(w) - 1) < 1e-9
    plt.close(fig)


def test_error_structure_counts_match_confusion_table(tree):
    spec = _spec(RES_CFG, "fig5_error_structure")
    d = _dfs(tree, spec)
    fig, _, _ = brf.plot_error_structure(d, spec)
    shown = sorted(int(t.get_text().split("n=")[1].rstrip(")")) for t in fig.axes[0].texts if "n=" in t.get_text())
    assert shown == sorted(d["confusion"].n.astype(int))
    plt.close(fig)


def test_robustness_lists_every_registered_analysis_and_marks_populations(tree):
    spec = _spec(RES_CFG, "fig6_robustness")
    d = _dfs(tree, spec)
    fig, n, _ = brf.plot_robustness(d, spec)
    ticks = [t.get_text() for t in fig.axes[0].get_yticklabels()]
    assert {"primary", "policy_warning_only", "k_10", "windows_60_60", "offset_invariant_features"} <= set(ticks)
    s = d["summary"]
    assert set(s[s.analysis == "windows_60_60"].population_note.str[:9]) == {"different"}
    assert "not run" in {t.get_text() for t in fig.axes[0].texts}
    plt.close(fig)


def test_dataset_design_bars_equal_source_counts(tree):
    spec = _spec(DS_CFG, "fig1_dataset_and_design")
    d = _dfs(tree, spec)
    fig, _, _ = brf.plot_dataset_design(d, spec)
    tot = d["classes"][d["classes"].topology == "ALL"].set_index("class")
    heights = [p.get_height() for p in fig.axes[1].patches]
    np.testing.assert_allclose(sorted(heights), sorted(tot.n_windows.astype(float)))
    topo = d["classes"][d["classes"].topology != "ALL"]
    np.testing.assert_allclose(sorted(p.get_height() for p in fig.axes[0].patches), sorted(topo.n_runs.astype(float)))
    plt.close(fig)


def test_every_panel_has_labelled_axes(tree):
    for cfg in (RES_CFG, DS_CFG):
        for spec in yaml.safe_load(cfg.read_text(encoding="utf-8"))["figures"]:
            fig, _, _ = brf.KINDS[spec["kind"]][0](_dfs(tree, spec), spec)
            for ax in fig.axes:
                if ax.get_label() == "<colorbar>" or not ax.get_visible():
                    continue
                has_note = any("not estimable" in t.get_text().lower() or "no " in t.get_text().lower() for t in ax.texts)
                assert ax.get_title(loc="left") or ax.get_title(), (spec["id"], "untitled panel")
                assert ax.get_xlabel() or has_note or ax.get_xticklabels(), (spec["id"], "unlabelled x")
            plt.close(fig)


# ---------------------------------------------------------------- tables
def test_tables_preserve_values_and_mark_non_estimable(tree, tmp_path):
    man = brt.build(RES_CFG, tmp_path / "t", tree)
    assert set(man.status) == {"BUILT_ILLUSTRATIVE"}
    src = pd.read_csv(_p(tree, "rq1.csv"))
    src = src[src.variant == "primary"]
    out = pd.read_csv(tmp_path / "t" / "illustrative" / "T5_rq1_effects.csv")
    np.testing.assert_allclose(out.difference.to_numpy(float), src.difference.to_numpy(float), equal_nan=True)
    md = (tmp_path / "t" / "illustrative" / "T5_rq1_effects.md").read_text(encoding="utf-8")
    assert "n.e." in md and "SYNTHETIC" in md


# ---------------------------------------------------------------- official repository tree
def test_official_dataset_outputs_trace_to_current_sources():
    for d, f in ((ROOT / "03_results" / "figures" / "dataset_design", "FIGURE_MANIFEST.csv"),
                 (ROOT / "03_results" / "tables" / "dataset_design", "TABLE_MANIFEST.csv")):
        man = pd.read_csv(d / f)
        assert set(man.status) == {"BUILT_FINAL"} and set(man.artifact_class) == {"DATASET_DESCRIPTIVE"}
        for r in man.itertuples():
            for inp, h in zip(r.input_file.split(";"), str(r.input_sha256).split(";")):
                assert brf.sha256_path(ROOT / inp) == h, inp
            assert brf.sha256_path(ROOT / r.output_file) == r.output_sha256
    prov = json.loads((ROOT / "03_results" / "dataset_design" / "provenance.json").read_text())
    assert prov["config_sha256"] == "f788b6d870183303b4478b2852858e270074cd1d716398e6058b6c650b234aae"


def test_official_tree_has_no_synthetic_or_unauthorized_results():
    runs = ROOT / "03_results" / "primary_protocol"  # real model results only from authorized runs
    for m in (runs.glob("*/run_manifest.json") if runs.exists() else []):
        man = json.loads(m.read_text(encoding="utf-8"))
        assert man.get("artifact_class") != "SYNTHETIC_TEST", m
        assert man.get("run_key") == "sensitivity_summary" or man.get("authorization"), m
    for m in list((ROOT / "03_results").rglob("FIGURE_MANIFEST.csv")) + list((ROOT / "03_results").rglob("TABLE_MANIFEST.csv")):
        man = pd.read_csv(m)
        assert not man.status.astype(str).str.contains("ILLUSTRATIVE").any(), m
        assert "SYNTHETIC_TEST" not in set(man.artifact_class.dropna()), m


# ---------------------------------------------------------------- results lifecycle (build_results.py)
import build_results as bres  # noqa: E402


def test_lifecycle_builds_versioned_outputs_and_preserves_history(tree, tmp_path):
    qa = tmp_path / "qa"
    r1 = bres.run(tree, qa, allow_synthetic=True)
    assert r1["status"] == "BUILT"
    idx = pd.read_csv(qa / "RESULTS_INDEX.csv")
    assert set(idx[idx.run_dir == "PRIMARY"].status) == {"VALID"} and (idx.n_failed == 0).all()
    ver = qa / "figures" / "primary" / r1["version"]
    assert (ver / "reporting_config_used.yaml").exists() and (ver / "FIGURE_MANIFEST.csv").exists()
    before = {p: p.read_bytes() for p in ver.rglob("*.png")}
    r2 = bres.run(tree, qa, allow_synthetic=True)  # same run again: never overwritten
    assert r2["status"] == "UNCHANGED" and all(p.read_bytes() == b for p, b in before.items())


def test_lifecycle_rejects_synthetic_and_unauthorized_runs_for_official_tree(tree, monkeypatch):
    monkeypatch.setattr(brf, "REPO", tree)
    with pytest.raises(SystemExit, match="cannot write into the official"):
        bres.run(tree, tree / "03_results", allow_synthetic=True)
    with pytest.raises(SystemExit, match="PRIMARY run missing or INVALID"):
        bres.run(tree, tree / "03_results", allow_synthetic=False)
    v = json.loads(next((tree / "03_results" / "validation").glob("PRIMARY_*.json")).read_text())
    assert {c["check"] for c in v["checks"] if not c["ok"]} == {"execution_class"}


def test_incomplete_run_is_invalid_and_refused_by_official_builders(tree, tmp_path, monkeypatch):
    import shutil
    root = tmp_path / "r"
    shutil.copytree(tree / "03_results" / "primary_protocol" / "PRIMARY", root / "03_results" / "primary_protocol" / "PRIMARY")
    mp = root / "03_results" / "primary_protocol" / "PRIMARY" / "run_manifest.json"
    m = json.loads(mp.read_text())
    m.update(status="RUNNING", artifact_class="PRIMARY_EXPERIMENT")
    mp.write_text(json.dumps(m))
    for c in mp.parent.glob("*.csv"):  # isolate the status guard from the synthetic guard
        if c.stat().st_size > 1:
            df = pd.read_csv(c)
            if "artifact_class" in df.columns:
                df.assign(artifact_class="PRIMARY_EXPERIMENT").to_csv(c, index=False)
    v = bres.validate_run(mp.parent, False, bres._sha(bres.PINNED_CONFIG))
    failed = {c["check"] for c in v["checks"] if not c["ok"]}
    assert v["status"] == "INVALID" and {"status_completed", "authorization_recorded", "protocol_config_is_pinned"} <= failed
    monkeypatch.setattr(brf, "REPO", root)
    with pytest.raises(ReportingInputError, match="COMPLETED required"):
        brf.build(RES_CFG, root / "03_results" / "figures" / "primary", root)


def test_lifecycle_refuses_when_no_run_exists(tmp_path):
    with pytest.raises(SystemExit, match="no recorded runs"):
        bres.run(tmp_path, tmp_path / "qa", allow_synthetic=True)


def test_runner_records_authorization_only_for_authorized_execution(tree):
    m = json.loads((tree / "03_results" / "primary_protocol" / "PRIMARY" / "run_manifest.json").read_text())
    assert "authorization" in m and m["authorization"] is None  # synthetic run: no authorization recorded


def test_all_not_estimable_rq1_keeps_full_schema_and_builds_ne_panels(tmp_path):
    """Real primary run 2026-11-11: every pooled RQ1 comparison was NOT_ESTIMABLE, and rq1.csv lacked numeric columns."""
    rows = [{"fold": 1, "variant": "primary", "method": m, "target": 0.8, "mode": "rank_matched",
             "status": "NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL", "test_max_attainable_coverage": 0.2} for m in ("s_C", "s_C_minus_D")]
    preds = pd.DataFrame({"window_id": ["w0"], "y_true": ["LEAK"], "Scenario_Family_ID": ["f"], "topology": ["T"], "fold": [1]})
    agg = pp.aggregate({"dataset": {"classes": ["NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"]}}, preds, rows, "SYNTHETIC_TEST")
    assert set(pp.RQ1_COLUMNS) <= set(agg["rq1"].columns) and agg["rq1"].difference.isna().all()
    legacy = pd.DataFrame({"comparison_b": ["s_C_minus_D"], "variant": ["primary"], "target": [0.8], "mode": ["rank_matched"],
                           "status": ["NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL"]})  # schema written before the fix
    (tmp_path / "r").mkdir()
    legacy.to_csv(tmp_path / "r" / "rq1.csv", index=False)
    cfg = tmp_path / "c.yaml"
    cfg.write_text(yaml.safe_dump({"dpi": 60, "figures": [{"id": "x", "kind": "incremental_value", "inputs": {"rq1": {"input": "r/rq1.csv"}},
                                                         "evidence_status": "PENDING", "title": "t"}]}))
    man = brf.build(cfg, tmp_path / "o", tmp_path)
    assert man.non_estimable.all() and (man.n_rows_plotted == 0).all()


def test_lifecycle_versions_secondary_runs_and_writes_results_provenance(tree, tmp_path):
    """Validated secondary runs give a new version key (PRIMARY key + hash of the run set); F13 RESULTS_PROVENANCE
    lists every run file with hashes taken from that run's manifest (never UNKNOWN for config/manifest/folds)."""
    r = bres.run(tree, tmp_path / "qa", allow_synthetic=True)
    idx = pd.read_csv(tmp_path / "qa" / "RESULTS_INDEX.csv")
    assert (idx.run_dir != "PRIMARY").any() and "_s" in r["version"]
    prov = pd.read_csv(tmp_path / "qa" / "RESULTS_PROVENANCE.csv")
    runs = tree / "03_results" / "primary_protocol"
    files = {p.relative_to(tree).as_posix() for d in ("PRIMARY", "SENSITIVITY_k_10") for p in (runs / d).rglob("*") if p.is_file()}
    assert files <= set(prov.output_file)
    assert prov.config_hash.notna().all() and (prov.config_hash != "UNKNOWN").all() and prov.folds_hash.notna().all()


def test_risk_coverage_topology_panels_never_crop_values():
    """Regression (real run 2026-11-11): the shared y-axis took the LAST panel's 0-0.05 limit and cropped Center."""
    rows = []
    for scope, risk in (("pooled", 0.15), ("Center", 0.44), ("Downstream", 0.0), ("Upstream", 0.0)):
        for m in ("s_C", "s_C_minus_D", "confidence"):
            for c in (0.05, 0.25):
                rows.append({"scope": scope, "variant": "primary", "method": m, "mode": "rank_matched", "coverage_requested": c,
                             "status": "ESTIMABLE", "n_total": 100, "n_specific": int(c * 100), "n_errors": 0,
                             "coverage": c, "selective_risk": risk})
    fig, _, _ = brf.plot_risk_coverage_panels({"curve": pd.DataFrame(rows), "targets": None}, {"title": "t"})
    for ax in fig.axes[1:]:
        assert ax.get_ylim()[1] >= 0.44
    plt.close(fig)


def test_sensitivity_summary_marks_executed_incomplete_runs(tree, tmp_path):
    """Regression (real batch 2026-11-11): an executed run that stopped (manifest not COMPLETED) was listed as NOT_RUN."""
    import json
    import shutil
    runs = tmp_path / "primary_protocol"
    shutil.copytree(tree / "03_results" / "primary_protocol" / "PRIMARY", runs / "PRIMARY")
    inc = runs / "SENSITIVITY_k_50"
    inc.mkdir(parents=True)
    (inc / "run_manifest.json").write_text(json.dumps({"status": "RUNNING", "run_key": "abc", "artifact_class": "SYNTHETIC_TEST"}))
    s = bss.collect(runs, allow_synthetic=True)
    assert set(s[s.analysis == "k_50"].status) == {"RUN_INCOMPLETE"}
    assert set(s[s.analysis == "k_10"].status) == {"NOT_RUN"}
