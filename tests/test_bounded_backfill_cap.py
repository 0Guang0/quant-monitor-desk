"""R3-DCP-09 bounded backfill cap contract and shard planner tests."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
import yaml

from backend.app.sync.jobs import (
    ABSOLUTE_MAX_BACKFILL_SHARDS,
    BackfillShardCapExceededError,
    DEFAULT_MAX_BACKFILL_SHARDS,
    ECO_MAX_BACKFILL_DAYS_PER_TASK,
    load_bounded_backfill_cap,
    plan_backfill_shards,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CAP_YAML = PROJECT_ROOT / "specs/contracts/bounded_backfill_cap.yaml"


def test_load_bounded_backfill_cap_reads_ssot() -> None:
    """覆盖范围：bounded backfill cap YAML 契约
    测试对象：load_bounded_backfill_cap
    目的/目标：ADR-030 双层 cap 须机器可读 SSOT
    验证点：default_max_backfill_shards=3；absolute_max_backfill_shards=12
    失败含义：cap 契约缺失则 CLI/runner 无法 fail-closed
    """
    doc = load_bounded_backfill_cap()
    caps = doc["caps"]
    assert caps["eco_max_backfill_days_per_task"] == ECO_MAX_BACKFILL_DAYS_PER_TASK
    assert caps["default_max_backfill_shards"] == DEFAULT_MAX_BACKFILL_SHARDS
    assert caps["absolute_max_backfill_shards"] == ABSOLUTE_MAX_BACKFILL_SHARDS


def test_plan_backfill_shards_respects_max_shards_fail_closed() -> None:
    """覆盖范围：超 max_shards 日期窗默认 fail-closed
    测试对象：plan_backfill_shards(..., max_shards=3)
    目的/目标：无 --truncate-to-cap 时不得 silent 扩窗
    验证点：64 天窗 + max_shards=3 抛 BackfillShardCapExceededError
    失败含义：operator 可无意触发超 cap FullLoad
    """
    start = date(2026, 1, 1)
    end = date(2026, 5, 1)
    with pytest.raises(BackfillShardCapExceededError):
        plan_backfill_shards(start, end, max_shards=3)


def test_plan_backfill_shards_respects_max_shards_truncate() -> None:
    """覆盖范围：显式 truncate_to_cap 截断日期窗
    测试对象：plan_backfill_shards(..., max_shards=3, truncate_to_cap=True)
    目的/目标：--truncate-to-cap 可审计地缩小 end
    验证点：shard 数≤3；末片 end 不晚于原 end
    失败含义：truncate 标志无效，cap 策略名存实亡
    """
    start = date(2026, 1, 1)
    end = date(2026, 5, 1)
    shards = plan_backfill_shards(start, end, max_shards=3, truncate_to_cap=True)
    assert len(shards) <= 3
    assert all((e - s).days + 1 <= ECO_MAX_BACKFILL_DAYS_PER_TASK for _tid, s, e in shards)
    assert shards[-1][2] <= end


def test_bounded_backfill_cap_yaml_indexed() -> None:
    """覆盖范围：cap 契约文件存在且 version 字段
    测试对象：specs/contracts/bounded_backfill_cap.yaml
    目的/目标：loop_maintain / docs index 可发现本契约
    验证点：version=v1；owner=r3-dcp-09
    失败含义：契约未入库，CI 无法绑定 ADR-030
    """
    raw = yaml.safe_load(CAP_YAML.read_text(encoding="utf-8"))
    assert raw["version"] == "v1"
    assert raw["owner"] == "r3-dcp-09"
