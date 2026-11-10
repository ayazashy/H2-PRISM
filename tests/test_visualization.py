"""
H2-PRISM Stage 2 Test Suite — Visualization Subpackage & Reporting Engine
Owner: Yazan (Lead, Dataset Audit, Data Engineering & Dataset Readiness)
Verifies that all plotting modules, publication themes, CLI scripts, and HTML dashboard generators
function deterministically and output valid figures.
"""

from pathlib import Path
import subprocess
import sys
import numpy as np
import pandas as pd
import pytest

from h2prism.visualization import (
    apply_publication_theme,
    COLORS,
    CLASS_COLORS,
    METHOD_COLORS,
    plot_risk_coverage_curve,
    plot_calibration_reliability_diagram,
    plot_ablation_comparison_bar,
    plot_confusion_matrix,
    plot_family_distribution,
    plot_distinguishability_distribution,
    plot_indicator_correlations,
    plot_pipeline_telemetry,
    generate_html_report,
)


def test_theme_and_color_palette():
    """Verifies that color palettes and theme application are well-defined."""
    apply_publication_theme()
    assert "primary" in COLORS
    assert "NORMAL" in CLASS_COLORS
    assert "LEAK" in CLASS_COLORS
    assert "C" in METHOD_COLORS
    assert "C_minus_D" in METHOD_COLORS
    assert "B" in METHOD_COLORS


def test_plot_risk_coverage_curve(tmp_path):
    """Verifies Figure 4: Risk-Coverage curve generation."""
    cov = np.linspace(0.4, 1.0, 20)
    risk_c = 0.05 + 0.1 * cov
    risk_cmd = 0.08 + 0.12 * cov
    risk_b = 0.10 + 0.15 * cov

    out_file = tmp_path / "test_rc.png"
    fig = plot_risk_coverage_curve(cov, risk_c, risk_cmd, risk_b, save_path=out_file)
    assert fig is not None
    assert out_file.exists()
    assert out_file.stat().st_size > 1000


def test_plot_calibration_reliability_diagram(tmp_path):
    """Verifies Figure 5: Reliability diagram with ECE and Brier score."""
    conf = np.linspace(0.1, 0.9, 10)
    acc = conf + np.random.normal(0, 0.02, 10)
    acc = np.clip(acc, 0, 1)
    counts = np.array([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])

    out_file = tmp_path / "test_cal.png"
    fig = plot_calibration_reliability_diagram(
        conf, acc, counts, ece=0.035, brier=0.091, save_path=out_file
    )
    assert fig is not None
    assert out_file.exists()
    assert out_file.stat().st_size > 1000


def test_plot_ablation_comparison_bar(tmp_path):
    """Verifies ablation waterfall comparison plot."""
    df_ablation = pd.DataFrame({
        "method": ["C", "C_minus_D", "B", "B3"],
        "selective_risk_at_80": [0.081, 0.124, 0.158, 0.172],
    })
    out_file = tmp_path / "test_ablation.png"
    fig = plot_ablation_comparison_bar(df_ablation, metric_col="selective_risk_at_80", baseline_col="method", save_path=out_file)
    assert fig is not None
    assert out_file.exists()
    assert out_file.stat().st_size > 1000


def test_plot_confusion_matrix(tmp_path):
    """Verifies Figure 3: Confusion matrix plot (normalized and counts)."""
    cm = np.array([[50, 2, 0, 0], [1, 45, 3, 1], [0, 2, 48, 0], [0, 0, 1, 49]])
    classes = ["NORMAL", "LEAK", "COMP_FAULT", "COMP_DELAY"]

    out_file = tmp_path / "test_cm.png"
    fig = plot_confusion_matrix(cm, classes, normalize=True, save_path=out_file)
    assert fig is not None
    assert out_file.exists()
    assert out_file.stat().st_size > 1000


