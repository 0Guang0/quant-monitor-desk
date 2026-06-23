# MASTER 计划 — Round 2 Batch D（014 DataSyncOrchestrator）

> **Execute 入口（唯一全文）** · v1.0 · 2026-06-18  
> Trellis slug：`06-18-round2-batch-d-orchestrator`  
> 本文件用于让执行角色直接进入 Execute；禁止再按记忆补计划。  
> 语言：计划与验收用中文；代码标识符、命令、路径保持英文。

---

## 0. 元信息

| 字段            | 值                                                                         |
| --------------- | -------------------------------------------------------------------------- |
| slug            | `06-18-round2-batch-d-orchestrator`                                        |
| 关联 Round      | `ROUND_2_DATA_INGESTION_VALIDATION` Batch **D**                            |
| 原计划任务      | `014_implement_data_sync_orchestrator.md`                                  |
| 前置            | Batch A/B/C PASS；Batch C `READY_FOR_BATCH_D: yes`                         |
| 决策输入        | `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/DECISIONS.md` |
| Batch C 台账    | `BATCH_C_REPAIR_STATUS.md` · `BATCH_C_LEDGER.md`                           |
| 默认分支        | `master`                                                                   |
| 建议执行分支    | `feat/round2-batch-d-orchestrator`                                         |
| analysis_waiver | `false`                                                                    |

### 0.1 Execute 开场白（复制给执行角色）

```text
Round 2 Batch D Execute：MUST read .cursor/skills/trellis-execute/SKILL.md。
Phase 0 Boot → 读 MASTER.plan.md + implement.jsonl **每一条**（§0.3）+ DECISIONS + BATCH_B/C_* + 014 任务卡
→ 6.pre GitNexus/CodeGraph → research/gitnexus-execute-summary.md
→ 严格执行 MASTER §8.0–§8.11
→ 每步保存 execute-evidence/{step}-red.txt 与 execute-evidence/{step}-green.txt
→ 执行 §9/§10 验收
→ validate-execute-handoff
→ 交接 Audit。
不要 finish-work。不要实现 Round 3 Layer 建模 / Round 4 API·前端 / Round 5 Release。
```

### 0.2 Trellis 协议约束

- Execute 只认本 `MASTER.plan.md` 全文与 `implement.jsonl`。
- `implement.jsonl` 第一条必须是 `MASTER.plan.md`，第二条必须是 `.cursor/skills/trellis-execute/SKILL.md`。
- Audit 只认 `AUDIT.plan.md` + `audit.jsonl` + 本文件 §2/§9/§10 证据。
- Repair 只认 `REPAIR.plan.md` + `repair.jsonl` + `audit.report.md`。
- 不允许临时创建 scratch / tmp / round report 作为最终产物。

### 0.3 Execute 强制必读清单（零遗漏）

**规则：** Execute Phase 0 Boot **必须 Read `implement.jsonl` 中每一条**（以文件行数为准）。**禁止**用 §8.0 或本节的摘要替代未读条目。读完每条后在 `execute-evidence/8.0-boot-reads.txt` 记录「路径 + 一行要点」。

**v3 读法（§0.4）：** 先读 `research/integration-ledger.md` 确定每条路径是 **inline**（以 MASTER 为准）还是 **pointer**（按 `extract` / `for` 精读）。`implement.jsonl` 的 `reason` 字段与 ledger 同步。

**机械闭包：** 全部路径见 `implement.jsonl`（当前 ~67 条）。`check.jsonl` ⊆ `implement.jsonl`（E14）。

**6.pre（Execute 独有）：** GitNexus/CodeGraph 刷新 → 新建 `research/gitnexus-execute-summary.md`（Plan 阶段 `gitnexus-summary.md` **不替代**）。

### 0.4 上下文打包（协议 v3）

Execute **以 MASTER inline 为准**；`research/integration-ledger.md` 规定 pointer 类原稿的 **extract / for**。Boot 时先读 ledger，再按策略读 implement 路径（非盲读全表）。

---

## 1. 目标

### 1.1 一句话

交付 Round 2 Batch D：**DataSyncOrchestrator** + sync 表 migration + job 状态机，把 registry/adapter/validator/gate/WriteManager 串成可测试的 ingestion 编排，并偿还 GPT-init_db、GPT-P3-6、B-P1-6-full 等延后台账。

### 1.2 子交付物

