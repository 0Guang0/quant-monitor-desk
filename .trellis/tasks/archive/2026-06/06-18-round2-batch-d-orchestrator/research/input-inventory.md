# Input Inventory — round2-batch-d-orchestrator (P0i)

> 2026-06-18 · Plan P0i · 文档宇宙审计（在 2a brainstorm 之前）

## 1. 任务卡展开

| 来源 | 路径 | 状态 |
|------|------|------|
| 任务卡本体 | `014_implement_data_sync_orchestrator.md` | in-repo |
| §3 | `docs/modules/data_sync_orchestrator.md` | in-repo |
| §3 | `specs/contracts/sync_job_contract.yaml` | in-repo |
| §3 | GLOBAL×4 | in-repo |
| §5 | `docs/architecture/03_runtime_flows.md` | in-repo |
| §5 | `docs/architecture/04_data_architecture.md` | in-repo |
| §5 | `docs/quality/final_package_rules.md` | in-repo |
| §5 | `docs/architecture/07_project_directory_structure.md` | in-repo |
| Round | `ROUND_2/README.md`, `DECISIONS.md` | in-repo |
| 台账 | `BATCH_B_REPAIR_STATUS.md`, `BATCH_C_*` | in-repo |
| 前置 | Batch C `finish.md` | in-repo |
| 门禁 | `scripts/production_gate.py`, `scripts/check_doc_links.py` | in-repo |
| v3 | `research/integration-ledger.md` | Plan 产出 |
| 交叉引用 | `docs/modules/duckdb_and_parquet.md`（orchestrator spec） | in-repo |

## 2. 六类关键信息覆盖

| 类别 | 必须覆盖 | 已定位路径 | 缺口 |
|------|----------|------------|------|
| 决策 defer | DECISIONS §9 + §3.2 | `DECISIONS.md` | 无 |
| 规则/规范 | GLOBAL + Trellis spec | GLOBAL×4, `.trellis/spec/backend/*` | 无 |
| 架构边界 | 03/04/07 + final_package | 已列入 | 无 |
| 业务需求 | 014 + orchestrator spec | `014_*.md`, `data_sync_orchestrator.md` | 无 |
| 契约 | sync/data_quality/source_conflict/adapter | `specs/contracts/*` | 无 |
| 前置 Batch | C 接线 + handoff | validators, gate, write_manager, finish.md | 无 |

## 3. 交叉引用闭包（1-hop）

| 自 | 引用 | 状态 |
|----|------|------|
| `data_sync_orchestrator.md` | `duckdb_and_parquet.md` | required |
| `data_sync_orchestrator.md` | `sync_job_contract.yaml` | required |

## 4. missing-in-repo

- （无）— 本任务所需权威文档均在仓库内

## 5. 门禁

- [x] 任务卡 §3 + §5 已展开
- [x] 六类关键信息均有路径
- [x] 与 `original-plan-trace.md` manifest 列一致

`P0i complete`
