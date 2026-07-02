# R3-DCP-07 参考项目采纳调研（L1/L2/L3）

> **任务：** `.trellis/tasks/07-02-wave4-r3-dcp-07-layer2/`  
> **日期：** 2026-07-02  
> **方式：** 实读 `参考项目/**` 源码 + QMD 仓内 Layer2 承接标注（**不进 L 梯**）  
> **SSOT：** `specs/contracts/reference_adoption_guardrails.yaml`

---

## 0. 铁律

1. **L1/L2/L3 只评 `参考项目/**`**；`backend/app/layer2_sensors/\*\*` 记为「仓内承接」。
2. 禁止 runtime import / sys.path / 软链参考树。
3. OpenBB = **architecture_only**（AGPL）— 行为对齐，不拷贝 Fetcher 类。
4. EasyXT `unified_data_interface` = **forbidden**（DuckDB 空 → 在线回退）。
5. DCP-07 **不新增 fetch**；读 DCP-05 clean = OpenBB 流水线后端。

---

## 1. 三等级总表（仅参考项目）

| 参考路径                                                 | 等级                            | 采纳 / 禁止                            | QMD DCP-07 目标                                            |
| -------------------------------------------------------- | ------------------------------- | -------------------------------------- | ---------------------------------------------------------- |
| `OpenBB/.../fetcher.py` L36–85                           | **architecture_only → L3 对齐** | transform → extract → transform 三阶段 | Layer2 **只读** clean；不新 port fetch                     |
| `OpenBB/.../fred_base.py` L31–75                         | **L2**                          | `observation_start`/`end` 窗参数       | VIXCLS 已由 DCP-05 fred 写 `axis_observation`；Layer2 消费 |
| `OpenBB/.../series.py` L18–26                            | **L2 概念**                     | `symbol` ↔ `series_id` 别名映射        | registry `FRED:VIXCLS` → clean `indicator_id=VIXCLS`       |
| `EasyXT/data_manager/unified_data_interface.py` L172–250 | **forbidden**                   | DuckDB 无数据 → QMT 在线               | Layer2 clean 读 **禁止** silent fallback                   |
| `EasyXT/.../unified_data_interface.py` L233–237          | **forbidden**                   | 降级 `_read_from_duckdb` 后再下载      | 负向：clean 缺行不得换源                                   |
| `TradingAgents-astock/.../quality_gate.py`               | **architecture_only**           | 多层 quality gate 概念                 | 对齐 QMD `DbValidationGate` + VR 已有链                    |

---

## 2. 分参考深读

### 2.1 OpenBB Fetcher（architecture_only · L3 行为对齐）

**读什么：** `Fetcher.fetch_data` 三阶段流水线。

```36:85:参考项目/OpenBB/openbb_platform/core/openbb_core/provider/abstract/fetcher.py
class Fetcher(Generic[Q, R]):
    @classmethod
    async def fetch_data(cls, params, credentials=None, **kwargs):
        query = cls.transform_query(params=params)
        data = await maybe_coroutine(cls.extract_data, ...)
        return cls.transform_data(query=query, data=data, **kwargs)
```

**QMD 决策：** DCP-07 数据面由 DCP-05 闭合。Layer2 读 `axis_observation` 等价于 OpenBB `transform_data` 之后。禁止拷贝 `Fetcher` 类。

### 2.2 OpenBB FRED base（L2 · 已承接在 DCP-05）

```31:75:参考项目/OpenBB/openbb_platform/providers/fred/openbb_fred/utils/fred_base.py
    def get_series(self, series_id, start_date=None, end_date=None, **kwargs):
        url = f"{ROOT_URL}/series/observations?series_id={series_id}"
        if start_date:
            url += "&observation_start=" + start_date.strftime("%Y-%m-%d")
        ...
        return root["observations"]
```

**QMD 决策：** fred port + `ops/fred_incremental_*` 已 L2 拷改；Layer2 通过 `indicator_id=VIXCLS` 消费，**不重复 L2 fetch**。

### 2.3 EasyXT unified_data_interface（forbidden）

```172:250:参考项目/EasyXT/data_manager/unified_data_interface.py
        # 1. 优先从DuckDB读取
        # 2. 如DuckDB无数据或数据不全，使用QMT在线获取
        ...
        if data is None or data.empty:
            need_download = True
```

**QMD 决策：** Layer2 clean 读路径 **禁止**此模式；测：clean 缺行 → fail-closed + quality_flags，不触发 sync 旁路。

---

## 3. 仓内承接（非参考 L 梯）

| 组件              | 路径                                               | DCP-07 用法                               |
| ----------------- | -------------------------------------------------- | ----------------------------------------- |
| Registry loader   | `sensor_loader.py`                                 | 扩 P0 clean replay mode                   |
| Snapshot builder  | `snapshot_builder.py`                              | 复用；输入改 clean reader                 |
| Lineage           | `lineage.py`                                       | `source_fetch_id` / content_hash 契约不变 |
| Staged 测         | `test_layer2_sensor_loader.py`                     | 保留；新增 parallel clean e2e             |
| DCP-05 clean      | `clean_write_targets.py`, `ops/fred_incremental_*` | VIXCLS replay 种子                        |
| DCP-06 先例       | `layer1_axes/clean_observation_reader.py`          | 读 `axis_observation` 模式借鉴（仓内）    |
| Production policy | `docs/quality/production_live_pilot_policy.md`     | replay 默认                               |

---

## 4. Execute RED 前门禁

实读参考文件并落盘 `research/execute-reference-read-evidence-sNN.md`（Execute 阶段），路径与 §1 表一致。

---

## 5. 采纳决策摘要

| 能力               | 参考等级             | 决策                                   |
| ------------------ | -------------------- | -------------------------------------- |
| 宏观序列窗参数     | OpenBB fred **L2**   | **已实现于 DCP-05**；Layer2 只读 clean |
| Fetch 三阶段       | OpenBB **L3 对齐**   | 不新 fetch；读 clean = 流水线后端      |
| DB 空则换源        | EasyXT **forbidden** | 负向测 + 代码审查                      |
| snapshot + lineage | 仓内 Batch 3 019     | 复用 builder；新 clean reader          |
