#!/usr/bin/env python3
"""Fetch and freeze a real SEC XBRL companyfacts registry snapshot."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.request
from datetime import date
from decimal import Decimal
from pathlib import Path

COMPANY_LIMIT = 20
CONCEPTS = {
    "assets": ("Assets", "USD"),
    "revenue": ("Revenues", "USD"),
    "net_income": ("NetIncomeLoss", "USD"),
    "operating_income": ("OperatingIncomeLoss", "USD"),
}
TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"


def fetch(url: str, user_agent: str, attempts: int = 3) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    error: Exception | None = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.read()
        except (OSError, TimeoutError) as exc:
            error = exc
            if attempt + 1 < attempts:
                time.sleep(2**attempt)
    raise RuntimeError(f"failed to fetch {url}") from error


def latest_facts(payload: dict, ticker: str, source_url: str, source_hash: str) -> list[dict]:
    records: list[dict] = []
    us_gaap = payload.get("facts", {}).get("us-gaap", {})
    for attribute, (concept, preferred_unit) in CONCEPTS.items():
        fact = us_gaap.get(concept)
        if not fact:
            continue
        units = fact.get("units", {})
        candidates = units.get(preferred_unit, [])
        candidates = [
            item
            for item in candidates
            if item.get("form") in {"10-K", "10-Q"}
            and item.get("filed")
            and item.get("end")
            and item.get("val") is not None
        ]
        by_period: dict[str, dict] = {}
        for item in sorted(candidates, key=lambda row: (row["filed"], row.get("accn", ""))):
            by_period[item["end"][:4]] = item
        for period, item in sorted(by_period.items())[-2:]:
            value = item["val"]
            value_text = format(value, "f") if isinstance(value, Decimal) else str(value)
            accession = item.get("accn", "")
            records.append(
                {
                    "fact_id": f"{ticker}:{attribute}:{period}",
                    "entity_id": ticker,
                    "entity_name": payload.get("entityName", ticker),
                    "claim_type": "numeric_claim",
                    "attribute": attribute,
                    "value": value_text,
                    "unit": preferred_unit,
                    "period": period,
                    "provenance": {
                        "source_id": f"sec:companyfacts:{payload.get('cik')}:{concept}:{accession}",
                        "source_type": "SEC XBRL Companyfacts API snapshot",
                        "source_hash": source_hash,
                        "record_id": accession,
                        "snapshot_date": date.today().isoformat(),
                        "source_url": source_url,
                    },
                }
            )
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("evaluation/uir_external/registry_v1.jsonl"))
    parser.add_argument("--manifest", type=Path, default=Path("evaluation/uir_external/REGISTRY_MANIFEST.json"))
    parser.add_argument("--user-agent", default="HETE UIR Research contact@example.com")
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    tickers_raw = fetch(TICKERS_URL, args.user_agent)
    tickers = json.loads(tickers_raw)
    companies = [tickers[key] for key in sorted(tickers, key=int)[:COMPANY_LIMIT]]
    sources = [{"url": TICKERS_URL, "sha256": hashlib.sha256(tickers_raw).hexdigest(), "bytes": len(tickers_raw)}]
    records: list[dict] = []
    for company in companies:
        cik = int(company["cik_str"])
        ticker = company["ticker"].upper()
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
        raw = fetch(url, args.user_agent)
        source_hash = hashlib.sha256(raw).hexdigest()
        sources.append({"url": url, "sha256": source_hash, "bytes": len(raw)})
        payload = json.loads(raw, parse_float=Decimal)
        records.extend(latest_facts(payload, ticker, url, source_hash))
    records.sort(key=lambda row: row["fact_id"])
    content = "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for row in records
    ).encode()
    args.out.write_bytes(content)
    manifest = {
        "version": "registry-v1",
        "source": "U.S. SEC XBRL Companyfacts API",
        "documentation": "https://www.sec.gov/search-filings/edgar-application-programming-interfaces",
        "snapshot_date": date.today().isoformat(),
        "record_count": len(records),
        "entity_count": len({row["entity_id"] for row in records}),
        "sha256": hashlib.sha256(content).hexdigest(),
        "sources": sources,
    }
    args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: manifest[key] for key in ("record_count", "entity_count", "sha256")}, sort_keys=True))


if __name__ == "__main__":
    main()
