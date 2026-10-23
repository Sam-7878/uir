import os
import hashlib
import json
from datetime import datetime

base_dir = r'd:\_Work\goat_bank\uir\projects\uir_base\results\120_electronics_release_closure_2026_10_24'
paper_dir = r'd:\_Work\goat_bank\uir\projects\uir_base\paper\mdpi_electronics_120'
out_manifest = os.path.join(base_dir, 'EVIDENCE_MANIFEST_120.json')

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

items = []

# Scan results directory
for root, dirs, files in os.walk(base_dir):
    for f in files:
        if f == 'EVIDENCE_MANIFEST_120.json':
            continue
        full_p = os.path.join(root, f)
        rel_p = os.path.relpath(full_p, r'd:\_Work\goat_bank\uir\projects\uir_base').replace('\\', '/')
        sz = os.path.getsize(full_p)
        h = sha256_file(full_p)
        
        category = 'AUDIT'
        if '/scripts/' in rel_p:
            category = 'SCRIPTS'
        elif '/editorial/' in rel_p:
            category = 'EDITORIAL'
        elif '/release/' in rel_p:
            category = 'RELEASE'
        elif '/publication_gates/' in rel_p:
            category = 'GATES'
        elif '/statistics/' in rel_p:
            category = 'STATISTICS'
        elif '/scientific/' in rel_p or '/claim_audit/' in rel_p:
            category = 'SCIENTIFIC'
        
        items.append({
            "path": rel_p,
            "bytes": sz,
            "sha256": h,
            "category": category,
            "verification_status": "VERIFIED_STAGE_120",
            "description": f"Stage 120 deliverable: {f}"
        })

# Scan paper directory
for root, dirs, files in os.walk(paper_dir):
    for f in files:
        if f.endswith(('.aux', '.bbl', '.blg', '.out', '.log', '.toc')) or f.startswith('test_'):
            continue
        full_p = os.path.join(root, f)
        rel_p = os.path.relpath(full_p, r'd:\_Work\goat_bank\uir\projects\uir_base').replace('\\', '/')
        sz = os.path.getsize(full_p)
        h = sha256_file(full_p)
        
        items.append({
            "path": rel_p,
            "bytes": sz,
            "sha256": h,
            "category": "MANUSCRIPT_SOURCE",
            "verification_status": "VERIFIED_STAGE_120",
            "description": f"Stage 120 manuscript asset: {f}"
        })

manifest = {
    "manifest_version": "120.0.0",
    "stage": "STAGE_120_EVIDENCE_EDITORIAL_RELEASE_CLOSURE",
    "created_at_iso": datetime.now().astimezone().isoformat(),
    "manuscript_title": "Policy-and-Evidence Intermediate Contracts for Generative-AI Software: Independent Interpreter Conformance and Query-Aware Grounding",
    "target_venue": "MDPI Electronics (Special Issue: Generative and Multi-Agent AI for Next-Generation Electronic and Software Systems)",
    "summary_counts": {
        "total_manifested_items": len(items),
        "total_manifested_bytes": sum(x["bytes"] for x in items)
    },
    "records": sorted(items, key=lambda x: x["path"])
}

with open(out_manifest, 'w', encoding='utf-8') as f:
    json.dump(manifest, f, indent=2)

print(f"Generated manifest with {len(items)} items, total {manifest['summary_counts']['total_manifested_bytes']} bytes at {out_manifest}")
