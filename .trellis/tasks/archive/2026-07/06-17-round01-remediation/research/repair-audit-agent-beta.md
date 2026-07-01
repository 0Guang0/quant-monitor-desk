# Round 0/1 GPT Repair — 独立审计（Agent Beta）

> **复核日期：** 2026-06-17  
> **输入：** `GPT_ROUND01_REPAIR_STATUS.md` · `REPAIR.plan.md` · 源码交叉核对 · 本地验收命令  
> **视角：** 安全、prod-path、CI 对齐、WriteManager/ResourceGuard 边界（对抗性）  
> **对照：** Round 2 Batch A `MASTER.plan.md` v1.3 · `adversarial-audit-remediation.md`

---

## 1. Verdict

### **PASS_WITH_FIXES**

Round 0/1 GPT repair **核心代码主张已落地**，pytest + coverage + init_db 沙箱 + migration 003 列扩展 **本地验收通过**。但存在 **3 项合并前必修**（其中 1 项会导致 CI `ruff` job 失败），以及 **2 项 repair 引入的文档/编号漂移**，Batch A Execute 前须同步。Repair 状态文档对 `ruff` 的「全绿」声明 **不实**。

| 维度                   | 结论                                                                 |
| ---------------------- | -------------------------------------------------------------------- |
| 代码 vs GPT 主张       | **基本一致**（见 §2）                                                |
| 验收命令               | **pytest/coverage/init_db/compileall/grep 通过**；**ruff 失败**      |
| Batch A migration 序号 | **MASTER.plan 已用 004**；**DECISIONS.md 仍写 003_ingestion** → 漂移 |
| 新引入问题             | **5 条**（§5），含 1 条 CI 硬失败                                    |

**不建议 BLOCK 整个 repair**：功能与测试 substantively 完成；必修项为单行 lint + 文档同步，非架构回滚。

---

## 2. GPT 主张 vs 代码交叉核对

### 2.1 `connection.py` — reader pragmas（P0-3）

| 主张                                        | 证据                                                                                        | 判定         |
| ------------------------------------------- | ------------------------------------------------------------------------------------------- | ------------ |
| `reader()` 在 yield 前调用 `_apply_pragmas` | `backend/app/db/connection.py:174-177`                                                      | **✓ 已修复** |
| 测试覆盖 threads/memory/temp                | `test_applyPragmas_readerProfile_setsThreadsAndMemory` · `test_reader_appliesTempDirectory` | **✓**        |

**残留风险（低）：** reader 与 writer 共用 `_apply_pragmas`，会在 `DATA_ROOT/cache/duckdb_tmp` 上 `mkdir`；只读连接侧效应可接受，但多进程 reader 并发 mkdir 非原子（Windows 上通常无害）。

### 2.2 `resource_guard.py` — evaluate + INSERT 列（P0-4）

| 主张                                        | 证据                                                                       | 判定                                                             |
| ------------------------------------------- | -------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| `ResourceSnapshot` 含 temp/cache/system pct | `resource_guard.py:26-34` · `snapshot():248-264`                           | **✓**                                                            |
| `evaluate()` 全信号                         | `evaluate():89-183` — memory/disk/project/rss/temp/cache/system mem%/disk% | **✓**（超出 REPAIR.plan §8.4「system\_\* deferred」口径，见 §5） |
| migration 003 扩展列                        | `003_resource_guard_metrics.sql` ALTER ×4                                  | **✓**                                                            |
| INSERT 对齐扩展列                           | `check():277-299` 12 个 metric 列 + `created_at`                           | **✓**                                                            |
| 测试                                        | `test_check_lowMemorySnapshot_writesExtendedGuardLogColumns` 断言 4 新列   | **✓**                                                            |

**边界（对抗）：**

- `check()` 在传入 `con` 时无条件 `BEGIN`/`COMMIT`（`272-304`）。若调用方已在 `ConnectionManager.writer()` 事务内嵌套调用，DuckDB 无 SAVEPOINT → **可能 abort 外层事务**；**无测试**覆盖此路径。
- `WARN` 决策 **也写** `resource_guard_log`（`test_check_warnDecision_writesGuardLog`），但 `format_pause_event` 仅对 PAUSE/HARD_STOP 打 stderr。运维信号 **不对称**（DB 有记录、操作员无哨兵）。

### 2.3 `write_manager.py` — `own_transaction=False`（P1 repair）

