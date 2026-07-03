# M-DATA-03 参考项目采纳调研（借鉴三等级 · 仅 `参考项目/**`）

> **任务：** `.trellis/tasks/m-data-03-tier-a-live/`  
> **日期：** 2026-07-02（Plan 对抗性审计修订）  
> **方式：** 实读 `参考项目/**` 源码；QMD 仓内代码单独标注 **「仓内直接复用」**  
> **SSOT：** `specs/contracts/reference_adoption_guardrails.yaml` · 活卡 §6

---

## 0. 借鉴三等级定义（Execute 必须遵守）

> **适用范围：** 仅 `参考项目/**` 外部源码。  
> **禁止：** 把 `backend/app/**`、`tests/**` 仓内已有代码标成 L1/L2/L3 — 那些走 **§4 仓内直接复用**。

| 等级                  | 含义                                  | 允许动作                                                                                                                                                | 禁止                                                          |
| --------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| **L1**                | 逻辑契合 QMD 栈，license/语义通过     | 将参考源码 **复制** 到 `backend/app/**` 等 qmd_owned 路径；任务卡记录出处                                                                               | 本票 **无 L1 项**（无整段可原样粘贴的外部实现）               |
| **L2**                | 有借鉴价值但路径/SQL/证据形态不一致   | **可复制片段** 作起点，**必须** 改写为 ConnectionManager、registry、product_live_gate、structured evidence；**禁止** 把参考文件当模块 import 或直接运行 | 禁止未改造即合并；禁止 `sys.path` / runtime import 参考树     |
| **L3**                | 无合适拷贝体，或 license/语义禁止拷贝 | **只借鉴** 概念、管线阶段、目录分工；在仓内 **绿场实现**                                                                                                | 禁止粘贴参考源码；禁止拷贝 OpenBB Provider/Fetcher 类（AGPL） |
| **forbidden**         | 红线语义                              | 仅作负向测与审查                                                                                                                                        | 任何 runtime 采纳                                             |
| **architecture_only** | OpenBB 特判（= L3 + AGPL）            | 三阶段管线、credentials 门等 **概念**                                                                                                                   | runtime 拷贝                                                  |

**本票总结：** 参考侧 **0×L1 · 1×L2（bis 窗参数模式）· 多项 L3 · 多项 forbidden**；实现主体 = **仓内 DCP-05 直接复用 + live 接通**。

---

## 1. 三等级总表（仅 `参考项目/**`）

| 参考路径                                         | 等级                       | 采纳 / 禁止                                 | QMD 目标（改造后）                                                                                                              |
| ------------------------------------------------ | -------------------------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `OpenBB/.../fetcher.py` L36–85                   | **L3**                     | 三阶段管线概念：query → extract → transform | 仓内 `FetchRequest` + port live；**禁止**拷贝 Fetcher/async 基类                                                                |
| `OpenBB/.../providers/fred/` 目录/README         | **architecture_only (L3)** | Provider 注册 + credentials 门概念          | 已有 `fred_port.py`；live 用 `FRED_API_KEY`                                                                                     |
| `digital-oracle/.../bis.py` L54–66               | **L2**                     | HTTP `startPeriod` 窗参数 **模式**          | 拷 **思路** 到 `bis_incremental_*`：watermark → `start_year`/`startPeriod`；**禁止** import `BisProvider` 或粘贴 CSV 解析未改写 |
| `digital-oracle/.../base.py` L22–32              | **L3**                     | Provider 元数据字段形态                     | 对齐既有 `source_registry.yaml`；**禁止**新建 `SignalProvider` 平行体系                                                         |
| `digital-oracle/.../concurrent.py` gather        | **L3**                     | 并发边界概念                                | 本票 **禁止** 11 源并行 live 写同一隔离库                                                                                       |
| `EasyXT/.../auto_data_updater.py` L114–147       | **L3**                     | 「交易日/今日是否更新」**概念**             | 仅 ops 文档；**禁止** schedule 线程进 sync                                                                                      |
| `EasyXT/.../auto_data_updater.py` L149–178       | **L3**                     | 日期窗增量 **概念**                         | watermark → `date_start`/`date_end`；**禁止**拷贝 `DataManager` 调用链                                                          |
| `EasyXT/.../auto_data_updater.py` L31–32, L87–97 | **forbidden**              | sys.path + DataManager 绕过门面             | sync 路径负向审查                                                                                                               |
| `EasyXT/.../unified_data_interface.py` L172–244  | **forbidden**              | DuckDB 不全 → 在线 silent 回退              | 负向测：`test_*` 或 harness 断言无换源                                                                                          |
| `JQ2PTrade/.../data_loader.py`                   | **L3**                     | rehearsal loader **形状**概念               | 本票不用（DCP-09 backfill 已覆盖）                                                                                              |
| `agents-for-openbb` / `TradingAgents*`           | **forbidden**              | Round4 only                                 | 无采纳                                                                                                                          |

