"""M-G1-03 P1-05 — unified sync watermark entry."""

from __future__ import annotations

import pytest

from tests._m_g1_03_red_stub import red_skip

pytestmark = pytest.mark.skip(reason="M-G1-03 RED: P1-05 watermark (S02)")


def test_syncWatermark_readWatermark_singleEntryMacroAndBar() -> None:
    """覆盖范围：sync watermark 单一读入口
    测试对象：backend.app.sync.watermark.read_watermark
    目的/目标：macro_series 与 bar domain 共用 read_watermark(domain, key)
    验证点：ops watermark 改为 re-export，无双实现
    失败含义：增量窗口不一致导致重复/漏抓
    """
    red_skip("S02", "P1-05")
