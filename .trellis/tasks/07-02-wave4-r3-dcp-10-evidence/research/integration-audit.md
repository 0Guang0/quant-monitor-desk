# Integration Audit — R3-DCP-10 Plan

> Phase 5d · 2026-07-02

## CLAIM → DOUBT → RECONCILE

| CLAIM | DOUBT | RECONCILE |
| --- | --- | --- |
| mootdx 最适合 P0 | baostock 是 plan YAML primary | ADR-031 冻结 mootdx；baostock 后续 wave |
| bundle_layer5_provenance 够用 | 缺 schema_hash | S01 扩展 + dataset id 编码 |
| 023A 已够 | 需 DB evidence_chain | Out of scope；validator + lineage 断言 |
| replay 够 G5 | 用户要 live | replay 含真实 finalize_bundle；live optional |

## 六类检查（Plan 期）

| 类 | 状态 | 备注 |
| --- | --- | --- |
| 契约 | PASS | ADR-031 + snapshot_lineage + sandbox_clean_write |
| 测试 | PASS | S01/S02 测定义清晰 |
| 安全 | PASS | 无参考 runtime；WriteManager 金路径 |
| 架构 | PASS | 桥接 helper；不改 orchestrator 核心 |
| 文档 | PASS | Plan 包 + provenance 映射表 |
| 运维 | PASS | ACC G5 子集 S03 |

## adversarial（对抗性审计）

| 检查项 | 结果 |
| --- | --- |
| plan-doubt-review Q1–Q5 | PASS |
| 参考 L 梯仅 `参考项目/**` | PASS |
| 不假关全链 E2E | PASS |
| GitNexus impact LOW | PASS |

## doc-gap → Execute

| GAP | Owner | 路由 |
| --- | --- | --- |
| `layer5_evidence/provenance.py` | Execute S01 | S01 |
| `test_layer5_provenance_bridge.py` | Execute S01 | S01 |
| `test_layer5_mootdx_bar_clean_e2e.py` | Execute S02 | S02 |
| ACC G5 台账行 | Execute S03 | S03 |

**Phase 5d complete · PASS（GAP 已登记 owner → Execute S01/S02/S03；Plan 对抗审计见 `plan-audit-dcp10.md`）**

## 对齐检查

| 项 | 状态 |
| --- | --- |
| DCP-05 前置 | ✅ mootdx S08 |
| R3H-08 env-gate | ✅ ADR-027 只读 |
| 待修复清单 ACC | ✅ G5 子集 Execute S03 |
