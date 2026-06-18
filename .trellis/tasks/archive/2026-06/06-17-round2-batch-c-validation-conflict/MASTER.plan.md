# MASTER 计划 — Round 2 Batch C（015 + 016 validation/conflict）

> **Execute 入口（唯一全文）** · v1.0 · 2026-06-17  
> Trellis slug：`06-17-round2-batch-c-validation-conflict`  
> 本文件用于让执行角色直接进入 Execute；禁止再按记忆补计划。  
> 语言：计划与验收用中文；代码标识符、命令、路径保持英文。

---

## 0. 元信息

| 字段 | 值 |
|------|-----|
| slug | `06-17-round2-batch-c-validation-conflict` |
| 关联 Round | `ROUND_2_DATA_INGESTION_VALIDATION` Batch **C** |
| 原计划任务 | `015_implement_data_quality_validator.md` + `016_implement_source_conflict_validator.md` |
| 前置 | Batch A PASS；Batch B PASS；C-C0 三个小修复已完成 |
| 决策输入 | `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/DECISIONS.md` |
| Batch B 修复台账 | `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/BATCH_B_REPAIR_STATUS.md` |
| C-C0 台账 | `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/BATCH_C_LEDGER.md` |
| 默认分支 | `master` |
| 建议执行分支 | `feat/round2-batch-c-validation-conflict` |
| analysis_waiver | `false` |

### 0.1 Execute 开场白（复制给执行角色）

```text
Round 2 Batch C Execute：MUST read .cursor/skills/trellis-execute/SKILL.md。
Phase 0 Boot → 读 MASTER.plan.md + implement.jsonl + DECISIONS + BATCH_B_REPAIR_STATUS + BATCH_C_LEDGER
→ 严格执行 MASTER §8.0–§8.10
→ 每步保存 execute-evidence/{step}-red.txt 与 execute-evidence/{step}-green.txt
→ 执行 §9/§10 验收
→ validate-execute-handoff
→ 交接 Audit。
不要 finish-work。不要实现 Batch D / Round 4 / Round 5 范围。
```

### 0.2 Trellis 协议约束

- Execute 只认本 `MASTER.plan.md` 全文与 `implement.jsonl`。
- `implement.jsonl` 第一条必须是 `MASTER.plan.md`，第二条必须是 `.cursor/skills/trellis-execute/SKILL.md`。
- Audit 只认 `AUDIT.plan.md` + `audit.jsonl` + 本文件 §2/§9/§10 证据。
- Repair 只认 `REPAIR.plan.md` + `repair.jsonl` + `audit.report.md`。
- 不允许临时创建 scratch / tmp / round report 作为最终产物。

---

## 1. 目标

### 1.1 一句话

交付 Round 2 Batch C 的 ingestion validation 底座：`DataQualityValidator`、`SourceConflictValidator`、`DbValidationGate`、005 migration、SUCCESS evidence/staging 验证、Fetch/Port 错误状态对齐与最小错误脱敏。

### 1.2 子交付物

| ID | 交付 | 目标路径 |
|----|------|----------|
| C-1 | migration 005 | `backend/app/db/migrations/005_ingestion_validation.sql` |
| C-2 | DataQualityValidator | `backend/app/validators/data_quality.py` |
| C-3 | SourceConflictValidator | `backend/app/validators/source_conflict.py` |
| C-4 | DbValidationGate | `backend/app/db/validation_gate.py` |
| C-5 | SUCCESS evidence/staging check | `backend/app/datasources/fetch_result.py` / `fetch_log.py` / validator flow |
| C-6 | PortErrorStatus ↔ FetchStatus alignment | `backend/app/datasources/adapters/fetch_port.py` |
| C-7 | tests | `tests/test_*validation*`, `tests/test_*conflict*`, `tests/test_db_validation_gate.py` |
| C-8 | status docs | `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/BATCH_C_REPAIR_STATUS.md` |

### 1.3 原计划 + 延后项归并

