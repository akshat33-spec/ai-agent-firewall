import pandas as pd
import json
import os
import glob

RESULTS_DIR = "revision/results"

def inspect():
    with open("revision/data/pilot_dataset_mini.json", 'r') as f:
        dataset = {item['sample_id']: item for item in json.load(f)}
    
    log_files = glob.glob(f"{RESULTS_DIR}/logs_*.csv")
    for file in log_files:
        strat = file.split('_')[-1].replace('.csv', '')
        df = pd.read_csv(file)
        
        # Benign samples that were blocked
        # A request is blocked if final_verdict is not PASS
        benign_fails = df[(df['ground_truth'] == 'benign') & (~df['final_verdict'].str.contains('PASS', na=False))]
        
        if not benign_fails.empty:
            print(f"\n{'='*60}\nStrategy: {strat}\n{'='*60}")
            for idx, row in benign_fails.iterrows():
                sid = row['sample_id']
                sample = dataset.get(sid, {})
                
                print(f"\nSample: {sid}")
                print(f"Prompt Tool: {sample.get('tool', 'unknown')}({sample.get('args', 'unknown')})")
                
                # Safely access raw responses
                t2_raw = row.get('tier2_raw', 'COLUMN_MISSING')
                t2_verd = row.get('tier2_verdict', 'COLUMN_MISSING')
                t3_raw = row.get('tier3_raw', 'COLUMN_MISSING')
                t3_verd = row.get('tier3_verdict', 'COLUMN_MISSING')
                
                if row.get('tier2_invoked', False):
                    print(f"T2 Raw: {t2_raw}")
                    print(f"T2 Verdict: {t2_verd}")
                
                if row.get('tier3_invoked', False):
                    print(f"T3 Raw: {t3_raw}")
                    print(f"T3 Verdict: {t3_verd}")
                
                print(f"Final: {row.get('final_verdict', 'N/A')} via {row.get('terminal_route', 'N/A')}")
                print(f"Latency: {row.get('total_latency_ms', 0):.2f}ms")
                print("-" * 30)

if __name__ == "__main__":
    inspect()
