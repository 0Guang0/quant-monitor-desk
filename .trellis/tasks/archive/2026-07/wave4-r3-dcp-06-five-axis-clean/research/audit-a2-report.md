# Audit A2 — Ponytail（wave4-r3-dcp-06-five-axis-clean）

> **维：** A2 ponytail-review  
> **协议：** plan_protocol_version 4.1  
> **模板：** `agents/audit-a2-ponytail.md`  
> **日期：** 2026-07-02  
> **diff 基线：** `git diff master..HEAD`

---

## 维度证据 §3.2

### Boot / diff 记录

| 项                             | 证据                                                                                                                                                                                                                                                                         |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `git diff --stat`（全量）      | 72 files · +3113 / −110                                                                                                                                                                                                                                                      |
| `git diff --stat`（代码+契约） | 17 files · +1381 / −66（`backend/` · `tests/` · `specs/model_inputs/` · ADR-029 · 活卡/台账）                                                                                                                                                                                |
| S00 触及                       | `backend/app/layer1_axes/clean_observation_reader.py` (+256) · `tests/layer1_clean_e2e_support.py` (+76) · `tests/test_layer1_clean_reader.py` (+131)                                                                                                                        |
| S01–S05 触及                   | 五轴 e2e 测各 +52–83 LOC；`test_layer1_five_axis_panel_clean_smoke.py` (+228)                                                                                                                                                                                                |
| S06/S07 触及                   | `layer1_source_whitelist.yaml` (+63) · `test_model_input_whitelist.py` (+39) · 台账/matrix 文档                                                                                                                                                                              |
| **staged 桥**                  | `git diff master..HEAD -- backend/app/layer1_axes/ingestion.py` **空** — Batch 2.5 默认 staged 路径未改                                                                                                                                                                      |
| DOUBT 搜索范围                 | `clean_observation_reader.py` · `layer1_clean_e2e_support.py` · `test_layer1_*_clean_e2e.py` · `test_layer1_five_axis_panel_clean_smoke.py` · `test_layer1_clean_reader.py` · `test_model_input_whitelist.py` · 对照 `ingestion.py` / `macro_incremental_common.py` 共享模式 |

### ponytail 注释核对

| 锚点                                                   | 状态                                                        |
| ------------------------------------------------------ | ----------------------------------------------------------- |
| `clean_observation_reader.py:3-5`                      | macro `indicator_id` 映射天花板 + Batch 6 升级路径          |
| `clean_observation_reader.py:30`                       | `P0_ROW_CAPS`/`P0_WINDOW_CAPS` 镜像 K1 YAML；升级 load YAML |
| `clean_observation_reader.py:217`                      | Amihud 流动性 ponytail（ADR-029 alpha_vantage bar）         |
| `ADR-029:22`                                           | tiingo primary 阶段外置                                     |
| `layer1_source_whitelist.yaml` L1-LIQ-AMIHUD-SPY notes | tiingo reconcile 绑定 Batch 6+                              |

### 候选删改（file:line · ponytail 梯级）

| 候选删改                                                                                                             | ponytail 梯级                             | 备注                                                             |
| -------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- | ---------------------------------------------------------------- |
| `test_layer1_sentiment_clean_e2e.py:18-40` + `test_layer1_five_axis_panel_clean_smoke.py:45-60` 重复 COT weekly seed | 梯级 2（复用 `layer1_clean_e2e_support`） | ~39 LOC 同形；见 A2-P2-001                                       |
| `clean_observation_reader.py:30-45` `P0_ROW_CAPS`/`P0_WINDOW_CAPS`                                                   | 梯级 5（有意简化）                        | S07 A4 cap 证明所需；已有 `ponytail:` — **不算 bloat**           |
| `clean_observation_reader.py` 全文 (+256)                                                                            | —（计划内 AC）                            | 模块函数非 class 包装；fail-closed + macro/bar/Amihud 单文件收敛 |
| 五轴 per-axis e2e（S01–S05 各 ~52–83 LOC）                                                                           | —（切片设计）                             | `to-issues-slices.md` 并行 tracer-bullet；非可删重复             |
| `ingestion.py`                                                                                                       | —（PASS）                                 | diff 空；clean reader 并行路径，未替换 staged 默认               |
| `_row_to_observation` 单调用点                                                                                       | 梯级 2                                    | ~27 LOC；内联不省 ≥20 行 — **不计 finding**                      |

