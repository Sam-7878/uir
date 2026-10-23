"""Explicit stage-bounded write-once evidence, independent of historical T paths."""
import json
from pathlib import Path

from ..policy import ROOT, RUN_PATTERN, safe_relative, sha, utc

PREFIX = Path("projects/uir_base/results/116_electronics_confirmatory_2026_10_23")


class RunStore:
    def __init__(self, directory, *, root=ROOT):
        self.root = Path(root).absolute()
        self.directory = Path(directory).absolute()
        relative = self.directory.relative_to(self.root / PREFIX)
        if len(relative.parts) != 1 or not RUN_PATTERN.fullmatch(relative.name):
            raise ValueError("EXPLICIT_FRESH_STAGE116_RUN_REQUIRED")
        self._no_links(self.directory)
        if self.directory.resolve() != self.directory:
            raise ValueError("NONCANONICAL_RUN")

    @staticmethod
    def _no_links(path):
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError("SYMLINK_EVIDENCE_ESCAPE")

    def create(self):
        self.directory.mkdir(parents=True, exist_ok=False)

    def path(self, relative):
        result = self.directory / safe_relative(relative)
        self._no_links(result)
        return result

    def write(self, relative, value):
        if (self.directory / "evidence_manifest.json").exists():
            raise FileExistsError("SEALED_RUN_IS_READ_ONLY")
        path = self.path(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not isinstance(value, (str, bytes)):
            value = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        with path.open("xb") as handle:
            handle.write(value.encode("utf-8") if isinstance(value, str) else value)

    def jsonl(self, relative, rows):
        self.write(relative, "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows))

    def seal(self):
        files = {}
        for path in sorted(self.directory.rglob("*")):
            self._no_links(path)
            if path.name == "evidence_manifest.json":
                raise FileExistsError("NO_RESEAL")
            if path.is_file():
                files[str(path.relative_to(self.directory))] = {"sha256": sha(path), "rights_class": "PRIVATE", "public_approved": False}
        if not files:
            raise ValueError("EMPTY_RUN")
        self.write("evidence_manifest.json", {"files": files, "created_at_utc": utc(), "self_hash": "EXCLUDED_DETACHED_MANIFEST",
                                              "scope": "BYTE_INTEGRITY_NOT_SCIENTIFIC_APPROVAL"})
        return sha(self.directory / "evidence_manifest.json")

    def verify(self):
        manifest = json.loads(self.path("evidence_manifest.json").read_text())
        if not manifest.get("files"):
            raise ValueError("EMPTY_RUN")
        for name, record in manifest["files"].items():
            path = self.path(name)
            if not path.is_file() or sha(path) != record["sha256"]:
                raise ValueError("EVIDENCE_MISSING_OR_MODIFIED")
        actual = set()
        for path in self.directory.rglob("*"):
            self._no_links(path)
            if path.is_file() and path != self.directory / "evidence_manifest.json":
                actual.add(str(path.relative_to(self.directory)))
        if actual != set(manifest["files"]):
            raise ValueError("UNDECLARED_EVIDENCE")
        return len(actual)
