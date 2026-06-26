# Plan 冻结记录 — R3FR-07 Legacy Wrapper Cleanup

> **读者：Plan agent** · Execute / Audit **不读**  
> **分支：** `chore/round3fr-cleanup-rehome`（**禁止在 master 上 Execute**）  
> **状态：** Plan 完成，**待用户审阅** → `task.py start`

---

## 1. Plan 阶段 Skill 执行记录

| Phase    | Skill                          | 产出                                   | 已完成 |
| -------- | ------------------------------ | -------------------------------------- | ------ |
| boot     | agent-toolchain + trellis-plan | `research/plan-boot.md`                | [x]    |
| P0-index | trellis-plan                   | `EXECUTION_INDEX.md`                   | [x]    |
| 1a       | gitnexus-plan-1a               | `research/project-overview.md`         | [x]    |
| 2a       | trellis-brainstorm             | `prd.md`                               | [x]    |
| 2b       | spec-driven-development        | frozen §6–§8 + EXECUTION_INDEX §3      | [x]    |
| 3        | grill-me                       | `research/grill-me-session.md`         | [x]    |
| 3.5      | to-issues                      | `research/vertical-slices.md`          | [x]    |
| 1b       | gitnexus-plan-1b               | `research/gitnexus-summary.md`         | [x]    |
| 5a       | planning-and-task-breakdown    | EXECUTION_INDEX §1 + frozen §9         | [x]    |
| 5b       | writing-plans                  | EXECUTION_INDEX §1 RED/GREEN + §2 Tier | [x]    |
| 5c       | trellis-before-dev             | `integration-ledger.md`                | [x]    |
| 5d       | doubt-driven-development       | `integration-audit.md` PASS            | [x]    |

---

## 2. Plan 贡献溯源 & 5d 结论

- **integration-audit: PASS**（2026-06-27 对抗性修复后）
- **adversarial-plan-audit: PASS**（ADV-07-01..25 闭合，见 `research/adversarial-plan-audit.report.md`）
- §3 manifest 5 → 27 行；`implement.jsonl` 已 regenerate
- 本任务为 cleanup-only；3G runtime 不在范围

---

## 3. 冻结自检（`task.py start` 前）

### 3.0v4 冻结三件套

| ✓   | Execute                                                        | ✓   | Audit                        |
| --- | -------------------------------------------------------------- | --- | ---------------------------- |
| [x] | `frozen/R3FR_07_LEGACY_WRAPPER_CLEANUP_AND_REDIRECTS.md` §8–§9 | [x] | `AUDIT.plan.md` §1 无 `{{}}` |
| [x] | `EXECUTION_INDEX.md` §1–§2                                     | [x] | §5 追溯集                    |
| [x] | §3 manifest → implement.jsonl                                  | [x] | A6/A7 SKIP 已注明            |
| [x] | `freeze-task-card` 已执行                                      | [x] | audit.jsonl 已 generate      |

### 3.0a Phase 产出门禁

| ✓   | 检查项                                |
| --- | ------------------------------------- |
| [x] | project-overview.md                   |
| [x] | grill-me-session.md                   |
| [x] | vertical-slices ≥7 切片               |
| [x] | gitnexus-summary.md                   |
| [x] | integration-audit PASS                |
| [x] | adversarial-plan-audit.report.md PASS |
| [x] | project-map-omission-check.md         |

### 3.0b 原计划包

| ✓   | 检查项                                     |
| --- | ------------------------------------------ |
| [x] | GLOBAL×4 + batch README + R3FR_07 活卡加固 |
| [x] | `EXECUTION_INDEX` P0i 索引完整             |
| [x] | `research/plan-boot.md` Phase P0 complete  |

### 3.7 用户批准（不计入机器门禁）

审阅 `PLAN_REVIEW.md` 后批准，再执行：

```powershell
uv run python .trellis/scripts/task.py start .trellis/tasks/06-27-06-27-round3fr-cleanup-rehome
```

**批准前禁止：** `task.py start`、在 `master` 上改 `backend/` 业务代码。

---

## 4. 修订记录

| 版本 | 日期       | 变更                                                    |
| ---- | ---------- | ------------------------------------------------------- |
| v2   | 2026-06-27 | 对抗性审计 ADV-07-01..25；§3 manifest 扩充；AC-07-07/08 |
