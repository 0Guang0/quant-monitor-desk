# MASTER 计划 — Round2.6 Phase C/D Routing Service Gate

> **Execute 入口**  
> Execute：本文件 + `implement.jsonl`。Audit 见同目录 `AUDIT.plan.md`（Execute 不读）。  
> Gate：本任务 PASS 后才能启动 Round3 `017_implement_layer1_axis_loader.md`。

---

## 0. 元信息

| 字段 | 值 |
|---|---|
| 任务 slug | `06-19-round2-6-routing-service-gate` |
| 原计划 Round | `docs/implementation_tasks/ROUND_2_6_DATASOURCE_ROUTING_OPS_ALIGNMENT/` |
| 父任务 | `06-19-round2-6-contract-gate` 必须 PASS，除非用户显式 override |
| Audit 计划 | `.trellis/tasks/06-19-round2-6-routing-service-gate/AUDIT.plan.md` |
| 分析豁免 | `analysis_waiver: false`; Execute 必须跑 GitNexus Phase 0 |

### 0.1 门控速查

- Execute 必须先验证父任务 Contract Gate 已 PASS 或有用户 override。
- 禁止实现 FastAPI diagnostics、frontend UI、BacktestReviewEngine、qmt_xqshare adapter。
- 默认不新增 schema migration；RoutePlan 先写 `job_event_log.payload_json`。如不可行，停止并请求用户确认 ADR。
- 每步 RED/GREEN 证据必填。

---

## 1. 目标

### 1.1 一句话目标

实现 Round2.6 进入 Round3 前的最小运行闭环：CapabilityRegistry、SourceRoutePlanner、DataSourceService、service-based sync path、生产等价 smoke、deferred registry 清理与 Round3 gate 更新。

### 1.2 非目标

- 不实现 Round4 API/Frontend/Agent/Backtest。
- 不启用 QMT/Yahoo/qmt_xqshare live source。
- 不新增依赖，除非用户另行确认 optional extra。
- 不新增 migration，除非 payload_json 方案被证据否定并获用户批准。
- 不重写 sync orchestrator 状态机；只做 service/fetch callable 边界接入。

---

## 2. 预期结果（A5 trace-ac 追溯用）

| ID | 预期结果 | 验证链 |
|---|---|---|
| AC-PRE | 父任务 `06-19-round2-6-contract-gate` PASS 或用户 override；其 tests/checker 成为本任务基线。 | §8.0; parent audit/report |
| AC-C1 | `SourceCapabilityRegistry` 可加载 `source_capabilities.yaml` 并校验 source/domain/operation；未知/缺失 capability 在 fetch 前失败。 | §8.1; `tests/test_source_capabilities.py` |
| AC-C2 | Adapter domain mismatch 关闭：supported_domains 与 source_registry domains 对齐，或有显式 compatibility map 且测试覆盖。 | §8.2; adapter tests |
| AC-C3 | `SourceRoutePlan` / `SourceRoutePlanner` 实现 READY/DISABLED_SOURCE/NO_AVAILABLE_SOURCE/CAPABILITY_MISSING/USER_AUTH_REQUIRED/RESOURCE_GUARD_PAUSED。 | §8.3; route planner tests |
| AC-C4 | `DataSourceService` 是生产 fetch facade：route → capability → ResourceGuard → internal adapter factory → fetch_log/event。 | §8.4; service tests |
| AC-C5 | Sync runner/orchestrator production path 使用 service 或 narrow fetch callable；不直接承担 route/adapter construction。 | §8.5; sync tests |
| AC-C6 | Module boundary checker 在 refactor 后保持 green。 | §8.6; checker |
| AC-C7 | RoutePlan evidence 写入 `job_event_log.payload_json`，包含 route_status、selected_source_id、skipped candidates/disabled reason/quality_flags。 | §8.7; job event tests |
| AC-C8 | QMT/Yahoo/qmt_xqshare 默认禁用仍生效；不 auto-probe、不 auto-login、不 silent fallback。 | §8.8; platform/source tests |
| AC-D1 | `scripts/production_equivalent_smoke.py` 或等效 smoke 走 capability → route → service → fixture fetch → validation/write 路径。 | §8.9; prod-path smoke |
| AC-D2 | ResourceGuard / shard / fixture-scale 指标在 smoke 中可观测，不污染项目。 | §8.10; smoke output |
| AC-D3 | `docs/AUDIT_DEFERRED_REGISTRY.md` 与 `docs/implementation_tasks/README.md` 的 Round3 gate 更新为当前 truth。 | §8.11; docs diff |
| AC-D4 | `ROUND2_6_PHASE_A_SELF_CHECK.md` 已迁移到 Trellis research 或删除；根目录不保留一次性 self-check。 | §8.12; workspace status |

---