| 来源 | 进入 Batch C 的内容 |
|------|---------------------|
| 原计划 015 | 空值、重复、日期、schema drift、stale、insufficient history、validation_report、失败不进 clean |
| 原计划 016 | 多源冲突、source_conflict、manual_review_queue、严重冲突人工确认、口径差异分源保存 |
| `DECISIONS.md` | Batch C = DataQualityValidator + SourceConflictValidator + real ValidationGate；migration 005 建表 |
| `BATCH_B_REPAIR_STATUS.md` | fetch_log DB CHECK、SUCCESS staging evidence、PortErrorStatus 对齐、错误脱敏最小闭环 |
| `BATCH_C_LEDGER.md` | C-C0 已关闭；仅作为上下文读取，不再重复修复 |

---

## 2. 预期结果（A5 trace-ac）

| AC | 预期结果 | 验证链 |
|----|----------|--------|
| AC-1 | `005_ingestion_validation.sql` 新增 validation/conflict/manual review 表，不修改已应用 004 | §8.1 + §10 A/B |
| AC-2 | `DataQualityValidator` 读取 `data_quality_rules.yaml`，输出 PASSED/WARNING/FAILED | §8.3 + §10 A |
| AC-3 | missing PK / duplicate PK / missing required / invalid timestamp / schema drift / stale / insufficient history / high<low / negative price-volume 均有语义测试 | §8.3 + §10 A |
| AC-4 | FAILED validation report 必须 `can_write_clean=false`，不得写 clean | §8.4 + §8.8 |
| AC-5 | SUCCESS 必须有 raw evidence 或存在 staging table；不存在 staging 不得进入 clean | §8.4 + §8.8 |
| AC-6 | `SourceConflictValidator` 区分 within tolerance、warning、severe conflict、口径差异 | §8.5 |
| AC-7 | severe conflict 写 `source_conflict`；必要时写 `manual_review_queue` | §8.6 |
| AC-8 | `DbValidationGate` 用 DB 中 `validation_report` 放行/拒绝 WriteManager | §8.2 + §8.8 |
| AC-9 | PortErrorStatus 与 FetchStatus 对齐；error_message 不泄漏 token/password/api_key/secret | §8.7 |
| AC-10 | 全库 pytest、ruff、compileall、production_gate、doc links 通过 | §10 |
| AC-11 | 不实现 Orchestrator / API/前端 / Agent sandbox / Release manifest / 真实 vendor Port | §3.2 + Audit |

---

## 3. 范围与边界

### 3.1 In scope

- `backend/app/db/migrations/005_ingestion_validation.sql`
- `backend/app/validators/data_quality.py`
- `backend/app/validators/source_conflict.py`
- `backend/app/db/validation_gate.py`
- `backend/app/datasources/fetch_result.py`
- `backend/app/datasources/fetch_log.py`
- `backend/app/datasources/adapters/fetch_port.py`
- Tests for migration, quality validator, conflict validator, DB gate, end-to-end validation flow.
- Batch C status documentation.

### 3.2 Out of scope · 显式 defer

| 项 | 偿还批次 | 说明 |
|----|----------|------|
| `014 DataSyncOrchestrator` | Batch D / Round 3 | 本轮只实现可被 Orchestrator 调用的 validation/gate |
| ResourceGuard WARN/PAUSE/HARD_STOP 动作闭环 | Batch D / Round 3 | 本轮只遵守资源限制，不实现编排动作 |
| 真实 HTTP/SDK FetchPort | Batch D+ | 本轮只做状态对齐与错误脱敏 |
| API/前端生产化 | Round 4 | 不碰 `frontend/*` 和 `backend/app/main.py` |
| Agent sandbox | Round 5 | 不实现 AgentToolRegistry |
| Release manifest / FINAL_AUDIT | Round 5 | 不生成最终发布包 |
| security CI full hardening | Batch D / Round 5 | 不做 CodeQL/gitleaks/action pin/SBOM |
| coverage 90/95 uplift | Batch D | 本轮保持现有全库门禁，核心新增测试必须充分 |

### 3.3 路径修正

原任务 015/016 写的是 `backend/validation/*`，但当前仓库实际结构为 `backend/app/*`，且已有 `backend/app/validators/`。本任务必须使用：

```text
backend/app/validators/data_quality.py
backend/app/validators/source_conflict.py
```

不得创建平行的 `backend/validation/`。

---

## 4. 技术设计摘要

