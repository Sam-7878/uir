#!/usr/bin/env python3
import argparse,json
from collections import Counter
from pathlib import Path
def main():
    ap=argparse.ArgumentParser();ap.add_argument("raw",type=Path);a=ap.parse_args()
    with a.raw.open(encoding="utf-8") as handle:rows=[json.loads(line) for line in handle if line.strip()]
    b6=[x for x in rows if x["pipeline"]=="B6_UIR_FILTER_AND_RENDER"]
    data={"rows":len(rows),"format_errors":sum(x["format_error"] is not None for x in rows),"truncated":sum(x.get("json_truncated",False) for x in rows),
          "max_output_tokens":max((x["latency"]["output_tokens"] for x in rows),default=0),"b6_states":Counter(x.get("output_state") for x in b6),
          "b6_numeric_preservation":sum(x["metrics"].get("numeric_exact_match",0) for x in b6)/len(b6) if b6 else 0,
          "b6_unsupported_accepted":sum(x["metrics"]["accepted_unsupported_claims"] for x in b6)}
    data["by_pipeline"]={p:{"n":len(g),"format_errors":sum(x["format_error"] is not None for x in g),
        "at_192_token_budget":sum(x["latency"]["output_tokens"]>=192 for x in g),"max_output_tokens":max((x["latency"]["output_tokens"] for x in g),default=0)}
        for p in sorted({x["pipeline"] for x in rows}) for g in [[x for x in rows if x["pipeline"]==p]]}
    print(json.dumps(data,sort_keys=True))
if __name__=="__main__":main()
