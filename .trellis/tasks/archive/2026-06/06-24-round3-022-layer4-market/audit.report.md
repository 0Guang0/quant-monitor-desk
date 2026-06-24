# Audit Report — round3-022-layer4-market（Repair 闭环）

> **Phase 7 + Repair：** Trellis Audit · model: composer-2.5  
> **分支：** `feature/round3-022-layer4-market` @ `quant-monitor-desk-wt-022-layer4`  
> **日期：** 2026-06-24

---

## 总判定

| 项                    | 值                    |
| --------------------- | --------------------- |
| **判定**              | **PASS_AFTER_REPAIR** |
| **BLOCKING OPEN**     | **0**                 |
| **NON-BLOCKING OPEN** | **0**                 |
| **书面 DEFER**        | **4**                 |
| **A6**                | SKIP                  |

**对抗性审计：** 可进入二次对抗审计 — 原 A1–A8 登记缺口已 CLOSED 或书面 DEFER（含 owner/phase/closure_test）；`validate-plan-freeze` / `validate-execute-handoff` 均 exit 0。

---

## Repair 修复清单

| #   | 来源     | 修复                                                                                                           |
| --- | -------- | -------------------------------------------------------------------------------------------------------------- |
| 1   | A5 E8    | `implement.jsonl` 补 §6 四 wiring：`market_structure.py`、`lineage.py`、`models.py`、`manifest.yaml`           |
| 2   | A8/A4/A3 | 新增 7 测：非交易日、calendar 未来 as_of、缺 manifest、缺 calendar、breadth 缺字段、负 volume、bundle_dir 越界 |
| 3   | A1 P2/P3 | `_load_breadth_row` 非负校验；`_load_calendar_rows` 强制 `source`/`quality_flag`                               |
| 4   | A2       | 测试 `_mutate_*` 合并为 `_mutate_bundle_file`（purpose 不变）                                                  |
| 5   | loop     | `loop_maintain.py --fix` 刷新 `test_catalog.yaml` + `project_map.generated.json`                               |

---

## BLOCKING 列表

（无）

---

## DEFER 列表（书面）

| ID       | 描述                                       | owner                    | phase                  | closure_test                                         |
| -------- | ------------------------------------------ | ------------------------ | ---------------------- | ---------------------------------------------------- |
| A1-P1    | `session_type` 非交易日例外                | Wave D / Batch 6         | multi-session calendar | `test_marketSnapshot_sessionTypeAllowsNonTradingDay` |
| EXT-5    | L3/L4 `staged_bundle` 重复（超 022 scope） | Wave C merge coordinator | Batch 6+               | `core/staged_bundle.py` + L3/L4 迁移测               |
| A4-NB-2  | 畸形数值 `ValueError` 泄漏                 | 022 follow-up            | error model slice      | `test_marketBreadth_rejectsNonNumericAdvancers`      |
| OOB-A3-4 | symlink 路径天花板（对齐 L3）              | security hardening       | untrusted bundle_dir   | `test_stagedBundle_rejectsSymlinkEscape`             |

---

## pytest 复跑（Repair 后）

| 命令                                                                                 | exit | 摘要                |
| ------------------------------------------------------------------------------------ | ---- | ------------------- |
| `uv run pytest tests/test_layer4_market_structure.py -q`                             | 0    | **14 passed**       |
| `uv run pytest tests/test_batch3_staged_downstream_gate.py -q`                       | 0    | 2 passed（A8 基线） |
| `uv run pytest -q`                                                                   | 0    | 全库绿              |
| `uv run ruff check backend/app/layer4_markets tests/test_layer4_market_structure.py` | 0    | All checks passed   |

---

## 门控

| 门控                       | 结果                  |
| -------------------------- | --------------------- |
| `validate-plan-freeze`     | **PASS**（E8 已闭合） |
| `validate-execute-handoff` | **PASS**              |
| `loop_maintain.py --fix`   | **PASS**              |

---

## 维度摘要

| 维  | 判定 | 证据                                           |
| --- | ---- | ---------------------------------------------- |
| A1  | PASS | `research/audit-evidence/a1.md` + Repair P2/P3 |
| A2  | PASS | mutate 合并；EXT-5 defer                       |
| A3  | PASS | bundle_dir 测闭合                              |
| A4  | PASS | 测试缺口闭合；NB-2 defer                       |
| A5  | PASS | plan-freeze 闭合                               |
| A6  | SKIP | 无 hot path                                    |
| A7  | PASS | 零 DB 写                                       |
| A8  | PASS | 14 测五字段齐全                                |

---

## GitNexus

Repair 前 `impact(MarketStructureBuilder)` 符号未入索引（greenfield，LOW/UNKNOWN）。变更仅触及 `layer4_markets` + pytest；无生产调用链。

---

**可进入对抗性二次审计 / 主会话 merge gate（用户侧 commit）。**

**FINAL: PASS_AFTER_REPAIR**
