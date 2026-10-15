# Experiment Design

## Research Question

How does accumulated benign agent context affect the detection of
distributed multi-step security risks by runtime risk detectors?

## Hypothesis

Increasing benign context will degrade detection performance, with a greater
degradation for distributed multi-step risks than for localized single-step
risks.

## Independent Variables

### Risk Structure

- Localized
- Distributed

### Benign Context

- Short: approximately 300 monitor-input tokens
- Medium: approximately 1,000 monitor-input tokens
- Long: approximately 2,500 monitor-input tokens

Actual token counts must be recorded for every sample.

## Context Manipulation

The security-relevant trajectory must remain constant across context levels.

Only benign filler preceding the risk trajectory should change.

Benign filler must not:

- contain target attack evidence
- alter ground-truth environment state
- reference the confidential dataset
- reference external data export
- introduce security-relevant actions

## Detector Input

The runtime detector receives only observable agent history:

- tool/action names
- action arguments
- observable tool outputs
- current action

The detector must not receive:

- environment state
- ground-truth labels
- evaluator output
- hidden state
- risk-structure labels

## Ground Truth

Ground truth is determined independently by the deterministic environment
evaluator.

The LLM detector does not determine ground truth.

## Decision Point

Primary detection measurement occurs at the completing action.

For distributed scenarios, this is the action at which the security invariant
becomes true.

Pre-completion alerts are recorded separately as anticipatory alerts and are
not treated as the primary latency measure.

## Experimental Matrix

| Risk Structure | Short | Medium | Long |
|---|---|---|---|
| Localized | L-S | L-M | L-L |
| Distributed | D-S | D-M | D-L |

Each cell contains:

- positive examples
- matched benign negative examples
- multiple independent seeds

## Primary Metrics

- True Positive Rate / Recall
- False Positive Rate
- Detection outcome per trajectory

## Primary Statistical Question

Does benign context have a different effect on detection depending on risk
structure?

Conceptual model:

Detection ~ RiskStructure * Context

The interaction between RiskStructure and Context is the primary inferential
quantity.

## Secondary Metrics

- Context token count
- Action count
- Decision latency
- Detector confidence
- Evidence spans
- Model/runtime information

## Reproducibility

Every experiment records:

- experiment configuration
- seed
- scenario
- risk structure
- context level
- actual token count
- action count
- model
- prompt version
- temperature
- detector output
- ground truth
- timestamp