## 3. 范围与边界

### 3.1 允许修改

- `backend/app/datasources/capability_registry.py`
- `backend/app/datasources/route_models.py`
- `backend/app/datasources/route_planner.py`
- `backend/app/datasources/service.py`
- `backend/app/datasources/adapters/*.py` domain alignment or compatibility map
- `backend/app/sync/runners.py` service/fetch callable接入
- `backend/app/sync/orchestrator.py` 如需注入 service/fetch callable
- `backend/app/sync/event_payload.py` route payload fields
- `scripts/production_equivalent_smoke.py`
- tests created by parent task and service-path tests
- `docs/AUDIT_DEFERRED_REGISTRY.md`
- `docs/implementation_tasks/README.md`
- root self-check cleanup

### 3.2 禁止修改

- `frontend/src/**`
- FastAPI diagnostics routes
- Backtest/review modules
- `pyproject.toml` / frontend package files, unless user confirms dependency change
- `backend/app/db/migrations/**` unless ADR + user approval
- qmt_xqshare adapter/source enablement

---

## 4. 代码地图

| 路径 | 操作 |
|---|---|
| `backend/app/datasources/capability_registry.py` | 创建 |
| `backend/app/datasources/route_models.py` | 创建 dataclasses/Pydantic models |
| `backend/app/datasources/route_planner.py` | 创建 |
| `backend/app/datasources/service.py` | 创建 facade |
| `backend/app/datasources/adapters/*.py` | domain alignment / compatibility map |
| `backend/app/sync/runners.py` | service/fetch callable 接入 |
| `backend/app/sync/orchestrator.py` | 最小注入调整 |
| `backend/app/sync/event_payload.py` | route payload fields |
| `scripts/production_equivalent_smoke.py` | service-path smoke |
| `tests/test_vendor_fetch_e2e.py` | 增加 service-path E2E |
| `tests/test_sync_orchestrator.py` | 更新 route-plan before fetch 断言 |
| `docs/AUDIT_DEFERRED_REGISTRY.md` | 最终对齐 |

---

## 5. 模式与约束

- Implement smallest working path; keep existing runner split.
- CapabilityRegistry must not replace SourceRegistry authority.
- SourceRoutePlanner must not silently fallback.
- DataSourceService may call adapter factory; API/Agent/sync callers should not.
- QMT/Yahoo/qmt_xqshare remain disabled unless user explicitly authorizes.
- Production-equivalent smoke uses isolated `.audit-sandbox` / temp data, not real production writes.

---

## 6. 接口/契约

- `SourceCapabilityRegistry.assert_source_domain_operation(source_id, domain, operation)`
- `SourceRoutePlan` with fields defined by `source_route_contract.yaml`
- `SourceRoutePlanner.plan(data_domain, operation, market_id=None)`
- `DataSourceService.preview_route(...) -> SourceRoutePlan`
- `DataSourceService.fetch(request, job_id=None) -> FetchResult`
- RoutePlan persistence default: `job_event_log.payload_json`

---

## 7. Red Flags

| Red Flag | 预防 |
|---|---|
| New schema migration without approval | Stop and request ADR/user confirmation |
| qmt_xqshare enabled | Tests must fail; non-goal |
| Runner re-aggregation | Keep runner classes; inject service/fetch callable |
| SourceRoutePlan generated after fetch | AC-C4/C5 require before adapter construction |
| Silent fallback | RoutePlan must carry selected/skipped/quality_flags |
| Production smoke pollutes repo | Use `.audit-sandbox` and cleanup evidence |

---

## 8. 实现步骤（RED/GREEN）

### 8.0 Parent gate check

| 字段 | 内容 |
|---|---|
| 做什么 | Verify parent Contract Gate PASS or user override; read parent audit/report. |
| RED 命令 | manual: missing parent PASS should block |
| GREEN 命令 | manual + `pytest` parent gating suite |
| 通过条件 | Parent tests green or explicit override recorded in `research/execute-boot.md`. |
| 已执行 | [ ] |

### 8.1 CapabilityRegistry

| 字段 | 内容 |
|---|---|
| 做什么 | Implement capability loader and validation from `source_capabilities.yaml`. |
| RED 命令 | `pytest tests/test_source_capabilities.py::test_unknownCapability_rejectedBeforeFetch -q` |
| GREEN 命令 | `pytest tests/test_source_capabilities.py -q` |
| 通过条件 | Missing source/domain/operation rejected before fetch; qmt/xqshare remains disabled. |
| 已执行 | [ ] |

### 8.2 Adapter domain reconciliation