| ID  | 交付                   | 目标路径                                                                                                                                 |
| --- | ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| D-1 | migration 006          | `backend/app/db/migrations/006_ingestion_sync.sql`                                                                                       |
| D-2 | Job 状态机 + 模型      | `backend/app/sync/jobs.py`                                                                                                               |
| D-3 | Orchestrator           | `backend/app/sync/orchestrator.py`                                                                                                       |
| D-4 | Registry bootstrap CLI | `scripts/sync_registry.py`                                                                                                               |
| D-5 | 测试                   | `tests/test_sync_migration.py`, `tests/test_sync_jobs.py`, `tests/test_sync_orchestrator.py`, `tests/test_batch_d_orchestration_flow.py` |
| D-6 | Smoke 扩展             | `scripts/ci_ingestion_smoke.py`                                                                                                          |
| D-7 | 状态文档               | `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/BATCH_D_STATUS.md`                                                          |
| D-8 | 可选索引               | `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/plans/014_batch_d.plan.md`                                                  |

### 1.3 原计划 + 延后项归并

| 来源                            | 进入 Batch D 的内容                                                                          |
| ------------------------------- | -------------------------------------------------------------------------------------------- |
| 原计划 014                      | FullLoad/Incremental/Backfill/RevisionAudit/Reconcile 状态机；job/run/task id；ResourceGuard |
| 014 §9 用语纠偏                 | 任务卡写 `job_run_log` → 权威表名 **`job_event_log`**（`schema.sql` L102+）                  |
| `data_sync_orchestrator.md` §13 | 状态转移、event log、断点续跑字段                                                            |
| `sync_job_contract.yaml`        | job_type + status 枚举                                                                       |
| `DECISIONS.md` §9               | GPT-init_db、GPT-P3-6、GPT-P2-2（`tombstone_missing` API）、B-P1-6-full                      |
| `BATCH_C_LEDGER.md` C-C2        | fetch_log 004 CHECK 继续 app 层                                                              |
| Batch C finish                  | validator/gate 已就绪，Batch D 只编排不重写                                                  |

### 1.5 停止条件（可追加 · loop 必填）

| #   | 事件                    | 处理                   |
| --- | ----------------------- | ---------------------- |
| 1   | Batch C gate 未关       | 禁止 start             |
| 2   | ResourceGuard HARD_STOP | 中止 orchestrator run  |
| 3   | scope 偏离 014 任务卡   | 退回 Plan              |
| 4   | RED 非本步预期失败      | 停当前 §8 步           |
| 5   | 状态机不可恢复转移      | 中止；记 MANUAL_REVIEW |

---

## 2. 预期结果（A5 trace-ac）

| AC    | 预期结果                                                                                                                           | 验证链            |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------- | ----------------- |
| AC-1  | 六种 `job_type` 可 **create_job** 创建且状态转移符合 `sync_job_contract.yaml`（含 `reconcile`；见 §4.2）                           | §8.2 + §10 A      |
| AC-2  | 六种 `job_type` **各有语义测试**（§4.2 骨架边界：FullLoad/RevisionAudit **无**完整 fetch→write E2E；Incremental 以 §8.5 E2E 为准） | §8.2–§8.7 + §10 A |
| AC-3  | Backfill 大范围在 eco 下自动分片（≤31 天/task）                                                                                    | §8.6 + §10 A      |
| AC-4  | `data_sync_job` + `job_event_log` 持久化 run_id/job_id/task_id                                                                     | §8.1–§8.3 + §10 A |
| AC-5  | 重任务 `FETCHING` 前 `ResourceGuard.check()`；guard 暂停 → job `FAILED_RETRYABLE` + event message 含 `RESOURCE_GUARD_PAUSED`       | §8.4 + §10 A      |
| AC-6  | Incremental：`Adapter→staging→DataQualityValidator→SourceConflictValidator→DbValidationGate→WriteManager`                          | §8.5 + §10 B      |
| AC-7  | migration 006 对齐 `specs/schema/schema.sql` L73–113                                                                               | §8.1 + §10 A      |
| AC-8  | Orchestrator **不**直接 SQL 写 clean；不经 WriteManager 不写 clean                                                                 | §8.5 + Audit A2   |
| AC-9  | `ci_ingestion_smoke.py` 覆盖 orchestrator 路径（GPT-P3-6）                                                                         | §8.9 + §10 C      |
| AC-10 | `sync_registry.py` 或 bootstrap 同步 YAML→DB（GPT-init_db）                                                                        | §8.8 + §10 B      |
| AC-11 | 全库 pytest、ruff、compileall、production_gate 通过                                                                                | §10               |
| AC-12 | 不实现 Layer 建模/API·前端/Agent/真实 vendor Port/全量 security CI                                                                 | §3.2 + Audit A7   |

