# HETE Multilingual Frontend Specification

**Version:** 3.0.0  
**Specification Reference:** Deterministic Frontend Compilation Envelope  
**Module Reference:** `llm_trust/frontends/` (`router.py`, `en.py`, `ko.py`, `base.py`)

---

## 1. Architectural Role and Non-Authority Invariant

The multilingual frontend acts as an initial syntactic normalization and semantic slot-filling compiler. It converts natural-language queries (English and Korean) into a typed syntactic draft (`ParsedDraft`).

> [!CRITICAL]
> **Strict Prohibition on Security Field Mutation:**  
> The multilingual frontend is completely **forbidden from writing or influencing security-authoritative fields**.  
> The parser **cannot** write or modify:
> - `principal_id`
> - `trust_level`
> - `allowed_capabilities`
> - `forbidden_capabilities`
> - `data_classification`
> - `approval_tokens`
> - `evidence_trust`
>
> All authority bindings are performed downstream by `UirV2Builder` and `create_trusted_security_context` using immutable authenticated session credentials and cryptographic evidence verification.

---

## 2. Pipeline Stages

```
Raw User Text
    │
    ▼
[1. InputGuard: Unicode NFKC Normalization & Control Char Filtering]
    │
    ▼
[2. LanguageRouter: Regex-based Hangul Detection]
    ├── (KO detected) ──► KoreanFrontend.parse()
    └── (EN default)  ──► EnglishFrontend.parse()
         │
         ▼
    ParsedDraft (Intent, Action, Entities, Temporal, Constraints)
         │  (Untrusted Semantics Only)
         ▼
[3. UirV2Builder: Ingests Authenticated Session State]
```

---

## 3. Linguistic Processing Rules

### 3.1 Normalization
- Unicode NFKC decomposition and recomposition collapses full-width characters, homoglyphs, and compatibility forms.
- Control characters ($0x00 - 0x1F$ except newline and tab) are stripped deterministically.

### 3.2 Language Routing
- Text containing Korean Hangul syllables or jamo (`[\uac00-\ud7a3\u1100-\u11ff\u3130-\u318f]`) is dispatched to `KoreanFrontend`.
- All other text defaults to `EnglishFrontend`.

### 3.3 Slot Filling and Entity Extraction
- **Entities:** Extracted via uppercase ticker pattern matching (`[A-Z]{1,5}`), Korean enterprise nomenclature matching, and 6-digit DART disclosure identifiers (`\b\d{6}\b`).
- **Temporal constraints:** Fiscal year and quarterly markers (`2023`, `FY2023`, `2023년`, `3분기`, `Q3`).
- **Metrics:** Balance sheet and income statement items (`revenue`, `net income`, `operating profit`, `매출액`, `영업이익`, `순이익`).

---

## 4. Failure Modes and Fallback Semantics

- **Unknown Intent:** If no recognized intent keyword matches, the parser emits `action = "LOOKUP"` with empty entities.
- **Parse Ambiguity:** Ambiguous terms are retained as literal parameters without capability assignment.
- **Fail-Closed Guarantee:** An unrecognized command cannot synthesize an administrative or executable action.
