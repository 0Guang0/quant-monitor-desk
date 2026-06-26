# Plan 对抗性审计报告 — R3FR-05

> Agent: 2955e567 · 主会话修复轮次 2026-06-26 · **全部项已修复**

## P0（已修复）

| ID    | 问题                         | 修复                                                 |
| ----- | ---------------------------- | ---------------------------------------------------- |
| P0-01 | openbb 缺 capability         | 活卡/frozen §9.2 + design §1.6 + EXECUTION_INDEX 9.2 |
| P0-02 | qmd_target_files 路径矛盾    | 活卡/frozen §1 → datasource_registry                 |
| P0-03 | 9.0 Boot RED=true            | EXECUTION_INDEX 9.0 → pytest ModuleNotFound          |
| P0-04 | 9.6 缺全库 pytest            | §9.6 + §2.1 A+                                       |
| P0-05 | registry 22→23 计数          | plan-boot / overview / EXECUTION_INDEX §0            |
| P0-06 | openbb registry 字段未规格化 | 活卡 §9.2 YAML 模板                                  |

## P1（已修复）

| ID    | 问题                                | 修复                                                 |
| ----- | ----------------------------------- | ---------------------------------------------------- |
| P1-01 | R3G production_default_allowed 漂移 | design §5 canonical enabled                          |
| P1-02 | catalog↔registry 无映射             | design §1.5 + 具名测试 §2                            |
| P1-03 | 9.4「若有」弱化                     | 必做 test_provider_catalog_contractRefs              |
| P1-04 | guardrails 无具名 closure           | §9.5 test_r3fr05ProviderCatalogClosure               |
| P1-05 | registry 无 file lock               | playbook §2                                          |
| P1-06 | capability 对齐可选                 | §2 必做 test_catalogStatus_matchesCapabilityRegistry |
| P1-07 | candidate/enabled 无专测            | test_productionDefaultCandidate_distinctFromEnabled  |
| P1-08 | gitnexus 文件名                     | frozen §9.0 execute-summary 明确                     |
| P1-09 | provider 分组不清                   | design §1.2 表                                       |
| P1-10 | enabled_by_default 无专测           | test_catalogEnabledByDefault_notLooserThanRegistry   |

## P2（已修复）

| ID    | 问题                      | 修复                         |
| ----- | ------------------------- | ---------------------------- |
| P2-01 | context_pack 空           | context_router 重跑          |
| P2-02 | ledger 缺六类             | integration-ledger 重写      |
| P2-03 | implement.jsonl 薄        | §3 扩 manifest + freeze 再生 |
| P2-04 | integration-audit 假 PASS | 改 remediated PASS           |
| P2-05 | v4 freeze 弱于 manifest   | EXECUTION_INDEX §6 注明      |
| P2-06 | 缺 Context Packing Gate   | plan.freeze §3               |
| P2-07 | AUDIT 薄                  | A8 扩三文件+source_registry  |
| P2-08 | loop 未预置               | §9.6 loop --fix + design §2  |
| P2-09 | test_catalog 未写         | §9.6 --fix                   |
| P2-10 | required fields 未入 §2   | original-plan-trace + §2     |
| P2-11 | 五字段未索引              | GLOBAL_TESTING_POLICY §3     |
| P2-12 | check/audit jsonl 薄      | freeze 再生                  |

## P3（已修复）

| ID    | 问题              | 修复                                            |
| ----- | ----------------- | ----------------------------------------------- |
| P3-01 | 用户未批准        | plan.freeze §4 保留待审阅（流程项，非计划缺陷） |
| P3-02 | frozen 跳 §7      | 活卡补 §7                                       |
| P3-03 | source-index 遗漏 | §B 扩 batch/global/map                          |
| P3-04 | implement.md 薄   | handoff checklist                               |
| P3-05 | 9.6 无 RED        | §1 注明 gate-only / 基线绿则跳过 RED            |
| P3-06 | priority P2       | task.json → P1                                  |

## 开放项

无（Execute 前仅剩用户 §4 批准）。
