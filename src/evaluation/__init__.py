"""Checkout-only legacy imports over the single canonical project source trees.

New code should use projects.<project>.evaluation. This namespace creates no
filesystem aliases or source copies and never imports project code into core.
"""
from importlib.machinery import ModuleSpec
from pathlib import Path
import sys
from types import ModuleType


_root = next(
    (parent for parent in Path(__file__).resolve().parents
     if (parent / "Cargo.toml").is_file() and (parent / "projects").is_dir()),
    None,
)
if _root is None:
    raise ImportError("Legacy evaluation imports require a UIR research checkout")

__path__ = [
    str(_root / "projects" / project / "evaluation")
    for project in ("uir_base", "uir_security", "uir_law")
    if (_root / "projects" / project / "evaluation").is_dir()
]
if not __path__:
    raise ImportError("No canonical project evaluation sources found")

# Older project-qualified imports are namespace names, not filesystem aliases.
# The real source directories remain projects/<project>/evaluation exclusively.
for _project in ("uir_base", "uir_security", "uir_law"):
    _directory = _root / "projects" / _project / "evaluation"
    if _directory.is_dir():
        _name = f"{__name__}.{_project}"
        _namespace = ModuleType(_name)
        _namespace.__file__ = str(_directory / "__init__.py")
        _namespace.__package__ = _name
        _namespace.__path__ = [str(_directory)]
        _namespace.__spec__ = ModuleSpec(_name, loader=None, is_package=True)
        _namespace.__spec__.submodule_search_locations = _namespace.__path__
        sys.modules[_name] = _namespace
        setattr(sys.modules[__name__], _project, _namespace)
