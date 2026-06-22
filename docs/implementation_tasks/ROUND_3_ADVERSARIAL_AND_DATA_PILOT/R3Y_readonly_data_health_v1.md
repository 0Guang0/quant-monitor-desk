# R3Y_readonly_data_health_v1 — Read-only Data Health v1

## 1. 任务性质

本任务是 read-only data health 功能实现任务，不是数据写入任务、不是 production-live 启用任务。

目标是在真实数据 staged pilot 已产生 raw/staging evidence 后，提供最小可执行的数据质量检查能力，使系统能够用机器可读方式判断真实数据是否存在字段、schema、source lineage、row count、price/volume、date window、duplicate key、staleness 等问题。

本任务只读检查数据与 evidence，默认不得写 production DB，不得生成 source_health_snapshot clean table，不得运行 migration，不得执行真实 source fetch。

## 2. 分支与工作方式

- 建议分支：`feature/round3-readonly-data-health-v1`
- 基准分支：最新用户确认完成收尾后的 `master`
- 目标合并：`integration/round3` 或用户指定的下一批集成分支
- 工作方式：先 `/to-issues` 垂直切片计划，再 TDD/RED-GREEN 实现，再执行只读 gate

## 3. 任务目标

完成后必须提供一个最小 read-only data health 能力，用于检查：

1. staged pilot 产出的 raw/staging manifests 是否完整。
2. market daily bar 形态是否满足基础质量规则。
3. cninfo metadata 形态是否满足基础字段规则。
4. source_used / source_fetch_id / content_hash / as_of_timestamp 是否存在且一致。
5. duplicate primary key、invalid price、invalid volume、missing required fields、stale data、insufficient history 是否可被发现。
6. validation-only / disabled source 是否被错误用作 clean primary。
7. 输出是否是 machine-readable JSON + human-readable summary。
8. 是否能被下一阶段 sandbox clean-write rehearsal 作为 gate 输入。

## 4. /to-issues 垂直切片

执行者必须在 Plan 阶段使用 `/to-issues` skill。每个 issue 必须是 tracer-bullet vertical slice：可独立验证、覆盖端到端行为，并写明标题、建设内容、验收标准、依赖项、证据输出和测试计划。每个 issue 必须独立可测试，不能只做“CLI 壳”。

| Issue ID  | 垂直切片                               | 要实现/验证的功能                                                                                | 验收证据             |
| --------- | -------------------------------------- | ------------------------------------------------------------------------------------------------ | -------------------- |
| R3Y-DH-01 | DataHealth rule model                  | 定义 check result、severity、domain、rule_id、evidence_path、row_count、status                   | model tests          |
| R3Y-DH-02 | Manifest loader                        | 只读加载 raw/staging manifest 与 staged pilot evidence，路径必须 project-relative / sandbox-safe | loader tests         |
| R3Y-DH-03 | Daily bar health                       | 检查 missing required fields、invalid OHLC、negative volume、duplicate key、insufficient history | daily bar rule tests |
| R3Y-DH-04 | Metadata health                        | 检查 cninfo metadata required fields、empty title/date/source、vendor_api/source fields          | metadata rule tests  |
| R3Y-DH-05 | Source lineage health                  | 检查 source_used、source_fetch_id、content_hash、as_of_timestamp、validation-only misuse         | lineage rule tests   |
| R3Y-DH-06 | Staleness/window health                | 检查 date window、max lag、empty response、stale data taxonomy                                   | staleness tests      |
| R3Y-DH-07 | Report builder                         | 输出 JSON summary + markdown/text summary，不写 DB                                               | report tests         |
| R3Y-DH-08 | CLI/service entrypoint                 | 提供 read-only entrypoint，例如 `qmd data health` 或 thin script，禁止 free SQL                  | CLI tests            |
| R3Y-DH-09 | Integration with staged pilot evidence | 对 PROMPT_14 / v2 evidence 执行检查并输出 PASS/WARN/FAIL                                         | execute evidence     |

每个 issue 必须说明读取哪些文件、实现哪些函数、修改哪些测试、输出哪些 evidence。

## 5. 功能范围

### 5.1 必须实现

- DataHealthCheckResult / DataHealthReport 等最小模型。
- 只读 manifest/evidence loader。
- 至少支持以下 domain/profile：
  - `cn_equity_daily_bar`
  - `cn_announcements` / `cn_filings` metadata subset
  - staged pilot evidence bundle
- 规则最小集：
  - `MISSING_REQUIRED_FIELD`
  - `DUPLICATE_PRIMARY_KEY`
  - `INVALID_OHLC`
  - `NEGATIVE_VOLUME`
  - `EMPTY_RESPONSE`
  - `INSUFFICIENT_HISTORY`
  - `MISSING_SOURCE_USED`
  - `MISSING_SOURCE_FETCH_ID`
  - `MISSING_CONTENT_HASH`
  - `MISSING_AS_OF_TIMESTAMP`
  - `VALIDATION_ONLY_AS_PRIMARY`
  - `DISABLED_SOURCE_USED`
  - `STALE_DATA`
- JSON + text/markdown summary output。
- read-only CLI/service entrypoint。

### 5.2 明确不实现

- 不实现完整 Batch6 data-health 平台。
- 不写 `source_health_snapshot` clean table。
- 不写 production DB。
- 不执行 source fetch。
- 不做 full market scan。
- 不执行 migration。
- 不提供 free SQL。
- 不做前端页面。
- 不做自动修复。

