"""Generated extra denominator and final source/QA binding, no author approval."""
import csv
from .common import OUT, ROOT, load, sha, write
from .manuscript import PAPER


def prepare_extra():
    source = ROOT / "projects/uir_base/results/mdpi_next_2026_10_11_v2/historical_reanalysis/internal_utility_recomputed.csv"
    with source.open() as handle:
        n = next(csv.DictReader(handle))["N_all"]
    with (PAPER / "generated_metrics_extra.tex").open("x") as handle:
        handle.write("% same science_release_manifest input: " + sha(source) + "\n" + r"\newcommand{\ResultHistoricalAll}{" + n + "}\n")
    write(PAPER / "extra_metric_inputs.json", {"source_sha256": sha(source), "ResultHistoricalAll": int(n),
          "science_release_sha256": sha(OUT / "science_release_manifest.json")})


if __name__ == "__main__": prepare_extra()
