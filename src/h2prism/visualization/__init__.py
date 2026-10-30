"""
H2-PRISM Visualization Subpackage
Exports theme presets, curves, confusion matrices, distinguishability plots, telemetry plots, and HTML reports.
"""

from .theme import apply_publication_theme, COLORS, CLASS_COLORS, METHOD_COLORS
from .curves import (
    plot_risk_coverage_curve,
    plot_calibration_reliability_diagram,
    plot_ablation_comparison_bar,
)
from .matrices import (
    plot_confusion_matrix,
    plot_family_distribution,
)
from .distinguishability import (
    plot_distinguishability_distribution,
    plot_indicator_correlations,
)
from .telemetry import (
    plot_pipeline_telemetry,
)
from .dashboard import (
    generate_html_report,
)

__all__ = [
    "apply_publication_theme",
    "COLORS",
    "CLASS_COLORS",
    "METHOD_COLORS",
    "plot_risk_coverage_curve",
    "plot_calibration_reliability_diagram",
    "plot_ablation_comparison_bar",
    "plot_confusion_matrix",
    "plot_family_distribution",
    "plot_distinguishability_distribution",
    "plot_indicator_correlations",
    "plot_pipeline_telemetry",
    "generate_html_report",
]
