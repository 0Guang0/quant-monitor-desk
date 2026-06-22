"""覆盖范围：core/snapshot_lineage 共享内核；测试对象：校验与 DB tuple 映射；目的：三层层 lineage 去重后行为不变。"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from backend.app.core.snapshot_lineage import (
    LINEAGE_REQUIRED_FIELDS,
    assert_lineage_fields_complete,
    lineage_row_to_db_tuple,
    parameter_hash_for,
    validate_source_dataset_ids,
)


class _StubEnvelope:
    def __init__(self, **kwargs) -> None:
        for field in LINEAGE_REQUIRED_FIELDS:
            setattr(self, field, kwargs.get(field))


def test_parameter_hash_for_is_deterministic():
    """覆盖：parameter_hash_for；目的：同输入产生稳定 digest。"""
    h1 = parameter_hash_for(rule_version="v1", inputs=("a", "b"))
    h2 = parameter_hash_for(rule_version="v1", inputs=("a", "b"))
    assert h1 == h2
    assert len(h1) == 64


def test_validate_source_dataset_ids_rejects_agent_outputs():
    """覆盖：validate_source_dataset_ids；目的：拒绝 agent 伪装的 source_dataset_id。"""
    with pytest.raises(ValueError, match="agent outputs"):
        validate_source_dataset_ids(("agent_summary:foo",))


def test_assert_lineage_fields_complete_requires_core_fields():
    """覆盖：assert_lineage_fields_complete；目的：缺字段时 fail-closed。"""
    now = datetime.now(UTC)
    env = _StubEnvelope(
        snapshot_id="s1",
        snapshot_type="t",
        layer_id="layer1",
        as_of_timestamp=now,
        generated_at=now,
        input_data_window_start=now,
        input_data_window_end=now,
        source_dataset_ids=("raw:x",),
        source_fetch_ids=("f1",),
        source_content_hashes=("h1",),
        rule_version="r1",
        code_version="c1",
        parameter_hash="p1",
        resource_profile="eco",
        upstream_snapshot_ids=(),
        is_incremental=False,
        rebuild_reason=None,
    )
    assert_lineage_fields_complete(env)
    env.source_fetch_ids = None
    with pytest.raises(ValueError, match="source_fetch_ids"):
        assert_lineage_fields_complete(env)


def test_lineage_row_to_db_tuple_serializes_json_columns():
    """覆盖：lineage_row_to_db_tuple；目的：JSON 列与 layer_id 原样写入 tuple。"""
    now = datetime.now(UTC)
    env = _StubEnvelope(
        snapshot_id="snap-1",
        snapshot_type="axis_feature_snapshot",
        layer_id="layer2",
        as_of_timestamp=now,
        generated_at=now,
        input_data_window_start=now,
        input_data_window_end=now,
        source_dataset_ids=("raw:a",),
        source_fetch_ids=("fetch-1",),
        source_content_hashes=("hash-1",),
        rule_version="rule_v1",
        code_version="code_v1",
        parameter_hash="param",
        resource_profile="eco",
        upstream_snapshot_ids=("up-1",),
        is_incremental=True,
        rebuild_reason="test",
    )
    row = lineage_row_to_db_tuple(env)
    assert row[0] == "snap-1"
    assert row[2] == "layer2"
    assert '"fetch-1"' in row[8]
