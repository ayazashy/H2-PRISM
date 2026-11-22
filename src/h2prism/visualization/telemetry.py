"""
H2-PRISM Visualization Engine — SCADA Telemetry Timeseries Plots
Owner: Research & Visualization Lead
Implements pipeline pressure profiles, mass flow rates, and event boundary shading.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from .theme import apply_publication_theme, COLORS


def plot_pipeline_telemetry(
    df_scenario: pd.DataFrame,
    title: str = "Pipeline SCADA Telemetry Dynamics",
    event_onset: Optional[float] = None,
    event_offset: Optional[float] = None,
    event_label: Optional[str] = None,
    downsample_factor: int = 10,
    save_path: Optional[Union[str, Path]] = None,
) -> plt.Figure:
    """
    Renders a synchronized 2-panel plot showing:
    1. Pressure sensors (PS1 inlet to PS12 outlet)
    2. Mass flow sensors (MFS1 inlet to MFS4 outlet)
    With shaded event duration window.
    """
    apply_publication_theme()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)

    # Subsample for rendering speed if long
    df_sub = df_scenario.iloc[::downsample_factor].copy() if downsample_factor > 1 else df_scenario.copy()
    time_s = df_sub["Timestamp"] if "Timestamp" in df_sub.columns else np.arange(len(df_sub)) * downsample_factor

    # Top: Key Pressures (PS1 inlet, PS4, PS7 midpoint, PS12 outlet)
    ps_channels = [c for c in ["PS1", "PS4", "PS7", "PS12"] if c in df_sub.columns]
    colors_ps = [COLORS["primary"], COLORS["secondary"], COLORS["purple"], COLORS["accent_warm"]]
    for col, col_c in zip(ps_channels, colors_ps):
        ax1.plot(time_s, df_sub[col], label=f"{col} ({col.lower()})", color=col_c, linewidth=1.2)

    ax1.set_ylabel("Pressure (MPa)")
    ax1.set_title(title, pad=10)
    ax1.legend(frameon=True, loc="upper right", ncol=min(len(ps_channels), 4), edgecolor="#D1D5DB")

    # Bottom: Key Mass Flows (MFS1 inlet, MFS3 midpoint, MFS4 outlet)
    mfs_channels = [c for c in ["MFS1", "MFS3", "MFS4"] if c in df_sub.columns]
    colors_mfs = [COLORS["accent_success"], COLORS["secondary"], COLORS["accent_danger"]]
    for col, col_c in zip(mfs_channels, colors_mfs):
        ax2.plot(time_s, df_sub[col], label=f"{col} ({col.lower()})", color=col_c, linewidth=1.2)

    ax2.set_ylabel("Mass Flow (kg/s)")
    ax2.set_xlabel("Time (seconds)")
    ax2.legend(frameon=True, loc="upper right", ncol=min(len(mfs_channels), 3), edgecolor="#D1D5DB")

    # Shaded Event Duration
    if event_onset is not None and not np.isnan(event_onset):
        t_end = event_offset if (event_offset is not None and not np.isnan(event_offset)) else time_s.iloc[-1]
        label_text = f"Active Event: {event_label}" if event_label else "Active Event Region"
        for ax in [ax1, ax2]:
            ax.axvspan(event_onset, t_end, color="#FEE2E2", alpha=0.5, label="Event Horizon")
            ax.axvline(event_onset, color=COLORS["accent_danger"], linestyle="--", linewidth=1.2)

    plt.tight_layout()
    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(save_path)
    return fig