```text
FetchResult / staging table / raw evidence
  ↓
DataQualityValidator
  - rule contract: specs/contracts/data_quality_rules.yaml
  - writes validation_report + data_quality_log
  - FAILED => can_write_clean=false
  ↓
SourceConflictValidator
  - rule contract: specs/contracts/source_conflict_rules.yaml
  - writes source_conflict
  - serious unresolved conflict => manual_review_queue
  ↓
DbValidationGate
  - reads validation_report
  - rejects failed/missing/manual-review validation reports
  ↓
WriteManager
  - clean writes only when gate allows
```

### 4.1 DataQualityValidator contract

Suggested public objects:

```python
@dataclass(frozen=True)
class DataQualityRequest:
    run_id: str
    job_id: str
    data_domain: str
    source_id: str
    staging_table: str
    primary_keys: tuple[str, ...]
    required_fields: tuple[str, ...]
    rule_set_id: str

@dataclass(frozen=True)
class DataQualityFinding:
    rule_id: str
    severity: str
    row_key: str | None
    field_name: str | None
    observed_value: str | None
    expected_condition: str
    message: str

@dataclass(frozen=True)
class DataQualityReport:
    validation_report_id: str
    status: str
    checked_rows: int
    failed_rows: int
    warning_rows: int
    quality_flags: tuple[str, ...]
    can_write_clean: bool
    needs_manual_review: bool
    findings: tuple[DataQualityFinding, ...]
```

### 4.2 SourceConflictValidator contract

Suggested public objects:

```python
@dataclass(frozen=True)
class SourceConflictRequest:
    run_id: str
    job_id: str
    data_domain: str
    primary_source: str
    validation_sources: tuple[str, ...]
    key_fields: tuple[str, ...]
    comparable_fields: tuple[str, ...]
    tolerance_rule_set_id: str

@dataclass(frozen=True)
class SourceConflictFinding:
    field_name: str
    primary_value: str
    competing_source: str
    competing_value: str
    normalized_diff: float | None
    severity: str
    manual_review_required: bool

@dataclass(frozen=True)
class SourceConflictReport:
    conflict_report_id: str
    status: str
    can_write_primary_value: bool
    needs_reconcile: bool
    needs_manual_review: bool
    conflicts: tuple[SourceConflictFinding, ...]
```

### 4.3 DbValidationGate behavior

- `validation_report_id` 不存在 → reject。
- `status == FAILED` → reject。
- `can_write_clean == false` → reject。
- `needs_manual_review == true` → reject。
- `status == PASSED` 且 `can_write_clean == true` → allow。
- `status == WARNING` 的默认策略必须显式：建议 allow only if `can_write_clean=true` and `needs_manual_review=false`。
- `StubValidationGate` 只能保留给测试显式使用，不得恢复生产默认 stub。

---

## 5. 依赖与切片

```text
§8.0 Phase 0 boot / baseline / evidence dirs
§8.1 migration 005 + tests
§8.2 DbValidationGate + tests
§8.3 DataQualityValidator pure logic + tests
§8.4 DataQualityValidator persistence/evidence/staging + tests
§8.5 SourceConflictValidator pure logic + tests
§8.6 SourceConflictValidator persistence/manual review + tests
§8.7 FetchStatus/PortErrorStatus alignment + redaction
§8.8 end-to-end validation flow with WriteManager
§8.9 docs/status update
§8.10 final gates + handoff
```

---

## 6. 接口契约与数据模型

### 6.1 Migration 005 target tables

Create or ensure:

```text
validation_report
data_quality_log
source_conflict
manual_review_queue
```

Also add defensive DB checks/indexes where feasible:

```text
fetch_log status enum guard
fetch_log SUCCESS evidence guard
fetch_log no-evidence status guard
source_registry enabled/domain/index guard
```

Important: do not modify already-applied migration 004. If DuckDB cannot `ALTER TABLE ADD CONSTRAINT` safely on existing tables, document the fallback in code comments and tests: app-layer guard + new table constraints + explicit audit note in `BATCH_C_REPAIR_STATUS.md`.

### 6.2 Rule contracts

- Data quality logic must read or mirror `specs/contracts/data_quality_rules.yaml`.
- Source conflict logic must read or mirror `specs/contracts/source_conflict_rules.yaml`.
- No hard-coded financial rule set may conflict with YAML.

