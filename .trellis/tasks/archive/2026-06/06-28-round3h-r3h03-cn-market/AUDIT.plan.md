# Audit 计划 — R3H-03 CN Market Adapters

> **读者：** 主会话 + A1–A8  
> **索引：** `EXECUTION_INDEX.md` §5

| 字段        | 值                                   |
| ----------- | ------------------------------------ |
| slug        | `06-28-round3h-r3h03-cn-market`      |
| audit.jsonl | 第一条 = 本文件                      |

---

## 0.1 Trace Authority Set

| 类别                | 文件                                                                                                                                            | 用途            |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| 原始任务卡          | `docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_03_CN_MARKET_ADAPTERS.md`               | scope / AC      |
| task README         | `docs/implementation_tasks/README.md`                                                                                                           | 入口合规        |
| task input index    | `docs/implementation_tasks/TASK_INPUT_CONTEXT_INDEX.md`                                                                                         | 必读上下文      |
| unresolved coverage | `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`                                                                                    | G11/G16 等      |
| project map         | `MIGRATION_MAP.md`                                                                                                                              | docs/specs 边界 |
| round map           | `PROJECT_IMPLEMENTATION_ROADMAP.md` §5                                                                                                          | Batch 3H        |
| 执行索引            | `EXECUTION_INDEX.md`                                                                                                                            | 血缘 + manifest |
| 3G gaps             | `docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_MASS_REHEARSAL_OPEN_GAPS.md`                            | G11/G16         |
| omission-check      | `research/project-map-omission-check.md`                                                                                                        | 地图倒查        |
| integration-ledger  | `research/integration-ledger.md`                                                                                                                | context packing |
| batch playbook      | `BATCH_3H_COORDINATOR_PLAYBOOK.md`                                                                                                              | registry 合并   |

---

## 1. 本任务验证覆写

| 维  | 本任务 | 命令 / 检查                                                                                                                                                                                                                              | 环境          | 通过条件       | 已执行 |
| --- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- | -------------- | ------ |
| A1  | 必做   | 对照活卡 §9–§12、十源终态、§2.8 主库禁止；未扩 R3H-04 source（kalshi/polymarket/web_search）                                                                                                                                          | local         | 无 scope 漏/扩 | [ ]    |
| A5  | 必做   | 十源 × 八项闭环（§5.1 表）；每 Step GREEN 证据 `execute-evidence/`；registry manifest §9.8                                                                                                                                              | local         | AC 全覆盖      | [ ]    |
| A3  | 必做   | rg `参考项目` import；rg `akshare` primary route 升级；QMT 无授权 READY                                                                                                                                                                  | local         | fail-closed    | [ ]    |
| A4  | 必做   | 未授权 QMT/iFinD；akshare primary 负例；cap 溢出；silent primary 替换                                                                                                                                                                    | audit-sandbox | 对抗 fixture   | [ ]    |
| A6  | 不用   | **SKIP** — 无 hot path SLA；CN 低频 batch/replay                                                                                                                                                                                         | —             | —              | [ ]    |
| A7  | 必做   | 无新增写主库 CLI；sandbox promote 仍拒 canonical DB                                                                                                                                                                                        | audit-sandbox | CLI 边界       | [ ]    |
| A8  | 必做   | `pytest tests/test_cn_market_adapters.py tests/test_source_route_planner.py -q -k "baostock or cninfo or akshare or tdx or mootdx or eastmoney or sina or ifind or qmt or xqshare or layer_cn or evidence_contract" --basetemp=.audit-sandbox/pytest`；附录 `test_source_capabilities -k r3h03` | audit-sandbox | 全绿           | [x]    |

---

## 2. DoD（主会话）

- [ ] 7.pre → `research/gitnexus-audit-summary.md`
- [ ] 派发 A1–A8 → `audit.report.md`
- [ ] PASS / PASS_WITH_FIXES / FAIL
