# Round 2 — 缺口、漏洞与偏差台账

> **Status:** living document · **Last updated:** 2026-06-19 · **Baseline:** `master` post PR #10/#11  
> **审计来源：** 多维度对抗审计（composer-2.5）+ `DECISIONS.md` / `AUDIT_DEFERRED_REGISTRY.md` 交叉核对

## 如何使用本文

| 类型         | 含义                                              | 是否阻塞 Round 3                    |
| ------------ | ------------------------------------------------- | ----------------------------------- |
| **RESOLVED** | 已实现 + 测试 + 证据                              | —                                   |
| **OPEN**     | 未完成且阻塞门控                                  | 是                                  |
| **DEFERRED** | 延后但必须登记 **解决阶段 + 任务钩子 + 闭合测试** | 见 registry 列 `Blocks 017?`        |
| **PARTIAL**  | 模块存在但语义未闭合                              | 登记为 DEFERRED，不得仅写「不阻塞」 |
| **GAP**      | 设计卡 vs 实现差距                                | 同上                                |
| **RISK**     | 架构/运维隐患                                     | 同上                                |

**原则：** 凡问题必须 **全清** 或在 [`docs/AUDIT_DEFERRED_REGISTRY.md`](../../AUDIT_DEFERRED_REGISTRY.md) **详细记录延后**；不阻塞 ≠ 不解决。

---

## 0. 总评（设计初衷 vs 现状）

| 维度                                | 得分 (/20) | 摘要                                                |
| ----------------------------------- | ---------- | --------------------------------------------------- |
| 完整性 vs 011–016 清单              | 15         | 核心模块齐；6 类 job 仅 1 条金路径 E2E              |
| 质量（测试/契约/错误路径）          | 17         | 362 tests · 94% cov；backfill/reconcile 路径偏薄    |
| 可信链（staging→gate→WriteManager） | 16         | **incremental 强制**；backfill 绕过                 |
| 同步编排                            | 13         | 状态机全；`run_*` 仅 3 个，其中 2 个不完整          |
| 生产就绪                            | 10         | skeleton + smoke CLI；无真实 vendor / 生产 sync CLI |
| 文档诚实度                          | 13         | 延后登记好；本文补齐 PARTIAL 语义缺口               |

**综合：84/100** — 与「抓得可信」**哲学对齐**；与「全 job、全源、生产级可信抓取」**未对齐**（符合 Round 2 批次边界）。

---

## 1. 设计清单逐条对照（011–016 预期能力）

