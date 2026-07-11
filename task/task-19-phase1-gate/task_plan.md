# task-19-phase1-gate · Implementation Plan

> **序号：** 19/19 · **阶段：** P1-GATE 总关账
> **前置：** task-18 关账后方可开工本票
> **后继：** （关账终点）
> **权威：** `MIGRATION_MAP.md` 索引 → PHASE1_PRD.md · data_cli_contract.yaml

---

## 目标

将 **P1-GATE 总关账** 做到与设计文档一致的 **R4 成品形态**（本步范围内）。

## 范围

- `daily_close` 整 profile live 复验 · P1-GATE **G1–G8**（见 `PHASE1_COMPLETION_INVENTORY.md`）
- 汇总勾选 task-01～task-18 均已关账
- **不**在本票做模块级修复（修复在对应 task 完成）

## 不在本票

- 各流水线步骤的实现与 findings（见 `../TASK_PIPELINE_INDEX.md`）
- Phase 2（62 指标 feature engine）

## 关账 AC（P1-GATE）

- [ ] task-01～task-18 各自 `progress.md` 已关账
- [ ] `PHASE1_COMPLETION_INVENTORY.md` §12 勾选全满足
- [ ] `daily_close` 四 job live 整单 PASS（无 synthetic PASS / 无 patch 冒充）
- [ ] `legacy-task-02-findings.md` 23 项已拆分/disposition 到各票或总表清零
- [ ] `uv run pytest -q` exit 0
- [ ] 已更新本票 `progress.md`

## 允许触及（开工前填写/收窄）

```text
（实现时按 GitNexus impact 补充路径）
```

## 依赖索引

- 总顺序：`../TASK_PIPELINE_INDEX.md`
