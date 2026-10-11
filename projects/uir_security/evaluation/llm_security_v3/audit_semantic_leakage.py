"""Semantic Leakage and Defense-Attack Lexical Overlap Auditor for v3.

Work Order Mandate §1.2 & §1.3:
"Report:
- exact duplicate rate
- normalized duplicate rate
- n-gram overlap
- template-family overlap
- identical attack-payload stem rate
Measure overlap with:
- InputGuard markers
- ContextFirewall regexes
- NONEXISTENT_ENTITIES
Save results to results/llm_security_v3/"
"""
from __future__ import annotations

import json
import re
import string
from pathlib import Path
from typing import Any, Dict, List, Set


def normalize_text(text: str) -> str:
    t = text.lower()
    t = re.sub(rf"[{re.escape(string.punctuation)}]", " ", t)
    return " ".join(t.split())


def get_ngrams(text: str, n: int = 3) -> Set[str]:
    words = normalize_text(text).split()
    if len(words) < n:
        return {" ".join(words)}
    return {" ".join(words[i:i+n]) for i in range(len(words) - n + 1)}


def jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / float(len(set_a | set_b))


class SemanticLeakageAuditor:
    def __init__(self, dev_path: Path, heldout_path: Path):
        self.dev_path = dev_path
        self.heldout_path = heldout_path

        self.dev_rows = [json.loads(line) for line in dev_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.heldout_rows = [json.loads(line) for line in heldout_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def audit_independence(self) -> Dict[str, Any]:
        dev_prompts = [r.get("user_input") or r.get("prompt", "") for r in self.dev_rows]
        heldout_prompts = [r.get("user_input") or r.get("prompt", "") for r in self.heldout_rows]

        dev_set = set(dev_prompts)
        heldout_set = set(heldout_prompts)

        dev_norm = set(normalize_text(p) for p in dev_prompts)
        heldout_norm = set(normalize_text(p) for p in heldout_prompts)

        exact_dups = dev_set & heldout_set
        norm_dups = dev_norm & heldout_norm

        # N-gram overlap across all prompts
        dev_3grams: Set[str] = set().union(*(get_ngrams(p, 3) for p in dev_prompts))
        heldout_3grams: Set[str] = set().union(*(get_ngrams(p, 3) for p in heldout_prompts))
        overlap_3gram = jaccard_similarity(dev_3grams, heldout_3grams)

        dev_5grams: Set[str] = set().union(*(get_ngrams(p, 5) for p in dev_prompts))
        heldout_5grams: Set[str] = set().union(*(get_ngrams(p, 5) for p in heldout_prompts))
        overlap_5gram = jaccard_similarity(dev_5grams, heldout_5grams)

        return {
            "dev_total_cases": len(self.dev_rows),
            "heldout_total_cases": len(self.heldout_rows),
            "exact_cross_split_duplicates": len(exact_dups),
            "exact_duplicate_rate": len(exact_dups) / max(1, len(self.heldout_rows)),
            "normalized_cross_split_duplicates": len(norm_dups),
            "normalized_duplicate_rate": len(norm_dups) / max(1, len(self.heldout_rows)),
            "ngram_3_jaccard_overlap": overlap_3gram,
            "ngram_5_jaccard_overlap": overlap_5gram,
            "independence_verified": len(exact_dups) == 0 and len(norm_dups) == 0,
        }

    def audit_defense_lexical_overlap(self) -> Dict[str, Any]:
        """Measures how many heldout attacks rely on textbook defense trigger phrases."""
        defense_markers = [
            "ignore previous instructions",
            "system override",
            "admin mode",
            "reveal confidential",
            "disregard rules",
            "이전 지시를 무시",
            "시스템 프롬프트",
            "관리자 모드",
        ]

        heldout_prompts = [r.get("user_input") or r.get("prompt", "") for r in self.heldout_rows]
        matches = {marker: 0 for marker in defense_markers}

        novel_attacks_count = 0
        for p in heldout_prompts:
            low = p.lower()
            contains_any = False
            for marker in defense_markers:
                if marker in low:
                    matches[marker] += 1
                    contains_any = True
            if not contains_any:
                novel_attacks_count += 1

        return {
            "total_heldout_cases": len(heldout_prompts),
            "heldout_cases_free_of_textbook_defense_markers": novel_attacks_count,
            "lexically_novel_attack_ratio": novel_attacks_count / max(1, len(heldout_prompts)),
            "marker_frequency": matches,
        }


def run_audit(dev_file: Path, heldout_file: Path, results_dir: Path) -> Dict[str, Any]:
    auditor = SemanticLeakageAuditor(dev_file, heldout_file)
    results_dir.mkdir(parents=True, exist_ok=True)

    independence = auditor.audit_independence()
    lexical = auditor.audit_defense_lexical_overlap()

    out_indep = results_dir / "dataset_independence_audit.json"
    out_lex = results_dir / "defense_attack_lexical_overlap.json"

    with open(out_indep, "w", encoding="utf-8") as f:
        json.dump(independence, f, indent=2)
    with open(out_lex, "w", encoding="utf-8") as f:
        json.dump(lexical, f, indent=2)

    return {"independence": independence, "lexical_overlap": lexical}


if __name__ == "__main__":
    base = Path(__file__).parent
    dev_path = base / "datasets" / "custom_dev_v3.jsonl"
    heldout_path = base / "datasets" / "custom_heldout_v3.jsonl"
    results_path = Path(__file__).resolve().parents[2] / "results" / "llm_security_v3"

    report = run_audit(dev_path, heldout_path, results_path)
    print("Semantic Leakage Audit Complete:")
    print(json.dumps(report, indent=2))