---

## 2. 分参考深读

### 2.1 OpenBB Fetcher（L3 · architecture_only）

```36:85:参考项目/OpenBB/openbb_platform/core/openbb_core/provider/abstract/fetcher.py
class Fetcher(Generic[Q, R]):
    require_credentials = True
    ...
    async def fetch_data(cls, params, credentials=None, **kwargs):
        query = cls.transform_query(params=params)
        data = await maybe_coroutine(cls.extract_data, ...)
        return cls.transform_data(query=query, data=data, **kwargs)
```

**L3 对齐（仓内实现，非拷贝）：**

| OpenBB 阶段       | QMD 仓内等价                                       |
| ----------------- | -------------------------------------------------- |
| `transform_query` | watermark → `FetchRequest.start_time` / `end_time` |
| `extract_data`    | `*_port.py` live HTTP/SDK（`use_mock=False`）      |
| `transform_data`  | normalizer + evidence → staging → clean            |

**按源 Execute（均为仓内改 port/ops，参考仅 L3）：**

| 源                     | 参考锚点                       | 等级 | Execute                                                |
| ---------------------- | ------------------------------ | ---- | ------------------------------------------------------ |
| fred                   | OpenBB fred 目录形态           | L3   | 扩展仓内 `fred_port` live；**SDD：** FRED API 官方文档 |
| alpha_vantage          | credentials 门概念             | L3   | `ALPHA_VANTAGE_API_KEY`；**SDD：** AV 官方 API         |
| deribit                | 无外部拷贝体                   | L3   | 仓内 `deribit_port` REST live                          |
| sec_edgar              | 无                             | L3   | 仓内 port + rate limit；**SDD：** SEC EDGAR 官方       |
| baostock/cninfo/mootdx | 无（EasyXT 仅 forbidden 反例） | L3   | 仓内 CN port live                                      |

### 2.2 digital-oracle BIS（唯一 L2）

**L2 改造清单（禁止直接使用参考模块）：**

1. 读 `read_observation_date_watermark`（仓内 `sync/watermark.py`）
2. 推导 `start_year` / API `startPeriod`（**借鉴** bis.py L54–66 参数形态，**不** import `BisProvider`）
3. HTTP 经仓内 fetch port + ResourceGuard
4. 写入 `official_macro_evidence_v1` + `axis_observation`（ADR-028）

**L2 同族（均为「窗参数 L2 思路 + 仓内 port 实现」，非粘贴 digital-oracle 代码）：** `world_bank` · `us_treasury` · `cftc_cot`

### 2.3 EasyXT（L3 概念 + forbidden）

- **L3 概念：** 增量只拉窗内数据；交易日感知文档化（完整日历 → 后续 G4，本票 ponytail calendar day watermark）
- **forbidden：** `unified_data_interface` 式 silent fallback — 须 `ProductLiveGateError` fail-closed，禁止换源

---

## 3. 十一源 × 借鉴等级 × 仓内触点

