# R3E_fred_authorized_sandbox_pilot — FRED-only Authorized Sandbox Pilot

> Roadmap link: `PROJECT_IMPLEMENTATION_ROADMAP.md` → Round 3E.1.  
> Priority: P0.  
> Suggested branch: `feature/round3-fred-authorized-sandbox-pilot`.  
> Type: backend + specs + tests + evidence task.  
> Production posture: authorized raw/staging/sandbox only; no production clean write; no production-live readiness claim.  
> Batch hardening: must read `BATCH_01_MODEL_SOURCE_READINESS/README.md`, `BATCH_01_TASK_CARD_MANIFEST.md`, `BATCH_01_ADVERSARIAL_AUDIT.md`, and `BATCH_01_HARDENING_RULES.md` before execution.

---

## 1. 任务目标

为五层模型中明确依赖 FRED 的宏观/美股核心序列建立一个 FRED-only、用户授权、受资源限制、raw/staging/sandbox-only 的真实数据试跑路径。

本任务要证明：FRED 可以作为未来宏观主干数据源候选被安全接入，但还不能被宣传为 production-live，也不能写 production clean table。

---

## 2. 预期结果

完成后系统应具备：

- `fred` source_id 在 registry/capability 中被明确登记为 disabled-by-default 或 sandbox-candidate。
- 一个受控 `FredFetchPort` 或等价 fetch boundary，能在授权环境下获取小规模 FRED series。
- 初始 P0 series 只限白名单，例如 `DGS10`, `T10Y3M`, `VIXCLS`, `SP500`, `DFII10`。
- raw/staging evidence 包含 `series_id`, `observation_date`, `value`, `source_fetch_id`, `content_hash`, `as_of_timestamp`, `retrieved_at`, `quality_flags`。
- FRED data health 能检查 missing/stale/non-numeric/date-order/update-time/vintage 相关风险。
- `B2.5-O-05` 是否关闭或继续 re-defer 有明确证据。
- 生产库 no-mutation proof 或明确声明未触碰 production DB path。

---

## 3. 输入文件

执行前必须读取：

