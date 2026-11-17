"""Figure style for the A13 builders, derived from the repository's established visual identity.

Source of truth: ``h2prism.visualization.theme`` (``apply_publication_theme``, ``COLORS``, ``CLASS_COLORS``,
``METHOD_COLORS``). This module only (1) maps runner method names onto that palette, (2) adds redundant
encodings (line style, marker, hatch) so no comparison depends on colour alone, and (3) sets the export
settings needed for deterministic PNG/PDF/SVG files. It defines no new palette.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict

import matplotlib

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from h2prism.visualization.theme import CLASS_COLORS, COLORS, METHOD_COLORS, apply_publication_theme  # noqa: E402

# runner method name -> (theme METHOD_COLORS key, display label, line style, marker)
METHODS = {
    "s_C": ("C", "s_C — H$_2$-PRISM (with D(x))", "-", "o"),
    "s_C_minus_D": ("C_minus_D", "s_C−D — no-D ablation", "--", "s"),
    "confidence": ("B", "B — confidence only", ":", "^"),
    "margin": ("B2", "B2 — margin only", "-.", "v"),
    "neg_entropy": ("B3", "B3 — −entropy only", (0, (5, 1)), "D"),
    "D_only": ("D_only", "D(x) only", (0, (3, 1, 1, 1)), "P"),
}
METHOD_ORDER = tuple(METHODS)
CLASS_ORDER = ("NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY")
CLASS_SHORT = {"NORMAL": "NORMAL", "LEAK": "LEAK", "COMPRESSOR_FAULT": "C-FAULT", "COMPRESSOR_DELAY": "C-DELAY"}
CLASS_HATCH = {"NORMAL": "", "LEAK": "//", "COMPRESSOR_FAULT": "..", "COMPRESSOR_DELAY": "xx"}
OUTCOMES = {  # decision outcome -> (colour, hatch, label)
    "specific": (COLORS["primary"], "", "SPECIFIC"),
    "ambiguity_set": (COLORS["accent_warm"], "//", "AMBIGUITY_SET"),
    "unresolved": (COLORS["gray_medium"], "..", "UNRESOLVED"),
}
TOPOLOGY_MARKERS = ("o", "s", "^", "D")
INK, MUTED, LIGHT = COLORS["gray_dark"], COLORS["gray_medium"], COLORS["gray_light"]

EXPORT_RC = {"axes.edgecolor": COLORS["gray_medium"], "xtick.color": COLORS["gray_dark"], "ytick.color": COLORS["gray_dark"],
             "axes.labelcolor": COLORS["gray_dark"], "grid.linestyle": "-", "grid.linewidth": 0.45, "grid.color": "#E5E7EB",
             "axes.linewidth": 0.8, "svg.hashsalt": "h2prism-a13", "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.pad_inches": 0.05,
             "axes.titleweight": "bold", "axes.titlesize": 10, "axes.labelsize": 9, "xtick.labelsize": 8,
             "ytick.labelsize": 8, "legend.fontsize": 8, "font.size": 9, "axes.spines.top": False, "axes.spines.right": False}
PNG_META = {"Software": None}
SVG_META = {"Date": None}
PDF_META = {"CreationDate": None, "ModDate": None, "Producer": None, "Creator": None}


def apply() -> None:
    """Repository theme first, then compact multi-panel sizes and deterministic export settings."""
    apply_publication_theme()
    matplotlib.rcParams.update(EXPORT_RC)


def method_style(m: str) -> Dict[str, object]:
    key, label, ls, mk = METHODS.get(m, ("B", str(m), "-", "o"))
    return {"color": METHOD_COLORS[key], "linestyle": ls, "marker": mk, "label": label}


def class_style(c: str) -> Dict[str, object]:
    return {"color": CLASS_COLORS.get(c, CLASS_COLORS["UNKNOWN"]), "hatch": CLASS_HATCH.get(c, ""), "label": CLASS_SHORT.get(c, c)}


def panel_label(ax, letter: str) -> None:
    """Prefix the panel title with its letter, left-aligned (no free-floating label to collide with titles)."""
    title = ax.get_title()
    ax.set_title("")
    ax.set_title(f"({letter}) {title}", loc="left", fontsize=8.5, fontweight="bold", color=INK)


TOPOLOGY_HATCHES = ("", "///", "xxx")
