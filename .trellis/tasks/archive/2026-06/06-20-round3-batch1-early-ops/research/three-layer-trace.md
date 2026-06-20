# Three-Layer Trace — Round 3 Batch 1

> 依据 `docs/implementation_tasks/TASK_INPUT_CONTEXT_INDEX.md` §1 三层模型建立。  
> Plan 阶段必须在写 `MASTER.plan.md` 前完成本追溯；Execute 默认不读本文件。

```text
Layer 1  设计文档 / 规则 / 契约 / 定义
           ↓
Layer 2  docs/implementation_tasks/** 原始执行任务
           ↓  Plan 过滤、归并、去噪
Layer 3  .trellis/tasks/06-20-round3-batch1-early-ops/** 冻结计划（待写）
```

---

## Layer 1 — 设计 / 契约 / 规则（已读摘要）

### 1.1 全局规则与治理

| 路径                                       | 归并到 MASTER 的约束                                                      |
| ------------------------------------------ | ------------------------------------------------------------------------- |
| `README.md`                                | `docs/`/`specs/` 非实现地址；MANIFEST 权威边界                            |
| `MIGRATION_MAP.md`                         | Round 3 已进入；inspect CLI 落点 `backend/app/ops/`、`scripts/`、`tests/` |
| `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §3    | Batch 1 八项 ID；不得与 `017`–`023` 合并                                  |
| `docs/quality/staged_acceptance_policy.md` | 本批为 **backend** 阶段验收（非 docs-only）                               |
| `docs/quality/PENDING_USER_DECISIONS.md`   | D-01 uv.lock；D-11 QMT 默认禁用 — Plan 不得重问                           |
| `specs/contracts/runtime_versions.md`      | `uv sync --locked` + `uv run pytest` 为验收权威                           |

### 1.2 登记册（权威 defer/resolve）

| 路径                                 | 关键结论                                                                   |
| ------------------------------------ | -------------------------------------------------------------------------- |
| `docs/AUDIT_DEFERRED_REGISTRY.md`    | **Registry wins on conflict**；无 OPEN 阻塞 017；`R2.6-IMPL-7` 已 RESOLVED |
| `docs/UNRESOLVED_ISSUES_REGISTRY.md` | Batch 1 八项状态见下表；`DOC-R3-001/002` 为 OPEN-DOC                       |
| `docs/RESOLVED_ISSUES_REGISTRY.md`   | Plan 须核对，避免重开已关闭项                                              |

| Item ID                     | Registry 状态 | Layer 1 证据来源                                                             |
| --------------------------- | ------------- | ---------------------------------------------------------------------------- |
| `DOC-R3-001`                | OPEN-DOC      | `ROUND3_HANDOFF.md` 仍偏 Round2.5 措辞                                       |
| `DOC-R3-002`                | OPEN-DOC      | `ROUND3_EARLY_CLOSE_PLAN.md` 缺 registry 权威声明                            |
| `R2.6-IMPL-8`               | DEFERRED      | `qmt_xtdata_setup.md` + `platform_source_matrix`；仅 user-authorized staging |
| `DB-R3-001`                 | DEFERRED      | `local_file_system.md` + 实测 data root 仅 duckdb + gitkeep                  |
| `DB-R3-002`                 | VERIFY        | 需 sanctioned read-only inspect（本批核心实现）                              |
| `R3-PARTIAL-2`              | DEFERRED      | `data_adapter_contract.md`；`run_full_load` **代码不存在**                   |
| `R3-EARLY-DB-INSPECT-CLI`   | 设计冻结      | `db_inspect_cli.md` + `ops_db_inspect_contract.yaml`                         |
| `R3-EARLY-PROD-SCALE-BENCH` | early         | `016F` 设计 + `production_equivalent_smoke.py`；`R2.6-IMPL-7` 已 RESOLVED    |

### 1.3 模块设计（Batch 1 source bundle）

| 路径                                         | 与本批关系                                              |
| -------------------------------------------- | ------------------------------------------------------- |
| `docs/modules/duckdb_and_parquet.md`         | key_tables 语义；DuckDB 存结构化证据                    |
| `docs/modules/local_file_system.md`          | `data/raw/`、`data/parquet/` 目录约定 → `DB-R3-001`     |
| `docs/modules/write_manager.md`              | inspect **不得**调用 writer / WriteManager              |
| `docs/modules/data_sources.md`               | Primary/Validation/Fallback；adapter 不写 clean 表      |
| `docs/modules/qmt_xtdata_adapter.md`         | D-11 默认禁用                                           |
| `docs/modules/source_capability_registry.md` | fetch 前 capability 检查                                |
| `docs/modules/source_route_plan.md`          | `route_status` 枚举 → inspect 只读报告                  |
| `docs/modules/datasource_service.md`         | 生产 fetch facade；`test_vendor_fetch_e2e` service path |
| `docs/modules/data_sync_orchestrator.md`     | `fetch_log`/`data_sync_job`/`job_event_log` 证据表      |

### 1.4 运维设计

| 路径                                    | 与本批关系                                         |
| --------------------------------------- | -------------------------------------------------- |
| `docs/ops/db_inspect_cli.md`            | **冻结** v1 范围 §5–§9；deferred_item_mapping §9.7 |
| `docs/ops/data_sync_quick_reference.md` | staging 授权参考；当前仍以 scripts 为准            |
| `docs/ops/qmt_xqshare_setup.md`         | `USER_AUTH_REQUIRED`；inspect 不得启用             |
| `docs/ops/privacy_data_flow.md`         | local-only；inspect 不打印 secrets                 |

### 1.5 机器契约

| 路径                                               | 不可无损总结 → Execute must-read                          |
| -------------------------------------------------- | --------------------------------------------------------- |
| `specs/contracts/ops_db_inspect_contract.yaml`     | 参数、key_tables、deferred_item_mapping、acceptance_tests |
| `specs/contracts/data_adapter_contract.md`         | FetchRequest/FetchResult；R3-PARTIAL-2                    |
| `specs/contracts/data_cli_contract.yaml`           | `qmd data` 未来形态；本批 transitional CLI                |
| `specs/contracts/source_route_contract.yaml`       | route_status 枚举                                         |
| `specs/contracts/datasource_service_contract.yaml` | service fetch 边界                                        |
| `specs/contracts/sync_job_contract.yaml`           | job_type / status                                         |
| `specs/contracts/platform_source_matrix.yaml`      | QMT/xqshare 平台规则                                      |

### 1.6 既有实现（接线事实，非设计）

| 路径                                     | 事实                                                     |
| ---------------------------------------- | -------------------------------------------------------- |
| `backend/app/db/connection.py`           | `reader()` 使用 `duckdb.connect(..., read_only=True)`    |
| `scripts/init_db.py`                     | 默认 `DATA_ROOT/duckdb/quant_monitor.duckdb`；**写**路径 |
| `scripts/production_equivalent_smoke.py` | 隔离 `.audit-sandbox`；只读查询 metrics                  |
| `tests/test_vendor_fetch_e2e.py`         | 已有 orchestrator + **service-path** fixture E2E         |
| `backend/app/ops/`                       | **不存在** — 本批新建                                    |

---

## Layer 2 — 原始执行任务（已读）

### 2.1 全局任务包（P0o 必读）

| 路径                                  | 状态                                                |
| ------------------------------------- | --------------------------------------------------- |
| `docs/implementation_tasks/README.md` | 已读 — Round 3 在 `017`–`023`                       |
| `GLOBAL_EXECUTION_RULES.md`           | 已读 — WriteManager、QMT 禁用、无 drive-by refactor |
| `GLOBAL_TESTING_POLICY.md`            | 已读 — 语义断言；禁止 call-only                     |
| `GLOBAL_RESOURCE_LIMITS.md`           | 已读 — eco 默认；禁止全市场扫描                     |
| `GLOBAL_TASK_TEMPLATE.md`             | 已读 — 阶段化验收 §11                               |

### 2.2 Round 3 原始任务（本批相关）

| 路径                                | 角色                                                  |
| ----------------------------------- | ----------------------------------------------------- |
| `ROUND_3_MODELING_LAYERS/README.md` | 声明 `017`–`023` 顺序执行；**inspect CLI 不在编号内** |
| `ROUND3_EARLY_CLOSE_PLAN.md`        | early 六项；inspect CLI 冻结实现                      |
| `docs/ROUND3_HANDOFF.md`            | 入口 checklist；item 7 = inspect CLI                  |

**本批明确排除的原始任务卡：** `017`–`023`（属 Batch 2–5）

### 2.3 Round 2.6 关联原始任务（仅追溯，非本批实现）

| 路径                                             | 追溯用途                                                                       |
| ------------------------------------------------ | ------------------------------------------------------------------------------ |
| `016F_define_prod_equivalent_scale_benchmark.md` | `R3-EARLY-PROD-SCALE-BENCH` 设计输入；`R2.6-IMPL-7` 已在 routing gate RESOLVED |

### 2.4 原始任务 → Item ID 映射

| 原始任务 / 计划文档                                | 映射 Item                       | MASTER 子交付物（草案）  |
| -------------------------------------------------- | ------------------------------- | ------------------------ |
| `ROUND3_EARLY_CLOSE_PLAN.md` §Local DB inspect CLI | `R3-EARLY-DB-INSPECT-CLI`       | AC-CLI-\*                |
| 同上 §Production-scale                             | `R3-EARLY-PROD-SCALE-BENCH`     | AC-BENCH-\*              |
| 同上 §Real QMT/Yahoo                               | `R2.6-IMPL-8`                   | AC-OPS-1（defer + 文档） |
| `ROUND3_HANDOFF.md` checklist                      | `DOC-R3-001`                    | AC-DOC-1                 |
| Registry rows                                      | `DB-R3-001/002`, `R3-PARTIAL-2` | AC-DB-_, AC-E2E-_        |

---

## Layer 3 — Trellis 前置计划（继承 trace）

| Trellis 任务                          | 与本批关系                                               |
| ------------------------------------- | -------------------------------------------------------- |
| `06-19-round2-6-contract-gate`        | archived PASS — 契约/design 对齐                         |
| `06-19-round2-6-routing-service-gate` | archived PASS — service path + smoke；`R2.6-IMPL-7` 证据 |
| `06-19-round2-repair-alignment`       | Round 3 入口 gate cleared                                |

本批 **新建** Layer 3 目录：`06-20-round3-batch1-early-ops`（status=planning）

---

## Plan 归并分类（→ MASTER Source Context Index）

| 分类                               | 路径示例                                                                          |
| ---------------------------------- | --------------------------------------------------------------------------------- |
| **可总结**                         | GLOBAL\_\*、MIGRATION_MAP、module 设计高层边界、registry 状态                     |
| **不可无损总结 → implement.jsonl** | `ops_db_inspect_contract.yaml`、`db_inspect_cli.md` §5–9、`connection.py` reader  |
| **已过滤 / 本批排除**              | `017`–`023` 任务卡；migration 008；`qmd data health`/`source probe` future phases |
| **原始任务卡**                     | 不进入 implement.jsonl；仅 Plan trace                                             |

---

## 关键 Plan 判断（读完三层后的结论）

1. **主实现面**是 `R3-EARLY-DB-INSPECT-CLI`；其余多为证据关闭或 docs-only。
2. **`DB-R3-001`** 可通过 inspect 输出 **documented absence**（raw/parquet=0）关闭，不必在本批强制 live vendor 写入 `data/`。
3. **`R3-PARTIAL-2`**：`test_vendor_fetch_e2e.py` 已有 fixture E2E（含 service path），但 registry 仍 DEFERRED 且 `run_full_load` 不存在 — Plan 须决定：扩展/登记 RESOLVED **或** 补 `run_full_load` skeleton pytest。
4. **`R3-EARLY-PROD-SCALE-BENCH`**：`R2.6-IMPL-7` 已 RESOLVED；本批可能仅需重跑 smoke + 记录证据，或显式 re-defer 并链接既有证据。
5. **`R2.6-IMPL-8`**：本批 **不执行** live validation；保持禁用 + runbook 文档即可。

---

## P0 阅读完成确认

- Layer 1：Batch 1 source bundle（`ROUND3_BATCH_IMPLEMENTATION_MAP.md` §4.2）已逐项读取或核对
- Layer 2：GLOBAL\_\* + Round3 early 原始任务已读；`017`–`023` 已标为 out-of-scope
- Layer 3：前置 Trellis gate 已索引

**可以开始** Phase 1a 之后的 MASTER §1–§3 草稿与 §2 AC 精化。
