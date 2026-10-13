"""Actual API/domain extension conformance and small automated costs, not labor productivity."""
import ast
import json
import subprocess
import time
from uir_common.contracts import canonical_digest
from .api_frontends import shared, specialized
from .common import ROOT, csvfile, read, sha, textfile, utc, write
from .interpreter_python import interpret


def run(out):
    textfile(out / "portability_change_requests.md", "# Extension trial\n\nAdd one actual structured JSON frontend to both conditions, including a new energy_kwh attribute/unitkWh not in raw financial CNL, without changing either interpreter core. Common validation utility is allowed in both. Implementation is already written before this execution protocol; this is an automated extension conformance trial, NOT a blinded developer-effort experiment. Independent specialized developer and reviewer labor are NOT_MEASURED.\n")
    write(out / "portability_pre_execution_receipt.json", {"created_at_utc": utc(), "request_sha256": sha(out / "portability_change_requests.md"),
          "source_sha256": sha(ROOT / "projects/uir_base/representation_research/api_frontends.py"), "protocol_before_extension_execution": True,
          "protocol_before_implementation": False, "independent_developer": False})
    row = read(out / "runtime/query_aware_dev.jsonl")[0]
    authority = row["authority"]
    energy = {"version": "synthetic-energy-S1", "trusted_provenance": ["synthetic-energy:owned"], "facts": [
        {"id": "ENERGY_1", "entity": "BUILDING_A", "metric": "energy_kwh", "period": "2025", "unit": "kWh", "value": "320",
         "provenance": "synthetic-energy:owned", "status": "current", "visibility": "public"}]}
    data = [("financial_api", {"entity": "CIRRUS", "metric": "assets", "period": "2024", "unit": "USD", "predicate": None}, row["source"]),
            ("energy_domain_api", {"entity": "BUILDING_A", "metric": "energy_kwh", "period": "2025", "unit": "kWh", "predicate": None}, energy)]
    results = []
    packets = []
    for label, payload, source in data:
        a, b = shared(payload, authority, source), specialized(payload, authority, source)
        # Public contract actually crosses Python-to-Rust JSON-line boundary.
        rust = subprocess.run([str(ROOT / "target/debug/uir_contract_eval")], input=json.dumps(a) + "\n", text=True, capture_output=True, check=True)
        actual_rust = json.loads(rust.stdout)
        actual_a, actual_b = interpret(a), interpret(b)
        results.append({"change_case": label, "UIR_python": actual_a, "specialized_python": actual_b, "UIR_Rust": actual_rust,
                        "all_semantics_preserved": actual_a == actual_b == actual_rust, "core_source_changes_for_API": 0,
                        "shared_utilities_allowed_in_both": True, "evidence_kind": "SYNTHETIC_CONFORMANCE"})
        packets.append(a)
    sourcefile = ROOT / "projects/uir_base/representation_research/api_frontends.py"
    tree = ast.parse(sourcefile.read_text())
    sizes = {n.name: n.end_lineno - n.lineno + 1 for n in tree.body if isinstance(n, ast.FunctionDef)}
    costs = []
    for name, builder in (("UIR_SHARED_TYPED", shared), ("SPECIALIZED_EQUIVALENT", specialized)):
        values = []
        for _ in range(100):
            start = time.perf_counter_ns()
            packet = builder(data[0][1], authority, data[0][2])
            if name == "UIR_SHARED_TYPED":
                packet = json.loads(json.dumps(packet))
            interpret(packet)
            values.append((time.perf_counter_ns() - start) / 1e6)
        values.sort()
        costs.append({"condition": name, "source_file_count": 1, "wrapper_function_LOC": sizes["shared" if name == "UIR_SHARED_TYPED" else "specialized"],
                      "shared_validation_LOC": sizes["typed_query"], "N_automated_repetitions": 100, "P50_ms": values[49], "P95_ms": values[94], "P99_ms": values[98],
                      "includes_serialization": name == "UIR_SHARED_TYPED", "developer_hours": "NOT_MEASURED", "independent_review_hours": "NOT_MEASURED",
                      "scope": "one-host warm API-build+guard; not total implementation complexity or productivity"})
    from .common import jsonl
    jsonl(out / "backend_portability_cases.jsonl", results)
    jsonl(out / "portability_UIR_packets.jsonl", packets)
    csvfile(out / "implementation_cost.csv", costs)
    csvfile(out / "per_condition_git_diff_manifest.csv", [{"condition": r["condition"], "source_path": str(sourcefile.relative_to(ROOT)), "source_sha256": sha(sourcefile),
             "code_revision_kind": "new uncommitted source; byte hash authoritative", "observed_wrapper_LOC": r["wrapper_function_LOC"], "historical_core_modified_for_extension": False} for r in costs])
    textfile(out / "development_effort_protocol.md", "# Cost interpretation\n\nWrapper LOC includes only these two functions and a shared typed validation helper; it excludes public contract/core implementations and is not a productivity estimate. UIR intentionally includes a serialize/deserialize boundary, specialized does not; timings measure that actual differing workload.100 warm repetitions are not independent humans or cold-start/GPU latency. Developer/reviewer hours and independent specialist effort remain NOT_MEASURED. Both core implementations accept the declared new domain without a core patch; no universal cost advantage follows.\n")
    print(json.dumps({"portability_cases": results, "costs": costs}))