---

## 3. 范围与边界

### 3.1 In scope

- `backend/app/db/migrations/006_ingestion_sync.sql`
- `backend/app/sync/jobs.py`
- `backend/app/sync/orchestrator.py`
- `scripts/sync_registry.py`
- `scripts/ci_ingestion_smoke.py`（扩展）
- Tests listed in §1.2
- `BATCH_D_STATUS.md`

### 3.2 Out of scope · 显式 defer

| 项                                                | 偿还批次    | 说明                                                                |
| ------------------------------------------------- | ----------- | ------------------------------------------------------------------- |
| Layer 1–5 建模                                    | Round 3     | Batch D 只编排 ingestion                                            |
| FastAPI 生产路由 / 前端                           | Round 4     | 不碰 `frontend/*` 生产页                                            |
| Agent sandbox / ToolRegistry                      | Round 5     | —                                                                   |
| 真实 HTTP/SDK vendor Port                         | Batch D+    | 用 FakeAdapter/RecordingAdapter                                     |
| CodeQL/gitleaks/SBOM 全量 CI                      | Round 5     | —                                                                   |
| `fetch_log` 004 ALTER CHECK                       | 不可行      | C-C2 app 层 + 文档                                                  |
| `registry_generation` / `removed_from_yaml_at` 列 | Round 3+    | §8.8 调用既有 `sync_to_db(tombstone_missing=True)`                  |
| FullLoad checkpoint / 断点续跑字段                | Round 3     | §13.4.1 完整 resume；Batch D 仅 `create_job` + 最小状态转移（AC-2） |
| `quant_monitor.sync` 生产 CLI                     | Round 3 ops | Batch D 以 programmatic API + `sync_registry.py` + smoke            |
| 014 任务卡 §11 `npm run typecheck`                | N/A         | Batch D **backend-only**；不触 `frontend/*`                         |

### 3.3 路径修正

任务卡 §4 写 `backend/sync/*`；DECISIONS §1 要求 `backend/app/*`：

```text
backend/app/sync/orchestrator.py
backend/app/sync/jobs.py
```

禁止创建 `backend/sync/` 平行目录。

---

## 4. 技术设计摘要

```text
CLI / Orchestrator.bootstrap()
  → SourceRegistry.load + sync_to_db (optional, writer 事务 — §6.5)
  → ResourceGuard.check()  # FETCHING 前；见 §4.4
  → create run_id / job_id / task_id
  → PLANNED → FETCHING
  → with ConnectionManager.writer() as con:
        BaseDataAdapter.fetch(req, con=con, job_id=job_id)  # staging 由 adapter 写入；见 §6.5
  → staging（**Batch D：仅 adapter.fetch**，orchestrator 不 INSERT staging）
  → STAGED → VALIDATING
  → DataQualityValidator
  → SourceConflictValidator
  → DbValidationGate
  → READY_TO_WRITE → WRITING
  → DuckDBWriteManager.write(..., job_id=job_id)
  → COMPLETED + job_event_log
```

异常：`FAILED_RETRYABLE` / `FAILED_FINAL` / `MANUAL_REVIEW_REQUIRED` / `WAITING_RECONCILE` / `CANCELLED` 按契约转移；**禁止**发明契约外 status（含把 `RESOURCE_GUARD_PAUSED` 当作 job status）。

### 4.1 核心类型（jobs.py）

```python
@dataclass(frozen=True)
class SyncJobSpec:
    run_id: str
    job_id: str
    job_type: str  # sync_job_contract job_types
    data_domain: str
    market_id: str
    source_id: str
    adapter_id: str | None  # 可空；FETCHING 后回填 data_sync_job.adapter_id
    date_start: date | None
    date_end: date | None
    instrument_id: str | None
    partition_key: str | None
    trigger_reason: str | None  # backfill only；持久化见 §6.1.1 payload_json，非 data_sync_job 列

class SyncJobStateMachine:
    def transition(self, job_id: str, new_status: str, *, task_id: str | None, message: str) -> None: ...
```

### 4.2 Orchestrator 公共 API

