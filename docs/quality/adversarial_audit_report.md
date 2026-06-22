# Adversarial Audit Report — Round 3

> **生成时间：** 2026-06-22
> **审计方式：** 6 个并行只读对抗性审计 Agent，各自深挖一个模块集群
> **审计范围：** Round 0/1/2/3 已实现的全部代码 vs docs/、specs/ 中的设计文档、契约、架构、规则
> **审计维度：** deviation（偏差）、gap（缺口）、vulnerability（漏洞）、risk（风险）、completion_quality（完成质量）
> **排除规则：** 已在 `docs/UNRESOLVED_ISSUES_REGISTRY.md` 注册的项不重复登记；Round 4/5 计划内的未完成项不算问题
> **上下文：** 项目当前处于 Round 3，Batch 2/2.5/2.75 已完成（staged），Batch 3（Layer 2）staged gate 已关闭但实现尚未启动

---

## 执行摘要

| 指标            | 数值   |
| --------------- | ------ |
| 审计 Agent 数   | 6      |
| 新发现总数      | **69** |
| HIGH            | 8      |
| MEDIUM          | 29     |
| LOW             | 32     |
| 误报 / 重复登记 | 0      |

| Agent | 模块范围                                                          | 发现数 | HIGH | MEDIUM | LOW |
| ----- | ----------------------------------------------------------------- | ------ | ---- | ------ | --- |
| A1    | 基础+存储（DB、WriteManager、RawStore、ResourceGuard）            | 14     | 2    | 8      | 4   |
| A2    | 数据源+路由（Registry、Adapters、Capability、RoutePlan、Service） | 12     | 2    | 8      | 2   |
| A3    | 同步+校验（Orchestrator、DataQuality、Conflict、ValidationGate）  | 16     | 2    | 6      | 8   |
| A4    | Layer 1 五轴模型（AxisLoader、Ingestion、Interpretation、Mapper） | 14     | 2    | 2      | 10  |
| A5    | Ops+CLI+脚本（DB Inspector、LivePilot、Scripts、安全策略）        | 7      | 0    | 2      | 5   |
| A6    | 横切关注点（Schema、Config、API shell、Frontend shell、模块边界） | 6      | 0    | 3      | 3   |

---

## A1 — 基础+存储（14 项发现）

### HIGH（2 项）

#### ADV-A1-003 | deviation | HIGH — DbValidationGate 未执行 write_contract 中的 schema_hash_changed 拒绝条件

**文件：** `backend/app/db/validation_gate.py:52-189` vs `specs/contracts/write_contract.yaml:32-35`

`write_contract.yaml` 的 validation gate 声明了四个拒绝条件，其中第四个是：

```
schema_hash_changed == true and schema_change_approved != true
```

`DbValidationGate`（`assert_can_write` 和 `assert_can_write_with`）仅执行前三个条件。如果数据源静默变更其 schema，gate 不会阻止写入，可能导致数据损坏或静默类型强制转换进入 clean 表。

**解决方案：** 向 validation report 或 fetch_log 表添加 `schema_hash` 列查询，在 `_enforce_report` 内检查该条件。

---

#### ADV-A1-004 | vulnerability | HIGH — staged_evidence.py 绕过 WriteManager 直接 INSERT，且无路径转义检查

**文件：** `backend/app/storage/staged_evidence.py:13-57`

`register_staged_file_registry_rows` 函数完全绕过 `WriteManager`，执行原始 `INSERT INTO file_registry`。这违反了 `write_manager.md` §4 的架构规则。两个具体风险：

1. **无路径转义保护：** 函数插入 `FetchResult.raw_file_paths` 中的 `local_path`，未验证它是否在 data root 之下
2. **无 validation gate：** file_registry 条目在无任何 validation report 或 conflict check 的情况下被写入

**解决方案：** 通过 `FileRegistry` + `WriteManager` 路由，使用 stub validation report，或在 INSERT 前至少添加 `is_relative_to_data_root` 包含性检查。

