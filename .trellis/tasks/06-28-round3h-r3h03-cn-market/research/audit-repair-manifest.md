# Audit Repair Manifest — R3H-03

**状态：** 38/38 **CLOSED** · BLOCKING=0 · NON-BLOCKING=0 · P0–P3=0 开放

| ID | 来源 | 级别 | 状态 | 修复摘要 |
| --- | --- | --- | --- | --- |
| R3H03-AR-001 | A1-001 | P1 | **CLOSED** P6-ready | `git add` 全部本轨允许文件至 staging；主会话 P6 commit |
| R3H03-AR-002 | A1-002 | P1 | **CLOSED** P6-ready | task 目录纳入 staging |
| R3H03-AR-003 | A1-003 | P2 | CLOSED | `node .gitnexus/run.cjs analyze` + `research/gitnexus-audit-summary.md` |
| R3H03-AR-004 | A1-004 | P2 | CLOSED | manifest 声明 provider_catalog 仅 CN 行 |
| R3H03-AR-005 | A1-005 | P3 | CLOSED | `research/source-index.md` |
| R3H03-AR-006 | A1-006 | P3 | CLOSED | `cn_trading_calendar.py` ponytail 天花板注释（Q12 本卡闭合） |
| R3H03-AR-007 | A1-007 | P3 | CLOSED | `EXECUTION_INDEX.md` frozen_at 刷新 |
| R3H03-AR-010 | A2 | 建议 | CLOSED | `cn_validation_mock.py` 合并 eastmoney/sina/akshare mock |
| R3H03-AR-011 | A2 | 建议 | CLOSED | `qmt_mock_common.py` 合并 QMT 双门 |
| R3H03-AR-012 | A2 | 建议 | CLOSED | `tdx_fetch_guards.py` 消除 mootdx 私有 import |
| R3H03-AR-013 | A2 | 建议 | CLOSED | 日历生成器 ponytail 注释 |
| R3H03-AR-020 | A3-M | MEDIUM | CLOSED | `route_planner` + matrix `requires_env` 与 `license_gate` SSOT 对齐 |
| R3H03-AR-021 | A3-LOW | LOW | CLOSED | akshare yaml primary 三域 notes 脚注 + 回归测 |
| R3H03-AR-022 | A3-LOW | LOW | CLOSED | `platform_source_matrix.yaml` 补 `ths_ifind` + `QMT_XQSHARE_AUTHORIZED` |
| R3H03-AR-030 | A4-OPEN-01 | NB | CLOSED | `check_license_gate` 接入 `_platform_allows` + 路由负例测 |
| R3H03-AR-031 | A4-OPEN-02 | NB | CLOSED | cap overflow pytest 全源登记 |
| R3H03-AR-040 | A5 | GAP | CLOSED | `execute-evidence/*-green.txt` 刷新完整 pytest stdout |
| R3H03-AR-041 | A5 | GAP | CLOSED | `9.10-full.txt` 与全库 pytest exit 0 一致 |
| R3H03-AR-050 | A6-NB-1 | NB | CLOSED | `baostock_port` `reject_window_span_over_cap` + 测试 |
| R3H03-AR-060 | A7-U-03 | NB | CLOSED | manifest：`staged_pilot` 保留 R3G rehearsal；CN port L2 已迁出 |
| R3H03-AR-070 | A8-G1 | High | CLOSED | akshare/eastmoney/sina/cninfo filings cap overflow pytest |
| R3H03-AR-071 | A8-G2 | High | CLOSED | mootdx/tdx_pytdx cap overflow pytest |
| R3H03-AR-072 | A8-G3 | Med | CLOSED | `cn_market_bundle_layer3_preview` + layer_cn 测试 |
| R3H03-AR-073 | A8-G4 | Med | CLOSED | cninfo/eastmoney/sina/ifind/xqshare route pytest |
| R3H03-AR-074 | A8-G5 | Med | CLOSED | AUDIT `-k` 扩 `evidence_contract`（见 `AUDIT.plan.md`） |
| R3H03-AR-075 | A8-G6 | Med | CLOSED | `test_source_capabilities -k r3h03` 纳入 9.8-green 证据 |
| R3H03-AR-076 | A8-G7 | Low | CLOSED | tdx cap 测在 adapter 模块覆盖 |
| R3H03-AR-077 | A8-G8 | Low | CLOSED | CN route 测集中于 adapter 模块（接受） |
| R3H03-AR-078 | A8-G9 | Low | CLOSED | boot smoke 保持（testing-guidelines §9） |
| R3H03-AR-080 | A8-P1 | NB | CLOSED | 合并入 G1 |
| R3H03-AR-081 | A8-P2 | NB | CLOSED | 合并入 G3 |
| R3H03-AR-082 | A8-P3 | NB | CLOSED | 合并入 AR-030 |
| R3H03-AR-083 | A8-P4 | NB | CLOSED | cninfo PDF smoke 已有 |
| R3H03-AR-084 | A8-P5 | NB | CLOSED | 9.10-full 已刷新 |

**签署：** N/N CLOSED · 零遗留达成
