import requests, json, time, os, csv, re
from revision.src.run_benchmark_stable import call_ollama, sanitize_decision, guard_deterministic

def debug_run():
    dataset = json.load(open("revision/data/pilot_dataset.json"))
    item = dataset[0]
    tool, args = item['tool'], item['args']
    
    print(f"Testing sample: {item['sample_id']}")
    
    # Test Deterministic
    v1 = guard_deterministic(args)
    print(f"T1: {v1}")
    
    # Test Cheap
    raw2, lat2 = call_ollama("llama3.2:latest", f"Prompt for {tool}({args})")
    v2 = sanitize_decision(raw2)
    print(f"T2: {v2} ({lat2:.2f}ms)")
    
    # Test Deep
    raw3, lat3 = call_ollama("llama3:latest", f"Prompt for {tool}({args})")
    v3 = sanitize_decision(raw3)
    print(f"T3: {v3} ({lat3:.2f}ms)")

if __name__ == "__main__":
    debug_run()
