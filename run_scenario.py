"""
H2-PRISM Scenario Execution Runner.
Usage:
  python run_scenario.py --mock leak
  python run_scenario.py --mock operational_transient
  python run_scenario.py --mock sensor_fault
  python run_scenario.py --mock ambiguous
  python run_scenario.py --file path/to/scenario.csv
"""

import argparse
import json
import sys
from pathlib import Path
from src.data import generate_mock_scenario, load_scenario
from src.pipeline import H2PrismPipeline


def print_event_report(report) -> None:
    d = report.decision
    p = report.physics
    prop = report.propagation
    obs = report.decision.observability

    print("\n" + "=" * 70)
    print(f" H2-PRISM STRUCTURED EVENT REPORT: {report.event_id}")
    print("=" * 70)
    print(f" Timestamp:      {report.timestamp:.2f} s")
    print(f" Scenario:       {report.scenario_id}")
    print(f" Stage 1 Trigger:{report.candidate.notes}")
    print("-" * 70)
    print(f" FINAL DECISION: {d.decision.value} (Abstained: {d.is_abstained})")
    print(f" Decision Reason:{d.reason}")
    print(f" Confidence:     {d.confidence:.2%}")
    print("-" * 70)
    print(f" Observability:  {obs.overall_observability:.2f} [{obs.observability_level.value}]")
    print(f"   - O_Q (Quality):     {obs.o_q:.2f}")
    print(f"   - O_S (Structural):  {obs.o_s:.2f}")
    print(f"   - O_E (Evidential):  {obs.o_e:.2f}")
    if obs.failing_criteria:
        print(f"   - Failing Criteria:  {', '.join(obs.failing_criteria)}")
    print("-" * 70)
    print(f" Physics Evidence:")
    print(f"   - Normalized z_MB:   {p.normalized_mass_balance_residual:.2f}")
    print(f"   - Raw Imbalance:     {p.raw_imbalance:.4f} kg/s")
    print(f"   - Line-Pack Delta:   {p.line_pack_correction or 0.0:.4f} kg/s")
    print(f"   - Consistency:       {p.physics_consistency:.2f}")
    print("-" * 70)
    print(f" Propagation Evidence:")
    print(f"   - Est. Delay dt_12:  {prop.estimated_delay if prop.estimated_delay is not None else 'N/A'}")
    print(f"   - Peak Correlation:  {prop.correlation_strength:.2f}")
    print(f"   - Consistent:        {prop.propagation_consistency}")
    print(f"   - Localization:      {prop.localization_interval if prop.localization_observable else 'NOT_OBSERVABLE'}")
    print(f"   - Resolution Floor:  +/-{prop.resolution_floor:.1f} m")
    print("-" * 70)
    print(f" ML Likelihoods: {report.ml.calibrated_probabilities}")
    print(f" Contradiction:  {report.evidence.contradiction_score:.2f}")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="H2-PRISM Scenario Runner")
    parser.add_argument("--mock", type=str, choices=["normal", "leak", "operational_transient", "sensor_fault", "ambiguous"],
                        default="leak", help="Run with synthetic/mock scenario")
    parser.add_argument("--file", type=str, default=None, help="Path to scenario CSV/Parquet file")
    args = parser.parse_args()

    if args.file:
        print(f"[+] Loading scenario from file: {args.file}")
        df = load_scenario(args.file)
    else:
        print(f"[+] Generating mock scenario: type='{args.mock}'")
        df = generate_mock_scenario(scenario_type=args.mock)

    pipeline = H2PrismPipeline()
    print("[+] Executing H2-PRISM Pipeline...")
    reports = pipeline.process_scenario(df)

    if not reports:
        print("[-] No candidate anomalies detected in scenario (NORMAL operation maintained).")
        return

    print(f"[+] Detected and analyzed {len(reports)} candidate event(s):")
    for r in reports:
        print_event_report(r)


if __name__ == "__main__":
    main()
