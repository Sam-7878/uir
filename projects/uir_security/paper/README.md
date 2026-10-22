# UIR Security (HETE-ZTA) Manuscript Workspace

## Publication visibility policy

Unsubmitted manuscript sources (HETE preprint and MDPI Electronics journal drafts), TeX templates, and compiled PDFs remain local and Git-ignored. Public supporting evidence, typed schemas, and reproducible evaluation bundles reside in `../results/HETE_UIR_ZTA_V3_2_FINAL_PACKAGE/` and `../../archive/uir_security/results/`.

## Reproduction

Public users can verify security module source integrity and test suites:

```bash
bash projects/uir_security/reproduce.sh verify
bash projects/uir_security/reproduce.sh tests
```

`verify` validates the Python evaluation portal and integrity checks. Full manuscript regeneration is local to the author's private review workspace.
