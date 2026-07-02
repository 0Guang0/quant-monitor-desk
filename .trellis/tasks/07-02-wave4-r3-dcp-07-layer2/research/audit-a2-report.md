# Audit A2 — Ponytail（07-02-wave4-r3-dcp-07-layer2）

> **维：** A2 ponytail-review  
> **协议：** plan_protocol_version 4.1  
> **模板：** `agents/audit-a2-ponytail.md`  
> **日期：** 2026-07-02  
> **diff 基线：** `git diff HEAD`（工作区未提交）+ 未跟踪 DCP-07 新文件  
> **工作目录：** `quant-monitor-desk-wt-dcp07`

---

## 维度证据 §3.2

### Boot / diff 记录

| 项                                      | 证据                                                                                                                                                                                                      |
| --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `git diff HEAD --stat`（layer2 已跟踪） | 4 files · +59 / −10：`__init__.py` · `observation.py` · `sensor_loader.py` · `snapshot_builder.py`                                                                                                        |
| 未跟踪新文件（DCP-07 核心）             | `clean_observation_reader.py` (~179 LOC) · `test_layer2_clean_reader.py` (~131) · `test_layer2_vix_clean_e2e.py` (~156) · `layer2_cross_asset_registry_clean_replay.yaml` (~20) · `ADR-032`               |
| S00 触及                                | `backend/app/layer2_sensors/clean_observation_reader.py` · `sensor_loader.py`（`production_clean_replay`）· `tests/test_layer2_clean_reader.py`                                                           |
| S01 触及                                | `tests/test_layer2_vix_clean_e2e.py` · `observation.py`（`assert_observation_source`）· `snapshot_builder.py`（调用切换）                                                                                 |
| **staged 桥**                           | `git diff HEAD -- tests/test_layer2_sensor_loader.py` **空** — 既有 staged 测未改；`STAGED_REGISTRY_FIXTURE` 路径保留                                                                                     |
| AUDIT.plan A2 要点                      | ponytail 单传感器（L2-VIX）；staged 路径保留                                                                                                                                                              |
| DOUBT 搜索范围                          | `backend/app/layer2_sensors/**` · `tests/test_layer2_*.py` · 对照 `layer1_axes/clean_observation_reader.py` · `tests/layer1_clean_e2e_support.py` · `tests/test_layer2_sensor_loader.py` 共享 helper 模式 |

### ponytail 注释核对

| 锚点                                  | 状态                                                           |
| ------------------------------------- | -------------------------------------------------------------- |
| `clean_observation_reader.py:3-4`     | macro VIXCLS → OHLC 折叠天花板 + ETF/futures 升级路径          |
| `clean_observation_reader.py:163-165` | replay `fetch_time` clamp 天花板                               |
| `plan-spec.md` ASSUMPTIONS            | replay 默认；非 live primary                                   |
| `reference-adoption-dcp07.md`         | EasyXT fallback **forbidden**；L1 reader **模式参考勿 import** |

### 候选删改（file:line · ponytail 梯级）

| 候选删改                                                                                              | ponytail 梯级                                                        | 备注                                                                                        |
| ----------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `test_layer2_vix_clean_e2e.py:24-66` 重复 `_layer2_cm` + `_insert_validation_report`                  | 梯级 2（复用 `test_layer2_sensor_loader` 或抽 `layer2_e2e_support`） | ~41 LOC 同形；见 A2-P2-001                                                                  |
| `clean_observation_reader.py` 全文 (~179)                                                             | —（计划内 AC）                                                       | ADR-032 / S00 新建 reader；`CrossAssetObservation` 映射为域必需                             |
| `clean_observation_reader.py:13-23` 与 `layer1_axes/clean_observation_reader.py:16-48` 并行 guard/cap | 梯级 5（有意简化）                                                   | ENTRY §6 明确 L1 **勿 import**；跨层抽 shared module 为可选升级，非本票必删                 |
| `Layer2CleanObservationReader` 单方法 class                                                           | —（ADR 命名）                                                        | ADR-032 指定类名；与 L1 模块函数风格略异但非 wrapper 堆叠                                   |
| `sensor_loader.py` `production_clean_replay` (+37)                                                    | —（计划内 AC）                                                       | `to-issues` S00 registry mode + P0 fred 白名单                                              |
| `observation.py` `assert_observation_source` (+18)                                                    | —（计划内）                                                          | clean vs staged 绑定；不足 20 行且为 snapshot 路径必需                                      |
| `P0_CLEAN_REPLAY_ASSET_IDS` 双定义                                                                    | 梯级 2                                                               | `sensor_loader.py:27` 与 `clean_observation_reader.py:15` 各 1 行常量 — **未达 ≥20 行阈值** |