---

## 7. Resource / security constraints

- Default mode is `eco`.
- Do not scan full market/full history by default.
- No unpaginated API or Agent large query.
- No free SQL / direct DB write from Agent.
- Clean writes must go through `WriteManager`.
- Do not import `WriteManager` from datasource adapters.
- Secrets in error messages must be redacted: `token`, `password`, `api_key`, `apikey`, `secret`, `authorization`, `bearer`.

---

## 8. Execute steps

### 8.0 Boot, baseline, and evidence

1. Create evidence directories:

```bash
mkdir -p .trellis/tasks/06-17-round2-batch-c-validation-conflict/execute-evidence
```

2. Read:

```text
MASTER.plan.md
implement.jsonl
.cursor/skills/trellis-execute/SKILL.md
docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/README.md
docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/DECISIONS.md
docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/BATCH_B_REPAIR_STATUS.md
docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/BATCH_C_LEDGER.md
015_implement_data_quality_validator.md
016_implement_source_conflict_validator.md
docs/modules/data_validation_and_conflict.md
specs/contracts/data_quality_rules.yaml
specs/contracts/source_conflict_rules.yaml
```

3. Run baseline:

```bash
pytest -q
ruff check .
python -m compileall -q backend scripts tests
python scripts/production_gate.py
```

4. Save:

```text
execute-evidence/8.0-baseline.txt
```

### 8.1 Add migration 005

Create:

```text
backend/app/db/migrations/005_ingestion_validation.sql
tests/test_ingestion_validation_migration.py
```

Required tests:

- fresh `init_db` creates validation/conflict/manual review tables.
- `init_db` can run twice idempotently.
- direct invalid `fetch_log.status` rejected if DB check feasible, or blocked by app-layer guard with explicit test.
- `validation_report` required fields enforced.
- `source_conflict` required fields enforced.
- `manual_review_queue` required fields enforced.

Evidence:

```text
execute-evidence/8.1-red.txt
execute-evidence/8.1-green.txt
```

### 8.2 Implement DbValidationGate

Modify:

```text
backend/app/db/validation_gate.py
tests/test_db_validation_gate.py
```

Required tests:

- missing report rejected.
- FAILED report rejected.
- `can_write_clean=false` rejected.
- `needs_manual_review=true` rejected.
- PASSED allowed.
- WARNING with `can_write_clean=true` and no manual review follows chosen explicit policy.
- `StubValidationGate` remains test-only explicit helper; no production default.

Evidence:

```text
execute-evidence/8.2-red.txt
execute-evidence/8.2-green.txt
```

### 8.3 Implement DataQualityValidator pure logic

Create:

```text
backend/app/validators/data_quality.py
tests/test_data_quality_validator.py
```

Required semantic tests:

- missing primary key → FAILED.
- duplicate primary key → FAILED.
- missing required field → FAILED or WARNING per rule.
- invalid timestamp → FAILED.
- invalid enum → FAILED.
- schema drift → FAILED or manual review.
- stale data → WARNING or FAILED per rule.
- insufficient history → WARNING.
- high < low → FAILED.
- negative price/volume/amount → FAILED.
- findings include rule_id, severity, row_key/field, expected condition, business message.

Evidence:

```text
execute-evidence/8.3-red.txt
execute-evidence/8.3-green.txt
```

### 8.4 DataQualityValidator persistence and evidence/staging

Extend:

```text
backend/app/validators/data_quality.py
tests/test_data_quality_validator.py
tests/test_batch_c_validation_flow.py
```

Required behavior:

- persist `validation_report`.
- persist `data_quality_log`.
- FAILED report sets `can_write_clean=false`.
- SUCCESS FetchResult with nonexistent staging table cannot be validated as clean-write-ready.
- raw evidence path must exist when used as evidence.
- validation failure preserves raw/audit evidence and does not delete source files.

Evidence:

```text
execute-evidence/8.4-red.txt
execute-evidence/8.4-green.txt
```

### 8.5 SourceConflictValidator pure logic

Create:

```text
backend/app/validators/source_conflict.py
tests/test_source_conflict_validator.py
```

Required semantic tests:

