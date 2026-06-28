"""Manual-review evidence staging (R3H-04 web_search path).

reference_adoption:
  - ladder: architecture_only
  - reference: agents-for-openbb/30-vanilla-agent-raw-widget-data (item.content separation)
  - reference: agents-for-openbb/40-vanilla-agent-dashboard-widgets (bounded table metadata)
  - forbidden: FastAPI/OpenAI/openbb_ai runtime import; agent output as fact source
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.app.datasources.normalizers.evidence_bundle import (
    attach_bundle_metadata,
    finalize_bundle,
)

WEB_EVIDENCE_STAGING_SCHEMA_VERSION = "web_evidence_staging_v1"

# OpenBB agents-for-openbb widget artifact field names (architecture_only; no runtime import).
OPENBB_WIDGET_ARTIFACT_KIND = "bounded_widget_summary"


class ManualReviewStagingError(ValueError):
    """Web evidence staging bundle is invalid or attempts clean promotion."""


def build_bounded_widget_artifact(
    *,
    widget_name: str,
    widget_id: str,
    results: list[dict[str, Any]],
    description: str = "Bounded supplemental web evidence for manual review",
) -> dict[str, Any]:
    """Mirror OpenBB widget JSON artifact shape: separated source rows + item.content summaries."""
    columns = ["title", "url", "snippet"]
    rows = [
        [str(row.get("title") or ""), str(row.get("url") or ""), str(row.get("snippet") or "")]
        for row in results
    ]
    items = [
        {
            "content": (
                f"{row.get('title') or 'untitled'}: "
                f"{str(row.get('snippet') or '')[:120]}"
            ).strip()
        }
        for row in results
    ]
    return {
        "artifact_kind": OPENBB_WIDGET_ARTIFACT_KIND,
        "source_data_separated": True,
        "widget_metadata": {
            "name": widget_name,
            "widget_id": widget_id,
            "description": description,
        },
        "items": items,
        "columns": columns,
        "rows": rows,
    }


def build_web_evidence_staging_bundle(
    *,
    query: str,
    results: list[dict[str, Any]],
    data_domain: str,
    source_fetch_id: str,
    content_hash: str,
    as_of_timestamp: str,
    retrieved_at: str | None = None,
    source_id: str = "web_search",
) -> dict[str, Any]:
    if not query.strip():
        raise ManualReviewStagingError("web evidence requires non-empty query")
    if not results:
        raise ManualReviewStagingError("web evidence requires at least one result")
    norm_results = [
        {
            "title": str(row.get("title") or ""),
            "url": str(row.get("url") or ""),
            "snippet": str(row.get("snippet") or ""),
        }
        for row in results
    ]
    widget_id = f"web-evidence-{source_fetch_id[:24]}"
    return {
        "schema_version": WEB_EVIDENCE_STAGING_SCHEMA_VERSION,
        "source_id": source_id,
        "data_domain": data_domain,
        "query": query,
        "results": norm_results,
        "evidence_artifact": build_bounded_widget_artifact(
            widget_name="Supplemental Web Evidence",
            widget_id=widget_id,
            results=norm_results,
        ),
        "need_human_review": True,
        "manual_review_state": "queued",
        "source_fetch_id": source_fetch_id,
        "content_hash": content_hash,
        "as_of_timestamp": as_of_timestamp,
        "retrieved_at": retrieved_at or as_of_timestamp,
    }


def read_web_evidence_staging_bundle(path: Path | str) -> dict[str, Any]:
    evidence_path = Path(path)
    if evidence_path.is_dir():
        evidence_path = evidence_path / "web_evidence_staging.json"
    if not evidence_path.is_file():
        raise ManualReviewStagingError(f"missing web evidence staging: {evidence_path}")
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    bundle = build_web_evidence_staging_bundle(
        query=str(payload.get("query") or ""),
        results=payload.get("results") or [],
        data_domain=str(payload.get("data_domain") or "supplemental_web_evidence"),
        source_id=str(payload.get("source_id") or "web_search"),
        source_fetch_id=str(payload.get("source_fetch_id") or "web-unknown"),
        content_hash=str(payload.get("content_hash") or "web-unknown-hash"),
        as_of_timestamp=str(payload.get("as_of_timestamp") or payload.get("retrieved_at") or ""),
        retrieved_at=str(payload.get("retrieved_at") or payload.get("as_of_timestamp") or ""),
    )
    return attach_bundle_metadata(bundle)


def write_web_evidence_staging_bundle(out_dir: Path | str, bundle: dict[str, Any]) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    canonical = build_web_evidence_staging_bundle(
        query=str(bundle.get("query") or ""),
        results=bundle.get("results") or [],
        data_domain=str(bundle.get("data_domain") or "supplemental_web_evidence"),
        source_id=str(bundle.get("source_id") or "web_search"),
        source_fetch_id=str(bundle.get("source_fetch_id") or "web-unknown"),
        content_hash=str(bundle.get("content_hash") or "web-unknown-hash"),
        as_of_timestamp=str(
            bundle.get("as_of_timestamp") or bundle.get("retrieved_at") or "1970-01-01T00:00:00Z"
        ),
        retrieved_at=str(bundle.get("retrieved_at") or bundle.get("as_of_timestamp") or None),
    )
    finalized = finalize_bundle(canonical)
    (out_dir / "web_evidence_staging.json").write_text(
        json.dumps(finalized, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return out_dir.resolve()


def stage_for_manual_review(bundle: dict[str, Any]) -> dict[str, Any]:
    """Return staging metadata; never promotes to clean factual tables."""
    if not bundle.get("need_human_review"):
        raise ManualReviewStagingError("web evidence must set need_human_review=true")
    if bundle.get("manual_review_state") != "queued":
        raise ManualReviewStagingError("web evidence must set manual_review_state=queued")
    artifact = bundle.get("evidence_artifact") or {}
    return {
        "staging_kind": "manual_review_evidence",
        "source_id": bundle.get("source_id"),
        "source_fetch_id": bundle.get("source_fetch_id"),
        "content_hash": bundle.get("content_hash"),
        "query": bundle.get("query"),
        "result_count": len(bundle.get("results") or []),
        "artifact_kind": artifact.get("artifact_kind"),
        "widget_name": (artifact.get("widget_metadata") or {}).get("name"),
        "need_human_review": True,
        "manual_review_state": "queued",
        "clean_write_permitted": False,
    }


def reject_clean_table_promotion(*, target_table: str) -> None:
    """ponytail: hard guard — web evidence never writes clean tables."""
    if target_table.strip():
        raise ManualReviewStagingError(
            f"web evidence cannot promote to clean table: {target_table!r}"
        )
