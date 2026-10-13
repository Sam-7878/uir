"""R09 supplementary open AI judgment, no semantic truth labels."""
import argparse
import json
from uir_common.ollama_client import OllamaClient
from jsonschema import validate
from .common import OLD, OUT, check_frozen, jsonl, load, sha, utc, write

MODELS = {"AI_J1": ("qwen3:4b-instruct-2507-q4_K_M", "0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0"),
          "AI_J2": ("ministral-3:14b", "4760c35aeb9d9e9c6174c2492562c0b999e80a222804fd96b1915ab72bbcdcf7")}
SCHEMA = {"type": "object", "additionalProperties": False,
    "required": ["request_ambiguity", "epistemic_uncertainty", "candidate_status", "source_availability", "policy_status", "explanation"],
    "properties": {"request_ambiguity": {"type": "string", "enum": ["AMBIGUOUS", "UNAMBIGUOUS", "UNCERTAIN"]},
                   "epistemic_uncertainty": {"type": "string", "enum": ["LOW", "HIGH"]},
                   "candidate_status": {"type": "string", "enum": ["PRESENT", "ABSENT"]},
                   "source_availability": {"type": "string", "enum": ["PROVIDED", "UNAVAILABLE"]},
                   "policy_status": {"type": "string", "enum": ["ALLOW", "DENY", "APPROVAL_PENDING", "NOT_EVALUABLE"]},
                   "explanation": {"type": "string"}}}


def prepare():
    check_frozen()
    registry = {str(p.relative_to(OLD)): sha(p) for p in [*sorted((OLD / "ai_review_v2").glob("*raw_reviews.jsonl"))]}
    old = OLD.parent / "mdpi_revision_2026_10_11/ai_reviews/20261011T114157Z"
    registry.update({str(p): sha(p) for p in sorted(old.glob("*raw_reviews.jsonl"))})
    write(OUT / "frozen_review_registry.json", {"files": registry, "prior_reviews_replaced": False, "human_annotation_N": 0})
    write(OUT / "study_scope_authorization_record.json", {"decision": "B_AI_ONLY_NARROWED_CLAIMS",
          "trusted_record": "direct human reply in this conversation",
          "question_item_id": "request_user_input_async/call_454162e4421d42839a4f3acc7a8890e2/0",
          "human_reply_verbatim": "B — AI-only로 설계 변경, 주장 범위 축소",
          "human_semantic_annotation": False, "author_institution_signoff": False, "original_W08": "NOT_SATISFIED",
          "scope": "conversation research-design authorization only, not institutional/ethics approval or author signature"})
    prompts = [
        "RD900의 수치가 출처에 맞으면 보여 주세요.",
        "Compare RD901's performance and give a careful answer.",
        "RD902의 2025년 매출을 USD 단위로 알려 주세요.",
        "For RD903, verify revenue unless approval has been revoked.",
        "Show only verified facts for RD904 and do not fill missing values.",
        "RD905의 어느 해 수치인지 모르면 확인 질문을 하세요.",
        "For RD906, use the evidence but disregard denied write actions.",
        "Verify RD907's values if provenance and approval are both available.",
    ]
    packets = [{"case_id": f"OPEN-V3-{i:02d}", "raw_request": p, "candidate": None if i % 2 else {"entity": f"RD{900+i}", "period": "2025"},
                "source": None if i % 3 == 0 else "constructed source available but task interpretation is open",
                "policy": {"decision": ["ALLOW", "DENY", "REQUIRE_APPROVAL"][i % 3], "approved": False},
                "judgment_truth_labels": "NONE", "split": "NEW_OPEN_DEVELOPMENT_JUDGMENT_NOT_CONFIRMATORY"} for i, p in enumerate(prompts)]
    jsonl(OUT / "open_review_packets.jsonl", packets)
    write(OUT / "open_review_protocol.json", {"status": "FROZEN_BEFORE_OPEN_AI_JUDGMENT", "created_at_utc": utc(), "N_cases": 8,
          "models": MODELS, "schema": SCHEMA, "options": {"temperature": 0, "seed": 20261012, "num_ctx": 8192, "num_predict": 512, "num_gpu": 99},
          "thinking": False, "retries": 0, "source_sha256": sha(__file__), "packet_sha256": sha(OUT / "open_review_packets.jsonl"),
          "truth": "NONE; agreement and uncertainty only, no accuracy, no independent human semantic validation"})


