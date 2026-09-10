#!/usr/bin/env python3
"""
Repair campaign jsonl files where raw LLM text outputs contain unescaped newline characters.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results/uir_phase3b"

def repair_file(path: Path) -> list[dict]:
    if not path.exists():
        return []
    
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    
    records = []
    current_buf = []
    
    for idx, line in enumerate(lines):
        if not line.strip():
            continue
        
        # Check if line by itself is valid JSON
        try:
            obj = json.loads(line)
            if current_buf:
                # Flush existing buffer by trying to parse
                buf_str = "\\n".join(current_buf)
                try:
                    records.append(json.loads(buf_str))
                except Exception:
                    pass
                current_buf = []
            records.append(obj)
            continue
        except Exception:
            # Not valid standalone JSON line (part of multi-line unescaped output)
            current_buf.append(line)
            # Try combining current buffer
            # Replace actual newlines inside buffer with \\n
            # But keep string formatting intact
            buf_str = ""
            for i, chunk in enumerate(current_buf):
                if i > 0:
                    buf_str += "\\n"
                buf_str += chunk
            
            try:
                obj = json.loads(buf_str)
                records.append(obj)
                current_buf = []
            except Exception:
                # Keep accumulating until complete
                pass
                
    print(f"Repaired {path.name}: {len(records)} valid records extracted")
    return records

def main():
    f_v2 = OUT / "campaign_frozen_v2.jsonl"
    f_real = OUT / "campaign_real_fact.jsonl"
    
    recs_v2 = repair_file(f_v2)
    recs_real = repair_file(f_real)
    
    print(f"Frozen v2 valid records: {len(recs_v2)} / 8400")
    print(f"Real fact valid records: {len(recs_real)} / 1400")
    
    # Re-save cleaned files
    if recs_v2:
        content_v2 = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for r in recs_v2)
        f_v2.write_bytes(content_v2.encode("utf-8"))
        print(f"Saved clean {f_v2.name}")
        
    if recs_real:
        content_real = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for r in recs_real)
        f_real.write_bytes(content_real.encode("utf-8"))
        print(f"Saved clean {f_real.name}")
        
    # Re-combine campaign_raw.jsonl
    combined = OUT / "campaign_raw.jsonl"
    combined.write_bytes(f_v2.read_bytes() + f_real.read_bytes())
    print(f"Saved clean {combined.name}")

if __name__ == "__main__":
    main()
