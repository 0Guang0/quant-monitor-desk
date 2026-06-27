"""Official macro evidence normalizer (R3H-01 G10)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION = "official_macro_evidence_v1"


class OfficialMacroEvidenceError(ValueError):
    """Fred / official-macro evidence bundle is invalid or incomplete."""


def _normalize_observation(row: dict[str, Any]) -> dict[str, Any]:
    obs_date = str(row.get("observation_date") or row.get("date") or "")
    return {
        "series_id": str(row.get("series_id") or ""),
        "observation_date": obs_date,
        "value": row.get("value"),
    }


def fred_observations_from_live_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten fred_live_fetch_evidence series[].rows into canonical observations."""
    observations: list[dict[str, Any]] = []
    for series in payload.get("series") or []:
        series_id = str(series.get("series_id") or "")
        for row in series.get("rows") or []:
            observations.append(
                _normalize_observation({**row, "series_id": row.get("series_id") or series_id})
            )
    return observations


def build_fred_evidence_bundle(
    *,
    observations: list[dict[str, Any]],
    series_id: str,
    source_fetch_id: str,
    content_hash: str,
    as_of_timestamp: str,
    retrieved_at: str | None = None,
    source_id: str = "fred",
) -> dict[str, Any]:
    norm_obs = [_normalize_observation(obs) for obs in observations]
    if not norm_obs:
        raise OfficialMacroEvidenceError("fred evidence bundle requires observations")
    return {
        "schema_version": OFFICIAL_MACRO_EVIDENCE_SCHEMA_VERSION,
        "series_id": series_id,
        "source_id": source_id,
        "observations": norm_obs,
        "source_fetch_id": source_fetch_id,
        "content_hash": content_hash,
        "as_of_timestamp": as_of_timestamp,
        "retrieved_at": retrieved_at or as_of_timestamp,
    }


def read_fred_evidence_bundle(path: Path | str) -> dict[str, Any]:
    """Read fred_evidence.json and return canonical official_macro_evidence_v1 shape."""
    evidence_path = Path(path)
    if evidence_path.is_dir():
        evidence_path = evidence_path / "fred_evidence.json"
    if not evidence_path.is_file():
        raise OfficialMacroEvidenceError(f"missing fred evidence: {evidence_path}")
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    observations = [_normalize_observation(obs) for obs in payload.get("observations") or []]
    if not observations:
        raise OfficialMacroEvidenceError("fred evidence bundle has no observations")
    return build_fred_evidence_bundle(
        observations=observations,
        series_id=str(payload.get("series_id") or observations[0].get("series_id") or "DGS10"),
        source_id=str(payload.get("source_id") or "fred"),
        source_fetch_id=str(payload.get("source_fetch_id") or "fred-unknown"),
        content_hash=str(payload.get("content_hash") or "fred-unknown-hash"),
        as_of_timestamp=str(payload.get("as_of_timestamp") or payload.get("retrieved_at") or ""),
        retrieved_at=str(payload.get("retrieved_at") or payload.get("as_of_timestamp") or ""),
    )


def write_fred_evidence_bundle(out_dir: Path | str, bundle: dict[str, Any]) -> Path:
    """Write canonical fred_evidence.json under out_dir."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    canonical = build_fred_evidence_bundle(
        observations=bundle.get("observations") or [],
        series_id=str(bundle.get("series_id") or "DGS10"),
        source_id=str(bundle.get("source_id") or "fred"),
        source_fetch_id=str(bundle.get("source_fetch_id") or "fred-unknown"),
        content_hash=str(bundle.get("content_hash") or "fred-unknown-hash"),
        as_of_timestamp=str(
            bundle.get("as_of_timestamp") or bundle.get("retrieved_at") or "1970-01-01T00:00:00Z"
        ),
        retrieved_at=str(bundle.get("retrieved_at") or bundle.get("as_of_timestamp") or None),
    )
    (out_dir / "fred_evidence.json").write_text(
        json.dumps(canonical, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return out_dir.resolve()


def materialize_fred_evidence_from_live(
    live_evidence_path: Path | str,
    out_dir: Path | str,
) -> Path:
    """Convert fred_live_fetch_evidence.json into promote-ready fred_evidence.json."""
    live_evidence_path = Path(live_evidence_path)
    if not live_evidence_path.is_file():
        raise OfficialMacroEvidenceError(f"live evidence file missing: {live_evidence_path}")
    payload = json.loads(live_evidence_path.read_text(encoding="utf-8"))
    observations = fred_observations_from_live_payload(payload)
    if not observations:
        raise OfficialMacroEvidenceError(f"no observations in {live_evidence_path}")
    series_block = (payload.get("series") or [{}])[0]
    as_of = str(
        series_block.get("as_of_timestamp")
        or series_block.get("retrieved_at")
        or "2026-06-27T00:00:00Z"
    )
    bundle = build_fred_evidence_bundle(
        observations=observations,
        series_id=str(observations[0].get("series_id") or "DGS10"),
        source_fetch_id=str(series_block.get("source_fetch_id") or "fred-live"),
        content_hash=str(series_block.get("content_hash") or "fred-live-hash"),
        as_of_timestamp=as_of,
        retrieved_at=as_of,
    )
    return write_fred_evidence_bundle(out_dir, bundle)
