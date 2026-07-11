# task-06-staging · Task Plan

> **planning-with-files 工作记忆** · 序号 06/19 · 阶段：Staging
> **模块：** Staging 暂存层
> **README：** `README.md` · **索引：** `../TASK_PIPELINE_INDEX.md`

## Goal

将 **Staging** 做到与设计文档一致的 **R4 成品形态**（本步范围内）。

## Current Phase

Phase 1 — 权威对齐与范围收窄（**未开工**）

## Phases

### Phase 1: 权威对齐与范围收窄
- [ ] 阅读 `README.md` 权威文件（仅 `**/design/**`）
- [ ] 区分运行时文件（依赖/产出/验收）
- [ ] 填写「允许触及」路径（GitNexus impact 后）
- [ ] 记录发现到 `findings.md`
- **Status:** pending

### Phase 2: RED — 测试先行
- [ ] 为本步目标写失败测试（五字段 docstring）
- [ ] `uv run pytest` 预期 RED
- **Status:** pending

### Phase 3: GREEN — 最小实现
- [ ] 实现使测试通过（ponytail）
- [ ] 记录决策到 `findings.md`
- **Status:** pending

### Phase 4: 关账验证
- [ ] 关账 AC 逐项勾选
- [ ] `findings.md` 全部 disposition 关账
- [ ] `uv run pytest -q` 全绿
- **Status:** pending

### Phase 5: 交付
- [ ] 更新 `progress.md`
- [ ] 通知后继 task 可开工（若适用）
- **Status:** pending

## Key Questions

1. 本票 design 权威是否已全部倒查？（见 README）
2. 前置 task 是否已关账？（**task-05 关账后方可开工本票**）
3. 本步最小可运行验证是什么？

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| — | （实现后填写） |

## Errors Encountered

| Error | Attempt | Resolution |
|-------|---------|------------|
| — | — | — |

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

## 流水线位置

| 项 | 内容 |
|----|------|
| **前置** | task-05 关账后方可开工本票 |
| **上游** | task-05-raw-store |
| **下游** | task-07 · task-08 |