```python
class DataSyncOrchestrator:
    def bootstrap(self, *, sync_registry: bool = False) -> None: ...
    def create_job(self, spec: SyncJobSpec) -> str: ...
    def run_incremental(self, spec: SyncJobSpec, *, adapter: BaseDataAdapter) -> SyncJobResult: ...
    def run_backfill(self, spec: SyncJobSpec, *, adapter: BaseDataAdapter) -> list[SyncJobResult]: ...
    def run_reconcile(self, conflict_id: str, *, adapter: BaseDataAdapter) -> SyncJobResult: ...
```

FullLoad / RevisionAudit / **data_quality** / **reconcile** / **incremental** / **backfill**：

- **AC-1：** `create_job` 必须接受全部六种 `job_type`（`reconcile` 可由 `run_reconcile(conflict_id)` 内部 `create_job(job_type="reconcile", ...)` 实现）。
- **AC-2 骨架边界（禁止 over-build）：**
  - `full_load` / `revision_audit`：`create_job` + **最小**状态转移 + `job_event_log`（§8.2）；**不要求**完整 fetch→write E2E（§13.4.1 断点续跑 defer §3.2）。
  - `revision_audit` 测试：mock fetch 至 **STAGED** 即可，**不必**进入 VALIDATING（§8.2 tracer）。
  - `incremental`：§8.2 须有 `job_type=incremental` 骨架测 + §8.5 完整 E2E。
  - `backfill` / `reconcile`：§8.6 / §8.7 语义测。
  - `data_quality`：§6.6 + §8.2 tracer。
- FullLoad / RevisionAudit **不**要求完整 fetch→write E2E；断点续跑 defer Round 3（§3.2）。

### 4.3 Backfill 分片（eco）

- `max_days_per_task = 31`（§6.3）
- `date_range > 31` → 生成多个 `task_id`，顺序执行，失败不吞已完成 task
- **每个 shard/task 再次进入 `FETCHING` 前**须 `ResourceGuard.check()`（同 §4.4）
- `trigger_reason`（spec §13.4.3 六值）写入 `job_event_log.payload_json`（`event_type=BACKFILL_SHARD`）；Batch D **无** `data_sync_job.trigger_reason` 列

### 4.4 ResourceGuard 集成（AC-5 / B-P1-6-full）

- 在 **每个** 进入 `FETCHING` 的路径前调用 `ResourceGuard(con=writer_con).check()`（含 backfill 各 shard/task）。
- `Decision.OK` → 继续 `PLANNED → FETCHING`。
- `Decision.PAUSE` 或 `Decision.HARD_STOP` → **不进入 FETCHING**；job 转移为 **`FAILED_RETRYABLE`**（契约合法 retryable status）。
- `job_event_log.message` **必须**包含 `ResourceGuard.format_pause_event(...)` 输出（含 `RESOURCE_GUARD_PAUSED` 前缀）；**不得**把 `RESOURCE_GUARD_PAUSED` 写入 `data_sync_job.status`。
- `error_type` 建议映射 guard `reason`（如 `DISK_SPACE_LOW`）；stderr 已由 `ResourceGuard.check()` 打印。

---

## 5. 依赖与切片

```text
§8.0  Boot / baseline / evidence dirs
§8.1  migration 006 + tests
§8.2  SyncJob state machine + job_event_log
§8.3  DataSyncOrchestrator core persistence
§8.4  ResourceGuard integration
§8.5  Incremental E2E (FakeAdapter)
§8.6  Backfill partition + guard
§8.7  Reconcile + SourceConflictValidator
§8.8  Registry bootstrap + sync_registry CLI
§8.9  ci_ingestion_smoke extension
§8.10 docs/status
§8.11 final gates + handoff
```

---

## 6. 接口契约与数据模型

### 6.1 Migration 006

创建表（列以 `specs/schema/schema.sql` L73–113 为准）：

```text
data_sync_job
job_event_log
```

不修改 004/005。索引建议：`data_sync_job(run_id)`, `job_event_log(job_id)`。

### 6.1.1 `data_sync_job` 列与 Batch D 持久化

006 须实现 `schema.sql` L73–99 **全部列**（migration 对齐 AC-7）。`SyncJobSpec`（§4.1）为创建时最小字段集；其余列（`priority`, `retry_count`, `max_retries`, cursors, report/write IDs, `error_*`, timestamps）由 state machine / orchestrator 在转移时填充，**允许 NULL 直至对应阶段**。

`trigger_reason`（backfill）**无** `data_sync_job` 列 → 写入 `job_event_log.payload_json`（§4.3）。

