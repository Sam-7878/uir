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


def test_campaign_hashes_cover_real_source_files():
    from evaluation.uir_security.llm_security_v3_2.closure_campaign import source_hashes
    hashes = source_hashes()
    expected = {
        str(path.relative_to(ROOT))
        for folder in (SOURCE, ROOT / "evaluation/uir_security/llm_security_v3_2")
        for path in folder.rglob("*.py")
    }
    assert expected and set(hashes) == expected
    assert "src/llm_trust/__init__.py" in hashes
    assert not any(path.startswith("llm_trust/") for path in hashes)
    for name, digest in hashes.items():
        assert digest == hashlib.sha256((ROOT / name).read_bytes()).hexdigest()


@pytest.mark.parametrize("missing_package", [False, True])
def test_campaign_fails_closed_for_incomplete_source_tree(tmp_path, monkeypatch, missing_package):
    from evaluation.uir_security.llm_security_v3_2 import closure_campaign
    # Keep the evaluation root nonempty so the test exercises the package
    # root specifically, rather than an unrelated missing evaluation tree.
    evaluation = tmp_path / "evaluation/uir_security/llm_security_v3_2"
    evaluation.mkdir(parents=True)
    (evaluation / "__init__.py").write_text("", encoding="utf-8")
    if not missing_package:
        (tmp_path / "src/llm_trust").mkdir(parents=True)
    monkeypatch.setattr(closure_campaign, "REPO", tmp_path)
    with pytest.raises(RuntimeError, match="missing or empty source tree"):
        closure_campaign.source_hashes()
