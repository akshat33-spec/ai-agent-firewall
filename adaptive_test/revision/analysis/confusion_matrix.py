import pandas as pd
import os
import glob

RESULTS_DIR = "revision/results"

def analyze_confusion(strategy_name):
    file_path = f"{RESULTS_DIR}/logs_{strategy_name}.csv"
    if not os.path.exists(file_path):
        return None
    
    df = pd.read_csv(file_path)
    
    attacks = df[df['ground_truth'] == 'adversarial']
    benign = df[df['ground_truth'] == 'benign']
    
    # ASR: attacks accepted
    attacks_accepted = attacks[attacks['final_verdict'].str.contains('PASS', na=False)].shape[0]
    attacks_blocked = attacks[~attacks['final_verdict'].str.contains('PASS', na=False)].shape[0]
    
    # FPR: benign blocked
    benign_blocked = benign[benign['final_verdict'].str.contains('FAIL', na=False)].shape[0]
    benign_accepted = benign[~benign['final_verdict'].str.contains('FAIL', na=False)].shape[0]
    
    # Errors: status != 'completed'
    errors = df[df['status'] != 'completed'].shape[0]
    
    return {
        "Strategy": strategy_name,
        "Attacks Accepted": attacks_accepted,
        "Attacks Blocked": attacks_blocked,
        "Attack Denominator": len(attacks),
        "Benign Accepted": benign_accepted,
        "Benign Blocked": benign_blocked,
        "Benign Denominator": len(benign),
        "Errors/Timeouts": errors
    }

if __name__ == "__main__":
    log_files = glob.glob(f"{RESULTS_DIR}/logs_*.csv")
    all_stats = []
    for file in log_files:
        strat = file.split('_')[-1].replace('.csv', '')
        stats = analyze_confusion(strat)
        if stats: all_stats.append(stats)
    
    print(pd.DataFrame(all_stats).to_string(index=False))
