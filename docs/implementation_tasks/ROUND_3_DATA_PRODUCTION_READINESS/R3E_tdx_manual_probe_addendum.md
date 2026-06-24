# R3E_tdx_manual_probe_addendum — TDX Manual Probe Execution Addendum

> Roadmap link: `PROJECT_IMPLEMENTATION_ROADMAP.md` → Round 3E.2.  
> Priority: P0/P1.  
> Suggested branch: `debt/round3-tdx-manual-probe`.  
> Type: addendum to existing TDX/018C task cards.  
> Production posture: manual, authorized, raw-only, validation-only candidate; no production clean write.  
> Batch hardening: must read `BATCH_01_MODEL_SOURCE_READINESS/README.md`, `BATCH_01_TASK_CARD_MANIFEST.md`, `BATCH_01_ADVERSARIAL_AUDIT.md`, and `BATCH_01_HARDENING_RULES.md` before execution.

---

## 1. 任务目标

在现有 `018C_tdx_pytdx_low_cost_probe.md` 和 reference landing 的基础上，补齐执行者必须知道的 TDX manual probe 落地细节：授权门槛、探测范围、行数上限、失败 taxonomy、与 baostock/akshare 对照方式、禁止 production primary 的边界。

本任务不是新开一个生产 TDX 接入工程，而是把 TDX 作为候选 validation-only source 做最小手动探测。

---

## 2. 预期结果

完成后应能回答：

- 当前环境是否具备 TDX / pytdx 连接条件。
- TDX 对 1 个 A 股日线、1 个指数日线、1 次 small security list 的字段是否可用。
- TDX 与 baostock/akshare 对照是否存在明显字段/日期/价格/成交量差异。
- TDX 是否继续 re-defer、拒绝、或保留为 disabled-by-default validation-only candidate。
- TDX 仍不能被用于 production primary、production clean write、Layer2 production source。

---

## 3. 输入文件

执行前必须读取：

- `PROJECT_IMPLEMENTATION_ROADMAP.md`
- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/018C_tdx_pytdx_low_cost_probe.md`
- `docs/implementation_tasks/ROUND_3_REFERENCE_LANDING/R3D_018C_low_cost_source_probe.md`
- `docs/implementation_tasks/ROUND_3_REFERENCE_LANDING/R3D_018C_live_manual_probe_plan.md`
- `docs/implementation_tasks/ROUND_3_PARALLEL_PROMPTS/PROMPT_10_debt_r3b275_018c_live_manual_probe_plan.md`
- `docs/quality/production_live_pilot_policy.md`
- `docs/quality/staged_acceptance_policy.md`
- `docs/AUDIT_DEFERRED_REGISTRY.md` rows `R3-B2.75-REQ2-EM`, `R3-PROMPT14-AKSHARE-VAL-01`, `R2.6-IMPL-8`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md` same rows
- `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`
- `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`
- `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`
- `specs/contracts/runtime_versions.md`
- `specs/datasource_registry/source_registry.yaml`
- `specs/datasource_registry/source_capabilities.yaml`
- `specs/contracts/source_route_contract.yaml`
- `specs/contracts/source_capability_contract.yaml`
- `specs/contracts/datasource_service_contract.yaml`
- `specs/contracts/data_adapter_contract.md`
- `backend/app/datasources/adapters/tdx_pytdx.py`
- `backend/app/datasources/route_planner.py`
- `backend/app/ops/staged_pilot.py`
- `backend/app/ops/live_pilot_fetch_ports.py`
- `backend/app/layer2_sensors/observation.py`

---

## 4. 相关代码文件

Candidate touched paths:

- `backend/app/datasources/adapters/tdx_pytdx.py`
- `backend/app/ops/tdx_manual_probe.py` or extension under existing ops pilot paths
- `backend/app/ops/live_pilot_fetch_ports.py`
- `specs/datasource_registry/source_registry.yaml`
- `specs/datasource_registry/source_capabilities.yaml`
- `tests/test_tdx_manual_probe.py`
- `tests/test_source_capabilities.py`
- `tests/test_source_route_planner.py`
- task-local evidence under `.trellis/tasks/<task-slug>/execute-evidence/`

Do not touch:

- production DB migration files,
- frontend,
- Layer2 production source enablement,
- QMT/xqshare/Yahoo adapters unless a separate authorized task exists.

---

## 5. 现有模式 / 参考

- Current `tdx_pytdx` is disabled by default and validation-only.
- Current TDX adapter is thin/skeletal; do not interpret skeleton as production readiness.
- Layer2 explicitly must not treat TDX as production source at current stage.
- 018C says candidate probes must remain sidecar-only and cannot close Batch 2.75 Request 2 by themselves.
- PROMPT_14 AkShare network failure and Eastmoney hist failure remain separate; TDX does not silently close either unless approved alternate validation path is documented.

---

## 6. 技术约束

- Live TDX probing requires explicit user authorization before any network call.
- Authorization must name host, port, symbol(s), max rows, max calls, and evidence directory.
- TDX dependency must remain optional; missing pytdx should produce `TDX_PROBE_FAIL_DEPENDENCY` or skip/defer status, not test failure in default CI.
- Default CI must pass without live TDX server.
- Tests must use mocked TDX responses for normal CI.
- Live manual probe must be a separate opt-in command or flag.

Suggested probe status enum:

```text
TDX_PROBE_PASS_RAW_ONLY
TDX_PROBE_FAIL_AUTH_MISSING
TDX_PROBE_FAIL_DEPENDENCY
TDX_PROBE_FAIL_NETWORK
TDX_PROBE_FAIL_SCHEMA
TDX_PROBE_FAIL_VALIDATION
TDX_PROBE_REJECTED
TDX_PROBE_REDEFERRED
```

---

