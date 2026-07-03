# M-DATA-03 Doubt-Driven Review（Plan R2）

> Phase 5c · 用户 grill 决策记录 · **AC 以 `plan-revision-r2.md` §2 为准**

---

## Cycle 1 — 复用 DCP-05 vs 重写管道

| 步骤      | 内容                                                 |
| --------- | ---------------------------------------------------- |
| CLAIM     | 需新写 11 源 incremental                             |
| RECONCILE | **复用 DCP-05**；R2 仅去重 dispatch 包装 + live 门控 |
| STOP      | noise                                                |

---

## Cycle 2 — replay 测试保留

| 步骤      | 内容                                                   |
| --------- | ------------------------------------------------------ |
| RECONCILE | **保留** replay 为默认快测；**新增** network live 验收 |
| STOP      | trade-off accepted                                     |

---

## Cycle 3 — 禁止 SKIP 当过关（用户锁定）

| 步骤      | 内容                                                       |
| --------- | ---------------------------------------------------------- |
| CLAIM     | partial F0 + SKIP 可 11/11 绿                              |
| DOUBT     | 缩 AC？                                                    |
| RECONCILE | **禁止**；四族 profile 全跑；见 `plan-revision-r2.md` §2.3 |
| STOP      | **用户决策 · 不可回退**                                    |

---

## Cycle 4 — 新建证据契约（用户锁定）

| 步骤      | 内容                                                   |
| --------- | ------------------------------------------------------ |
| CLAIM     | 仓内 manifest v2 为 SSOT                               |
| RECONCILE | **`live_tier_a_evidence_v1.yaml`** 新建；11 源统一信封 |
| STOP      | **用户决策 · 不可回退**                                |

---

## Cycle 5 — dispatch 全量去重（用户 D-08）

| 步骤      | 内容                                   |
| --------- | -------------------------------------- |
| CLAIM     | ponytail 保留 `_live_sync_registry`    |
| RECONCILE | **全量去重**；DataSourceService 金路径 |
| STOP      | **用户决策 · 不可回退**                |

---

## Cycle 6 — B2 主验证器 R4（用户 B2 裁决）

| 步骤      | 内容                                                       |
| --------- | ---------------------------------------------------------- |
| RECONCILE | acceptance 主路径接 `validate_table`；按 `source_bindings` |
| STOP      | **用户决策 · 不可回退**                                    |

---

## Cycle 7 — 11 源同一验收层（用户题7）

| 步骤      | 内容                                                       |
| --------- | ---------------------------------------------------------- |
| RECONCILE | 统一流水线 + 分域 `source_bindings`；`--report` JSON 11 行 |
| STOP      | **用户决策 · 不可回退**                                    |

---

## Cycle 8 — failure_class + ADR（用户题9）

| 步骤      | 内容                                         |
| --------- | -------------------------------------------- |
| RECONCILE | `FAIL_FIXABLE` 必修 · `FAIL_EXTERNAL` 须 ADR |
| STOP      | **用户决策 · 不可回退**                      |

---

## Cycle 9 — mootdx platform matrix（用户题10）

| 步骤      | 内容                            |
| --------- | ------------------------------- |
| RECONCILE | mootdx 纳入 matrix；去掉 bypass |
| STOP      | **用户决策 · 不可回退**         |

---

## Cycle 10 — F0 EasyXT L2 模板（用户调整2）

| 步骤      | 内容                                                                 |
| --------- | -------------------------------------------------------------------- |
| RECONCILE | 四族 profile 在 EasyXT checker **类别**上 L2 扩展；无 runtime import |
| STOP      | **用户决策 · 不可回退**                                              |

---

## 汇总

| 分类      | 项                                                                         |
| --------- | -------------------------------------------------------------------------- |
| 用户锁定  | 无 SKIP · 证据契约 · 同层验收 · B2 R4 · dispatch 去重 · CI · failure_class |
| trade-off | replay+live 双轨；无新 DDL                                                 |
| noise     | 重写整条 incremental 管道（已否决）                                        |

---

## Cycle 14 — 对抗审查 F-01…F-30（2026-07-03）

| ID               | disposition | 证据                                                        |
| ---------------- | ----------- | ----------------------------------------------------------- |
| F-01             | 已修复      | 活卡 §5 R2 取代声明                                         |
| F-02             | 已修复      | ADR-034 Amendment                                           |
| F-03             | 已修复      | contract `failure_class_canonical`                          |
| F-04/05/23       | 已修复      | `to-issues-slices.md` 依赖图 + DISPATCH blocked by EVIDENCE |
| F-06/07/12/15/16 | 已修复      | `to-issues-slices.md` E2/MCR/bypass/manifest/测试 AC        |
| F-08             | 已修复      | `plan-boot.md` pipeline                                     |
| F-09             | 已修复      | contract `status: accepted`                                 |
| F-10             | 已修复      | `plan-spec.md` mootdx matrix 模板                           |
| F-11             | 已修复      | `data_health_cli.md` §5.1.1 四族                            |
| F-13             | 已修复      | contract `failure_artifact` + plan-spec                     |
| F-14             | 已修复      | plan-spec Official API 表                                   |
| F-17/18          | 已修复      | `context_pack.json` evidence 路径 + contract authority      |
| F-19             | 已修复      | inventory contract 行 · eligibility 去 S00                  |
| F-20             | 已修复      | `gitnexus-summary.md` R2                                    |
| F-21/22/30       | 已修复      | REPAIR superseded · archive README · execute 横幅           |
| F-24             | 已修复      | `plan-boot.md` §3 十条指针                                  |
| F-25/26/27       | 已修复      | consolidation · plan.freeze §3.1 · `frozen_revision: R2`    |
| F-28/29          | 已修复      | plan-spec retry + 按源 F0 表                                |

**Ledger：** 30/30 已修复 · 0 阶段外置 · MCR 正文更新留 Execute S-R2-ACCEPT（AC#9）
