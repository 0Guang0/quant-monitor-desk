# task-02-source-route-plan · Task Plan

> **planning-with-files 工作记忆** · 序号 02/19 · 阶段：路由计划
> **模块：** 源路由计划模块（SourceRoutePlanner / SourceRoutePlan）
> **README：** `README.md` · **索引：** `../TASK_PIPELINE_INDEX.md`

## Goal

将 **路由计划** 做到权威设计规定的完整成品形态：RoutePlan 是唯一选源决定，持久化领域固定候选顺序、有效启用状态、来源/质量等级、失败原因、恢复关联和写入目标；它只能把结果送往可信最终库、连续监控区或审计归档区之一，不得混淆三类数据语义。

## Current Phase

Phase 0 — Gate 1A 接口准备（task-01 尚未 R4；可完成只读倒查和接线清单，不能开始依赖其未验证接口的实现）

## Phases

### Phase 1: 权威对齐与范围收窄
- [ ] 阅读 `README.md` 权威文件（仅 `**/design/**`）
- [ ] 区分运行时文件（依赖/产出/验收）
- [ ] 填写「允许触及」路径（GitNexus impact 后）
- [ ] 记录发现到 `findings.md`
- **Status:** pending

### Phase 1A: Gate 1A 策略接线契约
- [ ] 与 task-01 的有效启用／capability 查询结果对齐，禁止读取可变 registry 对象或自行放行
- [ ] 固化并持久化 RoutePlan 的候选优先级、来源/质量等级、失败原因、覆盖层版本与恢复关联
- [ ] 列出 task-17、task-18 的正式调用入口、同参横测命令和验收责任
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
2. task-01 是否已发布经测试的策略查询契约？未发布时只允许做接线设计，不得假设其字段或绕过行为。
3. 每个领域的固定候选优先级和恢复窗口是否已由现有受控配置唯一确定？缺失或冲突时登记为用户裁决项。
4. 本步最小可运行验证是什么？

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
- [ ] 同一策略输入在 RoutePlan、CLI、scheduler 入口得到同一 source/状态/原因码；次源只能是 `FallbackPolicy + DEGRADED`
- [ ] 可信最终库、连续监控区、审计归档区三种写入目标及其标签可从 RoutePlan 追溯
- [ ] `uv run pytest -q` 全绿（关账日复验）
- [ ] 已更新 `progress.md`

## 允许触及（开工前填写/收窄）

```text
（实现时按 GitNexus impact 补充路径）
```

## 流水线位置

| 项 | 内容 |
|----|------|
| **前置** | task-01 关账后方可开工本票 |
| **上游** | task-01-source-registry |
| **下游** | task-03-resource-guard · task-04-datasource-fetch |
