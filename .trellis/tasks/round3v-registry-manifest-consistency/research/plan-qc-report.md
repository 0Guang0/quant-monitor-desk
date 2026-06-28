# Plan 质检报告 — B3V-REG (Agent-2)

> **Worktree:** `C:/Users/Guang/Desktop/quant-monitor-desk-wt-b3v-reg`  
> **Plan:** `.trellis/tasks/round3v-registry-manifest-consistency/DEBT.plan.md`  
> **Playbook:** `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.6 / §3.8 / §3.9 / §3.10 / §5.1  
> **Manifest:** `B3V-C05` · **Card:** `B02_05_migration_registry_and_manifest_consistency.md`  
> **Branch:** `fix/round3v-registry-manifest-consistency`  
> **Date:** 2026-06-28（对抗性复检 · WAVE0 §0.2 DOC-ALL 粒度）

---

## Verdict

**PASS_FOR_PLAN_FREEZE**

Plan 已对齐 WAVE0 INDEX §0.2/§1：整卡 1 GitHub issue（REG-ISSUE-1）；垂直切片 REG-BOOT/01/02 + DOC-ALL；registry 三件套仅 proposed delta；`check_docs_specs_indexed.py` exit 0（worktree 实测）。

---

## 对抗性发现与处置

| #   | 发现                                                                                                | 处置                                                                    | 状态       |
| --- | --------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- | ---------- |
| 1   | 旧版 `plan-qc-report.md` 仍按 DOC-01/02/03 三竖条写 §3.9，与 WAVE0 §0.2 DOC-ALL 裁决不一致          | 本报告全文按 DOC-ALL + 票内 checklist 重写                              | **已修复** |
| 2   | `DEBT.plan` §3.10 缺 `schema.sql`、`MIGRATION_008_PLAN`、三件套分行、`§2.6/§8.5`、research 证据路径 | 当场扩表 §3.10（36 行，遗漏风险列全「无」）                             | **已修复** |
| 3   | §3.9 旧报告 Execute order 写 DOC-03 在 restore 前                                                   | 与 DEBT.plan 一致：`REG-BOOT → REG-01 → REG-02 → DOC-ALL`（票内 1→2→3） | **已修复** |

无未关闭 Plan 级缺口。

---

## §3.8 Checklist（Agent-2）

| 项                                              | 结果 | 说明                                                                                                          |
| ----------------------------------------------- | ---- | ------------------------------------------------------------------------------------------------------------- |
| §3.1 + §3.6 每行入 DEBT.plan                    | PASS | playbook §3.6 六行路径均在 §3.6 表有落点；B02_05 §3 扩展路径（schema、三件套、allowlist）已补                 |
| registry 三件套齐全                             | PASS | `AUDIT_DEFERRED` / `UNRESOLVED` / `RESOLVED` 均在 §3.6 + §3.10；REG-02 仅 proposed delta，禁止分支直接 commit |
| `authority_graph.yaml`                          | PASS | §3.10：本切片无新 backend 包                                                                                  |
| `GLOBAL_TASK_TEMPLATE.md` 15 节                 | PASS | Vertical slices + Boundary 展开 B02_05 §1–8                                                                   |
| `BATCH_3V_HARDENING_RULES.md` §3–§7 + §2.5/§2.6 | PASS | Boundary Forbidden + TDD + §7 垂直切片                                                                        |
| 任务卡 §3 必读无缺口                            | PASS | B02_05 §3 全路径在 DEBT；额外补 `AUDIT_DEFERRED`、`MIGRATION_008_PLAN`、`test_schema_contract`                |
| debt slices 表已冻结                            | PASS | REG-BOOT/01/02 + DOC-ALL（WAVE0 §0.2 粒度 quiz）                                                              |
| 每个 owned `VR-*` 有 closure / re-defer         | PASS | 见 §3.9 VR 追溯                                                                                               |
| `check_docs_specs_indexed.py` exit 0            | PASS | 2026-06-28 worktree 实测 exit 0                                                                               |
| `BATCH_3V_SELF_CHECK.md` PASS_FOR_DISPATCH      | PASS | 批次级；FINAL_AUDIT gap 已纳入 DEBT Blockers                                                                  |
| 遗漏项写回 DEBT 并修复                          | PASS | §3.10 扩表完成；本报告复检零遗留                                                                              |
| 粒度 quiz（整卡 1 issue）                       | PASS | REG-ISSUE-1；DOC-01/02/03 合并 DOC-ALL，不拆独立 issue                                                        |

---

## §3.9 追溯审计

### 1. Playbook §3.6 → DEBT.plan 索引行

| Playbook §3.6 路径                                                             | DEBT.plan 落点    | 结果 |
| ------------------------------------------------------------------------------ | ----------------- | ---- |
| `backend/app/db/migrations/009_status_check_constraints.sql`                   | §3.6 → REG-01     | OK   |
| `docs/schema/MIGRATION_COVERAGE.md`                                            | §3.6 → REG-01     | OK   |
| `README.md` · `MANIFEST.json` · `docs/quality/final_package_rules.md`          | §3.6 → DOC-ALL    | OK   |
| `scripts/check_manifest_files.py` · `tests/test_manifest_files_check.py`       | §3.6 → DOC-ALL    | OK   |
| `tests/test_unresolved_item_task_coverage.py`                                  | §3.6 → Merge gate | OK   |
| `docs/quality/quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | §3.6 → VR 路由    | OK   |

