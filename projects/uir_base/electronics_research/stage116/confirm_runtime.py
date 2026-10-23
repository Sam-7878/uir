"""Gold-hidden primary interpreter trial. No reference scorer or gold imports."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

from uir_common.contracts import canonical_digest, reject_gold
from uir_common.query_contract import make_artifact
from projects.uir_base.representation_research.interpreter_python import interpret
from .interchange import to_native, to_uir


def parse_release_query(raw):
    fixed_en = re.fullmatch(r"For release_snapshot, fetch ([A-Z0-9_]+)\.([a-z0-9_]+) as ([A-Z_]+)\.", raw)
    fixed_ko = re.fullmatch(r"release_snapshot에서 ([A-Z0-9_]+)\.([a-z0-9_]+) 값을 ([A-Z_]+)\(으\)로 조회하세요\.", raw)
    if fixed_en or fixed_ko:
        entity, metric, unit = (fixed_en or fixed_ko).groups()
        return {"entity": entity, "metric": metric, "period": "release_snapshot", "unit": unit, "predicate": None}
    en = re.fullmatch(r"Read ([a-z0-9_]+) from ([A-Z0-9_]+)'s release_snapshot manifest in ([A-Z_]+)\.", raw)
    ko = re.fullmatch(r"([A-Z0-9_]+) 릴리스 manifest에서 ([a-z0-9_]+)을 ([A-Z_]+) 단위로 읽으세요\.", raw)
    if en:
        metric, entity, unit = en.groups()
    elif ko:
        entity, metric, unit = ko.groups()
    else:
        raise ValueError("UNSUPPORTED_HELDOUT_CNL")
    return {"entity": entity, "metric": metric, "period": "release_snapshot", "unit": unit, "predicate": None}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--probe-gold", type=Path, required=True)
    parser.add_argument("--mode", choices=("probe", "infer"), required=True)
    args = parser.parse_args()
    try:
        args.probe_gold.read_bytes()
    except (PermissionError, FileNotFoundError): pass
    else: raise RuntimeError("GOLD_VISIBLE_TO_RUNTIME")
    data = args.runtime.read_bytes()
    print(json.dumps({"type": "boundary", "gold_read": "BLOCKED", "runtime_sha256": hashlib.sha256(data).hexdigest()}), flush=True)
    if args.mode == "probe": return  # no heldout decisions before protocol freeze
    rows = [json.loads(x) for x in data.splitlines() if x]
    reject_gold(rows)
    todo = []
    for row in rows:
        semantics = parse_release_query(row["raw_user_request"])
        packet = {"artifact": make_artifact(semantics, row["authority"], row["source"]), "authority": row["authority"], "context": {},
                  "current_evidence_version": row["source"]["version"], "current_evidence_sha256": canonical_digest(row["source"])}
        for representation in ("UIR", "SPECIALIZED"):
            actual = json.loads(json.dumps(packet)) if representation == "UIR" else to_native(packet)
            wire = actual if representation == "UIR" else to_uir(actual)
            todo.append((row, representation, actual, wire))
    rust = subprocess.run(["/consumer/uir_contract_eval"], input="".join(json.dumps(r[3]) + "\n" for r in todo),
                          text=True, capture_output=True, timeout=120, check=True)
    answers = [json.loads(x) for x in rust.stdout.splitlines()]
    for (row, representation, actual, wire), answer in zip(todo, answers, strict=True):
        python = interpret(actual)
        by_id = {f["id"]: f for f in row["source"]["facts"]}
        print(json.dumps({"type": "outcome", "case_id": row["case_id"], "family": row["family"], "representation": representation,
                          "python": python, "rust": answer, "consumer_agreement": python == answer,
                          "accepted_values": [{k: by_id[fid][k] for k in ("id", "value", "provenance")} for fid in python["fact_ids"]],
                          "compiled_semantics": wire["artifact"]["semantics"],
                          "semantic_digest": wire["artifact"]["semantic_digest"], "selector": "DETERMINISTIC", "renderer": "TEMPLATE",
                          "split": "CONFIRMATORY_FRESH_FIXED_CORPUS", "model_invoked": False}), flush=True)


if __name__ == "__main__": main()