| source_id     | 参考项目（仅外部）           | 借鉴等级                 | 仓内直接复用（非 L 梯）                             | Execute 要点                    |
| ------------- | ---------------------------- | ------------------------ | --------------------------------------------------- | ------------------------------- |
| fred          | OpenBB fred 形态             | L3                       | `fred_port` · `fred_incremental_run` · orchestrator | `use_mock=False` + SDD 官方 API |
| us_treasury   | 宏观 HTTP 窗概念             | L3（窗思路可对照 L2 表） | `us_treasury_incremental_*`                         | live + watermark                |
| sec_edgar     | —                            | L3                       | `sec_edgar_port` · ops                              | SDD: sec.gov EDGAR              |
| cftc_cot      | —                            | L3                       | `cftc_incremental_*`                                | 周频 watermark                  |
| bis           | digital-oracle bis.py        | **L2**                   | `bis_incremental_*`                                 | L2 改造清单 §2.2                |
| world_bank    | 类 API 窗概念                | L3                       | `world_bank_incremental_*`                          | indicator + date window         |
| alpha_vantage | credentials 概念             | L3                       | `alpha_vantage_port`                                | key + bar cap                   |
| deribit       | —                            | L3                       | `deribit_port`                                      | REST live                       |
| baostock      | EasyXT **仅 forbidden 反例** | L3                       | `baostock_port` · DCP-01 先例                       | session live                    |
| cninfo        | —                            | L3                       | `cninfo_port`                                       | disclosure live                 |
| mootdx        | —                            | L3                       | `mootdx_port`（R3FR 已在仓内）                      | pytdx env live                  |

---

## 4. 仓内直接复用（禁止标 L1/L2/L3）

> DCP-05 / R3H-08 已 merge 的 QMD 代码：**只扩 live 路径**，不算「从参考项目拷贝」。

| 组件         | 路径                                             | M-DATA-03 动作                                                |
| ------------ | ------------------------------------------------ | ------------------------------------------------------------- |
| 增量编排     | `sync/orchestrator.py`                           | **直接复用**；禁止改 `run_incremental` 签名                   |
| Watermark    | `sync/watermark.py`                              | **直接复用**                                                  |
| 11 源 ops    | `ops/*_incremental_*.py`                         | **直接复用**；`use_mock=False` + `build_product_live_service` |
| Live 闸      | `product_live_gate.py` · `product_live_ports.py` | **直接复用**（ADR-027）                                       |
| Service 门面 | `datasources/service.py`                         | **直接复用**（ADR-025）                                       |
| Clean 路由   | `clean_write_targets.py`                         | **只读**（ADR-028）                                           |
| CLI 路由     | `data_commands.py` `--source-id`                 | **直接复用**（DCP-05 S12）                                    |
| Replay e2e   | `tests/test_*_incremental_e2e.py`                | **保留**；**追加** `@pytest.mark.network` live 变体           |

**Execute 混淆禁令：** 不得在 PR/注释写「L1 复用 orchestrator」— 应写「仓内直接复用 orchestrator」。

---

## 5. Execute RED 前门禁

1. 读 `reference-adoption-m-data-03.md` 本切片等级行
2. **L2 切片：** 列出「借鉴点」与「改造点」对照表（禁止粘贴参考代码未改）
3. **L3 切片：** 列官方 API URL（`EXTERNAL-INDEX.md` §E · `source-driven-development`）
4. 落盘 `research/execute-reference-read-evidence-<branch>.md`（Execute 阶段，非 Plan 新建）

---

## 6. 采纳决策摘要

| 能力            | 借鉴等级           | 决策                              |
| --------------- | ------------------ | --------------------------------- |
| Fetch 三阶段    | L3（OpenBB）       | 仓内行为对齐；零 OpenBB 类型      |
| 宏观 API 窗     | **L2**（bis 模式） | 思路拷改；禁 `BisProvider` import |
| 增量日期窗      | L3（EasyXT 概念）  | 文档；禁 DataManager              |
| Silent fallback | forbidden          | 负向测                            |
| 管道+clean      | **仓内直接复用**   | DCP-05；非借鉴梯                  |

## Caveats

- `参考项目/**` 将退役；L2 改造结果必须落在 qmd_owned 路径
- OpenBB provider 子文件未全量枚举；每源 RED 前 **SDD** 补官方 API