### 2. Registry 三件套（主会话批闭合）

| 路径                                 | DEBT.plan 落点        | 分支动作                                                | 结果 |
| ------------------------------------ | --------------------- | ------------------------------------------------------- | ---- |
| `docs/AUDIT_DEFERRED_REGISTRY.md`    | REG-02 proposed delta | 仅 `execute-evidence/REG-02-proposed-registry-delta.md` | OK   |
| `docs/UNRESOLVED_ISSUES_REGISTRY.md` | REG-02 proposed delta | 同上                                                    | OK   |
| `docs/RESOLVED_ISSUES_REGISTRY.md`   | REG-02 proposed delta | 同上                                                    | OK   |

### 3. Owned `VR-*` 三联（Source ID → AC → verification）

**`VR-REG-001`**

| Slice    | Source ID    | AC（摘要）                                                  | Verification / closure test                                                                                                                 |
| -------- | ------------ | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| REG-BOOT | 基线矩阵     | 009 ↔ schema ↔ registry 现状断言                            | `research/migration-009-coverage-matrix.md`                                                                                                 |
| REG-01   | `B02-REG-01` | 覆盖矩阵 + 更新 `MIGRATION_COVERAGE` / `MIGRATION_008_PLAN` | `uv run pytest tests/test_schema_contract.py::test_schemaContract_includesStatusCheckConstraints -q` + `execute-evidence/REG-01-matrix.txt` |
| REG-02   | `B02-REG-02` | proposed registry delta（主会话闭合）                       | `execute-evidence/REG-02-proposed-registry-delta.md`；coordinator 应用后无 UNRESOLVED/RESOLVED 矛盾                                         |

**`VR-DOC-001`（DOC-ALL 合并竖条 + 票内 checklist）**

| 子步 | Source ID    | AC（摘要）                                   | Verification / closure test                                                            |
| ---- | ------------ | -------------------------------------------- | -------------------------------------------------------------------------------------- |
| 1    | `B02-DOC-01` | restore-or-replace `FINAL_AUDIT_REPORT.md`   | `git show 416e74bc:FINAL_AUDIT_REPORT.md` + `execute-evidence/DOC-01-restore.txt`      |
| 2    | `B02-DOC-02` | README/MANIFEST/rules/allowlist 与文件树一致 | `execute-evidence/DOC-02-doc-sync.txt` + `check_manifest_files.py` exit 0              |
| 3    | `B02-DOC-03` | manifest checker TDD                         | `pytest tests/test_manifest_files_check.py -q` + `DOC-03-red.txt` / `DOC-03-green.txt` |

切片级 closure：`check_manifest_files.py` **exit 0**（`--verify-hash` after restore）；`VR-DOC-001` 关账表见 DEBT「Proposed registry deltas § VR-\* closure」。

### 4. 负向边界（§2.6 Must not own + §8.5 未改什么）

