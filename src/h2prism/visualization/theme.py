"""
H2-PRISM Visualization Engine — Theme & Style Configuration
Owner: Research & Visualization Lead
Defines academic, publication-grade aesthetics (IEEE / Nature / ACM standard).
"""

from typing import Dict, Any
import matplotlib.pyplot as plt
import matplotlib as mpl

# Publication Color Palette (Accessible, High Contrast, Colorblind Friendly)
COLORS = {
    "primary": "#1E3A8A",      # Deep Navy
    "secondary": "#0284C7",    # Electric Blue
    "accent_warm": "#D97706",  # Amber / Warning
    "accent_danger": "#DC2626",# Crimson / Leak
    "accent_success": "#059669", # Emerald / Normal
    "purple": "#7C3AED",       # Royal Purple / Distinguishability D
    "gray_dark": "#1F2937",    # Slate 800 (text)
    "gray_medium": "#6B7280",  # Slate 500 (grid/subtitles)
    "gray_light": "#F3F4F6",   # Slate 100 (backgrounds)
    "white": "#FFFFFF",
}

# Class-specific colors for the 4 primary classes
CLASS_COLORS = {
    "NORMAL": "#059669",             # Emerald Green
    "LEAK": "#DC2626",               # Crimson Red
    "COMPRESSOR_FAULT": "#D97706",   # Amber / Orange
    "COMPRESSOR_DELAY": "#2563EB",   # Cobalt Blue
    "UNKNOWN": "#6B7280",            # Muted Gray
}

# Method Comparison Colors (RQ1 & RQ2)
METHOD_COLORS = {
    "C": "#1E3A8A",       # Primary Method: Combined with D(x)
    "C_minus_D": "#D97706", # Essential Ablation: Combined without D(x)
    "B": "#6B7280",       # Primary Baseline: Confidence-only
    "B2": "#0284C7",      # Margin-only
    "B3": "#7C3AED",      # Entropy-only
    "D_only": "#EC4899",  # Distinguishability-only
}


def apply_publication_theme():
    """Applies clean, deterministic academic styling to Matplotlib."""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.labelsize": 11,
        "axes.labelweight": "normal",
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "figure.titlesize": 14,
        "figure.titleweight": "bold",
        "axes.edgecolor": "#D1D5DB",
        "axes.linewidth": 1.0,
        "axes.grid": True,
        "grid.color": "#E5E7EB",
        "grid.linestyle": "--",
        "grid.linewidth": 0.7,
        "figure.facecolor": "#FFFFFF",
        "axes.facecolor": "#FFFFFF",
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    })
