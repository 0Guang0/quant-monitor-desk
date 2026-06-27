"""Bridge staged-pilot / FRED live evidence into promote-ready rehearsal bundles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.app.config import PROJECT_ROOT
from backend.app.datasources.normalizers.official_macro import (
    OfficialMacroEvidenceError,
    materialize_fred_evidence_from_live,
)
from backend.app.datasources.normalizers.official_macro import (
    fred_observations_from_live_payload as _normalize_fred_live_observations,
)


class LiveEvidenceBridgeError(RuntimeError):
    """Live evidence could not be normalized for promote loader."""


def _write_sandbox_rehearsal_gate_sidecars(out_dir: Path) -> None:
    """DH gate files required for isolated pilot promote (not production)."""
    (out_dir / "pilot_v2_closeout.json").write_text(
        json.dumps(
            {
                "sandbox_clean_write_rehearsal": True,
                "production_live_readiness_claim": False,
                "live_wire_promote": True,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out_dir / "validation_report_summary.json").write_text(
        json.dumps({"allow_clean_write": True}, indent=2) + "\n",
        encoding="utf-8",
    )


def _resolve_raw_path(path: str | Path) -> Path:
    candidate = Path(path)
    if not candidate.is_file():
        candidate = PROJECT_ROOT / path
    if not candidate.is_file():
        raise LiveEvidenceBridgeError(f"raw evidence file missing: {path}")
    return candidate.resolve()


def baostock_rows_from_staged_raw(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert BaostockStagedFetchPort array rows into bars.json row dicts."""
    default_symbol = str(payload.get("symbol") or "")
    out: list[dict[str, Any]] = []
    for row in payload.get("rows") or []:
        if isinstance(row, list) and len(row) >= 6:
            symbol = str(row[1]) if len(row) > 1 else default_symbol
            out.append(
                {
                    "symbol": symbol,
                    "instrument_id": symbol,
                    "trade_date": str(row[0]),
                    "open": float(row[2]),
                    "high": float(row[3]),
                    "low": float(row[4]),
                    "close": float(row[5]),
                    "volume": int(float(row[6])) if len(row) > 6 else 0,
                }
            )
        elif isinstance(row, dict):
            symbol = str(row.get("symbol") or row.get("instrument_id") or default_symbol)
            out.append({**row, "symbol": symbol, "instrument_id": symbol})
    return out


def materialize_baostock_promote_evidence(
    staged_evidence_dir: Path | str,
    out_dir: Path | str,
) -> Path:
    """Write bars.json + raw_evidence_manifest.json from staged pilot v2 capture dir."""
    staged_evidence_dir = Path(staged_evidence_dir)
    out_dir = Path(out_dir)
    manifest_path = staged_evidence_dir / "raw_evidence_manifest_v2.json"
    if not manifest_path.is_file():
        raise LiveEvidenceBridgeError(f"missing {manifest_path.name} in {staged_evidence_dir}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    all_bars: list[dict[str, Any]] = []
    seen: set[str] = set()
    for fetch in manifest.get("fetches") or []:
        fr = fetch.get("fetch_result") or {}
        for raw_path in fr.get("raw_file_paths") or []:
            key = str(raw_path)
            if key in seen:
                continue
            seen.add(key)
            payload = json.loads(_resolve_raw_path(raw_path).read_text(encoding="utf-8"))
            all_bars.extend(baostock_rows_from_staged_raw(payload))
    for entry in manifest.get("manifest_entries") or []:
        for rel in entry.get("relative_paths") or []:
            key = str(rel)
            if key in seen:
                continue
            seen.add(key)
            payload = json.loads(_resolve_raw_path(rel).read_text(encoding="utf-8"))
            all_bars.extend(baostock_rows_from_staged_raw(payload))
    if not all_bars:
        raise LiveEvidenceBridgeError("staged v2 manifest produced zero baostock bars")
    deduped: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str]] = set()
    for bar in all_bars:
        key = (str(bar.get("instrument_id") or bar.get("symbol")), str(bar.get("trade_date")))
        if key in seen_keys:
            continue
        seen_keys.add(key)
        deduped.append(bar)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "bars.json").write_text(
        json.dumps({"rows": deduped}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (out_dir / "raw_evidence_manifest.json").write_text(
        json.dumps({"fetches": manifest.get("fetches") or []}, indent=2) + "\n",
        encoding="utf-8",
    )
    _write_sandbox_rehearsal_gate_sidecars(out_dir)
    return out_dir.resolve()


def fred_observations_from_live_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten fred_live_fetch_evidence series[].rows into loader observations."""
    return _normalize_fred_live_observations(payload)


def materialize_fred_promote_evidence(
    live_evidence_path: Path | str,
    out_dir: Path | str,
) -> Path:
    """Write fred_evidence.json from fred sandbox live fetch evidence."""
    try:
        return materialize_fred_evidence_from_live(
            _resolve_raw_path(live_evidence_path),
            out_dir,
        )
    except OfficialMacroEvidenceError as exc:
        raise LiveEvidenceBridgeError(str(exc)) from exc
