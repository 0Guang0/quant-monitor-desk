# Integration Audit — 020 Layer3 loader

> Plan 5d · doubt-driven-development

## 1. doc-gap

| 检查                                | 结果 |
| ----------------------------------- | ---- |
| BATCH_MAP Batch4 `020` → MASTER §2  | PASS |
| contract hard rules → §8.3–8.5      | PASS |
| 019 loader 模式 → §8.2              | PASS |
| registry 路径纠偏 → source-index §A | PASS |
| lineage 写权限 → defer 021/023A     | PASS |
| slice forbidden 列表 → MASTER §3.3  | PASS |

## 2. 六类关键信息

| 类别         | ledger/implement                      | MASTER 归并 | 缺口                |
| ------------ | ------------------------------------- | ----------- | ------------------- |
| decision     | BATCH3 gate, D-09                     | §0          | 无                  |
| contract     | layer3_loader, snapshot_lineage(只读) | §6          | 无                  |
| business     | registry v1.2 形态                    | §4          | 无                  |
| architecture | layer3 module, 03/04 runtime          | §4          | 无                  |
| rule         | GLOBAL, staged_acceptance             | §0/§10      | 无                  |
| wiring       | sensor_loader 019                     | §8.2        | Execute 待建 loader |

## 3. adversarial

| 攻击面                 | 处置                                 |
| ---------------------- | ------------------------------------ |
| 全量 registry 默认加载 | `staged_fixture_only` + fixture 子集 |
| 弱校验假绿             | §5.3 语义断言表                      |
| event_only 当行情锚    | AC-020-3 专用测                      |
| scope 改 layer2        | §3.3 forbidden + AUDIT A1            |
| 声称 production-live   | §0 + batch3 gate tests               |

## 4. closure

**integration-audit: PASS**（Plan freeze 2026-06-23）

## 5. plan-manifest-audit

| 检查                 | implement   | audit | check |
| -------------------- | ----------- | ----- | ----- |
| 条数                 | ≥15         | ≥8    | ≥5    |
| extract/for          | 全覆盖      | 部分  | A1    |
| validate-plan-freeze | exit 0 待跑 | —     | —     |