### A4 交叉引用

- `assert_observation_source`（`observation.py:85-100`）与 reader 内 `_assert_clean_source_used`（`clean_observation_reader.py:51-59`）分工不同：前者在 snapshot 构建路径校验 registry↔observation；后者在 clean 读路径拒绝 staged 行。非 A4 重复错误处理样板。
- `FORBIDDEN_FALLBACK_SOURCE_PREFIXES` 与 L1 镜像 — 与 DCP-06 A2 caps 镜像同理：有意简化 + ENTRY 禁止跨层 import reader。

### Checklist

- [x] `git diff --stat` 已记录（已跟踪 + 未跟踪分项）
- [x] 每候选附 `file:line` + ponytail 梯级
- [x] A4 交叉引用（snapshot vs reader guard 已核对）
- [x] staged 桥未破坏（`test_layer2_sensor_loader.py` 零 diff）
- [x] ponytail 简化处均有注释（OHLC 折叠 · fetch_time clamp）

---

## §维度裁决

**FAIL**

（§计划内 1 条非占位 finding）

---

## 计划内问题

| ID        | P   | 标题                              | 锚点                                                                                                      | 根因                                                                                                                                                                                                           | 修复方案                                                                                                                                                                                                                                                       | 验证                                                                                                           |
| --------- | --- | --------------------------------- | --------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| A2-P2-001 | P2  | Layer2 e2e 重复 WM/VR 测试 helper | `tests/test_layer2_vix_clean_e2e.py:24-66` · 对照 `tests/test_layer2_sensor_loader.py:73-78` · `:112-148` | S01 新建 e2e 时拷贝 `_layer2_cm`（6 行）与 `_insert_validation_report`（~35 行），而 `test_layer2_sensor_loader.py` 已有同形 helper；违反 `to-issues`「共享 layer2_sensors 读路径」纪律与 ponytail 梯级 2 复用 | 新建 `tests/layer2_e2e_support.py`（对齐 `layer1_clean_e2e_support.py` 模式）导出 `layer2_cm` + `insert_layer2_validation_report`（`source_id`/`rule_version` 参数化）；`test_layer2_vix_clean_e2e.py` 与 `test_layer2_sensor_loader.py` 删除本地副本并 import | `uv run pytest tests/test_layer2_vix_clean_e2e.py tests/test_layer2_sensor_loader.py -q`；`rg "def \_layer2_cm | def \_insert_validation_report" tests/` 仅命中 support 模块 |

---

## 计划外发现

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| —   | —   | 无   | —    | —    | —        | —    |

已对抗搜索：`backend/app/layer2_sensors/clean_observation_reader.py` 全文 · `sensor_loader.py` diff · `tests/test_layer2_clean_reader.py` · `tests/test_layer2_vix_clean_e2e.py` · 对照 `layer1_axes/clean_observation_reader.py`（跨层并行 guard/SQL 为 ENTRY 禁止 import 下的有意模式复用）· `tests/test_layer2_sensor_loader.py` staged 路径。除 §计划内 WM helper 重复外，未发现净增 ≥20 行且可删的生产侧单消费者 wrapper、未请求 factory，或计划外重复日志/错误处理样板。`test_catalog.yaml` 大 diff 为 loop 机械刷新，不计入 A2 代码 bloat。

---

## Verification Story

- **Tests reviewed:** yes — S00 五字段 docstring、fail-closed/fallback/cap 断言对齐 ADR-032；S01 e2e 证明 `source=fred` 非 `staged_fixture`
- **Build verified:** yes — `uv run pytest tests/test_layer2_clean_reader.py tests/test_layer2_vix_clean_e2e.py -q` exit 0（6 passed）
- **Security checked:** yes（A2 范围）— 无 `参考项目/**` runtime import；`FORBIDDEN_FALLBACK_SOURCE_PREFIXES` + `assert_observation_source` 拒绝 staged 混入 clean replay

### What's Done Well

- **单传感器竖切**：仅 `L2-VIX` P0 白名单；`production_clean_replay` registry 不放开全资产 live。
- **staged 桥保留**：`test_layer2_sensor_loader.py` 未改；`assert_observation_source` 最小扩展 snapshot 路径。
- **clean reader ponytail 可审计**：OHLC 折叠与 fetch_time clamp 均有 `ponytail:` 注释与升级路径。
- **测试 bootstrap 复用 L1**：`test_layer2_clean_reader.py` 正确使用 `layer1_clean_e2e_support.seed_macro_series`，未重复 macro seed 逻辑。
