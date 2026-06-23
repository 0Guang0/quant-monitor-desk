# R3Y-AUD-02 — Source route / DataSourceService 反证

**Result: WARN**

Worktree: `quant-monitor-desk-wt-review-r3-post-r3x-strict-audit` · 基准 `master` @ `61436a51`  
审计模式：只读 · 模板：`agents/security-auditor.md` · 未修改 backend/specs/docs

---

## 目标与反证假设

| 反证假设                                                           | 核查结论                                                                                                    |
| ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------- |
| `DataSourceService.fetch` 未必先经 `SourceRoutePlanner`            | **生产 service 路径：否**（L149–158 必先 `plan`）；**orchestrator `adapter=` 路径：是旁路**                 |
| disabled / validation-only / authorization-required 源可被默认调度 | **默认生产路径 fail-closed**；staged fixture 模式存在受控旁路                                               |
| sync orchestrator `adapter=` 可绕过 route / capability gate        | **是**（测试与 reconcile 路径保留直调）                                                                     |
| registry yaml 与 runtime planner 行为漂移                          | **部分**：akshare 作 primary 的 validation-only domain 在 registry 与 runtime 语义分裂，但 runtime 阻断正确 |

---

## 读取文件（含 call path 追溯）

| 类别                 | 路径                                                                                                                           |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| 派发矩阵             | `.trellis/tasks/06-23-round3-post-r3x-strict-audit/research/parallel-audit-dispatch.md`                                        |
| R3Y §4 R3Y-AUD-02    | `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_post_r3x_strict_adversarial_audit.md`                        |
| Fetch facade         | `backend/app/datasources/service.py`                                                                                           |
| Route planner        | `backend/app/datasources/route_planner.py`                                                                                     |
| Capability gate      | `backend/app/datasources/capability_registry.py`                                                                               |
| Registry 权威        | `specs/datasource_registry/source_registry.yaml`                                                                               |
| Capability 权威      | `specs/datasource_registry/source_capabilities.yaml`                                                                           |
| Platform matrix      | `specs/contracts/platform_source_matrix.yaml`                                                                                  |
| Service 契约         | `specs/contracts/datasource_service_contract.yaml`                                                                             |
| Sync 旁路入口        | `backend/app/sync/orchestrator.py` L127–204                                                                                    |
| Adapter 直调         | `backend/app/sync/runners.py` L42–75、L325–328、L868                                                                           |
| Staged pilot route   | `backend/app/ops/staged_pilot.py` L316–334、L500–520、L700–778                                                                 |
| Layer1 staged bypass | `backend/app/layer1_axes/ingestion.py` L433–474                                                                                |
| 必跑测试             | `tests/test_datasource_service.py`（12）· `tests/test_source_route_planner.py`（6）· `tests/test_source_capabilities.py`（13） |

### Call path（生产 fetch 主链）

```text
DataSourceService.fetch
  → SourceRoutePlanner.plan (L149-155)
  → _augment_plan_with_requested_source (L156)
  → ResourceGuard.check (L160-174) — PAUSE/HARD_STOP 抛 ResourceGuardBlockedError
  → non-READY fail-closed → FetchResult(DISABLED_SOURCE) (L182-193)
  → capability re-assert on override/staged (L203-219)
  → create_adapter / create_test_adapter (L245-251)
  → adapter.fetch → FetchLogWriter.write (L256-257)
```

```text
DataSyncOrchestrator.run_incremental / run_backfill (adapter= 分支)
  → IncrementalJobRunner.run / BackfillShardRunner.run
  → _fetch_with_guard(adapter=...) (runners.py L59-64)
  → adapter.fetch 直接调用 — 无 SourceRoutePlanner、无 capability assert
```

---

## 核查方法（code trace + pytest）

### Runtime 探针（route planner 生产配置）

