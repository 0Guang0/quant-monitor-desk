# Audit A7 报告 — B3V-SYNC Sync Job Support Matrix & Crash-window Recovery

| 字段 | 值 |
|------|-----|
| 维度 | **A7** Ops / DBA / SRE |
| 任务 | `round3v-sync-support-matrix-recovery` · Manifest `B3V-C04` |
| Worktree | `C:/Users/Guang/Desktop/quant-monitor-desk-wt-b3v-sync` |
| 分支 | `fix/round3v-sync-support-matrix-recovery` |
| 模式 | **只读 Audit**（不改代码、不 commit） |
| Agent 模板 | `database-administrator.md` · `sre-engineer.md` · `devops-incident-responder.md` |
| 对抗权威 | `agents/audit-adversarial-authority.md` |
| 审计日期 | 2026-06-28 |

---

## 1. AUDIT.plan §1 与默认 A7 冻结条件

`AUDIT.plan.md` §1 **未覆写 A7**；按 `audit-skill-registry.md` §2 默认矩阵执行：

| 项 | 冻结要求 | 审计结论 |
|----|----------|----------|
| migration / schema | 本任务不得改 DDL / migration | **PASS** — `git diff master` 对 `specs/schema/`、`backend/app/db/migrations/`、`scripts/init_db.py` **零 diff** |
| write 契约 | 不得改 `write_contract.yaml` / WriteManager 写模式 | **PASS** — 同上路径零 diff |
| registry 三件套 | 分支禁止 commit 闭合 | **PASS** — 仅 `research/registry_proposed_delta.yaml`（协调员队列） |
| init/migrate 幂等 | 两遍 `init_db`；第二次 `applied` 为空或等价 | **PASS** — 见 §3.7 |
| 异常场景（必做 1 项） | kill migrate **或** 任务等价异常 | **PASS（替代）** — 无 migration 面；以 ADR-001 **crash-window**（写提交后、COMPLETED 前中断 + recovery）替代 kill-migrate |
| 失败可观测 | exit code + 可定位错误 | **PASS** — recovery 非法状态 `ValueError`；hook 非 pytest 环境 `ValueError` |

**说明：** 分支相对 `master` 的代码 diff 仅 `tests/conftest.py`（R3G/R3H auth YAML bootstrap）；B3V-SYNC 交付物（`sync/**`、`sync_job_contract.yaml`、crash/recovery 测试）已在 `master` 基线。A7 审计对象为**任务 AC 所覆盖的运行时数据路径**，不限于未 merge 的 branch diff。

---

## 2. Diff 范围与数据面核对

### 2.1 分支相对 master 变更

| 文件 | 类别 | A7 相关 |
|------|------|---------|
| `.trellis/tasks/round3v-sync-support-matrix-recovery/**` | 任务元数据 / evidence | 非 DB 面 |
| `tests/conftest.py` | pytest bootstrap | 物化 `.audit-sandbox/round3g|round3h` auth YAML；**不写 DuckDB** |
| `docs/generated/*` · `WAVE0_BATCH3V_TO_ISSUES_INDEX.md` | 文档索引 | 非 DB 面 |

### 2.2 显式未触及路径（对抗性 diff + grep）

- `specs/schema/schema.sql`
- `backend/app/db/migrations/**`
- `scripts/init_db.py`
- `specs/contracts/write_contract.yaml`
- `backend/app/db/write_manager.py`（只读依赖，未改 `SUPPORTED_MODES`）
- `specs/datasource_registry/source_registry.yaml` 等 registry 三件套

### 2.3 运行时数据路径影响（DBA）

| 组件 | 写库？ | 说明 |
|------|--------|------|
| `IncrementalJobRunner.run` | **是（既有路径）** | 写事务内 clean write；`write_id` 落 `data_sync_job`；COMPLETED 在事务外（ADR-001） |
| `post_write_pre_complete_hook` | **否（测试注入）** | 仅 `PYTEST_CURRENT_TEST` 环境允许；生产 `ValueError` fail-closed |
| `recover_stuck_writing_job` | **仅状态迁移** | `WRITING`+`write_id` → `COMPLETED`；**不**调用 WriteManager 二次写入 |
| `DeferredJobTypeError` | **否** | reserved job 在 DB 写入前即拒绝 |

