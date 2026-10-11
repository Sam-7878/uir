"""Install the approved local models and capture operational smoke-test evidence.

This does NOT generate human annotations or validate judge accuracy. Model weights
remain in ignored local_storage; public evidence contains metadata and test outputs.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import threading

from uir_common.ollama_client import OllamaClient, sha256_text
from uir_common.paths import repo_root


MODELS = {
    "phi3.5:latest": {"role": "answer_generator", "source": "https://huggingface.co/microsoft/Phi-3.5-mini-instruct", "license": "MIT"},
    "qwen3:4b-instruct-2507-q4_K_M": {"role": "AI_J1", "source": "https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507", "license": "Apache-2.0"},
    "ministral-3:14b": {"role": "AI_J2", "source": "https://huggingface.co/mistralai/Ministral-3-14B-Instruct-2512", "license": "Apache-2.0"},
}
GPU_UUID = "GPU-ab53069a-3217-ee09-80f8-748b5fdbd156"
PRINT_LOCK = threading.Lock()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def install(endpoint: str, model: str) -> str:
    client = OllamaClient(endpoint)
    last = {}
    def progress(event):
        status = event.get("status", "")
        digest = event.get("digest", "")
        total = event.get("total", 0)
        if total:
            bucket = min(10, int(event.get("completed", 0) / total * 10))
            if last.get(digest) == bucket:
                return
            last[digest] = bucket
            status = f"{status}: {bucket * 10}%"
        elif last.get("status") == status:
            return
        else:
            last["status"] = status
        with PRINT_LOCK:
            print(f"{model}: {status}", flush=True)
    try:
        client.pull(model, progress)
        return model
    finally:
        client.close()


def gpu_snapshot() -> str:
    result = subprocess.run(["nvidia-smi", "--query-gpu=name,uuid,memory.total,memory.used", "--format=csv,noheader"],
                            check=True, text=True, capture_output=True, timeout=30)
    return result.stdout.strip()


def smoke(client: OllamaClient, model: str, out: Path) -> dict:
    probes = [
        ("english_instruction", "Reply with exactly READY.", None, "READY"),
        ("korean_arithmetic", "7 더하기 5의 결과를 계산하세요. 숫자만 출력하세요.", None, "12"),
        ("structured_output", 'Return only a JSON object with status set to READY.',
         {"type": "object", "properties": {"status": {"type": "string", "enum": ["READY"]}},
          "required": ["status"], "additionalProperties": False}, {"status": "READY"}),
    ]
    records = []
    for name, prompt, schema, expected in probes:
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False,
                   "keep_alive": "10m", "options": {"num_ctx": 8192, "num_predict": 64, "temperature": 0, "seed": 20261011}}
        # The selected Qwen Instruct-2507 model is non-thinking by construction.
        if schema:
            payload["format"] = schema
        response = client.post("/api/chat", payload, timeout=300)
        raw = response.get("message", {}).get("content", "")
        try:
            actual = json.loads(raw) if schema else raw.strip().rstrip(".")
        except (ValueError, TypeError):
            actual = None
        passed = response.get("done") is True and response.get("done_reason") == "stop" and actual == expected
        record = {"probe": name, "request": payload, "response": response, "raw_content_sha256": sha256_text(raw),
                  "passed": passed, "scope": "operational_smoke_only_not_benchmark_or_judge_accuracy"}
        records.append(record)
        print(f"{model}: {name} {'PASS' if passed else 'FAIL'}", flush=True)
    loaded = [r for r in client.get("/api/ps").get("models", []) if r.get("name") == model or r.get("model") == model]
    write_json(out / (model.replace(":", "_") + "_smoke.json"), {"records": records, "loaded_models": loaded,
               "nvidia_smi": gpu_snapshot()})
    gpu_used = any(r.get("size_vram", 0) > 0 for r in loaded)
    # Unload only the model loaded by this smoke test, not another service/model.
    client.post("/api/generate", {"model": model, "keep_alive": 0, "stream": False})
    return {"probe_count": len(records), "probe_passed": sum(r["passed"] for r in records),
            "all_probes_passed": all(r["passed"] for r in records), "gpu_memory_allocated": gpu_used,
            "loaded_models": loaded}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default="http://127.0.0.1:18747")
    parser.add_argument("--models", nargs="+", choices=list(MODELS), default=list(MODELS))
    args = parser.parse_args()
    root = repo_root()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = root / "projects/uir_base/results/mdpi_revision_2026_10_11/local_models" / stamp
    out.mkdir(parents=True, exist_ok=False)
    client = OllamaClient(args.endpoint)
    manifest = {"created_at_utc": stamp, "endpoint": client.endpoint, "scope": "installation_and_operational_smoke",
                "models": {}, "status": "RUNNING", "gpu_uuid_expected_on_this_host": GPU_UUID,
                "installation_script_sha256": sha256_text(Path(__file__).read_text(encoding="utf-8")),
                "human_review_complete": False, "W08_human_requirement_satisfied": False,
                "AI_review_completed": False, "weights_git_tracked": False,
                "server_version": client.get("/api/version"), "gpu_before": gpu_snapshot()}
    write_json(out / "installation_manifest.json", manifest)
    installed = {r["name"]: r for r in client.get("/api/tags").get("models", [])}
    to_pull = [m for m in args.models if m not in installed]
    errors = []
    # Downloads may overlap, but inference below is deliberately sequential.
    with ThreadPoolExecutor(max_workers=2) as pool:
        pending = {pool.submit(install, args.endpoint, m): m for m in to_pull}
        for future in as_completed(pending):
            model = pending[future]
            try:
                future.result()
            except Exception as exc:
                errors.append({"model": model, "phase": "pull", "error": str(exc)})
    installed = {r["name"]: r for r in client.get("/api/tags").get("models", [])}
    for model in args.models:
        metadata = installed.get(model)
        if metadata is None:
            continue
        info = client.post("/api/show", {"model": model})
        write_json(out / (model.replace(":", "_") + "_show.json"), info)
        entry = {**MODELS[model], **metadata, "template_sha256": sha256_text(info.get("template", "")),
                 "license_text_sha256": sha256_text(info.get("license", "")),
                 "gguf_identity": {k: v for k, v in info.get("model_info", {}).items() if k.startswith("general.")}}
        try:
            entry["smoke"] = smoke(client, model, out)
        except Exception as exc:
            errors.append({"model": model, "phase": "smoke", "error": str(exc)})
        manifest["models"][model] = entry
        manifest["errors"] = errors
        write_json(out / "installation_manifest.json", manifest)
    complete = (len(manifest["models"]) == len(args.models) and not errors and
                all(m.get("smoke", {}).get("all_probes_passed") and m["smoke"]["gpu_memory_allocated"]
                    for m in manifest["models"].values()))
    operational = (len(manifest["models"]) == len(args.models) and not errors and
                   all(m.get("smoke", {}).get("gpu_memory_allocated") for m in manifest["models"].values()))
    manifest["strict_probe_warning_models"] = [name for name, m in manifest["models"].items()
                                               if not m.get("smoke", {}).get("all_probes_passed")]
    manifest["status"] = ("INSTALLED_GPU_SMOKE_VERIFIED" if complete else
                          "INSTALLED_GPU_VERIFIED_WITH_SMOKE_PROBE_WARNINGS" if operational else
                          "INCOMPLETE_OR_SMOKE_FAILURE")
    manifest["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    write_json(out / "installation_manifest.json", manifest)
    client.close()
    print(f"{manifest['status']}: {out}", flush=True)
    return 0 if operational else 1


if __name__ == "__main__":
    sys.exit(main())
