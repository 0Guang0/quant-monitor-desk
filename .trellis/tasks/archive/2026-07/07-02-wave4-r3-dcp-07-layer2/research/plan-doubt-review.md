# Plan Doubt Review — R3-DCP-07

> doubt-driven-development · Phase 5c

## 质疑 1：P0 传感器选 VIX 还是 HYG？

| 轮次      | 内容                                                                                 |
| --------- | ------------------------------------------------------------------------------------ |
| CLAIM     | 任选 registry 中一资产即可                                                           |
| EXTRACT   | L2-VIX→FRED/VIXCLS→axis_observation；L2-HYG→ETF→security_bar_1d                      |
| DOUBT     | 哪条 clean 证据链最稳？                                                              |
| RECONCILE | **L2-VIX**：DCP-05 fred + DCP-06 S03 已证明 VIXCLS clean replay；单表 macro 映射简单 |
| STOP      | ADR-032 冻结 L2-VIX                                                                  |

**分类：** actionable → ADR-032

## 质疑 2：是否要扩全 staging→clean pipeline？

| 轮次      | 内容                                                 |
| --------- | ---------------------------------------------------- |
| CLAIM     | module doc §7 要求完整 pipeline                      |
| DOUBT     | 本票 scope？                                         |
| RECONCILE | 活卡 §6 非目标 + F-019-R02 defer；本票只读既有 clean |
| STOP      | 阶段外置 Batch 4/5 task 020–022                      |

**分类：** noise（已 defer）

## 质疑 3：registry mode 放开会不会误开 production live？

| 轮次      | 内容                                                                |
| --------- | ------------------------------------------------------------------- |
| CLAIM     | 去掉 staged_fixture_only 即可                                       |
| DOUBT     | 全资产 live 风险？                                                  |
| RECONCILE | P0-only `production_clean_replay` 白名单；其余资产仍 staged_fixture |
| STOP      | S00 AC + loader 测试                                                |

**分类:** actionable → S00

## 质疑 4：ACC-LAYER-E2E 能否在 DCP-07 全关？

| 轮次      | 内容                                                       |
| --------- | ---------------------------------------------------------- |
| CLAIM     | 一条 L2 传感器 = 全链 PASS                                 |
| DOUBT     | 台账 L3–L5？                                               |
| RECONCILE | **仅 L2 子集**关账；L3–L5 阶段外置 DCP-08/10 + R3H-05-GATE |
| STOP      | S02 登记 待修复清单                                        |

**分类:** actionable → S02

## 质疑 5：live 网是否必须？

| 轮次      | 内容                                                                     |
| --------- | ------------------------------------------------------------------------ |
| CLAIM     | 活卡写「真市况」= live                                                   |
| DOUBT     | DCP-06 先例？                                                            |
| RECONCILE | replay clean 种子 = 真 Tier A clean 路径；live 须 env-gate（非本票默认） |
| STOP      | plan-spec ASSUMPTIONS                                                    |

**分类:** trade-off → replay default
