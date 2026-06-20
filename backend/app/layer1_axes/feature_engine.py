"""Layer 1 axis feature computation and snapshot rows."""

from __future__ import annotations

import math
import statistics
import uuid
from collections.abc import Sequence
from datetime import datetime

from backend.app.core.resource_guard import Decision, ResourceGuard
from backend.app.layer1_axes.models import AxisObservation, FeatureSnapshotRow

ROBUST_Z_SCALE = 0.6745

WINDOW_POLICY = {
    "daily": (756, 500),
    "weekly": (260, 156),
    "monthly": (120, 60),
    "quarterly": (60, 40),
}


class Layer1SnapshotError(ValueError):
    """Invalid snapshot inputs (e.g. no_future_data violation)."""


class ResourceGuardBlockedError(RuntimeError):
    """ResourceGuard blocked feature computation."""


class AxisFeatureEngine:
    """Compute Layer 1 standardized feature snapshots (module doc §7–8).

    ResourceGuard: only HARD_STOP and PAUSE block compute; WARN is logged upstream
    and compute proceeds (eco profile default per GLOBAL_RESOURCE_LIMITS).
    """

    def __init__(
        self,
        *,
        resource_guard: ResourceGuard | None = None,
        frequency: str = "daily",
        window_len: int | None = None,
        min_obs_required: int | None = None,
    ) -> None:
        self._guard = resource_guard or ResourceGuard()
        self._frequency = frequency.lower()
        default_len, default_min = WINDOW_POLICY.get(self._frequency, WINDOW_POLICY["daily"])
        self._window_len = window_len if window_len is not None else default_len
        self._min_obs = min_obs_required if min_obs_required is not None else default_min

    def compute_features(
        self,
        *,
        as_of: datetime,
        observations: Sequence[AxisObservation],
        history: Sequence[AxisObservation] | None = None,
    ) -> list[FeatureSnapshotRow]:
        decision, _reason = self._guard.check()
        if decision in (Decision.HARD_STOP, Decision.PAUSE):
            raise ResourceGuardBlockedError(f"resource guard blocked: {decision.value}")

        hist = list(history or observations)
        rows: list[FeatureSnapshotRow] = []
        for obs in observations:
            if obs.publish_timestamp > as_of:
                raise Layer1SnapshotError(
                    f"future input: publish {obs.publish_timestamp} > as_of {as_of}"
                )
            past = [
                h
                for h in hist
                if h.indicator_id == obs.indicator_id and h.publish_timestamp <= as_of
            ]
            past.sort(key=lambda h: h.publish_timestamp)
            if self._window_len and len(past) > self._window_len:
                past = past[-self._window_len :]
            rows.append(self._compute_one(as_of=as_of, obs=obs, past=past))
        return rows

    def _compute_one(
        self,
        *,
        as_of: datetime,
        obs: AxisObservation,
        past: list[AxisObservation],
    ) -> FeatureSnapshotRow:
        values = [p.raw_value for p in past if p.raw_value is not None]
        valid_count = len(values)
        min_required = self._min_obs
        coverage = valid_count / self._window_len if self._window_len else 0.0
        flags = list(obs.quality_flags)

        if obs.source_switched:
            flags.append("SOURCE_SWITCHED")

        stale_reason = (
            obs.fallback_policy if obs.source_switched and obs.fallback_policy else None
        )

        if valid_count < min_required:
            flags.append("INSUFFICIENT_HISTORY")
            return FeatureSnapshotRow(
                feature_id=str(uuid.uuid4()),
                indicator_id=obs.indicator_id,
                as_of_timestamp=as_of,
                raw_value=obs.raw_value,
                z_score=None,
                robust_z_score=None,
                percentile_rank=None,
                percentile_left_tail=None,
                percentile_right_tail=None,
                raw_delta_abs=None,
                raw_delta_pct=None,
                raw_delta_log=None,
                z_score_delta=None,
                percentile_delta=None,
                level_state=None,
                delta_state=None,
                state_bucket="insufficient_history",
                extreme_flags="",
                standardize_method="rolling",
                delta_method="pct",
                window_len=self._window_len,
                window_unit=self._frequency,
                min_obs_required=min_required,
                valid_obs_count=valid_count,
                coverage_ratio=coverage,
                quality_flags=tuple(dict.fromkeys(flags)),
                stale_reason=stale_reason,
            )

        mean = statistics.mean(values)
        stdev = statistics.pstdev(values) if len(values) > 1 else 0.0
        median = statistics.median(values)
        mad = statistics.median([abs(v - median) for v in values])
        z_score = (
            (obs.raw_value - mean) / stdev if stdev > 0 and obs.raw_value is not None else None
        )

        robust_z: float | None = None
        if mad > 0 and obs.raw_value is not None:
            robust_z = ROBUST_Z_SCALE * (obs.raw_value - median) / mad
        elif obs.raw_value is not None:
            flags.append("ROBUST_Z_UNAVAILABLE")

        sorted_vals = sorted(values)
        rank = _percentile_rank(obs.raw_value, sorted_vals) if obs.raw_value is not None else None
        left_tail = rank
        right_tail = 1.0 - rank if rank is not None else None

        prev = past[-2].raw_value if len(past) >= 2 else None
        delta_abs = obs.raw_value - prev if obs.raw_value is not None and prev is not None else None
        delta_pct = (delta_abs / prev) if delta_abs is not None and prev not in (0, None) else None
        delta_log = (
            math.log(obs.raw_value / prev)
            if obs.raw_value and prev and obs.raw_value > 0 and prev > 0
            else None
        )

        state_bucket = _state_bucket(z_score, rank)

        return FeatureSnapshotRow(
            feature_id=str(uuid.uuid4()),
            indicator_id=obs.indicator_id,
            as_of_timestamp=as_of,
            raw_value=obs.raw_value,
            z_score=z_score,
            robust_z_score=robust_z,
            percentile_rank=rank,
            percentile_left_tail=left_tail,
            percentile_right_tail=right_tail,
            raw_delta_abs=delta_abs,
            raw_delta_pct=delta_pct,
            raw_delta_log=delta_log,
            z_score_delta=None,
            percentile_delta=None,
            level_state=state_bucket,
            delta_state="steady",
            state_bucket=state_bucket,
            extreme_flags="",
            standardize_method="rolling",
            delta_method="pct",
            window_len=self._window_len,
            window_unit=self._frequency,
            min_obs_required=min_required,
            valid_obs_count=valid_count,
            coverage_ratio=coverage,
            quality_flags=tuple(dict.fromkeys(flags)),
            stale_reason=stale_reason,
        )


def _percentile_rank(value: float, sorted_vals: list[float]) -> float:
    below = sum(1 for v in sorted_vals if v < value)
    equal = sum(1 for v in sorted_vals if v == value)
    return (below + 0.5 * equal) / len(sorted_vals)


def _state_bucket(z_score: float | None, percentile: float | None) -> str:
    if percentile is not None:
        if percentile >= 0.95:
            return "extreme_high"
        if percentile <= 0.05:
            return "extreme_low"
        if percentile >= 0.75:
            return "elevated"
        if percentile <= 0.25:
            return "depressed"
    if z_score is not None:
        if z_score >= 2:
            return "elevated"
        if z_score <= -2:
            return "depressed"
    return "normal"
