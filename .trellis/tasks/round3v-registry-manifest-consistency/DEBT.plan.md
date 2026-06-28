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
| Playbook | `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.1 + §3.6 + §5.1 + §2.5/§2.6 |
| Hardening | `BATCH_3V_HARDENING_RULES.md` §1–§7, §4 debt-lite TDD |
| Phase 8D | `.trellis/spec/guides/complex-task-planning-protocol.md` Phase 8D + `round3-repair-debt-worktree-plan.md` §5–§8 |
| Wave 0 INDEX | `WAVE0_BATCH3V_TO_ISSUES_INDEX.md` §0.2 + §1（2026-06-28 粒度 quiz） |
| Vertical slices SSOT | `research/vertical-slices.md` |
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

### Playbook §2.6 摘要（SSOT 抄录）

| Owns（可写） | Must not own |
|---|---|
| migration 009 覆盖矩阵、manifest/doc/registry 对齐 | 无证明重写 migration 009；伪造 `FINAL_AUDIT_REPORT` |

完整以任务卡 §4 + `BATCH_3V_TASK_CARD_MANIFEST.md` §3 C05 为准；上表为 playbook §2.6 摘要。

### Forbidden files / actions

| Must not own | Reason |
|---|---|
| `validation_gate.py`, RawStore, sync runtime, `layer5_evidence/**` | Playbook §2.5 / §8.5 负向边界 |
| 无证明重写 migration 009 | B02_05 §4 · §2.6 |
| 伪造 `FINAL_AUDIT_REPORT` 内容 | Hardening §1 / B02_05 §4 · §2.6 |
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
| `README.md` · `MANIFEST.json` · `final_package_rules.md` · `release_cleanup_allowlist.yaml` | Slice DOC-ALL |
| `scripts/check_manifest_files.py` · `tests/test_manifest_files_check.py` | Slice DOC-ALL |
| `WAVE0_BATCH3V_TO_ISSUES_INDEX.md` §1 | GitHub issue + 票内 checklist |
| `tests/test_unresolved_item_task_coverage.py` | Merge gate / coordinator |
| `docs/quality/quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | VR 路由 |
| `docs/schema/MIGRATION_008_PLAN.md` | REG-01 stale narrative fix |
| `tests/test_schema_contract.py` | REG-01 closure evidence |
| `agent-toolchain.md` · `round3-repair-debt-worktree-plan.md` Phase 8D | Boot |

Research detail: `research/vertical-slices.md`, `research/wave0-index-ruling-refresh.md`, `research/migration-009-coverage-matrix.md`, `research/final-audit-report-restore-or-replace.md`, `research/manifest-doc-crosscheck.md`.

---

## GitHub issue（整卡 1 票 · WAVE0 §0.2 2026-06-28）

| Issue | 标题 | 范围 |
| ----- | ---- | ---- |
| **REG-ISSUE-1** | `[B3V-REG] migration 009 + manifest/doc 树对齐 + checker` | `VR-REG-001` + `VR-DOC-001` 全卡 |

票内 checklist 见 `research/vertical-slices.md`；**DOC-01/02/03 不拆独立 issue**。

---

## Vertical slices

> **Rule（WAVE0 §1）：** 票内竖条 REG-BOOT/01/02 + DOC-ALL；`VR-REG-001` 与 `VR-DOC-001` 同属 REG-ISSUE-1，禁止无分步证据的水平关账。  
> **SSOT 镜像：** `research/vertical-slices.md`

| Slice ID | VR-* | Source ID / AC | Allowed | Forbidden | Verification | Evidence path |
|---|---|---|---|---|---|---|
| **REG-BOOT** | `VR-REG-001` | 基线矩阵 — migration 009 ↔ `schema.sql` ↔ registry 现状断言 | `research/`, `009_status_check_constraints.sql`, `schema.sql`（只读对照） | Rewrite 009; registry commit | Matrix rows in `research/migration-009-coverage-matrix.md` | `research/migration-009-coverage-matrix.md` |
| **REG-01** | `VR-REG-001` | `B02-REG-01` — Coverage matrix; update `MIGRATION_COVERAGE.md` + `MIGRATION_008_PLAN.md` | `MIGRATION_COVERAGE.md`, `MIGRATION_008_PLAN.md`, `research/` | Rewrite 009 SQL; registry direct commit | `uv run pytest tests/test_schema_contract.py::test_schemaContract_includesStatusCheckConstraints -q` | `execute-evidence/REG-01-matrix.txt` |
| **REG-02** | `VR-REG-001` | `B02-REG-02` — Proposed registry deltas; narrow re-defer gaps | `research/`, `execute-evidence/` delta markdown only | Bulk registry rewrite commit on branch | Main session applies deltas | `execute-evidence/REG-02-proposed-registry-delta.md` |
| **DOC-ALL** | `VR-DOC-001` | `B02-DOC-01..03` **合并** — restore/replace + doc tree + manifest checker TDD | `FINAL_AUDIT_REPORT.md`, README, MANIFEST, final_package_rules, allowlist, `check_manifest_files.py`, `test_manifest_files_check.py` | Fake content; manifest row before test | `check_manifest_files.py` exit 0; `pytest tests/test_manifest_files_check.py -q` | `execute-evidence/DOC-01-restore.txt`, `DOC-02-doc-sync.txt`, `DOC-03-red.txt`, `DOC-03-green.txt` |

### DOC-ALL 票内 checklist（非独立 issue）

| 子步 | 原 ID | AC |
| ---- | ----- | -- |
| 1 | `B02-DOC-01` | Restore `FINAL_AUDIT_REPORT.md` from `416e74bc`（preferred）或 coordinator 批准 replace |
| 2 | `B02-DOC-02` | README / MANIFEST / rules / allowlist 与文件树一致 |
| 3 | `B02-DOC-03` | Manifest checker TDD 绿；`--verify-hash` after restore |

### Execute order

```text
REG-BOOT → REG-01 → REG-02 → DOC-ALL（REG-02 后可并行起步）→ uv run pytest -q
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
| Docs index | `uv run python scripts/check_docs_specs_indexed.py` → exit 0（2026-06-28 worktree 已验证） |
| Full suite | `uv run pytest -q` |
| GitNexus | `impact()` before symbol edits; `detect_changes()` before commit |
| Registry | Proposed delta file only — no direct三件套 commit |
| Adversarial | `agents/audit-adversarial-authority.md` post-Execute |
| DB | No production mutation proof: N/A |

---

## §3.10 Plan 质检表

| 路径 | 已入 DEBT.plan | 摘要一句 | 遗漏风险 |
|---|---|---|---|
| `agent-toolchain.md` | §Source + §3.6 Boot | GitNexus/codebase-memory 路由已读 | 无 |
| `round3-repair-debt-worktree-plan.md` Phase 8D | §Source | debt-lite 切片/merge gate 对齐 | 无 |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.1 | §Source + Boundary | 共用底座索引 | 无 |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.6 | §3.6 表 | REG 分支必读全文（playbook 六行路径） | 无 |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §5.1 | §Source track | debt-lite 流水线 | 无 |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §2.6 / §8.5 | Boundary + §未改什么 | Must not own + 负向边界 | 无 |
| `BATCH_3V_HARDENING_RULES.md` §3–§7 | Boundary + TDD + Execute order | 硬停/TDD/§7 垂直切片 | 无 |
| `BATCH_3V_TASK_CARD_MANIFEST.md` §3 C05 | §Source + Boundary | 分支 allowed/forbidden | 无 |
| `B02_05_migration_registry_and_manifest_consistency.md` | Vertical slices | 五子 AC → REG-BOOT/01/02 + DOC-ALL | 无 |
| `WAVE0_BATCH3V_TO_ISSUES_INDEX.md` §0.2 + §1 | GitHub issue + slices | 整卡 1 issue；DOC-ALL 粒度 quiz | 无 |
| `backend/app/db/migrations/009_status_check_constraints.sql` | REG-01 | 009 覆盖矩阵源 | 无 |
| `specs/schema/schema.sql` | §3.6 → REG-01 | CHECK 契约对照 | 无 |
| `docs/schema/MIGRATION_COVERAGE.md` | REG-01 | 陈旧 PARTIAL 待修 | 无 |
| `docs/schema/MIGRATION_008_PLAN.md` | REG-01 | stale narrative fix | 无 |
| `docs/AUDIT_DEFERRED_REGISTRY.md` | REG-02 proposed | 三件套之一；不直接 commit | 无 |
| `docs/UNRESOLVED_ISSUES_REGISTRY.md` | REG-02 proposed | 三件套之二；不直接 commit | 无 |
| `docs/RESOLVED_ISSUES_REGISTRY.md` | REG-02 proposed | 三件套之三；不直接 commit | 无 |
| `README.md` | DOC-ALL | restore-or-replace 叙事一致 | 无 |
| `MANIFEST.json` | DOC-ALL | 存在性/哈希与文件树一致 | 无 |
| `docs/quality/final_package_rules.md` | DOC-ALL | 包规则对齐 | 无 |
| `specs/contracts/release_cleanup_allowlist.yaml` | DOC-ALL | allowlist 对齐 | 无 |
| `FINAL_AUDIT_REPORT.md` | DOC-ALL 专节 + checklist §1 | restore `416e74bc` 路径已冻结 | 无 |
| `scripts/check_manifest_files.py` | DOC-ALL checklist §3 | manifest gate；Done exit 0 | 无 |
| `tests/test_manifest_files_check.py` | DOC-ALL checklist §3 | TDD RED→GREEN | 无 |
| `tests/test_schema_contract.py` | REG-01 | schema CHECK closure 证据 | 无 |
| `tests/test_unresolved_item_task_coverage.py` | Merge gate | 主会话闭合后期望集 | 无 |
| `docs/quality/quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | §Source + §3.6 | VR-REG-001 / VR-DOC-001 路由 | 无 |
| `research/vertical-slices.md` | Vertical slices SSOT | REG-BOOT/01/02 + DOC-ALL | 无 |
| `research/wave0-index-ruling-refresh.md` | 裁决追溯 | 2026-06-28 粒度刷新对照 | 无 |
| `research/migration-009-coverage-matrix.md` | REG-BOOT/01 | 矩阵已落盘 | 无 |
| `research/final-audit-report-restore-or-replace.md` | DOC-ALL | restore 决策已落盘 | 无 |
| `research/manifest-doc-crosscheck.md` | DOC-ALL | 工具与命令基线 | 无 |
| `specs/context/authority_graph.yaml` | §3.10 | 本切片无新 backend 包 | 无 |
| `GLOBAL_TASK_TEMPLATE.md` | Vertical slices + Boundary | 卡片 §1–8 已展开 | 无 |
| `BATCH_3V_SELF_CHECK.md` | Blockers | PASS_FOR_DISPATCH；FINAL_AUDIT gap 已纳入 Plan | 无 |
| `scripts/check_docs_specs_indexed.py` | Merge gate | 2026-06-28 worktree exit 0 | 无 |

---

## Blockers / caveats

1. **Registry 主会话批闭合** — `VR-REG-001` / `VR-DOC-001` 分支侧已完成 proposed delta + Execute 证据；**主会话**须应用 `execute-evidence/REG-02-proposed-registry-delta.md` 与 `repair-evidence/registry-ready-for-coordinator.md` 后更新 `EXPECTED_UNRESOLVED_IDS`。
2. **codebase-memory MCP** — worktree 路径未索引；GitNexus + 直读已交叉核实；见 research。
3. **Plan 粒度刷新（2026-06-28）** — WAVE0 §0.2 整卡 1 issue；DOC-01/02/03 合并为 DOC-ALL；不影响已落地 Execute 证据路径。
4. **`check_docs_specs_indexed.py`** — 2026-06-28 worktree 实测 **exit 0**；非 Plan 阻塞。

---

## 未改什么（负向边界 · §8.5）

- `validation_gate.py`, RawStore, sync orchestration/runners, `layer5_evidence/**` runtime
- migration 009 SQL semantics (unless RED test proves bug)
- production DuckDB state
- Registry 三件套直接闭合行