| 路径                                     | 行为                                    | 证据                                                       | 判定                       |
| ---------------------------------------- | --------------------------------------- | ---------------------------------------------------------- | -------------------------- |
| ValidationRejected / GateError           | 同连接 `_write_audit`，不 ROLLBACK 外层 | `229-241` · `test_write_ownTransactionFalse_stubFail_*`    | **✓**                      |
| `duckdb.Error` + `own_transaction=True`  | ROLLBACK + 第二连接 audit               | `242-254`                                                  | **✓**                      |
| `duckdb.Error` + `own_transaction=False` | 返回 FAILED **无 audit 行**             | `255-260` · `test_write_ownTransactionFalse_duckdbError_*` | **✓ 按设计**；**审计缺口** |

设计注释（L255）明确：外层事务可能已 aborted，禁止第二 `duckdb.connect`。合理，但 **与 validation 失败路径不对称** — 嵌入事务的 SQL 失败 **无 `write_audit_log` 行**，仅 `WriteResult`。下游若依赖 audit 表做 SLA 追踪，此为 **已知盲区**。

### 2.4 `config.py` — `_path_env`（SEC-4 / 空 env）

| 主张                        | 证据                                             | 判定                           |
| --------------------------- | ------------------------------------------------ | ------------------------------ |
| 空 `QMD_DATA_ROOT` 回退默认 | `_path_env():11-15` · `test_dataRoot_emptyEnv_*` | **✓**                          |
| `expanduser` 支持 `~`       | L15 · `test_dataRoot_tildePath_*`                | **✓（超出 GPT 清单的加分项）** |

**安全注记：** `_path_env` 不校验路径是否在 repo 内；`QMD_DATA_ROOT=/etc` 等可被接受。Round 1 范围可接受；Batch D smoke 前应文档化「勿指向系统目录」。

---

## 3. 验收命令执行记录

> 环境：Windows · Python 3.14.6 · 2026-06-17 · `required_permissions: all`

| 命令                                                               | 结果               | 证据摘要                                                                |
| ------------------------------------------------------------------ | ------------------ | ----------------------------------------------------------------------- |
| `pytest -q --cov=backend --cov-fail-under=75`                      | **PASS** exit 0    | 114 passed；coverage **93.97%**（门槛 75%）                             |
| `QMD_DATA_ROOT=.audit-sandbox/data python scripts/init_db.py` ×2   | **PASS**           | 首次 `applied ['003_resource_guard_metrics']`；二次 `none (up to date)` |
| DuckDB `SHOW TABLES` + `resource_guard_log` 列                     | **PASS**           | 12 列含 4 个 003 扩展列；applied 含 `003_resource_guard_metrics`        |
| `python -m compileall -q backend scripts tests`                    | **PASS** exit 0    | —                                                                       |
| `grep -riE 'WriteManager\|write_manager' backend/app/datasources/` | **PASS**（无匹配） | 与 `.github/workflows/ci.yml` L20-25 一致                               |
| `ruff check .`                                                     | **FAIL** exit 1    | `write_manager.py:255` E501 行宽 102 > 100                              |
| `python scripts/check_doc_links.py`                                | **PASS**           | 107 md 文件                                                             |

### 3.1 prod-path / audit-sandbox 隔离

- `init_db` 在 `QMD_DATA_ROOT=.audit-sandbox/data` 下 **仅写** `.audit-sandbox/data/duckdb/quant_monitor.duckdb`。
- 仓库内 **预存** `data/duckdb/quant_monitor.duckdb`（开发残留）；本次 audit **未证明** sandbox 命令创建或修改了 `data/`（mtime 未对比）。**建议：** 未来 audit 脚本在跑 sandbox 前记录 `data/` mtime 或临时 rename。

### 3.2 CI 与 REPAIR.plan 偏差

| 项              | `ci.yml`          | `REPAIR.plan` §5 Tier A | 判定                                  |
| --------------- | ----------------- | ----------------------- | ------------------------------------- |
| compileall 范围 | `backend scripts` | `backend scripts tests` | **CI 更窄** — tests 目录未 compile    |
| ruff            | 有                | 有                      | **本地失败** → push 后 backend job 红 |

---

## 4. Batch A migration 序号（004 vs 003）

| 工件                                    | migration 003 含义               | migration 004 含义          | 冲突？         |
| --------------------------------------- | -------------------------------- | --------------------------- | -------------- |
| **Round 1 repair（已落地）**            | `003_resource_guard_metrics.sql` | —                           | —              |
| **MASTER.plan v1.3**                    | 已占用（resource guard）         | `004_ingestion_sources.sql` | **无序号冲突** |
| **DECISIONS.md §3**                     | 仍写 `003_ingestion_sources.sql` | 未提及 004                  | **⚠ 文档冲突** |
| **adversarial-audit-remediation.md E4** | 仍写 `003_ingestion_sources.sql` | —                           | **⚠ 过时**     |

