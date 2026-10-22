# UIR Law Manuscript Workspace

## Publication visibility policy

Legal domain manuscript drafts remain local and Git-ignored. Public benchmark code, schemas, and test suites are maintained under `projects/uir_law/evaluation/law200/`.

## Reproduction

Public users can verify source integrity and run evaluation unit tests:

```bash
bash projects/uir_law/reproduce.sh verify
bash projects/uir_law/reproduce.sh tests
```

`verify` confirms source portal integrity without third-party raw legal corpora dependencies.
