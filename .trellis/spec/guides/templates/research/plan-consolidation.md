# Plan Consolidation — {{任务标题}}

> **Phase 5e complete** · **v4.1 Execution Bundle**  
> Execute 日常读 `research/00-EXECUTION-ENTRY.md` + 包内 skill 产出；**不**依赖本表以外的 Plan 草稿。

## 5e 完备性（v4.1）

| 内容类型                                            | 落点                                      | Execute 读法          |
| --------------------------------------------------- | ----------------------------------------- | --------------------- |
| Skill 产出（to-issues / 5a–5c' / trellis-research） | `research/*.md`                           | **freeze 后仍读原文** |
| 总路由                                              | `research/00-EXECUTION-ENTRY.md` §5.1–5.3 | 入口                  |
| 外部路径                                            | `research/EXTERNAL-INDEX.md`              | §A 必读 · §B/C 情境   |
| ADR                                                 | `docs/decisions/` + ENTRY §4              | 外部必读              |
| 活卡摘要                                            | `frozen/*.md`                             | 薄指针，不复制 slices |
| 步骤/证据指针                                       | `EXECUTION_INDEX.md` §0/§3                | 薄索引                |
| Plan 过程-only                                      | `research/plan-boot.md` 等                | Execute **不读**      |

**禁止：** 将 `to-issues-slices.md` 全文 merged 进 frozen；`implement.jsonl` 禁止仅指向未登记的 `research/*`。

冻结前自问：ENTRY §5.1 是否列出**全部**将纳入 §5.2 必读的 `research/*.md`？

```bash
python .trellis/scripts/task.py validate-plan-phase <task-dir> 5e
python .trellis/scripts/task.py validate-plan-freeze <task-dir>
```

## Skill 产出对照表（登记 ENTRY §5.1）

| Skill                       | 产出路径                             | 结构自检（SKILL.md）         | 状态 |
| --------------------------- | ------------------------------------ | ---------------------------- | ---- |
| to-issues                   | `research/to-issues-slices.md`       | issue-template + 依赖图      |      |
| planning-and-task-breakdown | `research/`                          | Plan Document Template       |      |
| spec-driven-development     | `research/`                          | Spec 六要素                  |      |
| context-engineering         | `research/plan-context.md`           | PROJECT CONTEXT + 情境路由   |      |
| doubt-driven-development    | `research/plan-doubt-review.md`      | Doubt cycle                  |      |
| documentation-and-adrs      | `docs/decisions/ADR-*.md`            | ADR Template                 |      |
| trellis-research            | `research/`                          | trellis-research File Format |      |
| （可选）旁路基线            | `research/bypass-baseline-matrix.md` | —                            |      |

## 打包产出

| 文件                             | 状态 |
| -------------------------------- | ---- |
| `research/00-EXECUTION-ENTRY.md` |      |
| `research/EXTERNAL-INDEX.md`     |      |
| `EXECUTION_PLAN.md`              |      |

**Phase 5e complete**
