import json
import os
from collections import Counter

DATASET_PATH = "revision/data/dataset_v1.json"

def audit():
    if not os.path.exists(DATASET_PATH):
        print(f"Error: {DATASET_PATH} not found.")
        return

    with open(DATASET_PATH, 'r') as f:
        data = json.load(f)
    
    total = len(data)
    labels = Counter([item.get('label') for item in data])
    categories = Counter([item.get('attack_category') for item in data])
    
    print("="*30)
    print("DATASET AUDIT RESULTS")
    print("="*30)
    print(f"Total Samples: {total}")
    print("\nLabels:")
    for label, count in labels.items():
        print(f"  - {label}: {count} ({count/total*100:.2f}%)")
        
    print("\nAttack Categories:")
    for cat, count in categories.items():
        print(f"  - {cat}: {count}")
    print("="*30)

if __name__ == "__main__":
    audit()