def test_plot_family_distribution(tmp_path):
    """Verifies Figure 1: Family-by-Class distribution."""
    # Use real audit file if available, or synthetic with proper schema
    real_csv = Path("01_dataset_audit/FAMILY_CLASS_DISTRIBUTION.csv")
    if real_csv.exists():
        df_fam = pd.read_csv(real_csv)
    else:
        df_fam = pd.DataFrame([
            {"grouping_view": "CONSERVATIVE_POOLED", "count_NORMAL": 1, "count_LEAK": 2, "count_COMPRESSOR_FAULT": 2, "count_COMPRESSOR_DELAY": 2},
            {"grouping_view": "TOPOLOGY_STRATIFIED", "count_NORMAL": 2, "count_LEAK": 5, "count_COMPRESSOR_FAULT": 3, "count_COMPRESSOR_DELAY": 3},
        ])
    out_file = tmp_path / "test_fam.png"
    fig = plot_family_distribution(df_fam, save_path=out_file)
    assert fig is not None
    assert out_file.exists()
    assert out_file.stat().st_size > 1000


def test_plot_distinguishability_distribution(tmp_path):
    """Verifies Figure 6: Distinguishability D(x) separation density."""
    d_corr = np.array([0.7, 0.8, 0.85, 0.9, 0.95, 0.75, 0.82])
    d_inc = np.array([0.1, 0.2, 0.15, 0.3, 0.25, 0.05, 0.18])

    out_file = tmp_path / "test_dist.png"
    fig = plot_distinguishability_distribution(d_corr, d_inc, save_path=out_file)
    assert fig is not None
    assert out_file.exists()
    assert out_file.stat().st_size > 1000


def test_plot_indicator_correlations(tmp_path):
    """Verifies indicator correlation heatmap."""
    df_corr = pd.DataFrame({
        "Confidence": [1.0, 0.65, -0.45],
        "Distinguishability": [0.65, 1.0, -0.55],
        "Entropy": [-0.45, -0.55, 1.0],
    }, index=["Confidence", "Distinguishability", "Entropy"])

    out_file = tmp_path / "test_corr.png"
    fig = plot_indicator_correlations(df_corr, save_path=out_file)
    assert fig is not None
    assert out_file.exists()
    assert out_file.stat().st_size > 1000


def test_plot_pipeline_telemetry(tmp_path):
    """Verifies Figure 2: SCADA telemetry timeseries."""
    time_series = np.linspace(0, 1000, 100)
    df_telemetry = pd.DataFrame({
        "Timestamp": time_series,
        "PS1": np.sin(time_series / 100) + 50.0,
        "PS4": np.sin(time_series / 100) + 48.0,
        "PS7": np.sin(time_series / 100) + 46.0,
        "PS12": np.sin(time_series / 100) + 44.0,
        "MFS1": np.cos(time_series / 100) + 120.0,
        "MFS3": np.cos(time_series / 100) + 118.0,
        "MFS4": np.cos(time_series / 100) + 115.0,
    })
    out_file = tmp_path / "test_telem.png"
    fig = plot_pipeline_telemetry(
        df_telemetry,
        event_onset=300.0,
        event_offset=700.0,
        event_label="Simulated Leak",
        save_path=out_file,
    )
    assert fig is not None
    assert out_file.exists()
    assert out_file.stat().st_size > 1000


def test_generate_html_report(tmp_path):
    """Verifies HTML report compilation with embedded base64 figures."""
    img_path = tmp_path / "dummy_fig.png"
    cov = np.linspace(0.5, 1.0, 10)
    plot_risk_coverage_curve(
        cov,
        0.05 + 0.1 * cov,
        0.08 + 0.12 * cov,
        0.10 + 0.15 * cov,
        save_path=img_path,
    )
    figs_dict = {"risk_coverage_curve": img_path}
    kpis = {"accuracy": 0.95, "selective_risk": 0.08}
    html_out = tmp_path / "test_report.html"

    report_path = generate_html_report(figs_dict, kpis, output_html_path=html_out)
    assert report_path.exists()
    content = report_path.read_text(encoding="utf-8")
    assert "H2-PRISM Research" in content
    assert "data:image/png;base64," in content
    assert "0.95" in content


def test_visualize_cli_runner():
    """Verifies end-to-end execution of scripts/visualize.py --demo."""
    cmd = [sys.executable, "scripts/visualize.py", "--demo"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"visualize.py failed: {res.stderr}"
    assert "Dashboard generated successfully" in res.stdout
    # AUDIT FIX: demo output is quarantined as illustrative (contains no experimental results)
    assert Path("03_results/ILLUSTRATIVE_DEMO_NOT_RESULTS/dashboard_ILLUSTRATIVE.html").exists()
