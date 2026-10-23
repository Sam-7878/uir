# Dataset Card — UIR Software Manifest Conformance Corpus (V4)

## 1. Corpus Summary
- **Domain:** Open-source software manifests (Rust ecosystem, `Cargo.toml`/`Cargo.lock`).
- **Eligible Target Frame:** $M = 82$ distinct GitHub-owner clusters meeting strict inclusion criteria (permissive license, clean manifest parsing, non-empty release snapshot).
- **Primary Sample Size:** $n = 60$ distinct clusters sampled without replacement ($SRSWOR$).
- **Cases per Cluster:** 4 balanced queries (2 ALLOW: major/minor version; 2 DENY: unauthorized scope/metric).
- **Total Evaluated Cases:** 240 unique cases $\times 2$ representations (UIR, Specialized) $= 480$ records.

## 2. Supported Metrics and Grounding
- **Entities:** Software package names (canonical uppercase tokens).
- **Metrics:** `package_version_major`, `package_version_minor`.
- **Period:** `release_snapshot`.
- **Units:** `COUNT`.
- **Grounding Target:** Exact source provenance pointers pointing to physical source byte offsets (`github-owner:<owner>:<commit>/package/version#<field>`).

## 3. Second-Domain Status
- US Treasury fiscal debt data was piloted on 5 rows to verify parser extensibility.
- Due to lack of independent large-scale query-aware gold and OS isolation in the pilot, it is **excluded from confirmatory claims** and documented solely as an exploratory feasibility demonstration.
