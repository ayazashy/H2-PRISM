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
    assert not (ROOT / "03_results" / "primary_protocol").exists()  # no real model results exist without authorization
    for m in list((ROOT / "03_results").rglob("FIGURE_MANIFEST.csv")) + list((ROOT / "03_results").rglob("TABLE_MANIFEST.csv")):
        man = pd.read_csv(m)
        assert not man.status.astype(str).str.contains("ILLUSTRATIVE").any(), m
        assert "SYNTHETIC_TEST" not in set(man.artifact_class.dropna()), m