**GitNexus：** `impact(recover_stuck_writing_job)` → target not in index（worktree 未索引）；已手工对照 `orchestrator.py` / `runners.py` / `tests/test_sync_orchestrator.py` 调用链。

**DOUBT（DBA）：** 第二次 init 是否仅「不报错」？→ 第二次 `applied none (up to date)`；`test_schema_migration.py` 10/10 绿（§3.7）。

**DOUBT（SRE）：** crash 后是否静默 COMPLETED？→ hook 抛错后 `status=WRITING` 且 `write_id` 非空；recovery 前 clean 行数不变（§3.7）。

---

## 3. §3.7 运维证据表

### 3.1 Database Administrator（幂等 / schema 一致性）

| 步骤 | 命令 | exit | 关键输出 / 证据 |
|------|------|------|-----------------|
| schema/migration diff | `git diff master -- specs/schema/ backend/app/db/migrations/ scripts/init_db.py specs/contracts/write_contract.yaml` | 0 | **空输出** — 零 migration 改动 |
| migration 回归 | `uv run pytest tests/test_schema_migration.py -q --basetemp=.trellis/tasks/round3v-sync-support-matrix-recovery/.audit-sandbox/pytest-mig` | **0** | `..........` 10 passed |
| init_db 第 1 遍 | `QMD_DATA_ROOT=<sandbox/data> uv run python scripts/init_db.py --db <sandbox/duckdb/quant_monitor.duckdb>` | **0** | `applied ['001_foundation', …, '012_migration_residuals']`（12 项） |
| init_db 第 2 遍 | 同上 | **0** | `applied none (up to date)` |

### 3.2 SRE Engineer（crash-window / fail-closed）

| 场景 | 命令 | exit | 日志 / 证据 |
|------|------|------|-------------|
| 写后 crash 留 WRITING+write_id | `pytest …::test_syncJob_incremental_crashWindow_leavesWritingWithWriteId` | **0** | hook 抛 `RuntimeError` 后 DB `status=WRITING`，`write_id` 非空 |
| recovery 无二次写 | `pytest …::test_syncJob_incremental_recoverStuckWriting_completesWithoutDoubleWrite` | **0** | recovery 后 `COMPLETED`；clean 表行数 crash 前后一致 |
| recovery 非法状态拒绝 | `pytest …::test_syncJob_recoverStuckWriting_rejectsInvalidState` | **0** | `CREATED` 作业 → `ValueError` 含 `WRITING` |
| hook 生产路径拒绝 | `pytest …::test_syncJob_incremental_hook_rejectedOutsidePytest`（Execute 证据） | **0** | `sync_adapter_bypass_allowed=False` → `ValueError` pytest-only |
| WriteManager 回归 | `uv run pytest tests/test_write_manager.py -q` | **0** | 22 passed（与 crash 三测合计 25 passed） |
| Execute §9.7 交叉 | `research/execute-evidence/9.7-green.txt` | 0 | 2 passed；与上表 crash/recovery 一致 |

**异常场景选定：** ADR-001 crash-window（写提交后进程中断）+ `recover_stuck_writing_job` 恢复 — 替代本任务不适用的 kill-migrate。

### 3.3 DevOps Incident Responder（RCA / 事故面）

| 检查项 | 结论 |
|--------|------|
| 新 production clean-write 入口 | **无** — recovery 仅 `SyncJobStateMachine.transition` |
| migration 中途失败面 | **N/A** — 零 migration diff |
| Execute evidence 可 RCA | `9.7-red.txt` 记录 RED（无 `recover_stuck_writing_job`）；`9.7-green.txt` 实现后 2 passed — 非占位符 |
| 全量 pytest | `full-pytest-green.txt`：1744 passed / 34 failed — 失败为 R3G auth YAML 缺失（`conftest` bootstrap 已修，未 commit）；**非** B3V-SYNC sync 面 |

