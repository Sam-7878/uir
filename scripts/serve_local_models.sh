#!/usr/bin/env bash
set -euo pipefail
task_repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
export OLLAMA_HOST="127.0.0.1:18747"
export OLLAMA_MODELS="$task_repo/local_storage/ollama/models"
export OLLAMA_NO_CLOUD=1
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_MAX_LOADED_MODELS=1
export CUDA_VISIBLE_DEVICES="GPU-ab53069a-3217-ee09-80f8-748b5fdbd156"
exec /usr/local/bin/ollama serve
