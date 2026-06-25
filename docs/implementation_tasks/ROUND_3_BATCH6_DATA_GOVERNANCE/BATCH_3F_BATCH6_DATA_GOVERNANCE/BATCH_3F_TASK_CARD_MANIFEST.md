# Batch 3F Task Card Manifest

> Batch: Round 3F / Batch6 Data Governance & Ops.  
> Source of truth: `PROJECT_IMPLEMENTATION_ROADMAP.md` Round 3F.  
> Purpose: centralize Batch6 ownership so open items do not remain scattered across Round3 map, unresolved registry, and Wave-B pending registries.

---

## 1. Segment ownership（八路并行）

| Playbook ID | 轨道          | Segment                    | Branch（canonical）                                  | Owns                                                                         | Primary roadmap rows                          |
| ----------- | ------------- | -------------------------- | ---------------------------------------------------- | ---------------------------------------------------------------------------- | --------------------------------------------- |
| **B3F-MIG** | **complex**   | 3F.1 Migration residuals   | `feature/round3f-migration-residual-checks`          | 009 residual, 008 plan routing, migration coverage                           | `R3F-MIG-01..06`                              |
| **B3F-CLI** | **complex**   | 3F.2 CLI / ops entrypoints | `feature/round3-qmd-data-cli`                        | `qmd data`, console scripts, authorized staging E2E runbook                  | `R3F-CLI-01..05`                              |
| **B3F-SH**  | **complex**   | 3F.3 Source health         | `feature/round3-source-health-and-quality-runners`   | source health table/writer, data quality runners, live FRED primary tracking | `R3F-SH-01..07`                               |
| **B3F-BR**  | **complex**   | 3F.4 Backfill/reconcile    | `feature/round3-backfill-reconcile-parity`           | reconcile, backfill parity, orchestrator registry, R3-PARTIAL-4/5 closeout   | `R3F-BR-01..05`                               |
| **B3F-HYG** | **complex**   | 3F.5 Hygiene/perf          | `chore/round3-batch6-technical-debt`                 | C901, packaging, adapter/storage port, ResourceGuard, perf, CI handoff       | `R3F-HYG-01..13`                              |
| **B3F-LIN** | **complex**   | 3F.6 Lineage/Layer3        | `fix/round3f-batch6-lineage-layer3-registry-closure` | `ADV-R3X-LINEAGE-001`, `R3Y-LINEAGE-VR-001`, `R3-B6-021-O-01/02`             | `R3F-LIN-01..03`, `R3F-L3-01..02`             |
| **B3F-REG** | **debt-lite** | Registry closeout          | `chore/round3f-registry-batch-closeout`              | 三 registry + COVERAGE 收口；已 RESOLVED verify-only                         | `R3F-LIN-03`, `R3F-BR-05`, `R3F-HYG-11/13` 等 |
| **B3F-CI**  | **debt-lite** | CI gate handoff            | `chore/round3-ci-gate-hardening`                     | verification command matrix；PROMPT_05                                       | `R3F-HYG-12`                                  |

**轨道统计：** 6 complex + 2 debt-lite = **8 路并行**。派发表 SSOT：`BATCH_3F_COORDINATOR_PLAYBOOK.md` §3.0。

---

## 2. High-priority open items newly centralized

| Item                          | Prior scattered location                   | Batch 3F owner                         |
| ----------------------------- | ------------------------------------------ | -------------------------------------- |
| `ADV-R3X-LINEAGE-001`         | `UNRESOLVED_ISSUES_REGISTRY`, `待修复清单` | 3F.6 / `R3F-LIN-01`                    |
| `R3Y-LINEAGE-VR-001`          | same                                       | 3F.6 / `R3F-LIN-02`                    |
| `R3-B6-021-O-01`              | `ROUND3_BATCH6_021_PENDING_FIX_REGISTRY`   | 3F.6 / `R3F-L3-01`                     |
| `R3-B6-021-O-02`              | `ROUND3_BATCH6_021_PENDING_FIX_REGISTRY`   | 3F.6 / `R3F-L3-02`                     |
| `B2.5-O-05` live FRED primary | Batch01 FRED card + registries             | 3F.3 / `R3F-SH-06`                     |
| `R2-RISK-2`                   | 023/016 task notes + registries            | 3F.5 / `R3F-HYG-10`                    |
| `R2-RISK-3`                   | old map/unresolved vs resolved conflict    | 3F.5 / `R3F-HYG-11` registry reconcile |
| `R3-AUDIT-DEF-01/02/03`       | early close plan / unresolved coverage     | 3F.2 + 3F.5                            |
| `R3-PARTIAL-4`                | ADR-023 + unresolved registry              | 3F.4 / `R3F-BR-05` registry closeout   |
| `R3-PARTIAL-5`                | resolved but old roadmap row active        | 3F.1/3F.4 regression guard only        |

---

## 3. Already-resolved items that must not be reimplemented

- `R2-RISK-3` appears in older unresolved/map contexts, but `RESOLVED_ISSUES_REGISTRY.md` records fail-closed `WriteManager.UNSUPPORTED_MODES` closure. Batch 3F handles registry consistency only unless latest tests prove regression.
- `R3-AUDIT-DEF-03` appears in older unresolved coverage, but `RESOLVED_ISSUES_REGISTRY.md` records per-subdir scan-cap tests. Batch 3F handles registry consistency only unless regression appears.
- `R3-PARTIAL-5` crash-window path A is closed by B3V crash/recovery tests. Batch 3F must not reopen it as active implementation unless regression appears.

---

## 4. Non-negotiable hard constraints tracked but not newly opened

- `R3-B2.75-REQ2-EM` remains deferred; do not close with TDX/Sina/sidecar evidence.
- `R3-PROMPT14-AKSHARE-VAL-01` remains validation-only and must not promote AkShare to Primary.
- staged-only evidence and sandbox evidence are not production-live readiness.
