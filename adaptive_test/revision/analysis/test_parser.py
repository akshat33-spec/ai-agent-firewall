from revision.src.run_benchmark_stable import sanitize_decision

test_cases = [
    ("PASS", "PASS"),
    ("FAIL", "FAIL"),
    ("UNSURE", "UNSURE"),
    ("  pass  ", "PASS"),
    ("FAIL!", "FAIL"),
    ("Verdict: PASS", "PASS"),
    ("The result is FAIL", "FAIL"),
    ("I am not sure, so UNSURE", "UNSURE"),
    ("This is a long explanation. Verdict: PASS", "PASS"),
    ("Both PASS and FAIL here", "FAIL"), # should take the last one per logic
    ("", "UNSURE"),
    (None, "UNSURE"),
    ("Random text", "UNSURE"),
    ("NOT PASS", "UNSURE"), # My current sanitize_decision doesn't handle 'NOT' specifically, it looks for PASS/FAIL/UNSURE
]

print(f"{'Input':<40} | {'Expected':<10} | {'Actual':<10} | {'Result'}")
print("-" * 70)

for inp, exp in test_cases:
    act = sanitize_decision(inp)
    res = "✅" if act == exp else "❌"
    print(f"{str(inp):<40} | {exp:<10} | {act:<10} | {res}")
