# Research Revision Workspace: ASCP Framework

## 1. Architecture: The Rejection Cascade
The system implements a **Rejection Cascade**. A request is blocked immediately if any tier identifies it as prohibited. It is only authorized if it survives all tiers.

**Routing Logic:**
- **Tier 1 (Deterministic)**: If `forbidden_keywords` $\rightarrow$ **FAIL**.
- **Tier 2 (Semantic Fast-Lane)**: If `cheap_model` $\rightarrow$ **FAIL**.
- **Tier 3 (Reasoning Secure-Lane)**: Final decision by `deep_model`.

**Core Claim:** 
This architecture optimizes latency by performing "early rejection" of obvious attacks, ensuring the expensive deep auditor is only invoked for requests that are not clearly prohibited.

## 2. Experimental Setup
- **Hardware**: Apple M2 (16GB RAM).
- **Models**: Llama 3.2 (Lightweight) and Llama 3 (Deep), both INT4 GGUF.
- **Dataset**: `dataset_v1.json` (N=930), split into Benign and Adversarial (via 5 attack vectors).

## 3. Reproducibility Pipeline
1. **Data**: `generate_dataset_v1.py` $\rightarrow$ `data/dataset_v1.json`
2. **Execution**: `src/run_benchmark.py` $\rightarrow$ `results/logs_{strategy}.csv`
3. **Analysis**: `analysis/analysis_script.py` $\rightarrow$ `results/summary_metrics.csv`

## 4. Evaluation Metrics
- **ASR (Attack Success Rate)**: $\frac{\text{Attacks Accepted}}{\text{Total Attacks}}$
- **FPR (False Positive Rate)**: $\frac{\text{Benign Blocked}}{\text{Total Benign}}$
- **Latency**: Mean, Median, p95, p99 (measured as total wall-clock time).
