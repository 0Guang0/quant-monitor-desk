# R3E_real_data_staged_pilot_v3 — Model-driven baostock / cninfo / akshare Staged Pilot v3

> Roadmap link: `PROJECT_IMPLEMENTATION_ROADMAP.md` → Round 3E.3.  
> Priority: P1.  
> Suggested branch: `feature/round3-real-data-staged-pilot-v3`.  
> Type: backend + evidence + tests.  
> Production posture: raw/staging/sandbox only; no production clean write; model-driven expansion only.  
> Batch hardening: must read `BATCH_01_MODEL_SOURCE_READINESS/README.md`, `BATCH_01_TASK_CARD_MANIFEST.md`, `BATCH_01_ADVERSARIAL_AUDIT.md`, and `BATCH_01_HARDENING_RULES.md` before execution.

---

## 1. 任务目标

在 PROMPT_14 / PROMPT_19 staged pilot v1/v2 的基础上，按 `R3D_model_input_whitelist` 的输出，把 baostock、cninfo、akshare 的小样本真实数据试跑升级为 model-driven staged pilot v3。

本任务不是全市场接入，也不是生产入库。它只扩展当前模型第一批需要的 symbols / issuers / domains，并输出 source readiness 证据。

---

## 2. 预期结果

完成后应具备：

- baostock A 股日线从 v2 的极小样本扩展到 5–20 个 model-input symbols。
- cninfo 公告/披露 metadata 扩展到 model-input issuers/symbols。
- akshare 只做 validation-only retry / comparison，不作为 Primary。
- 每个 source/domain 有 route preview、raw evidence manifest、staging evidence manifest、validation report、source conflict dry-run summary。
- 明确哪些 source/domain 可以进入 later sandbox clean-write rehearsal，哪些继续 re-defer。
- 证明系统仍是 model-driven ingestion，而不是 full-market ingestion。

---

## 3. 输入文件

执行前必须读取：

- `PROJECT_IMPLEMENTATION_ROADMAP.md`
- `docs/implementation_tasks/ROUND_3_DATA_PRODUCTION_READINESS/R3D_model_input_whitelist.md`
- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3X_real_data_staged_pilot.md`
- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_real_data_staged_pilot_v2.md`
- `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_staged_pilot_v2_execution_addendum.md`
- `docs/quality/prompt14_user_authorization_2026-06-22.md`
- `docs/quality/production_live_pilot_policy.md`
- `docs/quality/staged_acceptance_policy.md`
- `docs/AUDIT_DEFERRED_REGISTRY.md` rows `R3-PROMPT14-AKSHARE-VAL-01`, `R3-B2.75-REQ2-EM`
- `docs/UNRESOLVED_ISSUES_REGISTRY.md` same rows
- `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`
- `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`
- `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`
- `specs/contracts/runtime_versions.md`
- `specs/datasource_registry/source_registry.yaml`
- `specs/datasource_registry/source_capabilities.yaml`
- `specs/contracts/source_route_contract.yaml`
- `specs/contracts/datasource_service_contract.yaml`
- `specs/contracts/data_quality_rules.yaml`
- `specs/contracts/source_conflict_rules.yaml`
- `specs/contracts/resource_limits.yaml`
- `backend/app/ops/staged_pilot.py`
- `backend/app/ops/staged_pilot_fetch_ports.py`
- `backend/app/ops/live_pilot_fetch_ports.py`
- `backend/app/storage/staged_evidence.py`
- `backend/app/validators/data_quality.py`
- `backend/app/validators/source_conflict.py`
- `tests/test_staged_pilot.py`
- `tests/test_raw_store.py`

If `specs/model_inputs/**` does not yet exist, this task must stop and either depend on `R3D_model_input_whitelist` or create only a blocked plan update, not invent source scope.

---

## 4. 相关代码文件

Candidate touched paths:

- `backend/app/ops/staged_pilot.py`
- `backend/app/ops/staged_pilot_fetch_ports.py`
- `backend/app/ops/live_pilot_fetch_ports.py`
- `backend/app/storage/staged_evidence.py` only if evidence registration requires narrow extension
- `backend/app/validators/data_quality.py` only if existing validation rules cannot validate v3 evidence
- `tests/test_staged_pilot.py`
- `tests/test_raw_store.py`
- `tests/test_real_data_staged_pilot_v3.py` if a new focused test file is clearer
- task-local evidence under `.trellis/tasks/<task-slug>/execute-evidence/`

Do not touch:

- production DB migration files,
- production clean tables,
- frontend,
- Layer2/3/4 model computation,
- full backfill or scheduling.

---

## 5. 现有模式 / 参考

- v2 used bounded route preview, raw evidence, staging evidence, validation report, no-mutation proof, and resource caps.
- staged evidence registry bypass has been privatized; do not resurrect public bypass.
- AkShare validation route previously failed for the Eastmoney hist family; do not treat a different sidecar as closure without explicit evidence reconciliation.
- baostock is the preferred A股 daily bar source candidate for this pilot.
- cninfo scope is metadata first, not bulk PDF download.

---

## 6. 技术约束

- Pilot v3 must be driven by model input whitelist output.
- No hard-coded broad market universe.
- Symbols and issuers must be capped and auditable.
- Every source attempt must produce success/failure taxonomy.
- Validation-only source output must not become primary raw fact automatically.
- Evidence files must include pilot_id/version and input whitelist reference/hash if available.
- `skip_live_fetch=True` / dry-run must remain supported.
- Live network fetch must be explicitly authorized and capped.

Suggested pilot status enum:

```text
PILOT_V3_PASS_STAGED_RAW
PILOT_V3_PASS_WITH_VALIDATION_WARNINGS
PILOT_V3_FAIL_SOURCE
PILOT_V3_FAIL_VALIDATION
PILOT_V3_FAIL_CONFLICT
PILOT_V3_REDEFERRED
```

---

## 7. 资源约束

Default caps unless whitelist is stricter:

- baostock: 5–20 symbols, 30–120 trading days, max 2,000 rows total.
- cninfo: 5–20 symbols/issuers, 30–120 calendar days, metadata only, max 500 rows.
- akshare: 2–10 comparison symbols, 30–120 trading days, validation-only, max 1,000 rows.
- Network calls: max 50 total unless explicitly approved.
- No full-market scan.
- No full-history backfill.
- No minute/intraday data.
- No PDF full-text download.

ResourceGuard must stop on cap breach and record status.

---

## 8. 边界约束

Must not:

- Claim production-live readiness.
- Write production clean DB.
- Run full market or full history.
- Download all cninfo PDFs.
- Promote AkShare to Primary.
- Use AkShare network success to close Eastmoney hist failure without evidence reconciliation.
- Enable TDX/QMT/Yahoo/FRED.
- Treat source conflict as automatically resolved.
- Use staged data to drive production monitoring.

Must do:

- Keep all outputs in raw/staging/sandbox paths.
- Produce no-mutation proof for production DB or prove production DB path was not opened.
- Explicitly list every selected symbol/issuer/series and why it belongs to model input whitelist.
- Generate source readiness matrix.

---

## 9. 实现步骤

Use `/to-issues` and `/tdd`. Suggested vertical slices:

1. **Slice SP3-01 — Whitelist input loader / validator**  
   RED: pilot refuses to run without whitelist or with over-broad inputs.  
   GREEN: load whitelist subset and enforce caps.

2. **Slice SP3-02 — baostock daily bar expansion**  
   RED: mocked baostock model-input symbols produce raw/staging manifests with hashes/fetch ids.  
   GREEN: implement capped expansion.

3. **Slice SP3-03 — cninfo metadata expansion**  
   RED: mocked cninfo metadata produces metadata-only raw/staging evidence and refuses PDF full-text.  
   GREEN: implement metadata expansion.