- objective value within tolerance → PASSED/no conflict.
- slightly over warning threshold → WARNING.
- severe diff → SEVERE_CONFLICT.
- source-specific methodology field → no severe conflict; mark per-source/methodology difference.
- missing peer source → no false severe conflict.
- threshold lookup by data_domain/field, not global hard-code only.

Evidence:

```text
execute-evidence/8.5-red.txt
execute-evidence/8.5-green.txt
```

### 8.6 SourceConflictValidator persistence/manual review

Extend:

```text
backend/app/validators/source_conflict.py
tests/test_source_conflict_validator.py
tests/test_batch_c_validation_flow.py
```

Required behavior:

- severe conflict writes `source_conflict`.
- unresolved severe conflict writes `manual_review_queue`.
- conflict links run_id/job_id/data_domain/source/field/values/tolerances/severity.
- methodology difference does not block clean by default, but remains explainable by source.
- manual review does not directly patch clean; it queues review or downstream manual_patch request only.

Evidence:

```text
execute-evidence/8.6-red.txt
execute-evidence/8.6-green.txt
```

### 8.7 Align FetchStatus / PortErrorStatus and redact errors

Modify as needed:

```text
backend/app/datasources/fetch_result.py
backend/app/datasources/adapters/fetch_port.py
backend/app/datasources/fetch_log.py
tests/test_data_adapter_contract.py
tests/test_fetch_log.py
```

Required behavior:

- AUTH_FAILED, RATE_LIMITED, NETWORK_ERROR, SCHEMA_DRIFT, NOT_PUBLISHED_YET map consistently.
- PortErrorStatus cannot drift from FetchStatus without explicit mapping test.
- `error_message` persisted to fetch_log redacts token/password/api_key/secret/authorization/bearer.
- Real vendor Port implementation remains out of scope.

Evidence:

```text
execute-evidence/8.7-red.txt
execute-evidence/8.7-green.txt
```

### 8.8 End-to-end validation flow with WriteManager

Create or extend:

```text
tests/test_batch_c_validation_flow.py
tests/test_write_manager.py
```

Required paths:

```text
valid staging data
  -> DataQualityValidator PASSED
  -> SourceConflictValidator no severe conflict
  -> DbValidationGate allows
  -> WriteManager writes clean

invalid staging data
  -> DataQualityValidator FAILED
  -> DbValidationGate rejects
  -> WriteManager does not write clean
  -> validation_report/data_quality_log/write_audit_log preserved
```

Evidence:

```text
execute-evidence/8.8-red.txt
execute-evidence/8.8-green.txt
```

### 8.9 Documentation/status update

Update:

```text
docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/README.md
docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/DECISIONS.md
docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/BATCH_C_REPAIR_STATUS.md
```

Required content:

- Batch C completed items.
- Deferred items to Batch D/Round 3/Round 4/Round 5.
- Migration 005 constraints caveats if DuckDB limitations apply.
- Validation commands and results.
- ResourceGuard trigger status.
- Confirmation that no frontend/API/Agent/real Port work was done.

Evidence:

```text
execute-evidence/8.9-docs.txt
```

### 8.10 Final gates and handoff

Run §10 commands. Save:

```text
execute-evidence/8.10-final-gates.txt
execute-evidence/8.10-detect-changes.txt
execute-evidence/8.10-handoff.txt
```

Then hand off to Audit. Do not finish-work before Audit.

---

## 9. Testing strategy

### 9.1 Tier A — targeted Batch C tests

```bash
pytest tests/test_data_quality_validator.py \
       tests/test_source_conflict_validator.py \
       tests/test_db_validation_gate.py \
       tests/test_ingestion_validation_migration.py \
       tests/test_batch_c_validation_flow.py -q
```

### 9.2 Tier B — existing contract regression

```bash
pytest tests/test_write_manager.py \
       tests/test_data_adapter_contract.py \
       tests/test_source_registry.py \
       tests/test_raw_store.py -q
```

### 9.3 Tier C — full backend gate

```bash
pytest -q --cov=backend --cov-fail-under=75
ruff check .
python -m compileall -q backend scripts tests
python scripts/production_gate.py
```

### 9.4 Tier D — docs/smoke

