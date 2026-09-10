#!/usr/bin/env python3
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def current_hash():
    paths=[*sorted((ROOT/"crates/poa-uir/src/frontend").glob("*.rs")),ROOT/"crates/poa-uir/src/resolution.rs",ROOT/"crates/poa-uir/src/output_contract.rs"]
    h=hashlib.sha256()
    for p in paths:h.update(p.relative_to(ROOT).as_posix().encode());h.update(p.read_bytes())
    return h.hexdigest()
def main():
    phase3=json.loads((ROOT/"results/uir_phase3/frozen_v2_manifest.json").read_text())
    digest=current_hash()
    if digest!=phase3["parser_source_sha256"]:raise SystemExit("parser changed after Phase-3 candidate generation")
    subprocess.run(["git","cat-file","-e","309e694^{commit}"],cwd=ROOT,check=True)
    data={"status":"frozen_before_human_review","parser_implementation_commit":"309e694","parser_source_sha256":digest,
          "human_review_started":False,"phase3_candidate_sha256":phase3["candidate_sha256"],
          "scope":["crates/poa-uir/src/frontend/*.rs","crates/poa-uir/src/resolution.rs","crates/poa-uir/src/output_contract.rs"],
          "note":"Phase-3B may change evaluation instrumentation but not these parser/semantic/output-contract sources after review begins."}
    (ROOT/"evaluation/uir_phase3b/PARSER_FREEZE.json").write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
