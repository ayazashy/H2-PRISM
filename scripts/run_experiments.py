"""Run the frozen, leakage-aware H2-PRISM outer-fold experiments."""

import argparse
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT / "src"))

from h2prism.simnet_experiments import DEFAULT_CONFIG, DEFAULT_OUTPUT_DIR, run_experiments


def main():
    parser = argparse.ArgumentParser(
        description="Run the frozen H2-PRISM grouped outer-fold experiment."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="Frozen YAML configuration to use.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for generated results and provenance.",
    )
    args = parser.parse_args()
    artifacts = run_experiments(args.config.resolve(), args.output_dir.resolve())
    print("Experiment completed. Generated artifacts:")
    for name, path in artifacts.items():
        print(f"  {name}: {path}")


if __name__ == "__main__":
    main()