| 字段 | 内容 |
|---|---|
| 做什么 | Align adapter supported_domains to registry domains or add tested compatibility map. |
| RED 命令 | `pytest tests/test_source_capabilities.py::test_adapterSupportedDomains_reconciledToCapabilityRegistryOrCompatibilityMap -q` |
| GREEN 命令 | `pytest tests/test_source_capabilities.py tests/test_adapter_skeletons.py -q` |
| 通过条件 | No hidden legacy domains; existing adapter behavior not broken. |
| 已执行 | [ ] |

### 8.3 SourceRoutePlanner

| 字段 | 内容 |
|---|---|
| 做什么 | Implement route models/planner from SourceRegistry + CapabilityRegistry + platform matrix. |
| RED 命令 | `pytest tests/test_source_route_planner.py::test_qmtDisabled_routePlanShowsSkipReason -q` |
| GREEN 命令 | `pytest tests/test_source_route_planner.py -q` |
| 通过条件 | Route status/candidates/disabled reason/fallback flags match contract. |
| 已执行 | [ ] |

### 8.4 DataSourceService facade

| 字段 | 内容 |
|---|---|
| 做什么 | Implement service fetch/preview facade; restrict production adapter factory usage. |
| RED 命令 | `pytest tests/test_datasource_service.py::test_serviceBuildsRouteBeforeFetch -q` |
| GREEN 命令 | `pytest tests/test_datasource_service.py -q` |
| 通过条件 | route/capability/resource guard happen before adapter fetch; fetch_log/event written. |
| 已执行 | [ ] |

### 8.5 Sync runner service-path integration

| 字段 | 内容 |
|---|---|
| 做什么 | Update runner/orchestrator to use service or narrow fetch callable without changing state machine. |
| RED 命令 | `pytest tests/test_sync_orchestrator.py::test_plannedJobWritesRoutePlanBeforeFetching -q` |
| GREEN 命令 | `pytest tests/test_sync_orchestrator.py tests/test_batch_d_orchestration_flow.py -q` |
| 通过条件 | Incremental/backfill/reconcile still pass; route plan before fetch. |
| 已执行 | [ ] |

### 8.6 Module boundary remains green

| 字段 | 内容 |
|---|---|
| 做什么 | Run/fix module boundary violations caused by service refactor. |
| RED 命令 | `python scripts/check_module_boundaries.py` before refactor baseline |
| GREEN 命令 | `pytest tests/test_module_boundaries.py -q && python scripts/check_module_boundaries.py` |
| 通过条件 | exit 0; no forbidden imports. |
| 已执行 | [ ] |

### 8.7 RoutePlan event payload

| 字段 | 内容 |
|---|---|
| 做什么 | Persist/expose route plan fields in `job_event_log.payload_json`. |
| RED 命令 | `pytest tests/test_datasource_service.py::test_serviceWritesRoutePlanPayloadBeforeFetch -q` |
| GREEN 命令 | `pytest tests/test_datasource_service.py tests/test_sync_jobs.py -q` |
| 通过条件 | payload includes route_status, selected_source_id, skipped/disabled reason, quality_flags. |
| 已执行 | [ ] |

### 8.8 Disabled source safety

| 字段 | 内容 |
|---|---|
| 做什么 | Ensure qmt/yahoo/qmt_xqshare disabled behavior survives service integration. |
| RED 命令 | `pytest tests/test_platform_source_matrix.py::test_qmtXqshareMissingEnvNotSchedulable -q` |
| GREEN 命令 | `pytest tests/test_platform_source_matrix.py tests/test_source_registry.py -q` |
| 通过条件 | no auto-probe, no auto-login, selected_source_id null when disabled. |
| 已执行 | [ ] |

### 8.9 Production-equivalent smoke service path

| 字段 | 内容 |
|---|---|
| 做什么 | Extend smoke to run capability→route→service→fixture fetch→validation/write in isolated data root. |
| RED 命令 | `python scripts/production_equivalent_smoke.py --use-service-path` (expected unsupported before implementation) |
| GREEN 命令 | `python scripts/production_equivalent_smoke.py --use-service-path --data-root .audit-sandbox/r26-smoke` |
| 通过条件 | route/event/fetch/validation/write evidence visible; no real production pollution. |
| 已执行 | [ ] |

### 8.10 ResourceGuard and scale evidence

| 字段 | 内容 |
|---|---|
| 做什么 | Add fixture-scale stats to smoke: row counts, shard count, elapsed, guard status. |
| RED 命令 | `pytest tests/test_resource_guard.py tests/test_vendor_fetch_e2e.py -q` plus missing smoke stats check |
| GREEN 命令 | same + smoke command |
| 通过条件 | ResourceGuard checked before heavy operation; metrics emitted. |
| 已执行 | [ ] |

### 8.11 Deferred registry and Round3 gate update

