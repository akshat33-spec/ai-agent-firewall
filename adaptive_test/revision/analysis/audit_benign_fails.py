import pandas as pd
import glob
import os

RESULTS_DIR = "revision/results"

def audit_benign_fails():
    log_files = glob.glob(f"{RESULTS_DIR}/logs_*.csv")
    if not log_files: return

    for file in log_files:
        strat = file.split('_')[-1].replace('.csv', '')
        df = pd.read_csv(file)
        
        # Find benign samples that were blocked (final_verdict contains FAIL or is UNSURE)
        # Note: In our current logic, any non-PASS is a block.
        benign_fails = df[(df['ground_truth'] == 'benign') & (~df['final_verdict'].str.contains('PASS', na=False))]
        
        if not benign_fails.empty:
            print(f"\n=== Strategy: {strat} ===")
            for idx, row in benign_fails.iterrows():
                print(f"Sample: {row['sample_id']}")
                print(f"  T2 Verdict: {row['tier2_verdict']}")
                print(f"  T3 Verdict: {row['tier3_verdict']}")
                print(f"  Final: {row['final_verdict']}")
                print(f"  Route: {row['terminal_route']}")
                print(f"  Latency: {row['total_latency_ms']:.2f}ms")
                print("-" * 20)

if __name__ == "__main__":
    audit_benign_fails()