| 设计项                                             | 状态             | 偏差类型                                        | 证据                                                         |
| -------------------------------------------------- | ---------------- | ----------------------------------------------- | ------------------------------------------------------------ |
| `source_registry` 数据源注册表                     | **DONE**         | —                                               | `backend/app/datasources/source_registry.py` · migration 004 |
| Primary / Validation / FallbackPolicy              | **DONE**         | —                                               | `source_registry.py` · `DECISIONS.md` §4                     |
| `BaseDataAdapter` + `FetchResult`                  | **DONE**         | —                                               | `base_adapter.py` · `fetch_result.py`                        |
| QMT / baostock / AkShare / CNINFO / Yahoo skeleton | **DONE**（结构） | **GAP**：无真实 `FetchPort`                     | `adapters/*.py` · `DECISIONS.md` §2 Batch B                  |
| `fetch_log` 失败也落库                             | **DONE**         | —                                               | `fetch_log.py` · `base_adapter.fetch`                        |
| staging 先于 clean                                 | **PARTIAL**      | incremental ✅；backfill 仅 STAGED              | `orchestrator.run_incremental` vs `run_backfill`             |
| `DataQualityValidator`                             | **DONE**         | 仅接入 incremental 路径                         | `validators/data_quality.py` · `sync/pipeline.py`            |
| `SourceConflictValidator`                          | **DONE**         | incremental + conflict staging                  | `validators/source_conflict.py`                              |
| `source_conflict` 表                               | **DONE**         | —                                               | migration 005                                                |
| `manual_review_queue`                              | **PARTIAL**      | reconcile 未解决时入队，非 severe 即刻          | `source_conflict.record_unresolved_reconcile`                |
| `DataSyncOrchestrator`                             | **PARTIAL**      | 类与状态机完整；job 矩阵不全                    | `sync/orchestrator.py` · `sync/jobs.py`                      |
| **IncrementalUpdateJob** E2E                       | **DONE**         | 金路径：fetch→validate→gate→write               | `test_batch_d_orchestration_flow.py`                         |
| **BackfillJob** E2E                                | **PARTIAL**      | 分片 fetch + guard；**无 validator / 无 clean** | §2.1                                                         |
| **FullLoadJob**                                    | **DEFERRED**     | 可建 job + 状态；无 `run_full_load`             | `AUDIT_DEFERRED_REGISTRY` D2-P1-1                            |
| **RevisionAuditJob**                               | **DEFERRED**     | 状态机可达 STAGED；无运行器                     | D2-P1-1 · `BATCH_D_STATUS.md` D-A7-1                         |
| **ReconcileJob**                                   | **PARTIAL**      | `run_reconcile` 存在；不 re-fetch/compare       | §2.2 · D2-P2-2                                               |
| **DataQualityJob**（独立 job 类型）                | **DEFERRED**     | 无 `run_data_quality`                           | D2-P1-1                                                      |
| 严重冲突 → 人工确认                                | **PARTIAL**      | gate 阻断 + reconcile 失败入队；无 UI/API       | Round 4 范围                                                 |
| `python -m quant_monitor.sync` CLI                 | **DEFERRED**     | 仅有 `scripts/sync_registry.py` smoke           | D2-P1-3                                                      |
| `source_health_snapshot`                           | **DEFERRED**     | 未建表                                          | D2-P2-1                                                      |
| ResourceGuard 重任务门禁                           | **DONE**         | `begin_fetching` · backfill 每 shard            | `orchestrator.py`                                            |
| `DbValidationGate` 替换 Stub                       | **DONE**         | —                                               | `validation_gate.py` · Batch C                               |
| WriteManager 同事务 gate（默认路径）               | **DONE**         | 审计修复已合并                                  | `write_manager.py` · `test_audit_fixes.py`                   |

---

## 2. 部分实现与语义缺口（PARTIAL — 本次重点补齐文档）

### 2.1 Backfill 不经质量门、不写 clean（R2-PARTIAL-1）

| 字段                 | 内容                                                                                                                       |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| **设计读者可能误解** | 「Round 2 完成后数据质量不合格不进入 clean」适用于所有 job                                                                 |
| **实际行为**         | `run_backfill`：分片 `adapter.fetch` → `STAGED` →（末片）`COMPLETED`；**不调用** `SyncValidationPipeline` / `WriteManager` |
| **代码**             | `backend/app/sync/orchestrator.py` `run_backfill` L209–285                                                                 |
| **当前缓解**         | fetch_log + staging/raw 证据；ResourceGuard 每 shard；eco 分片上限                                                         |
| **目标阶段**         | Round 3 ops — 补「backfill 完成后批量 validate+write」或文档明确 backfill=仅补证据层                                       |
| **阻塞 Round 3？**   | **否**（Layer 建模可用 incremental/fixture 种子）                                                                          |

### 2.2 Reconcile 不真正重抓/复核（R2-PARTIAL-2）

| 字段         | 内容                                                                                      |
| ------------ | ----------------------------------------------------------------------------------------- |
| **设计预期** | 按 conflict 读取 primary/validation、重抓、再比较                                         |
| **实际行为** | `run_reconcile` 读 `source_conflict` 行、建 reconcile job；`adapter` 参数保留未用于 fetch |
| **代码**     | `orchestrator.run_reconcile` L287+（注释：Round 3 vendor fetch）                          |
| **目标阶段** | Round 3 · `AUDIT_DEFERRED_REGISTRY` D2-P2-2                                               |

