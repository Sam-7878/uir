#!/usr/bin/env bash
set -euo pipefail
uir_repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$uir_repo_dir"
exec "${UIR_PYTHON:-python}" scripts/reproduce_project.py uir_base "${1:-verify}"
