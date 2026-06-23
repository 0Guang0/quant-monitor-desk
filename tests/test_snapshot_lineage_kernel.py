"""快照血缘共享内核测试。

覆盖范围：core/snapshot_lineage 的参数哈希、字段校验、
source_dataset_id 拒绝规则与 DB 行序列化。
"""

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
    """覆盖范围：parameter_hash_for 的稳定性
    测试对象：parameter_hash_for
    目的/目标：相同 rule_version 与 inputs 应产出相同 64 位十六进制摘要
    验证点：两次调用结果相等且长度为 64
    失败含义：血缘 parameter_hash 漂移，增量重建无法判断输入是否变化
    """
    h1 = parameter_hash_for(rule_version="v1", inputs=("a", "b"))
    h2 = parameter_hash_for(rule_version="v1", inputs=("a", "b"))
    assert h1 == h2
    assert len(h1) == 64


def test_validate_source_dataset_ids_rejects_agent_outputs():
    """覆盖范围：来源数据集标识合法性
    测试对象：validate_source_dataset_ids
    目的/目标：代理生成的伪数据集标识不得冒充事实行情来源
    验证点：agent_summary 前缀 → ValueError 且含 agent outputs
    失败含义：代理文本可写入血缘来源字段，事实与解释边界失守
    """
    with pytest.raises(ValueError, match="agent outputs"):
        validate_source_dataset_ids(("agent_summary:foo",))


def test_assert_lineage_fields_complete_requires_core_fields():
    """覆盖范围：血缘信封必填字段完整性
    测试对象：assert_lineage_fields_complete
    目的/目标：缺核心字段时 fail-closed，完整信封应通过
    验证点：完整 _StubEnvelope 通过；source_fetch_ids=None 抛 ValueError
    失败含义：残缺血缘可落库，下游审计无法追溯抓取批次
    """
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
    """覆盖范围：血缘记录写入 DB 的 tuple 映射
    测试对象：lineage_row_to_db_tuple
    目的/目标：snapshot_id、layer_id 与 JSON 列按契约序列化
    验证点：row[0]=snap-1；row[2]=layer2；source_fetch_ids JSON 含 fetch-1
    失败含义：持久化列错位或 JSON 未序列化，写入 axis_snapshot_lineage 会失败
    """
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
