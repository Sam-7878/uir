#!/usr/bin/env python3
"""JSON stdin/stdout bridge used by Rust LocalSlmRenderer."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from ollama_client import OllamaClient


def main() -> None:
    request = json.load(sys.stdin); config_path = Path(__file__).parent / "model_config" / "phi35_ollama.json"; client = OllamaClient(config_path); options = {"temperature": request["temperature"], "top_p": request["top_p"], "top_k": request["top_k"], "max_new_tokens": request["max_new_tokens"], "repetition_penalty": request["repetition_penalty"], "seed": request["seed"]}
    system = "Render only the supplied verified facts. Return strict JSON with answer and claims. Never add a claim."
    prompt = "UIR:\n" + json.dumps(request["uir"], ensure_ascii=False, sort_keys=True) + "\nVERIFIED_FACTS:\n" + json.dumps(request["facts"], ensure_ascii=False, sort_keys=True) + "\nReturn {\"answer\":string,\"claims\":[{\"claim_type\":string,\"key\":string,\"value\":string,\"provenance\":string|null}]}"
    result = client.generate(prompt, system, options)
    try:
        payload = json.loads(result.text)
    except json.JSONDecodeError as error:
        raise SystemExit(f"SLM_FORMAT_ERROR:{error.msg}") from error
    facts = request["facts"] if isinstance(request["facts"], list) else request["facts"].get("0", [])
    allowed_types = {fact["claim_type"] for fact in facts}
    converted = []
    for claim in payload.get("claims", []):
        if not isinstance(claim, dict) or claim.get("claim_type") not in allowed_types:
            continue
        converted.append({"claim_type": str(claim["claim_type"]), "key": str(claim.get("key", "")), "value": str(claim.get("value", "")), "provenance": claim.get("provenance")})
    json.dump({"text": str(payload.get("answer", "")), "claims": converted}, sys.stdout, ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__": main()
