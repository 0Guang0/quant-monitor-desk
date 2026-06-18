# PLAN FREEZE — Round 2 Batch D

> Plan freeze self-check before `task.py start`.

## 1. Required files

- [x] `task.json`
- [x] `MASTER.plan.md`
- [x] `implement.jsonl`
- [x] `AUDIT.plan.md`
- [x] `audit.jsonl`
- [x] `check.jsonl`
- [x] `REPAIR.plan.md`
- [x] `repair.jsonl`
- [x] thin `prd.md`
- [x] thin `design.md`
- [x] thin `implement.md`

## 2. Protocol checks

- [x] `implement.jsonl` first entry is `MASTER.plan.md`.
- [x] `implement.jsonl` second entry is `.cursor/skills/trellis-execute/SKILL.md`.
- [x] `audit.jsonl` first entry is `AUDIT.plan.md`.
- [x] MASTER §8 contains step-by-step execution (8.0–8.11).
- [x] MASTER §9/§10 contain runnable commands.
- [x] MASTER §12 freezes Execute skills.
- [x] AUDIT.plan contains A1–A8 validation matrix.
- [x] REPAIR.plan defines repair policy.

## 3. Scope checks

- [x] Batch D includes original 014.
- [x] Batch D includes DECISIONS §9 orchestration deferrals (GPT-init_db, GPT-P3-6, B-P1-6-full).
- [x] Batch D excludes Layer modeling / frontend / API / Agent / real Port / full security CI.
- [x] Path correction: `backend/app/sync/*`.

### 3.0b 原计划包门禁

- [x] 已读 `docs/implementation_tasks/` README + GLOBAL 四文件
- [x] 已读 ROUND README + DECISIONS + 014 任务卡 + §3 输入文件
- [x] `research/original-plan-trace.md` 已产出
- [x] `research/plan-boot.md` 含 `Phase P0 complete`
- [x] `implement.jsonl` 含 GLOBAL + 014 + **全量 Batch D 必读（~67 条；含 004/005、Batch C 接线、§9.2/§9.3 回归与门禁）**
- [x] MASTER **§0.3** Execute 强制必读 + `8.0-boot-reads.txt` 证据

## 4. Plan phase checklist (1a→5d)

- [x] P0 Boot + plan-skill-reads.jsonl
- [x] 1a project-overview.md
- [x] 2a prd.md
- [x] 2b MASTER §2 AC
- [x] 3 grill-with-docs-session.md
- [x] 3.5 slice-issues.md
- [x] 1b gitnexus-summary.md
- [x] 4 MASTER §4–6
- [x] 5a MASTER §5
- [x] 5b orchestrator-tests.md
- [x] 5c implement.jsonl curated
- [x] 5d doubt-driven §7/§8 + AUDIT §2 修订

## 5. Ready

`PLAN_FREEZE_READY: yes`

## 6. Manifest Gate (E15)

- [x] `original-plan-trace.md` 含 manifest 列
- [x] `plan-manifest-audit.md` doc-gap + adversarial PASS
- [x] `implement.jsonl` 覆盖 trace required + §6/§9
- [x] `check.jsonl` ⊆ implement（E14）
- [x] `task.json` `predecessor_tasks` 已填
- [x] `suggest-implement-context` ≤5 缺失
- [x] MASTER §0.3 已冻结

## 7. Context Packing Gate（v3 · E15 扩展）

- [x] `research/input-inventory.md` P0i complete
- [x] `research/integration-ledger.md` ≥5 行
- [x] `research/integration-audit.md` PASS
- [x] `meta.manifest_protocol_version: "3"`

## 8. Execute handoff（`task.py start` 后）

- [x] `python .trellis/scripts/task.py validate-plan-freeze` → exit 0（2026-06-18）
- [x] `python .trellis/scripts/task.py start` → `status: in_progress`
- [x] `research/EXECUTE-READY.md` 已产出
- [x] `docs/.../BATCH_D_STATUS.md` + ROUND README + DECISIONS §Batch D checkpoint
- [ ] 用户/Execute：**下一动作 = MASTER §8.0 Boot**（读 `trellis-execute` SKILL）

```text
validate-plan-freeze: Plan freeze validation passed
task.py start: planning → in_progress
```