- `PROJECT_IMPLEMENTATION_ROADMAP.md`
- `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/R3D_model_input_whitelist.md`
- `docs/AUDIT_DEFERRED_REGISTRY.md` row `B2.5-O-05`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md` row `B2.5-O-05`
- `docs/quality/production_live_pilot_policy.md`
- `docs/quality/staged_acceptance_policy.md`
- `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`
- `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`
- `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`
- `specs/contracts/runtime_versions.md`
- `specs/datasource_registry/source_registry.yaml`
- `specs/datasource_registry/source_capabilities.yaml`
- `specs/contracts/source_capability_contract.yaml`
- `specs/contracts/source_route_contract.yaml`
- `specs/contracts/datasource_service_contract.yaml`
- `specs/contracts/data_adapter_contract.md`
- `specs/contracts/data_quality_rules.yaml`
- `specs/contracts/resource_limits.yaml`
- `specs/layer1_axes/restructured_axes_v1_1/environment_axis/environment_axis_indicator_spec.yaml`
- `specs/layer1_axes/restructured_axes_v1_1/risk_appetite_axis/risk_appetite_axis_indicator_spec.yaml`
- `specs/layer1_axes/restructured_axes_v1_1/credit_stress_axis/credit_stress_axis_indicator_spec.yaml`
- `backend/app/datasources/route_planner.py`
- `backend/app/datasources/capability_registry.py`
- `backend/app/datasources/service.py`
- `backend/app/ops/staged_pilot.py`
- `backend/app/ops/staged_pilot_fetch_ports.py`
- `backend/app/ops/live_pilot_fetch_ports.py`
- `backend/app/ops/data_health.py`

Related history:

- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018B_production_live_pilot_gate.md`
- `docs/implementation_tasks/ROUND_3_PARALLEL_PROMPTS/PROMPT_04_debt_r3b275_fred_staged_semantics.md`
- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_readonly_data_health_v1.md`

---

## 4. 相关代码文件

Expected or candidate paths:

- `specs/datasource_registry/source_registry.yaml`
- `specs/datasource_registry/source_capabilities.yaml`
- `backend/app/datasources/adapters/fred.py` or a narrower fetch-port-only path if adapter abstraction is not yet needed
- `backend/app/ops/fred_sandbox_pilot.py` or an extension of `staged_pilot.py` if ponytail review shows extension is simpler
- `backend/app/ops/fred_fetch_ports.py` or equivalent port inside existing ops fetch ports
- `backend/app/ops/data_health.py`
- `tests/test_fred_source_registry.py`
- `tests/test_fred_sandbox_pilot.py`
- `tests/test_fred_staged_semantics.py`
- `tests/test_ops_data_health.py` only if data health extension naturally belongs there
- task-local evidence under `.trellis/tasks/<task-slug>/execute-evidence/`

Do not modify frontend, production DB files, or broad Layer1 computation unless this task is formally expanded and approved.

---

## 5. 现有模式 / 参考

Use existing project patterns:

- Source registry/capability gates must control source availability.
- `DataSourceService` and `SourceRoutePlanner` are the sanctioned fetch path.
- Production/live pilot policy requires explicit authorization, dry-run/route preview, raw-only first, bounded windows, and no production DB mutation.
- `macro_supplementary` is not a FRED substitute; it cannot close FRED primary readiness.
- staged pilot v2 used bounded calls, caps, raw/staging manifest, validation report, and no-mutation proof; reuse those patterns instead of inventing a broad ingestion framework.

---

## 6. 技术约束

- FRED integration must be optional and disabled unless explicitly authorized by environment/config/test fixture.
- No new heavy dependency without user approval.
- Prefer standard library HTTP or existing project HTTP pattern if available.
- If an official FRED API key is required, the task must support a skip/defer state when absent. Do not commit keys.
- The pilot must support `skip_live_fetch=True` / dry-run behavior.
- Live network execution must be opt-in and must record authorization evidence.
- `fred` rows must not be marked production-ready in registry/capability.
- The pilot must not write production clean tables.

Suggested result status enum:

```text
FRED_PILOT_PASS_RAW_ONLY
FRED_PILOT_PASS_SANDBOX_STAGING
FRED_PILOT_FAIL_AUTH
FRED_PILOT_FAIL_NETWORK
FRED_PILOT_FAIL_SCHEMA
FRED_PILOT_FAIL_VALIDATION
FRED_PILOT_REDEFERRED
```

---

## 7. 资源约束

Initial pilot caps:

- Series: max 5.
- Rows per series: max 100 by default, or a narrow date window such as 1–3 years if monthly series require it.
- Network calls: max 10 unless user approves more.
- No full FRED catalog scan.
- No auto-discovery of thousands of series.
- No full historical backfill.
- No scheduled polling.

ResourceGuard behavior:

- If caps are exceeded, stop and report `RESOURCE_GUARD_PAUSED` or task-local equivalent.
- If source response is too large, store a capped raw sample and record truncation.

---

## 8. 边界约束

Must not:

- Enable production-live FRED.
- Write production clean DB.
- Modify existing production data tables.
- Treat FRED raw pilot as production monitoring.
- Use AkShare or `macro_supplementary` to close FRED primary source readiness.
- Backfill all FRED history.
- Fetch all FRED series in Layer1 specs.
- Drive official dashboard/alerts from FRED pilot data.
- Hide missing auth/network failures as PASS.

Must do:

- Keep all outputs in raw/staging/sandbox evidence paths.
- Record source_fetch_id and content_hash for every successful payload.
- Record no-mutation proof for production DB or prove production DB path was not opened.
- Preserve `B2.5-O-05` as DEFERRED if no FRED-only evidence exists.

---

## 9. 实现步骤

Use `/to-issues` and `/tdd`; do not implement this as one large horizontal change. Suggested vertical slices:

1. **Slice FRED-01 — Registry and capability guard**  
   RED: test `fred` cannot route as production-live and is capped/disabled by default.  
   GREEN: add `fred` registry/capability rows with sandbox/authorization constraints.

2. **Slice FRED-02 — Route preview only**  
   RED: route preview for P0 FRED series returns sandbox/raw-only plan and rejects unlisted series.  
   GREEN: add route planning support without live fetch.

3. **Slice FRED-03 — Mocked fetch port**  
   RED: mocked FRED payload with valid rows creates raw/staging evidence with required fields.  
   GREEN: implement port/parser/manifest logic behind dry-run/live boundary.

4. **Slice FRED-04 — Failure taxonomy**  
   RED: missing auth, network failure, non-numeric value, stale date, bad series_id produce explicit failure statuses.  
   GREEN: implement taxonomy and evidence report.

5. **Slice FRED-05 — Read-only data health checks**  
   RED: health check catches missing rows, stale observations, malformed values, and missing fetch/hash.  
   GREEN: extend data health profile narrowly.

6. **Slice FRED-06 — Registry closeout decision**  
   RED: `B2.5-O-05` cannot close without FRED-only evidence.  
   GREEN: update docs/registry only if actual gates pass, otherwise re-defer with clearer closure test.

---

## 10. 测试要求

Minimum tests:

- Registry/capability test: FRED is not production-live and requires explicit authorization.
- Route test: only whitelisted P0 series are accepted by this pilot.
- Dry-run test: route preview produces raw/staging plan and no DB mutation.
- Mock fetch test: valid FRED response produces manifest with series_id, date, value, fetch id, hash, as_of.
- Failure tests: auth/network/schema/validation failures are explicit statuses.
- Data health tests: stale/missing/malformed FRED data fails or warns correctly.
- Registry semantics test: `macro_supplementary` does not close `B2.5-O-05`.

Every new/changed test must include a docstring or nearby comment explaining:

- coverage scope,
- test object,
- purpose/goal.

No test should only assert that a function was called or that a file exists.

---

## 11. 验收命令

Targeted commands:

```bash
uv sync --locked
uv run pytest tests/test_source_capabilities.py tests/test_source_route_planner.py -q
uv run pytest tests/test_fred_source_registry.py tests/test_fred_sandbox_pilot.py tests/test_fred_staged_semantics.py -q
uv run pytest tests/test_ops_data_health.py -q
uv run ruff check backend/app/datasources backend/app/ops tests/test_fred_source_registry.py tests/test_fred_sandbox_pilot.py tests/test_fred_staged_semantics.py tests/test_ops_data_health.py
```

Merge-gate recommendation:

```bash
uv run pytest -q
uv run ruff check .
uv run python -m compileall backend scripts tests
```

If optional live FRED authorization is absent, live tests must be skipped with explicit reason and mocked tests must still pass.

---

## 12. 完成标准

- `fred` source capability exists but is not production-live.
- P0 FRED series are limited and documented.
- Dry-run/route preview works without network.
- Mocked fetch path creates raw/staging evidence with content hash and fetch id.
- Authorized live run, if performed, respects caps and writes only raw/staging/sandbox evidence.
- Data health v2 can evaluate FRED pilot evidence or a clearly documented interim profile exists.
- `B2.5-O-05` is either closed with FRED-only evidence or re-deferred with stronger closure test.
- No production clean write occurs.
- Tests pass or environment failure is recorded exactly.

---

## 13. Red Flags

Stop and repair if any occur:

- FRED is enabled by default.
- FRED is marked production-ready.
- The task writes clean production tables.
- The task fetches all FRED series or full history by default.
- Missing API key is treated as success.
- Network failure silently falls back to AkShare or macro_supplementary.
- `B2.5-O-05` closes without FRED-only evidence.
- Tests are only mocked call assertions and do not verify evidence content.

---

## 14. 输出要求

Final report must include:

1. Source registry/capability changes.
2. Fetch/route/data-health changes.
3. Evidence artifact paths and status.
4. Whether live authorization was present.
5. Whether live fetch was actually run.
6. Production DB mutation proof or no-production-DB-open statement.
7. `B2.5-O-05` closure or re-deferral decision.
8. Test commands/results.
9. Remaining risks.

---

## 15. 审计修复新增强制项

- **版本与锁文件:** Do not add a FRED library without approval; if added, update lockfile intentionally and explain why stdlib/current HTTP pattern is insufficient.
- **阶段化验收:** Dry-run/mocked tests are required even when live authorization is absent.
- **回滚与恢复:** Raw/staging sandbox artifacts can be deleted; no production DB rollback should be needed.
- **幂等与重试:** Use deterministic source_fetch_id or include request fingerprint/date window; repeated runs should not create ambiguous duplicate evidence.
- **安全与隐私:** No API keys in repo; no logged secrets; no broad endpoint discovery.
- **lineage / as-of:** Every evidence row must carry as_of/retrieved_at/source hash/fetch id sufficient for Layer5 chain later.
- **测试质量:** Tests must verify business safety: FRED remains sandbox-only and cannot be substituted by macro_supplementary.
