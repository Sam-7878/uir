# HETE UIR-ZTA V3.2: Complete Reproduction Guide

## 1. Environment Requirements & Prerequisites

The evaluation runs on Windows 11 with WSL2 (Ubuntu 24.04 LTS) utilizing an NVIDIA GPU for high-throughput live local model inference.

### Hardware Specifications
- **GPU**: NVIDIA GeForce RTX 4070 Laptop GPU (8GB GDDR6 VRAM) or equivalent.
- **RAM**: 16 GB+ system memory.
- **Storage**: ~20 GB free space for model weights and evaluation records.

### Software Stack
- **Python**: 3.11+ (Windows native or WSL2).
- **Ollama**: Official Linux native service installed inside WSL2 with CUDA 13.2 support (`/usr/lib/wsl/lib/libcuda.so.1`).
- **LaTeX**: TeX Live with `pdflatex` and `bibtex` inside WSL2.

---

## 2. Setting Up Ollama GPU Acceleration in WSL2

1. **Install Official Ollama in WSL2**:
   ```bash
   wsl -u root bash -c "curl -fsSL https://ollama.com/install.sh | sh"
   ```
2. **Verify GPU Offload**:
   ```bash
   wsl -u root systemctl restart ollama
   wsl nvidia-smi
   ```
3. **Pull Evaluated Model Weights**:
   ```bash
   wsl ollama pull qwen2.5:7b
   wsl ollama pull phi3.5:latest
   ```
4. **Confirm Endpoint Connectivity**:
   ```powershell
   Invoke-RestMethod -Uri http://127.0.0.1:11434/api/tags
   ```

---

## 3. Running Unit Tests

Execute the comprehensive 46-test unit suite covering OutputGuard, Mock Agency, Resource Tracking, Mutation Engine, and McNemar Statistics:

```powershell
cd d:\_Work\goat_bank\uir
python -m pytest tests/security_v3_2/ -v
```
*Expected result: 46 passed in < 1.0s.*

---

## 4. Executing the Authoritative Publication Campaign

Run the 10-phase campaign runner:

```powershell
python -u evaluation/llm_security_v3_2/run_publication_campaign_v3_2.py --qwen qwen2.5:7b --phi phi3.5:latest --endpoint http://127.0.0.1:11434
```

### Campaign Execution Workflow:
- **Phase 1**: Generates and freezes stratified $N=240$ evaluation cases to `results/llm_security_v3_2/datasets/`.
- **Phase 2**: Evaluates all 6 systems (Vanilla SLM, Naive RAG, Spotlighting, Progent, CaMeL, HETE) on Qwen2.5-7B.
- **Phase 3**: Analyzes specialized metrics (exfiltration egress, mock tool agency, dynamic token budgeting).
- **Phase 4**: Computes exact two-sided binomial McNemar tests with Holm-Bonferroni correction.
- **Phase 5**: Evaluates cross-model generalization on Phi-3.5 across the exact same 240 cases.
- **Phase 6**: Evaluates full-size 9-configuration ablation matrix ($9 \times 240$ cases).
- **Phase 7**: Runs genuine 14-operator adaptive search (30 seeds, budget $B=20$).
- **Phase 8**: Evaluates AgentDojo-inspired micro-suite ($N=5$).
- **Phase 9**: Generates containment funnels and path-specific latency benchmarks.
- **Phase 10**: Hashes all raw JSONLs, summaries, and configs into `ARTIFACT_MANIFEST.json`.

---

## 5. Running the Independent Scientific Validator

Run the strict auditor to verify raw data integrity, zero fallback, dataset stratification, and metric parity:

```powershell
python evaluation/llm_security_v3_2/validate_v3_2_results.py --strict --output-json results/llm_security_v3_2/publication_evidence_validation.json
```
*Expected result: All 10 scientific validity audits return `[✓] PASS` with zero violations.*

---

## 6. Compiling the LaTeX Manuscript

Compile the camera-ready 22-page paper with synchronized empirical tables:

```powershell
wsl bash -c "cd /mnt/d/_Work/goat_bank/uir/docs/papers/_47_1_UIR_for_ZTA && pdflatex _47.1_UIR_ZTA.tex && bibtex _47.1_UIR_ZTA && pdflatex _47.1_UIR_ZTA.tex && pdflatex _47.1_UIR_ZTA.tex"
```
*Expected result: Produces `_47.1_UIR_ZTA.pdf` with zero missing citations or unresolved references.*