**结论：** 代码与 `MASTER.plan` **已对齐 004**；`docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/DECISIONS.md` §3 **未随 repair 重编号更新** — Execute 若只读 DECISIONS 会 **重复占用 003 或建错文件名**。属 **repair 引入的文档债务**，非代码 bug。

`MASTER.plan` L345 脚注「003 仅在 §8.1 RED 之后」语境混乱（应指 **004**）；Implementer 可能误读。

---

## 5. Repair 新引入问题（不在原 GPT 清单）

| ID       | 严重度           | 问题                                                 | 证据                                                                                           | 建议                                                   |
| -------- | ---------------- | ---------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| **N-01** | **P1 / CI 阻塞** | `ruff check .` 失败                                  | `write_manager.py:255` E501；`GPT_ROUND01_REPAIR_STATUS.md` L38 声称 ruff 全绿 **不实**        | 折行或缩短注释；合并前必跑 ruff                        |
| **N-02** | **P1**           | DECISIONS §3 migration 编号过时                      | `DECISIONS.md:38` `003_ingestion_sources` vs 实际 `003_resource_guard_metrics` + Batch A `004` | 更新 §3 为 `004_ingestion_sources`                     |
| **N-03** | P2               | `ResourceGuard.check()` 嵌套 `BEGIN` 未测            | `resource_guard.py:274-304`                                                                    | Batch D 或 repair 跟进：传入 writer 事务内调用时的语义 |
| **N-04** | P2               | `own_transaction=False` + SQL 错误无 audit           | `write_manager.py:255-260`                                                                     | 文档化于 `write_manager.md`；或 caller 负责补 audit    |
| **N-05** | P3               | `system_*_pct` 已实现但 REPAIR.plan §8.4 标 deferred | `evaluate():162-181` vs `REPAIR.plan` L176                                                     | 统一 DECISIONS/performance_limits 口径                 |

**非新引入但需点名：** `test_schema_contract.py` 已覆盖 003_resource_guard（`migration_names` L48），与 Batch A P0-2 remediation 要求一致 — **repair 侧已做好**；Batch A 004 扩展仍待 Execute。

---

## 6. 安全与 prod-path 快审

| 检查项                         | 结果                                                                        |
| ------------------------------ | --------------------------------------------------------------------------- |
| SQL 标识符注入（WriteManager） | `quote_ident` 在 `_validate_request`；`test_write_invalidIdentifier_*` 覆盖 |
| 写锁绕过（datasources）        | grep 无 WriteManager；仅 `__init__.py` stub                                 |
| 空 env → `Path("")` 污染 prod  | `_path_env` 已封堵                                                          |
| init_db 默认路径               | `DATA_ROOT/duckdb/quant_monitor.duckdb`；audit 须 `QMD_DATA_ROOT`           |
| ResourceGuard 日志事务         | 失败时 ROLLBACK+raise；不吞异常                                             |
| 前端 CVE                       | 未在本轮复跑 `npm audit`（GPT 主张已修复）；CI workflow 含 high 门槛        |

---

## 7. 必修项（合并 / Batch A 前）

1. **修 `write_manager.py:255` E501** — 否则 `.github/workflows/ci.yml` backend job 失败。
2. **更新 `DECISIONS.md` §3**：`003_ingestion_sources` → `004_ingestion_sources`；注明 003 已被 `resource_guard_metrics` 占用。
3. **更正 `GPT_ROUND01_REPAIR_STATUS.md` §验收**：ruff 当前非全绿。
4. **（建议）** `adversarial-audit-remediation.md` E4 行同步 004。
5. **（建议）** `ci.yml` compileall 加入 `tests`，与 REPAIR.plan Tier A 对齐。

---

## 8. 签核

| 角色                 | 结论                                                               |
| -------------------- | ------------------------------------------------------------------ |
| Agent Beta（本报告） | **PASS_WITH_FIXES** — repair 实质完成；合并前修 ruff + DECISIONS   |
| Round 2 Batch A 准入 | **条件放行** — 完成 §7 1–2 后可 `task.py start`                    |
| 对抗立场             | GPT 状态文档 **过度乐观**（ruff）；migration 重编号 **文档未跟进** |

**证据工件：** 本文件 · 本地 pytest/coverage/init_db/duckdb 查询输出 · 源码行号引用 · `MASTER.plan` grep
