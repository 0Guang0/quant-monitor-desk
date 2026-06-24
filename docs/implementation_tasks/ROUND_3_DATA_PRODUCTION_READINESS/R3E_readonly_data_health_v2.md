# R3E_readonly_data_health_v2 — Source Readiness Data Health v2

> Roadmap link: `PROJECT_IMPLEMENTATION_ROADMAP.md` → Round 3E.4.  
> Priority: P1.  
> Suggested branch: `feature/round3-readonly-data-health-v2`.  
> Type: backend read-only checks + evidence + tests.  
> Production posture: read-only only; no fetch; no source_health_snapshot clean table; no production clean write.  
> Batch hardening: must read `BATCH_01_MODEL_SOURCE_READINESS/README.md`, `BATCH_01_TASK_CARD_MANIFEST.md`, `BATCH_01_ADVERSARIAL_AUDIT.md`, and `BATCH_01_HARDENING_RULES.md` before execution.

---

## 1. 任务目标

在 `R3Y_readonly_data_health_v1` 的基础上，扩展 read-only data health，让它能检查第一批数据生产准备任务产生的证据：model input whitelist、FRED sandbox pilot、TDX manual probe、real-data staged pilot v3。

本任务只做检查和报告，不执行真实 fetch，不写 clean table，不创建 `source_health_snapshot`。

---

## 2. 预期结果

完成后系统应能回答：

- 某个 staged/raw/sandbox evidence bundle 是否属于 model input whitelist。
- FRED evidence 是否具备 series_id/date/value/fetch/hash/as_of/retrieved_at。
- TDX probe evidence 是否授权、受限、validation-only、未触碰生产库。
- baostock/cninfo/akshare v3 evidence 是否满足 caps、role、schema、conflict summary。
- 证据是否足够进入 later sandbox clean-write rehearsal。
- 哪些 source/domain 必须继续 re-defer。

---

## 3. 输入文件

执行前必须读取：

- `PROJECT_IMPLEMENTATION_ROADMAP.md`
- `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/R3D_model_input_whitelist.md`
- `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/R3E_fred_authorized_sandbox_pilot.md`
- `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/R3E_tdx_manual_probe_addendum.md`
- `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/R3E_real_data_staged_pilot_v3.md`
- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_readonly_data_health_v1.md`
- `docs/implementation_tasks/ROUND_3_PARALLEL_PROMPTS/PROMPT_20_feature_round3_readonly_data_health_v1.md`
- `docs/AUDIT_DEFERRED_REGISTRY.md`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`
- `docs/RESOLVED_ISSUES_REGISTRY.md`
- `docs/quality/staged_acceptance_policy.md`
- `docs/quality/production_live_pilot_policy.md`
- `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`
- `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`
- `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`
- `specs/contracts/runtime_versions.md`
- `specs/contracts/data_quality_rules.yaml`
- `specs/contracts/resource_limits.yaml`
- `specs/contracts/source_conflict_rules.yaml`
- `specs/datasource_registry/source_registry.yaml`
- `specs/datasource_registry/source_capabilities.yaml`
- `backend/app/ops/data_health.py`
- `backend/app/ops/staged_pilot.py`
- `tests/test_ops_data_health.py`
- `tests/test_staged_pilot.py`

If model-input whitelist files do not exist yet, this task must provide a BLOCKED/WARN result rather than guessing scope.

---

## 4. 相关代码文件

Candidate touched paths:

- `backend/app/ops/data_health.py`
- `backend/app/ops/data_health_cli.py` only if existing CLI entrypoint must expose v2 profile
- `tests/test_ops_data_health.py`
- `tests/test_data_health_v2.py` if new focused file is cleaner
- `docs/quality/model_input_readiness_matrix.md` only if data health updates a docs summary by design
- task-local evidence under `.trellis/tasks/<task-slug>/execute-evidence/`

Do not touch:

- source fetch ports,
- production DB migration files,
- `source_health_snapshot` table implementation,
- frontend,
- production clean-write code.

---

## 5. 现有模式 / 参考

- v1 data health is read-only and checks staged pilot evidence, bars, metadata, lineage, and no-mutation posture.
- v1 explicitly forbids writing `source_health_snapshot` clean table.
- staged pilot evidence uses manifests and validation reports.
- source readiness must preserve staged/sandbox/validation-only wording.
- Production live pilot policy remains authoritative for no-production-mutation and authorization constraints.

---

## 6. 技术约束

- Data health v2 must read evidence files and specs; it must not fetch data.
- It must produce deterministic report output from a given evidence directory.
- It must support missing evidence as FAIL or WARN depending on declared gate, never silent PASS.
- It must differentiate:
  - `PASS`: evidence satisfies stated gate.
  - `WARN`: evidence is usable for staged planning but insufficient for sandbox clean-write rehearsal.
  - `FAIL`: evidence violates safety/schema/role/no-mutation constraints.
  - `BLOCKED`: prerequisite artifact, authorization statement, or whitelist is missing.
- It must not write DB tables.
- It must not update registries automatically.

Suggested profile names:

```text
data_health_profile=model_input_whitelist
data_health_profile=fred_sandbox_pilot
data_health_profile=tdx_manual_probe
data_health_profile=staged_pilot_v3
data_health_profile=source_readiness_rollup
```

---

## 7. 资源约束

