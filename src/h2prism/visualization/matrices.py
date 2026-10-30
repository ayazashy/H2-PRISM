"""
H2-PRISM Visualization Engine — Matrices & Distributions
Owner: Research & Visualization Lead
Implements Confusion Matrices, Family Distribution Bars, and Co-occurrence Heatmaps.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from .theme import apply_publication_theme, COLORS, CLASS_COLORS


def plot_confusion_matrix(
    cm: np.ndarray,
    class_names: List[str],
    normalize: bool = True,
    title: str = "Multi-Class Attribution Confusion Matrix",
    save_path: Optional[Union[str, Path]] = None,
) -> plt.Figure:
    """
    Renders an academic, high-resolution annotated confusion matrix.
    """
    apply_publication_theme()
    fig, ax = plt.subplots(figsize=(6.5, 5.5))

    if normalize:
        cm_norm = cm.astype("float") / cm.sum(axis=1)[:, np.newaxis]
        cm_norm = np.nan_to_num(cm_norm)
        display_data = cm_norm
        val_format = "{:.1%}"
    else:
        display_data = cm
        val_format = "{:d}"

    im = ax.imshow(display_data, interpolation="nearest", cmap="Blues", vmin=0, vmax=1.0 if normalize else None)
    cbar = ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.set_ylabel("Normalized Ratio" if normalize else "Count", rotation=-90, va="bottom")

    tick_marks = np.arange(len(class_names))
    ax.set_xticks(tick_marks)
    ax.set_xticklabels(class_names, rotation=35, ha="right")
    ax.set_yticks(tick_marks)
    ax.set_yticklabels(class_names)

    # Annotate cells
    thresh = display_data.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            val = display_data[i, j]
            count_str = f"\n(n={cm[i, j]})" if normalize else ""
            txt = val_format.format(val) + count_str
            text_color = "white" if val > thresh else "#1F2937"
            ax.text(j, i, txt, ha="center", va="center", color=text_color, fontsize=9, fontweight="bold")

    ax.set_title(title, pad=12)
    ax.set_ylabel("True Ground-Truth Class")
    ax.set_xlabel("Predicted Attribution Class")
    ax.grid(False)

    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path)
    return fig


def plot_family_distribution(
    fam_dist_df: pd.DataFrame,
    title: str = "Dataset Composition: Independent Families per Target Class",
    save_path: Optional[Union[str, Path]] = None,
) -> plt.Figure:
    """
    Visualizes the count of independent scenario families per target class.
    Crucial for justifying why topology-stratified 3-fold CV is required.
    """
    apply_publication_theme()
    fig, ax = plt.subplots(figsize=(7, 4.5))

    # Aggregate counts per class from the distribution dataframe
    classes = ["NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"]
    
    # Check conservative vs topology
    df_conserv = fam_dist_df[fam_dist_df["grouping_view"] == "CONSERVATIVE_POOLED"]
    counts_conserv = [
        int((df_conserv["count_" + c] > 0).sum()) if ("count_" + c) in df_conserv.columns else 0
        for c in classes
    ]

    df_topo = fam_dist_df[fam_dist_df["grouping_view"] == "TOPOLOGY_STRATIFIED"]
    counts_topo = [
        int((df_topo["count_" + c] > 0).sum()) if ("count_" + c) in df_topo.columns else 0
        for c in classes
    ]

    x = np.arange(len(classes))
    width = 0.35

    ax.bar(x - width/2, counts_conserv, width, label="Conservative Global Families", color=COLORS["accent_warm"], edgecolor="#1F2937")
    ax.bar(x + width/2, counts_topo, width, label="Topology-Stratified Families", color=COLORS["primary"], edgecolor="#1F2937")

    ax.set_ylabel("Number of Independent Families")
    ax.set_title(title, pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(classes, rotation=15, ha="right")
    ax.legend(frameon=True, edgecolor="#D1D5DB")
    ax.set_ylim(0, max(max(counts_topo), max(counts_conserv)) * 1.25)

    for i in range(len(classes)):
        ax.text(x[i] - width/2, counts_conserv[i] + 0.2, str(counts_conserv[i]), ha="center", fontsize=9, fontweight="bold")
        ax.text(x[i] + width/2, counts_topo[i] + 0.2, str(counts_topo[i]), ha="center", fontsize=9, fontweight="bold")

    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path)
    return fig
