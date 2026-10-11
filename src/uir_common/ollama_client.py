"""Small loopback-only Ollama client; no cloud inference or implicit retries."""
from __future__ import annotations

import hashlib
import json
from urllib.parse import urlsplit

import requests


def local_endpoint(value: str) -> str:
    parsed = urlsplit(value)
    if (parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.path not in {"", "/"}):
        raise ValueError("Use a loopback HTTP endpoint, without credentials or a path")
    # Accessing port also detects malformed or out-of-range ports.
    if parsed.port is None:
        raise ValueError("An explicit local port is required")
    return value.rstrip("/")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class OllamaClient:
    def __init__(self, endpoint: str):
        self.endpoint = local_endpoint(endpoint)
        self.session = requests.Session()
        # Do not forward private local inference through an environment proxy.
        self.session.trust_env = False

    def get(self, route: str) -> dict:
        response = self.session.get(self.endpoint + route, timeout=(10, 60))
        response.raise_for_status()
        return response.json()

    def post(self, route: str, payload: dict, timeout: int = 300) -> dict:
        response = self.session.post(self.endpoint + route, json=payload, timeout=(10, timeout))
        response.raise_for_status()
        result = response.json()
        if result.get("error"):
            raise RuntimeError(result["error"])
        return result

    def pull(self, model: str, progress=None) -> None:
        succeeded = False
        with self.session.post(self.endpoint + "/api/pull", json={"model": model, "stream": True},
                               stream=True, timeout=(10, 300)) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                event = json.loads(line)
                if event.get("error"):
                    raise RuntimeError(event["error"])
                if progress:
                    progress(event)
                succeeded |= event.get("status") == "success"
        if not succeeded:
            raise RuntimeError(f"Pull ended without success for {model}")

    def close(self) -> None:
        self.session.close()
