# AUDIT 计划 — round3-022-layer4-market

> 读者：主会话 + A1–A8 · audit.jsonl 第一条 = 本文件

---

## 0. 元信息

| 字段            | 值                                       |
| --------------- | ---------------------------------------- |
| 任务 slug       | `06-24-round3-022-layer4-market`         |
| AUDIT_PROD_ROOT | `.audit-sandbox/r3-022-audit-prod-equiv` |

## 1. 维度 — Skill 冻结

| 维  | Agent            | Skill                                                     | 本任务   | 已执行   |
| --- | ---------------- | --------------------------------------------------------- | -------- | -------- |
| A1  | audit-spec       | trellis-check + doubt-driven-development                  | 必做     | [ ]      |
| A2  | audit-ponytail   | ponytail-review + doubt-driven-development                | 必做     | [ ]      |
| A3  | audit-security   | security-and-hardening + doubt-driven-development         | 必做     | [ ]      |
| A4  | audit-quality    | code-review-and-quality + doubt-driven-development        | 必做     | [ ]      |
| A5  | audit-completion | verification-before-completion + doubt-driven-development | 必做     | [ ]      |
| A6  | audit-perf       | doubt-driven-development                                  | **不用** | [ ] SKIP |
| A7  | audit-ops        | doubt-driven-development                                  | 必做     | [ ]      |
| A8  | audit-test-gap   | testing-guidelines + doubt-driven-development             | 必做     | [ ]      |
| A9  | 主会话           | —                                                         | 必做     | [ ]      |

## 2. 维度验证矩阵

| 维  | 验证类型        | 命令 / 检查                                                                                     | 环境            | 通过条件                         | 已执行 |
| --- | --------------- | ----------------------------------------------------------------------------------------------- | --------------- | -------------------------------- | ------ |
| A1  | read-only       | 对照 `layer4_market_contract.yaml`、`layer4_market_structure.md`、MASTER §2/§3.2、playbook §8.2 | local           | 无 scope 泄漏；defer 边界 intact | [ ]    |
| A2  | review-only     | ponytail-review `backend/app/layer4_markets/market_structure.py` + `tests/` 增量                | local           | 最小 diff；复用 L2/L3 模式       | [ ]    |
| A3  | static          | `rg` live fetch / 改 forbidden 路径 / 三 registry 写                                            | local           | 无 mutation                      | [ ]    |
| A4  | review-only     | as_of / breadth / lineage 链一致                                                                | local           | 无阻断质量问题                   | [ ]    |
| A5  | trace-ac        | AC-022-1..8 ↔ §8 evidence + playbook §8.2                                                       | local           | 全 AC 可追溯                     | [ ]    |
| A5  | cli-sandbox     | `.audit-sandbox/r3-022` 复跑 `test_layer4_market_structure.py`                                  | audit-sandbox   | 与 Execute 一致                  | [ ]    |
| A5  | audit-prod-path | 复制树到 `AUDIT_PROD_ROOT`；Tier A pytest；prod data hash 不变                                  | audit-prod-path | 无污染（staged N/A）             | [ ]    |
| A6  | —               | **本任务跳过 — builder 无 hot path/SLA**                                                        | —               | SKIP                             | [ ]    |
| A7  | cli-sandbox     | 确认无 migration/DB 写；sandbox 无 `data/` 污染                                                 | audit-sandbox   | 无 prod 写                       | [ ]    |
| A8  | pytest-isolated | 五字段 docstring + ponytail 测试代码；补边界：空 fixture / 非交易日                             | audit-sandbox   | 新测绿或记入 audit.report        | [ ]    |
| A8  | audit-prod-path | 复跑 `test_batch3_staged_downstream_gate.py`                                                    | audit-prod-path | 全绿                             | [ ]    |

### 2.2 A6 SKIP

本任务跳过性能审计 — market structure builder 仅处理小型 staged fixture。

## 3. Audit Source Trace

| Item        | 原文                                               | AC           | 证据                              |
| ----------- | -------------------------------------------------- | ------------ | --------------------------------- |
| `022`       | `022_implement_layer4_market_structure.md`         | AC-022-\*    | `test_layer4_market_structure.py` |
| contract    | `layer4_market_contract.yaml`                      | AC-022-2,3,7 | contract 测试名                   |
| module      | `layer4_market_structure.md`                       | AC-022-1..3  | builder 断言                      |
| lineage     | `snapshot_lineage_contract.yaml`                   | AC-022-4,5   | contract 测试名                   |
| L3 上游     | `layer3_chains/snapshot_builder.py`                | AC-022-4     | upstream_snapshot_ids 可选        |
| staged gate | `BATCH3_STAGED_DOWNSTREAM_GATE.md`                 | AC-022-6     | batch3 gate tests                 |
| playbook    | `WAVE_C_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` §8.2 | AC-022-8     | §2.1 勾销表                       |
| defer       | MASTER §3.2 ADV-R3X / R3Y                          | —            | 未改三 registry                   |
| L2/L3 模式  | `snapshot_builder.py` + `snapshot_lineage.py`      | AC-022-4     | lineage 复用                      |

## 4. Audit DoD

- [ ] 7.pre `gitnexus-audit-summary.md`
- [ ] A1–A8（A6 SKIP）
- [ ] A9 汇总 PASS / FAIL
- [ ] §3.2 defer 边界未被 Execute 越界关闭
- [ ] playbook §8.2 子 AC 全勾
