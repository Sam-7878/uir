"""Reuse cached logo conversions only after pristine EPS source hash matching."""
import shutil
from pathlib import Path
from .common import sha, write
from .manuscript import PAPER


def run():
    neighbor = Path("/mnt/d/_Work/goat_bank/dlg_gnn/projects/benchmark/paper/current/mdpi/Definitions")
    records = []
    for name in ("logo-mdpi", "logo-updates"):
        original = PAPER / "Definitions" / (name + ".eps")
        if sha(original) != sha(neighbor / (name + ".eps")): raise ValueError("LOGO_CONVERSION_SOURCE_HASH_MISMATCH")
        pdf = neighbor / (name + "-eps-converted-to.pdf")
        target = PAPER / "Definitions" / pdf.name
        if target.exists(): raise FileExistsError(target)
        shutil.copyfile(pdf, target)
        records.append({"pristine_eps_sha256": sha(original), "cached_pdf_sha256": sha(target), "pdf": str(target.relative_to(PAPER)),
                        "conversion_executed_this_run": False, "provenance": "cached neighbor conversion with identical pristine EPS input; not author/paper content"})
    write(PAPER / "cached_logo_conversion_manifest.json", {"files": records, "shell_escape_required": False})


if __name__ == "__main__": run()