### 6.2 Status 枚举与转移

以 `specs/contracts/sync_job_contract.yaml` 为权威；Python 侧 `SYNC_JOB_STATUSES` 常量 + 测试防 drift。

**Happy path** 以 `data_sync_orchestrator.md` §13.2 为准：`CREATED→PLANNED→FETCHING→STAGED→VALIDATING→(WAITING_RECONCILE/RECONCILING)→READY_TO_WRITE→WRITING→COMPLETED`。

- **Terminal**（`COMPLETED` / `FAILED_FINAL` / `SKIPPED` / `CANCELLED` / `MANUAL_REVIEW_REQUIRED`）不可再进入 `FETCHING`。
- **非法跳迁**（如 `CREATED→WRITING`）`SyncJobStateMachine.transition` 必须 reject。
- Retryable：`FAILED_RETRYABLE` 可经显式 retry 策略回到 `PLANNED`（Batch D 测最小路径即可）。

### 6.3 Backfill 分片常量

```python
ECO_MAX_BACKFILL_DAYS_PER_TASK = 31
```

### 6.4 Registry sync（GPT-P2-2 / GPT-init_db）

- `SourceRegistry.sync_to_db(con, tombstone_missing=True)` **已实现**：YAML 缺失源标记 `is_enabled=false`（见 `source_registry.py` L340–397）。
- `scripts/sync_registry.py`：独立 CLI，`SourceRegistry.load` → `ConnectionManager.writer()` 事务内 `sync_to_db`。
- `DataSyncOrchestrator.bootstrap(sync_registry=True)` 可选调用同路径；**不**修改 `init_db.py` 默认行为。
- 仍 defer：`registry_generation` / `removed_from_yaml_at` 审计列（DECISIONS §9 GPT-P2-2 完整 generation）。

### 6.5 Orchestrator 接线契约（Batch C 继承）

| 触点            | 要求                                                                                                                              |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| DB 连接         | `ConnectionManager.writer()` 用于 `data_sync_job` / `job_event_log` / registry sync / fetch 阶段                                  |
| `adapter.fetch` | **必须** `con=writer_con` 且传 `job_id`；`FetchLogWriter` 在 `BaseDataAdapter.fetch` 内落库（勿在 orchestrator 重复写 fetch_log） |
| Staging 写入    | **Batch D：仅经 `adapter.fetch`**；orchestrator **禁止**直接 `INSERT` staging 表                                                  |
| Registry sync   | caller-owned 事务（`BATCH_C_LEDGER` **C-C1**）；`sync_to_db` 不内部 BEGIN                                                         |
| Write           | `WriteManager.write(WriteRequest(..., job_id=job_id))`；gate 用同 `con`                                                           |
| Validators      | 与 `test_batch_c_validation_flow.py` 相同 `con` 传递模式                                                                          |

### 6.6 `job_type=data_quality`（AC-2 第六种）

- 创建：`job_type="data_quality"`，`data_domain` + optional `instrument_id`。
- Batch D 最小语义：`PLANNED → VALIDATING → COMPLETED` 或 `MANUAL_REVIEW_REQUIRED`；VALIDATING 阶段调用 `DataQualityValidator.validate_table` 对 **测试 fixture 表** 抽样（`tests/conftest.py` 或测试内 `CREATE TABLE staging_*`；**不**自选生产表名）。
- **不做**：Layer 3 全市场审计、独立 cron 调度表。

### 6.7 `fetch_log` 004 约束（GPT-P1-5-DB / C-C2）

- migration **006 不得** `ALTER TABLE` 已应用的 **004** `fetch_log` / `source_registry`（`BATCH_C_LEDGER.md` C-C2）。
- 继续依赖：`FetchResult` Pydantic 校验 + `FetchLogWriter._validate_for_persist` 应用层双保险。
- Execute §8.5 incremental E2E **必须**断言 `fetch_log` 行存在（验证 adapter.fetch 传 writer `con`）。
- 若未来需 DB CHECK：须单独用户决策与新 migration 策略（**非** Batch D AC）。

### 6.8 测试 double（FakeAdapter）

- Batch D E2E 使用 `tests/test_data_adapter_contract.py` 内 `FakeAdapter`（**不**要求提取到 `datasources/_testing.py`）。
- **仅允许**在 `tests/**` 中 `from tests.test_data_adapter_contract import FakeAdapter`；**禁止**在 `backend/app/sync/*` 生产代码 import tests 模块。

