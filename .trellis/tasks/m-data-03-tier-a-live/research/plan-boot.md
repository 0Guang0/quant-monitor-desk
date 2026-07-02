# Plan Boot — M-DATA-03 Tier A 真网

> **轨道：** 模块闭环 v2 · Plan v4.1  
> **日期：** 2026-07-02  
> **活卡：** `docs/implementation_tasks/M_DATA_03_TIER_A_LIVE/M_DATA_03_TIER_A_LIVE.md`

---

## Phase P0 complete

### 1. 做什么

把 Wave 4 DCP-05 已交付的 **11 源 replay 增量逻辑**，在 **隔离库** 上升级为 **真连网验收主路径**：每源 `sync→clean→inspect/health` 绿；MCR 诚实标 R4 真网 scope。

### 2. 为什么做

- 路线图 §0.3.1：**PASS = 真代码 + 真跑**；DCP-05 CLOSED 但 C3 仍 R3（全 mock e2e）
- M-G1-03 依赖宏观/行情 **真 clean**，不能继续 seed/replay 冒充

### 3. 做到什么算完成

活卡 §5 + `to-issues-slices.md` 全切片绿 + 统一 A1–A8 Audit PASS + `uv run pytest -q` exit 0

### 4. 约束复述

| 约束      | 要求                                                                |
| --------- | ------------------------------------------------------------------- |
| 金路径    | `DataSourceService` + `run_incremental`（ADR-025）                  |
| 真网闸    | `QMD_ALLOW_LIVE_FETCH=1` + `product_live_gate`（ADR-027）           |
| 隔离      | 专用 `DATA_ROOT`；禁止写 canonical 主库                             |
| 11/11     | 用户 §0.3.4 无 ADR 例外                                             |
| 参考 L 梯 | **仅** `参考项目/**`；仓内 DCP-05 = **直接复用**（禁止标 L1/L2/L3） |

### 5. 架构触点

```text
qmd data sync --source-id <id>
  → product_live_gate
  → DataSourceService.fetch
  → fetch_ports/* (live)
  → sync/orchestrator.run_incremental
  → validators + WriteManager
  → clean 表
  → qmd data inspect / data_health
```

### 6. P0 已读清单

- [x] `docs/implementation_tasks/README.md` · `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.1 · §0.3.3–0.3.4
- [x] `MODULE_COMPLETION_RATING.md` §0 Pass E（DCP-05 子集 vs 模块 Rating）
- [x] `MIGRATION_MAP.md` §4.12 · `authority_graph.yaml` C3/D1/E1/E2/F0/B2
- [x] `R3H_PASS_EXECUTION_PLAN.archived-20260702.md` §2.1 Tier A 表
- [x] DCP-05 归档：`to-issues-slices.md` · `reference-adoption-dcp05.md` · ADR-028
- [x] `docs/modules/data_sync_orchestrator.md` §12–13 · `datasource_service.md`
- [x] `specs/contracts/reference_adoption_guardrails.yaml`
- [x] `backend/app/datasources/product_live_gate.py` · `sync/orchestrator.py` · `ops/*_incremental_*`
- [x] `tests/test_*_incremental_e2e.py`（11 文件，当前 replay 主路径）
- [x] 参考项目实读：OpenBB `fetcher.py` · digital-oracle `bis.py` · EasyXT `unified_data_interface.py` L172–244 · `auto_data_updater.py` L114–178

### 7. 与 DCP-05 差异

| 项          | DCP-05（已 CLOSED）    | M-DATA-03（本票）                      |
| ----------- | ---------------------- | -------------------------------------- |
| 验收路径    | replay/mock e2e 为主   | **live 为主**（replay 仅 CI 快测）     |
| 模块 Rating | Milestone ✅；C3 仍 R3 | C3/D1/E1/E2/F0/B2 → **R4**             |
| 新增 DDL    | migration 015          | **无**（封板）                         |
| 核心工作    | 增量逻辑 + clean 路由  | live port 接通 + 隔离验收 + inspect 绿 |