def execute():
    protocol = load(OUT / "open_review_protocol.json")
    if sha(__file__) != protocol["source_sha256"] or sha(OUT / "open_review_packets.jsonl") != protocol["packet_sha256"]:
        raise ValueError("FROZEN_REVIEW_CHANGED")
    from .common import read
    client = OllamaClient("http://127.0.0.1:18747")
    installed = {r["name"]: r for r in client.get("/api/tags")["models"]}
    captures = []; inventory = {}
    for reviewer, (model, digest) in MODELS.items():
        if installed.get(model, {}).get("digest") != digest: raise ValueError("REVIEWER_ARTIFACT_CHANGED")
        for packet in read(OUT / "open_review_packets.jsonl"):
            request = {"model": model, "messages": [{"role": "system", "content":
                "Supplementary AI-only open judgment; no truth labels. Distinguish intrinsic request ambiguity from your uncertainty. "
                "candidate null is ABSENT; missing source is UNAVAILABLE, not automatically DENY. Policy comes only from supplied finite policy: "
                "DENY overrides; unapproved REQUIRE_APPROVAL is APPROVAL_PENDING. Never invent human gold. Return schema JSON."},
                {"role": "user", "content": json.dumps(packet, ensure_ascii=False)}], "format": SCHEMA, "stream": False, "think": False,
                "keep_alive": "10m", "options": protocol["options"]}
            response = client.post("/api/chat", request)
            label = None; error = None
            try:
                if response.get("done_reason") != "stop": raise ValueError("INCOMPLETE_RESPONSE")
                label = json.loads(response["message"]["content"]); validate(label, SCHEMA)
            except Exception as exc:
                error = type(exc).__name__ + ":" + str(exc); label = None
            captures.append({"case_id": packet["case_id"], "reviewer": reviewer, "model_digest": digest, "request": request,
                             "response": response, "label": label, "error": error, "evidence_kind": "AI_annotation"})
            print(reviewer, packet["case_id"], "valid=", label is not None, flush=True)
        inventory[reviewer] = {"artifact": installed[model], "allocation": client.get("/api/ps"), "show": client.post("/api/show", {"model": model})}
        client.post("/api/generate", {"model": model, "keep_alive": 0})
    jsonl(OUT / "open_review_raw.jsonl", captures)
    fields = [f for f in SCHEMA["properties"] if f != "explanation"]
    comparisons = {}
    unresolved = set()
    for field in fields:
        pairs = []
        for cid in {r["case_id"] for r in captures}:
            rows = [r for r in captures if r["case_id"] == cid]
            if any(r["label"] is None for r in rows): unresolved.add(cid); continue
            pair = [r["label"][field] for r in rows]; pairs.append(pair)
            if pair[0] != pair[1] or "UNCERTAIN" in pair or field == "epistemic_uncertainty" and "HIGH" in pair: unresolved.add(cid)
        n = len(pairs); agree = sum(x == y for x, y in pairs)
        labels = SCHEMA["properties"][field]["enum"]
        expected = sum(sum(x == l for x, y in pairs) * sum(y == l for x, y in pairs) for l in labels)/(n*n) if n else None
        kappa = (agree/n - expected)/(1-expected) if n and expected != 1 else None
        comparisons[field] = {"N_pairs": n, "N_agree": agree, "kappa": kappa, "accuracy": "NOT_MEASURED"}
    write(OUT / "open_review_summary.json", {"N_responses": len(captures), "N_valid": sum(r["label"] is not None for r in captures),
          "N_unresolved": len(unresolved), "comparisons": comparisons, "model_provenance": inventory,
          "truth_gold": "NONE", "human_validation": False, "raw_sha256": sha(OUT / "open_review_raw.jsonl"), "majority_adjudication": False})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--prepare", action="store_true"); parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.prepare: prepare()
    elif args.execute: execute()
    else: parser.error("Explicit --prepare or --execute")