### 2.3 manual_review_queue 入队路径（R2-PARTIAL-3）

| 字段         | 内容                                                                                                   |
| ------------ | ------------------------------------------------------------------------------------------------------ |
| **设计预期** | 严重冲突进入人工确认                                                                                   |
| **实际行为** | severe → `WAITING_RECONCILE` + gate 阻断 clean；`manual_review_queue` 在 **reconcile 仍未解决** 时写入 |
| **语义**     | 「先 reconcile、再人工」— 与部分读者「severe 即刻入队」略有差别                                        |
| **代码**     | `source_conflict.py` `record_unresolved_reconcile`                                                     |

### 2.4 COMPLETED 与 write 非同事务（R2-PARTIAL-4）

| 字段         | 内容                                                               |
| ------------ | ------------------------------------------------------------------ |
| **行为**     | `run_incremental` 在 writer 事务提交后单独 `transition(COMPLETED)` |
| **风险**     | 极低概率：write 已提交但 job 状态未 COMPLETED（进程崩溃）          |
| **登记**     | `BATCH_D_STATUS.md` D-A2-3 · intentional split                     |
| **目标阶段** | Round 3 ops 可选同事务化                                           |

### 2.5 init_db 不自动 sync registry（R2-GAP-1）

| 字段         | 内容                                                                                                 |
| ------------ | ---------------------------------------------------------------------------------------------------- |
| **行为**     | `scripts/init_db.py` 仅 migration；registry 需 `sync_registry.py` 或 `bootstrap(sync_registry=True)` |
| **登记**     | `DECISIONS.md` §9 GPT-init_db（Batch D 已补 CLI，默认 init 仍 migration-only）                       |
| **目标阶段** | Round 3 packaging / ops 文档强化                                                                     |

### 2.6 源能力发现无对外 API（R2-GAP-2）

| 字段         | 内容                                                                        |
| ------------ | --------------------------------------------------------------------------- |
| **行为**     | `allowed_domains` / `SourceRecord` 在代码与 DB；无 list/capability HTTP API |
| **目标阶段** | Round 4 API                                                                 |

---

## 3. 有意延后项（DEFERRED — 摘要）

完整 ID 表见 [`docs/AUDIT_DEFERRED_REGISTRY.md`](../../AUDIT_DEFERRED_REGISTRY.md)。

| ID      | 项                                                          | 目标阶段          |
| ------- | ----------------------------------------------------------- | ----------------- |
| D2-P1-1 | `run_full_load` / `run_revision_audit` / `run_data_quality` | Round 3+          |
| D2-P1-2 | 真实 vendor `FetchPort`                                     | Round 3+          |
| D2-P1-3 | `quant_monitor.sync` 生产 CLI                               | Round 3 ops       |
| D2-P2-1 | `source_health_snapshot`                                    | Round 3+          |
| D2-P2-2 | Reconcile 完整重抓流程                                      | Round 3           |
| D2-P3-1 | `registry_generation` / `removed_from_yaml_at` 列           | Round 3+          |
| D7-P1-1 | Orchestrator 完整 handler registry                          | Round 3           |
| D7-P2-2 | 脚本 `sys.path.insert`                                      | Round 3 packaging |

---

## 4. 架构与耦合风险（RISK）

| ID        | 项                                            | 说明                                                        | 阶段                                           |
| --------- | --------------------------------------------- | ----------------------------------------------------------- | ---------------------------------------------- |
| R2-RISK-1 | Orchestrator 聚合点多                         | 同时依赖 guard/adapter/gate/validators/write                | Round 3 抽 handler（`pipeline.py` 已部分缓解） |
| R2-RISK-2 | adapters 直接依赖 storage 实现                | `RawStore`/`FileRegistry` 非端口注入                        | Round 3 `evidence_ports.py` 渐进               |
| R2-RISK-3 | `WriteRequest` 仍少于原始 write_contract 全集 | 已扩审计列；`replace_partition` 等模式未实现                | Round 3+                                       |
| R2-RISK-4 | 部分 status 列依赖应用层 CHECK                | migration 007 已补 sync job；`fetch_log.status` 等仍 app 层 | 维持 app 层（C-C2）                            |
| R2-RISK-5 | 无 gitleaks / 完整 security CI                | `DECISIONS.md` GPT-SEC-CI → Round 5                         | Round 5                                        |

