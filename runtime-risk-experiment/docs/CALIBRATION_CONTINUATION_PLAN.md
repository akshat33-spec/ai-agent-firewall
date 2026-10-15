# Calibration Continuation Plan

**Date**: 2026-10-13
**Prerequisite**: MODEL_CONTEXT_AUDIT.md, EXPERIMENT_REPRODUCTION_AUDIT.md,
PROMPT_CORRECTION_AND_SMOKE_TEST.md

---

## 1. Current Calibration Status

| Run | Prompt | TPR | FPR | Scientifically Informative? |
|-----|--------|-----|-----|---------------------------|
| run006 | v1.0 | 1.0 | 1.0 | **NO** — constant UNSAFE classifier |
| run007 | v1.1 | 1.0 | 0.325 | **PARTIALLY** — interesting distributed FPR but not reproducible |
| run008 | v1.1 | 1.0 | 0.0 | **NO** — ceiling performance, no variation to analyze |

### Core problem

Under the corrected v1.1 prompt, the model achieves **perfect discrimination**
(TPR=1.0, FPR=0.0) across all six feasible context levels (1k–100k tokens)
and both risk structures. There is no ceiling-to-floor transition, no
context-dependent degradation, and no differential between localized and
distributed structures.

This means the **hypothesis is currently untestable** with this
scenario/model/context-range combination.

---

## 2. Should Calibration Be Repeated?

### With the current setup: NO

Repeating the same calibration (gpt-4o-mini, v1.1 prompt, S1 scenario,
300–100k token range) would likely reproduce run008's ceiling result.
This would not yield new information.

### Under modified conditions: YES, if justified

Calibration should be repeated only if one or more experimental parameters
are changed in a scientifically justified manner.

---

## 3. Candidate Modifications (In Priority Order)

### 3A. Increase context range beyond 100k tokens

**Rationale**: The gpt-4o-mini context window is 128k tokens. The current
maximum tested level is 100k. If the ceiling extends to the model's context
limit, the scenario cannot produce the hypothesized degradation within this
model's capacity.

**Action**: Add levels at 110k and 120k. If still ceiling-level, the scenario
is insufficient for this model.

**Risk**: Minimal. Same model and prompt. Only the filler length changes.

### 3B. Use a more challenging scenario

**Rationale**: Scenario S1 may be too easy for gpt-4o-mini to detect. The
security-relevant keywords (`customer_records`, `CONFIDENTIAL`,
`external_storage`) are highly salient. A scenario with more subtle or
ambiguous security signals would be more likely to show context-dependent
degradation.

**Action**: Design and validate a Scenario S2 with less obvious security
indicators. This requires a new ablation cycle.

**Risk**: Significant time investment. Must not be manufactured to produce
desired results.

### 3C. Use a different or weaker model

**Rationale**: gpt-4o-mini may simply be too capable for this scenario at
these context lengths. A smaller model (e.g., gpt-3.5-turbo) or a model
with known long-context weaknesses might show the hypothesized effect.

**Action**: Re-run calibration with a different model. Document as a
separate experimental condition.

**Risk**: Changes the experimental setup. Must be disclosed as a different
model condition, not presented as a continuation of the same experiment.

### 3D. Make benign filler more security-adjacent

**Rationale**: The current benign filler (disk checks, schema validation,
cache syncs) is semantically distant from security-relevant actions. More
realistic filler — e.g., benign data operations that mention datasets,
permissions, or transfers — might create greater confusion.

**Action**: Modify `context/generator.py` to use security-adjacent
(but still benign) filler templates.

**Risk**: Must ensure filler remains genuinely benign and does not alter
ground truth.

---

## 4. Stopping Rules

### Calibration is informative when:
- At least one context level produces TPR < 1.0 (for positives)
- OR at least one context level produces FPR > 0 (for negatives)
- AND there is variation across levels

### Calibration is uninformative (ceiling) when:
- TPR = 1.0 and FPR = 0.0 at all tested levels
- No transition region is identifiable
- Increasing context to the model's limit does not change performance

### If ceiling persists:
- Document the ceiling result as a scientifically valid finding
- Report that the hypothesized degradation was not observed for this
  model/scenario/context combination
- Consider whether this is a meaningful negative result
- Do NOT manufacture degradation by weakening the prompt, providing
  contradictory instructions, or modifying the evaluator

---

## 5. Conditions for the Confirmatory 2×3 Experiment

The confirmatory experiment should proceed only when:

1. Calibration identifies at least three context levels spanning a
   transition from high to low detection performance (or provides
   a justified alternative selection)
2. The selected levels show measurable variation in at least one
   metric (TPR or FPR)
3. The prompt version and code are frozen
4. The acceptance criteria are documented before the experiment runs

**Current status**: Conditions NOT met. The 2×3 experiment should NOT proceed
with the current setup.

---

## 6. Recommended Next Step

**NEXT ACTION**: Determine whether extended context levels (110k, 120k) or
a different model can produce the variation needed to test the hypothesis.

If not, consider reporting the ceiling result as a valid finding: that
gpt-4o-mini with an explicit classification-enriched prompt can reliably
detect the S1 scenario even under 100k tokens of benign filler context.

This is itself a meaningful result, even though it does not confirm the
original hypothesis of context-dependent degradation.
