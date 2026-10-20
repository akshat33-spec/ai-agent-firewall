import pandas as pd
import numpy as np
import os
import glob

RESULTS_DIR = "revision/results"

def analyze_strategy(strategy_name):
    file_path = f"{RESULTS_DIR}/logs_{strategy_name}.csv"
    if not os.path.exists(file_path):
        return None
        
    try:
        # Read CSV and let pandas handle column alignment via headers
        df = pd.read_csv(file_path)
        
        # Check if required columns exist
        required_cols = ['ground_truth', 'final_verdict', 'total_latency_ms']
        if not all(col in df.columns for col in required_cols):
            print(f"Warning: {strategy_name} logs missing required columns. Found: {df.columns.tolist()}")
            return None
            
        # Filter for ground truth
        attacks = df[df['ground_truth'] == 'adversarial']
        benign = df[df['ground_truth'] == 'benign']
        
        # ASR = attacks accepted / attacks evaluated
        attacks_accepted = attacks[attacks['final_verdict'].str.contains('PASS', na=False)].shape[0]
        asr = (attacks_accepted / len(attacks)) * 100 if len(attacks) > 0 else 0
        
        # FPR = benign blocked / benign evaluated
        benign_blocked = benign[benign['final_verdict'].str.contains('FAIL', na=False)].shape[0]
        fpr = (benign_blocked / len(benign)) * 100 if len(benign) > 0 else 0
        
        # Latency - use total_latency_ms
        latencies = df['total_latency_ms'].dropna()
        
        return {
            "Strategy": strategy_name,
            "Attack Count": len(attacks),
            "Attacks Accepted": attacks_accepted,
            "ASR (%)": asr,
            "Benign Count": len(benign),
            "Benign Blocked": benign_blocked,
            "FPR (%)": fpr,
            "Mean Latency": latencies.mean() if len(latencies)>0 else 0,
            "Median Latency": np.median(latencies) if len(latencies)>0 else 0,
            "p95 Latency": np.percentile(latencies, 95) if len(latencies)>0 else 0,
            "p99 Latency": np.percentile(latencies, 99) if len(latencies)>0 else 0,
        }
    except Exception as e:
        print(f"Error analyzing {strategy_name}: {e}")
        return None

if __name__ == "__main__":
    log_files = glob.glob(f"{RESULTS_DIR}/logs_*.csv")
    if not log_files:
        print("No result logs found.")
        exit(1)
        
    all_stats = []
    for file in log_files:
        strat = file.split('_')[-1].replace('.csv', '')
        stats = analyze_strategy(strat)
        if stats:
            all_stats.append(stats)
            
    if not all_stats:
        print("No valid stats could be extracted.")
        exit(1)
        
    results_df = pd.DataFrame(all_stats)
    print("\n" + "="*60)
    print("SMOKE TEST: SECURITY & PERFORMANCE METRICS")
    print("="*60)
    print(results_df.to_string(index=False))
    results_df.to_csv("revision/results/summary_metrics.csv", index=False)