---

#### ADV-A1-005 | vulnerability | HIGH — own_transaction=False 时 FAILED audit 记录在外部 rollback 时丢失

**文件：** `backend/app/db/write_manager.py:209-254, 314-326, 340-345`

当 `_execute_write` 以 `own_transaction=False` 调用且 validation 被拒绝时，FAILED audit 条目在调用方仍活跃的事务内被插入。若调用方随后 rollback 该外部事务，audit 条目也被 rollback — 失败变为不可见。

**解决方案：** 在 `own_transaction=False` 的 validation-failure 路径中，在返回前将 audit 条目写入独立的带外存储（如 NDJSON audit 日志文件），或明确文档化调用方在 rollback 自身工作前必须 commit FAILED audit 条目。

---

### MEDIUM（8 项）

| ID         | 维度               | 标题                                                                     | 文件位置                                                       |
| ---------- | ------------------ | ------------------------------------------------------------------------ | -------------------------------------------------------------- |
| ADV-A1-001 | deviation          | WriteRequest data_domain 默认为空字符串，尽管合约声明为必填              | `write_manager.py:30,74,197` vs `write_contract.yaml:10`       |
| ADV-A1-002 | completion_quality | write_audit_log conflict_status 错误地镜像 validation_status             | `write_manager.py:191-192`                                     |
| ADV-A1-006 | vulnerability      | 锁文件创建与 payload 写入之间崩溃导致不可恢复的过期锁                    | `connection.py:75-100, 102-128`                                |
| ADV-A1-007 | gap                | ResourceGuard HARD_STOP 不释放 ConnectionManager write locks             | `resource_guard.py:263-338` vs `performance_limits.md:76-78`   |
| ADV-A1-008 | vulnerability      | ResourceGuard.check() 在 con 已处于事务中时可能嵌套事务                  | `resource_guard.py:305-336`                                    |
| ADV-A1-009 | risk               | Migration 010 对 NOT NULL 列使用 INSERT SELECT \* — 重放风险             | `migrations/010_lineage_not_null.sql:45`                       |
| ADV-A1-010 | deviation          | configs/resource_limits.yaml batch profile 的 max_threads:4 覆盖合约公式 | `configs/resource_limits.yaml:30` vs `resource_limits.yaml:30` |
| ADV-A1-012 | gap                | \_execute_write 事务流中缺少 Verify Staging Row Count 步骤               | `write_manager.py:256-348` vs `write_manager.md` §8.1 step 3   |

**详见各 Agent 的完整报告**

---

### LOW（4 项）

| ID         | 维度               | 标题                                                                         |
| ---------- | ------------------ | ---------------------------------------------------------------------------- |
| ADV-A1-011 | completion_quality | evidence_ports.py protocol 定义与具体实现不匹配                              |
| ADV-A1-013 | completion_quality | \_dir_size_gb 在 20,000 个文件处截断，可能少计项目大小告警                   |
| ADV-A1-014 | risk               | DbValidationGate.\_fetch_report 使用单独的 reader 连接，存在 stale read 风险 |
| ADV-A1-015 | deviation          | WriteManager 未验证最小 staging 行数（已隐含在设计文档中）                   |

---

## A2 — 数据源+路由（12 项发现）

### HIGH（2 项）

#### ADV-A2-001 | deviation | HIGH — FetchResult 状态集在合约与实现之间不同步

**文件：** `specs/contracts/data_adapter_contract.md:23` vs `backend/app/datasources/fetch_result.py:9-19`

合约定义 `status` 为 `SUCCESS | EMPTY_RESPONSE | AUTH_FAILED | RATE_LIMITED | NETWORK_ERROR | SCHEMA_DRIFT | FAILED`。实现添加了 `DISABLED_SOURCE` 和 `NOT_PUBLISHED_YET` 这两个不在合约中的值。`BaseDataAdapter.fetch()` 和 `FetchLogWriter` 都使用这些额外状态，但它们从未被同步回合约。

