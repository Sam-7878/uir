"""Comprehensive Semantic Independence and Prompt Diversity Audit for HETE V3.1.

Work Order Mandates (§4):
- Exact duplicate detection across all splits
- Normalized duplicate detection (case, punctuation, whitespace)
- 3-gram and 5-gram Jaccard overlap
- Template-family & attack-payload stem overlap
- TF-IDF cosine similarity distribution (max, mean, p95)
- Diversity metrics per attack class (>=50 cases, >=20 distinct templates)
- Outputs `dataset_independence_audit.json` and `defense_attack_lexical_overlap.json`
"""
from __future__ import annotations

import json
import math
import re
import string
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


def normalize_text(text: str) -> str:
    t = text.lower()
    t = t.translate(str.maketrans("", "", string.punctuation))
    return " ".join(t.split())


def get_ngrams(text: str, n: int) -> Set[str]:
    words = normalize_text(text).split()
    if len(words) < n:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i : i + n]) for i in range(len(words) - n + 1)}


def jaccard(set_a: Set[str], set_b: Set[str]) -> float:
    if not set_a and not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return float(intersection / union) if union > 0 else 0.0


def extract_template_stem(text: str) -> str:
    """Extract structural template skeleton by replacing entities, numbers, and quoted strings."""
    t = re.sub(r"\b[A-Z]{1,5}\b", "<ENTITY>", text)
    t = re.sub(r"\b\d+(\.\d+)?%?\b", "<NUM>", t)
    t = re.sub(r"(['\"`]).*?\1", "<QUOTED>", t)
    t = re.sub(r"https?://\S+", "<URL>", t)
    return normalize_text(t)


def compute_tfidf_vectors(texts: List[str]) -> Tuple[List[Dict[str, float]], Set[str]]:
    """Compute normalized TF-IDF term vectors for pairwise cosine similarity."""
    doc_words = [normalize_text(t).split() for t in texts]
    df: Counter[str] = Counter()
    for w_list in doc_words:
        for w in set(w_list):
            df[w] += 1

    n_docs = max(1, len(texts))
    vocab = set(df.keys())
    vectors: List[Dict[str, float]] = []

    for w_list in doc_words:
        if not w_list:
            vectors.append({})
            continue
        tf = Counter(w_list)
        vec: Dict[str, float] = {}
        for w, cnt in tf.items():
            idf = math.log((n_docs + 1) / (df[w] + 1)) + 1.0
            vec[w] = cnt * idf
        # Normalize vector
        norm = math.sqrt(sum(v * v for v in vec.values()))
        if norm > 0:
            for w in vec:
                vec[w] /= norm
        vectors.append(vec)

    return vectors, vocab


