"""Evaluation package supporting dual-project architecture: uir_base and uir_security.

Provides backward-compatible module resolution while cleanly partitioning benchmarks and
evaluation tools into:
- evaluation.uir_base: Core UIR protocol, generalization, and phase evaluations.
- evaluation.uir_security: LLM security, adversarial benchmarking, and ZTA validation.
"""
from pathlib import Path

_pkg_dir = Path(__file__).resolve().parent
_base_dir = _pkg_dir / "uir_base"
_sec_dir = _pkg_dir / "uir_security"

# Extend package __path__ so that legacy imports like 'evaluation.llm_security_v3_2'
# or 'evaluation.uir_phase4d' continue to resolve seamlessly.
for _sub_dir in [_base_dir, _sec_dir]:
    if _sub_dir.exists():
        _sub_str = str(_sub_dir)
        if _sub_str not in __path__:
            __path__.append(_sub_str)
