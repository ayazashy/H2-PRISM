"""
H2-PRISM Data Access Package
Owner: Yazan (Lead, Dataset Audit, Data Engineering & Dataset Readiness)
Exports high-level dataset loader functions and inspection tools.
"""

from .loader import (
    load_scenario,
    load_fold,
    list_scenarios,
    get_dataset_dir,
    get_dataset_summary,
    is_raw_dataset_available,
)

__all__ = [
    "load_scenario",
    "load_fold",
    "list_scenarios",
    "get_dataset_dir",
    "get_dataset_summary",
    "is_raw_dataset_available",
]

if __name__ == "__main__":
    import json
    summary = get_dataset_summary()
    print("=" * 70)
    print(" H2-PRISM DATASET ACCESS & INSPECTION")
    print("=" * 70)
    print(f"Raw Dataset Available   : {summary['raw_dataset_available']}")
    print(f"Dataset Path            : {summary['active_data_dir']}")
    print(f"Target Classes          : {', '.join(summary['primary_classes'])}")
    print(f"Pressure Sensors        : {len(summary['sensor_channels']['pressure'])} channels (PS1-PS12)")
    print(f"Mass Flow Sensors       : {len(summary['sensor_channels']['mass_flow'])} channels (MFS1-MFS4)")
    print(f"Temperature Sensors     : {len(summary['sensor_channels']['temperature'])} channels (None)")
    print("-" * 70)
    print("Listing 5 eligible scenarios:")
    scenarios = list_scenarios().head(5)
    for _, row in scenarios.iterrows():
        print(f"  • {row['Scenario_ID']:<40} [{row['target_class']:<16}] ({row['topology']})")
    print("=" * 70)
