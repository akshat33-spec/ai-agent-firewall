import json, os
import pandas as pd
from revision.src.run_benchmark import run_strategy

dataset = json.load(open("revision/data/pilot_dataset.json"))
strategies = ["DeterministicDeep", "LightweightDeep", "FullCascade"]

for strat in strategies:
    print(f"Running {strat}...")
    res = run_strategy(strat, dataset)
    pd.DataFrame(res).to_csv(f"revision/results/logs_{strat}.csv", index=False)
    print(f"Finished {strat}")