### A4 交叉引用

- `P0_ROW_CAPS`/`P0_WINDOW_CAPS` 与 K1 YAML 数值镜像 — S07 Repair #6/#7 与 A4 协同引入；ponytail 已标注漂移风险与升级路径，A2 不重复开项。

### Checklist

- [x] `git diff --stat` 已记录
- [x] 每候选附 `file:line` + ponytail 梯级
- [x] A4 交叉引用（caps 镜像已核对）
- [x] staged 桥未破坏
- [x] ponytail 简化处均有注释（流动性 / macro 映射 / caps）

---

## §维度裁决

**FAIL**

（§计划内 1 条非占位 finding）

---

## 计划内问题

| ID        | P   | 标题                                | 锚点                                                                                                                                                   | 根因                                                                                                                                                                 | 修复方案                                                                                                                                                                                    | 验证                                                                                                                                                      |
| --------- | --- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A2-P2-001 | P2  | COT weekly seed 重复未进共享 helper | `tests/test_layer1_sentiment_clean_e2e.py:18-40` · `tests/test_layer1_five_axis_panel_clean_smoke.py:45-60` · 对照 `tests/layer1_clean_e2e_support.py` | S00 已建 `layer1_clean_e2e_support`（`seed_macro_series`/`seed_spy_bars`）；S05/S06 各拷一份 ~23/16 行 COT 周频 seed，违反切片「共享 helper」与 ponytail 梯级 2 复用 | 在 `layer1_clean_e2e_support.py` 增加 `seed_cot_lf_net_weekly(con, *, n, start, ...)`（含 `frequency=weekly`/`source_used=cftc_cot` UPDATE）；S05/S06 删除本地 `_seed_*` 并 import 共享函数 | `uv run pytest tests/test_layer1_sentiment_clean_e2e.py tests/test_layer1_five_axis_panel_clean_smoke.py -q`；`rg "_seed_cot" tests/` 仅命中 support 模块 |

---

## 计划外发现

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| —   | —   | 无   | —    | —    | —        | —    |

已对抗搜索：`backend/app/layer1_axes/clean_observation_reader.py` 全文 · `tests/layer1_*` · `tests/test_model_input_whitelist.py` · `specs/model_inputs/layer1_source_whitelist.yaml` · 对照 `ingestion.py`（零 diff）· DCP-05 `macro_incremental_common` 共享模式。除 §计划内 COT seed 外，未发现净增 ≥20 行且可删的生产抽象、单消费者 wrapper，或计划外重复错误处理样板。

---

## Verification Story

- **Tests reviewed:** yes — S00–S06 测模块、五字段 docstring、fail-closed/cap/liquidity ponytail 断言与切片 AC 对齐
- **Build verified:** yes — `uv run pytest tests/test_layer1_clean_reader.py tests/test_layer1_five_axis_panel_clean_smoke.py -q` exit 0
- **Security checked:** yes（A2 范围）— 无 `参考项目/**` runtime import；`FORBIDDEN_FALLBACK_SOURCE_PREFIXES` 拒绝 staged 行；ingestion 桥未扩 attack surface

### What's Done Well

- **并行 clean 读路径**：`clean_observation_reader.py` 用模块级函数而非 `Layer1CleanObservationReader` class 包装，符合 ponytail YAGNI；`ingestion.py` 零 touch，staged 桥保留。
- **流动性 ponytail 可审计**：ADR-029 + 代码/whitelist `ponytail:` + Amihud 从 `alpha_vantage` bar 推导，tiingo 升级路径文档化。
- **共享 bootstrap**：`layer1_clean_e2e_support.py` 集中 DB migrate + macro/bar seed，五轴 e2e 复用 `AS_OF`/`bootstrap_layer1_clean_db`。
