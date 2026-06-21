# Audit Report — Round 3 Batch 2.75 Production Live Pilot Gate

## 1. 元信息

| 字段            | 值                                                             |
| --------------- | -------------------------------------------------------------- |
| GitNexus 刷新   | 2026-06-21T14:52:54.293Z local index; live MCP/CLI unavailable |
| 摘要文件        | `research/gitnexus-audit-summary.md`                           |
| Trace presence  | `research/audit-trace-presence-check.md` = PASS_TO_DISPATCH    |
| Execute handoff | `validate-execute-handoff` passed                              |

---

## 2. 维度验证汇总

| 维    | 验证命令/检查                                   | 环境          | 隔离          | 结果           | 证据                                     |
| ----- | ----------------------------------------------- | ------------- | ------------- | -------------- | ---------------------------------------- |
| PH-B0 | Phase -1 / Phase 0 reconciliation + fail-closed | local         | read-only     | PASS           | `research/audit-ph-b0-reconciliation.md` |
| PH-B1 | baseline + zero mutation                        | local         | read-only     | PASS           | `research/audit-ph-b1-baseline.md`       |
| PH-B2 | route matrix + no fixture fallback              | local         | read-only     | FAIL           | `research/audit-ph-b2-route.md`          |
| PH-B3 | HITL + raw fetch                                | local         | read-only     | PASS_WITH_RISK | `research/audit-ph-b3-raw-fetch.md`      |
| PH-B4 | validation + conflict                           | local         | read-only     | FAIL           | `research/audit-ph-b4-validation.md`     |
| PH-B5 | perf budget / re-defer                          | audit-sandbox | read-only     | FAIL           | `research/audit-ph-b5-perf.md`           |
| PH-B6 | closeout + registry + §10                       | local         | read-only     | FAIL           | `research/audit-ph-b6-closeout.md`       |
| A1    | original-source trace                           | local         | read-only     | PASS           | `research/audit-sections/A1.md`          |
| A2    | over-engineering                                | local         | read-only     | PASS           | `research/audit-sections/A2.md`          |
| A3    | security                                        | local         | read-only     | FAIL           | `research/audit-sections/A3.md`          |
| A4    | code quality                                    | local         | read-only     | FAIL           | `research/audit-sections/A4.md`          |
| A5    | AC source-chain completion                      | local         | read-only     | FAIL           | `research/audit-sections/A5.md`          |
| A6    | performance/resources                           | audit-sandbox | sandbox smoke | PASS           | `research/audit-sections/A6.md`          |
| A7    | ops/idempotency/logging                         | local         | read-only     | FAIL           | `research/audit-sections/A7.md`          |
| A8    | original red-flags test gap                     | local         | read-only     | FAIL           | `research/audit-sections/A8.md`          |

### Execute §10 证据索引（只读引用）

| Tier      | Execute 证据路径/摘要                                                                       |
| --------- | ------------------------------------------------------------------------------------------- |
| A/B/C/G   | `final_pytest_output.txt` and `8.8-green.txt` are insufficient for command-level Tier proof |
| D/E/F     | No ruff / compileall / production_gate / doc_links evidence found in Execute closeout       |
| prod-path | No `AUDIT_PROD_ROOT` copy/hash proof found                                                  |

---

## 3. 分维度详情

### 3.1 A1 · Spec

PASS. A1 found no Plan omission or source-scope drift. Registry closeout drift is real but owned by A5/PH-B6, not A1 source tracing.

### 3.2 A2 · Ponytail

PASS. A2 found non-blocking shrink opportunities, mainly repeated test scaffolding and duplicated mutation-proof helpers. No A2 item is blocking.

### 3.3 A3 · Security

FAIL. P1: authorization validation is bound to source/domain/operation but not exact approved symbol/window/per-request row cap. This can expand a live fetch under an approved triple.

### 3.4 A4 · Code Quality

FAIL. Phase 4 can continue without code-level fail-closed verification that Request 2 verdict/reconciliation artifacts exist and are authoritative.

### 3.5 A5 · Completion

FAIL. AC trace exists, but closeout fails on registry consistency, perf/hyg re-defer registry rows, §10 Tier proof, and prod-path hash proof.

### 3.6 A6 · Performance

PASS. A6 ran audit-sandbox smoke with `--use-service-path`: `ALL PASS`, `elapsed_s=8.08`. This does not replace Execute's missing perf/re-defer registry closeout.