| data_domain           | route_status            | selected_source | primary skip_reason               |
| --------------------- | ----------------------- | --------------- | --------------------------------- |
| `cn_equity_daily_bar` | READY                   | baostock        | —                                 |
| `macro_supplementary` | VALIDATION_ONLY_BLOCKED | None            | validation_only_cannot_be_primary |
| `cn_index`            | VALIDATION_ONLY_BLOCKED | None            | validation_only_cannot_be_primary |
| `sector_board`        | VALIDATION_ONLY_BLOCKED | None            | validation_only_cannot_be_primary |
| `security_list`       | DISABLED_SOURCE         | None            | source_disabled_by_default        |

### Pytest 执行记录

```bash
cd quant-monitor-desk-wt-review-r3-post-r3x-strict-audit
uv run pytest tests/test_datasource_service.py \
             tests/test_source_route_planner.py \
             tests/test_source_capabilities.py -q
```

| 指标     | 结果              |
| -------- | ----------------- |
| 收集用例 | 31（12 + 6 + 13） |
| 通过     | 31                |
| 失败     | 0                 |
| 跳过     | 0                 |

---

## Security Audit Report

### Summary

- Critical: 0
- High: 1
- Medium: 2
- Low: 2

### Findings

#### [HIGH] Sync orchestrator `adapter=` 参数可完全旁路 SourceRoutePlanner 与 capability gate

- **Location:** `backend/app/sync/runners.py:59-64`, `backend/app/sync/orchestrator.py:127-164`
- **Description:** `DataSyncOrchestrator.run_incremental` / `run_backfill` 接受 `adapter: BaseDataAdapter | None`。当调用方传入 `adapter` 且未传 `datasource_service` 时，`_fetch_with_guard` 直接执行 `adapter.fetch(req, con=con, job_id=job_id)`，不经过 `DataSourceService`、不生成 `ROUTE_PLAN`、不执行 `SourceCapabilityRegistry.assert_source_domain_operation`。
- **Impact:** 任何未来或误配置的调用方可对 disabled / validation-only / 未授权源发起 fetch，并进入 validate/write pipeline（若后续阶段未二次拦截）。
- **Proof of concept:** 测试路径已存在：`tests/test_sync_orchestrator.py` 多处 `orch.run_incremental(spec, adapter=adapter, ...)`；`tests/test_vendor_fetch_e2e.py:92` 同理。契约 `datasource_service_contract.yaml` 将 `backend.app.sync.runners` 列为 `forbidden_direct_callers`，但 runtime **未强制** 禁止 `adapter=` 分支。
- **Recommendation:** 生产入口仅接受 `datasource_service`；`adapter=` 在 orchestrator 层对非测试环境 `raise` 或 deprecate。若 reconcile 必须保留 adapter，应包裹为 narrow `FetchCallable` 并在文档中标注为 exception path。

#### [MEDIUM] `staged_fixture_mode` 可在 blocked route 下仍执行 fetch（受控旁路）

- **Location:** `backend/app/datasources/service.py:177-197`, `backend/app/layer1_axes/ingestion.py:460-474`
- **Description:** 当 `staged_fixture_mode=True`（或 `fetch_port` 注入且无 `file_registry_factory`）且 `route_status ∈ {VALIDATION_ONLY_BLOCKED, DISABLED_SOURCE}` 时，`staged_route_override` 为真，fetch 使用 `req.source_id` 继续。Layer1 `_prepare_staged_route_and_request` 对 allowlist indicator 有平行 `staged_bypass` 逻辑。
- **Impact:** 若生产装配误设 `staged_fixture_mode=True`，validation-only / disabled 路由门禁可被绕过；属授权边界弱化。
- **Proof of concept:** `build_staged_fixture_service()` / Layer1 `ENV-E1-DGS10` macro 路径依赖此旁路完成 staged micro-fetch；`macro_supplementary` organic route 为 `VALIDATION_ONLY_BLOCKED`，但 fixture 模式可 fetch。
- **Recommendation:** 保持现状仅限 ops 显式构造；增加启动时断言：生产 `DataSourceService` 不得同时 `staged_fixture_mode=True` 且无 sandbox 路径前缀；审计日志标记 `STAGED_ROUTE_OVERRIDE`。

