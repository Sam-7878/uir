# Main merge conflict resolution and verification

Date: 2026-10-11 (Asia/Seoul)

## Scope and status

Resolved the three conflicts between main commit `c369cf3` and revision commit
`0bdc5c3`: README.md, pyproject.toml, and the relocated V3.2 closure campaign.
Related package, import, resource, test-fixture, and documentation paths were
updated for the canonical project layout. No merge commit or push was made.
The repository remains in the user's in-progress merge, ready for final review.

## Resolution decisions

- README uses the three-project architecture and bounded evidence claims, while
  preserving the latest single-source/no-symbolic-link policy and installation guide.
- Packaging includes both shared packages, `llm_trust` and `uir_common`, their
  dependencies, test/evaluation extras, and the UIR JSON Schema resource.
- Default pytest discovery includes the LAW200 tests alongside root base/security
  tests, so a normal `python -m pytest` checks all three projects.
- The closure campaign locates the repository by Cargo.toml and fingerprints
  `projects/uir_security/evaluation/llm_security_v3_2` and `src/llm_trust`.
  Missing or empty source trees still fail closed.
- The small checkout-only `src/evaluation` namespace reads the real project
  source directories for legacy imports. It creates no filesystem links or
  duplicate evaluation implementations. New code should use project-qualified
  canonical imports. This adapter is separate from the domain-neutral core.
- Phase 4D frozen inputs, registry, policy, and source paths now use their actual
  project/archive locations. The original compiler, reviewer, evaluator, policy
  YAML, captured model outputs, and evidence manifests were not rewritten.
- V3.1 fixture tests now require their real dataset and trusted manifest paths.
  No assertions were weakened to accommodate missing files.
- V2 regression datasets are generated in temporary test directories, and those
  behavioral tests use explicitly offline simulated fallback responses. They
  neither overwrite frozen datasets nor constitute new model experiments.
- The Phase 4D runtime leakage audit is read-only by default. Explicit CLI
  report generation retains its report-writing behavior, while tests and gate
  checks do not overwrite historical audit reports. Two historical reports
  touched by the initial test run were restored byte-for-byte from the merge
  index; regression tests cover both read-only and explicit-output behavior.
- The old link-creating migration script is retired and exits without mutation.
  Its historical implementation remains recoverable from Git commit `0bdc5c3`.

## Verification results

| Check | Outcome |
| --- | --- |
| Default Python regression suite, including LAW200 | 213 passed |
| Rust workspace, all features, offline | 62 passed |
| Editable imports outside repository | Both shared packages load from src |
| Regular wheel installation | Both shared packages and JSON Schema load |
| Shared llm_trust source preservation | 30/30 original file hashes match |
| Base reproduction integrity | 10 immutable inputs and evaluator pass |
| Security source portal | 139 Python source files present |
| Law source portal | 41 Python source files present |
| Existing AI review integrity/agreement replay | 120 cases, 240 valid responses pass |
| Python syntax compilation | PASS |
| Symbolic links in tracked merge tree | 0 |
| Conflict-marker and edited-source whitespace checks | PASS |
| Historical audit reports unchanged after final tests | PASS |

Commands used in the shared Ubuntu virtual environment:

```bash
source /mnt/d/_Work/goat_bank/.venv_cuda/bin/activate
python -m pip install --no-deps --no-build-isolation -e .
python -m pytest -q
cargo test --workspace --all-features --offline
bash projects/uir_base/reproduce.sh verify
bash projects/uir_security/reproduce.sh verify
bash projects/uir_law/reproduce.sh verify
python -m compileall -q src projects
```

The combined suite includes the previously missing-data-dependent Phase 4D
checks without exclusions. Incoming frozen inputs are now accessed at their
actual project paths. An initial diagnostic run had two old-path fixture failures
(175 passed, 2 failed); after correcting those paths and isolating V2 fixtures,
the final default run passed all 213 tests in 14.28 seconds, including two new
audit side-effect regressions. Historical audit reports remained unchanged.

AI verification ran against a temporary copy at
`/tmp/uir-main-merge-ai-GSdHB46E/review`, preserving the original review directory.
The verifier confirmed original source/code/output hashes, case coverage,
request reconstruction, schema validity, labels, and exact-rational agreement.
Its status remains `INTEGRITY_AND_AGREEMENT_REPLAY_PASS_NOT_SEMANTIC_VALIDATION`:
119 cases still require adjudication, and human validation remains incomplete.
This merge verification does not claim publication readiness or rerun benchmarks.

## Recovery and generated files

The obsolete untracked root `evaluation` directory contained Python caches and
three generated V2 regression dataset files, not canonical project sources.
It was moved recoverably to
`/tmp/uir-main-merge-old-layout-CnD55PZ3/evaluation` after validating its contents.
Canonical source/data locations were not deleted. Temporary storage may later
be cleared by the host.

Two untracked audit reports from the initial old-path diagnostic (timestamp
`2026-10-11T13:02:57.541894+00:00`, all four inputs missing) were moved from
`results/uir_base/uir_phase4d` to
`/tmp/uir-main-merge-obsolete-audit-FWiQbk`. Only their now-empty old result
directories were removed. These diagnostic outputs were not frozen evidence.

The wheel verification artifacts and generated build copy are outside the
repository at `/tmp/uir-main-merge-wheel-yNe6G0Ho`. No generated build source copy
or symbolic-link compatibility directory was left inside the repository.

## Handoff

Conflict resolutions and their related source changes are staged for review.
The final merge commit and any GitHub push remain user actions. After reviewing
the staged diff, finish the current merge with `git commit`; do not start a new
merge while this one is pending.

The three pre-existing untracked documents in
`docs/work_reports/uir_base/108_llm_trust_src_migration` remain untouched and
unstaged. They are not conflict entries or pending source changes.
