# Round 3 Batch 2.5 — 待修复清单（审计对账）

> **Authority:** 本文件是 `临时报告/` 九 Agent 对抗审计（2026-06-21）的**可执行待办台账**。  
> **配对文档:** `docs/AUDIT_DEFERRED_REGISTRY.md`（正式延期登记）· `docs/UNRESOLVED_ISSUES_REGISTRY.md`（运营视图）  
> **分支:** `fix/audit-report-issues-20260621`  
> **规则:** 每项必须标明 **清理阶段**、**是否阻塞**、**关闭测试/证据**；合并前更新三项 registry 保持一致。

---

## 1. 已在本分支关闭（勿重复打开）

| ID                       | 问题                                | 关闭证据                                                                                          |
| ------------------------ | ----------------------------------- | ------------------------------------------------------------------------------------------------- |
| GLOBAL-P1-01 / A1-P1-01  | phase3/phase4 evidence 深层路径失败 | `path_compat.py` · `test_save_windowsLongPath_writesSuccessfully` · phase3/4 targeted 绿          |
| GLOBAL-P1-02             | 全量 pytest 失败                    | `pytest -q` 全绿                                                                                  |
| GLOBAL-P2-02 / B2.5-O-02 | `schema.sql` 滞后 migration 011     | `specs/schema/schema.sql` 已同步 · `test_layer1Ingestion_phase0_schemaSqlLagTrackedAsO02`         |
| GLOBAL-P2-03 / B2.5-O-03 | `axis_observation` 时间序 DB CHECK  | **应用层闭环**（DuckDB 无 `ALTER ADD CONSTRAINT`）· `test_layer1Observation_noFutureDataRejected` |
| GLOBAL-P2-04             | 缺 `uv.lock`                        | 根目录 `uv.lock`                                                                                  |
| GLOBAL-P2-05             | audit.report §3 pending             | `.trellis/.../audit.report.md` A1–A8 摘要已填                                                     |
| GLOBAL-P2-06             | ruff 未跑                           | `ruff check` + `ruff format --check` 绿                                                           |
| B2.5-WIN-PATH-01         | Windows MAX_PATH raw I/O            | 同上 path_compat                                                                                  |
| A06-P2-01 / A04-P3-02    | 异常 `=` / `frontend/=` 路径        | 目录已删除 · `.gitignore` 已加 `=/` · `frontend/=/` · `.audit-sandboxpytest-*/`                   |

---

## 2. 合理延期项 — 必须按阶段清理（已登记）

以下项**不阻塞 Batch 2.5 staged 闭环**；不得在未完成关闭证据前宣称 production-live ready。

### 2.1 Batch 2.75 — 受控生产/真实源试点（需用户显式授权）

| ID                         | 问题                                                                                                     | 清理阶段                       | 任务挂钩                                                               | 阻塞什么                    | 关闭条件                                                                                                                                                                             |
| -------------------------- | -------------------------------------------------------------------------------------------------------- | ------------------------------ | ---------------------------------------------------------------------- | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| GLOBAL-P2-01 / R3-B2.75-01 | 外部真实源 controlled live pilot 已执行；closeout `PILOT_FAIL_SOURCE`（Request 2 Eastmoney hist 不可达） | **Partial close 2026-06-21**   | `final_pilot_closeout.md` · `production_live_pilot_policy.md`          | 非全量 production-live PASS | `PILOT_FAIL_SOURCE` + Request 1/3 sandbox 证据 + 无生产 DB mutation；Request 2 见 `R3-B2.75-REQ2-EM`                                                                                 |
| A01-P1-01 / A02-P1-02      | Batch2.5 仅 staged，非 production-live                                                                   | **Batch 2.75** 或显式 re-defer | 同上 · `final_registry_update.md`                                      | 错误业务信任链              | Pilot closeout 或 MASTER 中 re-defer 文案                                                                                                                                            |
| B2.5-O-05 / A02-P2-01      | FRED primary vs staged `macro_supplementary`                                                             | **RE-DEFERRED — Batch 6**      | `ENV-E1-DGS10` · MASTER AC-P2-0 · `production_live_pilot_policy.md` §4 | Live FRED shape/授权        | Request 3 **does not close**; separate user-authorized `FRED:DGS10` pilot + sandbox/no-mutation proof **or** keep staged and document (`pytest tests/test_fred_staged_semantics.py`) |
| A09-P2-03 / A9-P1-03       | 真实源 DB shape / 写入未试点                                                                             | **Batch 2.75**                 | sandbox-only clean write                                               | 真实源 DB 证据链            | sandbox 内 raw-only + inspect delta                                                                                                                                                  |
| A08-P2-03                  | 真实网络延迟/重试未测                                                                                    | **Batch 2.75**                 | live micro-window                                                      | 生产 SLA 评估               | pilot 指标 p50/p95 + retry 记录                                                                                                                                                      |
| A09-P2-02                  | 生产 DB checksum before/after                                                                            | **Batch 2.75**（只读副本）     | `production_live_pilot_policy.md`                                      | 生产等价证明                | 对**副本**做 read-only baseline + after delta；禁止写生产库                                                                                                                          |