#### [MEDIUM] `run_reconcile` 永久旁路 DataSourceService route gate

- **Location:** `backend/app/sync/orchestrator.py:206-207` → `backend/app/sync/runners.py:857-868`
- **Description:** `ReconcileJobRunner.run` 在 `RECONCILING` 后直接 `adapter.fetch(req, con=con, job_id=job_id)`，无 route plan、无 capability registry、无 `DISABLED_SOURCE` 统一语义。
- **Impact:** 冲突和解路径若传入未门禁 adapter，可拉取 registry 禁止的源；风险限于已存在的 conflict 工作流与调用方传入的 adapter 实例。
- **Recommendation:** Reconcile fetch 改经 `DataSourceService.fetch` 或至少 `assert_capability_declared`；记录 `ROUTE_PLAN` 事件以与主链对齐。

#### [LOW] `test_source_route_planner` 未断言 `VALIDATION_ONLY_BLOCKED` / `USER_AUTH_REQUIRED` 精确状态

- **Location:** `tests/test_source_route_planner.py:88-101`
- **Description:** `test_userAuthRequired_routeStatusWhenAuthorizationMissing` 对 `etf_daily_bar` 接受 `DISABLED_SOURCE`（domain_disabled 优先于 user_auth），未覆盖 `USER_AUTH_REQUIRED` 纯平台授权场景；必跑三文件均无 `macro_supplementary` → `VALIDATION_ONLY_BLOCKED` 断言（该断言在 `test_r3x_residual_open_items_closure.py`，不在本 issue 必跑集）。
- **Impact:** 本 issue 必跑集对 validation-only primary 阻断的回归深度不足；与 R3Y-AUD-07 WARN 一致。
- **Recommendation:** 在 `test_source_route_planner.py` 增加 `macro_supplementary` / `cn_index` 的 `VALIDATION_ONLY_BLOCKED` 用例。

#### [LOW] Registry 将 validation-only 源标为 primary（文档/权威漂移）

- **Location:** `specs/datasource_registry/source_registry.yaml:144-188`（`macro_supplementary` / `cn_index` / `sector_board` primary=akshare，`validation_only: true`）
- **Description:** YAML 角色与 `validation_only` 标志矛盾；runtime planner 以 `validation_only_cannot_be_primary` fail-closed，行为正确但权威源易误导运维/Agent。
- **Impact:** 配置误读可能导致「registry 说能作主源、runtime 拒绝」的运维困惑；非直接 exploit。
- **Recommendation:** 将 staged domain 的 primary 改为非 validation-only 占位或显式 `staged_primary_requires_validation_role` 注释字段；保持 planner 逻辑不变。

### Positive Observations

- `DataSourceService.fetch` 生产链严格执行 **route → guard → capability（override 时）→ adapter → fetch_log**（`service.py:139-258`）。
- `SourceRoutePlanner` 对 disabled registry（`is_enabled`）、platform matrix（`user_authorization_required` / `missing_env`）、`validation_only` primary、`domain_enabled_by_default` 均 fail-closed（`route_planner.py:51-201`）。
- `SourceCapabilityRegistry.assert_source_domain_operation` 拒绝 `enabled_by_default: false` 与 `proposed_disabled_source`（`capability_registry.py:66-93`）；`qmt_xqshare` / `tdx_pytdx` 在 capabilities yaml 已标记。
- `staged_pilot` 使用 `APPROVED_PILOT_REQUESTS` + `DISABLED_PILOT_SOURCE_IDS` + `assert_pilot_ready_before_fetch` + `explicit_source_route_status == READY` 门禁；`_ExplicitSourceRoutePlanner` 仅在 candidate `enabled` 时强制源（`staged_pilot.py:507-511`）。
- 契约测试：`test_forbiddenDirectCallers_includesSyncRunners`、`test_createAdapterImports_onlyUnderTests` 限制 `create_adapter` 扩散。
- 必跑 31 项测试全部通过。

