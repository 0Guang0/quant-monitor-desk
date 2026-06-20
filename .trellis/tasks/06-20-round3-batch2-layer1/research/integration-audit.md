# Integration Audit — Round 3 Batch 2 Layer 1

> Plan 5d · 对抗审计（Composer 2.5 ×2）后更新

## 1. doc-gap

| 检查                              | 结果                                                      |
| --------------------------------- | --------------------------------------------------------- |
| BATCH_MAP Batch2 → MASTER §2      | PASS（修补后 AC-017-1..8,018-1..6,LINEAGE-1..4,WRIT,RES） |
| 五轴三件套 → implement.jsonl      | PASS（15 文件逐条列入）                                   |
| lineage 持久化模型                | PASS（`axis_snapshot_lineage` + §3.4 全字段）             |
| module §13 → §8 测试              | PASS                                                      |
| SHADOW 三名 → §8.2                | PASS                                                      |
| adversarial-audit-verification.md | PASS                                                      |
| 018 输入缺口                      | PASS（§13 注明借用 017 契约）                             |

## 2. 六类关键信息

| 类别         | ledger/implement                                             | MASTER 归并       | 缺口         |
| ------------ | ------------------------------------------------------------ | ----------------- | ------------ |
| decision     | PENDING, ADR-0003, Batch1+R2.6 gates                         | §0.7, AC-PRE      | 无           |
| contract     | layer1_axis, snapshot_lineage, resource_limits               | §6, AC-\*         | 无           |
| business     | ROUND3_EARLY_CLOSE, 五轴 specs                               | §1.3, §8.5        | 无           |
| architecture | layer1 module, duckdb, 03/04 runtime                         | §4, §8.1          | 无           |
| rule         | README, GLOBAL\_\*, staged_acceptance, write_manager         | §0.7-0.8, §10     | 无           |
| wiring       | write_manager, validation_gate, data_quality, resource_guard | §8.5, AC-WRIT/RES | Execute 待建 |

## 3. adversarial

| 攻击面            | 处置                                    |
| ----------------- | --------------------------------------- |
| 五轴 YAML 漏读    | implement 逐文件 + 测试设计稿           |
| lineage 空壳      | `axis_snapshot_lineage` 表 + 持久化测试 |
| WriteManager 绕过 | AC-WRIT-1 强制集成测                    |
| 假绿弱断言        | research/\*-tests.md 语义断言表         |
| AUDIT §2 缩水     | 补 prod-path + A6 perf 命令             |

## 4. closure

**integration-audit: PASS**（对抗修补后；见 `adversarial-audit-verification.md`）

## 5. plan-manifest-audit

| 检查                 | implement     | audit             | check       |
| -------------------- | ------------- | ----------------- | ----------- |
| 条数                 | 52            | 12                | 6           |
| extract/for          | 全覆盖        | 部分              | A1 对齐     |
| 五轴 YAML            | 5×3 文件      | common_axis_rules | sample yaml |
| validate-plan-freeze | exit 0 待复跑 | —                 | —           |
