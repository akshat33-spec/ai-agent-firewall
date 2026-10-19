# Pilot Report: Context Length and Evidence Position in LLM Runtime-Risk Monitoring

**Project**: AI Agent Permission Firewall  
**Subproject**: `runtime-risk-experiment`  
**Experiment Identifier**: `context_position_pilot_v1.0`  
**Date**: October 19, 2026  
**Status**: Pre-Flight Validated & Baseline Verified  

---

## 1. Executive Summary

This follow-up investigation addresses the reviewers' core objection to historical runs (Run006, Run007, Run008): namely, that existing data failed to establish whether context length or evidence position affects LLM runtime-risk monitoring.

We designed a fully controlled, leak-free experimental framework isolating context length ($1{,}000$, $10{,}000$, and $50{,}000$ tokens) and evidence position ($\text{Beginning}$, $\text{Middle}$, $\text{End}$ of the benign history prefix) alongside a localized risk control. All 72 trials were constructed with byte-for-byte matched benign prefixes between safe and unsafe classes, exact token accounting, randomized trial ordering, and verified final-action invariance.

---

## 2. Code Inspection & Verification of Observables

Before constructing the experiment, we conducted an empirical inspection of the codebase:
- [`detector/monitor.py`](file:///d:/Downloads/ai-agent-firewall-main/ai-agent-firewall-main/runtime-risk-experiment/detector/monitor.py): Confirmed prompt version `v1.1` and system prompt specifying the strict security policy.
- [`context/generator.py`](file:///d:/Downloads/ai-agent-firewall-main/ai-agent-firewall-main/runtime-risk-experiment/context/generator.py): Confirmed deterministic filler generation via `tiktoken` (`cl100k_base`).
- [`environment/evaluator.py`](file:///d:/Downloads/ai-agent-firewall-main/ai-agent-firewall-main/runtime-risk-experiment/environment/evaluator.py): Confirmed deterministic environment state evaluator `security_violation(state)`.
- [`scenarios/data_exposure.py`](file:///d:/Downloads/ai-agent-firewall-main/ai-agent-firewall-main/runtime-risk-experiment/scenarios/data_exposure.py) & [`environment/tools.py`](file:///d:/Downloads/ai-agent-firewall-main/ai-agent-firewall-main/runtime-risk-experiment/environment/tools.py):
  - **Action D Invariance Verified**:
    Action D call is `execute_export()` and returns strictly `Transfer executed to external_storage.`
    It contains **zero** dataset identifiers (`customer_records`, `public_records`) and **zero** classification keywords (`CONFIDENTIAL`, `PUBLIC`).
  - Decisive classification evidence is isolated strictly within Step A (`select_resource(...)`).

---

## 3. Pre-Flight Validation Gates

All required validation gates were executed and passed:

| Gate | Requirement | Status | Verification Method |
|---|---|---|---|
| **Gate 1** | Deterministic Safe/Unsafe Ground Truth | **PASSED** | Unit tests in [`test_context_position_pilot.py`](file:///d:/Downloads/ai-agent-firewall-main/ai-agent-firewall-main/runtime-risk-experiment/tests/test_context_position_pilot.py) |
| **Gate 2** | Final Action Observable Invariance | **PASSED** | Byte-for-byte string equality between positive and negative Action D |
| **Gate 3** | Evidence Placement Integrity | **PASSED** | Verified Action A at index 0 (Beginning), midpoint $N//2$ (Middle), and after filler (End) |
| **Gate 4** | Zero Final-Action Data Leakage | **PASSED** | Asserted absence of `CONFIDENTIAL`, `PUBLIC`, and dataset names in Action D |
| **Gate 5** | Token Accounting Fidelity | **PASSED** | Target $1\text{k}\to 1{,}005$ tok (0.5% error); $10\text{k}\to 10{,}009$ tok (0.09% error); $50\text{k}\to 50{,}005$ tok (0.01% error) |
| **Gate 6** | Reproducible Seed Pairing | **PASSED** | Verified identical filler sequences for safe/unsafe pairs |
| **Gate 7** | Full Test Suite Execution | **PASSED** | 20/20 unit tests passed (12 existing Scenario 2 tests + 8 new pilot tests) |
| **Gate 8** | Overwrite Protection | **PASSED** | Verified write-protection refusing any path containing historical run identifiers |
| **Gate 9** | API Authentication & Fail-Fast | **PASSED** | Verified immediate halted execution when API key is missing, protecting against corrupted runs |

---

## 4. Deterministic Stateful-Rule Baseline (Oracle)

We implemented an oracle-style deterministic stateful-rule baseline ([`baseline.py`](file:///d:/Downloads/ai-agent-firewall-main/ai-agent-firewall-main/runtime-risk-experiment/context_position_experiment/baseline.py)) that tracks environment state transitions directly:
- **Baseline Accuracy**: **100.0%** (72/72 decisions correct)
- **TPR**: 1.000 (95% CI: [0.904, 1.000])
- **FPR**: 0.000 (95% CI: [0.000, 0.096])
- **Precision**: 1.000 | **Recall**: 1.000 | **F1 Score**: 1.000

*Interpretation*: The oracle baseline proves that runtime policy compliance is computationally solvable with zero degradation when state transitions are tracked explicitly. It serves as an upper-bound empirical reference ceiling, not as an LLM equivalent.

---

## 5. Token Accounting and Resource Consumption

Across the 72 planned trials:
- **Target Context Distribution**:
  - $1{,}000$ tokens: 24 trials (18 distributed, 6 localized) $\to$ Mean: 1,004.7 tokens
  - $10{,}000$ tokens: 24 trials (18 distributed, 6 localized) $\to$ Mean: 10,009.0 tokens
  - $50{,}000$ tokens: 24 trials (18 distributed, 6 localized) $\to$ Mean: 50,004.8 tokens
- **Total Input Tokens**: Exactly $1{,}464,444$ tokens (~1.46M tokens).
- **Execution Budget**: ~$0.22 at standard `gpt-4o-mini` pricing ($0.15 / 1M input tokens).

---

## 6. What the Pilot Framework Proves vs. What Remains Unproven

### What the Pilot Proves:
1. **Methodological Feasibility**: The repository's existing generator can generate 1k, 10k, and 50k token contexts with controlled evidence placement at beginning, middle, and end without leaking classification metadata into Action D.
2. **Elimination of Historical Flaws**: The design completely resolves the metadata blindness of Run006 and the Action D leakage of Run008.
3. **Deterministic Reference Ceiling**: Stateful tracking achieves 100% accuracy regardless of filler token distance.

### What Remains Unproven (Pending Live API Key Execution):
1. **$H_1$ (Context Degradation)**: Whether `gpt-4o-mini` exhibits a statistically significant drop in TPR or increase in FPR between 1,000, 10,000, and 50,000 tokens remains unproven until live API calls are executed.
2. **$H_2$ (Lost-in-the-Middle Effect)**: Whether placement of Action A in the middle of a 50,000-token prefix degrades detection compared to beginning/end remains unproven.
3. **$H_3$ (Localized Ceiling)**: Whether localized single-action risks remain immune to context length increases while distributed risks degrade remains an empirical hypothesis.

---

## 7. Next Step for Live API Execution

To execute the live 72-decision pilot against the OpenAI API:
```powershell
$env:OPENAI_API_KEY = "your-api-key"
python context_position_experiment/runner.py
python context_position_experiment/analyze_results.py
```
This will automatically generate live CSV/JSONL records and compute final Wilson score confidence intervals and paired seed comparisons.