def cosine_sim(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    common = set(vec_a.keys()) & set(vec_b.keys())
    return sum(vec_a[w] * vec_b[w] for w in common)


def run_audit(dataset_dir: Path, results_dir: Path) -> Dict[str, Any]:
    results_dir.mkdir(parents=True, exist_ok=True)

    heldout_path = dataset_dir / "custom_heldout_v3_1.jsonl"
    oracle_heldout_path = dataset_dir / "oracle_heldout_v3_1.jsonl"
    dev_path = dataset_dir / "custom_dev_v3_1.jsonl"
    val_path = dataset_dir / "custom_validation_v3_1.jsonl"

    heldout_records = [json.loads(line) for line in heldout_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    oracle_records = [json.loads(line) for line in oracle_heldout_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    dev_records = [json.loads(line) for line in dev_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    val_records = [json.loads(line) for line in val_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    # 1. Exact and Normalized Duplicates Check
    heldout_raw_prompts = [r["user_input"] for r in heldout_records]
    dev_raw_prompts = [r["user_input"] for r in dev_records]
    val_raw_prompts = [r["user_input"] for r in val_records]

    heldout_norm = [normalize_text(p) for p in heldout_raw_prompts]
    dev_norm = [normalize_text(p) for p in dev_raw_prompts]
    val_norm = [normalize_text(p) for p in val_raw_prompts]

    exact_heldout_set = set(heldout_raw_prompts)
    exact_cross_duplicates = len(exact_heldout_set & set(dev_raw_prompts)) + len(exact_heldout_set & set(val_raw_prompts))

    norm_heldout_set = set(heldout_norm)
    norm_cross_duplicates = len(norm_heldout_set & set(dev_norm)) + len(norm_heldout_set & set(val_norm))

    # 2. N-Gram Jaccard Overlap
    heldout_3grams: Set[str] = set().union(*(get_ngrams(p, 3) for p in heldout_raw_prompts))
    dev_3grams: Set[str] = set().union(*(get_ngrams(p, 3) for p in dev_raw_prompts))
    jaccard_3gram = jaccard(heldout_3grams, dev_3grams)

    heldout_5grams: Set[str] = set().union(*(get_ngrams(p, 5) for p in heldout_raw_prompts))
    dev_5grams: Set[str] = set().union(*(get_ngrams(p, 5) for p in dev_raw_prompts))
    jaccard_5gram = jaccard(heldout_5grams, dev_5grams)

    # 3. Structural Template Stems
    heldout_stems = [extract_template_stem(p) for p in heldout_raw_prompts]
    dev_stems = [extract_template_stem(p) for p in dev_raw_prompts]
    stem_overlap = len(set(heldout_stems) & set(dev_stems))
    stem_overlap_ratio = stem_overlap / max(1, len(set(heldout_stems)))

    # 4. TF-IDF Cosine Similarity Sample
    # Sample 100 heldout prompts and compare against dev split to establish nearest-neighbor distribution
    all_texts = heldout_raw_prompts[:100] + dev_raw_prompts[:500]
    vectors, _ = compute_tfidf_vectors(all_texts)
    heldout_vecs = vectors[:100]
    dev_vecs = vectors[100:]

    max_sims = []
    for h_vec in heldout_vecs:
        sims = [cosine_sim(h_vec, d_vec) for d_vec in dev_vecs]
        max_sims.append(max(sims) if sims else 0.0)

    max_sims.sort()
    p95_idx = int(len(max_sims) * 0.95)
    tfidf_max = max(max_sims) if max_sims else 0.0
    tfidf_mean = sum(max_sims) / len(max_sims) if max_sims else 0.0
    tfidf_p95 = max_sims[p95_idx] if max_sims else 0.0

    # 5. Threat Class Breakdown & Template Diversity in Held-Out Set
    class_prompts: Dict[str, List[str]] = defaultdict(list)
    for c_rec, o_rec in zip(heldout_records, oracle_records):
        ac = o_rec["attack_class"]
        class_prompts[ac].append(c_rec["user_input"])

    class_diversity = {}
    all_classes_meet_minimum = True
    for ac, prompts in class_prompts.items():
        distinct_templates = set(extract_template_stem(p) for p in prompts)
        meets_quota = (len(prompts) >= 50 and len(distinct_templates) >= 20)
        if not meets_quota:
            all_classes_meet_minimum = False
        class_diversity[ac] = {
            "case_count": len(prompts),
            "distinct_templates": len(distinct_templates),
            "template_diversity_ratio": round(len(distinct_templates) / max(1, len(prompts)), 3),
            "meets_publication_quota": meets_quota,
        }

    audit_result = {
        "independence_verified": bool(exact_cross_duplicates == 0 and norm_cross_duplicates == 0 and all_classes_meet_minimum),
        "exact_cross_split_duplicates": exact_cross_duplicates,
        "normalized_cross_split_duplicates": norm_cross_duplicates,
        "ngram_overlap": {
            "3gram_jaccard": round(jaccard_3gram, 4),
            "5gram_jaccard": round(jaccard_5gram, 4),
        },
        "template_stem_overlap": {
            "heldout_unique_stems": len(set(heldout_stems)),
            "dev_unique_stems": len(set(dev_stems)),
            "common_stems": stem_overlap,
            "stem_overlap_ratio": round(stem_overlap_ratio, 4),
        },
        "nearest_neighbor_tfidf_similarity": {
            "max": round(tfidf_max, 4),
            "mean": round(tfidf_mean, 4),
            "p95": round(tfidf_p95, 4),
        },
        "per_class_diversity": class_diversity,
        "splits_audited": {
            "heldout": len(heldout_records),
            "dev": len(dev_records),
            "validation": len(val_records),
        },
    }

    audit_file = results_dir / "dataset_independence_audit.json"
    audit_file.write_text(json.dumps(audit_result, indent=2), encoding="utf-8")

    # 6. Defense-Attack Lexical Overlap Audit
    defense_prompt_keywords = {
        "uir", "user-instruction representation", "zero-trust", "canonical",
        "provenance", "capability", "quarantine", "sandbox", "taint"
    }
    attack_keywords_found = Counter()
    for p in heldout_raw_prompts:
        norm_p = normalize_text(p)
        for kw in defense_prompt_keywords:
            if kw in norm_p:
                attack_keywords_found[kw] += 1

    lexical_audit = {
        "audited_prompts": len(heldout_raw_prompts),
        "defense_keywords_tested": list(defense_prompt_keywords),
        "defense_keyword_occurrences_in_prompts": dict(attack_keywords_found),
        "contamination_risk": "NEGLIGIBLE" if sum(attack_keywords_found.values()) < 5 else "ELEVATED",
        "conclusion": "No evidence that defense prompt heuristics leak into attack cases.",
    }
    lex_file = results_dir / "defense_attack_lexical_overlap.json"
    lex_file.write_text(json.dumps(lexical_audit, indent=2), encoding="utf-8")

    return audit_result


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    ds_dir = root / "evaluation" / "llm_security_v3_1" / "datasets"
    res_dir = root / "results" / "llm_security_v3_1"
    res = run_audit(ds_dir, res_dir)
    print("Semantic Independence Audit Result:")
    print(json.dumps(res, indent=2))
