import pandas as pd
import numpy as np

RESULTS_FILE = "results_full_study.csv"

def analyze():
    df = pd.read_csv(RESULTS_FILE)
    
    # --- 1. Tail Latency Analysis ---
    # We look at Adaptive-Depth latency
    adaptive_df = df[df['group'] == 'Adaptive-Depth'].sort_values(by='latency', ascending=False)
    slowest_5 = adaptive_df.head(5)
    
    print("\n=== TOP 5 SLOWEST ADAPTIVE SAMPLES ===")
    print(slowest_5[['id', 'label', 'decision', 'latency']])
    
    # --- 2. Triage Audit ---
    # We need to look at the raw logic in the code, but from the CSV we can see 
    # the decision. However, the CSV only stores the FINAL decision for Adaptive.
    # To get the 'UNSURE' count, we'd need a different log or to re-run.
    # But we can look at the Fixed-Cheap vs Adaptive-Depth decision.
    # If Fixed-Cheap was PASS but Adaptive was FAIL, it was an escalation that caught a leak.
    
    # --- 3. Failure Mode Mapping ---
    # Find where Cheap failed (PASS) but Deep succeeded (FAIL)
    # Pivot the data to have one row per ID
    pivot_df = df.pivot(index='id', columns='group', values='decision')
    # Need to bring back the label
    labels = df[df['group'] == 'Fixed-Cheap'][['id', 'label']].set_index('id')
    full_df = pivot_df.join(labels)
    
    # Leaks: Fixed-Cheap said PASS, but Fixed-Deep said FAIL
    leaks = full_df[(full_df['Fixed-Cheap'] == 'PASS') & (full_df['Fixed-Deep'] == 'FAIL')]
    
    print("\n=== LEAKAGE ANALYSIS (Fixed-Cheap PASS vs Fixed-Deep FAIL) ===")
    print(f"Total Leaks Caught by Escalation: {len(leaks)}")
    
    # Breakdown leaks by label (though they should all be adversarial)
    leak_dist = leaks['label'].value_counts()
    print("\nLeak distribution by label:")
    print(leak_dist)

    # Identify the 'Hardest' samples (those where Fixed-Cheap was very confident but wrong)
    # Let's look at some examples of these leaks
    print("\n=== EXAMPLE LEAKS (Samples where Cheap failed) ===")
    if len(leaks) > 0:
        print(leaks.head(5))

if __name__ == "__main__":
    analyze()
