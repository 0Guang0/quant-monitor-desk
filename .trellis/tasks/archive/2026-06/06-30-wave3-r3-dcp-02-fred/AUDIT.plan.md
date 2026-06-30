# AUDIT 计划 — R3-DCP-02 fred macro incremental

> **读者：** 主会话 + A1–A8 子 agent  
> **任务目录：** `.trellis/tasks/06-30-wave3-r3-dcp-02-fred`

---

## 0. 元信息

| 字段            | 值                                                      |
| --------------- | ------------------------------------------------------- |
| 任务 slug       | `wave3-r3-dcp-02-fred`                                  |
| 活卡            | `R3_DCP_02_FRED_INCREMENTAL.md`                         |
| 协议            | debt-lite Phase 8D                                      |
| AUDIT_PROD_ROOT | `.audit-sandbox/user-live`（隔离；禁止 canonical 主库） |

---

## 1. 维度 — Skill 冻结

| 维  | Agent            | Skill                                                     | 本任务   | 已执行 |
| --- | ---------------- | --------------------------------------------------------- | -------- | ------ |
| A1  | audit-spec       | trellis-check + doubt-driven-development                  | 必做     | [ ]    |
| A2  | audit-ponytail   | ponytail-review + doubt-driven-development                | 必做     | [ ]    |
| A3  | audit-security   | security-and-hardening + doubt-driven-development         | 必做     | [ ]    |
| A4  | audit-quality    | code-review-and-quality + doubt-driven-development        | 必做     | [ ]    |
| A5  | audit-completion | verification-before-completion + doubt-driven-development | 必做     | [ ]    |
| A6  | audit-perf       | doubt-driven-development                                  | **SKIP** | [ ]    |
| A7  | audit-ops        | doubt-driven-development                                  | 必做     | [ ]    |
| A8  | audit-test-gap   | testing-guidelines + doubt-driven-development             | 必做     | [ ]    |
| A9  | 主会话           | —                                                         | 必做     | [ ]    |

---

## 2. 维度验证矩阵

| 维  | 验证类型        | 命令 / 检查                                                                            | 环境          | 通过条件                               | 已执行 |
| --- | --------------- | -------------------------------------------------------------------------------------- | ------------- | -------------------------------------- | ------ |
| A1  | read-only       | 对照活卡 §5 AC、`DEBT.plan.md` 边界、禁止 baostock 触及                                | local         | scope 无泄漏；金路径无 adapter bypass  | [ ]    |
| A2  | review-only     | ponytail-review `fred_port` · `fred_incremental*` · CLI 切片                           | local         | 最简 diff；无新依赖；ponytail 注释合理 | [ ]    |
| A3  | static          | `rg FRED_API_KEY` 泄露；canonical DB 写路径；`QMD_ALLOW_LIVE_FETCH` 门                 | local         | 无密钥落盘；fail-closed                | [ ]    |
| A4  | review-only     | watermark 语义 per-series；PK `observation_id`；与 `clean_write_targets` 一致          | local         | 无 trade_date 误用                     | [ ]    |
| A5  | trace-ac        | 活卡 AC ↔ S02-01..05 测试 docstring 五字段                                             | local         | 每条 AC 有测                           | [ ]    |
| A5  | pytest          | `uv run pytest tests/test_fred_macro_incremental*.py -q`                               | local/ci      | exit 0                                 | [ ]    |
| A5  | full            | `uv run pytest -q`                                                                     | local/ci      | 全绿                                   | [ ]    |
| A6  | —               | **跳过**                                                                               | —             | SKIP（见 §2.2）                        | [ ]    |
| A7  | cli-sandbox     | `qmd data sync --domain macro_series --source-id fred --dry-run`；隔离 `QMD_DATA_ROOT` | audit-sandbox | 无 canonical 写                        | [ ]    |
| A8  | pytest-isolated | 空表/多 series watermark；无 key 负例；幂等                                            | audit-sandbox | 边界测绿；五字段齐全                   | [ ]    |

### 2.1 参考项目 cite 抽检（A1/A8 横切）

- Execute 改动须含 `reference-adoption-dcp02.md` 等级 + 源码锚点
- 无 cite 的 port/CLI 改动 = **BLOCKING**

### 2.2 A6 SKIP 理由

本任务为 **Wave 3 tracer bullet**：单源、P0 series whitelist（≤10 series）、`MAX_ROWS_PER_SERIES=500` 硬 cap；无批量并行或大数据扫描性能 AC。性能优化 defer Wave 4 宏观扩展。

---

## 3. Audit Source Trace

| Item         | 原文                                | AC                                       | 证据                                   |
| ------------ | ----------------------------------- | ---------------------------------------- | -------------------------------------- |
| 活卡         | `R3_DCP_02_FRED_INCREMENTAL.md` §5  | watermark / replay / live / 幂等         | Execute 测试                           |
| INDEX        | `R3_DCP_TO_ISSUES_INDEX.md` §2      | L1/L2/L3 调研                            | `research/reference-adoption-dcp02.md` |
| 金路径       | R3H-10 / R3H-08 归档                | `datasource_service` + `run_incremental` | `test_fred_macro_incremental_e2e.py`   |
| Macro schema | R3H-06 · `clean_write_targets.py`   | `axis_observation` PK                    | `test_r3h06_clean_schema.py`（回归）   |
| Env gate     | ADR-027 · `product_live_gate.py`    | `QMD_ALLOW_LIVE_FETCH`                   | live smoke 测                          |
| 协调         | `00-MAIN-SESSION-COORDINATOR.md` §4 | 共享文件锁                               | diff 范围审查                          |
| 调研         | `reference-adoption-r3h08.md`       | fred Tier A 先例                         | 不重复发明 runner                      |

---

## 4. Audit DoD

- [ ] 7.pre `gitnexus-audit-summary.md`（Execute handoff 后）
- [ ] A1–A8 各维 `research/audit-a{n}-report.md`（A6 SKIP 记录理由）
- [ ] `audit.report.md` 草稿 + §4.3 findings
- [ ] A9 ledger：每项 {已修复, 阶段外置}
- [ ] Repair 后 `uv run pytest -q` exit 0

---

## 5. 禁止事项（审计硬门槛）

- 生产 canonical `data/duckdb/` 被本轨测试或 CLI 写入
- `baostock_port` / CN bar 域 diff
- 未 env-gate 的真网 live 默认开启
- 绕过 `DataSourceService` 的 fred fetch
- 与轨 A 同时修改 `sync/watermark*.py`（若存在）
- 本轨修改 `sync/orchestrator.py` 或 `sync/runners.py`（协调手册 §4 共享锁）
