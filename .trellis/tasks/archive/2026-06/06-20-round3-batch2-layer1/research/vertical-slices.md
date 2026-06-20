# Vertical Slices — Round 3 Batch 2（Phase 3.5 to-issues）

| 切片                          | 交付                                              | AC                       | 依赖                        |
| ----------------------------- | ------------------------------------------------- | ------------------------ | --------------------------- |
| VS-1 Schema foundation        | migration 011 + init_db                           | AC-017-4                 | 无                          |
| VS-2 Spec loader + guardrails | AxisSpecLoader + guardrails + loader tests        | AC-017-1..8              | VS-1                        |
| VS-3 Feature engine           | AxisFeatureEngine + feature tests + ResourceGuard | AC-018-1,2,4,5; AC-RES-1 | VS-2 + fixture observations |
| VS-4 Interpretation engine    | AxisInterpretationEngine + interpretation tests   | AC-018-3,6               | VS-3                        |
| VS-5 Lineage + write path     | lineage 表 + WriteManager 集成                    | AC-LINEAGE-\*; AC-WRIT-1 | VS-3/4                      |

对应 MASTER §8.1→8.5 顺序。