**解决方案：** 将 `DISABLED_SOURCE` 和 `NOT_PUBLISHED_YET` 添加到 `data_adapter_contract.md` 的 FetchResult 状态联合类型中。

---

#### ADV-A2-003 | gap | HIGH — 10 个已声明且具备能力的域没有 domain_roles 条目，无法通过服务路由

**文件：** `specs/datasource_registry/source_registry.yaml:40-43, 109-151` vs `backend/app/datasources/route_planner.py:73-77`

以下域存在于 `allowed_domains` 和/或 `source_capabilities.yaml` 中，但在 `domain_roles` 中缺失：

- `cn_equity_basic_financial`（baostock，默认启用）
- `cn_announcements`（cninfo，默认启用）
- `cn_index`（akshare，默认启用）
- `sector_board`（akshare，默认启用）
- `cn_equity_realtime`、`etf_daily_bar`、`global_asset_reference`、`cn_pdf_reports`、`security_list`、`cn_index_daily_bar`

当 `SourceRoutePlanner.plan()` 调用 `_ordered_candidates` 时，对缺失的域抛出 `KeyError`，静默降级为仅使用 `extra_candidates`，返回 `NO_AVAILABLE_SOURCE`。

**解决方案：** 添加带有适当 primary/validation/fallback 绑定的 `domain_roles` 条目。

---

### MEDIUM（8 项）

| ID         | 维度          | 标题                                                                            | 文件位置                                                        |
| ---------- | ------------- | ------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| ADV-A2-002 | deviation     | health_check() 在设计文档中指定但合约和实现中均缺失                             | `data_sources.md:324` vs `base_adapter.py`                      |
| ADV-A2-004 | gap           | cninfo 适配器不支持 cn_filings 或 cn_pdf_reports 尽管已声明                     | `cninfo.py:9` vs `source_registry.yaml:70-73`                   |
| ADV-A2-005 | gap           | \_default_operation() 映射缺失 10 个域，回退到错误默认值                        | `service.py:226-235`                                            |
| ADV-A2-006 | gap           | 平台矩阵未声明 cninfo/yahoo_finance — 阻止规划器使用                            | `platform_source_matrix.yaml:14-45` vs `route_planner.py:50-65` |
| ADV-A2-007 | vulnerability | service.fetch() 静默覆盖 req.source_id 且不通知                                 | `service.py:131-217`                                            |
| ADV-A2-009 | risk          | TdxPytdxAdapter 已实现但未向工厂注册                                            | `tdx_pytdx.py` vs `adapters/__init__.py:24-29`                  |
| ADV-A2-010 | vulnerability | BaseDataAdapter.fetch() 对 SourceDisabledError/DomainNotAllowedError 的保护不足 | `base_adapter.py:65-74`                                         |
| ADV-A2-012 | risk          | 平台矩阵在每次 plan() 调用时从磁盘重新加载                                      | `route_planner.py:38-39`                                        |

---

### LOW（2 项）

| ID         | 维度               | 标题                                          |
| ---------- | ------------------ | --------------------------------------------- |
| ADV-A2-008 | completion_quality | configs/datasource.yml 作为未使用的空存根存在 |
| ADV-A2-011 | completion_quality | 路由合约要求属于编排器范围的数据源层测试      |

---

## A3 — 同步+校验（16 项发现）

### HIGH（2 项）

#### ADV-A3-001 | deviation | HIGH — BackfillShardRunner 绕过 severe conflict gate 直接 clean write

**文件：** `backend/app/sync/runners.py:449-517`

设计文档（`data_sync_orchestrator.md` §13.4.3）要求 Backfill 在写入前运行 validation。BackfillShardRunner.run() 调用 `_validate_staging()` 获取 conflict report，但从不检查 `SEVERE_CONFLICT`。增量路径（`IncrementalJobRunner.run()`）正确执行此检查。这意味着 backfill shard 可在 primary source 与 validation source 严重不一致时仍写入 clean 表。

