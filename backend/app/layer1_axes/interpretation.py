"""Layer 1 interpretation snapshot builder."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime

from backend.app.layer1_axes.models import FeatureSnapshotRow, InterpretationSnapshotRow

FORBIDDEN_OUTPUT_TERMS = (
    "买入",
    "卖出",
    "加仓",
    "减仓",
    "入场",
    "出场",
    "信号",
)


class InterpretationRejectedError(ValueError):
    """Interpretation contains forbidden action semantics."""


class AxisInterpretationEngine:
    """Build human-readable interpretation snapshots without action terms."""

    def __init__(self, *, forbidden_terms: Sequence[str] | None = None) -> None:
        self._forbidden = tuple(forbidden_terms or FORBIDDEN_OUTPUT_TERMS)

    def build_interpretation(
        self,
        *,
        as_of: datetime,
        features: Sequence[FeatureSnapshotRow],
        templates: dict[str, str] | None = None,
    ) -> list[InterpretationSnapshotRow]:
        templates = templates or {}
        rows: list[InterpretationSnapshotRow] = []
        for feat in features:
            template = templates.get(
                feat.indicator_id,
                f"指标 {feat.indicator_id} 处于 {feat.state_bucket} 状态。",
            )
            needs_review = any(term in template for term in self._forbidden)
            if needs_review:
                for term in self._forbidden:
                    template = template.replace(term, "观察")
            rows.append(
                InterpretationSnapshotRow(
                    interpretation_id=str(uuid.uuid4()),
                    indicator_id=feat.indicator_id,
                    as_of_timestamp=as_of,
                    level_label=feat.level_state or feat.state_bucket,
                    change_label=feat.delta_state or "steady",
                    quality_label=",".join(feat.quality_flags) or "ok",
                    level_interpretation=template,
                    change_interpretation="变化平稳",
                    boundary_reminder="不构成交易动作",
                    warning_level="none",
                    warning_type="",
                    warning_reason_code="",
                    summary_sentence=template,
                    generated_by="layer1_interpretation_engine",
                    explanation_version="v1",
                    needs_human_review=needs_review,
                )
            )
        return rows

    def reject_if_forbidden(self, text: str) -> None:
        if any(term in text for term in self._forbidden):
            raise InterpretationRejectedError("interpretation contains forbidden action terms")
