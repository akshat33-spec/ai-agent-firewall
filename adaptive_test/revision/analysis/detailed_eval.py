import pandas as pd
import os
import glob

RESULTS_DIR = "revision/results"

def report_detailed():
    log_files = glob.glob(f"{RESULTS_DIR}/logs_*.csv")
    if not log_files: return
    
    for file in log_files:
        strat = file.split('_')[-1].replace('.csv', '')
        print(f"\n--- Strategy: {strat} ---")
        df = pd.read_csv(file)
        
        # Selecting a subset of columns for the table
        cols = ["sample_id", "ground_truth", "tier2_verdict", "tier3_verdict", "final_verdict", "status", "terminal_route", "total_latency_ms"]
        # Ensure columns exist
        existing_cols = [c for c in cols if c in df.columns]
        print(df[existing_cols].to_string(index=False))

if __name__ == "__main__":
    report_detailed()