### 2.2 Round 3 迁移 / DB 契约（非 live 授权类）

| ID                               | 问题                                            | 清理阶段                  | 任务挂钩                            | 关闭条件                        |
| -------------------------------- | ----------------------------------------------- | ------------------------- | ----------------------------------- | ------------------------------- |
| B2.5-O-06 / A09-P2-01 / A9-P1-01 | Migration 008 广义 DB CHECK closeout            | **Round 3 migration 008** | `docs/schema/MIGRATION_008_PLAN.md` | migration 应用 + contract tests |
| A9-P2-01..03 (registry)          | `manual_review_queue` / `source_conflict` CHECK | **Round 3 migration 008** | 同上                                | 同上                            |

### 2.3 Round 3 架构卫生（既有 registry，非 Batch 2.5 阻塞）

| ID                              | 问题                                 | 清理阶段                        | 关闭条件                           |
| ------------------------------- | ------------------------------------ | ------------------------------- | ---------------------------------- |
| D7-P1-1 / R2-RISK-1 / A07-P2-03 | Orchestrator handler registry 未抽取 | **Round 3 hygiene**（post 019） | handler registry + pytest          |
| D7-P2-2 / A07-P2-04             | 脚本 `sys.path.insert` packaging     | **Round 3 packaging / 035**     | editable install + console_scripts |

### 2.4 Round 4+（前端 / API / 通知）

| ID                     | 问题                     | 清理阶段                  | 关闭条件               |
| ---------------------- | ------------------------ | ------------------------- | ---------------------- |
| A05-P2-02 / A04-P2-02  | 前端 Vitest 过薄         | **Round 4 task 027**      | 路由/契约/错误态测试   |
| A08-P2-02 / A08-P3-01  | 前端 bundle 无 CI budget | **Round 4 CI hygiene**    | gzip budget gate in CI |
| R4-\* (see UNRESOLVED) | API 安全/通知页缺口      | **Round 4 tasks 024–028** | 各 HTTP/FE pytest      |

### 2.5 Round 5+

| ID        | 问题                   | 清理阶段             | 关闭条件  |
| --------- | ---------------------- | -------------------- | --------- |
| R2-RISK-5 | gitleaks / 全量安全 CI | **Round 5 task 035** | CI job 绿 |

---

## 3. 待修复 — 本分支后续 / 下一 PR（按风险排序）

### 3.1 低风险 — 可立即做（不拆大模块）

| ID                    | 问题                                               | 清理阶段               | 状态     | 计划                                                                                   |
| --------------------- | -------------------------------------------------- | ---------------------- | -------- | -------------------------------------------------------------------------------------- |
| A05-P1-02 / A04-P2-02 | pytest 1 skip 未文档化                             | **本分支 hygiene**     | **DONE** | `docs/quality/KNOWN_PYTEST_SKIPS.md` + gate 测试引用                                   |
| A05-P1-01 / A04-P2-01 | `observation_mapper` / `db_inspector` 边界覆盖偏低 | **本分支 hygiene**     | **DONE** | `tests/test_observation_mapper.py` · `test_raw_store`/`test_ops_db_inspector` 边界用例 |
| A02-P3-01             | registry O-02/O-03 文案 drift                      | **本分支 docs**        | **DONE** | 同步三份 registry                                                                      |
| A06-P3-01             | `ROUND3_HANDOFF.md` Batch 2.5 “execute ready” 误读 | **本分支 docs**        | **DONE** | 改为 archived PASS + staged-only                                                       |
| A01-P1-02             | Batch3 必须 staged downstream 文档化               | **Batch 3 规划门禁**   | **DONE** | `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md` + gate 测试                            |
| A05-P3-01             | `.audit-sandbox*` 测试产物噪音                     | **merge 前 / release** | **DONE** | `.gitignore` 覆盖 `.audit-sandboxpytest-*/`                                            |
| A04-P3-01             | `except OSError: pass`                             | **不修复**             | 接受     | best-effort 路径；保持现状                                                             |

