"""
H2-PRISM Visualization Engine — Curves and Performance Plots
Owner: Research & Visualization Lead
Implements Risk-Coverage Curves, Reliability Diagrams, and Ablation Plots.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from .theme import apply_publication_theme, COLORS, METHOD_COLORS


def plot_risk_coverage_curve(
    coverages: np.ndarray,
    risks_c: np.ndarray,
    risks_c_minus_d: np.ndarray,
    risks_b: np.ndarray,
    title: str = "Selective Diagnosis: Risk-Coverage Comparison (RQ1)",
    save_path: Optional[Union[str, Path]] = None,
) -> plt.Figure:
    """
    Plots the central evaluation curve comparing:
    - Method C: Combined with D(x)
    - Method C-D: Combined without D(x)
    - Method B: Confidence-only baseline
    """
    apply_publication_theme()
    fig, ax = plt.subplots(figsize=(7, 5))

    ax.plot(coverages, risks_c, color=METHOD_COLORS["C"], linewidth=2.2, label=r"Method C: Combined with $D(x)$ (Primary)")
    ax.plot(coverages, risks_c_minus_d, color=METHOD_COLORS["C_minus_D"], linewidth=2.0, linestyle="--", label=r"Method C$-$D: Combined without $D(x)$ (Ablation)")
    ax.plot(coverages, risks_b, color=METHOD_COLORS["B"], linewidth=1.8, linestyle=":", label="Method B: Confidence-only Baseline")

    # Target Operating Points (e.g. 80% coverage)
    idx_80 = np.argmin(np.abs(coverages - 0.80))
    ax.scatter([coverages[idx_80]], [risks_c[idx_80]], color=METHOD_COLORS["C"], s=50, zorder=5)
    ax.scatter([coverages[idx_80]], [risks_c_minus_d[idx_80]], color=METHOD_COLORS["C_minus_D"], s=50, zorder=5)
    ax.scatter([coverages[idx_80]], [risks_b[idx_80]], color=METHOD_COLORS["B"], s=50, zorder=5)

    ax.axvline(0.80, color=COLORS["gray_medium"], linestyle="-.", linewidth=0.8, alpha=0.7, label="Primary Coverage Target (80%)")

    ax.set_title(title, pad=12)
    ax.set_xlabel("Coverage (Fraction of Decisions Accepted as Specific)")
    ax.set_ylabel("Selective Risk (Error Rate on Accepted Decisions)")
    ax.set_xlim(0.4, 1.0)
    ax.set_ylim(0.0, max(np.max(risks_b) * 1.15, 0.20))
    ax.legend(frameon=True, loc="upper left", edgecolor="#D1D5DB")

    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path)
    return fig


def plot_calibration_reliability_diagram(
    confidences: np.ndarray,
    accuracies: np.ndarray,
    counts: np.ndarray,
    ece: float,
    brier: float,
    model_name: str = "Calibrated Random Forest",
    save_path: Optional[Union[str, Path]] = None,
) -> plt.Figure:
    """
    Plots a 10-bin Reliability Diagram showing empirical accuracy vs mean predicted confidence.
    Includes Expected Calibration Error (ECE) and Brier Score annotations.
    """
    apply_publication_theme()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6, 7), gridspec_kw={"height_ratios": [3, 1]}, sharex=True)

    bin_centers = np.linspace(0.05, 0.95, len(confidences))
    bin_width = 1.0 / len(confidences)

    # Perfect calibration reference
    ax1.plot([0, 1], [0, 1], color=COLORS["gray_medium"], linestyle="--", linewidth=1.5, label="Perfect Calibration")

    # Calibration error bars
    ax1.bar(bin_centers, accuracies, width=bin_width * 0.85, color=COLORS["primary"], alpha=0.7, edgecolor=COLORS["primary"], label="Empirical Accuracy")
    ax1.scatter(bin_centers, confidences, color=COLORS["accent_danger"], marker="D", s=30, label="Mean Confidence", zorder=5)

    # Metrics box
    metrics_text = f"ECE = {ece:.3f}\nBrier = {brier:.3f}"
    ax1.text(0.05, 0.85, metrics_text, transform=ax1.transAxes, fontsize=10, verticalalignment="top",
             bbox=dict(boxstyle="round,pad=0.5", facecolor=COLORS["gray_light"], edgecolor="#D1D5DB"))

    ax1.set_title(f"Reliability Diagram: {model_name}", pad=10)
    ax1.set_ylabel("Empirical Accuracy")
    ax1.set_ylim(0, 1)
    ax1.legend(frameon=True, loc="lower right", edgecolor="#D1D5DB")

    # Sample distribution histogram
    ax2.bar(bin_centers, counts, width=bin_width * 0.85, color=COLORS["gray_medium"], alpha=0.6, edgecolor="#4B5563")
    ax2.set_xlabel("Confidence Bin Center")
    ax2.set_ylabel("Count")
    ax2.set_xlim(0, 1)

    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path)
    return fig


def plot_ablation_comparison_bar(
    ablation_df: pd.DataFrame,
    metric_col: str = "selective_risk_at_80",
    baseline_col: str = "method",
    title: str = "Ablation Study: Risk Reduction at Matched 80% Coverage",
    save_path: Optional[Union[str, Path]] = None,
) -> plt.Figure:
    """
    Plots horizontal or vertical bar chart comparing methods across ablation configs.
    """
    apply_publication_theme()
    fig, ax = plt.subplots(figsize=(7, 4.5))

    methods = ablation_df[baseline_col].tolist()
    values = ablation_df[metric_col].tolist()
    colors = [METHOD_COLORS.get(m, COLORS["primary"]) for m in methods]

    y_pos = np.arange(len(methods))
    bars = ax.barh(y_pos, values, color=colors, height=0.6, edgecolor="#1F2937", linewidth=0.8)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(methods)
    ax.invert_yaxis()
    ax.set_xlabel("Selective Risk (Lower is Better)")
    ax.set_title(title, pad=12)

    # Value annotations on bars
    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.005, bar.get_y() + bar.get_height() / 2, f"{w:.3f}", va="center", fontsize=9, fontweight="bold")

    ax.set_xlim(0, max(values) * 1.25)
    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path)
    return fig
