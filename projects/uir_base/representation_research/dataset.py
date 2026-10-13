"""S02 source-first synthetic catalog and separate evaluator expectations."""
import json
from uir_common.contracts import canonical_digest
from uir_common.query_contract import METRICS, SCHEMA, parse_raw, make_artifact
from .common import csvfile, jsonl, sha, textfile, utc, write


def source_first():
    """Source table is built before any question or gold; no real-company claims."""
    facts = []
    provenance = []
    documents = []
    for index, entity in enumerate(("CIRRUS", "MAPLE", "ORBIT", "PINE")):
        for year in (2024, 2025):
            # Independently declared synthetic accounting table (integer values).
            revenue = (index + 1) * 1000 + (year - 2024) * 500
            entries = [("assets", revenue * 2, "USD"), ("revenue", revenue, "USD"), ("profit", revenue // 5, "USD")]
            document = {"entity": entity, "period": str(year), "table": entries, "source_kind": "SYNTHETIC_SOURCE_TABLE_NOT_REAL_REPORT"}
            digest = canonical_digest(document)
            ref = "synthetic-document:" + digest
            provenance.append(ref)
            documents.append({"document_id": ref, "body": document, "body_sha256": digest})
            base = []
            for metric, value, unit in entries:
                fid = f"{entity}_{year}_{metric}"
                base.append(fid)
                facts.append({"id": fid, "entity": entity, "metric": metric, "period": str(year), "unit": unit,
                              "value": str(value), "provenance": ref, "status": "current", "visibility": "public"})
            facts.append({"id": f"{entity}_{year}_margin", "entity": entity, "metric": "margin", "period": str(year),
                          "unit": "percent", "value": "20", "provenance": ref, "status": "current", "visibility": "public",
                          "dependencies": [base[2], base[1]], "operation": "PERCENT_DIV"})
            facts.extend([
                {"id": f"{entity}_{year}_assets_stale", "entity": entity, "metric": "assets", "period": str(year), "unit": "USD",
                 "value": "777", "provenance": ref, "status": "stale", "visibility": "public"},
                {"id": f"{entity}_{year}_assets_EUR", "entity": entity, "metric": "assets", "period": str(year), "unit": "EUR",
                 "value": "123", "provenance": ref, "status": "current", "visibility": "private"}])
    return {"version": "synthetic-corpus-S1", "facts": facts, "trusted_provenance": provenance}, documents


def prepare(out):
    source, documents = source_first()
    jsonl(out / "synthetic_source_documents.jsonl", documents)
    write(out / "source_snapshot.json", source)
    write(out / "source_bytes_manifest.json", {"source_kind": "SYNTHETIC_NON_ORACLE", "created_at_utc": utc(),
          "bytes_sha256": sha(out / "synthetic_source_documents.jsonl"), "document_count": len(documents),
          "real_document_bytes_verified": False, "source_before_query_and_gold": True,
          "rights": "new owner-controlled synthetic fixture; actual author public release approval pending"})
    authority = {"version": "policy-S1", "decision": "ALLOW", "approved": False}
    runtime = []
    gold = []
    bilingual = []
    # Twelve source-first targets, paired raw Korean/English. These are DEVELOPMENT.
    reverse = {value: key for key, value in METRICS.items()}
    for i, (entity, metric, year) in enumerate((e, m, 2025 if j % 2 else 2024)
            for j, e in enumerate(("CIRRUS", "MAPLE", "ORBIT", "PINE")) for m in ("assets", "revenue", "margin")):
        unit = "percent" if metric == "margin" else "USD"
        en = f"show {entity} {metric} for {year} in {unit}."
        ko = f"{entity}의 {year}년 {reverse[metric]}을 {unit} 단위로 보여 주세요."
        family = f"constructed:{entity}:{year}"
        bilingual.append({"pair_id": f"PAIR-{i:02}", "raw_en": en, "raw_ko": ko, "expected_relation": "same_semantics",
                          "evidence_kind": "SYNTHETIC_CONFORMANCE", "human_validated": False})
        for language, raw in (("EN", en), ("KO", ko)):
            cid = f"SDEV-{i:02}-{language}"
            runtime.append({"case_id": cid, "raw_user_request": raw, "language": language, "source": source,
                            "authority": authority, "context": {"active": True, "approved": False}, "family": family,
                            "action": "read", "evidence_kind": "DEVELOPMENT", "source_kind": "SYNTHETIC_NON_ORACLE"})
            # Evaluator-only direct fixture-row match, not runtime interpreter output.
            expected = [f["id"] for f in source["facts"] if (f["entity"], f["metric"], f["period"], f["unit"], f["status"], f["visibility"])
                        == (entity, metric, str(year), unit, "current", "public")]
            public = [f["id"] for f in source["facts"] if f["status"] == "current" and f["visibility"] == "public"]
            if set(expected) == set(public) or len(public) - len(expected) < 3:
                raise ValueError("NOT_A_REAL_SELECTION_TASK")
            gold.append({"case_id": cid, "expected_ids": expected, "expected_state": "FULL_VERIFIED_ANSWER",
                         "family": family, "evidence_kind": "DEVELOPMENT", "label_source": "deterministic synthetic query specification, not human"})
    jsonl(out / "runtime/query_aware_dev.jsonl", runtime)
    jsonl(out / "evaluator_only/query_aware_gold.jsonl", gold)
    csvfile(out / "raw_ko_en_pairs.csv", bilingual)
    csvfile(out / "candidate_catalog_manifest.csv", [{"case_id": r["case_id"], "N_candidate_facts": len(source["facts"]),
            "N_authorized_public_facts": 32, "N_distractors_min": 31, "raw_request_included": True, "scope": "DEVELOPMENT_SYNTHETIC"} for r in runtime])
    csvfile(out / "case_family_manifest.csv", [{"case_id": r["case_id"], "family": r["family"], "language": r["language"],
             "source_family": r["family"], "template_family": "show-entity-metric-year-unit", "split": "DEVELOPMENT"} for r in runtime])
    write(out / "UIR_query_schema_S1.json", SCHEMA)
    textfile(out / "query_aware_dataset_protocol.md", "# Query-aware synthetic development\n\nSource accounting tables precede questions and gold. Every request sees the same 48-fact universe (32 current public facts), with other entities, periods, metrics, stale and private/unit-mismatch facts. Gold has a strict proper subset, stored separately. Real company/source retrieval and confirmatory generalization are NOT_MEASURED. CNL is intentionally easy and constructed by the implementer, not human validated. Query semantics may be compiled without gold. Endpoint QUERY_AWARE_SELECTION is distinct from old CATALOG_ENUMERATION_TRANSPORT; END_TO_END_RETRIEVAL is NOT_IMPLEMENTED.\n")
    textfile(out / "query_aware_metrics_spec.md", "# Frozen endpoints\n\nPrimary: exact query-relevant accepted ID set per all 24 raw requests. Also preserve raw selector exact set, catalog copied flag, supported coverage, invalid/no-response states, accepted closed-language whole-output support, false denial and authorization. Full native prose AUCR remains NOT_MEASURED. Paired families are constructed entity/year clusters; they do not establish unseen template independence.\n")
    print(json.dumps({"S02": "DATA_PREPARED_NOT_FROZEN", "N": len(runtime), "source_facts": len(source["facts"])}))
