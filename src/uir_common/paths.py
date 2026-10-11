"""Find a checkout independently of directory depth and legacy aliases."""
from pathlib import Path


def repo_root(start: str | Path = __file__) -> Path:
    path = Path(start).resolve()
    for candidate in (path, *path.parents):
        if (candidate / "Cargo.toml").is_file() and (candidate / "projects").is_dir():
            return candidate
    raise FileNotFoundError(f"UIR checkout not found above {path}")


def project_root(project: str, start: str | Path = __file__) -> Path:
    if project not in {"uir_base", "uir_security", "uir_law"}:
        raise ValueError(f"Unknown project: {project}")
    return repo_root(start) / "projects" / project
