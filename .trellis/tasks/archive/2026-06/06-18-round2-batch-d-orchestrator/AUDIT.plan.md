# AUDIT 计划 — Round 2 Batch D DataSyncOrchestrator

> Audit 入口 · 2026-06-18  
> Audit agent 只读本文件 + `audit.jsonl` + `MASTER.plan.md` §2/§9/§10 + Execute evidence。

---

## 0. 元信息

| 字段 | 值 |
|------|-----|
| slug | `06-18-round2-batch-d-orchestrator` |
| 关联 Execute | `MASTER.plan.md` |
| Audit 输出 | `audit.report.md` |
| Repair 入口 | `REPAIR.plan.md` |
| 判定 | PASS / PASS_WITH_FIXES / FAIL |

### 0.1 维度映射（相对 `audit-skill-registry.md` 默认）

本任务 **有意定制** 维度焦点（skill 名与 registry 一致，验证焦点不同）：

| 维 | 本任务焦点 | registry 默认侧重 |
|----|-----------|-------------------|
| A2 | `backend/app/sync/*` 结构、§6.5 接线 | ponytail 过度工程 |
| A3 | migration 006 + init_db 幂等 | 安全威胁面 |
| A4 | sync/orchestration 语义测试 + AC-2 六种 job_type | 通用代码质量 |
| A7 | ResourceGuard + eco 分片 + scope | 运维 walkthrough |

A6 性能 **SKIP**（见 §2 末）；不表示遗漏。

---

## 1. Audit Skill freeze

| 维度 | Skill | 本任务 | 读取 | 输出 |
|------|-------|--------|------|------|
| A1 Spec | trellis-check | 必做 | `check.jsonl` + specs | audit.report §A1 |
| A2 Code review | ponytail-review | 必做 | `backend/app/sync/*` | audit.report §A2 |
| A3 DB/migration | diagnose | 必做 | 006 + init_db | audit.report §A3 |
| A4 Tests | qa | 必做 | sync tests + evidence | audit.report §A4 |
| A5 Traceability | trace-ac | 必做 | MASTER §2 + evidence | audit.report §A5 |
| A6 Security | security | 必做 | orchestrator errors/logs | audit.report §A6 |
| A7 Resource/scope | resource-review | 必做 | ResourceGuard + scope | audit.report §A7 |
| A8 Docs/handoff | docs-review | 必做 | BATCH_D_STATUS + README | audit.report §A8 |
| A9 Risk summary | 主会话 | 必做 | A1–A8 | audit.report §4 |

---

## 2. 维度验证矩阵

### A1 Spec compliance

Verify:

- `research/original-plan-trace.md` maps 014 → MASTER §2 AC-1…AC-12.
- `implement.jsonl` lists GLOBAL + 014 + contracts + Batch C wiring paths (`validation_gate`, `write_manager`, `source_registry`, validator modules).
- Job types/statuses match `specs/contracts/sync_job_contract.yaml`.
- VALIDATING/Reconcile stages match `data_quality_rules.yaml` and `source_conflict_rules.yaml`.
- Runtime flow matches `docs/architecture/03_runtime_flows.md` and `04_data_architecture.md`.
- `check.jsonl` covers ROUND README, BATCH_B/C ledgers, write_manager module spec, 004/005 migrations, Batch C wiring code, `source_registry.yaml`.
- `sync_to_db(tombstone_missing=True)` used for registry bootstrap; no duplicate tombstone implementation.
- Paths use `backend/app/sync/*`, not `backend/sync/*`.

**命令：** `python .trellis/scripts/task.py validate 06-18-round2-batch-d-orchestrator`  
**对抗触发器：** 必须找到 ≥1 个 implement.jsonl 未声明但 orchestrator 引用的模块；找不到则说明为什么。

### A2 Code review

Verify:

- Orchestrator does not SQL-write clean tables directly.
- No duplicate reconcile logic vs `SourceConflictValidator`.
- No WriteManager import in adapters.
- State transitions centralized in `jobs.py`.
- `adapter.fetch(..., con=writer_con, job_id=...)` on FETCHING path (§6.5).

