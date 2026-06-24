# Audit Report — round3-readonly-data-health-v1（Repair C-20）

> **Repair Agent：** trellis-implement · model: composer-2.5  
> **工作区：** `quant-monitor-desk-wt-r3-data-health`  
> **日期：** 2026-06-24

---

## 总判定

| 项                   | 值                                              |
| -------------------- | ----------------------------------------------- |
| **Repair 判定**      | **PASS_WITH_MERGE_GATE**                        |
| **BLOCKING 修复**    | **14/15 CLOSED**（余 A5-B04 提交锚点 → 主会话） |
| **OPEN（阻断业务）** | **0**                                           |
| **DEFERRED**         | **5**（Batch6 / merge 后 hygiene）              |
| **A6**               | SKIP（已记入 `audit_matrix.json`）              |

---

## 阻断项修复摘要

| ID             | 修复                                                                                                        |
| -------------- | ----------------------------------------------------------------------------------------------------------- |
| A1-01 / A5-B03 | `_checks_from_bundle` 读 `raw_file_paths`/`relative_paths`，调用 `check_daily_bars` / `check_metadata_rows` |
| A4-01          | `check_lineage_entry` v2 回退 `request.source_id`、`default_as_of`；消除 v2 假 FAIL                         |
| A5-B01/B02     | `loop_maintain.py --fix`；`implement.jsonl` 补 `data_health*.py`；`validate-plan-freeze` exit 0             |
| A3 P2          | `SourceNotFoundError` fail-closed；`evidence_dir_within_project` sandbox                                    |
| A8 集成        | v2 断言 `PASS/WARN`；`bad_bar_bundle` service 路径 FAIL                                                     |

---

## ponytail 瘦身项

| 项                | 动作                                                                                                                                                     | 约节省 |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| 死代码            | 删除 `default_v2_evidence_dir`、`_DEFAULT_V2_EVIDENCE`                                                                                                   | ~8 行  |
| 复用 staged_pilot | `_equity_bar_rows`、`_resolve_evidence_path` 替代自写行规范化                                                                                            | ~45 行 |
| 合并 helper       | 删除 `_raw_manifest_items`、`_checks_from_payload_paths`、`_payload_paths_from_entry`、`_domain_and_source_from_entry`、`_rows_from_payload`；单循环内联 | ~55 行 |
| lineage registry  | 单循环 `registry_ids` + `SourceNotFoundError` fail-closed                                                                                                | ~18 行 |
| CLI 测试          | 去掉 21 行内联 mkdir/manifest；用 `tests/fixtures/data_health/good_bundle`                                                                               | ~21 行 |
| evidence_path     | `dataclasses.replace` 替代手工 `DataHealthCheckResult` 复制                                                                                              | ~24 行 |

**净减约 170 行**（相对 Repair 前中间态），无新增依赖，无只为好看的 wrapper 层。

---

## pytest 复跑（Repair 后）

| 命令                                                                              | exit | 摘要                                                                                       |
| --------------------------------------------------------------------------------- | ---- | ------------------------------------------------------------------------------------------ |
| `uv run pytest tests/test_ops_data_health.py -q`                                  | 0    | **23 passed**                                                                              |
| `uv run ruff check backend/app/ops/data_health*.py tests/test_ops_data_health.py` | 0    | All checks passed                                                                          |
| `uv run python scripts/loop_maintain.py`（fix 后）                                | 0    | catalog + matrix 绿                                                                        |
| `uv run pytest -q --ignore=tests/test_loop_engineering_flow.py`                   | 0    | 全库绿（排除 loop 元测）                                                                   |
| `uv run pytest -q`（完整 Tier B）                                                 | 1    | `test_loop_engineering_flow` 在 `--fix` 后 `git checkout` 还原未提交的 `test_catalog.yaml` |

**Tier B 完整绿：** 主会话须 **commit** `tests/test_catalog.yaml` + `docs/generated/*` 后再跑 `uv run pytest -q`（loop 元测设计为不留下 hook 脏文件）。

---

## 门控

| 门控                       | 结果     |
| -------------------------- | -------- |
| `validate-plan-freeze`     | **PASS** |
| `validate-execute-handoff` | **PASS** |

---

## 剩余 OPEN / DEFERRED

| ID         | 状态     | 说明                                    |
| ---------- | -------- | --------------------------------------- |
| **A5-B04** | **OPEN** | 实现未 commit — **主会话 merge 前提交** |
| A1-02      | DEFERRED | Batch6 委托 `DataQualityValidator`      |
| A1-03      | DEFERRED | metadata 字段扩展                       |
| A1-05      | DEFERRED | GitNexus 索引刷新                       |
| A1-07      | DEFERRED | `INVALID_OHLC` ↔ 契约 rule_id 映射      |
| A5-NB01    | DEFERRED | GREEN 证据补完整 session                |

---

## 对抗性审计建议

**可派发** — 业务阻断已闭合；建议主会话 **先 commit allowed 文件 + catalog/generated**，再跑完整 `uv run pytest -q` 与第二轮 A1/A5 对抗复验。
