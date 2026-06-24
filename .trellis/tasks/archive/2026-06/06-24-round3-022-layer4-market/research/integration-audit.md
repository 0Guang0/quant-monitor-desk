# Integration Audit — 022 Layer4 market structure

> Plan 5d · doubt-driven-development

## 1. doc-gap

| 检查                                     | 结果                                   |
| ---------------------------------------- | -------------------------------------- |
| BATCH_MAP Batch5 `022` → MASTER §2       | PASS                                   |
| playbook §3.1+§3.3 → MASTER Source Index | PASS                                   |
| playbook §8.2 → MASTER §2.1              | PASS                                   |
| layer4_market contract → §8.4/§8.7       | PASS                                   |
| snapshot_lineage contract → §8.5/§8.6    | PASS                                   |
| 021 snapshot 上游 → §8.6                 | PASS                                   |
| ADV-R3X / R3Y defer → §3.2 register      | PASS                                   |
| slice forbidden 列表 → MASTER §3.3       | PASS                                   |
| 缺失 `layer3_loader_contract.yaml`       | **登记纠偏** — loader+L3 snapshot 替代 |

## 2. 六类关键信息

| 类别         | ledger/implement                | MASTER 归并 | 缺口                          |
| ------------ | ------------------------------- | ----------- | ----------------------------- |
| decision     | BATCH3 gate, D-09, playbook     | §0 / §SCI   | 无                            |
| contract     | layer4 + snapshot_lineage       | §6          | 无                            |
| business     | layer4 module doc               | §4          | 无                            |
| architecture | 03/04 runtime, module boundary  | §4 / §SCI   | 无                            |
| rule         | GLOBAL, staged_acceptance, §2.2 | §0/§10      | 无                            |
| wiring       | L3 snapshot, lineage kernel, WM | §8.5/8.6    | Execute 待建 market_structure |

## 3. adversarial

| 攻击面                  | 处置                               |
| ----------------------- | ---------------------------------- |
| live 全市场扫描         | staged_fixture_only + AC-022-6     |
| 改 ops/staged/registry  | §3.3 forbidden + 停止条件 #2       |
| 复制 Layer5/L1 大表字段 | contract boundaries + AC-022-7     |
| 弱断言假绿              | §5.3 语义断言表 + 五字段 docstring |
| 声称 production-live    | §0 + batch3 gate tests             |
| 输出买卖动作语义        | 任务卡 §8 + contract boundaries    |

## 4. closure

**integration-audit: PASS**（Plan freeze 2026-06-24）

## 5. plan-manifest-audit

| 检查                 | implement                         | audit | check |
| -------------------- | --------------------------------- | ----- | ----- |
| 条数                 | ≥15                               | ≥8    | ≥5    |
| extract/for          | 全覆盖                            | 部分  | A1    |
| validate-plan-freeze | exit 0（Agent-2 复检 2026-06-24） | —     | —     |