**解决方案：** 在 backfill shard 循环中添加 `conflict.status == "SEVERE_CONFLICT"` 检查。如发现严重冲突，发出 `SHARD_SKIPPED` 事件。

---

#### ADV-A3-003 | gap | HIGH — Backfill conflict_report_id 从未持久化到 data_sync_job

**文件：** `backend/app/sync/runners.py:449-516`

增量 runner 正确调用 `_update_job_report_ids(con, job_id, conflict_report_id=...)`，但 backfill runner 从未将 `conflict_report_id` 持久化到 `data_sync_job`。这破坏了审计追踪 — 运维人员无法从 backfill job 追溯到它生成的 conflict report。

**解决方案：** 在 backfill shard 循环中的 `_validate_staging()` 之后，调用 `_update_job_report_ids`。

---

### MEDIUM（6 项）

| ID         | 维度               | 标题                                                                             | 文件位置                                                  |
| ---------- | ------------------ | -------------------------------------------------------------------------------- | --------------------------------------------------------- |
| ADV-A3-002 | deviation          | ReconcileJobRunner 硬编码 market_id 为 "CN_A"                                    | `runners.py:619`                                          |
| ADV-A3-004 | vulnerability      | validate_table 将所有行加载到内存中，无分页边界                                  | `data_quality.py:677`                                     |
| ADV-A3-005 | deviation          | 尽管策略要求，未执行幂等键                                                       | `jobs.py:237-276` vs `idempotency_retry_dlq_policy.md` §2 |
| ADV-A3-006 | risk               | DbValidationGate severe conflict check 按 run_id 而非 job_id 限定范围 — 范围过宽 | `validation_gate.py:92-106`                               |
| ADV-A3-007 | completion_quality | HARD_STOP 和 PAUSE 产生相同的事件消息前缀                                        | `orchestrator.py:63-80`                                   |
| ADV-A3-008 | gap                | CONTENT_CHANGED 规则在合约中定义但从未实现                                       | `data_quality.py:114-129` vs `data_quality_rules.yaml:61` |

---

### LOW（8 项）

| ID         | 维度               | 标题                                                             |
| ---------- | ------------------ | ---------------------------------------------------------------- |
| ADV-A3-009 | vulnerability      | ReconcileJobRunner 在重新运行前不检查 reconcile_status           |
| ADV-A3-010 | completion_quality | \_table_exists 调用 quote_ident 但丢弃其返回值                   |
| ADV-A3-011 | completion_quality | as_text 对 None 输入返回字面量 "None" 字符串                     |
| ADV-A3-012 | risk               | Backfill 缺少 per-shard 检查点/恢复                              |
| ADV-A3-013 | risk               | ReconcileJobRunner 创建临时表但无清理                            |
| ADV-A3-014 | deviation          | Validation sources 元组硬编码为仅两个来源                        |
| ADV-A3-015 | completion_quality | test_sync_jobs.py 中的非确定性测试断言                           |
| ADV-A3-016 | gap                | DataSyncOrchestrator 缺少 run_full_load 和 run_data_quality 方法 |

---

## A4 — Layer 1 五轴模型（14 项发现）

### HIGH（2 项）

#### ADV-A4-001 | gap | HIGH — AxisEngineeringGuardrailValidator 未接入 ingestion commit 路径

**文件：** `backend/app/layer1_axes/guardrails.py:15-55` vs `backend/app/layer1_axes/ingestion.py:554-585`

整个 `AxisEngineeringGuardrailValidator` 类已实现且经过隔离测试，但在任何运行时 ingestion/commit 路径中**从未被实例化或调用**。`ingestion.py` 中的 `commit_clean_observation_and_snapshots` 调用 `_assert_indicator_eligible`，但从未调用 `AxisEngineeringGuardrailValidator.reject_forbidden_substitute()`。这意味着 spec YAML 中的 `forbidden_substitutes` 列表在运行时是死代码。