---

## 7. Resource / security constraints

- 默认 `eco`；禁止默认全市场全历史扫描。
- ResourceGuard 在 `FETCHING` 前必调；触发时 job→`FAILED_RETRYABLE`，`job_event_log.message` 含 `RESOURCE_GUARD_PAUSED`（§4.4）。
- Clean 写入仅经 WriteManager + DbValidationGate。
- Adapter 不 import WriteManager。
- 错误消息脱敏沿用 Batch C `error_redaction`。
- ReconcileJob 委托 `SourceConflictValidator`，禁止第二套冲突比较。

### 7.1 Red Flags

- Orchestrator 内直接 INSERT clean 表
- 新增 ad-hoc job status 不在契约 YAML
- 跳过 ResourceGuard 声称「测试简化」
- 重复实现 reconcile 逻辑
- 创建 `backend/sync/` 平行树
- 为绿而删 validator/gate 调用
- `adapter.fetch` 不传 writer `con`（会导致 fetch_log 缺失）
- 把 `RESOURCE_GUARD_PAUSED` 当作 `data_sync_job.status`

---

## 8. Execute steps

| Step | 内容              | RED 命令                                                  | GREEN 命令             | RED 证据               | GREEN 证据                                   |
| ---- | ----------------- | --------------------------------------------------------- | ---------------------- | ---------------------- | -------------------------------------------- |
| 8.0  | Boot + baseline   | `pytest -q`（记录基线）                                   | 同左 + production_gate | `8.0-baseline.txt`     | `8.0-baseline.txt`                           |
| 8.1  | migration 006     | `pytest tests/test_sync_migration.py -q`                  | 同左 exit 0            | `8.1-red.txt`          | `8.1-green.txt`                              |
| 8.2  | state machine     | `pytest tests/test_sync_jobs.py -q`                       | 同左 exit 0            | `8.2-red.txt`          | `8.2-green.txt`                              |
| 8.3  | orchestrator core | `pytest tests/test_sync_orchestrator.py -q`               | 同左 exit 0            | `8.3-red.txt`          | `8.3-green.txt`                              |
| 8.4  | ResourceGuard     | `pytest tests/test_sync_orchestrator.py -k guard -q`      | 同左 exit 0            | `8.4-red.txt`          | `8.4-green.txt`                              |
| 8.5  | incremental E2E   | `pytest tests/test_batch_d_orchestration_flow.py -q`      | 同左 exit 0            | `8.5-red.txt`          | `8.5-green.txt`（可选 `8.5-slice-full.txt`） |
| 8.6  | backfill          | `pytest tests/test_sync_orchestrator.py -k backfill -q`   | 同左 exit 0            | `8.6-red.txt`          | `8.6-green.txt`                              |
| 8.7  | reconcile         | `pytest tests/test_sync_orchestrator.py -k reconcile -q`  | 同左 exit 0            | `8.7-red.txt`          | `8.7-green.txt`                              |
| 8.8  | registry          | `pytest tests/test_sync_orchestrator.py -k registry -q`   | 同左 exit 0            | `8.8-red.txt`          | `8.8-green.txt`                              |
| 8.9  | smoke             | `QMD_DATA_ROOT=data python scripts/ci_ingestion_smoke.py` | 输出含 orchestrator ok | `8.9-smoke.txt`        | `8.9-smoke.txt`                              |
| 8.10 | docs              | —                                                         | 文档已更新             | `8.10-docs.txt`        | `8.10-docs.txt`                              |
| 8.11 | handoff           | —                                                         | §10 Tier C 全绿        | `8.11-final-gates.txt` | `8.11-handoff.txt`                           |

Tracer 全文见 `research/orchestrator-tests.md`（禁止在 MASTER 内嵌 >2 个 `def test_*`）。

### 8.0 Boot, baseline, and evidence

| 已执行 | [x] |

1. Create evidence directories:

```bash
mkdir -p .trellis/tasks/06-18-round2-batch-d-orchestrator/execute-evidence
```

2. **Read（零遗漏）：** 按 **§0.3** 逐条 Read `implement.jsonl` **全部路径**；先读 `research/integration-ledger.md` 按 inline/pointer 策略精读（**禁止**在 §8.0 枚举替代路径清单）。

3. 保存 `execute-evidence/8.0-boot-reads.txt`（每条 implement 路径一行要点）。

4. 6.pre: GitNexus refresh → `research/gitnexus-execute-summary.md`

