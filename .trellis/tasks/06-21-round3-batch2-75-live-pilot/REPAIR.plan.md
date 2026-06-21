# Repair 计划 — Round 3 Batch 2.75 Production Live Pilot Gate

> **读者：Repair 执行者**
> **输入：** `audit.report.md` §4.3
> **原则：** 修根因，不兜底；§3 Deferred 以外不得遗留。

## 0. 元信息

| 字段              | 值                                              |
| ----------------- | ----------------------------------------------- |
| slug              | `06-21-round3-batch2-75-live-pilot`             |
| Audit 报告        | `audit.report.md`                               |
| Repair Skill 词典 | `.trellis/spec/guides/repair-skill-registry.md` |

```text
进入 Repair。读 audit.report.md §4.3 与本文 §1。
逐项修根因（禁止防御性绕过）；每项填证据；跑 §2 复验命令。
Deferred 仅 §3 已批准项；其余全关才进 Finish。
```

---

## 1. 修复项清单

| ID  | 维度           | 问题                                                                                                                          | 根因修复方案                                                                                                                                       | Skill（冻结）                                                                 | 验证命令                                                                                                                               | 通过条件                                                                          | 证据                                            | 已修复 |
| --- | -------------- | ----------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ----------------------------------------------- | ------ |
| R-1 | A3/A8          | Authorization not bound to exact symbol/window/per-request cap.                                                               | Enforce exact authorized request envelope; add negative tests for wrong symbol, row cap/window expansion, and optional source expansion.           | systematic-debugging; test-driven-development; security-and-hardening         | `uv run pytest tests/test_batch275_live_pilot_gate.py -q`                                                                              | unauthorized variants fail before fetch                                           | `repair-evidence/R-1_authorization_envelope.md` | [x]    |
| R-2 | PH-B2/A7/A8    | Missing Batch-local route non-READY and fixture/staged fallback coverage.                                                     | Add stop-before-fetch and no-fixture tests covering `StubFetchPort`, `LocalFixtureFetchPort`, and staged service fallback.                         | systematic-debugging; test-driven-development                                 | `uv run pytest tests/test_batch275_live_pilot_gate.py -q`                                                                              | non-READY and fixture fallback cannot produce live evidence                       | `repair-evidence/R-2_route_fixture_fallback.md` | [x]    |
| R-3 | PH-B4/A4/A5/A7 | Phase 4 does not prove severe clean-write block or declared validator/conflict path; Request 2 prerequisites not fail-closed. | Require Request 2 verdict/reconciliation before Phase 4 and wire/freeze validation/conflict behavior with severe blocking proof.                   | systematic-debugging; test-driven-development; source-driven-development      | `uv run pytest tests/test_batch275_live_pilot_gate.py tests/test_source_conflict_validator.py tests/test_data_quality_validator.py -q` | Phase 4 fails closed without prerequisites and proves no-clean-write/severe block | `repair-evidence/R-3_phase4_fail_closed.md`     | [x]    |
| R-4 | A7             | Fetch failure and rerun/idempotency evidence are not durable.                                                                 | Persist per-request failure artifacts and rerun-safe sandbox evidence; prove repeated run does not corrupt evidence.                               | systematic-debugging; test-driven-development                                 | `uv run pytest tests/test_batch275_live_pilot_gate.py -q`                                                                              | vendor failure and rerun cases leave durable no-mutation/failure evidence         | `repair-evidence/R-4_idempotency_failure.md`    | [x]    |
| R-5 | PH-B5/A5/A6/A7 | Perf/hyg re-defer registry and smoke/ResourceGuard evidence are incomplete.                                                   | Align `AUDIT_DEFERRED`/unresolved registry rows; update perf closure evidence to include `--use-service-path` smoke or explicit approved re-defer. | systematic-debugging; test-driven-development; verification-before-completion | `uv run python scripts/production_equivalent_smoke.py --use-service-path --data-root .audit-sandbox/r3b275-audit`                      | smoke or re-defer evidence is authoritative and ResourceGuard-visible             | `repair-evidence/R-5_perf_registry_smoke.md`    | [x]    |
| R-6 | PH-B6/A5       | Registry conflict, Tier A-G proof, and prod-path hash proof missing.                                                          | Reconcile four registries; produce MASTER §10 A-G command logs; create `AUDIT_PROD_ROOT` copy/hash proof.                                          | systematic-debugging; verification-before-completion                          | MASTER §10 A-G commands                                                                                                                | all tiers pass; prod hash unchanged; registries agree                             | `repair-evidence/R-6_tier_ag_prod_hash.md`      | [x]    |

---

## 2. Repair Skill 冻结

| Skill                          | 本任务 | 绑定修复项   | `@` 指令                                                                     | 已执行 |
| ------------------------------ | ------ | ------------ | ---------------------------------------------------------------------------- | ------ |
| systematic-debugging           | 必做   | R-1..R-6     | Identify root cause before code edits; no wrapper-only fixes.                | [x]    |
| test-driven-development        | 必做   | R-1..R-5     | Add/enable failing test before implementation where code changes are needed. | [x]    |
| security-and-hardening         | 条件   | R-1          | Preserve fail-closed authorization and data boundaries.                      | [x]    |
| source-driven-development      | 条件   | R-3          | Follow validator/conflict contracts instead of inventing parallel semantics. | [x]    |
| verification-before-completion | 必做   | R-5,R-6,收尾 | Re-run MASTER §10 after repair.                                              | [x]    |

---

## 3. 批准遗留（Deferred）

| ID  | 问题 | 遗留理由       | 后续任务/ADR |
| --- | ---- | -------------- | ------------ |
| —   | —    | None approved. | —            |

---

## 4. Repair 完成 DoD

- [x] §1 全部可修项已修复并有证据
- [x] §3 Deferred 已用户确认（若有）
- [x] 复跑 MASTER §10 Tier A-G
- [x] `audit.report.md` §5 复验已更新
- [x] 主会话签字 → Finish
