# Plan 质检报告 — B3V-REG (Agent-2)

> **Worktree:** `C:/Users/Guang/Desktop/quant-monitor-desk-wt-b3v-reg`  
> **Plan:** `.trellis/tasks/round3v-registry-manifest-consistency/DEBT.plan.md`  
> **Playbook:** `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.6 / §3.8 / §3.9 / §3.10  
> **Manifest:** `B3V-C05` · **Card:** `B02_05_migration_registry_and_manifest_consistency.md`  
> **Date:** 2026-06-28（WAVE0 §0.2 粒度刷新复检）

---

## Verdict

**PASS_FOR_PLAN_FREEZE**

Plan 已对齐 WAVE0 INDEX 2026-06-28：整卡 1 GitHub issue（REG-ISSUE-1）；垂直切片 REG-BOOT/01/02 + DOC-ALL；`check_docs_specs_indexed.py` exit 0。

---

## §3.8 Checklist（Agent-2）

| 项 | 结果 | 说明 |
|---|---|---|
| §3.1 + §3.6 每行入 DEBT.plan | PASS | §3.6 九行路径均有 §3.6 表或切片落点；§3.1 经 Source of truth + §3.10 底座行覆盖 |
| `authority_graph.yaml` | PASS | §3.10 行：本切片无新 backend 包 |
| `GLOBAL_TASK_TEMPLATE.md` 15 节 | PASS | Vertical slices + Boundary 展开 B02_05 §1–8 |
| `BATCH_3V_HARDENING_RULES.md` §3–§7 + §2.5/§2.6 | PASS | Boundary Forbidden + TDD + §7 垂直切片；Blockers 引用 §4 debt-lite TDD |
| 任务卡 §3 必读无缺口 | PASS | B02_05 §3 全路径在 DEBT；额外补 `AUDIT_DEFERRED`、`MIGRATION_008_PLAN`、`test_schema_contract` |
| debt slices 表已冻结 | PASS | REG-BOOT/01/02 + DOC-ALL（WAVE0 §0.2） |
| 每个 owned `VR-*` 有 closure / re-defer | PASS | 见 §3.9 VR 追溯 |
| `check_docs_specs_indexed.py` exit 0 | PASS | 2026-06-28 worktree 实测 exit 0 |
| `BATCH_3V_SELF_CHECK.md` PASS_FOR_DISPATCH | PASS | 批次级；与本 Plan 内容一致 |
| 遗漏项写回 DEBT 并修复 | PASS | DEBT 内嵌 §3.10 自检 + 本报告复检 |

---

## §3.9 追溯审计

### 1. Playbook §3.6 → DEBT.plan 索引行

| Playbook §3.6 路径 | DEBT.plan 落点 | 结果 |
|---|---|---|
| `backend/app/db/migrations/009_status_check_constraints.sql` | §3.6 → Slice REG-01 | OK |
| `docs/schema/MIGRATION_COVERAGE.md` | §3.6 → Slice REG-01 | OK |
| `README.md` · `MANIFEST.json` · `docs/quality/final_package_rules.md` | §3.6 → Slice DOC-01/02 | OK |
| `scripts/check_manifest_files.py` · `tests/test_manifest_files_check.py` | §3.6 → Slice DOC-03 | OK |
| `tests/test_unresolved_item_task_coverage.py` | §3.6 → Merge gate / coordinator | OK |
| `docs/quality/quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | §3.6 → VR 路由 | OK |

### 2. Owned `VR-*` 三联（Source ID → AC → verification）

**`VR-REG-001`**

| Slice | Source ID | AC（摘要） | Verification |
|---|---|---|---|
| REG-01 | `B02-REG-01` | 009 覆盖矩阵 + 更新 MIGRATION_COVERAGE / MIGRATION_008_PLAN | `pytest test_schemaContract_includesStatusCheckConstraints` + `research/migration-009-coverage-matrix.md` |
| REG-02 | `B02-REG-02` | proposed registry delta（主会话闭合） | `execute-evidence/REG-02-proposed-registry-delta.md`；coordinator 后 optional test green |

**`VR-DOC-001`**

| Slice | Source ID | AC（摘要） | Verification |
|---|---|---|---|
| DOC-01 | `B02-DOC-01` | restore-or-replace `FINAL_AUDIT_REPORT.md` | restore `416e74bc` + `check_manifest_files.py --verify-hash` exit 0 |
| DOC-02 | `B02-DOC-02` | README/MANIFEST/rules/allowlist 对齐 | grep 零矛盾 + `check_manifest_files.py` exit 0 |
| DOC-03 | `B02-DOC-03` | manifest checker TDD | `pytest test_manifest_files_check.py` + RED/GREEN evidence |

VR 关账表（Proposed registry deltas § VR-* closure）与上表一致。

### 3. 负向边界（§2.6 Must not own + §8.5 未改什么）

| 来源 | DEBT.plan 落点 | 结果 |
|---|---|---|
| Playbook §2.6 B3V-REG：无证明重写 009 | Forbidden 表 | OK |
| Playbook §2.6：伪造 FINAL_AUDIT_REPORT | Forbidden 表 | OK |
| Manifest C05 Must not own：rewrite 009 without proof | Forbidden 表 | OK |
| Playbook §8.5：validation_gate / RawStore / sync / layer5 / production DB | §「未改什么」+ Forbidden | OK |
| Registry 三件套直接 commit | Forbidden + REG-02 仅 proposed | OK |

### 4. 垂直切片（§7 debt-lite + §3.9）

| Slice | VR | 子 AC | 水平合并？ |
|---|---|---|---|
| REG-01 | VR-REG-001 | B02-REG-01 | 否 |
| REG-02 | VR-REG-001 | B02-REG-02 | 否 |
| DOC-01 | VR-DOC-001 | B02-DOC-01 | 否 |
| DOC-02 | VR-DOC-001 | B02-DOC-02 | 否 |
| DOC-03 | VR-DOC-001 | B02-DOC-03 | 否 |

