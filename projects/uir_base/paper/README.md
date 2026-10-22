# UIR Base Manuscript Workspace

## Publication visibility policy

At the author's request, unsubmitted manuscript sources (`.tex`, `.bib`, `.cls`, `.sty`) and compiled PDFs remain local and are excluded from Git tracking (`paper/current/` and legacy drafts). Public supporting evidence, execution contracts, and independent numerical verification reside in `../results/mdpi_revision_2026_10_11/` and `../../archive/uir_base/results/`.

## Reproduction

Public checkout users can verify recorded integrity and regenerate audit tables without local manuscript dependencies:

```bash
bash projects/uir_base/reproduce.sh verify
bash projects/uir_base/reproduce.sh tables
```

`verify` checks immutable source inputs and evaluator hashes without requiring raw proprietary data or GPU access. Unsubmitted manuscript generation requires the author's private local environment and inputs.
