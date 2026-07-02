# Audit A2 — Ponytail（wave4-r3-dcp-08-layer4）

> **维：** A2 ponytail-review  
> **协议：** plan_protocol_version 4.1  
> **模板：** `agents/audit-a2-ponytail.md`  
> **日期：** 2026-07-02  
> **工作目录：** `quant-monitor-desk-wt-dcp08` · 分支 `feature/wave4-r3-dcp-08-layer4`  
> **diff 基线：** `git diff HEAD`（含未提交变更）+ untracked 新文件

---

## 维度证据 §3.2

### Boot / diff 记录

| 项                               | 证据                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `git diff --stat HEAD`（已跟踪） | 7 files · +488 / −488（`test_catalog.yaml` 重排净增≈0）                                                                                                                                                                                                                                                                                                                                                                                                     |
| 已跟踪触及                       | `market_structure.py` (+137) · `data_commands.py` (+3 行核心 hack + dry-run 分支) · `test_qmd_data_sync_tier_a_router.py` (+16) · ops/ADR 文档                                                                                                                                                                                                                                                                                                              |
| 未跟踪新文件                     | `clean_read.py` (~152 LOC) · `layer4_clean_e2e_support.py` (~97) · `test_layer4_clean_read.py` (~90) · `test_layer4_us_equity_clean_e2e.py` (~39) · ADR-033 · 活卡                                                                                                                                                                                                                                                                                          |
| INDEX §1 切片                    | S08-BOOT..S08-CLOSE 全 [x]；触及 `to-issues-slices.md` 所列全部生产/测路径                                                                                                                                                                                                                                                                                                                                                                                  |
| DOUBT 搜索范围                   | `backend/app/layer4_markets/clean_read.py` · `market_structure.py`（`build`/`_build_tier_a_clean`）· `data_commands.py`（`sync_mootdx_incremental`）· `tests/layer4_clean_e2e_support.py` · `tests/test_layer4_clean_read.py` · `tests/test_layer4_us_equity_clean_e2e.py` · `tests/test_qmd_data_sync_tier_a_router.py` · 对照 `tests/layer1_clean_e2e_support.py` · `StagedFixtureMarketAdapter` · `layer2_sensors/observation.reject_future_observation` |

### ponytail 注释核对

| 锚点                       | 状态                                                                                                                          |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `data_commands.py:540-542` | `validation_only` runtime 提升 + registry reconcile 升级路径 — **计划内 interim**（ADR-033 / `registry_proposed_delta.yaml`） |
| `data_commands.py:553-555` | dry-run `selected_source_id=mootdx` 覆盖 — ACC-MOOTDX 显式 AC，非未请求抽象                                                   |
| `market_structure.py:340`  | `collect_result_field_names` 已有 `ponytail:` — 本票未改                                                                      |
| `clean_read.py`            | 无 `ponytail:` 标注；重复 SQL 见 finding                                                                                      |

### 候选删改（file:line · ponytail 梯级）

| 候选删改                                                                                     | ponytail 梯级                           | 备注                                                              |
| -------------------------------------------------------------------------------------------- | --------------------------------------- | ----------------------------------------------------------------- |
| `clean_read.py:33-47` 与 `107-122` 同形 `security_bar_1d` JOIN 查询                          | 梯级 2（单次 fetch 复用）               | ~20+ LOC 可合并；见 A2-P2-001                                     |
| `market_structure.py:223-262` 与 `291-336` 平行 finalize（calendar 校验 → lineage → result） | 梯级 2（抽取 `_finalize_market_build`） | ~35 LOC 重复；见 A2-P2-002                                        |
| `USEquityCleanMarketAdapter`（`clean_read.py:136-151`）                                      | —（计划内 AC）                          | `to-issues-slices.md` S08-ADAPTER 显式要求                        |
| `layer4_clean_e2e_support.py` 全文                                                           | —（计划内 AC）                          | S08-BOOT；镜像 DCP-06 `layer1_clean_e2e_support` 模式             |
| `data_commands.py:543` `object.__setattr__(validation_only)`                                 | 梯级 5（有意简化）                      | registry delta 未 merge 前必需；已有 `ponytail:` — **不算 bloat** |
| `test_layer4_clean_read.py` aggregate + adapter 双测同 fixture                               | 梯级 2                                  | 各 ~15 LOC 重叠，未达 ≥20 行阈值 — **不计 finding**               |
| `seed_us_equity_bar` 合成 OHLC（`layer4_clean_e2e_support.py:63-67`）                        | 梯级 6                                  | breadth 仅用 close/pre_close；<20 行 — **不计 finding**           |

### A4 交叉引用