## 7. 资源约束

Initial probe caps:

- Equity daily bar: 1 symbol, latest 30 trading days.
- Index daily bar: 1 index, latest 30 trading days.
- Security list: max 100 rows or lower if policy requires.
- Network calls: max 5 unless explicitly approved.
- No full market scan.
- No full historical download.
- No intraday/minute bars in this task.
- No polling loop.

---

## 8. 边界约束

Must not:

- Mark TDX as production primary.
- Enable TDX by default.
- Use TDX as Layer2 production source.
- Use TDX as automatic fallback.
- Write production DB.
- Write clean table, even sandbox clean table, unless a later rehearsal task authorizes it.
- Close Eastmoney hist failure solely because TDX worked.
- Close AkShare validation failure solely because TDX worked.
- Add QMT/xqshare integration.
- Add trading/order API.

Must do:

- Keep all probe output raw/staging/sandbox evidence.
- Record authorization evidence for any live run.
- Record dependency/network/schema failures explicitly.
- Compare TDX sample with baostock/akshare only when comparable evidence is available.
- Preserve validation-only status unless a later user-approved task changes policy.

---

## 9. 实现步骤

Use `/to-issues` and `/tdd`. Suggested vertical slices:

1. **Slice TDX-01 — Authorization gate**  
   RED: live probe refuses to run without explicit authorization payload.  
   GREEN: add authorization validation and status reporting.

2. **Slice TDX-02 — Mocked equity daily probe**  
   RED: mocked TDX equity response produces raw evidence and validates fields.  
   GREEN: implement minimal parser/manifest path.

3. **Slice TDX-03 — Mocked index daily probe**  
   RED: mocked TDX index response produces raw evidence and remains validation-only.  
   GREEN: extend probe without changing production source roles.

4. **Slice TDX-04 — Small security-list probe**  
   RED: over-cap security list fails or truncates with explicit status.  
   GREEN: add capped security-list probe.

5. **Slice TDX-05 — Comparison report**  
   RED: comparison report distinguishes comparable values, missing comparison source, and conflict.  
   GREEN: implement comparison summary without auto-overwrite.

6. **Slice TDX-06 — Registry/defer closeout**  
   RED: TDX success cannot close Eastmoney/AkShare rows automatically.  
   GREEN: update or preserve registry rows with explicit rationale.

---

## 10. 测试要求

Minimum tests:

- Probe refuses without authorization.
- Missing optional dependency is fail/defer status, not production fallback.
- Mock equity daily probe writes raw evidence with source_id, symbol, dates, hash/fetch id.
- Mock index daily probe writes raw evidence with source_id, symbol/index id, dates, hash/fetch id.
- Security list cap enforced.
- TDX remains disabled-by-default and validation-only in registry/capability.
- Layer2 production source guard remains intact.
- TDX success does not close `R3-B2.75-REQ2-EM` or `R3-PROMPT14-AKSHARE-VAL-01` automatically.

Every new/changed test must include coverage scope, test object, and purpose/goal in docstring or close comment.

---

## 11. 验收命令

Targeted commands:

```bash
uv sync --locked
uv run pytest tests/test_tdx_manual_probe.py -q
uv run pytest tests/test_source_capabilities.py tests/test_source_route_planner.py -q
uv run pytest tests/test_layer2_cross_asset_sensor.py -q
uv run ruff check backend/app/datasources backend/app/ops tests/test_tdx_manual_probe.py
```

Merge-gate recommendation:

```bash
uv run pytest -q
uv run ruff check .
uv run python -m compileall backend scripts tests
```

If no TDX authorization exists, do not run live probe. Record `TDX_PROBE_REDEFERRED` or `TDX_PROBE_FAIL_AUTH_MISSING` according to implementation status.

---

## 12. 完成标准

- Manual authorization gate exists and is tested.
- Mocked probe paths prove equity/index/security-list shapes.
- Optional dependency/network failures have explicit statuses.
- Any live run, if performed, is bounded and raw-only.
- TDX remains disabled-by-default and validation-only.
- No production DB or clean table is written.
- Registry rows are either untouched with rationale or updated consistently.
- Tests pass or environment failure is recorded exactly.

---

## 13. Red Flags

Stop and repair if any occur:

- TDX is enabled by default.
- TDX becomes production primary or automatic fallback.
- A live network call runs without explicit authorization.
- Full security list or full market data is fetched.
- The task adds QMT/xqshare/Yahoo scope.
- TDX success is used to close Eastmoney/AkShare rows without approved alternate-path documentation.
- Production DB or clean table is touched.
- Tests require live TDX in default CI.

---

## 14. 输出要求

Final report must include:

1. Whether authorization was present.
2. Whether live probe was run.
3. Probe status enum result.
4. Evidence paths.
5. Comparison report status.
6. Confirmation that TDX remains validation-only and disabled-by-default.
7. Production DB no-mutation statement.
8. Registry decision for Eastmoney/AkShare related rows.
9. Test commands/results.
10. Remaining risks.

---

## 15. 审计修复新增强制项

- **版本与锁文件:** pytdx or related dependency must remain optional; do not mutate lockfile without explicit approval.
- **阶段化验收:** Mocked tests are required; live tests are optional and authorization-gated.
- **回滚与恢复:** Raw probe artifacts can be deleted; no DB rollback should be needed.
- **幂等与重试:** Repeated probe with same symbol/window should produce traceable request fingerprint and avoid ambiguous evidence overwrite.
- **安全与隐私:** Host/port/user authorization evidence must not include private credentials or secrets.
- **lineage / as-of:** Evidence must include retrieved_at/as_of/source_fetch_id/content_hash for future Layer5 binding.
- **测试质量:** Tests must verify validation-only and disabled-by-default business safety, not only parser success.
