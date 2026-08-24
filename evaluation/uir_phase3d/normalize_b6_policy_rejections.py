#!/usr/bin/env python3
"""Normalize pre-render policy rejections to the explicit B6 NO state."""
from __future__ import annotations
import argparse,json,os
from pathlib import Path

def normalize(path:Path)->int:
    temporary=path.with_name(path.name+".normalize")
    changed=0
    with path.open(encoding="utf-8") as source,temporary.open("w",encoding="utf-8",newline="\n") as target:
        for line in source:
            row=json.loads(line)
            if row.get("pipeline")=="B6_UIR_FILTER_AND_RENDER" and not row.get("renderer_invoked") and row.get("output_state")=="UNVALIDATED":
                row["output_state"]="NO_VERIFIED_ANSWER";changed+=1
            target.write(json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n")
        target.flush();os.fsync(target.fileno())
    temporary.replace(path)
    return changed

def main():
    ap=argparse.ArgumentParser();ap.add_argument("paths",nargs="+",type=Path);ap.add_argument("--evidence",type=Path,required=True);a=ap.parse_args()
    changes={str(path):normalize(path) for path in a.paths}
    evidence={"normalization":"B6 policy-prevented renderer path -> NO_VERIFIED_ANSWER","changed_rows":changes,"model_regeneration":False}
    a.evidence.write_text(json.dumps(evidence,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
