import pandas as pd

RESULTS_FILE = "ablation_results.csv"

def analyze():
    try:
        df = pd.read_csv(RESULTS_FILE)
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    results = []
    for p_type in ["professional", "naive"]:
        subset = df[df['prompt_type'] == p_type]
        
        for group in ['Fixed-Cheap', 'Adaptive-Depth']:
            group_subset = subset[subset['group'] == group]
            adversarial = group_subset[group_subset['label'] == 'adversarial']
            
            if len(adversarial) == 0:
                asr = 0.0
            else:
                passes = len(adversarial[adversarial['decision'] == 'PASS'])
                asr = (passes / len(adversarial)) * 100
            
            results.append({
                'Prompt': p_type,
                'Group': group,
                'ASR': asr,
                'Sample_Count': len(adversarial)
            })

    res_df = pd.DataFrame(results)
    print("\n=== ABLATION STUDY RESULTS ===")
    print(res_df.to_string(index=False))

if __name__ == "__main__":
    analyze()