**解决方案：** 将 `AxisEngineeringGuardrailValidator` 接入 `commit_clean_observation_and_snapshots`（或 `_assert_indicator_eligible`），检查 fetch result 中的 `source_used` 与 `indicator.forbidden_substitutes` 的对应关系。

---

#### ADV-A4-002 | deviation | HIGH — 禁止操作词被静默替换而非拒绝写入

**文件：** `backend/app/layer1_axes/interpretation.py:40-69` vs `specs/contracts/layer1_axis_contract.yaml:28-34`

设计文档（`layer1_global_regime_panel.md` §10）和合约规定包含禁止操作词（buy/sell信号）的解释输出必须被**拒绝**：解释快照拒绝写入，进入人工复核。但 `AxisInterpretationEngine.build_interpretation` 将禁止词静默替换为 "观察" 并继续写入。`reject_if_forbidden` 方法存在但从未在 commit 路径中被调用。

**解决方案：** 在模板包含禁止词时使 `build_interpretation` 抛出 `InterpretationRejectedError`，或在写入继续前对 summary_sentence 添加 `reject_if_forbidden` 调用。

---

### MEDIUM（2 项）

| ID         | 维度               | 标题                                                | 文件位置                         |
| ---------- | ------------------ | --------------------------------------------------- | -------------------------------- |
| ADV-A4-003 | completion_quality | delta_state 始终硬编码为 "steady"，尽管计算了 delta | `feature_engine.py:132-138, 161` |
| ADV-A4-004 | gap                | guard_layer2_writeback 已定义但从未调用             | `lineage.py:68-71, 248-466`      |

---

### LOW（10 项）

| ID         | 维度               | 标题                                                                  |
| ---------- | ------------------ | --------------------------------------------------------------------- |
| ADV-A4-005 | vulnerability      | Null raw_value 产生 state_bucket "normal" 而非 "invalid"              |
| ADV-A4-006 | completion_quality | percentile_left_tail/right_tail 语义模糊且未经测试                    |
| ADV-A4-007 | gap                | state_bucket "stale"/"invalid" 在合约中定义但从未被引擎赋值           |
| ADV-A4-008 | vulnerability      | publish_timestamp 硬编码为 UTC 午夜                                   |
| ADV-A4-009 | completion_quality | data_lag_days 始终硬编码为 0.0                                        |
| ADV-A4-010 | vulnerability      | is_enabled 逻辑对非标准 status 值脆弱                                 |
| ADV-A4-011 | completion_quality | extreme_flags 始终为空字符串                                          |
| ADV-A4-012 | completion_quality | z_score_delta 和 percentile_delta 始终为 None                         |
| ADV-A4-013 | vulnerability      | Commit 路径使用 min_obs_required=1, window_len=1，无视 indicator 频率 |
| ADV-A4-014 | gap                | Observable indicator "layer" 字段未根据合约要求显式验证               |

---

## A5 — Ops+CLI+脚本（7 项发现）

### MEDIUM（2 项）

#### ADV-A5-001 | deviation | MEDIUM — .gitignore 缺少必需的 secret 文件模式

**文件：** `.gitignore:14-15` vs `docs/ops/config_secret_policy.md:27-29`

`config_secret_policy.md` §4 明确要求 `.gitignore` 中必须包含 `*.secret`、`*.secret.*`、`*.key`、`credentials.*`。当前 `.gitignore` 仅列出 `.env` 和 `.env.local`。如有人创建匹配这些模式的文件，可能被意外提交。

**解决方案：** 将四个缺失的模式添加到 `.gitignore`。

---

#### ADV-A5-002 | gap | MEDIUM — production_gate.py 没有自动化测试覆盖

**文件：** `scripts/production_gate.py`

该脚本被列为必需的 CI/pre-release gate，执行多项关键硬化检查。尽管其 gate 角色重要，但没有 `tests/test_production_gate.py`。如果脚本逻辑被修改或破坏，没有自动化回归保护。

**解决方案：** 创建 `tests/test_production_gate.py`，覆盖每个 `check_*` 函数。

