# Implement — Round 3 Batch 2

> **Execute 入口：** `MASTER.plan.md` + `implement.jsonl`（55 条）  
> **下一会话起手：** `research/execute-handoff.md`  
> **Skill：** `.cursor/skills/trellis-execute/SKILL.md` Phase 0 Boot

| 步骤 | 标题                                           | 测试设计                                          |
| ---- | ---------------------------------------------- | ------------------------------------------------- |
| 8.0  | Boot gate                                      | —                                                 |
| 8.1  | Layer1 schema migration                        | MASTER §8.1                                       |
| 8.2  | AxisSpecLoader (017)                           | `research/layer1-axis-loader-tests.md`            |
| 8.3  | AxisFeatureEngine + feature snapshot (018)     | `research/layer1-feature-interpretation-tests.md` |
| 8.4  | AxisInterpretationEngine (018)                 | 同上                                              |
| 8.5  | Lineage consumers (R3-EARLY-LINEAGE-CONSUMERS) | `research/layer1-lineage-tests.md`                |
| 8.6  | Final gates                                    | MASTER §9–§10                                     |

**首条 RED：** §8.0 — `execute-boot.md` 不存在时 RED 须 exit 1（见 MASTER §8.0）。
