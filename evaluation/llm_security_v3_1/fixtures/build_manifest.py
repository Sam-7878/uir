"""Build Frozen Trusted Source Manifest for HETE V3.1 Provenance Verification."""
import hashlib
import json
from pathlib import Path
from evaluation.llm_security_v3_1.provenance import compute_evidence_signature
from evaluation.llm_security_v3_1.attacks.generator_v3_1 import VERIFIED_ENTITIES


def build_manifest() -> None:
    manifest = {"trusted_sources": []}
    for ticker, info in VERIFIED_ENTITIES.items():
        auth = info["domain"]
        res_id = f"reports/{ticker}/2023"
        cnt = f"Official filing for {info['name']} ({ticker}): Fiscal Year 2023 revenue was {info['revenue']}."
        sha = hashlib.sha256(cnt.encode("utf-8")).hexdigest()
        signer = "trusted_enterprise_signer"
        sig = compute_evidence_signature(auth, res_id, sha, signer)
        manifest["trusted_sources"].append({
            "authority": auth,
            "resource_id": res_id,
            "content_sha256": sha,
            "signer_id": signer,
            "signature": sig,
            "entity": ticker,
        })

    # Add internal registry entities
    for ticker in VERIFIED_ENTITIES:
        auth = "internal.entity.registry"
        res_id = ticker
        cnt = f"REGISTRY_ENTRY_{ticker}"
        sha = hashlib.sha256(cnt.encode("utf-8")).hexdigest()
        signer = "internal_registry"
        sig = compute_evidence_signature(auth, res_id, sha, signer)
        manifest["trusted_sources"].append({
            "authority": auth,
            "resource_id": res_id,
            "content_sha256": sha,
            "signer_id": signer,
            "signature": sig,
            "entity": ticker,
        })

    out_path = Path(__file__).parent / "trusted_source_manifest.json"
    out_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Generated {len(manifest['trusted_sources'])} trusted manifest entries at {out_path}")


if __name__ == "__main__":
    build_manifest()
