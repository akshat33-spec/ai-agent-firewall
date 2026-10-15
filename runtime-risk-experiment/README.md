# Runtime Risk Detection Experiment

**Research question**: How does accumulated benign agent context affect the detection of distributed multi-step security risks by runtime risk detectors?

**Hypothesis**: Increasing benign context will degrade detection performance, with a greater degradation for distributed multi-step risks than for localized single-step risks.

---

## Project Layout

```
runtime-risk-experiment/
├── environment/          # Deterministic agent environment
│   ├── state.py          # EnvironmentState, initial_state()
│   ├── tools.py          # select_resource, create_export_job, etc.
│   └── evaluator.py      # security_violation() — ground truth
├── scenarios/
│   ├── scenario1_spec.md # Scenario specification (source of truth)
│   └── data_exposure.py  # Positive/negative trajectory runners
├── context/
│   └── generator.py      # Benign filler context generation (tiktoken)
├── detector/
│   └── monitor.py        # LLM-based runtime monitor interface
├── experiments/
│   ├── run_ablation.py   # 15-subset deterministic validation
│   ├── run_calibration.py # Calibration across 7 token levels
│   ├── run_experiment.py  # Main 2×3 detection matrix
│   └── run_all.py         # Pipeline orchestrator
├── experiment_config.json # Main experiment configuration
├── calibration_config.json # Calibration configuration
├── experiment_design.md   # Formal experiment design document
└── results/               # All run outputs (never overwritten)
```

---

## Quick Start

```powershell
# Install dependencies
pip install -r requirements.txt

# 1. Validate everything (no LLM calls)
$env:PYTHONUTF8=1; python -m experiments.run_all --dry-run

# 2. Run ablation only (verifies scenario semantics)
$env:PYTHONUTF8=1; python -m experiments.run_all --ablation-only

# 3. Run calibration (determines useful context levels, requires API key)
$env:OPENAI_API_KEY="sk-..."
$env:PYTHONUTF8=1; python -m experiments.run_all --calibrate

# 4. Run the main 2×3 confirmatory experiment (after reviewing calibration)
$env:PYTHONUTF8=1; python -m experiments.run_all
```

You can also invoke the calibration standalone:
```powershell
$env:PYTHONUTF8=1; python -m experiments.run_calibration --dry-run
$env:PYTHONUTF8=1; python -m experiments.run_calibration
```

---

## Experiment Phases

### Phase 1 — Scenario Validation (ablation)
Runs 15 action subsets of the distributed risk trajectory against the deterministic evaluator. All 14 proper subsets must produce SAFE; only the complete A+B+C+D must produce UNSAFE.

**Status: PASSED (15/15)**

### Phase 2 — Infrastructure Dry Run
Validates all modules, context generation, detector prompt, token counting, and result storage — without making any LLM calls.

**Status: PASSED**

### Phase 3 — Calibration
Measures detection rates across 7 filler-context lengths (300 to 100,000 tokens) for both risk structures and both sample types. Identifies ceiling, floor, and transition regions to inform level selection for the confirmatory experiment.

**Run**: `python -m experiments.run_all --calibrate`

### Phase 4 — Confirmatory Experiment (2×3 matrix)
Runs the main 2×3 design after calibration levels are confirmed by the researcher.

**Do NOT run until calibration has been reviewed.**

---

## Ground Truth

Ground truth is determined exclusively by `environment/evaluator.py::security_violation(state)` — a deterministic function of environment state. The LLM detector never determines ground truth.

---

## Key Design Constraints

- Benign filler is prepended before the attack trajectory; **no filler is inserted between evidence-bearing actions**
- The detector receives only observable action text, never EnvironmentState
- Temperature = 0 for all formal experiment calls
- All runs are saved to unique directories; previous runs are never overwritten
- Errors are recorded explicitly; results are never fabricated or silently repaired

---

## Result Storage

```
results/
  YYYY-MM-DD_scenario1_runNNN/      ← main experiment
    config.json
    ablation_results.csv
    validation_report.md
    detector_results.csv
    raw_predictions.jsonl
    summary.md
    git_commit.txt

  YYYY-MM-DD_calibration_runNNN/    ← calibration
    config.json
    calibration_results.csv
    calibration_raw.jsonl
    calibration_report.md
    calibration_summary.json
    git_commit.txt
```
