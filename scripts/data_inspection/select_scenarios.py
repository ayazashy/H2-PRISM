"""
Benchmark Scenario Selector & Standardizer (Person 3: Yazan / Materials Lead).
Selects 6 representative scenarios from data/raw/H2-SimNet-Dataset/:
1. Normal Baseline (Steady State)
2. Weak Incipient Leak (leakG4 Transient)
3. Strong Localized Leak (leakG3 Steady State)
4. Overlapping Leaks (leakG5G6 Overlapped)
5. Compressor Operational Transient (brokenC1)
6. Compressor Delay (delayC1)

Copies them to data/selected/ and converts to standardized format in data/processed/.
"""

from pathlib import Path
import shutil
import pandas as pd
import numpy as np


BENCHMARK_SCENARIOS = [
    {
        "id": "scen_normal_001",
        "name": "normality_gest_center.csv",
        "relative_raw": "MATLAB_SIMSCAPE_Simulation/normality_scenarios/normality_gest_center.csv",
        "type": "NORMAL",
        "desc": "Normal steady-state operation with center topology"
    },
    {
        "id": "scen_leak_g4_weak",
        "name": "leakG4.csv",
        "relative_raw": "anomalous-scenarios/csv/anom_gestdown/assestment_transient/leakG4.csv",
        "type": "LEAK_WEAK_G4",
        "desc": "Weak transient leak at restriction valve G4 (gest_down)"
    },
    {
        "id": "scen_leak_g3_strong",
        "name": "leakG3.csv",
        "relative_raw": "anomalous-scenarios/csv/anom_gestdown/start_transient/leakG3.csv",
        "type": "LEAK_STRONG_G3",
        "desc": "Strong localized leak at restriction valve G3 (gest_down)"
    },
    {
        "id": "scen_leak_g5g6_overlap",
        "name": "leakG5G6_overlapped.csv",
        "relative_raw": "anomalous-scenarios/csv/anom_gestdown/assestment_transient/leakG5G6_overlapped.csv",
        "type": "LEAK_OVERLAPPED",
        "desc": "Overlapping multi-location leaks at G5 and G6"
    },
    {
        "id": "scen_comp_fault_c1",
        "name": "brokenC1_strong.csv",
        "relative_raw": "anomalous-scenarios/csv/anom_gestdown/constant_segment/brokenC1_strong.csv",
        "type": "COMPRESSOR_FAULT",
        "desc": "Compressor ramp-up failure at C1 (gest_down)"
    },
    {
        "id": "scen_comp_delay_c1",
        "name": "startdelayC1.csv",
        "relative_raw": "anomalous-scenarios/csv/anom_gestdown/constant_segment/startdelayC1.csv",
        "type": "COMPRESSOR_DELAY",
        "desc": "Compressor startup delay transient at C1 (gest_down)"
    }
]


def select_and_standardize_benchmarks(
    raw_dir: Path = Path("data/raw/H2-SimNet-Dataset"),
    selected_dir: Path = Path("data/selected"),
    processed_dir: Path = Path("data/processed")
):
    selected_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"[+] Selecting 6 benchmark scenarios from raw dataset...")
    
    for item in BENCHMARK_SCENARIOS:
        src = raw_dir / item["relative_raw"]
        dst_selected = selected_dir / f"{item['id']}_{item['name']}"
        dst_processed = processed_dir / f"{item['id']}_standardized.csv"
        
        if not src.exists():
            print(f"[-] Warning: Source file not found: {src}")
            continue
            
        # Copy to selected/
        shutil.copyfile(src, dst_selected)
        print(f"[+] Selected: {src.name} -> {dst_selected.name}")
        
        # Standardize for pipeline:
        # 1. Add timestamp (0, 1, 2, ..., N-1) assuming dt = 1.0s
        # 2. Convert pressure from MPa to Pa (p_upstream = PS1 * 1e6, p_downstream = PS12 * 1e6)
        # 3. Map flow rates (m_inlet = MFS1, m_outlet = MFS3 or MFS4)
        df = pd.read_csv(src)
        n_rows = len(df)
        
        df_std = pd.DataFrame()
        df_std["timestamp"] = np.arange(n_rows, dtype=float)
        df_std["scenario_id"] = item["id"]
        df_std["run_id"] = "run_01"
        
        # Assign primary pipeline boundary pressures in Pa
        if "PS1" in df.columns:
            df_std["p_upstream"] = df["PS1"] * 1e6
        else:
            df_std["p_upstream"] = 3.5e6
            
        if "PS12" in df.columns:
            df_std["p_downstream"] = df["PS12"] * 1e6
        elif "PS6" in df.columns:
            df_std["p_downstream"] = df["PS6"] * 1e6
        else:
            df_std["p_downstream"] = 3.0e6
            
        # Assign mass flow in kg/s
        df_std["m_inlet"] = df["MFS1"] if "MFS1" in df.columns else 4.5
        
        # In H2-SimNet topology: gest_center delivers to MFS3; gest_down delivers to MFS4 (or MFS2)
        if "center" in item["relative_raw"]:
            df_std["m_outlet"] = df["MFS3"] if "MFS3" in df.columns else df["MFS1"]
        elif "MFS4" in df.columns:
            df_std["m_outlet"] = df["MFS4"]
        elif "MFS2" in df.columns:
            df_std["m_outlet"] = df["MFS2"]
        elif "MFS3" in df.columns:
            df_std["m_outlet"] = df["MFS3"]
        else:
            df_std["m_outlet"] = df_std["m_inlet"]
            
        # Preserve all individual sensor columns (MPa / kg/s)
        for col in df.columns:
            if col not in df_std.columns:
                df_std[col] = df[col]
                
        # Determine standard label
        if "label_anomaly" in df.columns:
            df_std["label"] = np.where(df["label_anomaly"] == 1, item["type"], "NORMAL")
        else:
            df_std["label"] = "NORMAL"
            
        df_std.to_csv(dst_processed, index=False)
        print(f"    -> Standardized: {dst_processed.name} ({len(df_std)} timesteps)")
        
    print(f"[+] All 6 benchmark scenarios successfully curated and standardized.")


if __name__ == "__main__":
    select_and_standardize_benchmarks()
