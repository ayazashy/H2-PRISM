"""
H2-PRISM Visualization Engine — Empirical Distinguishability D(x) Plots
Owner: Research & Visualization Lead
Implements D(x) distribution comparisons, indicator correlations, and support flags.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from .theme import apply_publication_theme, COLORS, METHOD_COLORS


def plot_distinguishability_distribution(
    d_correct: np.ndarray,
    d_incorrect: np.ndarray,
    title: str = r"Empirical Distinguishability $D(x)$ Separation (RQ1)",
    save_path: Optional[Union[str, Path]] = None,
) -> plt.Figure:
    """
    Plots the empirical probability density / histogram of D(x) for correct vs incorrect decisions.
    Directly answers RQ1: Does D(x) separate correct from incorrect predictions among challenging cases?
    """
    apply_publication_theme()
    fig, ax = plt.subplots(figsize=(7, 4.8))

    bins = np.linspace(0.0, 1.0, 25)

    ax.hist(d_correct, bins=bins, density=True, alpha=0.65, color=COLORS["accent_success"],
            edgecolor=COLORS["accent_success"], label=f"Correct Decisions (n={len(d_correct)})")
    ax.hist(d_incorrect, bins=bins, density=True, alpha=0.65, color=COLORS["accent_danger"],
            edgecolor=COLORS["accent_danger"], label=f"Incorrect Decisions (n={len(d_incorrect)})")

    # Means
    mean_corr = np.mean(d_correct) if len(d_correct) > 0 else 0
    mean_inc = np.mean(d_incorrect) if len(d_incorrect) > 0 else 0

    ax.axvline(mean_corr, color=COLORS["accent_success"], linestyle="--", linewidth=1.5, label=f"Mean Correct: {mean_corr:.2f}")
    ax.axvline(mean_inc, color=COLORS["accent_danger"], linestyle="--", linewidth=1.5, label=f"Mean Incorrect: {mean_inc:.2f}")

    ax.set_title(title, pad=12)
    ax.set_xlabel(r"Empirical Distinguishability Statistic $D(x) = q_{(1)}(x) - q_{(2)}(x)$")
    ax.set_ylabel("Density")
    ax.set_xlim(0.0, 1.0)
    ax.legend(frameon=True, loc="upper right", edgecolor="#D1D5DB")

    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path)
    return fig


def plot_indicator_correlations(
    corr_matrix: pd.DataFrame,
    title: str = "Correlation Matrix: Uncertainty vs Distinguishability Indicators",
    save_path: Optional[Union[str, Path]] = None,
) -> plt.Figure:
    """
    Plots a correlation heatmap among Confidence C(x), Margin M(x), Entropy -H(x), and Distinguishability D(x).
    Demonstrates whether D(x) provides non-redundant orthogonal information.
    """
    apply_publication_theme()
    fig, ax = plt.subplots(figsize=(6, 5))

    labels = corr_matrix.columns.tolist()
    data = corr_matrix.values

    im = ax.imshow(data, cmap="coolwarm", vmin=-1.0, vmax=1.0)
    cbar = ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.set_ylabel("Pearson Correlation", rotation=-90, va="bottom")

    ax.set_xticks(np.arange(len(labels)))
    ax.set_yticks(np.arange(len(labels)))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_yticklabels(labels)

    for i in range(len(labels)):
        for j in range(len(labels)):
            val = data[i, j]
            txt_color = "white" if abs(val) > 0.5 else "#1F2937"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center", color=txt_color, fontsize=10, fontweight="bold")

    ax.set_title(title, pad=12)
    ax.grid(False)

    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path)
    return fig
