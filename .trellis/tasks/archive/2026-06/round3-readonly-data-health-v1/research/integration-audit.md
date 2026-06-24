# Integration Audit — read-only data health v1

> Plan 5d · doubt-driven-development

## 1. doc-gap

| 检查                                                     | 结果 |
| -------------------------------------------------------- | ---- |
| MAP §2.2 C-20 → MASTER §3 allowed/forbidden              | PASS |
| Playbook §3.1 共用底座 **每一行** → Source Context Index | PASS |
| Playbook §3.2 C-20 **每一行** → Source Context Index     | PASS |
| R3Y 九切片 → §8.1–8.9                                    | PASS |
| v2 evidence 路径 → implement + §8.9                      | PASS |
| rule_id 子集 → §5.3 / §8.3–8.6                           | PASS |

## 2. 六类关键信息

| 类别         | ledger/implement                       | MASTER 归并 | 缺口                     |
| ------------ | -------------------------------------- | ----------- | ------------------------ |
| decision     | REQ2-EM DEFERRED, staged-only          | §0          | 无                       |
| contract     | data_quality_rules, source_route       | §6          | 无                       |
| business     | R3Y 任务卡, evidence bundle            | §2, §8.9    | 无                       |
| architecture | ops modules, data_health_cli 设计      | §4, §6      | 无                       |
| rule         | GLOBAL, playbook §2.2                  | §5, §0      | 无                       |
| wiring       | db_inspector, staged_pilot, validators | §8.2+       | Execute 待建 data_health |

## 3. adversarial

| 攻击面                      | 处置                                      |
| --------------------------- | ----------------------------------------- |
| CLI 空壳无规则              | 九切片强制 §8.3–8.6 语义测                |
| 写 production DB            | forbidden + `production_db_mutated` 断言  |
| live fetch                  | forbidden + `source_fetch_performed` 断言 |
| 改 staged_evidence / layer4 | §3.3 forbidden；停止条件 #2               |
| 弱断言 call-only            | GLOBAL_TESTING_POLICY + §5.3              |
| 声称 production-live        | §0 + gate_rationale 字段                  |
| 并发改 registry             | §3.3；主会话批处理                        |

## 4. closure

**integration-audit: PASS**（Plan freeze 2026-06-24）

## 5. plan-manifest-audit

| 检查                 | implement                | audit | check |
| -------------------- | ------------------------ | ----- | ----- |
| 条数                 | ≥15                      | ≥8    | ≥5    |
| R3Y-DH-01..09        | §8 覆盖                  | —     | —     |
| validate-plan-freeze | **exit 0**（2026-06-24） | —     | —     |
