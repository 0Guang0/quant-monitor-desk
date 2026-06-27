"""R3G-01 rehearsal loader tests — bounded DataBundle from staged evidence."""

from __future__ import annotations

import pytest

from backend.app.ops.sandbox_clean_write.rehearsal_loader import (
    RehearsalLoaderError,
    load_rehearsal_bundle,
)
from backend.app.ops.sandbox_clean_write.rehearsal_plan import load_candidate_set
from tests.contract_gate_support import PROJECT_ROOT


def _candidate(source_id: str):
    return next(c for c in load_candidate_set("r3g_p0") if c.source_id == source_id)


def test_rehearsalLoader_baostockFixture_withinCaps() -> None:
    """覆盖范围：baostock 有界 DataBundle 加载
    测试对象：load_rehearsal_bundle（baostock / good_bundle 夹具）
    目的/目标：排练 loader 从 staged 证据加载确定性 bundle，禁止 broad universe
    验证点：raw_row_count>0；symbols 不超过契约 cap；含 source_fetch 或 content_hash 线索
    失败含义：loader 无法从证据构建 bundle，9.4 runner 无输入
    """
    bundle = load_rehearsal_bundle(_candidate("baostock"), dry_run=True)
    assert bundle.raw_row_count > 0
    assert len(bundle.symbols_or_series) <= 3
    assert bundle.source_id == "baostock"
    assert bundle.evidence_dir.is_dir()


def test_rehearsalLoader_cninfoMetadata_only() -> None:
    """覆盖范围：cninfo metadata-only bundle
    测试对象：load_rehearsal_bundle（cninfo / staged_pilot_v3 compliant）
    目的/目标：cninfo 排练仅 metadata，非 PDF 全量
    验证点：domain==cn_announcements；staged_row_count 有界
    失败含义：cninfo loader 误扩为 broad 下载语义
    """
    bundle = load_rehearsal_bundle(_candidate("cninfo"), dry_run=True)
    assert bundle.domain == "cn_announcements"
    assert bundle.staged_row_count == 5
    assert bundle.raw_row_count == 5
    assert len(bundle.symbols_or_series) <= 3


def test_rehearsalLoader_fredAuthorized_sample() -> None:
    """覆盖范围：授权 fred 样本 bundle
    测试对象：load_rehearsal_bundle（fred / fred_sandbox complete）
    目的/目标：fred 排练须从授权样本证据加载 macro_series
    验证点：domain==macro_series；source_fetch_ids 非空
    失败含义：fred 排练无法加载授权样本证据
    """
    bundle = load_rehearsal_bundle(_candidate("fred"), dry_run=True)
    assert bundle.domain == "macro_series"
    assert bundle.source_fetch_ids


def test_rehearsalLoader_reusesContractCapsNotMagicNumber() -> None:
    """覆盖范围：loader cap 复用 plan/契约而非魔数
    测试对象：load_rehearsal_bundle 入参校验
    目的/目标：loader 与 validate_source_caps 一致（R3G-REP-P1-08）
    验证点：超契约 cap 的 baostock 候选抛 RehearsalLoaderError（与 plan 同源消息）
    失败含义：loader 硬编码 >3 与契约漂移
    """
    from dataclasses import replace

    wide = replace(
        _candidate("baostock"),
        symbols_or_series=("sh.600519", "sh.600000", "sz.000001", "sz.000002"),
    )
    with pytest.raises(RehearsalLoaderError, match="max 3 symbols"):
        load_rehearsal_bundle(wide, dry_run=True)


def test_rehearsalLoader_rejectsBroadUniverse() -> None:
    """覆盖范围：loader 拒绝超 cap 符号列表
    测试对象：load_rehearsal_bundle 入参校验
    目的/目标：禁止默认 DB 路径与 broad universe
    验证点：4+ 非 fred 符号须 RehearsalLoaderError
    失败含义：loader 接受 broad universe，违反 R3G cap
    """
    from dataclasses import replace

    wide = replace(
        _candidate("baostock"),
        symbols_or_series=("sh.600519", "sh.600000", "sz.000001", "sz.000002"),
    )
    with pytest.raises(RehearsalLoaderError):
        load_rehearsal_bundle(wide, dry_run=True)


def test_rehearsalLoader_noDefaultProductionDbPath() -> None:
    """覆盖范围：loader 不隐式解析生产 DB
    测试对象：FIXTURE_EVIDENCE_DIRS 与 dry_run 路径
    目的/目标：输入为证据目录而非生产 duckdb 默认路径
    验证点：bundle.evidence_dir 在 tests/fixtures 或显式传入，非 DATA_ROOT duckdb
    失败含义：loader 绑定生产 DB 路径，sandbox-only 边界失效
    """
    bundle = load_rehearsal_bundle(_candidate("baostock"), dry_run=True)
    assert "fixtures" in str(bundle.evidence_dir).replace("\\", "/")
    prod_marker = str(PROJECT_ROOT / "data" / "duckdb" / "quant_monitor.duckdb")
    assert prod_marker not in str(bundle.evidence_dir)
