# Clean-Room Compilation Receipt: Stage 119 MDPI Manuscript

**Manuscript Title:** Policy-and-Evidence Intermediate Contracts for Generative-AI Software: Independent Interpreter Conformance and Query-Aware Grounding  
**Target Journal:** MDPI *Electronics*  
**Date of Build:** 2026-10-23 23:59:24 KST  
**Build Operator:** Automated Stage 119 Clean-Room Verification Agent  

---

## 1. System & Toolchain Environment

- **Host Operating System:** Windows 11 Enterprise (WSL2 Architecture)
- **Subsystem Guest OS:** Ubuntu 26.04.1 LTS (Linux Kernel 6.6.x x86_64)
- **TeX Distribution:** TeX Live 2025/Debian
- **PDF Engine:** pdfTeX 3.141592653-2.6-1.40.28 (TeX Live 2025/Debian)
- **BibTeX Engine:** BibTeX 0.99d (TeX Live 2025/Debian)
- **Python Runtime:** Python 3.14.4
- **LaTeX Class:** `Definitions/mdpi.cls` (Version: 18/06/2025 MDPI paper class)
- **Bibliography Style:** `Definitions/mdpi.bst`

---

## 2. Invocation Sequence & Exit Codes

```bash
cd projects/uir_base/paper/mdpi_electronics_119

# Step 1: Initial pass to generate auxiliary files and citation requests
pdflatex -interaction=nonstopmode main.tex   # Exit Code: 0

# Step 2: Resolve bibliographic database references
bibtex main                                # Exit Code: 0 (2 non-fatal field warnings)

# Step 3: Integrate generated .bbl bibliography
pdflatex -interaction=nonstopmode main.tex   # Exit Code: 0

# Step 4: Finalize cross-references, outlines, and LastPage counters
pdflatex -interaction=nonstopmode main.tex   # Exit Code: 0
```

---

## 3. Cryptographic Build Fingerprints

| Artifact Name | Relative Path | Byte Size | SHA-256 Digest |
|:---|:---|:---:|:---|
| Compiled Manuscript PDF | `paper/mdpi_electronics_119/main.pdf` | 275,391 bytes | `5c1925f5444d2ff1552f42dc4e364f4aebba41c974b6b82a15320df85c173729` |
| Primary LaTeX Source | `paper/mdpi_electronics_119/main.tex` | 48,670 bytes | `40452f1f8a7a0d0e7d6cfc451a4ea5bb180fb4edd829491b5ff1e28e5e678de3` |
| Curated Bibliography | `paper/mdpi_electronics_119/references.bib` | 13,010 bytes | `01378a396d4a0d1b46a514d88a6cb1d139e26eef27da27667c1c4942624785bf` |
| Compilation Transcript | `results/119_.../audit/compile_log_119.txt` | 44,220 bytes | `7cf02a3a1f11e03a985a5359a6fe40beac6d6a5cce0802c5c960307304191d9e` |

---

## 4. Diagnostics & Invariant Checks

- **Fatal TeX Errors:** 0
- **Undefined References:** 0
- **Undefined Citations:** 0
- **Fatal Overfull Margins (> 5 pt):** 0
- **Page Count:** Exactly 15 pages (A4 size: 595.276 x 841.89 pt)
- **PDF Version:** 1.7
- **Verification Status:** CLEAN_ROOM_BUILD_PASS
