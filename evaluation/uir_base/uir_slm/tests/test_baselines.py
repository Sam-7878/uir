import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "uir_external"))

from baselines import build_request
from registry_adapter import FrozenRegistry


def test_entity_validation_rejects_unknown_entity(tmp_path):
    registry_path = tmp_path / "registry.jsonl"
    registry_path.write_text(json.dumps({"fact_id":"A:x:2025","entity_id":"A","entity_name":"A","claim_type":"numeric_claim","attribute":"x","value":"1","unit":"USD","period":"2025","provenance":{"source_id":"s"}}) + "\n")
    registry = FrozenRegistry(registry_path)
    case = {"input":"verify Z", "expected_semantics":{"target":"Z", "metric":"x", "period":"2025"}, "entity_valid":False, "policy_valid":True}
    request = build_request("B3_RAG_WITH_ENTITY_VALIDATION", case, registry, None)
    assert not request.invoke_renderer
