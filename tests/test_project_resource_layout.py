"""Ownership, link-free task creation and byte-preserving relocation checks."""
import hashlib
import json
from pathlib import Path

import pytest
from uir_common.paths import PROJECTS, create_task, project_root, relocated_relative, repo_root, task_root

ROOT = repo_root()


@pytest.mark.parametrize("project", sorted(PROJECTS))
def test_all_projects_have_the_same_resource_portal(project):
    root = project_root(project)
    assert all((root / part).is_dir() for part in ("docs", "resources", "results", "evaluation", "scripts", "paper"))
    assert not root.is_symlink()


@pytest.mark.parametrize("project", sorted(PROJECTS))
def test_new_task_never_overwrites(tmp_path, project):
    (tmp_path / "Cargo.toml").touch()
    (tmp_path / "projects").mkdir()
    path = create_task(project, "999_fixture", tmp_path)
    assert path == tmp_path / "projects" / project / "results/999_fixture"
    assert all((path / part).is_dir() for part in ("data", "reports", "figures", "resources", "logs", "manifests"))
    with pytest.raises(FileExistsError):
        create_task(project, "999_fixture", tmp_path)


@pytest.mark.parametrize("task", ["..", ".", "../private", "/tmp/escape", "task/sub", "", "bad\\path"])
def test_task_path_traversal_denied(task):
    with pytest.raises(ValueError):
        task_root("uir_base", task)


def test_unknown_project_denied():
    with pytest.raises(ValueError):
        task_root("unknown", "task")


@pytest.mark.parametrize("old,new", [
    ("docs/work_reports/uir_base/110_mdpi_rev/x.json", "docs/work_reports/uir_base/110_mdpi_rev/x.json"),
    ("archive/uir_base/results/uir_phase3b/x.jsonl", "projects/uir_base/results/uir_phase3b/x.jsonl"),
    ("docs/papers/_47_UIR/a.tex", "projects/uir_base/paper/_47_UIR/a.tex"),
    ("docs/formal/uir_base/UIR_SPEC.md", "projects/uir_base/docs/formal/UIR_SPEC.md"),
])
def test_recorded_paths_translate_without_aliases(old, new):
    assert str(relocated_relative(old)) == new


def test_live_law_paths_are_not_in_evaluation_sources():
    from projects.uir_law.evaluation.law200.common import DATA_DIR, RESULTS_DIR, TASK_ROOT
    from projects.uir_law.evaluation.law200.kr.law_go_kr import KR_DATA_DIR
    assert TASK_ROOT == ROOT / "projects/uir_law/results/law200"
    assert DATA_DIR == TASK_ROOT / "data"
    assert RESULTS_DIR == TASK_ROOT / "execution"
    assert KR_DATA_DIR == DATA_DIR / "kr"


@pytest.mark.parametrize("name", ["relocation_manifest.json", "law_resource_relocation.json", "flat_paper_relocation.json"])
def test_relocated_evidence_bytes_are_unchanged(name):
    manifest = ROOT / "projects/uir_base/results/114_project_layout_2026_10_21/manifests" / name
    if not manifest.is_file():
        pytest.skip("Private local migration receipt not distributed with source-only checkout")
    records = json.loads(manifest.read_text())["files"]
    assert records  # no empty scan success
    exception_file = manifest.parent / "work_reports_owner_exception.json"
    restored = {row["old_path"]: row for row in json.loads(exception_file.read_text())["files"]} if exception_file.exists() else {}
    for row in records:
        old, new = ROOT / row["old_path"], ROOT / row["new_path"]
        if row["old_path"] in restored:
            assert restored[row["old_path"]] == row  # exact owner-approved reverse move
            old, new = new, old
        assert not old.exists() and new.is_file() and not new.is_symlink()
        digest = hashlib.sha256()
        with new.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        assert digest.hexdigest() == row["sha256"], row["new_path"]


def test_work_reports_is_canonical_private_exception():
    import subprocess
    assert (ROOT / "docs/work_reports").is_dir()
    probe = subprocess.run(["git", "check-ignore", "--quiet", "docs/work_reports/uir_base/example.md"], cwd=ROOT)
    assert probe.returncode == 0
    # Root docs are not blanket-excluded.
    public = subprocess.run(["git", "check-ignore", "--quiet", "docs/architecture/example.md"], cwd=ROOT)
    assert public.returncode == 1
