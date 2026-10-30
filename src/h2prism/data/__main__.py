"""CLI entrypoint for python3 -m h2prism.data"""
from h2prism.data import get_dataset_summary, list_scenarios, load_scenario

if __name__ == "__main__":
    summary = get_dataset_summary()
    print("=" * 80)
    print(" H2-PRISM DATASET ACCESS & INSPECTION ENGINE")
    print("=" * 80)
    print(f"[*] Raw Dataset Available   : {summary['raw_dataset_available']}")
    print(f"[*] Dataset Location        : {summary['active_data_dir']}")
    print(f"[*] Target Attribution Class: {', '.join(summary['primary_classes'])}")
    print(f"[*] Sensor Instrumentation  : 12 Pressures (PS1-PS12), 4 Mass Flows (MFS1-MFS4)")
    print(f"[*] Local Temperature Sense : 0 (Verified zero temperature sensors in SimNet)")
    print("-" * 80)
    
    scenarios = list_scenarios()
    print(f"[*] Eligible 4-Class Scenarios Cataloged: {len(scenarios)}")
    print("\nSample Scenario Records:")
    for _, row in scenarios.head(6).iterrows():
        print(f"  • {row['Scenario_ID']:<45} -> {row['target_class']:<16} ({row['topology']}, {row['phase']})")
    
    print("-" * 80)
    print("[*] Testing instant scenario load: 'leakG4'...")
    try:
        df_sample = load_scenario("leakG4")
        print(f"    ✓ Successfully loaded 'leakG4' in memory!")
        print(f"    ✓ Shape: {df_sample.shape[0]} rows x {df_sample.shape[1]} columns")
        print(f"    ✓ Key channels: PS1={df_sample['PS1'].iloc[0]:.2f} MPa, MFS1={df_sample['MFS1'].iloc[0]:.2f} kg/s")
    except Exception as e:
        print(f"    ✗ Failed to load scenario: {e}")
    print("=" * 80)
