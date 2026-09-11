"""CourtListener v4 citation-lookup client with raw-response preservation."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .common import PACKAGE_ROOT, SOURCE_RESPONSE_DIR, canonical_json, sha256_bytes, sha256_text, utc_now, write_json

ENDPOINT = "https://www.courtlistener.com/api/rest/v4/citation-lookup/"


class CourtListenerError(RuntimeError):
    pass


@dataclass(frozen=True)
class LookupBatch:
    entries: list[dict[str, Any]]
    raw_path: Path
    raw_sha256: str
    retrieved_at: str


class CourtListenerClient:
    def __init__(self, token: str | None = None, auth_scheme: str = "Token", timeout: int = 180):
        self.token = token or os.environ.get("COURTLISTENER_API_TOKEN")
        if not self.token:
            raise CourtListenerError(
                "COURTLISTENER_API_TOKEN is required. Export it in the Ubuntu shell; never save it in the repository."
            )
        if auth_scheme not in {"Token", "Bearer"}:
            raise ValueError("auth_scheme must be Token or Bearer")
        self.auth_scheme = auth_scheme
        self.timeout = timeout

    def lookup(self, citations: list[str], label: str) -> LookupBatch:
        if not citations or len(citations) > 60:
            raise ValueError("each authenticated batch must contain 1..60 citations")
        text = "\n".join(f"Citation {index}: {citation}." for index, citation in enumerate(citations, 1))
        payload = urllib.parse.urlencode({"text": text}).encode("utf-8")
        request = urllib.request.Request(
            ENDPOINT,
            data=payload,
            headers={
                "Authorization": f"{self.auth_scheme} {self.token}",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "UIR-LAW200/0.1 (research benchmark)",
            },
            method="POST",
        )
        started = time.perf_counter()
        raw = b""
        safe_headers: dict[str, str] = {}
        status = 0
        for attempt in range(1, 6):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    raw = response.read()
                    status = response.status
                    safe_headers = {
                        key.lower(): value for key, value in response.headers.items()
                        if key.lower() in {"content-type", "date", "retry-after", "x-ratelimit-limit", "x-ratelimit-remaining"}
                    }
                break
            except urllib.error.HTTPError as exc:
                raw = exc.read()
                if exc.code != 429 or attempt == 5:
                    detail = raw.decode("utf-8", errors="replace")[:1000]
                    raise CourtListenerError(f"CourtListener HTTP {exc.code}: {detail}") from exc
                delay = retry_delay_seconds(exc, raw)
                print(f"[courtlistener] throttled; retrying in {delay:.1f}s", flush=True)
                remaining = delay
                while remaining > 0:
                    interval = min(30.0, remaining)
                    time.sleep(interval)
                    remaining -= interval
            except urllib.error.URLError as exc:
                raise CourtListenerError(f"CourtListener request failed: {exc}") from exc
        if status != 200:
            raise CourtListenerError(f"unexpected CourtListener HTTP status {status}")
        try:
            entries = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CourtListenerError("CourtListener returned non-JSON content") from exc
        if not isinstance(entries, list):
            raise CourtListenerError("CourtListener citation lookup response must be a list")
        digest = sha256_bytes(raw)
        retrieved_at = utc_now()
        SOURCE_RESPONSE_DIR.mkdir(parents=True, exist_ok=True)
        raw_path = SOURCE_RESPONSE_DIR / f"{label}_{digest[:16]}.json"
        raw_path.write_bytes(raw)
        write_json(
            raw_path.with_suffix(".metadata.json"),
            {
                "endpoint": ENDPOINT,
                "requested_citations": citations,
                "retrieved_at": retrieved_at,
                "http_status": status,
                "safe_response_headers": safe_headers,
                "raw_sha256": digest,
                "elapsed_seconds": time.perf_counter() - started,
            },
        )
        return LookupBatch(entries, raw_path, digest, retrieved_at)


def retry_delay_seconds(error: urllib.error.HTTPError, raw: bytes) -> float:
    retry_after = error.headers.get("Retry-After") if error.headers else None
    if retry_after:
        try:
            return max(1.0, float(retry_after) + 1.0)
        except ValueError:
            pass
    try:
        payload = json.loads(raw)
        wait_until = payload.get("wait_until") or payload.get("wait_util")
        if wait_until:
            target = datetime.fromisoformat(str(wait_until).replace("Z", "+00:00"))
            return max(1.0, (target - datetime.now(timezone.utc)).total_seconds() + 1.0)
    except (ValueError, TypeError, AttributeError):
        pass
    return 61.0


def entry_record(entry: dict[str, Any], batch: LookupBatch, mutation: dict[str, Any] | None = None) -> dict[str, Any]:
    clusters = entry.get("clusters") if isinstance(entry.get("clusters"), list) else []
    cluster = clusters[0] if clusters and isinstance(clusters[0], dict) else {}
    normalized = entry.get("normalized_citations") or [entry.get("citation", "")]
    citation = str(normalized[0]) if normalized else str(entry.get("citation", ""))
    cluster_id = cluster.get("id")
    resource_uri = str(cluster.get("resource_uri") or "")
    if cluster_id is None and resource_uri:
        pieces = resource_uri.rstrip("/").split("/")
        if pieces and pieces[-1].isdigit():
            cluster_id = int(pieces[-1])
    source_uri = (
        f"https://www.courtlistener.com/opinion/{cluster_id}/" if cluster_id is not None
        else ENDPOINT
    )
    raw_entry_sha = sha256_text(canonical_json(entry))
    record: dict[str, Any] = {
        "citation_raw": str(entry.get("citation", "")),
        "citation_canonical": citation,
        "case_name": str(cluster.get("case_name") or cluster.get("case_name_full") or ""),
        "court": str(cluster.get("court") or "Supreme Court of the United States"),
        "date_filed": str(cluster.get("date_filed") or ""),
        "courtlistener_cluster_id": cluster_id,
        "lookup_status": int(entry.get("status", 0)),
        "source_uri": source_uri,
        "retrieved_at": batch.retrieved_at,
        "response_sha256": raw_entry_sha,
        "raw_response_file": str(batch.raw_path.relative_to(PACKAGE_ROOT)),
        "raw_batch_sha256": batch.raw_sha256,
        "error_message": str(entry.get("error_message") or ""),
        "source_id": f"courtlistener:cluster:{cluster_id}" if cluster_id is not None else f"courtlistener:citation:{sha256_text(citation)[:16]}",
    }
    if mutation:
        record["mutation"] = mutation
    return record


def wait_for_citation_window(seconds: float = 61.0) -> None:
    """Respect the documented 60-citation/minute scope between full batches."""
    time.sleep(seconds)
