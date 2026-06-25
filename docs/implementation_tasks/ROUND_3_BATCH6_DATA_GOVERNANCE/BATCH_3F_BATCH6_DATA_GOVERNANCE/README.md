# Batch 3F — Batch6 Data Governance & Ops

> Canonical executable entrypoint after Batch 3V.  
> Roadmap: `PROJECT_IMPLEMENTATION_ROADMAP.md` → Round 3F.  
> Current status: next executable batch after `master @ 2aeb6f0`.  
> Production posture: no production clean write; no default live source enablement; no full-market/full-history scans.

---

## 1. Why this batch exists

Round 3D/3E/3V completed important staged, sandbox, and verified-audit work, but several open/deferred items still belong to Batch6. This package prevents them from being scattered across old registries, Wave-B pending lists, and historical Round3 map sections.

The project planning source of truth is now:

1. `PROJECT_IMPLEMENTATION_ROADMAP.md` Round 3F.
2. This Batch 3F package.
3. Registry files only as evidence/closure tracking, not as competing forward plans.

---

## 2. Companion files

| File                                            | Purpose                                                           |
| ----------------------------------------------- | ----------------------------------------------------------------- |
| `BATCH_3F_TASK_CARD_MANIFEST.md`                | Batch task/card manifest and item ownership（八路 Playbook ID）。 |
| `BATCH_3F_COORDINATOR_PLAYBOOK.md`              | **主会话协调手册**：六复杂 + 两精简、文件锁、合并顺序、§8 验收。  |
| `BATCH_3F_PLAYBOOK_ADVERSARIAL_AUDIT.report.md` | Playbook 对抗性审计与修补闭环索引。                               |
| `BATCH_3F_HARDENING_RULES.md`                   | Safety constraints inherited by every 3F task.                    |

---

## 3. Batch segments

| Segment | Roadmap section                                  | Owns                                                                             |
| ------- | ------------------------------------------------ | -------------------------------------------------------------------------------- |
| 3F.1    | Migration 009 residual + 008 plan items          | migration/coverage/registry residuals                                            |
| 3F.2    | `qmd data` CLI & ops entrypoints                 | CLI, packaging, authorized staging E2E runbook                                   |
| 3F.3    | Source Health & Quality Runners                  | source health, live FRED primary re-defer/closure, hard-constraint tracking      |
| 3F.4    | Backfill / Reconcile / Recovery Parity           | reconcile/backfill/orchestrator parity and registry closeout                     |
| 3F.5    | Technical Debt / Packaging / Performance Hygiene | ResourceGuard, perf, adapter/storage, contract drift, CI handoff, Wave-B hygiene |
| 3F.6    | Lineage / Layer3 Hygiene Registry Closure        | ADV-R3X lineage, R3Y VR binding, R3-B6-021 O-01/O-02                             |

---

## 4. Hard boundaries

Batch 3F must not:

- enable production clean write,
- claim production-live readiness,
- default-enable FRED/TDX/QMT/xqshare/Yahoo,
- close `B2.5-O-05` without user-authorized FRED live primary evidence,
- close Eastmoney/AkShare validation failures via TDX/Sina/sidecar evidence,
- reopen items already RESOLVED except for registry consistency checks,
- treat 3D.3 partial hygiene as full lineage registry closure.