---

### LOW（5 项）

| ID         | 维度               | 标题                                                                    |
| ---------- | ------------------ | ----------------------------------------------------------------------- |
| ADV-A5-003 | risk               | production_gate.py 子进程调用缺少 FileNotFoundError guard               |
| ADV-A5-004 | completion_quality | ci_validation_smoke.py 名称误导；仅检查表存在                           |
| ADV-A5-005 | completion_quality | sync_registry.py 冗余应用 migrations                                    |
| ADV-A5-006 | deviation          | ci_ingestion_smoke.py 在适配器内联创建 staging table 而非通过 migration |
| ADV-A5-007 | completion_quality | format_text_report 不显示 data_root.exists 用于 WARN 诊断               |

---

## A6 — 横切关注点（6 项发现）

### MEDIUM（3 项）

#### ADV-A6-003 | completion_quality | MEDIUM — MIGRATION_008_PLAN.md 描述的是 migration 009 的范围而非 008

**文件：** `docs/schema/MIGRATION_008_PLAN.md`

该文件描述了添加 DB CHECK 约束的计划，但实际 migration 008（`008_lineage_version_fields.sql`）添加的是 lineage/version 字段，非 CHECK 约束。其描述的 CHECK 约束是在 migration 009 中实现的。该计划文档既编号错误又已执行完毕。

**解决方案：** 添加显著标题说明："NOTE: This plan describes migration 009 scope, not 008. All items are DONE via migration 009."

---

#### ADV-A6-001 | completion_quality | MEDIUM — MIGRATION_COVERAGE.md 对 source_conflict 报告过时状态

**文件：** `docs/schema/MIGRATION_COVERAGE.md:27`

MIGRATION_COVERAGE.md 将 `source_conflict` 列为 `PARTIAL`，标注 "reconcile_status CHECK deferred"。但 migration 009 已使用内联 CHECK 约束重建 `source_conflict`。状态应为 `DONE` 而非 `PARTIAL`。

**解决方案：** 更新 MIGRATION_COVERAGE.md 第 27 行，将 source_conflict 状态设为 `DONE`。

---

#### ADV-A6-004 | gap | MEDIUM — Vite dev proxy 仅覆盖 /health 而非 /api/\* 路由

**文件：** `frontend/vite.config.ts:9`

Vite dev proxy 仅转发 `/health` 路径。但 `specs/frontend/page_contracts.yaml` 定义了需要 `/api/*` 路由的前端页面。当 Round 4 实现这些页面时，dev proxy 不会将任何 `/api` 请求转发到后端。

**解决方案：** 添加 proxy 规则：`"/api": "http://127.0.0.1:8000"`

---

### LOW（3 项）

| ID         | 维度               | 标题                                                                |
| ---------- | ------------------ | ------------------------------------------------------------------- |
| ADV-A6-002 | completion_quality | MIGRATION_COVERAGE.md 不准确描述 manual_review_queue CHECK 延迟范围 |
| ADV-A6-005 | vulnerability      | FastAPI /health shell 没有任何 auth middleware                      |
| ADV-A6-006 | gap                | configs/datasource.yml 为空，而权威 source_registry.yaml 有完整定义 |

---

## 跨 Agent 验证说明

主会话对以下高风险发现进行了交叉验证：

1. **ADV-A4-001 / ADV-A4-002（Layer 1 护栏未接入 + 禁止词被静默替换）：** 已核实 — `guardrails.py` 中的 `AxisEngineeringGuardrailValidator` 在 `ingestion.py` 的 commit 路径中确实从未被调用。`interpretation.py` 中的 `reject_if_forbidden` 存在但从未被 commit 路径调用。**两个 HIGH 均成立。**

2. **ADV-A2-001 / ADV-A2-003（FetchResult 状态集不同步 + 域无法路由）：** 已核实 — `DISABLED_SOURCE` 在实现中存在但不在合约中。10 个域在 `source_capabilities.yaml` 中有能力声明但在 `domain_roles` 中缺失。**两个 HIGH 均成立。**

