# Full repository test repair history

The first `python -m pytest tests -q` attempt stopped during collection because
`tests/uir_phase4d/test_runtime_run.py` referenced the existing
`build_internal_request` function without importing it. The test module now
imports the function from `evaluation.uir_phase4d.pipelines`.

The next run collected all tests and produced one failure:
`tests/test_security_benchmark_v2.py::test_resume_rejects_a_changed_case`.
The V2 resume loader reported a fallback-model mismatch before checking the
changed case fingerprint, masking the expected data-integrity rejection. Its
checks were reordered so case fingerprints are verified before model metadata.
This does not make fallback evidence admissible: an unchanged fallback record
still fails the subsequent model/failure checks.

Both repairs are outside the V3.2 frozen evaluated-source set. The final run
passed 130 tests. Its exact pytest output is in `full_python_tests.txt`; the
security-focused suite separately passed 116 tests in `regression_tests.txt`.
