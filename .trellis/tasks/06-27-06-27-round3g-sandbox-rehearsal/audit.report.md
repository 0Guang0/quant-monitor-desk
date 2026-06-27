# Audit Report — R3G-01 Sandbox Clean-Write Rehearsal

**日期：** 2026-06-27 · **分支：** `feature/round3g-sandbox-rehearsal`  
**总判定：** **PASS_WITH_FIXES**（功能可合并前须闭环全部 P0–P3）

## 维度结论

| 维            | 判定                           | 证据                            |
| ------------- | ------------------------------ | ------------------------------- |
| A1 Spec       | FAIL_WITH_FIXES                | `research/audit-evidence/a1.md` |
| A2 Ponytail   | PASS                           | `a2.md`                         |
| A3 Security   | PASS                           | `a3.md`                         |
| A4 Quality    | REQUEST CHANGES                | `a4.md`                         |
| A5 Completion | CONDITIONAL / handoff BLOCKING | `a5.md`                         |
| A6 Perf       | SKIP                           | `a6.md`                         |
| A7 Ops        | PASS                           | `a7.md`                         |
| A8 Test gap   | PASS                           | `a8.md`                         |

## 合并修复清单（去重后 · 全量 P0–P3）

### P0 — 必须修复

| ID            | 来源               | 修复                                                                                |
| ------------- | ------------------ | ----------------------------------------------------------------------------------- |
| R3G-REP-P0-01 | A4-P0-01           | DH FAIL/BLOCKED 时拒绝 `_sandbox_clean_write`                                       |
| R3G-REP-P0-02 | A4-P0-02, A3-P2-02 | 移除/标注 synthetic validation；与 DH 结果联动或显式 `synthetic_admission`          |
| R3G-REP-P0-03 | A4-P0-03, A2/A7    | per-source `rollback_artifact_{source_id}.json` 或聚合数组 + 测试                   |
| R3G-REP-P0-04 | A5-E01/E02         | 补齐 `execute-evidence/9.1–9.6-green.txt`（真实 pytest 输出）；9.0-green 含终端输出 |

### P1

| ID            | 来源            | 修复                                                                        |
| ------------- | --------------- | --------------------------------------------------------------------------- |
| R3G-REP-P1-01 | A1-01, A4-P1-04 | 按 domain materialize 或 frozen 显式 smoke-only + 测试对齐                  |
| R3G-REP-P1-02 | A1-02, A4-P1-02 | `route_plan` 落盘 per-source                                                |
| R3G-REP-P1-03 | A4-P1-01        | 顶层/每源 report 满足契约 `required_report_fields`                          |
| R3G-REP-P1-04 | A4/A8           | 强化 DH profile 映射测试（spy 三 profile）                                  |
| R3G-REP-P1-05 | A8              | `DATA_ROOT/duckdb/quant_monitor.duckdb` 拒绝 pytest                         |
| R3G-REP-P1-06 | A8              | runner 级 FRED 无 artifact 集成测                                           |
| R3G-REP-P1-07 | A4-P1-05        | `validate_source_caps` 读契约 `metadata_only`/`requires_user_authorization` |
| R3G-REP-P1-08 | A4-P1-06        | loader cap 复用 plan/契约                                                   |
| R3G-REP-P1-09 | A4-P1-07, A8    | RG HARD_STOP、DH-fail 拒绝写、rollback 一致性测试                           |
| R3G-REP-P1-10 | A3-P2-01        | FRED auth 校验 `FRED_API_KEY` env（live 路径 fail-closed）                  |

### P2

| ID            | 来源     | 修复                                            |
| ------------- | -------- | ----------------------------------------------- |
| R3G-REP-P2-01 | A8       | `max_window_days` 超 cap 负向测                 |
| R3G-REP-P2-02 | A8       | `cninfo` loader 强断言                          |
| R3G-REP-P2-03 | A1-04/05 | FRED fixture 入 `tests/fixtures/`；证据路径文档 |
| R3G-REP-P2-04 | A1-08    | 回滚或登记 config/fred_fetch_ports/.env 变更    |
| R3G-REP-P2-05 | A4/OOB   | 契约补 `data_health_summary` 或 frozen 对齐     |
| R3G-REP-P2-06 | A5-E05   | conflict_check payload 断言                     |
| R3G-REP-P2-07 | A1-06/A5 | GitNexus analyze（若可）                        |

### P3

| ID            | 来源  | 修复                                        |
| ------------- | ----- | ------------------------------------------- |
| R3G-REP-P3-01 | A2    | 删 `__init__.py` 桶、死代码 `_resolve_path` |
| R3G-REP-P3-02 | A2    | mutation proof 薄包装（可选）               |
| R3G-REP-P3-03 | A1-09 | 契约 version bump 若改 schema               |
| R3G-REP-P3-04 | A6    | loader evidence row cap（可选常量）         |
| R3G-REP-P3-05 | A2/A8 | 测试 setup 合并、弱断言收紧                 |

## 修复后验证

1. `uv run pytest -q` 全库 0 失败
2. Tier A R3G 套件全绿
3. `validate-execute-handoff` exit 0
4. 主会话逐项 closure 表