**对抗触发器：** 必须找到 ≥1 处 ≥20 行可合并/删除；找不到则说明为什么。

### A3 DB/migration

Verify:

- `006_ingestion_sync.sql` idempotent; 004/005 unchanged.
- `data_sync_job` + `job_event_log` columns match `schema.sql`.
- `init_db` twice succeeds.

**命令：**

```bash
QMD_DATA_ROOT=.audit-sandbox/batch-d-db python scripts/init_db.py
QMD_DATA_ROOT=.audit-sandbox/batch-d-db python scripts/init_db.py
QMD_DATA_ROOT=.audit-sandbox/batch-d-db python -c "
from backend.app.db.connection import ConnectionManager
from backend.app.config import DATA_ROOT
cm = ConnectionManager(DATA_ROOT / 'duckdb' / 'quant_monitor.duckdb')
with cm.reader() as con:
    tables = {r[0] for r in con.execute('SHOW TABLES').fetchall()}
    assert {'data_sync_job', 'job_event_log'}.issubset(tables)
    assert '006_ingestion_sync' in {r[0] for r in con.execute('SELECT version_id FROM schema_version').fetchall()}
"
```

**对抗触发器：** kill 后重跑 migrate — 数据完整？

### A4 Tests

Verify semantic tests per `research/orchestrator-tests.md`:

- `tests/test_sync_migration.py`
- `tests/test_sync_jobs.py` — **含** `full_load` / `revision_audit` / `data_quality` 骨架测（AC-2）
- `tests/test_sync_orchestrator.py`
- `tests/test_batch_d_orchestration_flow.py`
- incremental E2E 断言 `fetch_log` 行存在（`adapter.fetch` 传 writer `con`）

### A5 Traceability

For AC-1…AC-12: implementation + test + evidence; score 1–5.

**证据抽检（必做）：** 独立复跑 Execute §10 Tier B 最弱 2 行于 audit-sandbox。  
**证据真实性（必做）：** 抽检 2 个 `execute-evidence/*-green.txt` 非占位符。

**audit-prod-path（必做）：**

```bash
# 1. 复制数据
cp -r data .audit-sandbox/prod-path-data
# 2. 验证 env
QMD_DATA_ROOT=.audit-sandbox/prod-path-data python -c "from backend.app.config import DATA_ROOT; assert '.audit-sandbox' in str(DATA_ROOT)"
# 3. 跑 Tier C
QMD_DATA_ROOT=.audit-sandbox/prod-path-data pytest -q --cov=backend --cov-fail-under=75
QMD_DATA_ROOT=.audit-sandbox/prod-path-data python scripts/ci_ingestion_smoke.py
```

### A6 Security/logging

Verify: error redaction; no secrets in job_event_log payload; no Agent free SQL.

**对抗触发器：** 检查硬编码 URL、API key 模式、SQL 拼接。

### A7 Resource/scope

Verify:

- ResourceGuard called before FETCHING.
- Backfill partitioned in eco.
- No Layer/API/frontend/Agent/real Port creep.

**cli-sandbox 异常场景（必做）：** ResourceGuard 模拟 `Decision.PAUSE` → job `FAILED_RETRYABLE`（非 `RESOURCE_GUARD_PAUSED` status）+ `job_event_log.message` 含 `RESOURCE_GUARD_PAUSED`。

### A8 Docs/handoff

Verify `BATCH_D_STATUS.md`, README Batch D row, DECISIONS checkpoint, handoff commands.

### A6 性能 — SKIP

**理由：** Batch D 无 latency SLA；eco 分片已在 A7 验证。§1 标不用。

---

## 3. GitNexus / CodeGraph（7.pre）

7.pre 刷新 → `research/gitnexus-audit-summary.md`  
A1–A8 各 ≥1 query → audit.report §3.x

---

## 4. Verdict rules

- **PASS:** AC-1…AC-12 全追溯 ≥4；§4.3 空
- **PASS_WITH_FIXES:** 仅 P2 + §4.3 可关闭
- **FAIL:** P0/P1 或 AC 缺口
