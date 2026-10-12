"""Explicitly install the user-selected Qwen3-1.7B generator, not a reviewer."""
from datetime import datetime, timezone
import hashlib
import json
from projects.uir_base.scripts import revision_audit as a
from projects.uir_base.scripts.next_release import DEFAULT
from uir_common.ollama_client import OllamaClient

MODEL = "qwen3:1.7b-q4_K_M"


def main():
    target = DEFAULT / "qwen3_1_7b_install_manifest.json"
    if target.exists():
        raise FileExistsError("Preserve existing installation provenance")
    client = OllamaClient("http://127.0.0.1:18747")
    installed = {r["name"]: r for r in client.get("/api/tags")["models"]}
    if MODEL not in installed:
        last = [None, -1]
        def progress(event):
            completed = int(event.get("completed", 0)); total = int(event.get("total", 1)) or 1
            bucket = int(10 * completed / total)
            state = event.get("status")
            if state != last[0] or bucket != last[1]:
                print(json.dumps({"status": state, "completed": completed, "total": total}), flush=True)
                last[:] = [state, bucket]
        client.pull(MODEL, progress)
    installed = {r["name"]: r for r in client.get("/api/tags")["models"]}
    artifact = installed[MODEL]
    info = client.post("/api/show", {"model": MODEL})
    if info["details"]["quantization_level"] != "Q4_K_M":
        raise ValueError("Unexpected quantization artifact")
    a.write_json(target, {"status": "INSTALLED_NOT_HOLDOUT_EXECUTED", "installed_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifact": artifact, "model_info": info["model_info"], "capabilities": info.get("capabilities"),
        "template_sha256": hashlib.sha256(info.get("template", "").encode()).hexdigest(),
        "role": "new_generator_comparison_NOT_independent_reviewer", "upstream": "https://huggingface.co/Qwen/Qwen3-1.7B",
        "distribution": "https://ollama.com/library/qwen3:1.7b-q4_K_M", "license": "Apache-2.0 (upstream model card)",
        "authorization": "User selected Qwen3-1.7B instead of Qwen2.5-7B in this task on 2026-10-12 KST",
        "historical_qwen_2_5_7b_evidence": "preserved, not overwritten or relabeled",
        "holdout_protocol": "must freeze a new prospective version with this artifact digest before any holdout calls",
        "comparability": "Phi-3.5 ~3.8B versus Qwen3 1.7B; NOT parameter-matched or a priori ability-matched",
        "thinking_policy": "prospective non-thinking primary arm; do not silently mix reasoning budgets",
        "old_generator_protocol": "FROZEN_NOT_EXECUTED; superseded only by explicit new version",
        "newer_means_better": "NOT_ESTABLISHED", "source_sha256": a.digest(__file__)})
    print(json.dumps({"model": MODEL, "digest": artifact["digest"], "status": "INSTALLED"}), flush=True)
    client.close()


if __name__ == "__main__":
    main()
