"""
Fast Forensic Dataset Audit & Manifest Generator (Pure Python Standard Library).
Parses all CSVs in data/raw/H2-SimNet-Dataset/ without third-party dependencies.
Outputs:
- results/materials_manifest.csv
- results/dataset_truth_table.md
"""

import csv
import os
from pathlib import Path


def parse_scenario_metadata(rel_path_str: str, file_name: str):
    p_lower = rel_path_str.lower()
    
    # Topology
    if "gestdown" in p_lower or "gest_down" in p_lower:
        topology = "gest_down"
    elif "gestcenter" in p_lower or "gest_center" in p_lower:
        topology = "gest_center"
    elif "gestup" in p_lower or "gest_up" in p_lower:
        topology = "gest_up"
    else:
        topology = "unspecified"
        
    # Phase
    if "start_transient" in p_lower:
        phase = "initial_rampup"
    elif "assestment_transient" in p_lower:
        phase = "transient"
    elif "constant_segment" in p_lower:
        phase = "steady_state"
    elif "normality" in p_lower:
        phase = "normal_operation"
    else:
        phase = "operational"

    # Fault Type
    stem = Path(file_name).stem
    s_lower = stem.lower()
    if "normal" in s_lower:
        fault_type = "NORMAL"
    elif "leakg3" in s_lower:
        fault_type = "LEAK_G3"
    elif "leakg4" in s_lower:
        fault_type = "LEAK_G4"
    elif "leakg5g6" in s_lower:
        fault_type = "LEAK_G5_G6_OVERLAPPED"
    elif "brokenc1" in s_lower:
        fault_type = "COMPRESSOR_FAULT_C1"
    elif "delayc1" in s_lower:
        fault_type = "COMPRESSOR_DELAY_C1"
    else:
        fault_type = stem

    return topology, phase, fault_type


def main():
    raw_dir = Path("data/raw/H2-SimNet-Dataset")
    if not raw_dir.exists():
        print("Raw dir not found:", raw_dir)
        return

    csv_files = sorted(list(raw_dir.glob("**/*.csv")))
    print(f"[+] Found {len(csv_files)} CSV files in {raw_dir}")

    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)

    manifest_rows = []
    total_timesteps = 0
    all_headers = set()
    category_counts = {}

    for idx, fpath in enumerate(csv_files):
        rel_path = str(fpath.relative_to(Path(".")))
        topology, phase, fault = parse_scenario_metadata(rel_path, fpath.name)
        
        row_count = 0
        has_anomaly = 0
        anomaly_count = 0
        p_min, p_max = float("inf"), float("-inf")
        m_min, m_max = float("inf"), float("-inf")
        headers = []

        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            try:
                headers = next(reader)
                all_headers.update(headers)
                
                # Column indices
                ps_indices = [i for i, h in enumerate(headers) if h.startswith("PS")]
                mfs_indices = [i for i, h in enumerate(headers) if h.startswith("MFS")]
                anom_idx = headers.index("label_anomaly") if "label_anomaly" in headers else -1

                for row in reader:
                    if not row:
                        continue
                    row_count += 1
                    
                    if anom_idx != -1 and anom_idx < len(row):
                        try:
                            val = int(float(row[anom_idx]))
                            if val == 1:
                                has_anomaly = 1
                                anomaly_count += 1
                        except ValueError:
                            pass

                    # Min/Max for pressure
                    for psi in ps_indices:
                        if psi < len(row):
                            try:
                                v = float(row[psi])
                                if v < p_min: p_min = v
                                if v > p_max: p_max = v
                            except ValueError:
                                pass

                    # Min/Max for mass flow
                    for mfsi in mfs_indices:
                        if mfsi < len(row):
                            try:
                                v = float(row[mfsi])
                                if v < m_min: m_min = v
                                if v > m_max: m_max = v
                            except ValueError:
                                pass

            except Exception as e:
                print(f"[-] Error reading {fpath}: {e}")

        total_timesteps += row_count
        file_size_kb = round(fpath.stat().st_size / 1024, 2)
        anom_frac = round(anomaly_count / max(1, row_count), 4)

        cat_key = (topology, phase, fault)
        category_counts[cat_key] = category_counts.get(cat_key, 0) + 1

        record = {
            "file_id": f"scen_{idx+1:03d}",
            "file_path": rel_path,
            "file_name": fpath.name,
            "topology": topology,
            "operational_phase": phase,
            "fault_type": fault,
            "num_rows": row_count,
            "num_columns": len(headers),
            "has_anomaly": has_anomaly,
            "anomaly_fraction": anom_frac,
            "p_range_mpa": f"[{p_min:.3f}, {p_max:.3f}]" if p_min != float("inf") else "N/A",
            "m_range_kg_s": f"[{m_min:.3f}, {m_max:.3f}]" if m_min != float("inf") else "N/A",
            "file_size_kb": file_size_kb
        }
        manifest_rows.append(record)

    # Write Manifest CSV
    manifest_csv_path = results_dir / "materials_manifest.csv"
    fieldnames = [
        "file_id", "file_path", "file_name", "topology", "operational_phase",
        "fault_type", "num_rows", "num_columns", "has_anomaly", "anomaly_fraction",
        "p_range_mpa", "m_range_kg_s", "file_size_kb"
    ]
    with open(manifest_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest_rows)
    print(f"[+] Saved materials manifest to {manifest_csv_path} ({len(manifest_rows)} records)")

    # Write Truth Table Markdown
    truth_path = results_dir / "dataset_truth_table.md"
    with open(truth_path, "w", encoding="utf-8") as f:
        f.write("# H2-SimNet Dataset Truth Table & Provenance Catalog\n\n")
        f.write(f"- **Total Scenarios Audited**: {len(manifest_rows)}\n")
        f.write(f"- **Total Timesteps Across Scenarios**: {total_timesteps:,}\n")
        f.write(f"- **Verified Signal Channels**: `{', '.join(sorted(list(all_headers))) }`\n")
        f.write(f"- **Nominal Sampling Resolution**: 1.0 s / 1 Hz (Each scenario = 20,000 timesteps ≈ 5.5 hours)\n\n")
        f.write("## Scenario Distribution by Operational Category\n\n")
        f.write("| Topology | Phase | Fault Type | Scenario Count |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        for (top, ph, flt), cnt in sorted(category_counts.items()):
            f.write(f"| `{top}` | `{ph}` | `{flt}` | {cnt} |\n")

        f.write("\n\n## Representative Scenario Sample Catalog\n\n")
        f.write("| ID | File Name | Topology | Phase | Fault Type | Has Anomaly | Anomaly Ratio |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for r in manifest_rows[:30]:
            f.write(f"| `{r['file_id']}` | `{r['file_name']}` | `{r['topology']}` | `{r['operational_phase']}` | `{r['fault_type']}` | {r['has_anomaly']} | {r['anomaly_fraction']} |\n")
        if len(manifest_rows) > 30:
            f.write(f"\n*(Truncated: {len(manifest_rows)} total records recorded in `results/materials_manifest.csv`)*\n")

    print(f"[+] Saved dataset truth table to {truth_path}")


if __name__ == "__main__":
    main()
