# Integration Audit — Round 3 Batch 1

> Plan 5d · 对抗审计后更新

## 1. doc-gap

| 检查                                            | 结果               |
| ----------------------------------------------- | ------------------ |
| BATCH_MAP 8 item IDs → MASTER §2                | PASS               |
| README / PENDING / runtime_versions → implement | PASS（对抗修补后） |
| Source Context Index ↔ three-layer-trace        | PASS               |
| AUDIT Source Trace ↔ §2 AC                      | PASS               |
| implement.jsonl 无原始任务卡泛滥                | PASS               |
| UNRESOLVED + HANDOFF 入 manifest                | PASS               |

## 2. 六类关键信息

| 类别         | ledger 行                                                        | MASTER 归并    | 缺口                  |
| ------------ | ---------------------------------------------------------------- | -------------- | --------------------- |
| decision     | PENDING_USER_DECISIONS, AUDIT_DEFERRED, UNRESOLVED, routing gate | §0.7, §8.3     | 无                    |
| contract     | ops_db_inspect, schema.sql                                       | §6, AC-CLI     | 无                    |
| business     | ROUND3_EARLY_CLOSE, HANDOFF, 016F                                | §1, §13        | 无                    |
| architecture | local_file_system, duckdb, data_sources                          | AC-DB, §6      | 无                    |
| rule         | README, GLOBAL\_\*, runtime_versions, write_manager              | §0.7-0.8, §3.3 | 无                    |
| wiring       | connection, vendor E2E, smoke                                    | §8.1–8.5       | ops 模块待 Execute 建 |

## 3. adversarial

| 攻击面                   | 发现             | 处置                        |
| ------------------------ | ---------------- | --------------------------- |
| inspect 写库             | mutation 风险    | AC-CLI-3 + AUDIT A3         |
| path traversal           | data_root scan   | AUDIT A8 边界测             |
| 017 范围蠕变             | 建模误入         | §3.2 defer + README pointer |
| fixture 冒充 live vendor | 登记口径         | AC-E2E-1 明确 fixture OR    |
| Windows §8.0 RED         | `test -f` 不可用 | 已改 pathlib Python（P1）   |
| 形式 freeze PASS         | 缺三项必读       | 已补 implement（F1-F3）     |

## 4. closure

**integration-audit: PASS**（对抗修补后）

## 5. plan-manifest-audit

| 检查                            | implement | audit                  | check      |
| ------------------------------- | --------- | ---------------------- | ---------- |
| 条数                            | 30        | 8                      | 5          |
| extract/for                     | 全覆盖    | 部分（Audit 口径不同） | 对齐 A1/A5 |
| E14 check ⊆ implement           | —         | —                      | PASS       |
| 新增必读 README/PENDING/runtime | 已列入    | README 已列入 audit    | —          |

详见 `research/adversarial-audit-verification.md`。