### 3.7 A7 · Ops

FAIL. Production DB mutation was not found, but idempotency, failure recovery artifacts, route-not-ready evidence, fixture fallback coverage, and Phase 4.5 ops evidence are incomplete.

### 3.8 A8 · Test Gap

FAIL. Missing Batch-local tests for route non-READY stop, LocalFixture/staged fallback, optional source allowlist rejection, and reconcile prohibition.

---

## 4. 风险与结论（A9）

### 4.2 结论

- [ ] **PASS**
- [ ] **PASS_WITH_FIXES**
- [x] **FAIL**

Audit cannot pass until §4.3 is repaired and Repair re-verifies MASTER §10.

### 4.3 修复项（→ REPAIR.plan §1）

| ID  | 维度           | 问题                                                                                                                                                                                               | 根因修复（非兜底）                                                                                                                                                                          | 优先级 |
| --- | -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| R-1 | A3/A8/PH-B0    | Authorization only checks approved triples, not exact symbol/window/per-request cap.                                                                                                               | Bind `validate_authorization()` to the authorization file's exact request envelope; add negative tests for wrong symbol, expanded row cap, and unapproved optional source.                  | P1     |
| R-2 | PH-B2/A7/A8    | Batch-local route non-READY and fixture/staged fallback tests are missing/incomplete.                                                                                                              | Add Batch 2.75 tests proving non-READY stops before fetch and both `StubFetchPort`/`LocalFixtureFetchPort`/staged service cannot satisfy live evidence.                                     | P1     |
| R-3 | PH-B4/A4/A5/A7 | Phase 4 evidence does not prove severe blocks clean write, and implementation does not use the declared validator/conflict paths or fail closed on Request 2 verdict/reconciliation prerequisites. | Wire or explicitly freeze the real Phase 4 validation/conflict gate; require Request 2 verdict/reconciliation before Phase 4; prove severe/no-clean-write behavior with tests/evidence.     | P1     |
| R-4 | A7             | Fetch failure and rerun/idempotency recovery are not structured; partial failure can leave no durable failure/no-mutation artifact.                                                                | Persist per-request failure evidence and rerun-safe sandbox evidence semantics; add tests or audit evidence for repeat execution and vendor failure.                                        | P1     |
| R-5 | PH-B5/A5/A6/A7 | Perf/hyg `RE_DEFERRED` is not in authoritative registries; Execute perf evidence lacks smoke/ResourceGuard proof.                                                                                  | Add/align authoritative registry rows for `R3-B25-PERF-BUDGET-01` and `R3-B25-HYG-03`; update closure command/evidence to include `--use-service-path` smoke or explicit approved re-defer. | P1     |
| R-6 | PH-B6/A5       | Closeout is not audit-complete: registry conflict, missing Tier A-G command proof, and missing `AUDIT_PROD_ROOT` hash proof.                                                                       | Reconcile four registries; produce command-level MASTER §10 A-G evidence; create audit-prod-path copy/hash proof with before/after production hash unchanged.                               | P1     |

### 4.4 Deferred

| ID  | 问题 | 理由                                       | 后续任务 |
| --- | ---- | ------------------------------------------ | -------- |
| —   | —    | No new deferred item approved by Audit A9. | —        |

---

## 5. Repair 复验（Phase 8 后）

| 项                   | 结果 | 证据                                                                                                                              |
| -------------------- | ---- | --------------------------------------------------------------------------------------------------------------------------------- |
| §4.3 全部关闭        | PASS | `repair-evidence/R-1_authorization_envelope.md` through `repair-evidence/R-6_tier_ag_prod_hash.md`                                |
| MASTER §10 Tier 复跑 | PASS | `repair-evidence/final_repair_verification.md`; Tier A-G all pass via direct venv equivalents because `uv` is unavailable on PATH |
| Prod-path hash proof | PASS | `repair-evidence/R-6_tier_ag_prod_hash.md`; hash unchanged `5EB65E0EDAAAB223A77C5A5D2660603383836704B4C0ECE1EB4AEBB047F1682E`     |

Repair closed R-1..R-6. Remaining deferred items are registry-owned follow-ups only: `R3-B2.75-REQ2-EM`, `R3-B25-PERF-BUDGET-01`, `R3-B25-HYG-03`, and `B2.5-O-05`.
