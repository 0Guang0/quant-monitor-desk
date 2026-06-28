"""THS/iFinD authorization-gated fetch port (R3H-03).

L2 migrate from backend/app/datasources/adapters/qmt_xtdata.py auth-gated boundary pattern;
default authorization-disabled via license_gate.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from backend.app.datasources.adapters.fetch_port import FetchPayload, PortError
from backend.app.datasources.auth.license_gate import require_license_gate
from backend.app.datasources.fetch_result import FetchRequest
from backend.app.datasources.normalizers.cn_market import build_cn_market_evidence_bundle
from backend.app.datasources.normalizers.evidence_bundle import finalize_bundle, reject_over_cap

MAX_ROWS = 5


@dataclass(frozen=True)
class ThsIfindMockFetchPort:
    concepts: Sequence[str]
    max_rows: int

    def fetch_payload(self, req: FetchRequest) -> FetchPayload:
        require_license_gate("ths_ifind")
        reject_over_cap(value=self.max_rows, cap=MAX_ROWS)
        concept = req.instrument_id or (self.concepts[0] if self.concepts else "")
        if not concept:
            raise PortError("FAILED", "missing instrument_id for ths_ifind fetch")

        retrieved_at = datetime.now(UTC).isoformat()
        fetch_id = f"ifind-mock-{concept}-{uuid.uuid4().hex[:12]}"
        filings = [
            {
                "filing_id": f"ifind-{idx}",
                "instrument_id": concept,
                "title": f"concept-theme-{idx}",
                "observation_date": retrieved_at[:10],
                "source_used": "ths_ifind",
            }
            for idx in range(min(self.max_rows, 2))
        ]
        bundle = build_cn_market_evidence_bundle(
            filings=filings,
            data_domain=req.data_domain or "concept_theme",
            source_id="ths_ifind",
            source_fetch_id=fetch_id,
            content_hash="pending",
            as_of_timestamp=retrieved_at,
            retrieved_at=retrieved_at,
        )
        bundle = finalize_bundle(bundle)
        content = json.dumps(bundle, ensure_ascii=False, default=str).encode("utf-8")
        return FetchPayload(content=content, file_type="json", row_count=len(filings))


def create_ths_ifind_fetch_port(*, concepts: Sequence[str], max_rows: int):
    return ThsIfindMockFetchPort(concepts=concepts, max_rows=max_rows)
