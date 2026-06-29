# Audit Repair Ledger — R3-DCP-01

> **A9 建账：** 2026-06-30 · **Repair 关账：** 2026-06-30

| ID | 源 finding | P | 问题摘要 | disposition | 证据 |
|----|------------|---|----------|-------------|------|
| RB-01 | A1-P2-001 · A4-P1-001 · A8-P2-002 | P1 | caught-up 倒置窗无 no-op | 已修复 | `incremental_window_is_empty` · runner SKIPPED 早退 · port 倒置窗空 bars · `test_watermark_caughtUp_*` · `test_incrementalRunner_caughtUp_*` |
| RB-02 | A3-P1-02 · A4-P2-001 · A7-P1-01 | P1 | dry-run migration 写库 | 已修复 | dry-run 只读 watermark（DB 不存在则 None）；`test_qmdData_syncBaostock_dryRun_noDbFileCreated` |
| RB-03 | A3-P1-01 · A7-P2-01 | P1 | canonical DB 无 fail-closed | 已修复 | `assert_sandbox_db_allowed` + `.audit-sandbox` 门禁；`test_qmdData_syncBaostock_refusesCanonicalDbPath` |
| RB-04 | A3-P1-03 | P1 | cn_equity 真跑绕过 operator 确认 | 已修复 | `_require_baostock_sync_operator_or_sandbox`；`test_qmdData_syncBaostock_operatorAuthRequired` |
| RB-05 | A2-P2-003 · A4-P2-003 · A8-P2-001 | P2 | main.py 缺 `--instrument-id` / help 测 | 已修复 | `main.py` `--instrument-id` + help；`test_qmdData_syncCli_instrumentIdPassedToSyncPlan` |
| RB-06 | A4-P2-002 | P2 | 非法日期未包装 CliFailure | 已修复 | `_parse_sync_date` + lookback ValueError 包装；`test_qmdData_syncBaostock_invalidInputDates` |
| RB-07 | A2-P2-001 · A2-P2-002 | P2 | L2 attribution 注释 | 已修复 | `runners.py` / `baostock_port.py` L2 (R3-DCP-01) 注释 |
| RB-08 | A3-P3-01 | P3 | watermark clean_table SQL 纵深 | 已修复 | `_BAR_CLEAN_TABLES` + `quote_ident`；`test_watermark_cleanTableRejectsUnknownTable` |
| RB-09 | A4-P2-004 | P2 | adapter staging 分叉未测 | 已修复 | `BaostockAdapter` L2 文档 + `tests/test_baostock_adapter_staging.py` |
| RB-10 | A2-P3-001 · A4-P3-001 | P3 | since 语义 / 重复 date parse | 已修复 | `parse_fetch_window_date` SSOT · since 覆盖 date_start；`test_qmdData_syncBaostock_sinceOverridesDateStart` |
| RB-11 | A5-P1-001 | P1 | 全量 pytest 未绿 | 已修复 | `uv run pytest -q` exit 0 · QMD_DATA_ROOT `.audit-sandbox` 隔离 |
| RB-12 | A5-P2-001 | P2 | execute-evidence txt 缺失 | 已修复 | `research/execute-evidence/s01-green.txt` … `s05-green.txt` |
| RB-13 | A8-P3-001 | P3 | dry-run date_start 弱断言 | 已修复 | `test_qmdData_syncBaostock_dryRun_includesWatermarkWindow` 断言 `date_start==2024-05-31` |
| RB-14 | A5-P3-002 | P3 | GitNexus 索引滞后 | 阶段外置 | merge 后 analyze |
