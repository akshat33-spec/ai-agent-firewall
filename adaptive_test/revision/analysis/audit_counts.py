import pandas as pd
import glob
import os

RESULTS_DIR = "revision/results"

def audit():
    log_files = glob.glob(f"{RESULTS_DIR}/logs_*.csv")
    all_data = []
    for file in log_files:
        strat = file.split('_')[-1].replace('.csv', '')
        df = pd.read_csv(file)
        df['file'] = file
        df['strategy'] = strat
        all_data.append(df)
    
    if not all_data:
        print("No logs found.")
        return

    full_df = pd.concat(all_data)
    
    print("="*40)
    print("COUNT RECONCILIATION")
    print("="*40)
    
    # 1. Total records per strategy
    print("\nTotal records per strategy:")
    print(full_df.groupby('strategy').size())
    
    # 2. Unique evaluation keys
    # Key: (experiment_id, sample_id, strategy, repetition)
    keys = full_df[['experiment_id', 'sample_id', 'strategy', 'repetition']]
    unique_keys = keys.drop_duplicates()
    print(f"\nUnique evaluation keys: {len(unique_keys)}")
    print(f"Total records: {len(full_df)}")
    
    if len(unique_keys) != len(full_df):
        print("\nWARNING: DUPLICATE RECORDS FOUND")
        dupes = full_df[full_df.duplicated(subset=['experiment_id', 'sample_id', 'strategy', 'repetition'], keep=False)]
        print(dupes[['experiment_id', 'sample_id', 'strategy', 'repetition']].sort_values(['sample_id', 'strategy']).head(10))

    # 3. Grouped counts
    print("\nCounts grouped by Strategy and Sample:")
    print(full_df.groupby(['strategy', 'sample_id']).size())

if __name__ == "__main__":
    audit()
