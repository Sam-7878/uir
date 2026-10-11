"""Regression checks for the single, link-free llm_trust source location."""
from __future__ import annotations

import hashlib
import importlib.resources
import json
from pathlib import Path
import subprocess
import sys

import llm_trust
import pytest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "llm_trust"


def test_single_canonical_package_location():
    assert Path(llm_trust.__file__).resolve() == SOURCE / "__init__.py"
    legacy = ROOT / "llm_trust"
    assert not legacy.exists() and not legacy.is_symlink()


def test_source_tree_has_no_symbolic_links():
    assert not SOURCE.is_symlink()
    assert not SOURCE.parent.is_symlink()
    assert not [path for path in SOURCE.rglob("*") if path.is_symlink()]


def test_schema_is_a_packaged_resource():
    resource = importlib.resources.files("llm_trust.uir").joinpath("schema_v2.json")
    schema = json.loads(resource.read_text(encoding="utf-8"))
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    from llm_trust.uir.builder import SCHEMA_V2_PATH, UirV2Builder
    assert SCHEMA_V2_PATH.resolve() == SOURCE / "uir" / "schema_v2.json"
    assert UirV2Builder().validator.schema == schema


def test_installed_package_imports_outside_repository(tmp_path):
    # -I ignores PYTHONPATH and the working directory: editable installation
    # must resolve the real source package without a root directory alias.
    probe = subprocess.run(
        [sys.executable, "-I", "-c",
         "import llm_trust; from llm_trust import UirV2Builder; "
         "UirV2Builder(); print(llm_trust.__file__)"],
        cwd=tmp_path, capture_output=True, text=True, check=True, timeout=30,
    )
    assert Path(probe.stdout.strip()).resolve() == SOURCE / "__init__.py"


def test_both_shared_packages_import_outside_repository(tmp_path):
    probe = subprocess.run(
        [sys.executable, "-I", "-c",
         "import json, llm_trust, uir_common; "
         "print(json.dumps([llm_trust.__file__, uir_common.__file__]))"],
        cwd=tmp_path, capture_output=True, text=True, check=True, timeout=30,
    )
    paths = [Path(value).resolve() for value in json.loads(probe.stdout)]
    assert paths == [SOURCE / "__init__.py", ROOT / "src/uir_common/__init__.py"]


def test_legacy_import_namespace_uses_only_canonical_project_sources():
    import evaluation
    from evaluation.uir_phase4d import common
    from evaluation.llm_security_v3_2.schema import runtime_case
    assert Path(evaluation.__file__).resolve() == ROOT / "src/evaluation/__init__.py"
    assert set(evaluation.__path__) == {
        str(ROOT / "projects" / project / "evaluation")
        for project in ("uir_base", "uir_security", "uir_law")
    }
    assert Path(common.__file__).resolve() == ROOT / "projects/uir_base/evaluation/uir_phase4d/common.py"
    assert common.EVAL_DIR == Path(common.__file__).resolve().parent
    assert common.FROZEN_DIR == ROOT / "projects/uir_base/results/uir_phase4d/frozen_inputs"
    assert Path(runtime_case.__file__).resolve() == ROOT / "projects/uir_security/evaluation/llm_security_v3_2/schema/runtime_case.py"


def test_retired_migration_cannot_create_link_aliases(tmp_path):
    probe = subprocess.run(
        [sys.executable, str(ROOT / "scripts/migrate_project_layout.py")],
        cwd=tmp_path, capture_output=True, text=True, timeout=30,
    )
    assert probe.returncode != 0
    assert "retired" in probe.stderr.lower()
    assert not list(tmp_path.iterdir())


def test_campaign_hashes_cover_real_source_files():
    from projects.uir_security.evaluation.llm_security_v3_2.closure_campaign import source_hashes
    hashes = source_hashes()
    expected = {
        str(path.relative_to(ROOT))
        for folder in (SOURCE, ROOT / "projects/uir_security/evaluation/llm_security_v3_2")
        for path in folder.rglob("*.py")
    }
    assert expected and set(hashes) == expected
    assert "src/llm_trust/__init__.py" in hashes
    assert not any(path.startswith("llm_trust/") for path in hashes)
    for name, digest in hashes.items():
        assert digest == hashlib.sha256((ROOT / name).read_bytes()).hexdigest()


@pytest.mark.parametrize("missing_package", [False, True])
def test_campaign_fails_closed_for_incomplete_source_tree(tmp_path, monkeypatch, missing_package):
    from projects.uir_security.evaluation.llm_security_v3_2 import closure_campaign
    # Keep the evaluation root nonempty so the test exercises the package
    # root specifically, rather than an unrelated missing evaluation tree.
    evaluation = tmp_path / "projects/uir_security/evaluation/llm_security_v3_2"
    evaluation.mkdir(parents=True)
    (evaluation / "__init__.py").write_text("", encoding="utf-8")
    if not missing_package:
        (tmp_path / "src/llm_trust").mkdir(parents=True)
    monkeypatch.setattr(closure_campaign, "REPO", tmp_path)
    with pytest.raises(RuntimeError, match="missing or empty source tree"):
        closure_campaign.source_hashes()
