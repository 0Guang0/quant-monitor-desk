# 派发对抗审计前自检 — Round 3 Batch 2.5

> 2026-06-20 · 主会话在派发 Agent1/Agent2 前完成

## 1. to-issues 切片自检

| 检查项                      | 结果                                                                          |
| --------------------------- | ----------------------------------------------------------------------------- |
| 是否对 MASTER §8 做垂直切片 | **是** — `research/vertical-slices.md`                                        |
| 切片数量与粒度              | 7 个 AFK 切片 + HITL 说明（live 源、可选 CLI）                                |
| 依赖关系                    | S1→S2→…→S7，Audit A0–A5 门控                                                  |
| 映射 MASTER / AC            | 每片含 MASTER §8.x、Audit、AC 引用                                            |
| Issue tracker 发布          | **未发布** — 无 GitHub issue 词汇表；切片保留在 task research 供 Execute 使用 |

结论：**to-issues 步骤 1–3 完成**；步骤 4–5（用户 quiz + issue tracker）按 Trellis 任务流在 plan.freeze 批准后由 Execute 承接，不阻塞对抗审计。

## 2. 项目地图缺漏自检与修补

| ID   | 发现                            | 处置                                            | 状态       |
| ---- | ------------------------------- | ----------------------------------------------- | ---------- |
| O-01 | MIGRATION_MAP 未列 018A         | Layer 1 行 + 新「Layer 1 observation bridge」行 | **已修补** |
| O-02 | schema.sql 滞后于 migration 011 | MASTER Phase 0 gate AC-P0-2；非地图遗漏         | **已记录** |
| O-03 | validation_gate.py 未索引       | WriteManager 行补充                             | **已修补** |
| O-04 | runners.py 候选接线             | MASTER §6 候选；非地图必须行                    | **已记录** |
| O-05 | TASK_INPUT_CONTEXT_INDEX        | 已覆盖                                          | OK         |
| O-06 | Batch 2 archived 路径           | task.json predecessor + MASTER                  | **已记录** |

`research/project-map-omission-check.md` 结论：**PASS**（修补后）。

## 3. validate-plan-freeze

| 轮次 | 结果                                                                      | 修补                                           |
| ---- | ------------------------------------------------------------------------- | ---------------------------------------------- |
| 初次 | E7 api_security_contract 缺失；E11 orchestrator/pipeline 不应在 implement | 追加 api_security_contract；移除 sync 接线路径 |
| 复检 | **exit 0**                                                                | —                                              |

## 4. 对抗审计派发

| Agent   | 焦点                                                                   | 模型         |
| ------- | ---------------------------------------------------------------------- | ------------ |
| Agent 1 | 上下文/追溯：018A、地图、契约、manifest、integration                   | composer-2.5 |
| Agent 2 | 协议：complex-task-planning-protocol、plan 质量、AUDIT/vertical-slices | composer-2.5 |

产出：`research/adversarial-audit-agent1.md`、`research/adversarial-audit-agent2.md`（主会话核实后合并至 `adversarial-audit-verification.md`）。
