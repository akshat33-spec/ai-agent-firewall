import pandas as pd
import glob
import os

RESULTS_DIR = "revision/results"

def audit():
    log_files = glob.glob(f"{RESULTS_DIR}/logs_*.csv")
    if not log_files:
        print("No logs found.")
        return

    print(f"Files found: {log_files}")
    
    for file in log_files:
        strat = file.split('_')[-1].replace('.csv', '')
        df = pd.read_csv(file)
        
        total_records = len(df)
        # Unique eval key: (experiment_id, sample_id, strategy, repetition)
        keys = df[['experiment_id', 'sample_id', 'strategy', 'repetition']]
        unique_keys = keys.drop_duplicates().shape[0]
        
        print(f"\nStrategy: {strat}")
        print(f"  Total records: {total_records}")
        print(f"  Unique eval keys: {unique_keys}")
        if total_records != unique_keys:
            print(f"  !!! DUPLICATES FOUND: {total_records - unique_keys} records")
            
        # Check for missing columns
        required = ["experiment_id", "sample_id", "strategy", "repetition", "final_verdict"]
        missing = [col for col in required if col not in df.columns]
        if missing:
            print(f"  !!! MISSING COLUMNS: {missing}")
        else:
            print("  Schema Validation: OK")

if __name__ == "__main__":
    audit()
