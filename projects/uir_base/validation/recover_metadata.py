"""Restore a missing historical metadata artifact ONLY from hash-verified bytes."""
import zipfile
from .common import ARCHIVE, OUT, ROOT, V3_SHA, load, sha, utc, write


def run():
    if sha(ARCHIVE) != V3_SHA: raise ValueError("FROZEN_ARCHIVE_CHANGED")
    relative = "docs/work_reports/uir_base/107_Astra_review/layout_migration_manifest.json"
    archived_relative = "docs/work_reports/uir_base/107_Astra_review/layout_migration_manifest.json"
    target = ROOT / relative
    if target.exists(): raise FileExistsError("Refuse to overwrite existing user metadata")
    with zipfile.ZipFile(ARCHIVE) as archive:
        import json
        manifest = json.loads(archive.read("archive_manifest.json"))
        expected = next(r["sha256"] for r in manifest["files"] if r["path"] == archived_relative)
        content = archive.read(archived_relative)
    import hashlib
    if hashlib.sha256(content).hexdigest() != expected: raise ValueError("ARCHIVED_METADATA_HASH_MISMATCH")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as handle: handle.write(content)
    write(OUT / "recovered_baseline_metadata.json", {"path": relative, "sha256": sha(target), "source_archive_sha256": V3_SHA,
          "reason": "baseline regression failed due to deleted historical metadata; exact bytes recovered, not recreated or test bypassed",
          "created_at_utc": utc(), "overwritten_existing_file": False})
    print(relative, sha(target))


if __name__ == "__main__": run()