- `clean_read.py:64-65` 非负 breadth 校验与 `Layer4MarketError` fail-closed — A4 错误模型维；非重复日志样板，A2 不重复开项。
- `data_commands.py:581-587` live path `selected_source_id` fail-closed — A4 语义；计划内 ACC-MOOTDX，非 ponytail 重复处理。

### Checklist

- [x] `git diff --stat` 已记录 Lxx / net lines
- [x] 每候选附 `file:line` + ponytail 梯级
- [x] 与 A4 过度抽象交叉引用（无重叠 finding）
- [x] 阻塞 vs 建议已区分（均为 P2 建议修复，无 P0/P1 阻塞项）
- [x] staged 022 路径未删改默认 `staged_fixture_only` 分支

---

## §维度裁决

**FAIL**

（§计划内 2 条非占位 finding）

---

## 计划内问题

| ID        | P   | 标题                                                          | 锚点                                                                 | 根因                                                                                                                                                                                                              | 修复方案                                                                                                                                                                         | 验证                                                                                                                                                                                                                                                               |
| --------- | --- | ------------------------------------------------------------- | -------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| A2-P2-001 | P2  | clean read 对同一 trade_date 双次扫描 `security_bar_1d`       | `backend/app/layer4_markets/clean_read.py:33-47` · `107-122`         | `aggregate_breadth_from_bars` 与 `collect_clean_lineage_provenance` 各跑一遍同形 JOIN/WHERE；`_build_tier_a_clean` 依次调用 adapter.load_breadth + collect_clean_lineage_provenance，同连接双 round-trip          | 抽取 `_fetch_clean_bar_rows(con, *, market_id, trade_date) -> list[tuple]`（或返回命名元组）；breadth 聚合与 lineage hash 共用同一结果集；fail-closed 空集只检一次               | `uv run pytest tests/test_layer4_clean_read.py tests/test_layer4_us_equity_clean_e2e.py -q`；`rg "FROM security_bar_1d b" backend/app/layer4_markets/clean_read.py` 仅 1 处                                                                                        |
| A2-P2-002 | P2  | `MarketStructureBuilder` staged/clean 双路径重复 lineage 组装 | `backend/app/layer4_markets/market_structure.py:223-262` · `291-336` | `build` staged 分支与 `_build_tier_a_clean` 各复制 `_calendar_for_day` → `_reject_future_observation`×2 → window → `parameter_hash_for` → `_lineage_builder.build` → `MarketStructureBuildResult`（~35 LOC 平行） | 新增私有 `_finalize_market_build(..., *, rule_version, code_version, source_dataset_ids, fetch_ids, content_hashes)`；两路径仅保留 adapter 读取与 provenance 差异，共享 finalize | `uv run pytest tests/test_layer4_market_structure.py tests/test_layer4_us_equity_clean_e2e.py -q`；`rg "_reject_future_observation" backend/app/layer4_markets/market_structure.py` 在 `build`/`_build_tier_a_clean` 内各 0 次（仅 `_finalize_market_build` 调用） |

---

## 计划外发现

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| —   | —   | 无   | —    | —    | —        | —    |

已对抗搜索：`backend/app/layer4_markets/` 全目录 · `backend/app/cli/data_commands.py`（mootdx 段）· `tests/layer4_*` · `tests/test_qmd_data_sync_tier_a_router.py` · 对照 Layer1 `layer1_clean_e2e_support.py` 与 `StagedFixtureMarketAdapter`。除 §计划内双重复块外，未发现净增 ≥20 行且可删的未请求 class 包装、单消费者 factory，或计划外重复错误处理/日志样板。`validation_only` runtime hack 与 registry delta 为 ENTRY/ADR-033 显式 interim，已标 `ponytail:`。

---

## Verification Story

- **Tests reviewed:** yes — S08-READ/ADAPTER/E2E 五字段 docstring 与切片 AC 对齐；e2e 断言 `staged_fixture` 不在 source
- **Build verified:** 未在本维独立复跑（A5 职责）；A2 仅审 diff 结构与 ponytail 梯级
- **Security checked:** yes（A2 范围）— 无 `参考项目/**` runtime import；clean 路径只读 DuckDB

### What's Done Well

- **切片对齐**：`clean_read.py` 用模块级函数 + 薄 adapter，未引入多余 factory/registry 层；`USEquityCleanMarketAdapter` 为 to-issues 显式 AC。
- **测试 bootstrap 复用模式**：`layer4_clean_e2e_support.py` 集中 migrate/seed，与 DCP-06 Layer1 先例一致。
- **staged 桥保留**：`source_mode=staged_fixture_only` 默认路径与 022 manifest 硬闸未动；`tier_a_clean` 为并行入口。
- **registry interim 可审计**：`data_commands.py` `validation_only` hack 与 dry-run `selected_source_id` 覆盖均有 `ponytail:` / ADR-033 升级路径。
