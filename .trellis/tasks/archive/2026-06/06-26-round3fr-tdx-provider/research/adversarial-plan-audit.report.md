# 对抗性 Plan 审计报告 — R3FR-03

> Agent: code-reviewer · 2026-06-26  
> **主会话修复状态：全部 ADV-01..25 已闭合**（见 §6）

---

## P0（已修复）

| ID     | 问题                  | 修复                                                                                   |
| ------ | --------------------- | -------------------------------------------------------------------------------------- |
| ADV-01 | caps 3 vs 10 权威冲突 | 活卡 §5.1 + `EXECUTION_INDEX` §0.2；授权 MD 改为 3；§9.4 同步 gate 步骤                |
| ADV-02 | AC-TDX-01 追溯断裂    | §0.1 绑定 `test_tdxPytdxPort_missingPytdx_returnsDisabledSource`；§1 Step 9.1 专用 RED |
| ADV-03 | AC-TDX-03 无测试设计  | §9.3 三则新测 + §1 Step 9.3 `-k rejects*`                                              |

## P1（已修复）

| ID     | 问题                       | 修复                                                               |
| ------ | -------------------------- | ------------------------------------------------------------------ |
| ADV-04 | gate 不在 §4 目标文件      | 活卡 §4 加入 gate + 授权 MD                                        |
| ADV-05 | 缺 rollback plan           | 活卡 §15 + `EXECUTION_INDEX` §4                                    |
| ADV-06 | AC-TDX-06 不测 caps 字段   | `test_tdxPytdx_capsMatchTaskCard` + `resource_caps` YAML 步骤 §9.6 |
| ADV-07 | PortError Literal 缺状态   | §9.1 扩展 `fetch_port.py` 子步                                     |
| ADV-08 | R3FR-05 registry 冲突      | `EXECUTION_INDEX` §5 + §9.6 独占行协议                             |
| ADV-09 | implement/audit jsonl 漂移 | §3 扩 manifest；`freeze-task-card` 重生 jsonl                      |
| ADV-10 | FORBIDDEN_LIVE 死代码      | §9.4 enforce + `test_tdxLiveGate_forbiddenDirectPortInvocation`    |
| ADV-11 | qmd_target_files 路径错    | 活卡 §1 → `datasources/fetch_ports`                                |
| ADV-12 | RED `-k` 弱绑定            | §1 每步绑定具名测试函数                                            |

## P2（已修复）

| ID     | 修复                                                  |
| ------ | ----------------------------------------------------- |
| ADV-13 | §6 注明空 context_pack 时以 §3 为准；Boot 复跑 router |
| ADV-14 | §9.7 + Tier C `loop_maintain.py`                      |
| ADV-15 | §0.1 统一 AC-TDX-04：hash=9.2，编排=9.5               |
| ADV-16 | §9.1/9.2 MIT 归因注释要求                             |
| ADV-17 | `evidence_index.json` 占位结构                        |
| ADV-18 | `integration-audit.md` §5 PASS                        |
| ADV-19 | `test_tdxRoute_tdxPytdx_disabledByDefault` §9.6       |
| ADV-20 | §12 显式不闭合 B01-C03 live defer                     |

## P3（已修复）

| ID     | 修复                                          |
| ------ | --------------------------------------------- |
| ADV-21 | `TASK_INPUT_CONTEXT_INDEX` §4 + §6 增 R3FR-03 |
| ADV-22 | `MIGRATION_MAP.md` 增 R3FR-03 行              |
| ADV-23 | `BATCH_3FR_TASK_CARD_MANIFEST` 全路径         |
| ADV-24 | 活卡 §13 扩 Red Flags                         |
| ADV-25 | `PLAN_REVIEW.md` 与 §9.7/loop 对齐            |

---

## §6 闭合判定

**Plan 审计：PASS（修复后）** — 可进入用户审阅；批准后 `task.py start`。