| 来源                                                                      | DEBT.plan 落点                 | 结果 |
| ------------------------------------------------------------------------- | ------------------------------ | ---- |
| Playbook §2.6：无证明重写 009                                             | Forbidden 表                   | OK   |
| Playbook §2.6：伪造 FINAL_AUDIT_REPORT                                    | Forbidden 表                   | OK   |
| Manifest C05 Must not own：rewrite 009 without proof                      | Forbidden 表                   | OK   |
| Playbook §8.5：validation_gate / RawStore / sync / layer5 / production DB | §「未改什么」+ Forbidden       | OK   |
| Registry 三件套直接 commit                                                | Forbidden + REG-02 仅 proposed | OK   |

### 5. 垂直切片（§7 debt-lite + §3.9）

| Slice    | VR         | 子 AC                            | 水平合并？                        |
| -------- | ---------- | -------------------------------- | --------------------------------- |
| REG-BOOT | VR-REG-001 | 基线矩阵                         | 否                                |
| REG-01   | VR-REG-001 | B02-REG-01                       | 否                                |
| REG-02   | VR-REG-001 | B02-REG-02                       | 否                                |
| DOC-ALL  | VR-DOC-001 | B02-DOC-01..03（票内 checklist） | 否 — 单竖条内分步证据，非水平关账 |

REG 与 DOC 未在同一 slice 水平关账；符合 Hardening §7 与 WAVE0 §0.2。

### 6. DOC-ALL restore-or-replace 完整性

| 要素                                                | 状态                                      |
| --------------------------------------------------- | ----------------------------------------- |
| 专节「FINAL_AUDIT_REPORT restore-or-replace」       | 有（hash、416e74bc、fallback、Done gate） |
| DOC-ALL 票内 checklist 三联                         | 有                                        |
| `research/final-audit-report-restore-or-replace.md` | 有                                        |
| 规划期 missing 文档化                               | 有（专节 On-disk state）                  |

### 7. Execute order

```text
REG-BOOT → REG-01 → REG-02 → DOC-ALL（REG-02 后可并行起步）
  DOC-ALL 票内：B02-DOC-01 restore → B02-DOC-02 doc sync → B02-DOC-03 TDD/checker
→ uv run pytest -q
```

票内顺序：先 restore 文件，再同步文档树，最后 TDD/哈希校验 — 符合 §5.1 manifest checker 门禁。

### 8. GitHub issue 粒度（WAVE0 §0.2 quiz）

| 裁决                        | DEBT.plan 落点           | 结果 |
| --------------------------- | ------------------------ | ---- |
| B3V-C05 整卡 **1** issue    | REG-ISSUE-1              | OK   |
| DOC-01/02/03 不拆独立 issue | DOC-ALL + 票内 checklist | OK   |

### 9. Research 矩阵

| 文件                                                | 对齐切片     | 结果 |
| --------------------------------------------------- | ------------ | ---- |
| `research/migration-009-coverage-matrix.md`         | REG-BOOT/01  | OK   |
| `research/final-audit-report-restore-or-replace.md` | DOC-ALL §1   | OK   |
| `research/manifest-doc-crosscheck.md`               | DOC-ALL §2/3 | OK   |
| `research/wave0-index-ruling-refresh.md`            | 粒度刷新追溯 | OK   |

---

## §3.10 Plan 质检输出表

> SSOT：`DEBT.plan.md` §3.10（36 行）；本表镜像复检，**遗漏风险列全为「无」**。

