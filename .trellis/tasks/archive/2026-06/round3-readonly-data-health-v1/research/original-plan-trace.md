# Original plan trace — round3-readonly-data-health-v1

| 字段           | 值                                                                                                       |
| -------------- | -------------------------------------------------------------------------------------------------------- |
| Round / Batch  | Round 3 Wave C **C-20**                                                                                  |
| Item ID        | `R3Y-readonly-data-health-v1` / PROMPT_20                                                                |
| 原计划任务卡   | `docs/implementation_tasks/ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_readonly_data_health_v1.md`            |
| 启动 Prompt    | `docs/implementation_tasks/ROUND_3_PARALLEL_PROMPTS/PROMPT_20_feature_round3_readonly_data_health_v1.md` |
| Batch map 条目 | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §2.2 C-20                                                           |
| 前置 gate      | staged pilot v2 archived；`R3-B2.75-REQ2-EM` DEFERRED                                                    |
| 分支           | `feature/round3-readonly-data-health-v1` @ worktree `../quant-monitor-desk-wt-r3-data-health`            |

## MASTER §2 AC 对照

| AC          | 任务卡 / Playbook §8.1 | 验证                                                |
| ----------- | ---------------------- | --------------------------------------------------- |
| AC-DH-PLAN  | Plan 行                | `validate-plan-freeze` exit 0                       |
| AC-DH-IMPL  | 实现行                 | `data_health.py` + 只读约束 pytest                  |
| AC-DH-BIZ   | 业务 AC 行             | v2 evidence integration §8.9                        |
| AC-DH-RULES | 规则面行               | §5.1 rule_id 子集 tests                             |
| AC-DH-SLICE | 切片证据行             | 每 §8.x RED/GREEN                                   |
| AC-DH-TEST  | 测试行                 | `test_ops_data_health.py`                           |
| AC-DH-MAP   | MAP 验证行             | §10 Tier A                                          |
| AC-DH-AUDIT | Audit 行               | `audit_matrix.json`                                 |
| AC-DH-BOUND | 边界行                 | forbidden diff                                      |
| AC-DH-GATE  | 门禁陈述行             | `sandbox_clean_write_gate_ready` + `gate_rationale` |

## 九切片 → §8

| Issue     | MASTER §8 |
| --------- | --------- |
| R3Y-DH-01 | §8.1      |
| R3Y-DH-02 | §8.2      |
| R3Y-DH-03 | §8.3      |
| R3Y-DH-04 | §8.4      |
| R3Y-DH-05 | §8.5      |
| R3Y-DH-06 | §8.6      |
| R3Y-DH-07 | §8.7      |
| R3Y-DH-08 | §8.8      |
| R3Y-DH-09 | §8.9      |

## Deferred / Register

| 项                                 | 本任务范围           | 偿还          |
| ---------------------------------- | -------------------- | ------------- |
| 完整 Batch6 `qmd data health` 平台 | out — v1 最小只读    | Batch 6       |
| `source_health_snapshot` clean 写  | **禁止**             | Batch 6       |
| `R3-B2.75-REQ2-EM` production-live | **不得**声称 unblock | Wave C 后协调 |
