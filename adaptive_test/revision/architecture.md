# Architecture Definition: Rejection Cascade

## Routing Policy
The system implements a sequential rejection cascade. A tool call is authorized only if it survives all previous layers of auditing.

### Flow Logic:
1. **Deterministic Layer**: 
   - If forbidden keywords are found $\rightarrow$ **BLOCK (FAIL)**
   - Otherwise $\rightarrow$ Proceed to Tier 2.
2. **Semantic Fast-Lane (Lightweight LLM)**:
   - If the model returns **FAIL** $\rightarrow$ **BLOCK (FAIL)**
   - If the model returns **PASS** or **UNSURE** $\rightarrow$ Proceed to Tier 3.
3. **Reasoning Secure-Lane (Deep LLM)**:
   - Final verdict is the output of the Deep LLM (**PASS** or **FAIL**).

## Key Distinction (The "Rejection" Rule)
The lightweight layer is used exclusively for **early rejection**. It cannot grant final authorization. This ensures that the security posture is anchored by the most capable model (Deep Auditor) for every potentially benign request, while reducing latency by filtering out obvious attacks early.

## Updated Paper Wording:
- **Abstract**: Replace "dynamically modulates the intensity" with "implements an early-rejection cascade."
- **Methodology**: Replace "escalating only when ambiguity is detected" with "escalating every request not rejected by the early stages."
- **Claim**: "The deep auditor evaluates every request not rejected by the deterministic and lightweight stages."