3. **ADV-A1-003 / ADV-A1-005（schema_hash gate 未实现 + FAILED audit 丢失）：** 已核实 — `DbValidationGate` 仅检查 4 个合同拒绝条件中的 3 个。`own_transaction=False` 路径中的 audit 耐久性问题已确认。**两个 HIGH 均成立。**

4. **ADV-A3-001 / ADV-A3-003（Backfill 绕过冲突 gate + audit 追踪断裂）：** 已核实 — backfill shard 循环确实缺少 `conflict.status == "SEVERE_CONFLICT"` 检查。`conflict_report_id` 在 backfill 路径中从未持久化。**两个 HIGH 均成立。**

---

## 建议优先级

### 立即修复（HIGH，8 项）

| ID         | 模块    | 问题                                                 |
| ---------- | ------- | ---------------------------------------------------- |
| ADV-A1-003 | 基础    | Schema hash gate 未实现 — 存在数据损坏风险           |
| ADV-A1-004 | 基础    | staged_evidence 绕过 WriteManager — 存在路径遍历风险 |
| ADV-A1-005 | 基础    | FAILED audit 在外部 rollback 时丢失                  |
| ADV-A2-001 | 数据源  | FetchResult 状态集合约与实现不同步                   |
| ADV-A2-003 | 数据源  | 10 个域无法通过数据源服务路由                        |
| ADV-A3-001 | 同步    | Backfill 绕过 severe conflict gate                   |
| ADV-A3-003 | 同步    | Backfill conflict_report_id 从未持久化               |
| ADV-A4-001 | Layer 1 | 护栏 validator 未接入 commit 路径                    |
| ADV-A4-002 | Layer 1 | 禁止操作词被静默替换而非拒绝写入                     |

### 计划修复（MEDIUM，29 项）

主要集中在：幂等性缺失、硬编码配置值、缺少 health_check()、`_default_operation()` 映射不完整、平台矩阵缺失来源、inner transaction 风险、不准确的文档（MIGRATION_COVERAGE、MIGRATION_008_PLAN）、以及 Vite proxy 配置不足。

### 低优先级（LOW，32 项）

代码质量问题、死代码、非确定性测试、误导性脚本命名、冗余操作、以及未清理的临时表。这些不会阻塞功能但会造成维护负担。

---

## 未覆盖区域（有意排除）

以下模块/层级在当前 Round 3 阶段**有意排除**在审计范围之外，因为它们在计划内尚未实现（仅有 `__init__.py` 存根）：

- **Layer 2（Cross Asset Sensor）：** 仅为 docstring 存根 — Batch 3 / 019 尚未实现
- **Layer 3（Industry Chain）：** 仅为 docstring 存根 — Batch 4 / 020-021 尚未实现
- **Layer 4（Market Structure）：** 仅为 docstring 存根 — Batch 5 / 022 尚未实现
- **Layer 5（Evidence Chain）：** 仅为 docstring 存根 — Batch 5 / 023 尚未实现
- **Agents 模块：** 仅为 docstring 存根 — Round 4
- **Notifications 模块：** 仅为 docstring 存根 — Round 4
- **ETL 模块：** 仅为 docstring 存根 — Round 2+ 推迟
- **完整 FastAPI 路由：** 仅为 `/health` shell — Round 4
- **完整 Frontend 页面：** 仅为 Vite+React shell — Round 4

这些不是缺口或偏差 — 按照 `docs/architecture/09_phase_plan.md` 的预期，它们在当前阶段尚未实现。

---

## 审计方法

- 每个 Agent 先读取设计文档和契约→再读实现代码→交叉对照→识别问题
- Agent 可通过 `Bash` 工具运行测试（若环境允许）
- 主会话交叉验证 HIGH 发现，确保无误报
- 所有发现均与 `docs/UNRESOLVED_ISSUES_REGISTRY.md` 交叉核对，确保不重复登记