```bash
python scripts/init_db.py
python scripts/init_db.py
QMD_DATA_ROOT=data python scripts/ci_ingestion_smoke.py
QMD_DATA_ROOT=data python scripts/ci_validation_smoke.py
python scripts/check_doc_links.py
```

If `scripts/ci_validation_smoke.py` does not exist before Batch C, create it in this task.

### 9.5 Frontend non-goal

Only run frontend if a touched file or doc link requires it:

```bash
cd frontend
npm ci
npm audit --audit-level=high
npm run typecheck
npm run build
```

---

## 10. Acceptance commands

Execute must paste command output or summary into evidence files.

```bash
pip install -e ".[dev]"

pytest tests/test_data_quality_validator.py \
       tests/test_source_conflict_validator.py \
       tests/test_db_validation_gate.py \
       tests/test_ingestion_validation_migration.py \
       tests/test_batch_c_validation_flow.py -q

pytest tests/test_write_manager.py \
       tests/test_data_adapter_contract.py \
       tests/test_source_registry.py \
       tests/test_raw_store.py -q

pytest -q --cov=backend --cov-fail-under=75

ruff check .
python -m compileall -q backend scripts tests

python scripts/init_db.py
python scripts/init_db.py

QMD_DATA_ROOT=data python scripts/ci_ingestion_smoke.py
QMD_DATA_ROOT=data python scripts/ci_validation_smoke.py

python scripts/production_gate.py
python scripts/check_doc_links.py
```

---

## 11. Handoff to Audit

Execute final response must include only:

1. 改动文件清单。
2. 新增文件清单。
3. 删除文件清单。
4. 测试命令和结果。
5. ResourceGuard 是否触发。
6. 未完成项或需要用户确认的点。
7. Evidence file paths.
8. Explicit statement: `READY_FOR_AUDIT: yes/no`.

Audit begins with `AUDIT.plan.md`; not this handoff alone.

---

## 12. Execute Skill freeze

| Skill | 本任务 | 绑定 §8 | 触发 | `@` 指令 | 已执行 |
|-------|--------|---------|------|----------|--------|
| `trellis-execute` | 必做 | 每步 | 每步 | `@trellis-execute 按 MASTER §8 顺序执行，保存 red/green evidence。` | [ ] |
| `diagnose` | 条件 | §8.1–§8.8 | 测试失败或行为不符合业务语义 | `@diagnose 复现→缩小→修根因→回归，不允许兜底假绿。` | [ ] |
| `tdd` | 必做 | §8.1–§8.8 | 每个新增模块/规则 | `@tdd 先写失败测试，再最小实现，再重构。` | [ ] |
| `improve-codebase-architecture` | 条件 | §8.3–§8.8 | 出现 validator/gate 职责混杂 | `@improve-codebase-architecture 保持 pure logic、persistence、gate 边界分离。` | [ ] |
| `ponytail-review` | 不用 | — | 禁止 Execute 使用 | `N/A` | [ ] |
| `prototype` | 不用 | — | 禁止前端原型 | `N/A` | [ ] |
| `security` | 条件 | §8.7 | 错误脱敏与状态映射 | `@security 检查 token/password/api_key/secret/authorization/bearer 不入日志。` | [ ] |

---

## 13. Red flags

出现以下任一情况，必须停止并修正：

- 修改已应用 migration 004，而不是新增 005。
- 创建 `backend/validation/*` 平行目录。
- 恢复 `WriteManager(...)` 默认 stub gate。
- 数据源 adapter import `WriteManager`。
- validation FAILED 仍写 clean。
- severe conflict 被静默降级为 warning。
- 口径差异字段被强行合并为单一事实。
- error message 泄漏 token/password/api_key/secret。
- 为了通过测试跳过业务断言。
- 实现了 Orchestrator / frontend / Agent / release manifest 等越界内容。
- 大查询未受 ResourceGuard 约束。
- 生成临时 scratch/tmp/round report 作为最终产物。

---

## 14. Final DoD

- §8.1–§8.10 全部有 evidence。
- §10 全部通过，或未通过项有明确阻塞原因且不被声称为 PASS。
- `BATCH_C_REPAIR_STATUS.md` 已记录完成项与延后项。
- `validate-execute-handoff` 通过。
- `READY_FOR_AUDIT: yes`。