### Recommendations（主动加固）

1. Orchestrator 生产路径硬编码 `datasource_service` 必填；`adapter=` 仅限 pytest fixture 并加 runtime guard。
2. 为 `staged_route_override` 增加结构化 audit flag（fetch_log / job_event payload）。
3. 扩展必跑集覆盖 `VALIDATION_ONLY_BLOCKED` 与 `USER_AUTH_REQUIRED` 分状态断言。
4. Reconcile 路径纳入 route/capability 最小门禁。

---

## 反证结论（修复是否进入 runtime）

| 声称修复                                    | Runtime 验证                                                               | 证据                                                             |
| ------------------------------------------- | -------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| fetch 必先 route（PROMPT_12 / R3X routing） | **已进入** — `DataSourceService.fetch` 主链                                | `service.py:149-158`；`test_serviceBuildsRouteBeforeFetch`       |
| disabled source fail-closed                 | **已进入** — `DISABLED_SOURCE` + 零行 fetch_log                            | `test_serviceDisabledRoute_writesFetchLog`；`security_list` 探针 |
| validation-only 不可作 primary              | **已进入** — `VALIDATION_ONLY_BLOCKED`                                     | runtime 探针；`test_r3x_residual_open_items_closure`（非必跑集） |
| authorization-required fail-closed          | **部分** — service 层 mock 测试覆盖；planner 对 qmt/yahoo/tdx 平台矩阵阻断 | `test_serviceUserAuthRequiredRoute_*`；platform matrix           |
| orchestrator 统一经 DataSourceService       | **未完全闭合** — `adapter=` 旁路仍存在                                     | `runners.py:59-64`；大量 sync 测试仍用 adapter                   |
| staged pilot 不绕过 route                   | **受控闭合** — 授权 + explicit READY + disabled 列表                       | `staged_pilot.py:702-713`                                        |

**相对 v0-monolithic（`review-evidence/v0-monolithic/R3Y-AUD-02-source-route.md` PASS）：** 深读后降级为 **WARN** — 主 service 链正确，但 sync `adapter=` / reconcile / staged_fixture 旁路未在必跑测试集中被否定，存在 latent bypass。

---

## 阻塞项 / 建议

| 类型                        | 项                                                                          |
| --------------------------- | --------------------------------------------------------------------------- |
| **不阻塞 pilot v2（受控）** | 主 fetch facade 与 staged_pilot 授权链可用                                  |
| **WARN 控制项**             | 合并前确认无生产 CLI 使用 `adapter=`；document reconcile exception          |
| **建议 follow-up issue**    | Orchestrator adapter 旁路 runtime guard；必跑集补 `VALIDATION_ONLY_BLOCKED` |

---

## 三条关键 Finding（协调者摘要）

1. **[HIGH]** `run_incremental`/`run_backfill` 的 `adapter=` 分支在 `runners._fetch_with_guard` 直调 `adapter.fetch`，完全跳过 `SourceRoutePlanner` 与 capability gate — 契约禁止但 runtime 未封死。
2. **[MEDIUM]** `staged_fixture_mode` + `staged_route_override` 允许在 `VALIDATION_ONLY_BLOCKED`/`DISABLED_SOURCE` 下继续 fetch（Layer1 macro / staged pilot 有意依赖）；生产误配该 flag 会削弱 fail-closed。
3. **[PASS 核]** 默认生产 `DataSourceService` 路径对 disabled、validation-only-primary、domain-disabled、resource-guard 均 fail-closed；必跑 pytest **31/31 绿** — 主链修复已进入 runtime，旁路为残留风险而非主路径失效。
