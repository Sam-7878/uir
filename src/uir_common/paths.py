"""Find a checkout independently of directory depth and legacy aliases."""
from pathlib import Path
import re

PROJECTS = {"uir_base", "uir_security", "uir_law"}

HISTORICAL_RESULTS = {
    "uir_base": {
        "uir", "uir_generalization", "uir_phase3", "uir_phase3b", "uir_phase3c",
        "uir_phase3d", "uir_phase4", "uir_phase4b", "uir_phase4c", "uir_phase4d",
        "uir_phase4e", "uir_phase4f", "uir_slm",
    },
    "uir_security": {
        "llm_security", "llm_security_v2", "llm_security_v3", "llm_security_v3_1",
        "llm_security_v3_1_preclosure", "llm_security_v3_prevalidation",
        "llm_security_v3_2_antigravity_incomplete_20260908",
        "llm_security_v3_2_interrupted_20260908",
    },
    "uir_law": set(),
}


def repo_root(start: str | Path = __file__) -> Path:
    path = Path(start).resolve()
    for candidate in (path, *path.parents):
        if (candidate / "Cargo.toml").is_file() and (candidate / "projects").is_dir():
            return candidate
    raise FileNotFoundError(f"UIR checkout not found above {path}")


def project_root(project: str, start: str | Path = __file__) -> Path:
    if project not in PROJECTS:
        raise ValueError(f"Unknown project: {project}")
    return repo_root(start) / "projects" / project


def task_root(project: str, task: str, start: str | Path = __file__) -> Path:
    """Single canonical place for a milestone's data, reports and figures."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", task) or task in {".", ".."}:
        raise ValueError("Invalid task ID")
    return project_root(project, start) / "results" / task


def create_task(project: str, task: str, start: str | Path = __file__) -> Path:
    """Create a fresh task; never silently reuse or overwrite historical results."""
    target = task_root(project, task, start)
    if any(p.is_symlink() for p in (target, *target.parents)):
        raise ValueError("Symbolic links are forbidden")
    target.mkdir(parents=True, exist_ok=False)
    for name in ("data", "reports", "figures", "resources", "logs", "manifests"):
        (target / name).mkdir()
    with (target / ".gitignore").open("x", encoding="utf-8") as handle:
        handle.write("# Local-only task evidence; explicit approved export required.\n*\n")
    return target


def relocated_relative(relative: str) -> Path:
    """Translate an OLD recorded path without editing frozen manifest bytes.

    No filesystem aliases, fallback copies, or implicit redirection of writes.
    Historical readers must explicitly opt in and still verify the original hash.
    """
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or "\\" in relative:
        raise ValueError("Unsafe recorded path")
    parts = path.parts
    law_prefix = ("projects", "uir_law", "evaluation", "law200")
    if len(parts) > 4 and parts[:4] == law_prefix and parts[4] in {"data", "results"}:
        kind = "data" if parts[4] == "data" else "execution"
        return Path("projects/uir_law/results/law200", kind, *parts[5:])
    # Historical results reside in archive/<project>/results/, active results in projects/<project>/results/
    if len(parts) >= 4 and parts[0] in {"archive", "projects"} and parts[1] in PROJECTS and parts[2] == "results":
        project = parts[1]
        task = parts[3]
        if task in HISTORICAL_RESULTS.get(project, set()):
            return Path("archive", project, "results", *parts[3:])
        else:
            return Path("projects", project, "results", *parts[3:])
    paper_map = {"_47_UIR": ("uir_base", "paper/_47_UIR"),
                 "_47_UIR_revision_next": ("uir_base", "results/110_mdpi_rev/manuscript_private/revision_next"),
                 "_47_1_UIR_ZTA": ("uir_security", "paper/_47_1_UIR_ZTA"),
                 "_47_2_UIR_Law": ("uir_law", "paper/_47_2_UIR_Law")}
    if len(parts) >= 3 and parts[:2] == ("docs", "papers") and parts[2] in paper_map:
        project, suffix = paper_map[parts[2]]
        return Path("projects", project, suffix, *parts[3:])
    if len(parts) >= 3 and parts[0] == "docs" and parts[1] in {"formal", "evaluation", "architecture"} and parts[2] in PROJECTS:
        return Path("projects", parts[2], "docs", parts[1], *parts[3:])
    return path


def recorded_path(root: Path, relative: str) -> Path:
    return Path(root) / relocated_relative(relative)