| 路径                                                              | 已入 DEBT.plan        | 摘要一句                              | 遗漏风险 |
| ----------------------------------------------------------------- | --------------------- | ------------------------------------- | -------- |
| `agent-toolchain.md`                                              | §Source + §3.6 Boot   | GitNexus/codebase-memory 路由已读     | 无       |
| `round3-repair-debt-worktree-plan.md` Phase 8D                    | §Source               | debt-lite 切片/merge gate 对齐        | 无       |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.1                           | §Source + Boundary    | 共用底座索引                          | 无       |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §3.6                           | §3.6 表               | REG 分支必读全文（playbook 六行路径） | 无       |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §5.1                           | §Source track         | debt-lite 流水线                      | 无       |
| `BATCH_3V_COORDINATOR_PLAYBOOK.md` §2.6 / §8.5                    | Boundary + §未改什么  | Must not own + 负向边界               | 无       |
| `BATCH_3V_HARDENING_RULES.md` §3–§7                               | Boundary + TDD        | 硬停/TDD/§7 垂直切片                  | 无       |
| `BATCH_3V_TASK_CARD_MANIFEST.md` §3 C05                           | §Source + Boundary    | 分支 allowed/forbidden                | 无       |
| `B02_05_migration_registry_and_manifest_consistency.md`           | Vertical slices       | 五子 AC → REG-BOOT/01/02 + DOC-ALL    | 无       |
| `WAVE0_BATCH3V_TO_ISSUES_INDEX.md` §0.2 + §1                      | GitHub issue + slices | 整卡 1 issue；DOC-ALL 粒度 quiz       | 无       |
| `009_status_check_constraints.sql`                                | REG-01                | 009 覆盖矩阵源                        | 无       |
| `specs/schema/schema.sql`                                         | REG-01                | CHECK 契约对照                        | 无       |
| `MIGRATION_COVERAGE.md`                                           | REG-01                | 陈旧 PARTIAL 待修                     | 无       |
| `MIGRATION_008_PLAN.md`                                           | REG-01                | stale narrative fix                   | 无       |
| `docs/AUDIT_DEFERRED_REGISTRY.md`                                 | REG-02 proposed       | 三件套之一                            | 无       |
| `docs/UNRESOLVED_ISSUES_REGISTRY.md`                              | REG-02 proposed       | 三件套之二                            | 无       |
| `docs/RESOLVED_ISSUES_REGISTRY.md`                                | REG-02 proposed       | 三件套之三                            | 无       |
| `README.md`                                                       | DOC-ALL               | restore-or-replace 叙事               | 无       |
| `MANIFEST.json`                                                   | DOC-ALL               | 存在性/哈希一致                       | 无       |
| `final_package_rules.md`                                          | DOC-ALL               | 包规则对齐                            | 无       |
| `release_cleanup_allowlist.yaml`                                  | DOC-ALL               | allowlist 对齐                        | 无       |
| `FINAL_AUDIT_REPORT.md`                                           | DOC-ALL 专节          | restore `416e74bc` 已冻结             | 无       |
| `check_manifest_files.py`                                         | DOC-ALL §3            | manifest gate                         | 无       |
| `test_manifest_files_check.py`                                    | DOC-ALL §3            | TDD RED→GREEN                         | 无       |
| `test_schema_contract.py`                                         | REG-01                | schema CHECK 证据                     | 无       |
| `test_unresolved_item_task_coverage.py`                           | Merge gate            | 主会话后期望集                        | 无       |
| `quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` | §Source               | VR 路由                               | 无       |
| `research/vertical-slices.md`                                     | SSOT                  | REG-BOOT/01/02 + DOC-ALL              | 无       |
| `research/wave0-index-ruling-refresh.md`                          | 裁决追溯              | 2026-06-28 刷新                       | 无       |
| `research/migration-009-coverage-matrix.md`                       | REG-BOOT/01           | 矩阵落盘                              | 无       |
| `research/final-audit-report-restore-or-replace.md`               | DOC-ALL               | restore 决策                          | 无       |
| `research/manifest-doc-crosscheck.md`                             | DOC-ALL               | 工具基线                              | 无       |
| `authority_graph.yaml`                                            | §3.10                 | 无新 backend 包                       | 无       |
| `GLOBAL_TASK_TEMPLATE.md`                                         | Vertical slices       | 卡片 §1–8 展开                        | 无       |
| `BATCH_3V_SELF_CHECK.md`                                          | Blockers              | PASS_FOR_DISPATCH                     | 无       |
| `check_docs_specs_indexed.py`                                     | Merge gate            | worktree exit 0                       | 无       |

---

## 阻塞项

**无 Plan 级阻塞项。**

---

## 主会话回报

| 字段             | 值                                                                                   |
| ---------------- | ------------------------------------------------------------------------------------ |
| **Verdict**      | **PASS**                                                                             |
| **Plan 修复**    | `DEBT.plan.md` §3.10 扩表；`plan-qc-report.md` 按 DOC-ALL 全文重写                   |
| **阻塞项**       | 无                                                                                   |
| **Execute 提醒** | registry 三件套须主会话批闭合；`EXPECTED_UNRESOLVED_IDS` 在 coordinator merge 后更新 |
