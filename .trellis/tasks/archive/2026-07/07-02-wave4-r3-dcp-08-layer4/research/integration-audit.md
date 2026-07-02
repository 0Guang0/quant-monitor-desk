# Integration Audit — R3-DCP-08（Plan 5d）

## CLAIM → DOUBT → RECONCILE

| CLAIM                   | DOUBT                    | RECONCILE                                                          |
| ----------------------- | ------------------------ | ------------------------------------------------------------------ |
| US_EQ vs CN_A P0        | registry 债是否强制 CN_A | 正交：registry 片独立；架构锚 R3H-07 → US_EQ (ADR-033)             |
| mootdx 全局 primary     | 破坏 baostock 产品路径   | 双轨 primary：domain default=baostock；explicit --source-id mootdx |
| breadth 需 sector/index | scope creep              | ponytail：仅 breadth+calendar                                      |
| 需新 migration          | clean read 是否够        | read-only 聚合；无 migration                                       |

## 六类检查（Plan 期）

| 类   | 状态 | 备注                          |
| ---- | ---- | ----------------------------- |
| 契约 | PASS | ADR-033 · 活卡 §3             |
| 测试 | GAP  | clean e2e 测 Execute 新建     |
| 安全 | PASS | sandbox replay · REQ2-EM 不关 |
| 架构 | PASS | staged 022 保留               |
| 文档 | PASS | Plan 包齐                     |
| 运维 | PASS | registry delta queued         |

## adversarial（对抗性审计）

| 检查项                             | 结果 |
| ---------------------------------- | ---- |
| plan-doubt-review Cycle 1–4        | PASS |
| reference-adoption L 梯仅 参考项目 | PASS |
| ENTRY §5.1 完整性                  | PASS |

## doc-gap

| GAP                                    | 路由               |
| -------------------------------------- | ------------------ |
| `clean_read.py`                        | Execute S08-READ   |
| `test_layer4_us_equity_clean_e2e` 实现 | Execute S08-E2E    |
| registry apply                         | 主会话 coordinator |

**Phase 5d complete · PASS_WITH_GAPS**
