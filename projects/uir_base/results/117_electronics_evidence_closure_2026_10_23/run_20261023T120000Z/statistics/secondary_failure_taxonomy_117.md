# Stage 117 — Secondary SLM Factorial Failure Taxonomy

**Date:** 2026-10-23  
**Corpus:** Stage 116 V3 Factorial Corpus ($N=240$ cases, 8 conditions = 1,920 outcomes)  
**Evaluator:** Stage 117 Causal Attribution Engine

---

## 1. Executive Headline Diagnostic

$$\boxed{\text{SLM Selector Raw Exact Match} = 0 / 240 \quad (0.00\%)}$$
$$\boxed{\text{Shared Guard Rescued Template Completion} = 120 / 120 \quad (100.00\%)}$$
$$\boxed{\text{SLM Renderer Accepted Completion} = 76 / 120 \quad (63.33\%)}$$
$$\boxed{\text{SLM Renderer Unverified Omission} = 44 / 120 \quad (36.67\%)}$$

---

## 2. Selector Failure Analysis: Model Selection Accuracy $\neq$ System Acceptance

Under the `SLM selector` condition, Phi-3.5-mini was prompted to select fact IDs matching the user's specific request from a candidate catalog containing distractors:
- **Raw Exact Match Rate:** $0 / 240$ ($0\%$). In every single case, the model failed to output the exact requested fact ID subset.
- **Error Pattern:** The model exhibited high recall ($1.00$) but poor precision ($\approx 0.35 - 0.50$, Macro F1 $= 0.51587$). It systematically selected the target fact plus one or more distractor facts from other packages/entities.
- **The Rescuing Mechanism (Shared Guard):**
  The deterministic intermediate contract does not allow the raw model proposal to reach display unverified.
  Instead, the guard performs a set-intersection:
  $$\mathcal{F}_{\text{accepted}} = \mathcal{F}_{\text{proposed}} \cap \mathcal{F}_{\text{authorized\_and\_requested}}$$
  Because $\mathcal{F}_{\text{proposed}}$ contained the true target fact ($\text{Recall} = 1.0$), the guard removed all distractor fact IDs and retained the exact target fact.
  As a direct result, the deterministic `TEMPLATE` renderer produced $120 / 120$ complete, verified answers.

**Scientific Finding:** System-level correctness was entirely mediated by the deterministic intermediate guard, not by the generative model's fact-selection reasoning.

---

## 3. Renderer Failure Analysis: Utility Degradation under SLM Generation

Under the `SLM renderer` condition, the model was provided with the verified supported fact lines and instructed to output exact supported lines in JSON without omission or external prose:
- Out of 120 authorized ALLOW requests:
  - **76 cases (63.33%):** Model faithfully reproduced the supported line in JSON format, resulting in verified display acceptance.
  - **44 cases (36.67%):** Model produced empty JSON arrays (`{"lines": []}`) or omitted the line, resulting in an unverified/empty output.
- **Root Cause Categorization of 44 Omissions:**
  1. *Empty JSON Output (`lines: []`):* 44 cases ($100\%$ of omissions). The model failed to copy the supported line into the JSON schema despite clear prompt instructions.
  2. *Schema Violations / Parse Errors:* 0 cases. Output was valid JSON, but functionally vacuous.
  3. *Unauthorized Hallucinated Lines:* 0 cases. The guard's line-by-line byte-level matching prevented any fabricated text from being accepted.
- **Utility Cost:** Relying on generative SLM rendering introduced a $36.67\%$ utility penalty compared to deterministic template rendering, while offering zero additional safety gain.

---

## 4. Policy Enforcement (DENY Cases)

Across all 8 conditions ($120 \times 8 = 960$ DENY rows):
- **120 / 120 Unauthorized Requests Successfully Blocked:** In every single negative case, access was denied at the contract authority boundary.
- **Zero Information Leakage:** Neither template nor SLM renderer emitted any protected values.
