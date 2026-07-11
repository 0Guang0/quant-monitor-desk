# task-15-job-revision-audit · Implementation Plan

> **序号：** 15/19 · **阶段：** RevisionAuditJob
> **前置：** task-14 关账后方可开工本票
> **后继：** task-16
> **权威：** `MIGRATION_MAP.md` 索引 → data_sync_orchestrator.md §12.5 · §13.4.4

---

## 目标

将 **RevisionAuditJob** 做到与设计文档一致的 **R4 成品形态**（本步范围内）。

## 范围

- revision diff · F-08

## 不在本票

- 下游步骤的实现（见 `TASK_PIPELINE_INDEX.md` 后继 task）
- 除非本步接缝明确要求，不修改其他 task 的 findings

## 关账 AC（R4）

- [ ] 回读本步 design 权威，逐条有实现或 ponytail+升级路径
- [ ] `findings.md` 本票条目全部 ∈ {已修复, 按设计, 阶段外置（须登记）}
- [ ] 本步至少有 **一条** 可运行验证（pytest 或 CLI）证明行为，非空壳
- [ ] `uv run pytest -q` 全绿（关账日复验）
- [ ] 已更新 `progress.md`

## 允许触及（开工前填写/收窄）

```text
（实现时按 GitNexus impact 补充路径）
```

## 依赖索引

- 总顺序：`../TASK_PIPELINE_INDEX.md`