4. **Slice SP3-04 — akshare validation-only retry**  
   RED: akshare cannot become primary and failure taxonomy is explicit.  
   GREEN: implement validation-only comparison path.

5. **Slice SP3-05 — conflict dry-run summary**  
   RED: baostock vs akshare mismatch creates conflict summary, not clean-table overwrite.  
   GREEN: implement dry-run conflict summary.

6. **Slice SP3-06 — closeout/readiness report**  
   RED: report cannot claim production readiness or sandbox-clean eligibility without required evidence.  
   GREEN: implement final closeout schema.

---

## 10. 测试要求

Minimum tests:

- Pilot refuses unbounded or missing whitelist input.
- baostock v3 sample respects symbol/date/row caps.
- cninfo metadata path rejects PDF/full-text expansion.
- akshare remains validation-only and cannot be selected as Primary.
- source failure taxonomy distinguishes network/auth/schema/validation/conflict.
- source conflict dry-run creates report and does not write clean table.
- production DB no-mutation proof or no-open proof is produced.
- readiness matrix contains each selected source/domain and allowed next gate.

Every new/changed test must include coverage scope, test object, and purpose/goal in docstring or nearby comment.

---

## 11. 验收命令

Targeted commands:

```bash
uv sync --locked
uv run pytest tests/test_staged_pilot.py -q
uv run pytest tests/test_raw_store.py -q
uv run pytest tests/test_real_data_staged_pilot_v3.py -q
uv run ruff check backend/app/ops backend/app/storage backend/app/validators tests/test_staged_pilot.py tests/test_raw_store.py tests/test_real_data_staged_pilot_v3.py
```

Merge-gate recommendation:

```bash
uv run pytest -q
uv run ruff check .
uv run python -m compileall backend scripts tests
```

If live network is not authorized, run dry-run/mocked tests and report live fetch as not executed.

---

## 12. 完成标准

- v3 pilot is model-input-whitelist driven.
- baostock/cninfo/akshare roles are explicit and capped.
- Evidence manifests include source_fetch_id/content_hash/as_of/retrieved_at.
- Source readiness matrix is produced.
- AkShare validation-only semantics are enforced.
- No full-market/full-history/PDF bulk behavior exists.
- No production clean write occurs.
- Registry rows are closed only with exact evidence or re-deferred explicitly.
- Tests pass or environment failure is recorded exactly.

---

## 13. Red Flags

Stop and repair if any occur:

- Pilot scope is hand-picked without whitelist trace.
- v3 expands to all A股 or all cninfo records.
- AkShare becomes Primary.
- cninfo downloads full PDF corpus.
- Conflict summary writes or overwrites clean table.
- Production DB is mutated.
- Evidence lacks source_fetch_id or content_hash.
- Tests only check that commands run, not safety semantics.

---

## 14. 输出要求

Final report must include:

1. Selected symbols/issuers and whitelist references.
2. Source attempts and status taxonomy.
3. Evidence artifact paths.
4. Validation and conflict summary.
5. Source readiness matrix.
6. Production DB no-mutation/no-open proof.
7. Registry decisions.
8. Test commands/results.
9. Remaining risks.

---

## 15. 审计修复新增强制项

- **版本与锁文件:** Do not add new source libraries unless approved; existing optional deps remain optional.
- **阶段化验收:** Dry-run/mocked mode is acceptable when live authorization is absent; do not claim live pass.
- **回滚与恢复:** Raw/staging artifacts can be deleted; no clean table rollback should be required.
- **幂等与重试:** source_fetch_id/request fingerprint must distinguish repeated attempts and source retries.
- **安全与隐私:** No credentials in evidence; redact endpoint tokens if any.
- **lineage / as-of:** All successful data rows must carry enough as-of/hash/fetch metadata for Layer5 evidence chain.
- **测试质量:** Tests must enforce model-driven scope and source role boundaries.