---

## 5. 质量与工程卫生（GAP / 非阻塞）

| ID       | 项                          | 说明                                                                   | 阶段                      |
| -------- | --------------------------- | ---------------------------------------------------------------------- | ------------------------- |
| R2-HYG-1 | C901 复杂度                 | `_validate_domain_roles`、`_execute_write`、`validate_status_contract` | Round 3 hygiene · D3-P1-2 |
| R2-HYG-2 | Windows 默认 pytest Temp    | 使用 `pyproject.toml` 内 `--basetemp`                                  | 已缓解 · D1-P3-1          |
| R2-HYG-3 | ~~Starlette/httpx warning~~ | **已解决** — `httpx2` dev dep · PR #11                                 | —                         |
| R2-HYG-4 | 测试互调味道                | `test_duckdb_connection` 曾 test-call-test                             | 可选清理                  |
| R2-HYG-5 | adapter metadata 字段       | `requires_auth` 等未在 skeleton 暴露                                   | Batch C/D 登记 B-P2-1     |

---

## 6. Round 3 建模层影响矩阵

| 缺口                                 | 阻塞 Layer 1 轴加载？ | 理由                                   |
| ------------------------------------ | --------------------- | -------------------------------------- |
| 无真实 vendor FetchPort              | **否**                | fixture / 测试 adapter 可种子 clean 表 |
| 无 full_load / revision_audit 运行器 | **否**                | 建模不依赖运维补数路径                 |
| Backfill 不写 clean                  | **否**                | incremental 金路径已证明 gate 纪律     |
| Reconcile 骨架                       | **否**                | 冲突治理在 incremental 已测            |
| 无生产 CLI                           | **否**                | 开发用 pytest + smoke                  |
| Orchestrator 耦合                    | **否**                | 不影响 layer 包接口设计                |

**结论：** Round 3 可启动当且仅当 [`AUDIT_DEFERRED_REGISTRY.md`](../../AUDIT_DEFERRED_REGISTRY.md) 中 **无未登记 OPEN 项**（当前仅 `PROC-R2.5-1` 合并/handoff）；其余 PARTIAL/GAP/RISK 必须已转为 **DEFERRED + 解决阶段** 或 **RESOLVED**。本文 §2–§5 各项均已映射至 registry。

---

## 7. 推荐偿还顺序（供排期）

1. **Round 3 早期：** `DECISIONS.md` §11 backfill 语义（本文 §2.1）+ 第一个真实 `FetchPort` 或 `run_full_load` 骨架
2. **Round 3 中期：** `run_reconcile` 真重抓 · `source_health_snapshot`
3. **Round 3 ops：** `quant_monitor.sync` CLI · backfill→validate→write 闭环
4. **Round 3 hygiene：** C901 拆分 · handler registry 完善
5. **Round 4/5：** API 能力矩阵 · security CI · write_contract 全模式

---

## 8. 相关文档索引

- [`DECISIONS.md`](./DECISIONS.md) — 批次边界与已拍板决策
- [`BATCH_D_STATUS.md`](./BATCH_D_STATUS.md) — Batch D Audit/Repair 延后裁定
- [`docs/AUDIT_DEFERRED_REGISTRY.md`](../../AUDIT_DEFERRED_REGISTRY.md) — 审计延后 ID 注册表
- [`docs/ROUND3_HANDOFF.md`](../../ROUND3_HANDOFF.md) — Round 3 启动清单