---

## 4. 计划外发现

| ID | 发现 | 严重度 | 说明 |
|----|------|--------|------|
| F1 | 分支 diff 不含 `backend/app/sync/**` — 实现已在 master | NON-BLOCKING | A7 已按交付物行为审计；合并协调员须确认 PR 范围与 evidence 一致 |
| F2 | `recover_stuck_writing_job` 不校验 `write_id` 在 write 审计表存在 | NON-BLOCKING | 信任 `data_sync_job.write_id`；误 recovery 需 ops 误调 utility；测试覆盖 WRITING+write_id 正向路径 |
| F3 | recovery `SELECT` 用 `reader()`，transition 在连接外 | NON-BLOCKING | 单写者 DuckDB + ops 手工 recovery；多进程并发 recovery 非本任务范围 |
| F4 | `tests/conftest.py` R3G/R3H bootstrap 未在 master | NON-BLOCKING | 改善全量 pytest 环境；与 sync DB 路径无关；建议随分支 merge |
| F5 | GitNexus index 未收录 worktree / `recover_stuck_writing_job` | NON-BLOCKING | 已手工 blast-radius 审查；建议 merge 前 `node .gitnexus/run.cjs analyze` |

**对抗搜索声明：** 已对照 `specs/schema/`、`migrations/`、`write_contract.yaml`、`WriteManager`、`sync_job_contract.yaml`、`ADR-001`、`init_db` 两遍输出、crash/recovery pytest；除上表外无计划外 DB 污染或 migration 面。

---

## 5. 判定

| 维度 | 判定 | 理由 |
|------|------|------|
| **AUDIT.plan A7（默认矩阵）** | **PASS** | 零 schema/migration/write 契约 diff；init 幂等；crash-window 异常场景可恢复且可观测 |
| DBA 幂等 | **PASS** | init 第二遍 `applied none`；migration pytest 10/10 |
| SRE crash-window | **PASS** | WRITING+write_id 可检测；recovery 无二次写；非法状态 fail-closed |
| Incident 生产写面 | **PASS** | 无新 WriteManager 模式；hook pytest-only |

### 移交主会话 / 其他维度

- registry 闭合仍由主会话 §7.3 批处理（`repair-evidence/registry-ready.md`）。
- **F4** 全量 pytest 34 fail 建议 merge `conftest.py` 后 A8 复跑；不阻塞 A7 PASS。

---

## 6. 参考命令（sandbox 复现）

```powershell
cd C:\Users\Guang\Desktop\quant-monitor-desk-wt-b3v-sync

# 静态边界
git diff master -- specs/schema/ backend/app/db/migrations/ scripts/init_db.py specs/contracts/write_contract.yaml

# migration 回归
uv run pytest tests/test_schema_migration.py -q `
  --basetemp=.trellis/tasks/round3v-sync-support-matrix-recovery/.audit-sandbox/pytest-mig

# init 幂等
$sb = ".trellis/tasks/round3v-sync-support-matrix-recovery/.audit-sandbox"
$env:QMD_DATA_ROOT = (Resolve-Path "$sb/data").Path
uv run python scripts/init_db.py --db "$sb/duckdb/quant_monitor.duckdb"
uv run python scripts/init_db.py --db "$sb/duckdb/quant_monitor.duckdb"

# crash-window + WriteManager
uv run pytest `
  tests/test_sync_orchestrator.py::test_syncJob_incremental_crashWindow_leavesWritingWithWriteId `
  tests/test_sync_orchestrator.py::test_syncJob_incremental_recoverStuckWriting_completesWithoutDoubleWrite `
  tests/test_sync_orchestrator.py::test_syncJob_recoverStuckWriting_rejectsInvalidState `
  tests/test_write_manager.py -q `
  --basetemp=.trellis/tasks/round3v-sync-support-matrix-recovery/.audit-sandbox/pytest-a7-sync
```

---

*A7 只读审计完成。未修改仓库代码。*
