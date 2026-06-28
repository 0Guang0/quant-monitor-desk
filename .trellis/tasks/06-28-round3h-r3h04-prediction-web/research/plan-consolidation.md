# Plan Consolidation — R3H-04 Prediction and Web Evidence Adapters

> **Phase 5e complete** · Execute **不读**本表以外的 `research/*` Plan 草稿

## 5e 完备性（分流 + 自检）

| 内容类型                  | 落点                                       | Execute 读法 |
| ------------------------- | ------------------------------------------ | ------------ |
| 可无损精简的可执行结论    | 活任务卡 → `frozen/*.md`；**INDEX §4**     | frozen       |
| 不可精简 / 精简必丢信息   | **INDEX §3** `must-read`（仓库原文）       | 原文         |
| Plan 过程记录、已无新结论 | `n/a`                                      | 不读         |
| 仅 Audit 追溯             | `pointer`（**仅** `integration-audit.md`） | 不读         |

**禁止：** 含决策的草稿标 `pointer`；`implement.jsonl` 出现 `research/*`。

冻结前自问：Execute **只读** frozen + INDEX + implement.jsonl 能否跑 §9？**能**。

```bash
python .trellis/scripts/task.py validate-plan-phase .trellis/tasks/06-28-round3h-r3h04-prediction-web 5e
python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/06-28-round3h-r3h04-prediction-web
```

## 对照表

| 来源                                        | 结论类型      | 落点                          | 状态    |
| ------------------------------------------- | ------------- | ----------------------------- | ------- |
| `research/plan-boot.md`                     | 边界/授权     | frozen §2.8 / §1.1              | merged  |
| `research/brainstorm-session.md`            | 方案否决/采纳 | frozen §1.1                   | merged  |
| `research/spec-driven-development-notes.md` | 契约→测试映射 | frozen §5.1 + INDEX §2        | merged  |
| `research/project-overview.md`              | 基线/模块     | frozen §4.2                   | merged  |
| `research/grill-me-session.md`              | 决策 Q&A      | frozen §1.1 / §8              | merged  |
| `research/gitnexus-summary.md`              | impact/风险   | frozen §4.3                   | merged  |
| `research/to-issues-slices.md`              | S0–S8 依赖    | INDEX §0.1/§1；frozen §9 首段 | merged  |
| `research/integration-ledger.md`            | 内联 vs §3    | INDEX §3/§4 规则              | n/a     |
| `research/integration-audit.md`             | 对抗/GAP      | frozen §10.2；Audit 可读      | pointer |
| `research/original-plan-trace.md`           | AC 血缘       | INDEX §0.1                    | merged  |
| `research/project-map-omission-check.md`    | 新建清单      | frozen §12                    | merged  |

**Execute GAP（若有）：** 无 Plan 可内联但未写入 frozen/INDEX 的决策。

**Phase 5e complete**
