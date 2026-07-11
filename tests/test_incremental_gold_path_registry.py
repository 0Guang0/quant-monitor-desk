"""Incremental gold-path registry + ADR-009 clean routing."""

from __future__ import annotations

import pytest

from backend.app.datasources.live_prod_source_tiers import INCREMENTAL_GOLD_PATH_SOURCE_IDS
from backend.app.ops.sandbox_clean_write.clean_write_targets import resolve_clean_write_target
from backend.app.sync.incremental_source_registry import (
    UnknownIncrementalGoldPathSourceError,
    iter_incremental_gold_path_sources,
    resolve_incremental_gold_path,
)

# ADR-009 canonical domain per source_id
ADR028_CANONICAL = {
    "baostock": "cn_equity_daily_bar",
    "mootdx": "cn_equity_daily_bar",
    "fred": "macro_series",
    "us_treasury": "us_treasury_yield_curve",
    "bis": "central_bank_policy",
    "world_bank": "development_indicator",
    "cftc_cot": "cot_positioning",
    "cninfo": "cn_announcements",
    "sec_edgar": "us_filings",
    "alpha_vantage": "us_equity_daily_bar",
    "deribit": "crypto_options_surface",
}

ADR028_CLEAN_TABLE = {
    "cn_equity_daily_bar": "security_bar_1d",
    "macro_series": "axis_observation",
    "us_treasury_yield_curve": "axis_observation",
    "central_bank_policy": "axis_observation",
    "development_indicator": "axis_observation",
    "cot_positioning": "axis_observation",
    "cn_announcements": "cn_announcement_clean",
    "us_filings": "us_disclosure_clean",
    "crypto_options_surface": "crypto_derivative_clean",
}


def test_incrementalGoldPathRegistry_coversAllGoldPathSources() -> None:
    """覆盖范围：11 个 incremental 金路径源登记
    测试对象：iter_incremental_gold_path_sources / INCREMENTAL_GOLD_PATH_SOURCE_IDS
    目的/目标：registry 与 live_prod_source_tiers 金路径集合一一对应
    验证点：数量 11；集合相等
    失败含义：漏源则 DCP-05 无法声称 11/11 clean 路径
    """
    registered = frozenset(iter_incremental_gold_path_sources())
    assert registered == INCREMENTAL_GOLD_PATH_SOURCE_IDS
    assert len(registered) == 11


@pytest.mark.parametrize("source_id,canonical_domain", list(ADR028_CANONICAL.items()))
def test_incrementalGoldPathRegistry_canonicalDomainMatchesAdr028(
    source_id: str, canonical_domain: str
) -> None:
    """覆盖范围：每源 canonical domain
    测试对象：resolve_incremental_gold_path
    目的/目标：与 ADR-009 矩阵一致
    验证点：canonical_domain 字段
    失败含义：域错位则 watermark/clean 写错表
    """
    entry = resolve_incremental_gold_path(source_id)
    assert entry.canonical_domain == canonical_domain


@pytest.mark.parametrize(
    "canonical_domain,expected_table",
    list(ADR028_CLEAN_TABLE.items()),
)
def test_incrementalGoldPathRegistry_canonicalDomainResolvesCleanTable(
    canonical_domain: str, expected_table: str
) -> None:
    """覆盖范围：canonical domain → clean 表
    测试对象：resolve_clean_write_target
    目的/目标：11/11 路径均有 clean upsert 目标（S00）
    验证点：target_table；write_mode upsert_by_pk
    失败含义：域无 clean 路由则 incremental 只能写 staging
    """
    target = resolve_clean_write_target(canonical_domain)
    assert target.target_table == expected_table
    assert target.write_mode == "upsert_by_pk"


def test_incrementalGoldPathRegistry_unknownSource_raises() -> None:
    """覆盖范围：非金路径源负向
    测试对象：resolve_incremental_gold_path
    目的/目标：fail-closed
    验证点：UnknownIncrementalGoldPathSourceError
    失败含义：静默默认域会写错 clean 表
    """
    with pytest.raises(UnknownIncrementalGoldPathSourceError, match="akshare"):
        resolve_incremental_gold_path("akshare")
