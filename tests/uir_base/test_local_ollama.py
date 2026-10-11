import pytest

from uir_common.ollama_client import local_endpoint, sha256_text
from projects.uir_base.scripts.setup_local_models import MODELS


@pytest.mark.parametrize("endpoint", ["http://127.0.0.1:18747", "http://localhost:18747/", "http://[::1]:18747"])
def test_only_local_endpoint_allowed(endpoint):
    assert local_endpoint(endpoint) == endpoint.rstrip("/")


@pytest.mark.parametrize("endpoint", ["https://127.0.0.1:18747", "http://ollama.com:80", "http://127.0.0.1",
                                      "http://user:secret@localhost:18747", "http://localhost:18747/api",
                                      "http://localhost:18747?key=secret", "http://localhost:99999"])
def test_reject_remote_or_credentialed_endpoint(endpoint):
    with pytest.raises(ValueError):
        local_endpoint(endpoint)


def test_approved_model_roles_never_impersonate_humans():
    assert set(MODELS) == {"phi3.5:latest", "qwen3:4b-instruct-2507-q4_K_M", "ministral-3:14b"}
    assert MODELS["qwen3:4b-instruct-2507-q4_K_M"]["role"] == "AI_J1"
    assert MODELS["ministral-3:14b"]["role"] == "AI_J2"
    assert "qwen3:1.7b" not in MODELS


def test_output_digest_uses_exact_utf8_bytes():
    assert sha256_text("READY") != sha256_text("READY\n")
