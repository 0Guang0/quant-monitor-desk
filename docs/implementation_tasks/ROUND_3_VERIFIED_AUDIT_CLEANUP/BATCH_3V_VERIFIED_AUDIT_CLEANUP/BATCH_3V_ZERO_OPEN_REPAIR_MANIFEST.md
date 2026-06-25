# Batch 3V 零遗留修复清单

> **策略：** `BATCH_3V_ZERO_OPEN_CLOSURE_POLICY.md` — BLOCKING + NON-BLOCKING **全部闭合**，0 OPEN  
> **主会话：** registry 三件套 §7.3 批闭合；分支 Repair 负责代码/测试/证据/commit

## 分支 Repair 队列

| 分支    | Repair agent         | 必闭合项                                                                                                     |
| ------- | -------------------- | ------------------------------------------------------------------------------------------------------------ |
| B3V-REG | zero-open-repair-reg | commit 全部；AA-B3V-03/04；`loop_maintain`；对抗性复跑 PASS                                                  |
| B3V-L5R | zero-open-repair-l5r | ADV-L5R-01..04 commit；N02 authority_graph；N06 矩阵勾选；对抗性复跑 PASS                                    |
| B3V-OPS | zero-open-repair-ops | A1-F01 parity 测；A3-F01 fail-fast；A4 catalog/spec；A5 证据加厚；A7/A8 报告+修复；commit；pytest 任务域全绿 |

## Registry（主会话 §7.3，分支仅 repair-evidence）

- REG-02 proposed delta → coordinator 应用
- L5R registry_proposed_delta → coordinator 应用 + `R3-MODEL-L3L4-MIGRATION` defer
- OPS B02-CLOSE-01 → coordinator 应用
- STOR/DATA/SYNC → Execute/Audit 后追加

## Done 门禁（每分支）

- [ ] `research/*-report.md` 无 OPEN finding
- [ ] `repair-evidence/zero-open-signoff.md` exit 0 清单
- [ ] 分支已 commit
- [ ] 任务域 pytest 全绿
