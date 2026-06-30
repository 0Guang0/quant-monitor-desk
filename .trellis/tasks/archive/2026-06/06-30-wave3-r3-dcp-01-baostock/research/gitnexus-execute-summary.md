# GitNexus Execute 摘要 — R3-DCP-01

**日期:** 2026-06-30

## query: baostock incremental watermark sync

- 相关先例：`test_batch_d_orchestration_flow.py` 幂等增量、`test_vendor_fetch_e2e.py` 服务路径 E2E
- 金路径：`DataSyncOrchestrator.run_incremental`（只读，本轨不改）

## impact: IncrementalJobRunner (upstream)

| 项       | 值                                                                      |
| -------- | ----------------------------------------------------------------------- |
| risk     | **LOW**                                                                 |
| d=1      | `DataSyncOrchestrator.__init__` 接线                                    |
| d=2      | orchestrator 构造链                                                     |
| 计划改动 | `run()` 内 `FetchRequest` 增加 `start_time/end_time` from `spec.date_*` |

## impact: read_bar_trade_date_watermark (新建)

- 预期 risk LOW；仅新模块 + 测试/CLI 调用方

## 纪律

- 不改 `orchestrator.py`
- 提交前 `detect_changes()`
