# R3-DCP-06 参考项目采纳调研（L1/L2/L3）

> **任务：** `.trellis/tasks/wave4-r3-dcp-06-five-axis-clean/`  
> **日期：** 2026-07-02  
> **方式：** 实读 `参考项目/**` 源码 + QMD 仓内 Layer1 承接标注（**不进 L 梯**）  
> **SSOT：** `specs/contracts/reference_adoption_guardrails.yaml`

---

## 0. 铁律

1. **L1/L2/L3 只评 `参考项目/**`**；`backend/app/layer1_axes/\*\*` 记为「仓内承接」。
2. 禁止 runtime import / sys.path / 软链参考树。
3. OpenBB = **architecture_only**（AGPL）— 行为对齐，不拷贝 Fetcher 类。
4. EasyXT `unified_data_interface` = **forbidden**（DuckDB 不全 → 在线回退）。
5. digital-oracle / TradingAgents = **L2 概念或 architecture_only**；情绪/宏观解析模式可借鉴，数据源仍走 QMD Tier A registry。

---

## 1. 三等级总表（仅参考项目）

| 参考路径                                        | 等级                            | 采纳 / 禁止                                  | QMD DCP-06 目标                                                           |
| ----------------------------------------------- | ------------------------------- | -------------------------------------------- | ------------------------------------------------------------------------- |
| `OpenBB/.../fetcher.py` L36–85                  | **architecture_only → L3 对齐** | transform_query → extract → transform 三阶段 | clean 读入前 **不**再 fetch；若扩 live 仍对齐 port 三阶段                 |
| `OpenBB/.../fred_base.py` L31–75                | **L2**                          | `observation_start`/`end` 窗参数             | 已由 DCP-05 fred incremental 实现；Layer1 **只读** `axis_observation`     |
| `digital-oracle/.../fear_greed.py` L42–76       | **L2 概念**                     | JSON 解析 + fail-closed `ProviderParseError` | 情绪轴 **不**接 CNN；COT 走 `cftc_cot` clean；解析纪律借鉴                |
| `digital-oracle/.../treasury.py`                | **L2 概念**                     | 官方宏观序列拉取形状                         | us_treasury 已由 DCP-05 写 clean；本票不新 port                           |
| `EasyXT/.../unified_data_interface.py` L172–244 | **forbidden**                   | DuckDB 无数据 → QMT 在线                     | Layer1 **禁止** silent fallback；clean 不足 → fail-closed + quality_flags |
| `EasyXT/.../unified_data_interface.py` L233–237 | **forbidden**                   | 降级 `_read_from_duckdb` 后再下载            | 负向测：读 clean 失败不得换源                                             |
| `TradingAgents-astock/.../quality_gate.py`      | **architecture_only**           | 多层 quality gate 概念                       | 对齐 QMD `DbValidationGate` + `DataQualityValidator` 已有链，不 import    |

---

## 2. 分参考深读

### 2.1 OpenBB Fetcher（architecture_only · L3 行为对齐）

**读什么：** `transform_query` → `extract_data` → `transform_data` 流水线。

**QMD 决策：** DCP-06 **不新增 fetch**；数据面由 DCP-05 闭合。Layer1 读 clean 等价于 OpenBB 流水线末段 `transform_data` 之后。若 Execute 扩 live ingestion，仍禁止拷贝 `Fetcher` 类。

### 2.2 OpenBB FRED base（L2 · 已承接在 DCP-05）

**读什么：** `get_series(series_id, start_date, end_date)` 窗参数。

**QMD 决策：** fred port + `ops/fred_incremental_*` 已 L2 拷改；Layer1 通过 `axis_observation` 消费，**不重复 L2**。

### 2.3 digital-oracle Fear & Greed（L2 概念 · 不采纳数据源）

**读什么：** HTTP JSON → 强类型 snapshot + parse fail-closed。

**QMD 决策：** 情绪轴 P0 用 **CFTC COT**（Tier A `cftc_cot` → `axis_observation`），不用 CNN fear/greed API。借鉴 **解析失败即抛错**，不 silent NaN。

### 2.4 EasyXT unified_data_interface（forbidden）

**读什么：** DuckDB 空 → `need_download = True` → 在线源。

**QMD 决策：** Layer1 clean 读路径 **禁止**此模式；测：`clean 缺行 → 明确错误/quality_flag`，不触发 DataSourceService 旁路。

---

## 3. 仓内承接（非参考 L 梯）

| 组件                     | 路径                                              | DCP-06 用法                                       |
| ------------------------ | ------------------------------------------------- | ------------------------------------------------- |
| Axis spec loader         | `axis_loader.py`                                  | 五轴 YAML SSOT；不改动 spec 语义                  |
| Feature / interpretation | `feature_engine.py`, `interpretation.py`          | 复用；输入改 clean reader                         |
| Ingestion bridge         | `ingestion.py`, `ingestion_commit.py`             | 保留 staged 桥；新增 **parallel** clean-read 入口 |
| Observation contract     | `observation_contract.py`                         | `axis_observation` DDL 不变                       |
| DCP-05 clean 写          | `clean_write_targets.py`, `ops/*_incremental_*`   | replay 种子数据来源                               |
| K1 whitelist             | `specs/model_inputs/layer1_source_whitelist.yaml` | P0 行 readiness 对齐                              |
| Production live policy   | `docs/quality/production_live_pilot_policy.md`    | 非 fixture smoke 门控                             |

---

## 4. Execute RED 前门禁

实读参考文件并落盘 `research/execute-reference-read-evidence.md`（Execute 阶段），路径与 §1 表一致。

---

## 5. 采纳决策摘要

| 能力               | 参考等级                   | 决策                                   |
| ------------------ | -------------------------- | -------------------------------------- |
| 宏观序列窗参数     | OpenBB fred **L2**         | **已实现于 DCP-05**；Layer1 只读 clean |
| Fetch 三阶段       | OpenBB **L3 对齐**         | 不新 fetch；读 clean = 流水线后端      |
| 情绪 JSON 解析纪律 | digital-oracle **L2 概念** | COT clean 映射；fail-closed            |
| DB 空则换源        | EasyXT **forbidden**       | 负向测 + 代码审查                      |
| 五轴特征/解释      | 仓内 Batch 2               | 复用引擎；新 clean reader              |
