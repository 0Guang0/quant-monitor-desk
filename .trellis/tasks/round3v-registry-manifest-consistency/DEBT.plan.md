# Repair/Debt Lite Plan — B3V-REG (`fix/round3v-registry-manifest-consistency`)

> **Track:** debt-lite §5.1 · **Manifest:** `B3V-C05` · **Card:** `B02_05_migration_registry_and_manifest_consistency.md`  
> **Owns:** `VR-REG-001`, `VR-DOC-001` · **Model:** `composer-2.5`  
> **Worktree:** `C:/Users/Guang/Desktop/quant-monitor-desk-wt-b3v-reg`  
> **Trellis task-dir:** `.trellis/tasks/round3v-registry-manifest-consistency`

---

## Source of truth

| Field | Value |
|---|---|
| Audit index | `docs/quality/quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` |
| Playbook | `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.1 + §3.6 + §5.1 |
| Hardening | `BATCH_3V_HARDENING_RULES.md` §1–§7, §4 debt-lite TDD |
| Phase 8D | `.trellis/spec/guides/round3-repair-debt-worktree-plan.md` §5–§8 |
| Base branch | `master` (post Batch 01) |
| Target branch | `fix/round3v-registry-manifest-consistency` |
| Owner agent | B3V-REG Execute agent |
| Registry close | **主会话批处理** — 本分支仅 proposed delta + evidence |

---

## Boundary

### Allowed files

| Path | Purpose |
|---|---|
| `docs/schema/MIGRATION_COVERAGE.md` | 009 coverage matrix reconcile |
| `README.md` | FINAL_AUDIT / manifest narrative (if replace path) |
| `MANIFEST.json` | Only if replace path or hash refresh after restore |
| `docs/quality/final_package_rules.md` | Doc consistency |
| `specs/contracts/release_cleanup_allowlist.yaml` | Allowlist consistency |
| `FINAL_AUDIT_REPORT.md` | **Restore only** (from `416e74bc`) or coordinator-approved replace |
| `backend/app/db/migrations/009_status_check_constraints.sql` | **Only** if test proves migration wrong |
| `scripts/check_manifest_files.py` | Manifest gate |
| `tests/test_manifest_files_check.py` | TDD wrapper |
| `tests/test_unresolved_item_task_coverage.py` | Only if registry test expectations need sync **after** main-session close (prefer coordinator) |
| `.trellis/tasks/round3v-registry-manifest-consistency/**` | Plan / research / execute-evidence |

### Forbidden files / actions

| Must not own | Reason |
|---|---|
| `validation_gate.py`, RawStore, sync runtime, `layer5_evidence/**` | Playbook §2.5 / §8.5 负向边界 |
| 无证明重写 migration 009 | B02_05 §4 |
| 伪造 `FINAL_AUDIT_REPORT` 内容 | Hardening §1 / B02_05 §4 |
| 直接 commit 闭合 `UNRESOLVED` / `RESOLVED` / `AUDIT_DEFERRED` 行 | Manifest §4 — proposed delta only |
| production DB 写入 / live fetch | Hardening §3 |
| `layer5_evidence/**` runtime | §2.5 |

### Production / data boundary

- Reconcile **migration files + schema.sql + docs** only.
- Do **not** claim production DuckDB applied 009 without read-only `db-inspect` evidence (out of scope unless coordinator adds).

---

## §3.6 必读索引（DEBT.plan 摘要）

| 路径 | Plan 落点 |
|---|---|
| `backend/app/db/migrations/009_status_check_constraints.sql` | Slice REG-01 |
| `specs/schema/schema.sql` | Slice REG-01 matrix |
| `docs/schema/MIGRATION_COVERAGE.md` | Slice REG-01 |
| `docs/AUDIT_DEFERRED_REGISTRY.md` | Slice REG-02 proposed delta |
| `docs/UNRESOLVED_ISSUES_REGISTRY.md` | Slice REG-02 proposed delta |
| `docs/RESOLVED_ISSUES_REGISTRY.md` | Slice REG-02 proposed delta |
| `README.md` · `MANIFEST.json` · `final_package_rules.md` · `release_cleanup_allowlist.yaml` | Slice DOC-01/02 |
| `scripts/check_manifest_files.py` · `tests/test_manifest_files_check.py` | Slice DOC-03 |
| `tests/test_unresolved_item_task_coverage.py` | Merge gate / coordinator |
| `docs/quality/quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | VR 路由 |
| `docs/schema/MIGRATION_008_PLAN.md` | REG-01 stale narrative fix |
| `tests/test_schema_contract.py` | REG-01 closure evidence |
| `agent-toolchain.md` · `round3-repair-debt-worktree-plan.md` Phase 8D | Boot |

Research detail: `research/migration-009-coverage-matrix.md`, `research/final-audit-report-restore-or-replace.md`, `research/manifest-doc-crosscheck.md`.

---

## Vertical slices

> **Rule:** 每行一个 `VR-*`；子步骤在 Execute 内垂直推进，禁止水平合并关账。

| Slice ID | VR-* | Source ID / AC | Allowed | Forbidden | Verification | Evidence path |
|---|---|---|---|---|---|---|
| **REG-01** | `VR-REG-001` | `B02-REG-01` — Build migration 009 coverage matrix; update `MIGRATION_COVERAGE.md` + `MIGRATION_008_PLAN.md` narrative to match `009_status_check_constraints.sql` and `schema.sql` | `MIGRATION_COVERAGE.md`, `MIGRATION_008_PLAN.md` (doc-only), `research/` | Rewrite 009 SQL; registry direct commit | `uv run pytest tests/test_schema_contract.py::test_schemaContract_includesStatusCheckConstraints -q`; matrix in `research/migration-009-coverage-matrix.md` updated if drift | `execute-evidence/REG-01-matrix.txt` |
| **REG-02** | `VR-REG-001` | `B02-REG-02` — Propose registry deltas: move 009-covered CHECKs to RESOLVED; re-defer only `manual_review_queue.priority`, `fetch_log`/`manual_review_queue` `SELECT *` (A9-P3-01 subset) | `research/` proposed delta markdown only | Bulk registry rewrite commit on branch | Main session applies deltas; optional `tests/test_unresolved_item_task_coverage.py` green after coordinator | `execute-evidence/REG-02-proposed-registry-delta.md` |
| **DOC-01** | `VR-DOC-001` | `B02-DOC-01` — **Restore-or-replace** `FINAL_AUDIT_REPORT.md` | `FINAL_AUDIT_REPORT.md` (restore from `416e74bc`) OR replace artifact + doc refs | Fake content | **Preferred restore:** byte+hash match MANIFEST; `uv run python scripts/check_manifest_files.py --verify-hash` exit 0 | `execute-evidence/DOC-01-restore.txt` |
| **DOC-02** | `VR-DOC-001` | `B02-DOC-02` — Align README / MANIFEST / final_package_rules / allowlist with chosen closeout path | README, MANIFEST, final_package_rules, allowlist | Unreferenced removal | Grep zero stale `FINAL_AUDIT_REPORT` contradictions; `check_manifest_files.py` exit 0 | `execute-evidence/DOC-02-doc-sync.txt` |
| **DOC-03** | `VR-DOC-001` | `B02-DOC-03` — Manifest checker TDD (RED→GREEN if extending) | `check_manifest_files.py`, `test_manifest_files_check.py` | Manifest row edits before test exists | `uv run pytest tests/test_manifest_files_check.py -q`; `uv run python scripts/check_manifest_files.py` exit 0 | `execute-evidence/DOC-03-red.txt`, `DOC-03-green.txt` |

### Execute order

```text
REG-01 → REG-02 (proposed delta only) → DOC-03 (if new assertions) → DOC-01 restore → DOC-02 → full pytest
```

TDD: touching `scripts/check_manifest_files.py` or manifest tests → RED before GREEN per hardening §4.

---

## FINAL_AUDIT_REPORT restore-or-replace（规划期记录）

| Item | Plan decision |
|---|---|
| On-disk state | **Missing** (allowed during Plan) |
| MANIFEST | Lists file + sha256 `b8f003b7…` |
| **Chosen path** | **Restore** from `git show 416e74bc:FINAL_AUDIT_REPORT.md` (4948 B, hash matches MANIFEST) |
| Fallback | Replace with `docs/quality/audits/quant_monitor_desk_verified_audit_report_2026-06-25_v3.md` + update all refs (coordinator approval) |
| Done gate | `check_manifest_files.py` **exit 0** (`--verify-hash` after restore) |
| Forbidden | Fabricate audit prose |

Detail: `research/final-audit-report-restore-or-replace.md`.

---

## Proposed registry deltas（文本 · 主会话批闭合）

> **Do not commit** these rows on the feature branch.

### Move toward RESOLVED (evidence: `009_status_check_constraints.sql` + `test_schemaContract_includesStatusCheckConstraints`)

| ID | Current | Proposed | Evidence |
|---|---|---|---|
| `A9-P1-01` | DEFERRED → migration 008 | **RESOLVED** (subset: `fetch_log.status`, `source_registry.source_type`/`license_type` DB CHECK) | Migration 009 file; schema contract test |
| `A9-P2-02` | DEFERRED → migration 008 | **RESOLVED** (`source_conflict.reconcile_status` CHECK in 009) | Migration 009 lines 127–131 |
| `B2.5-O-06` | DEFERRED (alias A9-P1-01) | **RESOLVED** or merge into A9-P1-01 close | Same as A9-P1-01 |

### Precise re-defer / narrow (remaining gaps)

| ID | Proposed note |
|---|---|
| `A9-P2-01` | **Narrow:** `manual_review_queue.status` + `source_object_type` → RESOLVED via 009; **`priority` CHECK** remains app-layer → keep DEFERRED with owner Round 3F / future migration, closure test: illegal priority insert test or doc ADR |
| `A9-P3-01` | **Narrow:** `source_registry`/`source_conflict` explicit INSERT → RESOLVED in 009; **`fetch_log` + `manual_review_queue` `SELECT *`** in 009 → remain DEFERRED until explicit-column rebuild |
| `R2-RISK-4` | Update text: app-layer CHECK **only** for agreed columns (e.g. `manual_review_queue.priority`); link `MIGRATION_COVERAGE.md` |

### VR-* closure (main session)

| VR ID | Close when |
|---|---|
| `VR-REG-001` | Matrix docs updated + proposed deltas accepted + no contradiction vs 009/schema |
| `VR-DOC-001` | `FINAL_AUDIT_REPORT` restored (or replace complete) + manifest checker exit 0 + tests green |

---

## Merge gate (§6 + §8.5)

| Gate | Command / evidence |
|---|---|
| Targeted tests | `uv run pytest tests/test_unresolved_item_task_coverage.py tests/test_manifest_files_check.py -q` |
| Manifest | `uv run python scripts/check_manifest_files.py` → **exit 0** |
| Docs index | `uv run python scripts/check_docs_specs_indexed.py` → exit 0 (**coordinator** if stale MIGRATION_MAP refs block) |
| Full suite | `uv run pytest -q` |
| GitNexus | `impact()` before symbol edits; `detect_changes()` before commit |
| Registry | Proposed delta file only — no direct三件套 commit |
| Adversarial | `agents/audit-adversarial-authority.md` post-Execute |
| DB | No production mutation proof: N/A |

---

## §3.10 Plan 质检表

| 路径 | 已入 DEBT.plan | 摘要一句 | 遗漏风险 |
|---|---|---|---|
| `agent-toolchain.md` | §Source + Boot | GitNexus/codebase-memory 路由已读 | 无 |
| `round3-repair-debt-worktree-plan.md` Phase 8D | §Source | debt-lite 切片/merge gate 对齐 | 无 |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.1 | §Source + Boundary | 共用底座索引 | 无 |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.6 | §3.6 表 | REG 必读全文摘要 | 无 |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §5.1 | §Source track | debt-lite 流水线 | 无 |
| `BATCH_3V_HARDENING_RULES.md` | Boundary + TDD | 硬停/TDD/registry 规则 | 无 |
| `BATCH_3V_TASK_CARD_MANIFEST.md` §3 C05 | §Source | 分支 allowed/forbidden | 无 |
| `B02_05_*.md` | Vertical slices | 五切片映射 REG/DOC | 无 |
| `009_status_check_constraints.sql` | REG-01 | 009 覆盖矩阵 | 无 |
| `MIGRATION_COVERAGE.md` | REG-01 | 陈旧 PARTIAL 待修 | 无 |
| `schema.sql` | REG-01 | CHECK 契约对照 | 无 |
| `AUDIT_DEFERRED` / `UNRESOLVED` / `RESOLVED` | REG-02 proposed | 不直接 commit | 无 |
| `README` / `MANIFEST` / `final_package_rules` / allowlist | DOC-01/02 | restore-or-replace 一致性 | 无 |
| `check_manifest_files.py` / `test_manifest_files_check.py` | DOC-03 | TDD + Done exit 0 | 无 |
| `test_unresolved_item_task_coverage.py` | Merge gate | 主会话后可能需期望集更新 | 无 |
| `quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | §Source | VR 路由 | 无 |
| `FINAL_AUDIT_REPORT.md` | DOC-01 专节 | 规划期 missing；restore 路径已冻结 | 无 |
| `authority_graph.yaml` | — | 本切片无新 backend 包 | 无 |
| `GLOBAL_TASK_TEMPLATE.md` | Vertical slices + Boundary | 卡片 §1–8 已展开 | 无 |
| `BATCH_3V_SELF_CHECK.md` | Blockers | PASS_FOR_PLANNING；FINAL_AUDIT gap 已纳入 | 无 |

---

## Blockers / caveats

1. **`check_docs_specs_indexed.py` exit 1** — 10 stale `MIGRATION_MAP` references to untracked Round 4/5/Batch6 task docs; **not** in B3V-REG allowed files → merge coordinator runs `loop_maintain.py --fix` or indexes docs on integration branch before Batch 3V Done.
2. **codebase-memory MCP** — project not indexed for worktree path; GitNexus + direct file reads used; documented in research.
3. **`FINAL_AUDIT_REPORT.md` missing** — **not** a Plan blocker (restore path validated); **is** Execute/Done blocker until DOC-01 lands.
4. **Registry test expectations** — `test_unresolved_item_task_coverage.py` still expects `A9-P1-01` open; after main-session RESOLVED, coordinator must update `EXPECTED_UNRESOLVED_IDS` or branch will fail full gate.

---

## 未改什么（负向边界 · §8.5）

- `validation_gate.py`, RawStore, sync orchestration/runners, `layer5_evidence/**` runtime
- migration 009 SQL semantics (unless RED test proves bug)
- production DuckDB state
- Registry 三件套直接闭合行
