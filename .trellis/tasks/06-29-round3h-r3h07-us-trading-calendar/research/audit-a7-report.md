# Audit A7 报告 — R3H-07 US Trading Calendar L2

| 字段       | 值                                                                       |
| ---------- | ------------------------------------------------------------------------ |
| 维度       | **A7** GitNexus / Loop / Ops                                             |
| 任务       | `06-29-round3h-r3h07-us-trading-calendar`                                |
| 协议       | `plan_protocol_version: 4.1`                                             |
| 仓库       | `C:\Users\Guang\Desktop\quant-monitor-desk`                              |
| 模式       | **只读 Audit**（不改代码、不 commit）                                    |
| Agent 模板 | `agents/database-administrator.md` · `agents/sre-engineer.md`（adjunct） |
| 对抗权威   | `agents/audit-adversarial-authority.md` · `agents/audit-boot-v4.1.md`    |
| 审计日期   | 2026-06-29                                                               |

---

## 维度证据

### 1. Loop 工程产物（v4.1）

| 检查项                | 命令 / 路径                                                                        | 结果                                                                                           |
| --------------------- | ---------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `context_pack.json`   | `.trellis/tasks/06-29-round3h-r3h07-us-trading-calendar/context_pack.json`         | **存在**；`modules` 含 `ops`/`datasources`/`layer4_markets`；`source_authorities` 路径均可解析 |
| `loop_manifest.json`  | 同上目录                                                                           | **存在**；§2 AC id 齐全（11 项）                                                               |
| `evidence_index.json` | 同上目录                                                                           | **存在**；`execute`/`audit` 均为空对象（Plan freeze 默认 stub）                                |
| `audit_matrix.json`   | 同上目录                                                                           | **缺失**（`context_pack.required_evidence` 列出；A9 合并前预期）                               |
| `loop_maintain`       | `uv run python scripts/loop_maintain.py`                                           | **exit 0** — `OK: loop maintain`                                                               |
| `check_task_evidence` | `uv run python scripts/check_task_evidence.py <task_dir>`                          | **exit 0** — `OK: task evidence`                                                               |
| `authority_graph`     | `specs/context/authority_graph.yaml` · `ops.implementation` → `backend/app/ops/**` | **PASS** — 新文件 `us_trading_calendar.py` 落在 `ops` 模块映射内，无需新包行                   |
| `test_catalog`        | `tests/test_catalog.yaml`                                                          | **已登记** `tests/test_us_trading_calendar.py`                                                 |

### 2. `gitnexus-audit-summary.md`（7.pre）

| 检查项                     | 结果                                                                      |
| -------------------------- | ------------------------------------------------------------------------- |
| 文件存在                   | **是** — `research/gitnexus-audit-summary.md`（当前 untracked，内容可读） |
| 记录 `detect_changes` 局限 | **是** — 写明 uncommitted 时 compare → 0 symbols                          |
| 列出 git diff 触达面       | **是** — SSOT / C3 / G4 / 测 / fixture / 索引                             |
| Blast radius 摘要          | **是** — MEDIUM；引用 Plan `gitnexus-summary.md`                          |

### 3. GitNexus `detect_changes` vs `git diff` 真值（uncommitted）

| 来源                                                   | 已跟踪变更文件数                          | 未跟踪代码文件                                                                                      | `changed_symbols`                  |
| ------------------------------------------------------ | ----------------------------------------- | --------------------------------------------------------------------------------------------------- | ---------------------------------- |
| `detect_changes({scope:"all"})`                        | **15**                                    | 不计入                                                                                              | **0**                              |
| `detect_changes({scope:"unstaged"})`                   | **15**                                    | 不计入                                                                                              | **0**                              |
| `detect_changes({scope:"compare", base_ref:"master"})` | —                                         | —                                                                                                   | **MCP 后端不可用**（单次调用失败） |
| `git diff master --name-only`（工作树）                | **14** 代码/索引相关 + 2 任务文档         | `backend/app/ops/data_health_profiles/us_trading_calendar.py` · `tests/test_us_trading_calendar.py` | —                                  |
| `git diff master --stat backend/ tests/`               | **13** 已跟踪（不含 2 个 untracked SSOT） | 同上 2 文件                                                                                         | —                                  |

**对齐结论：**

- 已跟踪 modified 文件与 `detect_changes` 的 `changed_files: 15` **基本一致**（含 `.trellis` 任务文档与 generated map）。
- **未对齐：** 2 个核心交付物仍为 **untracked**，不出现在 `detect_changes` 与 `git diff master` 统计中；`changed_symbols` 恒为 0，无法支撑 AUDIT.plan「impact · detect_changes」的符号级回归面。

### 4. GitNexus `impact` / `query`（本维必用）

| 调用                                                                                                                | 结果                                                                                 |
| ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| `impact({target:"is_trading_day", direction:"upstream"})`                                                           | **not found**                                                                        |
| `impact({target:"recent_window_start", file_path:"backend/app/datasources/fetch_window.py", direction:"upstream"})` | **not found**                                                                        |
| `impact({target:"MarketStructureBuilder", direction:"upstream"})`                                                   | **not found**                                                                        |
| `query({query:"US trading calendar fetch window"})`                                                                 | **有结果** — 命中 `fetch_payload` / `recent_window_start` 等既有流程（索引内旧符号） |

