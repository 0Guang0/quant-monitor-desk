# PRD — Round 3 Batch 1 Early Ops

> 详细计划见 `MASTER.plan.md` §1–3。Plan Phase 2a。

## 问题

Round 3 五层建模（`017`+）之前，登记册仍有 early 证据缺口：handoff 未完整反映 Round 2.6 PASS、本地 data root 未记录 real vendor raw/parquet 状态、缺少 sanctioned 只读 DuckDB inspect CLI、`R3-PARTIAL-2` 未在 registry 闭合、生产等价基准需归档 fixture-scale 证据。

## 目标用户

本地维护者 / Execute-Audit agent — 在不 mutate production DB、不默认启用 live vendor 的前提下获得可审计证据。

## 需求

| ID  | 需求                                                                                                   |
| --- | ------------------------------------------------------------------------------------------------------ |
| R1  | 实现冻结 Phase A `qmd ops db-inspect`（transitional `scripts/qmd_ops.py`）                             |
| R2  | inspect 输出 JSON/text，含 `deferred_item_mapping` 对接 `DB-R3-001/002`                                |
| R3  | 修补 `DOC-R3-001/002` 文档                                                                             |
| R4  | `R3-PARTIAL-2`：以既有 fixture FetchPort service-path E2E + `full_load` job skeleton 测试闭合 registry |
| R5  | `R3-EARLY-PROD-SCALE-BENCH`：重跑 smoke + 归档证据（链到 `R2.6-IMPL-7`）                               |
| R6  | `R2.6-IMPL-8`：保持 live 默认禁用；inspect 不启用 live source                                          |

## 验收标准（可测试）

- `pytest tests/test_ops_db_inspector.py -q` 全绿，含 read-only / no-mutation / JSON shape 语义断言
- `python scripts/qmd_ops.py db-inspect --format json` 对项目 DB 返回 `status` + `key_tables`
- registry 中 Batch 1 相关项更新为 RESOLVED 或带 closure test 的 DEFERRED
- `uv run pytest -q` + ruff + production_gate 保持 green

## 非目标

- `017`–`023` Layer 建模 · migration 008 · live QMT/Yahoo soak
- `qmd data health` / `source probe` / `ops report`（future phases）
- 在 `data/` 写入 real vendor 数据（除非用户另行授权 staging）

## 已确认事实（仓库证据，无需再问用户）

- Round 2.6 Contract + Routing Service Gate archived PASS
- `ConnectionManager.reader()` 已 `read_only=True`
- `test_vendor_fetch_e2e.py` 已有 orchestrator + service-path fixture E2E
- `test_sync_jobs.py` 已有 `full_load` create_job 骨架
- `backend/app/ops/` 尚不存在

## Plan 决策（无用户歧义项）

| 决策                      | 选择                                                                | 理由                                               |
| ------------------------- | ------------------------------------------------------------------- | -------------------------------------------------- |
| `R3-PARTIAL-2` 闭合路径   | fixture FetchPort E2E（已有）+ 引用 `test_sync_jobs` full_load 骨架 | registry 为 OR；无 user-authorized live vendor     |
| `DB-R3-001`               | documented absence via inspect WARN                                 | 不强制本批 live ingestion                          |
| `backend/app/cli/main.py` | v1 仅 `scripts/qmd_ops.py` 薄包装                                   | 仓库尚无 `backend/app/cli/`；契约允许 transitional |