### 3.2 中风险 — 下一小 PR（仍不拆 ingestion 主模块）

| ID                                | 问题                                      | 清理阶段                    | 计划                                                                                                                                                             |
| --------------------------------- | ----------------------------------------- | --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| A08-P1-02                         | full pytest ~100s+，缺 test tier          | **Round 3 CI hygiene**      | **DONE（本分支）**                                                                                                                                               | `@pytest.mark.slow` on phase3/4 evidence tests · `pyproject.toml` marker · `KNOWN_PYTEST_SKIPS.md` quick profile |
| A08-P2-01 / R3-B25-PERF-BUDGET-01 | 未重跑 A6 production-equivalent benchmark | **CI nightly / Batch6 ops** | `uv run python scripts/production_equivalent_smoke.py --use-service-path --data-root .audit-sandbox/r3b275-audit` 新证据文件；不得作为 live-source authorization |
| A08-P2-02 / R3-B25-HYG-03         | 无 performance budget 报告文件            | **CI nightly / Batch6 ops** | `uv run python scripts/production_equivalent_smoke.py --use-service-path --data-root .audit-sandbox/r3b275-audit` 扩展 smoke 输出阈值；不得作为 live-source authorization |

### 3.3 高风险 — 大模块拆分 / 解耦（**后置**；必须可回滚）

| ID                                            | 问题                                       | 清理阶段                     | 回滚方案                                                                 |
| --------------------------------------------- | ------------------------------------------ | ---------------------------- | ------------------------------------------------------------------------ |
| A03-P1-01 / A04-P1-02 / A07-P1-01             | `ingestion.py` 1516 LOC；`commit_*` 369 行 | **Batch 2.5+ hygiene PR-2**  | 见 `docs/architecture/layer1_ingestion_refactor_rollback_plan.md`        |
| A03-P2-01 / A05-P2-03 / A06-P2-02 / A07-P2-01 | evidence writer 与 runtime 混置            | **PR-R2a DONE** (2026-06-21) | `ingestion_evidence.py` + facade re-export; pytest I1–I7 green on PR #25 |
| A03-P2-02 / A07-P2-02                         | phase sandbox bootstrap 重复               | **PR-R2b** (next)            | 提取 helper；对比 evidence JSON hash                                     |
| A03-P3-01                                     | markdown formatter 重复                    | **PR-2 第 3 步**             | 纯函数提取；快照测试                                                     |
| A03-P1-02                                     | Phase3/4 fetch 重复                        | **已部分关闭**               | `_fetch_staging_on_connection` 已存在；PR-2 仅补回归防 double fetch_log  |

**禁止:** 在单 PR 内同时改 runtime 事务语义 + 拆文件 + 改证据格式。

---

## 4. 已知 pytest skip（平台预期）

| 测试                                                                         | 原因                     | 可接受？          |
| ---------------------------------------------------------------------------- | ------------------------ | ----------------- |
| `test_ops_db_inspector.py::test_dbInspect_symlinkOutsideDataRoot_notCounted` | Windows 无目录 symlink   | 是；Linux CI 覆盖 |
| `test_raw_store.py::test_save_windowsLongPath_writesSuccessfully`            | 非 Windows skip          | 是                |
| `test_path_compat.py::*`                                                     | 非 Windows skip          | 是                |
| `test_batch25_production_data_gate.py`（条件 skip）                          | 本地无生产 DB / raw 证据 | 是；gate 设计     |

---

## 5. 操作规则

1. 关闭任一项 → 同步更新本文件 + `AUDIT_DEFERRED_REGISTRY.md` + `UNRESOLVED`/`RESOLVED` registry。
2. Batch 2.75 项 **无用户授权不得执行** live fetch 或生产 DB 写入。
3. ingestion 拆分必须遵循 `layer1_ingestion_refactor_rollback_plan.md` 分步与回滚检查表。
