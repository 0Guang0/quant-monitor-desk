# M-DATA-03 Doubt-Driven Review

> Phase 5c · 非平凡决策质疑记录

---

## Cycle 1 — 是否重写 DCP-05 增量逻辑？

| 步骤      | 内容                                                      |
| --------- | --------------------------------------------------------- |
| CLAIM     | 需要新写 11 源 incremental 管道                           |
| EXTRACT   | DCP-05 已有 ops/_*incremental*_ + 11 replay e2e           |
| DOUBT     | 真网失败是否因逻辑缺失而非 mock 路径？                    |
| RECONCILE | **复用 DCP-05**；本票只接 `use_mock=False` + live harness |
| STOP      | actionable: 否 — 已收敛                                   |

**分类：** noise（若 Execute 发现 port bug 再开 repair 切片）

---

## Cycle 2 — replay 测试是否删除？

| 步骤      | 内容                                                                  |
| --------- | --------------------------------------------------------------------- |
| CLAIM     | live 为主应删 replay e2e                                              |
| EXTRACT   | CI 默认无 key；DCP-09 nightly 分层                                    |
| DOUBT     | 删 replay 会导致 PR 无网全红？                                        |
| RECONCILE | **保留 replay** 为默认快测；**新增** `@pytest.mark.network` live 变体 |
| STOP      | actionable: 是 — spec §Testing Strategy                               |

**分类：** trade-off accepted

---

## Cycle 3 — 参考项目是否 L1 复制 OpenBB fred？

| 步骤      | 内容                                          |
| --------- | --------------------------------------------- |
| CLAIM     | 复制 OpenBB fred fetcher 加速                 |
| EXTRACT   | guardrails: AGPL architecture_only            |
| DOUBT     | license + runtime 依赖                        |
| RECONCILE | **L3 对齐**三阶段；仓内 `fred_port` 扩展 live |
| STOP      | actionable: 否                                |

**分类：** actionable — 写入 reference-adoption §2.1

---

## Cycle 4 — 11 agent 并行？

| 步骤      | 内容                                           |
| --------- | ---------------------------------------------- |
| CLAIM     | 每源一 agent 最快                              |
| EXTRACT   | registry 三件套须 coordinator merge            |
| DOUBT     | sync 公共文件冲突                              |
| RECONCILE | **峰值 3–4 agent**；批次 2a→2b/2c              |
| STOP      | actionable: 是 — parallel-dispatch-protocol.md |

**分类：** actionable

---

## Cycle 5 — 新 migration 补 live 列？

| 步骤      | 内容                                       |
| --------- | ------------------------------------------ |
| CLAIM     | live 需要新 DDL                            |
| EXTRACT   | ADR-028 migration 015 已覆盖 11 源 clean   |
| DOUBT     | 缺列？                                     |
| RECONCILE | **禁止新 DDL**；缺列则 Batch6 单独票       |
| STOP      | actionable: 否 — 除非 Execute 实证 blocker |

**分类：** trade-off — 封板优先

---

## 汇总

| 分类       | 项                                                     |
| ---------- | ------------------------------------------------------ |
| actionable | replay+live 双轨；3–4 并行 agent；借鉴梯与仓内复用分轨 |
| trade-off  | 无新 DDL；live 验收与 CI 默认分离                      |
| noise      | 重写管道（已否决）                                     |

---

## Cycle 6 — 「L1 仓内」误标（Plan 审计 · actionable）

| 步骤      | 内容                                                              |
| --------- | ----------------------------------------------------------------- |
| CLAIM     | `reference-adoption` §4 把 orchestrator 标为「L1 仓内」           |
| EXTRACT   | 借鉴 L1 仅指 `参考项目/**` 直接拷贝；guardrails `adoption_ladder` |
| DOUBT     | Execute agent 可能从参考项目拷 orchestrator？                     |
| RECONCILE | §4 改为 **仓内直接复用**；本票参考侧 **0×L1**                     |
| STOP      | 已修 `reference-adoption-m-data-03.md` §0·§4                      |

**分类：** actionable — 已修复

---

## Cycle 7 — 「L2 概念」等级模糊（Plan 审计）

| 步骤      | 内容                                                                       |
| --------- | -------------------------------------------------------------------------- |
| CLAIM     | EasyXT 日期窗标「L2 概念」                                                 |
| EXTRACT   | L2 = 拷贝后必须改造；概念无拷贝应为 L3                                     |
| RECONCILE | EasyXT 日期窗/交易日 → **L3**；唯一 **L2** = digital-oracle bis 窗参数模式 |
| STOP      | 已修 reference-adoption §1                                                 |

**分类：** actionable — 已修复

---

## Cycle 8 — 接口契约缺失（api-and-interface-design）

| 步骤      | 内容                                                              |
| --------- | ----------------------------------------------------------------- |
| CLAIM     | `tier_a_live_acceptance.py` 无 exit code / CLI 契约               |
| EXTRACT   | Hyrum：可观测行为即契约                                           |
| RECONCILE | `plan-spec.md` Interface Contract 节：gate · ops · acceptance CLI |
| STOP      | 已写入 plan-spec                                                  |

**分类：** actionable — 已修复

---

## Cycle 9 — SDD 官方 API 未绑定切片（source-driven-development）

| 步骤      | 内容                                                                     |
| --------- | ------------------------------------------------------------------------ |
| CLAIM     | live port 实现可能凭训练数据写 URL                                       |
| RECONCILE | `plan-spec.md` Official API 表 + `EXTERNAL-INDEX.md` §E；to-issues AC #7 |
| STOP      | 已写入                                                                   |

**分类：** actionable — 已修复

---

## Cycle 10 — F0/E2 验收未进切片（context-engineering）

| 步骤      | 内容                                                      |
| --------- | --------------------------------------------------------- |
| CLAIM     | 活卡要求 inspect/health，S-ACCEPT 只写 sync→clean         |
| RECONCILE | S-ACCEPT AC 显式 `qmd data inspect` + data health (F0/E2) |
| STOP      | 已修 to-issues                                            |

**分类：** actionable — 已修复