5. Baseline:

```bash
pytest -q
ruff check .
python -m compileall -q backend scripts tests
python scripts/production_gate.py
```

6. Save `execute-evidence/8.0-baseline.txt`

**Skill:** trellis-execute · karpathy-guidelines · testing-guidelines

### 8.1 Migration 006

| 已执行 | [x] |

Create:

```text
backend/app/db/migrations/006_ingestion_sync.sql
tests/test_sync_migration.py
```

Tracer: `research/orchestrator-tests.md` §8.1

Evidence: `8.1-red.txt`, `8.1-green.txt`

**Skill:** test-driven-development · GitNexus impact before editing migrate runner

### 8.2 Job state machine

| 已执行 | [x] |

Create:

```text
backend/app/sync/jobs.py
tests/test_sync_jobs.py
```

Tracer: `research/orchestrator-tests.md` §8.2（含 AC-2 六种 `job_type` 骨架测：`full_load` / `revision_audit` / `data_quality`）

Evidence: `8.2-red.txt`, `8.2-green.txt`

### 8.3 Orchestrator core

| 已执行 | [x] |

Create:

```text
backend/app/sync/orchestrator.py
tests/test_sync_orchestrator.py
```

Tracer: `research/orchestrator-tests.md` §8.3

Evidence: `8.3-red.txt`, `8.3-green.txt`

### 8.4 ResourceGuard integration

| 已执行 | [x] |

Extend orchestrator + tests.

Tracer: `research/orchestrator-tests.md` §8.4

Evidence: `8.4-red.txt`, `8.4-green.txt`

### 8.5 Incremental E2E

| 已执行 | [x] |

Create:

```text
tests/test_batch_d_orchestration_flow.py
```

Reuse `FakeAdapter` from `tests/test_data_adapter_contract.py` / batch C validator fixtures pattern.

**接线：** `adapter.fetch(req, con=writer_con, job_id=job_id)`（§6.5）；禁止 orchestrator 重复 `FetchLogWriter.write`。

Tracer: `research/orchestrator-tests.md` §8.5

Evidence: `8.5-red.txt`, `8.5-green.txt`, `8.5-slice-full.txt`

### 8.6 Backfill partition

| 已执行 | [x] |

Extend orchestrator + tests.

Tracer: `research/orchestrator-tests.md` §8.6

Evidence: `8.6-red.txt`, `8.6-green.txt`

### 8.7 Reconcile job

| 已执行 | [x] |

Extend orchestrator + tests; call `SourceConflictValidator`.

Tracer: `research/orchestrator-tests.md` §8.7

Evidence: `8.7-red.txt`, `8.7-green.txt`

### 8.8 Registry bootstrap

| 已执行 | [x] |

Create `scripts/sync_registry.py`; orchestrator `bootstrap(sync_registry=True)` optional.

- Call `SourceRegistry.sync_to_db(con, tombstone_missing=True)` inside caller-owned writer transaction (BATCH_C_LEDGER **C-C1**).
- **不修改** `init_db.py` 默认行为（registry sync 仅 `sync_registry.py` / `bootstrap(sync_registry=True)`）。
- Test: YAML 缺失源 → DB `is_enabled=false`；二次调用幂等。
- Do **not** re-implement tombstone logic; defer `registry_generation` column.

Tracer: `research/orchestrator-tests.md` §8.8

Evidence: `8.8-red.txt`, `8.8-green.txt`

### 8.9 Ingestion smoke (GPT-P3-6)

| 已执行 | [x] |

Extend `scripts/ci_ingestion_smoke.py`:

1. 断言 migration `006_ingestion_sync` 已应用且 `data_sync_job` / `job_event_log` 表存在。
2. 跑一次 orchestrator incremental smoke（FakeAdapter / tmp_path 或 `QMD_DATA_ROOT` 隔离路径）。
3. stdout 含 `orchestrator_smoke: ok`。

Evidence: `8.9-smoke.txt`

### 8.10 Documentation

| 已执行 | [x] |

Create/update:

```text
docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/BATCH_D_STATUS.md
docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/README.md
docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/DECISIONS.md (Batch D checkpoint)
docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/plans/014_batch_d.plan.md (index only)
```

Evidence: `8.10-docs.txt`

### 8.11 Final gates and handoff

| 已执行 | [x] |

Run §10. Save:

