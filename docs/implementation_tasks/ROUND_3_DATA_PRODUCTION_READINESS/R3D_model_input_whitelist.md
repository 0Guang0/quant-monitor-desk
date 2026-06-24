# R3D_model_input_whitelist — Five-Layer Model Input Whitelist

> Roadmap link: `PROJECT_IMPLEMENTATION_ROADMAP.md` → Round 3D.2.  
> Priority: P0.  
> Suggested branch: `chore/round3-model-input-whitelist`.  
> Type: docs/spec/config planning task.  
> Production posture: no live fetch, no clean write, no production readiness claim.  
> Batch hardening: must read `BATCH_01_MODEL_SOURCE_READINESS/README.md`, `BATCH_01_TASK_CARD_MANIFEST.md`, `BATCH_01_ADVERSARIAL_AUDIT.md`, and `BATCH_01_HARDENING_RULES.md` before execution.

---

## 1. 任务目标

建立五层模型第一批真实数据输入白名单，明确哪些指标、标的、公告/财报/宏观序列可以进入后续 raw/staging/sandbox pilot，哪些只能 validation-only，哪些继续 staged/fixture/deferred。

---

## 2. 预期结果

完成后，执行者和业务方可以清楚回答：

- Layer1 需要哪些宏观/美股/FRED 序列作为第一批输入。
- Layer2 需要哪些跨资产 ETF、指数、期货、波动率或流动性观察项。
- Layer3 哪些产业链 anchor 已有可信 source，哪些只是 staged fixture。
- Layer4 哪些市场结构输入可以进入真实数据试跑。
- Layer5 哪些 instrument / bar / event / financial / valuation 证据优先接入。
- 系统当前不是全市场全量接入，而是 model-driven / whitelist-driven 接入。

最终输出应是一组可被后续 FRED pilot、TDX probe、staged pilot v3、data health v2 读取的白名单文件和 readiness matrix。

---

## 3. 输入文件

执行前必须读取：

- `PROJECT_IMPLEMENTATION_ROADMAP.md`
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md`（历史追踪；只用于核对，不作为未来执行入口）
- `MIGRATION_MAP.md`
- `docs/AUDIT_DEFERRED_REGISTRY.md`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`
- `docs/RESOLVED_ISSUES_REGISTRY.md`
- `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`
- `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`
- `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`
- `docs/quality/staged_acceptance_policy.md`
- `docs/quality/production_live_pilot_policy.md`
- `specs/contracts/runtime_versions.md`
- `specs/datasource_registry/source_registry.yaml`
- `specs/datasource_registry/source_capabilities.yaml`
- `specs/contracts/source_route_contract.yaml`
- `specs/contracts/source_capability_contract.yaml`
- `specs/contracts/datasource_service_contract.yaml`
- `specs/contracts/resource_limits.yaml`
- `specs/layer1_axes/restructured_axes_v1_1/**`
- `specs/contracts/layer2_sensor_contract.yaml`
- `specs/contracts/layer3_loader_contract.yaml`
- `specs/contracts/layer4_market_contract.yaml`
- `specs/contracts/layer5_evidence_contract.yaml`
- `tests/fixtures/layer2_cross_asset_registry_fixture.yaml`
- `tests/fixtures/layer3_staged_bundle/bundle_manifest.yaml`
- `tests/fixtures/layer4_staged_market/manifest.yaml`

Useful historical cards:

- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/017_implement_layer1_axis_loader.md`
- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018_implement_layer1_interpretation_snapshot.md`
- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/019_implement_layer2_cross_asset_sensor.md`
- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/020_implement_layer3_industry_chain_loader.md`
- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/021_implement_layer3_snapshot_builder.md`
- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/022_implement_layer4_market_structure.md`
- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/023_implement_layer5_evidence_chain.md`

---

## 4. 相关代码 / 输出文件

This task should primarily create docs/spec artifacts. Suggested outputs:

- `specs/model_inputs/layer1_source_whitelist.yaml`
- `specs/model_inputs/layer2_source_whitelist.yaml`
- `specs/model_inputs/layer3_anchor_source_plan.yaml`
- `specs/model_inputs/layer4_market_source_plan.yaml`
- `specs/model_inputs/layer5_instrument_source_plan.yaml`
- `specs/model_inputs/README.md`
- `docs/quality/model_input_readiness_matrix.md`
- tests under `tests/` if the project already has a docs/spec validation pattern suitable for whitelist contract checks

Implementation code should not be required unless the existing validation script must be extended to load these new specs. If code is touched, keep it limited to validation/doc-index tooling.

---

## 5. 现有模式 / 参考

Follow these existing patterns:

- Source status is controlled through `source_registry.yaml` and `source_capabilities.yaml`.
- Source routing must not bypass `SourceRoutePlanner` / `DataSourceService`.
- Existing staged-only model inputs are visible in Layer2/Layer3/Layer4 fixtures.
- FRED appears in Layer1 specs as an intended primary/validation macro source, but no production `fred` source is currently registered.
- `akshare` remains validation-only and must not become Primary through this whitelist.
- `tdx_pytdx` remains disabled by default and validation-only candidate unless later explicitly authorized.

---

## 6. 技术约束

- Use YAML for machine-readable whitelist files.
- Use Markdown for human readiness summary.
- Every whitelist row must include enough metadata for later tasks to choose fetch scope without guessing.
- Do not introduce a new schema format if YAML is sufficient.
- Do not add external dependencies.
- Do not alter runtime adapters, route planner, validators, database schema, or production config in this task.

Required row fields, unless a row is explicitly marked out of scope:

```yaml
input_id: string
layer: layer1|layer2|layer3|layer4|layer5
business_purpose: string
data_domain: string
source_id: string
operation: string
role: primary_candidate|validation_only|fallback_candidate|staged_fixture|deferred
readiness: production_candidate|sandbox_candidate|staged_only|fixture_only|deferred|forbidden
symbol_or_series: string | list
window_cap: string
row_cap: integer | null
requires_user_authorization: boolean
allowed_next_gate: none|raw_staging_pilot|sandbox_clean_rehearsal|limited_production_review
forbidden_claims: list
closure_test: string
notes: string
```

---

## 7. 资源约束

- This is a docs/spec task: no network fetch, no DB write, no source probe.
- No full-market inventory scan.
- No full-history scan.
- No generated giant whitelist from external market universes.
- Keep P0/P1 lists intentionally small and traceable to existing model specs.

Recommended initial caps for future tasks, recorded but not executed here:

- FRED P0: 3–5 series.
- baostock P0: 3–20 model-input symbols.
- cninfo P0: 2–20 model-input issuers / symbols.
- TDX P0: 1 equity + 1 index + capped security-list probe.
- akshare: validation-only samples only.

---

## 8. 边界约束

Must not:

- Claim the whitelist is a production enablement decision.
- Add source credentials, host, port, token, or live endpoint secrets.
- Promote `akshare` to Primary.
- Promote `tdx_pytdx` to production primary.
- Promote Yahoo/QMT/xqshare/FRED to production-live.
- Treat `macro_supplementary` as a FRED primary substitute.
- Require all markets/all instruments/all history/all minute bars.
- Modify production database or migrations.
- Modify model calculations.

Must explicitly mark:

- Layer2/3/4 entries that are still `staged_fixture` or `fixture_only`.
- FRED rows that are only `sandbox_candidate` until FRED-only authorized pilot closes.
- TDX rows that are only `validation_only` until manual probe closes.
- Any source requiring user authorization.

---

## 9. 实现步骤

Use `/to-issues` before execution. Suggested vertical slices:

1. **Slice WL-01 — Layer1 macro whitelist**  
   Extract P0/P1 macro/FRED/market series from Layer1 specs, classify `DGS10`, `T10Y3M`, `VIXCLS`, `SP500`, `DFII10`, and mark all others deferred or P2.

2. **Slice WL-02 — Layer2 cross-asset whitelist**  
   Identify staged Layer2 inputs such as VIX/HYG/Copper/ETF/futures-like proxies; classify as fixture-only, sandbox-candidate, or deferred.

3. **Slice WL-03 — Layer3 anchor/source plan**  
   Map industry-chain anchors and L5 mapping needs to available or missing source keys; mark staged-only vs needs-source.

4. **Slice WL-04 — Layer4 market source plan**  
   Define CN_A calendar/breadth first-source readiness and mark US/HK/FUT/options as deferred unless already supported.

5. **Slice WL-05 — Layer5 instrument/evidence source plan**  
   Define first instrument bar/event/metadata evidence candidates: baostock daily bars, cninfo metadata, FRED macro daily, TDX validation-only candidate.

6. **Slice WL-06 — Readiness matrix and tests**  
   Create `model_input_readiness_matrix.md` and a lightweight validation check, if existing test conventions support it.

---

## 10. 测试要求

At minimum:

- Add a docs/spec validation test or static assertion if the project has a suitable pattern.
- Validate every YAML row has required fields.
- Validate forbidden role transitions:
  - `akshare` cannot be `primary_candidate`.
  - `tdx_pytdx` cannot be `production_candidate`.
  - `fred` cannot be `production_candidate` before FRED pilot closure.
  - `macro_supplementary` cannot close FRED primary readiness.
- Validate each whitelist file has at least one P0 or explicit empty-with-reason section.

Every new/changed test must include a docstring or nearby comment explaining:

- coverage scope,
- test object,
- purpose/goal.

Do not add tests that only assert files exist. Tests must assert semantic constraints.

---

## 11. 验收命令

Docs/spec task baseline:

```bash
uv sync --locked
uv run pytest tests/test_round3_verification_command_matrix.py -q
uv run pytest tests/test_unresolved_item_task_coverage.py -q
uv run python scripts/check_docs_specs_indexed.py
```

If new whitelist validation tests are added:

```bash
uv run pytest tests/test_model_input_whitelist.py -q
```

Merge-gate recommendation after changes:

```bash
uv run pytest -q
uv run ruff check .
```

If the local environment cannot run `uv`, record the exact command and error; do not mark tests as passed.

---

## 12. 完成标准

- All five proposed whitelist files are either created or explicitly reduced with rationale.
- `model_input_readiness_matrix.md` explains what can enter raw/staging pilot, what remains fixture-only, and what is deferred.
- FRED, TDX, AkShare, baostock, and cninfo all have explicit allowed/prohibited roles.
- No full-market or full-history default path exists in the whitelist.
- No source is promoted beyond current authorization state.
- Any registry rows affected are updated or explicitly left unchanged with reason.
- Tests / checks listed above pass or have documented environment failure.

---

## 13. Red Flags

Stop and repair if any occur:

- A row implies full-market or full-history ingestion by default.
- `akshare` becomes Primary or production-candidate.
- `tdx_pytdx` becomes production primary.
- FRED is marked production-ready without FRED-only sandbox pilot evidence.
- Whitelist rows omit business purpose, source role, readiness, or next gate.
- The task modifies runtime fetch code or database schema.
- Tests only assert file existence.
- The output allows an executor to skip source authorization.

---

## 14. 输出要求

Final report must include:

1. Created/updated whitelist files.
2. Created/updated docs.
3. Tests run and exact results.
4. Sources explicitly still deferred.
5. Whether any registry rows changed.
6. Remaining ambiguity, if any, for user decision.
7. Confirmation that no production DB, live fetch, or clean write occurred.

---

## 15. 审计修复新增强制项

- **版本与锁文件:** Read `specs/contracts/runtime_versions.md`; do not alter lockfiles unless a test dependency is truly required and approved.
- **阶段化验收:** This is docs/spec stage; do not blindly require frontend/build tests unless touched.
- **回滚与恢复:** Docs/spec changes are rollback-by-revert; no DB rollback needed.
- **幂等与重试:** Future fetch tasks must use idempotent source_fetch_id/content_hash conventions; this card only records requirements.
- **安全与隐私:** Do not store credentials or private endpoint details in whitelist files.
- **lineage / as-of:** Every future-eligible data input must specify whether `as_of_timestamp`, `source_fetch_id`, `source_content_hash`, and `rule_version` are required downstream.
- **测试质量:** Semantic validation tests required if validation tests are added.
