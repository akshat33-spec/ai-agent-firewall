import pandas as pd
from scipy import stats
import numpy as np

RESULTS_FILE = "results_full_study.csv"

def run_final_analysis():
    try:
        # 1. Load Data
        df = pd.read_csv(RESULTS_FILE)
        
        print("\n--- DEBUGGING FILE STRUCTURE ---")
        print(f"Columns found in CSV: {df.columns.tolist()}")
        print(f"Total rows: {len(df)}")
        print("-" * 30)

        # AUTOMATIC COLUMN MAPPING
        # We look for columns that 'look like' group, label, and latency
        col_map: dict[str, str] = {}
        for col in df.columns:
            c_low = col.lower()
            if 'group' in c_low: col_map['group'] = col
            if 'label' in c_low: col_map['label'] = col
            if 'latency' in c_low: col_map['latency'] = col
            if 'decision' in c_low: col_map['decision'] = col

        if len(col_map) < 4:
            print(f"Error: Could not find all required columns. Found: {col_map}")
            return

        g_col = col_map['group']
        l_col = col_map['label']
        lat_col = col_map['latency']
        dec_col = col_map['decision']

        # Clean data: Remove NaNs
        df = df.dropna(subset=[lat_col, dec_col])

        # 2. Prepare Groups for ANOVA
        # We use the actual names found in your CSV
        group_names = df[g_col].unique()
        print(f"Groups found in data: {group_names}")
        
        latency_data = [
            pd.Series(df[df[g_col] == name][lat_col]).dropna().to_numpy(dtype=float)
            for name in group_names
        ]

        # 3. Calculate ANOVA
        f_stat, p_lat = stats.f_oneway(*latency_data)

        # 4. Calculate ASR (Attack Success Rate)
        def calc_asr(group_name: str) -> float:
            subset = df[(df[g_col] == group_name) & (df[l_col] == 'adversarial')]
            if len(subset) == 0: return 0.0
            # Check if 'PASS' is in the decision (case insensitive)
            dec_series = pd.Series(subset[dec_col], dtype="string")
            passes = dec_series.str.contains('PASS', na=False, case=False).sum()
            return float(passes / len(subset)) * 100.0

        # ==========================================
        # FINAL REPORT
        # ==========================================
        print("\n" + "="*30)
        print("FINAL RESEARCH RESULTS")
        print("="*30)
        
        if np.isnan(p_lat):
            print("Latency P-Value: Not Calculable (Zero Variance)")
        else:
            print(f"Latency P-Value: {p_lat:.4f} {'(Significant)' if p_lat < 0.05 else '(Not Significant)'}")
        print(f"F-Statistic: {f_stat:.4f}")
        
        for name in group_names:
            print(f"ASR {name}: {calc_asr(name):.2f}%")
        
        print("\n--- CONCLUSION ---")
        # Find which group is 'Adaptive' to check success
        adaptive_candidates = [n for n in group_names if 'Adaptive' in str(n)]
        deep_candidates = [n for n in group_names if 'Deep' in str(n)]
        
        if adaptive_candidates and deep_candidates:
            adaptive_group = adaptive_candidates[0]
            deep_group = deep_candidates[0]
            if calc_asr(adaptive_group) <= calc_asr(deep_group) + 5: 
                print("SUCCESS: Adaptive-Depth is as secure as the Deep model!")
            else:
                print("FAIL: Adaptive-Depth leaked too many attacks.")
        else:
            print("Warning: Could not identify both Adaptive and Deep groups for comparison.")

    except Exception as e:
        print(f"Analysis Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_final_analysis()