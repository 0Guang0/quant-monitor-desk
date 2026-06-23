"""Build industry_chain_daily_snapshot rows from staged loader + Layer5 bars."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml
from backend.app.config import PROJECT_ROOT
from backend.app.layer3_chains.lineage import Layer3LineageBuilder
from backend.app.layer3_chains.loader import IndustryChainLoadResult
from backend.app.layer3_chains.models import (
    AnchorEntry,
    IndustryChainDailySnapshotRow,
    IndustryChainSnapshotBuildResult,
    Layer3LineageEnvelope,
    Layer5MappingView,
)

STAGED_LAYER3_L5_BARS_DIR = PROJECT_ROOT / "tests" / "fixtures" / "layer3_l5_staged_bars"

# ponytail: module-level helpers mirror loader.py; no extra abstraction layer;
# ceiling is single-file builder + thin Layer3LineageBuilder (L2 clone);
# each build() re-reads manifest — Batch 6 CLI batch rebuild may memoize (A6 NB-3).

_RULE_VERSION = "layer3_chain_staged_v1"
_CODE_VERSION = "layer3-staged-v1"


class Layer3SnapshotError(ValueError):
    """Invalid Layer 3 staged snapshot build."""


class IndustryChainSnapshotBuilder:
    """Join loader anchors with staged Layer5 bar fixture under as_of boundary."""

    def __init__(
        self,
        *,
        rule_version: str = _RULE_VERSION,
        code_version: str = _CODE_VERSION,
    ) -> None:
        self._lineage_builder = Layer3LineageBuilder()
        self._rule_version = rule_version
        self._code_version = code_version

    def build(
        self,
        *,
        load_result: IndustryChainLoadResult,
        as_of: datetime,
        trade_date: date,
        l5_bundle_dir: Path | None = None,
    ) -> IndustryChainSnapshotBuildResult:
        # ponytail: no ResourceGuard on 021 staged join; Batch 6 CLI / live ingest must hook guard
        root = _resolve_l5_bundle_root(l5_bundle_dir)
        manifest = _read_l5_manifest(root)
        fetch_ids, content_hashes = _manifest_provenance(manifest)

        snapshots: list[IndustryChainDailySnapshotRow] = []
        mapping_views: list[Layer5MappingView] = []
        lineage_envelopes: list[Layer3LineageEnvelope] = []

        for anchor in load_result.anchors:
            if anchor.event_only:
                # ponytail: event_only 不读 L5 bar，但 fetch/hash 仍取自同份 staged manifest
                # （021 无 loader provenance）；升级路径：022+ 从 bundle_manifest 取 anchor 级指纹
                snapshots.append(_event_only_snapshot(anchor, trade_date, as_of))
                lineage_envelopes.append(
                    _lineage_for_anchor(
                        self,
                        anchor=anchor,
                        as_of=as_of,
                        trade_date=trade_date,
                        window_start=as_of,
                        window_end=as_of,
                        source_dataset_ids=(f"staged:layer3_anchor:{anchor.anchor_id}",),
                        source_fetch_ids=fetch_ids,
                        source_content_hashes=content_hashes,
                        hash_inputs=(anchor.anchor_id, trade_date.isoformat()),
                    )
                )
                continue

            ticker = anchor.ticker or anchor.anchor_id
            anchor_cfg = _anchor_l5_config(manifest, ticker)
            bar = _bar_for_trade_date(anchor_cfg, trade_date, ticker)
            _reject_future_bar(as_of=as_of, anchor_id=anchor.anchor_id, bar=bar)

            bar_as_of = _parse_ts(bar["as_of_timestamp"])
            close = _parse_bar_numeric(bar["close"], ticker=ticker, field="close")
            volume = bar.get("volume")
            vol_f = (
                None
                if volume is None
                else _parse_bar_numeric(volume, ticker=ticker, field="volume")
            )
            inst_raw = anchor_cfg.get("instrument_id")
            if inst_raw is None or str(inst_raw) == "":
                raise Layer3SnapshotError(
                    f"missing instrument_id for anchor ticker {ticker!r}"
                )

            snapshots.append(
                IndustryChainDailySnapshotRow(
                    anchor_id=anchor.anchor_id,
                    trade_date=trade_date,
                    as_of_timestamp=as_of,
                    latest_price=close,
                    pct_change_1d=None,
                    volume=vol_f,
                    quality_flags=(),
                    source_validation_status=anchor.source_validation_status,
                )
            )
            mapping_views.append(
                Layer5MappingView(
                    instrument_id=str(inst_raw),
                    trade_date=trade_date,
                    close=close,
                    volume=vol_f,
                    as_of_timestamp=bar_as_of,
                )
            )
            lineage_envelopes.append(
                _lineage_for_anchor(
                    self,
                    anchor=anchor,
                    as_of=as_of,
                    trade_date=trade_date,
                    window_start=bar_as_of,
                    window_end=bar_as_of,
                    source_dataset_ids=(f"staged:layer5_bar:{ticker}",),
                    source_fetch_ids=fetch_ids,
                    source_content_hashes=content_hashes,
                    hash_inputs=(ticker, trade_date.isoformat(), str(close)),
                )
            )

        return IndustryChainSnapshotBuildResult(
            snapshots=tuple(snapshots),
            lineage_envelopes=tuple(lineage_envelopes),
            layer5_mapping_views=tuple(mapping_views),
        )


def _resolve_l5_bundle_root(l5_bundle_dir: Path | None) -> Path:
    root = (l5_bundle_dir or STAGED_LAYER3_L5_BARS_DIR).resolve()
    try:
        root.relative_to(PROJECT_ROOT.resolve())
    except ValueError as exc:
        raise Layer3SnapshotError(
            f"l5_bundle_dir must be under project root, got {root!s}"
        ) from exc
    return root


def _read_l5_manifest(root: Path) -> dict[str, Any]:
    manifest_path = root / "manifest.yaml"
    if not manifest_path.is_file():
        # ponytail: error embeds path for local ops; HTTP/CLI slice should redact (UF-2)
        raise Layer3SnapshotError(f"missing L5 manifest: {manifest_path}")
    try:
        # ponytail: no max_bytes cap; staged_fixture_only trust boundary (UF-3 / A6 NB-2)
        raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise Layer3SnapshotError(f"invalid yaml in L5 manifest: {manifest_path}") from exc
    if not isinstance(raw, dict):
        raise Layer3SnapshotError("L5 manifest root must be a mapping")
    mode = str(raw.get("source_mode", ""))
    if mode != "staged_fixture_only":
        raise Layer3SnapshotError(
            f"source_mode {mode!r} is not staged_fixture_only; "
            "non-staged L5 source is forbidden on 021"
        )
    return raw


def _manifest_provenance(manifest: dict[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    fetch_raw = manifest.get("source_fetch_ids", [])
    hash_raw = manifest.get("source_content_hashes", [])
    if not isinstance(fetch_raw, list) or not fetch_raw:
        raise Layer3SnapshotError("L5 manifest missing source_fetch_ids")
    if not isinstance(hash_raw, list) or not hash_raw:
        raise Layer3SnapshotError("L5 manifest missing source_content_hashes")
    return tuple(str(x) for x in fetch_raw), tuple(str(x) for x in hash_raw)


def _anchor_l5_config(manifest: dict[str, Any], ticker: str) -> dict[str, Any]:
    anchors = manifest.get("anchors")
    if not isinstance(anchors, dict):
        raise Layer3SnapshotError("L5 manifest missing anchors mapping")
    cfg = anchors.get(ticker)
    if not isinstance(cfg, dict):
        raise Layer3SnapshotError(f"missing L5 bar config for anchor ticker {ticker!r}")
    return cfg


_BAR_REQUIRED_KEYS = ("close", "as_of_timestamp")


def _bar_for_trade_date(
    anchor_cfg: dict[str, Any], trade_date: date, ticker: str
) -> dict[str, Any]:
    bars = anchor_cfg.get("bars", [])
    if not isinstance(bars, list):
        raise Layer3SnapshotError(f"bars for {ticker!r} must be a list")
    target = trade_date.isoformat()
    # ponytail: O(bars) linear scan; staged 子集单日 bar；生产化可加索引或 max_bars cap (A6 NB-2)
    for bar in bars:
        if not isinstance(bar, dict):
            continue
        if str(bar.get("trade_date", "")) == target:
            for key in _BAR_REQUIRED_KEYS:
                if key not in bar:
                    raise Layer3SnapshotError(
                        f"bar for {ticker!r} missing required field {key!r}"
                    )
            return bar
    raise Layer3SnapshotError(f"no L5 bar for {ticker!r} on trade_date={trade_date}")


def _parse_bar_numeric(value: object, *, ticker: str, field: str) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise Layer3SnapshotError(
            f"bar for {ticker!r} {field} must be numeric, got {value!r}"
        ) from exc


def _parse_ts(value: object) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value)
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise Layer3SnapshotError(
            f"timestamp must be timezone-aware, got naive {parsed!r}"
        )
    return parsed


def _reject_future_bar(*, as_of: datetime, anchor_id: str, bar: dict[str, Any]) -> None:
    visibility = _parse_ts(bar["as_of_timestamp"])
    if visibility > as_of:
        raise Layer3SnapshotError(
            f"future input blocked for {anchor_id!r}: "
            f"as_of_timestamp {visibility!s} > snapshot as_of {as_of!s}"
        )


def _event_only_snapshot(
    anchor: AnchorEntry, trade_date: date, as_of: datetime
) -> IndustryChainDailySnapshotRow:
    return IndustryChainDailySnapshotRow(
        anchor_id=anchor.anchor_id,
        trade_date=trade_date,
        as_of_timestamp=as_of,
        quality_flags=(),
        source_validation_status=anchor.source_validation_status,
    )


def _lineage_for_anchor(
    builder: IndustryChainSnapshotBuilder,
    *,
    anchor: AnchorEntry,
    as_of: datetime,
    trade_date: date,
    window_start: datetime,
    window_end: datetime,
    source_dataset_ids: tuple[str, ...],
    source_fetch_ids: tuple[str, ...],
    source_content_hashes: tuple[str, ...],
    hash_inputs: tuple[str, ...],
) -> Layer3LineageEnvelope:
    param_hash = Layer3LineageBuilder.parameter_hash_for(
        rule_version=builder._rule_version,
        inputs=hash_inputs,
    )
    return builder._lineage_builder.build(
        snapshot_id=f"l3-lineage-{anchor.anchor_id}-{trade_date.isoformat()}",
        snapshot_type="industry_chain_daily_snapshot",
        as_of=as_of,
        input_window_start=window_start,
        input_window_end=window_end,
        source_dataset_ids=source_dataset_ids,
        source_fetch_ids=source_fetch_ids,
        source_content_hashes=source_content_hashes,
        rule_version=builder._rule_version,
        parameter_hash=param_hash,
        code_version=builder._code_version,
    )