```text
execute-evidence/8.11-final-gates.txt
execute-evidence/8.11-detect-changes.txt
execute-evidence/8.11-handoff.txt
```

`validate-execute-handoff` → Audit. Do not finish-work before Audit.

---

## 9. Testing strategy

### 9.1 Tier A — Batch D targeted

```bash
pytest tests/test_sync_migration.py \
       tests/test_sync_jobs.py \
       tests/test_sync_orchestrator.py \
       tests/test_batch_d_orchestration_flow.py -q
```

### 9.2 Tier B — regression

```bash
pytest tests/test_batch_c_validation_flow.py \
       tests/test_source_registry.py \
       tests/test_write_manager.py \
       tests/test_data_adapter_contract.py -q
```

### 9.3 Tier C — full gate

```bash
pytest -q --cov=backend --cov-fail-under=75
ruff check .
python -m compileall -q backend scripts tests
python scripts/production_gate.py
python scripts/check_doc_links.py
QMD_DATA_ROOT=data python scripts/ci_ingestion_smoke.py
```

---

## 10. Acceptance commands（DoD）

| Tier   | 命令                        | 通过条件                      |
| ------ | --------------------------- | ----------------------------- |
| A      | §9.1                        | exit 0                        |
| B      | §9.2                        | exit 0                        |
| C      | §9.3                        | exit 0；cov ≥75%              |
| Detect | GitNexus `detect_changes()` | 记录 risk；无 CRITICAL 未说明 |

Handoff 模板 `execute-evidence/8.11-handoff.txt`:

```text
READY_FOR_AUDIT: yes|no
pytest_total: <n>
cov: <pct>
ResourceGuard_triggered: yes|no
open_items: ...
```

---

## 11. Audit handoff

Execute 完成后主会话填写 handoff；Audit 读 `AUDIT.plan.md` + `audit.jsonl`。

禁止 Execute 阶段 dispatch trellis-check（Audit Phase 7 取代）。

---

## 12. Execute Skill 冻结清单

| Skill                      | 本任务 | 绑定 §8                | 触发           | @ 指令                       | 已执行 |
| -------------------------- | ------ | ---------------------- | -------------- | ---------------------------- | ------ |
| trellis-execute            | 必做   | 8.0                    | 每步           | Read SKILL.md Phase 0 Boot   | [x]    |
| test-driven-development    | 必做   | 8.1–8.9                | 每步写代码     | RED→GREEN per §8.x           | [x]    |
| incremental-implementation | 必做   | 8.1–8.11               | 全程           | 一次只完成当前 §8.x          | [x]    |
| systematic-debugging       | 条件   | 当前失败步             | pytest RED     | 根因→最小修复                | [ ]    |
| karpathy-guidelines        | 必做   | 8.x 实现前             | 每步 GREEN 前  | User Rule                    | [x]    |
| testing-guidelines         | 必做   | 8.x 测试               | 每步           | User Rule                    | [x]    |
| GitNexus impact            | 必做   | 改 symbol 前           | 非平凡编辑     | `impact({target, upstream})` | [x]    |
| trellis-implement          | 不用   | —                      | inline 主会话  | —                            | —      |
| trellis-check              | 不用   | —                      | Audit 取代     | —                            | —      |
| trellis-before-dev         | 不用   | —                      | Plan 5c 已完成 | —                            | —      |
| doubt-driven-development   | 条件   | 8.1 migration 幂等声称 | 声称前         | 对抗审查                     | [ ]    |

---

## 13. Plan 5d doubt-driven 修订记录

| 声称                            | 对抗结论              | 修订                                    |
| ------------------------------- | --------------------- | --------------------------------------- |
| ReconcileJob 独立实现冲突比较   | 与 Batch C 重复       | §4 委托 SourceConflictValidator         |
| init_db 默认 sync registry      | 破坏 Round 1 测试假设 | §8.8 独立 CLI + 可选 bootstrap          |
| 六种 job 全生产调度             | 范围膨胀              | §4.2 骨架+各 1 测；调度表 defer Round 3 |
| Backfill 无分片上限             | 违反 eco              | §6.3 冻结 31 天                         |
| fetch 不传 writer con           | fetch_log 缺失        | §6.5 冻结 adapter.fetch 签名            |
| RESOURCE_GUARD_PAUSED 当 status | 契约 drift            | §4.4 冻结 FAILED_RETRYABLE              |
| data_quality 当 VALIDATING 阶段 | 六种 job 语义混淆     | §6.6 冻结独立 job_type                  |