## 6. 工程纪律

- 同时遵守 `R3Y_execution_discipline_addendum.md`。
- 代码遵守 `/karpathy-guidelines`、`/tdd`、`/ponytail` full。
- 测试遵守 `/testing-guidelines`。
- 新增或修改测试需注明覆盖范围、测试对象、目的或目标。
- 代码修复后运行完整测试；测试表达可修正，但测试目标不可改变。

## 7. 必读索引文件

执行前必须读取并摘要以下文件。此清单是最低要求，不是上限；执行者必须根据 data_quality_rules、ops docs、staged pilot evidence、tests、imports 继续追溯相关文件。

### 6.1 协议与当前收尾

- `AGENTS.md`
- `CLAUDE.md`
- `.trellis/workflow.md`
- `.trellis/spec/guides/complex-task-planning-protocol.md`
- `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
- `docs/AUDIT_DEFERRED_REGISTRY.md`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`
- `docs/RESOLVED_ISSUES_REGISTRY.md`

### 6.2 Data health / validation / DB 设计

- `docs/ops/data_health_cli.md`
- `docs/ops/db_inspect_cli.md`
- `docs/modules/data_validation_and_conflict.md`
- `docs/modules/duckdb_and_parquet.md`
- `docs/modules/write_manager.md`
- `docs/quality/staged_acceptance_policy.md`
- `docs/quality/production_live_pilot_policy.md`
- `specs/contracts/data_quality_rules.yaml`
- `specs/contracts/source_conflict_rules.yaml`
- `specs/contracts/write_contract.yaml`
- `specs/contracts/ops_db_inspect_contract.yaml`
- `specs/contracts/source_route_contract.yaml`
- `specs/datasource_registry/source_registry.yaml`
- `specs/datasource_registry/source_capabilities.yaml`

### 6.3 前序 staged pilot evidence

- `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/merge_gate_report.md`
- `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/raw_evidence_manifest.json`
- `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/staging_evidence_manifest.json`
- `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/source_fetch_attempt_summary.json`
- `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/validation_report_summary.json`
- `.trellis/tasks/feature-round3-real-data-staged-pilot/execute-evidence/production_db_no_mutation_proof.md`
- `.trellis/tasks/fix-round3-post14-audit-staged-pilot/execute-evidence/merge_gate_report.md`
- If present: `.trellis/tasks/feature-round3-real-data-staged-pilot-v2/execute-evidence/`

### 6.4 实现与测试

- `backend/app/ops/db_inspector.py`
- `backend/app/ops/staged_pilot.py`
- `backend/app/ops/mutation_proof.py`
- `backend/app/db/validation_gate.py`
- `backend/app/storage/`
- `backend/app/datasources/`
- `backend/app/validators/` if present
- `tests/test_ops_db_inspector.py`
- `tests/test_staged_pilot.py`
- `tests/test_data_quality_validator.py` if present
- `tests/test_source_conflict_validator.py` if present
- `tests/test_db_validation_gate.py`
- `tests/test_raw_store.py`

## 7. 允许修改范围

只在 plan 中列明后修改最小必要文件。候选范围：

- `backend/app/ops/data_health.py` new
- `backend/app/ops/data_health_cli.py` or existing ops wrapper, if project pattern requires
- `scripts/qmd_ops.py` or thin script wrapper, if existing command style requires
- `tests/test_ops_data_health.py` new
- `tests/test_data_quality_validator.py` narrow additions, if appropriate
- task-local Trellis evidence

## 8. 禁止事项

禁止：

- 写 production DB
- 创建/更新 production clean tables
- 写 `source_health_snapshot` clean table
- 执行真实 source fetch
- 运行 migration
- full market scan / full history scan
- free SQL input
- 暴露 raw data dumps beyond capped evidence
- 启用 disabled source
- 声称 production-live readiness

## 9. 验证命令

最低命令：

```bash
python -m pytest tests/test_ops_data_health.py -q
python -m pytest tests/test_ops_db_inspector.py tests/test_staged_pilot.py -q
python -m pytest tests/test_data_quality_validator.py tests/test_source_conflict_validator.py -q
python -m pytest tests/test_db_validation_gate.py tests/test_raw_store.py -q
```

如果某些测试文件不存在，执行者必须创建最小对应测试或记录为什么不适用。

## 10. 输出格式要求

Data health report 至少包含：

```yaml
report_id: string
generated_at: iso timestamp
input_kind: staged_pilot_evidence | manifest | duckdb_readonly
profile: cn_equity_daily_bar | cninfo_metadata | staged_pilot_bundle
overall_status: PASS | WARN | FAIL
checks:
  - rule_id: string
    severity: INFO | WARN | FAIL
    status: PASS | WARN | FAIL | NOT_APPLICABLE
    source_id: string|null
    domain: string
    evidence_path: string|null
    row_count: int|null
    message: string
production_db_mutated: false
source_fetch_performed: false
```

## 11. 完成标准

- 所有 `/to-issues` issue 有 evidence。
- 能对 PROMPT_14 staged pilot evidence 生成 read-only health report。
- 能发现至少一个人工构造的 bad fixture 问题。
- 不写 production DB，不 fetch source。
- 输出 JSON + text/markdown summary。
- 明确是否可作为 sandbox clean-write rehearsal 前置 gate。