**说明：** Plan 阶段 `research/gitnexus-summary.md` 已记录 MEDIUM blast radius；Audit 时点 MCP `impact` 无法锚定 Execute 新增/修改符号，与未跟踪文件 + 索引未刷新一致。

### 5. Ops / DBA adjunct（本卡 AC-NO-DDL）

| 检查项                        | 命令                                                              | exit        | 结论                                                                                |
| ----------------------------- | ----------------------------------------------------------------- | ----------- | ----------------------------------------------------------------------------------- |
| 无 migration 面               | `git diff master -- specs/schema/ migrations/ scripts/init_db.py` | 0（无输出） | **PASS**                                                                            |
| CN 日历隔离                   | `git diff master -- cn_trading_calendar.py`                       | 0           | **PASS**                                                                            |
| 生产 DB / 新写库 CLI          | 静态：diff 未触 `init_db.py` · `qmd_ops.py` · migrations          | —           | **PASS**                                                                            |
| SSOT 运维形态                 | `us_trading_calendar.py` 纯内存有界表；无 DuckDB/文件写           | —           | **PASS**                                                                            |
| init/migrate 两遍 + kill 场景 | —                                                                 | **N/A**     | AUDIT.plan A7 本卡冻结为 **GitNexus/impact**；无 DDL 面，不适用标准 DBA walkthrough |

### 6. DOUBT（doubt-driven-development）

| 问题                                                      | 结论                                                                     |
| --------------------------------------------------------- | ------------------------------------------------------------------------ |
| `detect_changes` 0 symbol 是否掩盖真实回归面？            | **是** — 须以 `git diff` + pytest 补位；7.pre 已声明，但符号级门禁仍缺口 |
| 未跟踪 SSOT 是否导致 finish-work 前索引永久滞后？         | **是** — merge 前须 `git add` + `node .gitnexus/run.cjs analyze`         |
| `loop_manifest` 全 `pending` 与 INDEX §1 `[x]` 是否一致？ | **否** — Execute 步勾选未回写 manifest（loop 仪表盘漂移）                |

---

## §维度裁决

**FAIL**

---

## 计划内问题

| ID       | P   | 标题                                              | 锚点                                                                       | 根因                                                                                                       | 修复方案                                                                                                                        | 验证                                                                                                                |
| -------- | --- | ------------------------------------------------- | -------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| A7-P2-01 | P2  | `detect_changes` 与 git 真值未覆盖 untracked SSOT | `research/gitnexus-audit-summary.md` · `git status` · MCP `detect_changes` | 核心文件 `us_trading_calendar.py` / `test_us_trading_calendar.py` 未 `git add`；GitNexus 仅统计已跟踪 diff | `git add` 两文件后重跑 `node .gitnexus/run.cjs analyze`；再 `detect_changes({scope:"all"})` 应含新文件且 `changed_symbols` 非空 | `detect_changes` 的 `changed_files` ≥ 17 且 `changed_symbols` 含 `is_trading_day` 或 `us_trading_calendar` 相关符号 |
| A7-P2-02 | P2  | Audit 时点 `impact` 无法锚定任务变更符号          | AUDIT.plan §1 A7 · MCP `impact`                                            | 索引未含 Execute 新增符号；与 A7-P2-01 同源                                                                | 同 A7-P2-01；并对 `is_trading_day` / `recent_window_start` 跑 `impact({direction:"upstream"})`                                  | `impact` 返回 `risk` ∈ {LOW,MEDIUM,HIGH} 且 `impactedCount` > 0；与 `gitnexus-summary.md` MEDIUM 叙述一致           |

## 计划外发现

| ID       | P   | 标题                                       | 锚点                                                                | 根因                                        | 修复方案                                                                                             | 验证                                                            |
| -------- | --- | ------------------------------------------ | ------------------------------------------------------------------- | ------------------------------------------- | ---------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| A7-P3-01 | P3  | `context_pack.json` tests[] 未登记新模块测 | `context_pack.json` L211–299 vs `tests/test_us_trading_calendar.py` | Plan freeze 后未刷新 context pack           | `uv run python scripts/loop_maintain.py --fix` 或手动在 `tests[]` 增加 `test_us_trading_calendar.py` | `context_pack.json` 含该路径；`validate_context_pack` 仍 exit 0 |
| A7-P3-02 | P3  | `loop_manifest.json` AC 状态全为 pending   | `loop_manifest.json` · `EXECUTION_INDEX.md` §1                      | Execute 勾选 `[x]` 未同步 manifest `status` | Repair/Finish 前按 AC 验证结果将对应项标为 `closed`/`pass` 并写入 `repair_items`（若 FAIL）          | `loop_dashboard` 或 handoff 检查 manifest 与 INDEX 一致         |

已对抗搜索：`specs/schema/` · `migrations/` · `init_db.py` · `cn_trading_calendar.py` · `qmd_ops.py` · `authority_graph.yaml` · ops CLI 写路径 · production DB promote 链；除上表外无计划外 migration/主库写面。

---

_A7 只读审计完成。未修改仓库代码。_