| 字段 | 内容 |
|---|---|
| 做什么 | Update deferred registry and implementation README gate to point to completed Trellis tasks, not root temp self-check. |
| RED 命令 | manual grep for `ROUND2_6_PHASE_A_SELF_CHECK.md` in gate text |
| GREEN 命令 | `pytest tests/test_documentation_index.py -q` |
| 通过条件 | Round3 gate references Trellis tasks/artifacts; stale deferred rows resolved or re-hooked. |
| 已执行 | [ ] |

### 8.12 Cleanup temporary self-check

| 字段 | 内容 |
|---|---|
| 做什么 | Remove root `ROUND2_6_PHASE_A_SELF_CHECK.md` only after its content is migrated to Trellis research/audit artifacts. |
| RED 命令 | manual: content not migrated should block deletion |
| GREEN 命令 | `git status --short` review |
| 通过条件 | No root one-off self-check remains; Trellis research preserves needed facts. |
| 已执行 | [ ] |

---

## 9. 测试层次

| 层次 | 必做 | 环境 | 命令 | 通过条件 | 证据 |
|---|---|---|---|---|---|
| 单元 | ✅ | local | `pytest tests/test_source_capabilities.py tests/test_source_route_planner.py tests/test_datasource_service.py -q` | exit 0 | `research/execute-evidence/9-unit.txt` |
| 集成 | ✅ | local | `pytest tests/test_sync_orchestrator.py tests/test_batch_d_orchestration_flow.py tests/test_vendor_fetch_e2e.py -q` | exit 0 | `research/execute-evidence/9-integration.txt` |
| 管道/集成链 | ✅ | prod-path | `python scripts/init_db.py --db .audit-sandbox/r26/qmd.duckdb && python scripts/production_equivalent_smoke.py --use-service-path --data-root .audit-sandbox/r26` | isolated prod-equivalent path passes | `research/execute-evidence/9-pipeline.txt` |
| E2E/smoke | ✅ | prod-path | `pytest tests/test_resource_guard.py tests/test_documentation_index.py -q` + smoke output | exit 0, no pollution | `research/execute-evidence/9-e2e.txt` |

---

## 10. 验收 Tier 表

| Tier | 环境 | 命令 | 通过条件 | 证据 | 勾 |
|---|---|---|---|---|---|
| A | local | `pytest tests/test_source_capabilities.py tests/test_source_route_planner.py tests/test_datasource_service.py -q` | exit 0 | | [ ] |
| A | local | `pytest tests/test_module_boundaries.py tests/test_platform_source_matrix.py tests/test_dependency_extras_contract.py -q` | exit 0 | | [ ] |
| A | local | `python scripts/check_module_boundaries.py` | exit 0 | | [ ] |
| A | local | `ruff check . && ruff format --check .` | exit 0 if available; otherwise exact blocker recorded | | [ ] |
| B | prod-path | `python scripts/init_db.py --db .audit-sandbox/r26/qmd.duckdb` | isolated DB initialized | | [ ] |
| C | prod-path | `python scripts/production_equivalent_smoke.py --use-service-path --data-root .audit-sandbox/r26` | service-path smoke passes | | [ ] |
| C | local | `pytest -q` | full regression passes | | [ ] |
| C | docs | `python scripts/check_doc_links.py` | exit 0 if available; else exact blocker + docs index test | | [ ] |

---

## 11. Execute 交接 DoD

- [ ] Parent Contract Gate PASS verified or override documented.
- [ ] §8 RED/GREEN evidence complete.
- [ ] §9 and §10 complete.
- [ ] Production-equivalent smoke passed in isolated data root.
- [ ] Deferred registry and Round3 gate updated.
- [ ] Root self-check migrated/cleaned.
- [ ] `validate-execute-handoff` exit 0.
- [ ] Do not finish-work before Audit.

---

## 12. Execute Skill 冻结清单

| Skill | 本任务 | 绑定 §8 | 触发 | @ 指令 | 已执行 |
|---|---|---|---|---|---|
| test-driven-development | 必做 | 每个 §8 步 | RED/GREEN | 先失败测试再最小实现。 | [ ] |
| testing-guidelines | 必做 | 测试步骤 | 写/改测试 | 业务断言，不 mock 纯逻辑。 | [ ] |
| karpathy-guidelines | 必做 | GREEN 前 | 改代码 | 简洁实现，避免大重构。 | [ ] |
| incremental-implementation | 必做 | 每步 | 每步后 | 单步提交心智，全量回归后继续。 | [ ] |
| source-driven | 必做 | Capability/Route/Service | 读 contracts | 以 contracts 为实现源。 | [ ] |
| systematic-debugging | 条件 | 失败时 | RED/GREEN 非预期 | 记录根因。 | [ ] |
| GitNexus impact/context | 必做 | Phase 0 + 改 symbol 前 | 改代码 symbol 前 | 先影响分析。 | [ ] |