每行单一可测子 AC；REG 与 DOC 未在同一 slice 水平关账。符合 Hardening §7。

### 5. DOC-01 restore-or-replace 完整性

| 要素 | 状态 |
|---|---|
| 专节「FINAL_AUDIT_REPORT restore-or-replace」 | 有（hash、416e74bc、fallback、Done gate） |
| Vertical slice DOC-01 三联 | 有 |
| `research/final-audit-report-restore-or-replace.md` | 有（git 历史、hash 匹配、禁止伪造） |
| 规划期 missing 文档化 | 有（Blockers #3） |

### 6. DOC-03 在 restore 前（Execute order）

```text
REG-01 → REG-02 → DOC-03 → DOC-01 restore → DOC-02 → full pytest
```

DOC-03（TDD / manifest checker）在 DOC-01 restore **之前** — 顺序合理，符合 §5.1「manifest checker test before manifest row edits」与 Hardening §4 debt-lite TDD。

### 7. Research 矩阵（三份）

| 文件 | 对齐切片 | 结果 |
|---|---|---|
| `research/migration-009-coverage-matrix.md` | REG-01 / VR-REG-001 | OK |
| `research/final-audit-report-restore-or-replace.md` | DOC-01 / VR-DOC-001 | OK |
| `research/manifest-doc-crosscheck.md` | DOC-02/03 / VR-DOC-001 | OK |

---

## §3.10 Plan 质检输出表

| 路径 | 已入 DEBT.plan | 摘要一句 | 遗漏风险 |
|---|---|---|---|
| `agent-toolchain.md` | §Source + §3.6 Boot | GitNexus/codebase-memory 路由 | 无 |
| `round3-repair-debt-worktree-plan.md` Phase 8D | §Source | debt-lite 切片与 merge gate | 无 |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.1 | §Source + Boundary | 共用底座索引 | 无 |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.6 | §3.6 表 | REG 分支必读全文 | 无 |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §5.1 | §Source track | debt-lite 流水线 | 无 |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §2.6 / §8.5 | Boundary + §未改什么 | Must not own + 负向边界 | 无 |
| `BATCH_3V_HARDENING_RULES.md` §3–§7 | Boundary + TDD + Execute order | 硬停/TDD/§7 垂直切片 | 无 |
| `BATCH_3V_TASK_CARD_MANIFEST.md` §3 C05 | §Source + Boundary | 分支 allowed/forbidden | 无 |
| `B02_05_migration_registry_and_manifest_consistency.md` | Vertical slices | 五子 AC 映射 REG/DOC | 无 |
| `009_status_check_constraints.sql` | REG-01 | 009 覆盖矩阵源 | 无 |
| `specs/schema/schema.sql` | REG-01 | CHECK 契约对照 | 无 |
| `MIGRATION_COVERAGE.md` | REG-01 | 陈旧 PARTIAL 待修 | 无 |
| `MIGRATION_008_PLAN.md` | REG-01 | stale narrative fix | 无 |
| `AUDIT_DEFERRED_REGISTRY.md` | REG-02 proposed | 不直接 commit | 无 |
| `UNRESOLVED_ISSUES_REGISTRY.md` | REG-02 proposed | 不直接 commit | 无 |
| `RESOLVED_ISSUES_REGISTRY.md` | REG-02 proposed | 不直接 commit | 无 |
| `README.md` / `MANIFEST.json` | DOC-01/02 | restore-or-replace 一致性 | 无 |
| `docs/quality/final_package_rules.md` | DOC-02 | 包规则对齐 | 无 |
| `specs/contracts/release_cleanup_allowlist.yaml` | DOC-02 | allowlist 对齐 | 无 |
| `FINAL_AUDIT_REPORT.md` | DOC-01 专节 | 规划期 missing；restore 路径冻结 | 无 |
| `scripts/check_manifest_files.py` | DOC-03 | manifest gate | 无 |
| `tests/test_manifest_files_check.py` | DOC-03 | TDD RED→GREEN | 无 |
| `tests/test_unresolved_item_task_coverage.py` | Merge gate | 主会话闭合后期望集 | 无 |
| `tests/test_schema_contract.py` | REG-01 | schema CHECK 证据 | 无 |
| `quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | §Source | VR-REG-001 / VR-DOC-001 路由 | 无 |
| `specs/context/authority_graph.yaml` | §3.10 | 无新 backend 包 | 无 |
| `GLOBAL_TASK_TEMPLATE.md` | Vertical slices + Boundary | 卡片 §1–8 展开 | 无 |
| `BATCH_3V_SELF_CHECK.md` | Blockers | FINAL_AUDIT gap 已纳入 Plan | 无 |
| `research/migration-009-coverage-matrix.md` | REG-01 evidence | 矩阵已落盘 | 无 |
| `research/final-audit-report-restore-or-replace.md` | DOC-01 evidence | restore 决策已落盘 | 无 |
| `research/manifest-doc-crosscheck.md` | DOC-02/03 baseline | 工具与命令基线 | 无 |
| `MIGRATION_MAP.md` / `check_docs_specs_indexed.py` | Blockers #1 | stale ref；主会话 fix；非 REG allowed | 无 |

---

## 阻塞项

**无 Plan 级阻塞项。**

---

## 主会话回报（摘要）

| 字段 | 值 |
|---|---|
| **Verdict** | **PASS_FOR_EXECUTE** |
| **阻塞项** | 无 |
| **Execute 提醒** | integration 前主会话须 green `check_docs_specs_indexed.py`；DOC-01 restore 为 Done 硬门禁 |