- File reads only.
- Evidence directory must be inside project or approved sandbox path.
- No recursive scan beyond task evidence directories unless allowlisted.
- No full data root scan.
- No raw payload expansion beyond capped sample preview.
- Large evidence files must be summarized using row counts and hashes, not fully loaded into memory.

---

## 8. 边界约束

Must not:

- Fetch FRED, TDX, baostock, cninfo, akshare.
- Write source health clean tables.
- Run migration.
- Mark source production-ready.
- Convert WARN into PASS to unblock production.
- Close registry rows automatically.
- Treat missing production DB as mutation proof unless policy says no production DB path was touched.
- Treat fixture-only Layer2/3/4 data as production data.

Must do:

- Preserve source role semantics.
- Distinguish raw/staging/sandbox evidence from production clean evidence.
- Record whether evidence is enough for later sandbox clean-write rehearsal.
- Explain every FAIL/WARN with action and owner.

---

## 9. 实现步骤

Use `/to-issues` and `/tdd`. Suggested vertical slices:

1. **Slice DH2-01 — Whitelist profile**  
   RED: missing or malformed whitelist returns BLOCKED/FAIL with actionable message.  
   GREEN: add model-input whitelist reader/checker.

2. **Slice DH2-02 — FRED evidence profile**  
   RED: FRED evidence without series_id/fetch/hash/as_of fails.  
   GREEN: add FRED evidence checks.

3. **Slice DH2-03 — TDX probe profile**  
   RED: TDX evidence without authorization or validation-only status fails.  
   GREEN: add TDX evidence checks.

4. **Slice DH2-04 — staged pilot v3 profile**  
   RED: baostock/cninfo/akshare evidence that violates caps or roles fails.  
   GREEN: add v3 checks.

5. **Slice DH2-05 — source readiness rollup**  
   RED: mixed source results produce correct PASS/WARN/FAIL/BLOCKED summary.  
   GREEN: add rollup report.

6. **Slice DH2-06 — rehearsal gate statement**  
   RED: report cannot say eligible for sandbox clean write unless all required safety evidence exists.  
   GREEN: add gate decision text.

---

## 10. 测试要求

Minimum tests:

- Missing whitelist produces BLOCKED, not PASS.
- FRED evidence missing fetch/hash/as_of fails.
- FRED evidence from macro_supplementary does not close FRED primary readiness.
- TDX evidence without authorization fails or blocks.
- TDX evidence marked production primary fails.
- AkShare evidence marked primary fails.
- cninfo PDF bulk evidence fails for v3 metadata-only profile.
- v3 cap breach fails.
- source readiness rollup returns WARN when evidence is staged-only.
- report only marks sandbox-clean eligible when no-mutation proof, role checks, schema checks, and conflict summary exist.

Every new/changed test must include coverage scope, test object, and purpose/goal in docstring or nearby comment.

---

## 11. 验收命令

Targeted commands:

```bash
uv sync --locked
uv run pytest tests/test_ops_data_health.py -q
uv run pytest tests/test_data_health_v2.py -q
uv run ruff check backend/app/ops tests/test_ops_data_health.py tests/test_data_health_v2.py
```

If touching staged pilot fixtures or evidence helpers:

```bash
uv run pytest tests/test_staged_pilot.py tests/test_raw_store.py -q
```

Merge-gate recommendation:

```bash
uv run pytest -q
uv run ruff check .
uv run python -m compileall backend scripts tests
```

---

## 12. 完成标准

- Data health v2 supports whitelist, FRED, TDX, staged pilot v3, and source readiness rollup profiles.
- Every profile has semantic tests.
- Reports distinguish PASS/WARN/FAIL/BLOCKED.
- Reports do not claim production-live or production clean-write readiness.
- Reports can state whether evidence is sufficient for later sandbox clean-write rehearsal.
- No source fetch, migration, or DB write occurs.
- Tests pass or environment failure is recorded exactly.

---

## 13. Red Flags

Stop and repair if any occur:

- Data health code performs network fetch.
- Data health writes `source_health_snapshot` or any clean table.
- Missing evidence becomes PASS.
- FRED macro_supplementary evidence closes FRED primary readiness.
- TDX or AkShare is treated as Primary.
- Full data root scan is introduced.
- Tests only assert report exists and do not inspect safety decisions.

---

## 14. 输出要求

Final report must include:

1. Profiles added.
2. Evidence inputs used.
3. PASS/WARN/FAIL/BLOCKED summary.
4. Sandbox clean-write eligibility statement.
5. Registry rows affected or explicitly not affected.
6. Confirmation: no fetch, no DB write, no migration.
7. Test commands/results.
8. Remaining risks.

---

## 15. 审计修复新增强制项

- **版本与锁文件:** No new runtime dependency unless approved; data health should use existing parsing utilities or stdlib.
- **阶段化验收:** Read-only backend checks have targeted tests; no frontend/build requirement unless touched.
- **回滚与恢复:** Code/docs changes rollback by revert; no DB rollback should be needed.
- **幂等与重试:** Reports from same evidence should be deterministic; repeated runs should not mutate evidence.
- **安全与隐私:** Evidence reports must not leak credentials or raw private endpoint details.
- **lineage / as-of:** Checks must verify presence of as_of/source_fetch_id/content_hash where required for future Layer5.
- **测试质量:** Tests must assert gate semantics and forbidden promotions, not only successful parsing.
