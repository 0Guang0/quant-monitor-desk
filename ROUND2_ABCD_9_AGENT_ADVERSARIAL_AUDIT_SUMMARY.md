# Round2 Batch A/B/C/D 九维对抗性深度审计汇总报告

> 生成日期：2026-06-19  
> 审计对象：`quant-monitor-desk` 当前工作区  
> 审计基线：`specs/`、`docs/`、`docs/implementation_tasks/` 原始设计文档与执行计划  
> 审计方式：按 9 个独立审计角色顺序执行；本报告仅汇总结论，不替代各维度独立判定。

---

## 0. 审计边界与统一判定定义

### 0.1 不参考历史评分

本次审计不沿用历史审计分数、历史 PASS/FAIL 结论或历史主观评价。历史文档只作为仓库中存在的材料被交叉核对，不作为最终判定依据。

### 0.2 权威基线

本次审计以以下路径为权威基线：

- `specs/`
- `docs/`
- `docs/implementation_tasks/`

其中重点覆盖：

- `docs/implementation_tasks/README.md`
- `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`
- `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`
- `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`
- `docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/*`
- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/*`
- `specs/schema/schema.sql`
- `specs/contracts/*`
- `specs/datasource_registry/source_registry.yaml`

### 0.3 真实生产场景 / 生产等价场景定义

本次环境无法接入真实生产外部数据源、真实生产 DuckDB、真实 API key、真实券商/QMT 客户端或真实交易账户。为避免污染真实生产数据，本次采用生产等价场景：

- 使用临时 DuckDB / pytest tmp_path / fixture 数据。
- 使用项目 CLI 路径与 prod-path 测试验证 `init_db`、`sync_registry`、orchestrator bootstrap。
- 使用真实代码路径，不跳过 `ConnectionManager`、migrations、state machine、validators、WriteManager。
- 外部 I/O 使用 fixture / stub / mock，符合 `GLOBAL_TESTING_POLICY.md` 对外部 I/O mock 边界的要求。

残余风险：未覆盖真实外部 vendor API 行为、真实生产数据规模、真实权限模型、真实 API key / QMT 授权链路。

### 0.4 不污染项目定义

本次审计原则：

- 不修改原始设计文档。
- 不修改依赖锁文件。
- 不改写生产数据。
- 不提交无关代码。
- 仅新增本审计报告到项目根目录。

已观察到但未在本报告写入动作中清理的环境污染项：`frontend/=/npm-cache/_logs/` 为 npm 执行产生的未跟踪缓存日志目录，应单独清理或加入合适的临时目录策略。

### 0.5 评分规则

每个维度按 100 分制评分。只有全部维度均达到 95 分以上，并且 P0/P1 清零、当前阶段可修复 P2/P3 完成修复或有充分不阻塞理由，整体才可判定 PASS。

本次总体结论：**整体 FAIL，当前未达到 9 维全部 95+ 的质量门槛。**

---

## 1. 已执行验证命令与结果摘要

| 类别 | 命令 | 结果 |
|---|---|---|
| 后端全量测试 | `pytest -q` | PASS，约 362+ tests；存在 Starlette/httpx deprecation warning |
| 后端覆盖率 | `pytest -q --cov=backend --cov-fail-under=85` | PASS，总覆盖率 94.13% |
| Batch D orchestrator flow | `pytest tests/test_batch_d_orchestration_flow.py -q` | PASS，3 tests |
| Batch C validation/conflict | `pytest tests/test_batch_c_validation_flow.py tests/test_data_quality_validator.py tests/test_source_conflict_validator.py -q` | PASS，37 tests |
| sync orchestrator/jobs/migration | `pytest tests/test_sync_orchestrator.py tests/test_sync_jobs.py tests/test_sync_migration.py -q` | PASS，24 tests |
| schema/db validation | `pytest tests/test_schema_contract.py tests/test_schema_migration.py tests/test_db_validation_gate.py tests/test_duckdb_connection.py -q` | PASS，37 tests |
| prod-path 等价验证 | `pytest tests/test_sync_orchestrator.py::test_syncRegistry_cli_syncsYamlToDb tests/test_sync_orchestrator.py::test_orchestratorBootstrap_callsSyncToDb tests/test_ingestion_validation_migration.py::test_initDb_prodPath_appliesMigration005 -q` | PASS，3 tests |
| performance/resource guard | `pytest tests/test_resource_guard.py tests/test_audit_fixes.py::test_resourceGuard_largeCacheDir_completesWithinReasonableTime tests/test_sync_orchestrator.py::test_backfillJob_eachShard_callsResourceGuardBeforeFetching -q` | PASS，29 tests |
| 前端 typecheck | `npm run typecheck` in `frontend` | PASS |
| 前端 test | `npm test` in `frontend` | PASS，1 test |
| 前端 build | `npm run build` in `frontend` | PASS，bundle `190.75 kB`, gzip `60.16 kB` |
| ruff | `ruff check .` | 未执行成功：当前 CodexPro bash allowlist 拦截，不能计入已执行工具 |
| ponytail CLI | `ponytail` | 未确认存在可执行 CLI；本次按 ponytail-review / code-simplification 理念做静态审计，不能计为独立 CLI 执行结果 |

---

## 2. 九个独立审计 Agent 汇总结论

| Agent | 维度 | 评分 | PASS/FAIL | 关键扣分原因 |
|---|---|---:|---|---|
| Agent 1 | 当前完成情况、完成质量、Round3 进入可行性 | 96 | PASS | 可进入 Round3，但仍有若干非阻塞 Round3 early/mid/later 缺口 |
| Agent 2 | 实际实现与原始设计文档偏差 | 93 | FAIL | 部分 Round2 设计要求只实现骨架或延迟到 Round3；rule/version/lineage 强约束不足 |
| Agent 3 | ponytail 简化与冗余审计 | 91 | FAIL | orchestrator 偏胖，存在可压缩分支与职责过载 |
| Agent 4 | 代码质量与安全质量 | 94 | FAIL | ruff 未能执行；结构化 telemetry / error path / version binding 不完整 |
| Agent 5 | 可维护性与测试覆盖 | 96 | PASS | 覆盖率良好；组合场景和真实 vendor E2E 不足 |
| Agent 6 | 规范性、工程质量、架构设计 | 94 | FAIL | orchestrator 既协调 fetch/validate/write/reconcile 又承担部分策略，深模块边界需加固 |
| Agent 7 | 解耦性、嵌套、工程规范细节 | 95 | PASS | 边界通过；仍有隐式顺序依赖 |
| Agent 8 | 性能占用与运行速度 | 95 | PASS | ResourceGuard 与分片机制通过；真实大数据规模未验证 |
| Agent 9 | 数据库一致性与 schema 风险 | 94 | FAIL | schema 字段约束偏宽，部分状态/版本/lineage 未由 DB 强制约束 |

---

## 3. P0/P1/P2/P3 总问题清单与解决方案

### 3.1 P0 — 阻断级问题

| ID | 问题 | 证据位置 | 影响 | 当前阶段是否可修复 | 修复状态 | 解决方案 | 验证方式 |
|---|---|---|---|---|---|---|---|
| P0-00 | 未发现 P0 阻断级问题 | 全量 pytest、schema migration、prod-path 等价验证均通过 | 无直接阻断 Round3 进入的问题 | 不适用 | 不适用 | 无 | 继续保持全量测试、schema contract 与 prod-path smoke 作为 gate |

---

### 3.2 P1 — 高风险 / 必须优先闭环

#### P1-01 — Orchestrator 职责过载，影响 ponytail 与架构深度

- **涉及维度**：Agent 3、Agent 6、Agent 7、Agent 8
- **证据位置**：`backend/app/sync/orchestrator.py`
- **具体问题**：`DataSyncOrchestrator` 同时负责 job 创建、状态迁移、ResourceGuard、adapter fetch、validation、conflict、write、backfill shard、reconcile delegate。虽然测试通过，但接口变胖，未来 Round3/4 继续叠加时会形成高耦合中心。
- **影响**：新增 job type、Layer snapshot、reconcile fetch 或 partial write 时容易引入交叉回归；不满足 ponytail “删除不必要 bloat / 保持深模块”原则。
- **当前阶段是否可修复**：可修复。
- **修复状态**：未修复，本报告记录。
- **解决方案**：
  1. 保留 `DataSyncOrchestrator` 为门面。
  2. 将 fetch/validate/write 流程抽为 `SyncRunExecutor` 或 `IncrementalJobRunner`。
  3. 将 reconcile 处理抽为 `ReconcileJobRunner`。
  4. 将 backfill shard loop 抽为 `BackfillShardRunner`。
  5. 保持外部接口兼容，不改变现有测试行为。
- **验证方式**：
  - `pytest tests/test_sync_orchestrator.py tests/test_batch_d_orchestration_flow.py -q`
  - `pytest -q --cov=backend --cov-fail-under=85`
  - 对 refactor 前后 `job_event_log`、`data_sync_job.status`、`write_audit_log` 做行为快照比较。

#### P1-02 — `rule_version` / `contract version` / lineage 版本约束未完全落库

- **涉及维度**：Agent 2、Agent 4、Agent 9
- **证据位置**：`backend/app/validators/data_quality.py`、`backend/app/validators/source_conflict.py`、`specs/schema/schema.sql`
- **具体问题**：设计要求质量规则必须版本冻结，validation report 应记录 rule version 与输入 fetch/content hash；当前 validator 读取规则并记录 rule_id/severity，但未在 `validation_report` / `data_quality_log` / `source_conflict` 中完整持久化 `rule_version`、`rule_set_id`、`source_fetch_ids`、`source_content_hashes` 等 lineage 字段。
- **影响**：后续 Round3 Layer snapshot 与证据链无法严格追溯“哪一版规则产生了哪个判断”；回归审计、重跑、人工复核存在证据缺口。
- **当前阶段是否可修复**：可修复。
- **修复状态**：未修复，本报告记录。
- **解决方案**：
  1. 在 schema migration 中为 `validation_report` 增加 `rule_set_id`、`rule_version`、`source_fetch_ids_json`、`source_content_hashes_json`。
  2. 为 `data_quality_log` 增加 `rule_version`。
  3. 为 `source_conflict` 增加 `tolerance_rule_set_id`、`rule_version` 或等效字段。
  4. 修改 `DataQualityRequest` / `SourceConflictRequest`，让版本字段从 request 进入 report 和 DB。
  5. 增加 contract tests。
- **验证方式**：
  - `pytest tests/test_data_quality_validator.py tests/test_source_conflict_validator.py -q`
  - `pytest tests/test_schema_contract.py tests/test_schema_migration.py -q`
  - 新增测试：`test_validationReport_persistsRuleVersionAndFetchLineage`、`test_sourceConflict_persistsToleranceRuleVersion`。

#### P1-03 — 部分 Round2 原始执行计划只达到可验证骨架，未达到真实 vendor E2E

- **涉及维度**：Agent 1、Agent 2、Agent 8
- **证据位置**：`docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/012_implement_data_adapter_contract.md`、`014_implement_data_sync_orchestrator.md`、`backend/app/datasources/adapters/*`
- **具体问题**：adapter skeleton、FetchPort、orchestrator flow 可测试，但未接入任何真实 vendor FetchPort 的端到端链路。QMT / Yahoo 等按设计默认禁用是合理边界，但至少一个非高危公开/fixture vendor 的生产等价 E2E 应形成闭环。
- **影响**：Round3 建模层会依赖 ingestion 的真实数据质量，纯 fixture E2E 不能暴露 vendor latency、schema drift、rate limit、auth failure、publish lag 等真实问题。
- **当前阶段是否可修复**：部分可修复。真实 vendor 接入需要用户授权与外部服务条件；可先实现 vendor fixture adapter / local file adapter E2E。
- **修复状态**：未修复，本报告记录。
- **解决方案**：
  1. 增加一个 `LocalFixtureFetchPort` 或官方可公开访问、无需凭证的只读 vendor adapter。
  2. 用真实 orchestrator 路径跑 fetch → staging → validate → write → audit log。
  3. 对 QMT 继续保持默认禁用，禁止未授权连接。
- **验证方式**：
  - 新增 `tests/test_vendor_fetch_e2e.py`。
  - 断言 `fetch_log`、`validation_report`、`write_audit_log`、clean table 均产生正确记录。

#### P1-04 — DB CHECK / enum 强约束不足

- **涉及维度**：Agent 9、Agent 4、Agent 6
- **证据位置**：`specs/schema/schema.sql`、`backend/app/db/migrations/*`
- **具体问题**：多个状态字段依赖应用层验证，DB 侧没有足够 CHECK 约束，例如 `fetch_log.status`、`source_registry.source_type/license_type`、`manual_review_queue.status`、`source_conflict.reconcile_status`。
- **影响**：如果绕过应用层或未来脚本直接写入 DB，可能产生非法状态，破坏后续 Round3/4 下游判断。
- **当前阶段是否可修复**：可修复，但需要 migration。
- **修复状态**：未修复，本报告记录。
- **解决方案**：
  1. 新增 migration，使用 explicit column list rebuild 表。
  2. 对 status / severity / source_type / parse_status 等字段增加 CHECK。
  3. 对历史数据先做 preflight validation。
- **验证方式**：
  - `pytest tests/test_schema_migration.py tests/test_schema_contract.py -q`
  - 新增 `test_dbRejectsInvalidFetchStatus`、`test_dbRejectsInvalidManualReviewStatus`。

#### P1-05 — ruff / format gate 未在本次环境成功执行

- **涉及维度**：Agent 4、Agent 6
- **证据位置**：本次命令记录，`ruff check .` 被 CodexPro bash allowlist 拦截。
- **具体问题**：虽然 pytest 和 build 通过，但静态 lint / format gate 未能作为证据链完成。
- **影响**：无法确认复杂度、import、format、部分安全/质量规则是否全绿。
- **当前阶段是否可修复**：环境可执行后可修复。
- **修复状态**：未修复，本报告记录。
- **解决方案**：
  1. 在允许完整本地命令的 shell 中执行 `uv run ruff check .`。
  2. 执行 `uv run ruff format --check .`。
  3. 若失败，按最小变更修复。
- **验证方式**：
  - `uv run ruff check .`
  - `uv run ruff format --check .`

---

### 3.3 P2 — 中风险 / 当前阶段应尽量修复

#### P2-01 — Backfill 目前偏 fetch/shard 骨架，未执行完整 post-shard validate + clean write 闭环

- **涉及维度**：Agent 1、Agent 2、Agent 8
- **证据位置**：`backend/app/sync/orchestrator.py::run_backfill`
- **具体问题**：backfill shard 能分片、调用 ResourceGuard、fetch 与记录事件，但没有完整走每个 shard 的 validate + write clean path。
- **影响**：真实历史补齐时，可能 fetch 成功但未被质量门和 clean write 完整保护。
- **当前阶段是否可修复**：可修复。
- **修复状态**：未修复。
- **解决方案**：复用 incremental pipeline，为每个 shard 增加 validate/write 或显式标记为 fetch-only backfill skeleton，并在 DB 中记录不可写状态。
- **验证方式**：新增 `test_backfillShard_successPath_validatesAndWritesClean`。

#### P2-02 — Reconcile 未真实 re-fetch / compare，仅根据当前 conflict 状态进入 resolved/manual review

- **涉及维度**：Agent 1、Agent 2、Agent 9
- **证据位置**：`backend/app/sync/orchestrator.py::run_reconcile`
- **具体问题**：adapter 参数保留，但当前未调用 adapter re-fetch；reconcile 的真实二次抓取比较未完成。
- **影响**：无法验证“重新抓取仍冲突进入人工复核”的完整真实路径。
- **当前阶段是否可修复**：部分可修复。可先实现 fixture adapter re-fetch。
- **修复状态**：未修复。
- **解决方案**：实现 re-fetch compare path；若 re-fetch 后仍超过 severe threshold，则 `record_unresolved_reconcile` 入队；否则更新 `RESOLVED_BY_REFETCH`。
- **验证方式**：新增 `test_runReconcile_refetchStillDiff_entersManualReview` 与 `test_runReconcile_refetchMatches_resolvesByRefetch`。

#### P2-03 — Error / telemetry 结构化程度不足

- **涉及维度**：Agent 4、Agent 6、Agent 8
- **证据位置**：`job_event_log.message`、`data_sync_job.error_message`
- **具体问题**：错误信息有 redaction，但 event payload 与 structured telemetry 没有统一 schema。
- **影响**：生产 incident 诊断仍依赖 message 文本，不利于聚合检索、报警与审计。
- **当前阶段是否可修复**：可修复。
- **修复状态**：未修复。
- **解决方案**：定义 `job_event_log.payload_json` schema，至少包含 `error_code`、`source_id`、`task_id`、`retry_count`、`decision`、`rule_id`。
- **验证方式**：新增 `test_jobEventLog_payloadSchema_isMachineReadable`。

#### P2-04 — Partial success / item-level audit 覆盖不足

- **涉及维度**：Agent 4、Agent 5、Agent 8
- **证据位置**：`docs/implementation_tasks/ROUND_2_DATA_INGESTION_VALIDATION/014_implement_data_sync_orchestrator.md` §15
- **具体问题**：task 文件要求批任务支持 item-level 部分成功，不得用总状态覆盖全部；当前 backfill shard 有部分事件，但 item-level clean write / retry / skip audit 还不完整。
- **影响**：部分数据失败时可能难以定位到 instrument/partition/task 粒度。
- **当前阶段是否可修复**：可修复。
- **修复状态**：未修复。
- **解决方案**：引入 `task_id` / partition-level result 表或扩展 `job_event_log.payload_json`；所有 shard retry/skip/partial success 写入事件。
- **验证方式**：新增 `test_partialSuccess_eachItemWritesAuditEvent`。

#### P2-05 — Schema 字段命名存在隐式映射：`allowed_domain` vs `allowed_domains`

- **涉及维度**：Agent 2、Agent 9
- **证据位置**：`specs/schema/schema.sql`、`backend/app/datasources/source_registry.py`
- **具体问题**：DB 字段为 `allowed_domain`，代码对象为 `allowed_domains`，通过 JSON string 转换落库。当前可运行，但语义不够直观。
- **影响**：新 Agent 或未来 migration 容易误读为单一 domain 字段。
- **当前阶段是否可修复**：可修复，但涉及 migration / compatibility。
- **修复状态**：未修复。
- **解决方案**：保留兼容字段或新增 `allowed_domains_json`，文档明确旧字段含义；后续 migration 逐步替换。
- **验证方式**：新增 schema contract test，断言 DB 字段内容为 JSON array 且 loader 双向一致。

#### P2-06 — 真实生产数据规模 / 外部依赖行为未验证

- **涉及维度**：Agent 1、Agent 2、Agent 8、Agent 9
- **证据位置**：本次验证边界说明。
- **具体问题**：生产等价测试覆盖了 CLI、migrations、orchestrator、fixture adapter，但未覆盖真实 vendor、真实授权、真实数据规模、真实 IO latency。
- **影响**：Round3 初期可能暴露性能、schema drift、rate limit 与外部时区/交易日问题。
- **当前阶段是否可修复**：需要用户授权与环境支持；当前只能部分修复。
- **修复状态**：未修复。
- **解决方案**：建立只读 staging / snapshot / fixture-scale 数据集；优先使用脱敏快照或只读 vendor sandbox。
- **验证方式**：新增 staging smoke runbook 与 `scripts/production_equivalent_smoke.py`。

#### P2-07 — ADR 不足：关键事务边界与延迟设计未形成决策记录

- **涉及维度**：Agent 6、Agent 4
- **证据位置**：`docs/decisions/` 或相关 docs 未见完整 ADR。
- **具体问题**：validation/conflict/write transaction policy、COMPLETED 与 write atomicity、应用层 CHECK vs DB CHECK 的设计理由需要 ADR 固化。
- **影响**：后续 Agent 容易重复争论或做出相反实现。
- **当前阶段是否可修复**：可修复。
- **修复状态**：未修复。
- **解决方案**：新增 ADR：`ADR-xxx-ingestion-validation-write-transaction-boundary.md`。
- **验证方式**：docs link check + 新增文档索引引用。

---

### 3.4 P3 — 低风险 / 卫生与可维护性优化

#### P3-01 — `frontend/=/npm-cache/_logs/` 临时目录污染

- **涉及维度**：Agent 1、Agent 4、Agent 6
- **证据位置**：`frontend/=/npm-cache/_logs/2026-*.log`
- **具体问题**：执行 npm 命令后产生未跟踪缓存日志目录。
- **影响**：污染工作区、影响 final package cleanup。
- **当前阶段是否可修复**：可修复。
- **修复状态**：未修复。
- **解决方案**：删除 `frontend/=/`，并检查 npm cache 环境变量；必要时将 cache 指向 `.audit-sandbox/npm-cache` 且加入 ignore。
- **验证方式**：`show_changes` 确认未跟踪临时目录消失。

#### P3-02 — Starlette/httpx deprecation warning

- **涉及维度**：Agent 4、Agent 5
- **证据位置**：`pytest -q` warning summary。
- **具体问题**：测试运行出现 `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.`
- **影响**：当前不阻塞测试，但长期会导致依赖升级风险。
- **当前阶段是否可修复**：可修复，但需确认依赖策略。
- **修复状态**：未修复。
- **解决方案**：按项目依赖策略安装/锁定 `httpx2` 或更新 FastAPI/Starlette test client 路径。
- **验证方式**：`pytest -q` warning-free 或文档说明接受原因。

#### P3-03 — 前端测试覆盖极少

- **涉及维度**：Agent 5、Agent 8
- **证据位置**：`frontend/src/App.test.tsx` 仅 1 test。
- **具体问题**：当前 Round2 重点为后端 ingestion，前端为 shell 阶段；但若进入 Round4 会明显不足。
- **影响**：Round4 前端数据绑定、Notification Center、Layer 页面风险高。
- **当前阶段是否可修复**：当前阶段非阻塞，但可提前补充 smoke。
- **修复状态**：未修复。
- **解决方案**：Round4 024-028 前增加 route-level contract tests、empty state、loading state、API envelope tests。
- **验证方式**：`npm test`、`npm run typecheck`、`npm run build`。

#### P3-04 — ponytail CLI 不可用或未确认

- **涉及维度**：Agent 3
- **证据位置**：本次未能确认独立 `ponytail` 可执行工具。
- **具体问题**：要求维度三使用 ponytail，但当前只按 ponytail-review 理念和 code-simplification skill 做审计。
- **影响**：审计证据链中缺少正式 ponytail CLI 输出。
- **当前阶段是否可修复**：环境提供工具后可修复。
- **修复状态**：未修复。
- **解决方案**：安装/暴露 ponytail CLI 或明确项目采用 `ponytail-review` 作为审计 skill 而非 CLI；重新运行并附输出。
- **验证方式**：`ponytail <target>` 或等效工具输出归档到报告。

#### P3-05 — docs / task 输出路径与实际代码路径存在命名漂移

- **涉及维度**：Agent 2、Agent 6
- **证据位置**：task 文件中写 `backend/sources/*`、实际代码在 `backend/app/datasources/*`。
- **具体问题**：实现路径与早期 task 输出文件名存在差异，功能上可接受，但容易误导后续 Agent。
- **影响**：新执行者可能在旧路径新增重复模块。
- **当前阶段是否可修复**：可修复。
- **修复状态**：未修复。
- **解决方案**：在 task README 或 architecture index 中增加 “actual implementation path mapping”。
- **验证方式**：docs link check + search 确认无重复 `backend/sources`。

---

## 4. 每个维度达到 95 分以上的最小修复清单

### Agent 1 — 当前完成情况 / Round3 Gate

当前 96，已 PASS。保持 gate：

- 后端全量 pytest。
- prod-path 等价测试。
- Round3 017 前明确 R3 early 缺口不阻塞依据。

### Agent 2 — 设计偏差

当前 93，达到 95 的最小修复：

1. 补充 rule/version/lineage DB 字段与 tests。
2. 对 Round2 未完成 skeleton 项形成明确 “Round3 early close” 实施计划。
3. 写 actual implementation path mapping，避免 `backend/sources` 与 `backend/app/datasources` 漂移。

### Agent 3 — Ponytail

当前 91，达到 95 的最小修复：

1. 拆分 `DataSyncOrchestrator.run_incremental`。
2. 提取 backfill/reconcile runner。
3. 合并重复 status / report update 分支。
4. 重新运行 full tests 与 ponytail/简化审计。

### Agent 4 — 代码质量

当前 94，达到 95 的最小修复：

1. 成功执行 `ruff check .` 与 `ruff format --check .`。
2. 修复或记录 deprecation warning。
3. 结构化 job event payload schema。

### Agent 5 — 维护性与测试覆盖

当前 96，已 PASS。增强建议：

- 补充 partial success / schema drift combination tests。
- 保持 coverage > 90%。

### Agent 6 — 规范性 / 工程质量 / 架构设计

当前 94，达到 95 的最小修复：

1. 新增 ADR：validation/conflict/write transaction boundary。
2. 新增 ADR 或 doc：DB CHECK vs app-layer validation 策略。
3. orchestrator runner 拆分。

### Agent 7 — 解耦性

当前 95，已 PASS。增强建议：

- 把隐式顺序依赖写入 pipeline contract。
- 将 `SyncValidationPipeline` / `SyncWritePipeline` 的接口作为唯一跨 seam 测试面。

### Agent 8 — 性能

当前 95，已 PASS。增强建议：

- 建立生产等价规模数据集。
- 添加 shard latency / resource profile 基准。
- 保持 ResourceGuard before heavy operation。

### Agent 9 — 数据库

当前 94，达到 95 的最小修复：

1. 新增 DB CHECK migration。
2. 增加 lineage/rule_version 字段。
3. 处理 `allowed_domain` 命名兼容问题。
4. 增加 invalid status rejection tests。

---

## 5. 总体结论

当前项目 Round2 Batch A/B/C/D 的核心功能链路已经可运行：

- source registry 可加载并同步 DB。
- adapter contract / fetch_log 可验证。
- validation / conflict validator 可运行。
- sync orchestrator 可完成 incremental、backfill skeleton、reconcile skeleton。
- schema migration 与 prod-path 等价测试通过。
- 后端 coverage 94.13%。
- 前端 build/typecheck/test 通过。

但按“全部维度 95+ 才 PASS”的严格标准，当前整体结论为：

> **整体 FAIL，不满足 9 个维度全部 95+ 的质量门槛。**

主要阻塞不是功能失败，而是：

1. `DataSyncOrchestrator` 职责过载，ponytail/架构维度未达 95。
2. rule/version/lineage DB 强约束不足。
3. 部分 Round2 设计要求仍停留在 skeleton / production-equivalent，而非真实 vendor E2E。
4. DB CHECK / status enum 约束偏弱。
5. ruff / ponytail CLI 证据链不完整。

推荐执行顺序：

1. 先修 P1-02 与 P1-04：schema / lineage / DB CHECK。
2. 再修 P1-01：orchestrator runner 拆分。
3. 然后补 P2-01 / P2-02：backfill 与 reconcile 真闭环。
4. 最后处理 P3 workspace hygiene 与 warning。

完成上述最小闭环后，重新执行：

```bash
pytest -q
pytest -q --cov=backend --cov-fail-under=85
ruff check .
ruff format --check .
cd frontend && npm run typecheck && npm test && npm run build
```

并补充真实或生产等价 vendor E2E，即可重新评估 9 个维度是否均达到 95+。
