"""
H2-PRISM Visualization Engine — Master CLI Runner
Usage:
    python3 scripts/visualize.py --demo
    python3 scripts/visualize.py --results-dir 03_results/
    python3 scripts/visualize.py --open
"""

import argparse
import sys
import webbrowser
from pathlib import Path

# Add src to pythonpath
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
import pandas as pd

from h2prism.visualization import (
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

FIG_DIR = Path("03_results/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR = Path("01_dataset_audit")
# AUDIT FIX (audit/preparation-integration): figures 3-6 below are drawn from hard-coded
# or randomly generated numbers, NOT from any experiment. They are written only to this
# quarantine directory with an explicit ILLUSTRATIVE label and must never be cited as results.
DEMO_DIR = Path("03_results/ILLUSTRATIVE_DEMO_NOT_RESULTS")
DEMO_DIR.mkdir(parents=True, exist_ok=True)
ILLUSTRATIVE = "ILLUSTRATIVE ONLY - NOT A RESULT: "


def generate_demo_visualizations() -> Path:
    """Generates figures 1-2 from audit data and ILLUSTRATIVE (non-result) demo figures 3-6."""
    print("=" * 80)
    print(" H2-PRISM VISUALIZATION SUITE — GENERATING RESEARCH FIGURES")
    print("=" * 80)

    generated_figs = {}

    # 1. Figure 1: Family-by-Class Distribution
    fam_dist_csv = AUDIT_DIR / "FAMILY_CLASS_DISTRIBUTION.csv"
    if fam_dist_csv.exists():
        print("[*] Generating Figure 1: Family-by-Class Distribution...")
        df_fam = pd.read_csv(fam_dist_csv)
        f1_path = FIG_DIR / "fig1_family_distribution.png"
        plot_family_distribution(df_fam, save_path=f1_path)
        generated_figs["family_distribution"] = f1_path
        print(f"    -> Saved {f1_path}")

    # 2. Figure 2: SCADA Pipeline Telemetry Timeseries
    timing_csv = AUDIT_DIR / "EVENT_TIMING_AUDIT.csv"
    if timing_csv.exists():
        df_time = pd.read_csv(timing_csv)
        leak_rows = df_time[df_time["canonical_parquet"].str.contains("leakG3", na=False)]
        if len(leak_rows) > 0:
            print("[*] Generating Figure 2: SCADA Telemetry Dynamics with Event Window...")
            pq_rel = leak_rows.iloc[0]["canonical_parquet"]
            raw_pq_path = Path("data/raw") / pq_rel
            if raw_pq_path.exists():
                df_scen = pd.read_parquet(raw_pq_path)
                onset = leak_rows.iloc[0]["event_onset_s"]
                offset = leak_rows.iloc[0]["event_offset_s"]
                f2_path = FIG_DIR / "fig2_pipeline_telemetry.png"
                plot_pipeline_telemetry(df_scen, title=f"Real Telemetry Profile: Leak G3 ({pq_rel.split('/')[-1]})",
                                        event_onset=onset, event_offset=offset, event_label="Leak G3", save_path=f2_path)
                generated_figs["pipeline_telemetry"] = f2_path
                print(f"    -> Saved {f2_path}")

    # 3. Figure 3: Attribution Confusion Matrix
    print("[*] Generating Figure 3: 4-Class Attribution Confusion Matrix...")
    classes = ["NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"]
    # Benchmark demonstration matrix
    cm_demo = np.array([
        [98,  1,  1,  0],
        [ 2, 94,  2,  2],
        [ 1,  2, 95,  2],
        [ 0,  1,  2, 97],
    ])
    f3_path = DEMO_DIR / "fig3_confusion_matrix.png"
    plot_confusion_matrix(cm_demo, classes, normalize=True, title=ILLUSTRATIVE + "hard-coded matrix", save_path=f3_path)
    generated_figs["confusion_matrix"] = f3_path
    print(f"    -> Saved {f3_path}")

    # 4. Figure 4: Risk-Coverage Comparison Curve (RQ1)
    print("[*] Generating Figure 4: Risk-Coverage Curve Comparison (RQ1)...")
    cov = np.linspace(0.40, 1.0, 50)
    # Method C (with D): Lower selective risk at higher coverage
    risk_c = 0.02 + 0.12 * (cov ** 3)
    # Method C-D (without D): Higher selective risk
    risk_c_minus_d = 0.03 + 0.16 * (cov ** 2.8)
    # Method B (Confidence only): Highest selective risk
    risk_b = 0.04 + 0.22 * (cov ** 2.5)

    f4_path = DEMO_DIR / "fig4_risk_coverage_curve.png"
    plot_risk_coverage_curve(cov, risk_c, risk_c_minus_d, risk_b, title=ILLUSTRATIVE + "invented curves",
                             save_path=f4_path)
    generated_figs["risk_coverage_curve"] = f4_path
    print(f"    -> Saved {f4_path}")

    # 5. Figure 5: Calibration Reliability Diagram
    print("[*] Generating Figure 5: Calibration Reliability Diagram...")
    conf = np.linspace(0.1, 0.95, 10)
    acc = conf + np.random.normal(0, 0.03, len(conf))
    acc = np.clip(acc, 0, 1)
    counts = np.array([45, 80, 120, 210, 350, 480, 600, 750, 890, 1100])
    f5_path = DEMO_DIR / "fig5_calibration_reliability.png"
    plot_calibration_reliability_diagram(conf, acc, counts, ece=0.024, brier=0.082,
                                         model_name=ILLUSTRATIVE + "random numbers", save_path=f5_path)
    generated_figs["calibration_reliability"] = f5_path
    print(f"    -> Saved {f5_path}")

    # 6. Figure 6: Empirical Distinguishability D(x) Separation (RQ1)
    print("[*] Generating Figure 6: Distinguishability D(x) Separation (RQ1)...")
    np.random.seed(42)
    d_correct = np.random.beta(5, 2, size=500)   # Skewed toward high D
    d_incorrect = np.random.beta(2, 5, size=200) # Skewed toward low D
    f6_path = DEMO_DIR / "fig6_distinguishability_separation.png"
    plot_distinguishability_distribution(d_correct, d_incorrect, title=ILLUSTRATIVE + "random Beta draws",
                                         save_path=f6_path)
    generated_figs["distinguishability_separation"] = f6_path
    print(f"    -> Saved {f6_path}")

    # 7. Summary Scorecard & Interactive HTML Dashboard
    print("[*] Building Interactive HTML Evaluation Dashboard...")
    # AUDIT FIX: the previous KPI cards (benchmark_accuracy 0.960, selective_risk_at_80 0.081,
    # ece 0.024) were invented numbers and have been removed. Only audit-reported counts remain,
    # and they are labelled as reported (see 06_audit_preparation/YAZAN_DATASET_VERIFICATION.md).
    kpis = {
        "audit_reported_scenarios_unverified": 58,
        "audit_reported_families_unverified": 13,
        "experimental_results_available": "NONE",
    }
    dashboard_path = generate_html_report(
        generated_figs, kpis,
        output_html_path=str(DEMO_DIR / "dashboard_ILLUSTRATIVE.html"),
        title="H2-PRISM ILLUSTRATIVE DEMO - contains NO experimental results",
    )
    print(f"[✓] Dashboard generated successfully: {dashboard_path}")
    print("=" * 80)
    return dashboard_path


def main():
    parser = argparse.ArgumentParser(description="H2-PRISM Research Visualization & Reporting Engine")
    parser.add_argument("--demo", action="store_true", help="Generate demonstration figures & dashboard")
    parser.add_argument("--results-dir", type=str, default="03_results", help="Directory containing experimental results")
    parser.add_argument("--open", action="store_true", help="Open generated HTML dashboard in default browser")
    args = parser.parse_args()

    dashboard_path = generate_demo_visualizations()

    if args.open:
        print(f"[*] Opening {dashboard_path} in browser...")
        webbrowser.open(f"file://{dashboard_path.resolve()}")


if __name__ == "__main__":
    main()
