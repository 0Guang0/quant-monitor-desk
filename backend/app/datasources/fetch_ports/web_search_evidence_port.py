"""Web search supplemental evidence fetch port (R3H-04 L3 mock).

reference_adoption:
  - ladder: L3_greenfield (mock stub; real search API deferred per user gate)
  - staging_shape: backend/app/evidence/manual_review_staging.py (architecture_only OpenBB widget)
Mock stub READY; output is manual-review staging only — never clean factual tables.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from backend.app.datasources.adapters.fetch_port import FetchPayload, PortError
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.normalizers.evidence_bundle import finalize_bundle, reject_over_cap
from backend.app.evidence.manual_review_staging import build_web_evidence_staging_bundle

MAX_QUERIES = 3
MAX_RESULTS = 10

QUERY_WHITELIST = frozenset(
    {
        "fed rate cut outlook 2024",
        "vix term structure supplement",
    }
)


def _reject_unknown_query(query: str) -> None:
    if query not in QUERY_WHITELIST:
        raise PortError("FAILED", f"query not in web_search whitelist: {query!r}")


@dataclass(frozen=True)
class WebSearchEvidenceMockFetchPort:
    """Deterministic mock web search evidence port (staging only, no network)."""

    queries: tuple[str, ...]
    max_results: int

    def _mock_results(self, query: str) -> list[dict[str, Any]]:
        return [
            {
                "title": f"Supplemental result for: {query[:40]}",
                "url": "https://example.com/evidence/1",
                "snippet": "Bounded supplemental web evidence snippet for manual review.",
            }
        ][: self.max_results]

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        reject_over_cap(value=len(self.queries), cap=MAX_QUERIES, label="max_queries")
        reject_over_cap(value=self.max_results, cap=MAX_RESULTS, label="max_results")
        query = req.instrument_id or (self.queries[0] if self.queries else "")
        if not query:
            raise PortError("FAILED", "missing instrument_id (query) for web_search mock fetch")
        _reject_unknown_query(query)

        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"web-search-mock-{uuid.uuid4().hex[:12]}"
        domain = req.data_domain or "supplemental_web_evidence"
        results = self._mock_results(query)
        bundle = build_web_evidence_staging_bundle(
            query=query,
            results=results,
            data_domain=domain,
            source_id="web_search",
            source_fetch_id=fetch_id,
            content_hash="pending",
            as_of_timestamp=retrieved_at,
            retrieved_at=retrieved_at,
        )
        bundle = finalize_bundle(bundle)
        content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=len(results))


def create_web_search_evidence_fetch_port(*, queries: tuple[str, ...], max_results: int):
    if len(queries) > MAX_QUERIES:
        raise PortError("FAILED", f"max {MAX_QUERIES} queries allowed, got {len(queries)}")
    reject_over_cap(value=max_results, cap=MAX_RESULTS, label="max_results")
    return WebSearchEvidenceMockFetchPort(queries=queries, max_results=max_results)
