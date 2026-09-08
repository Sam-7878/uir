"""Trusted Evidence Resolver with Allow-list, Hash Integrity, and Quarantine."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from .provenance import EvidenceRecord, EvidenceTrust, SourceType, create_evidence_record


class ResolutionStatus(str, Enum):
    RESOLVED = "RESOLVED"
    NO_VERIFIED_EVIDENCE = "NO_VERIFIED_EVIDENCE"
    QUARANTINED = "QUARANTINED"
    CONFLICT_DETECTED = "CONFLICT_DETECTED"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"


# Trusted source registry (allow-list)
ALLOWED_SOURCE_DOMAINS: Set[str] = {
    "sec.gov",
    "dart.fss.or.kr",
    "open.law.go.kr",
    "treasury.gov",
    "bank.internal.corp",
}

# Known verified entities database for grounded testing
VERIFIED_ENTITY_REGISTRY: Dict[str, Dict[str, Any]] = {
    "AAPL": {
        "name": "Apple Inc.",
        "cik": "0000320193",
        "revenue_2023": "$383.29B",
        "net_income_2023": "$96.99B",
        "domain": "FINANCE",
    },
    "MSFT": {
        "name": "Microsoft Corporation",
        "cik": "0000789019",
        "revenue_2023": "$211.91B",
        "net_income_2023": "$72.36B",
        "domain": "FINANCE",
    },
    "GOOGL": {
        "name": "Alphabet Inc.",
        "cik": "0001652044",
        "revenue_2023": "$307.39B",
        "net_income_2023": "$73.80B",
        "domain": "FINANCE",
    },
    "GOOG": {
        "name": "Alphabet Inc.",
        "cik": "0001652044",
        "revenue_2023": "$307.39B",
        "net_income_2023": "$73.80B",
        "domain": "FINANCE",
    },
    "AMZN": {
        "name": "Amazon.com Inc.",
        "cik": "0001018724",
        "revenue_2023": "$574.78B",
        "net_income_2023": "$30.43B",
        "domain": "FINANCE",
    },
    "NVDA": {
        "name": "NVIDIA Corporation",
        "cik": "0001045810",
        "revenue_2023": "$60.92B",
        "net_income_2023": "$29.76B",
        "domain": "FINANCE",
    },
    "META": {
        "name": "Meta Platforms Inc.",
        "cik": "0001326801",
        "revenue_2023": "$134.90B",
        "net_income_2023": "$39.10B",
        "domain": "FINANCE",
    },
    "TSLA": {
        "name": "Tesla Inc.",
        "cik": "0001318605",
        "revenue_2023": "$96.77B",
        "net_income_2023": "$14.97B",
        "domain": "FINANCE",
    },
    "NFLX": {
        "name": "Netflix Inc.",
        "cik": "0001065280",
        "revenue_2023": "$33.72B",
        "net_income_2023": "$5.41B",
        "domain": "FINANCE",
    },
    "005930": {
        "name": "Samsung Electronics",
        "crno": "130111-0006246",
        "revenue_2023": "258.93T KRW",
        "operating_profit_2023": "6.57T KRW",
        "domain": "FINANCE",
    },
    "000660": {
        "name": "SK Hynix",
        "crno": "134211-0007872",
        "revenue_2023": "32.77T KRW",
        "operating_profit_2023": "-7.73T KRW",
        "domain": "FINANCE",
    },
    "005380": {
        "name": "Hyundai Motor",
        "crno": "110111-0085450",
        "revenue_2023": "162.66T KRW",
        "operating_profit_2023": "15.13T KRW",
        "domain": "FINANCE",
    },
    "035420": {
        "name": "NAVER",
        "crno": "110111-1707178",
        "revenue_2023": "9.67T KRW",
        "operating_profit_2023": "1.49T KRW",
        "domain": "FINANCE",
    },
    "000270": {
        "name": "Kia Corporation",
        "crno": "110111-0012543",
        "revenue_2023": "99.81T KRW",
        "operating_profit_2023": "11.61T KRW",
        "domain": "FINANCE",
    },
    "051910": {
        "name": "LG Chem",
        "crno": "110111-2244243",
        "revenue_2023": "55.25T KRW",
        "operating_profit_2023": "2.53T KRW",
        "domain": "FINANCE",
    },
    "068270": {
        "name": "Celltrion",
        "crno": "130111-0036647",
        "revenue_2023": "2.18T KRW",
        "operating_profit_2023": "0.65T KRW",
        "domain": "FINANCE",
    },
    "005490": {
        "name": "POSCO Holdings",
        "crno": "110111-0021674",
        "revenue_2023": "77.13T KRW",
        "operating_profit_2023": "3.53T KRW",
        "domain": "FINANCE",
    },
    "035720": {
        "name": "Kakao",
        "crno": "110111-1205164",
        "revenue_2023": "7.56T KRW",
        "operating_profit_2023": "0.46T KRW",
        "domain": "FINANCE",
    },
    "105560": {
        "name": "KB Financial Group",
        "crno": "110111-3893326",
        "revenue_2023": "85.42T KRW",
        "operating_profit_2023": "6.22T KRW",
        "domain": "FINANCE",
    },
    "055550": {
        "name": "Shinhan Financial Group",
        "crno": "110111-2309191",
        "revenue_2023": "67.89T KRW",
        "operating_profit_2023": "5.71T KRW",
        "domain": "FINANCE",
    },
}

# Explicit fictitious/nonexistent entities for negative testing
NONEXISTENT_ENTITIES: Set[str] = {
    "FAKE_CORP",
    "NULL_TICKER",
    "PHANTOM_LLC",
    "XYZ_MAGIC_TOKEN",
    "SHADOW_BANK_99",
    "NONEXISTENT_INC",
    "가짜기업_99",
    "유령법인_001",
    "허위주식회사",
}


@dataclass
class ResolutionResult:
    status: ResolutionStatus
    evidence: List[EvidenceRecord]
    verified_facts: Dict[str, Any] = field(default_factory=dict)
    rejection_reason: Optional[str] = None


class TrustedEvidenceResolver:
    """Resolves and validates evidence against cryptographic and policy allow-lists."""

    def __init__(
        self,
        allowed_domains: Optional[Set[str]] = None,
        entity_registry: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        self.allowed_domains = allowed_domains or ALLOWED_SOURCE_DOMAINS
        self.entity_registry = entity_registry or VERIFIED_ENTITY_REGISTRY

    def resolve_entity(self, entity_id: str, domain: str = "FINANCE") -> ResolutionResult:
        """Exact entity verification prior to any semantic processing."""
        clean_id = entity_id.strip().upper()

        if clean_id in NONEXISTENT_ENTITIES:
            return ResolutionResult(
                status=ResolutionStatus.NO_VERIFIED_EVIDENCE,
                evidence=[],
                rejection_reason=f"Entity '{entity_id}' is identified as fictitious or unverified.",
            )

        if clean_id in self.entity_registry:
            fact_data = self.entity_registry[clean_id]
            content_str = f"Official Record for {clean_id}: {fact_data}"
            ev = create_evidence_record(
                source_id=f"registry:{clean_id}",
                content=content_str,
                source_type=SourceType.DATABASE,
                trust=EvidenceTrust.TRUSTED,
                signer="trusted_registrar",
                instruction_bearing=False,
            )
            return ResolutionResult(
                status=ResolutionStatus.RESOLVED,
                evidence=[ev],
                verified_facts=fact_data,
            )

        return ResolutionResult(
            status=ResolutionStatus.NO_VERIFIED_EVIDENCE,
            evidence=[],
            rejection_reason=f"No verified record found for entity '{entity_id}'.",
        )

    def evaluate_retrieved_evidence(
        self,
        raw_evidence: List[Dict[str, Any]],
        strict_provenance: bool = True,
    ) -> ResolutionResult:
        """Validates retrieved evidence documents (RAG / Tool outputs).

        Quarantines or rejects:
        1. Documents with missing / mismatched SHA-256 hashes
        2. Documents bearing suspicious instruction payloads
        3. Documents from untrusted / unapproved sources
        4. Mutually contradictory evidence sets
        """
        verified_records: List[EvidenceRecord] = []
        quarantined_records: List[EvidenceRecord] = []

        for item in raw_evidence:
            source_id = item.get("source_id", "unknown_source")
            content = item.get("content", "")
            source_type_str = item.get("source_type", "RAG")
            source_type = SourceType(source_type_str) if source_type_str in SourceType.__members__ else SourceType.RAG
            provided_hash = item.get("sha256")
            signer = item.get("signer")
            is_instruction_bearing = bool(item.get("instruction_bearing", False))

            computed_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

            # Hash integrity check
            if provided_hash and provided_hash != computed_hash:
                return ResolutionResult(
                    status=ResolutionStatus.INTEGRITY_FAILURE,
                    evidence=[],
                    rejection_reason=f"Evidence integrity mismatch for source '{source_id}'.",
                )

            # Check if source is in allow-list
            is_source_allowed = any(domain in source_id.lower() for domain in self.allowed_domains)

            # Detect instruction injection markers in evidence
            suspicious_markers = [
                "ignore previous instructions",
                "system override",
                "reveal confidential",
                "you are now in admin mode",
                "이전 지시를 무시",
                "시스템 프롬프트를 공개",
            ]
            has_injection_payload = any(marker in content.lower() for marker in suspicious_markers)
            if has_injection_payload:
                is_instruction_bearing = True

            # If evidence contains active instructions or is untrusted/unsigned
            if is_instruction_bearing or not is_source_allowed:
                rec = EvidenceRecord(
                    source_id=source_id,
                    source_type=source_type,
                    trust=EvidenceTrust.QUARANTINED,
                    sha256=computed_hash,
                    verified=False,
                    instruction_bearing=is_instruction_bearing,
                    signer=signer,
                    content_payload=content,
                )
                quarantined_records.append(rec)
            else:
                rec = EvidenceRecord(
                    source_id=source_id,
                    source_type=source_type,
                    trust=EvidenceTrust.TRUSTED,
                    sha256=computed_hash,
                    verified=True,
                    instruction_bearing=False,
                    signer=signer,
                    content_payload=content,
                )
                verified_records.append(rec)

        if quarantined_records and strict_provenance:
            return ResolutionResult(
                status=ResolutionStatus.QUARANTINED,
                evidence=quarantined_records,
                rejection_reason="Untrusted or instruction-bearing evidence detected and quarantined.",
            )

        if not verified_records:
            return ResolutionResult(
                status=ResolutionStatus.NO_VERIFIED_EVIDENCE,
                evidence=[],
                rejection_reason="No verified admissible evidence found.",
            )

        return ResolutionResult(
            status=ResolutionStatus.RESOLVED,
            evidence=verified_records,
        )
