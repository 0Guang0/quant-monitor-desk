# R3H-08 参考项目采纳调研（源码权威 · 三等级）

- **任务：** `.trellis/tasks/06-29-round3h-r3h08-live-productization/`
- **日期：** 2026-06-29
- **调研方式：** 本地 `参考项目/**` 逐文件 Read + QMD 现有 `fetch_ports/` / `DataSourceService` / R3G-03 对照；**禁止以 README 为结论依据**
- **阶梯 SSOT：** `specs/contracts/reference_adoption_guardrails.yaml` · `adoption_ladder` L1/L2/L3

---

## 0. 调研铁律（写入本票规划约束）

1. `参考项目/**` **只读**；禁止 runtime import / sys.path / 执行期读参考路径。
2. 每个采纳/反采纳结论必须引用**源码**（路径 + 行号/符号）；README 仅作线索。
3. **OpenBB = architecture_only**（AGPL）：可借鉴 Fetcher 三阶段与 credentials 门；禁止 runtime 拷贝 Provider/Fetcher。
4. **EasyXT 反模式**不得进入产品 live：`silent_fallback`、DuckDB→QMT 自动回退、`auto_login`、`schedule` 旁路门面、`sys.path.insert`、硬编码 `get_default_db_path()`。
5. **agents-for-openbb / TradingAgents / TradingAgents-astock = Round4 only**；R3H-08 **无 runtime 采纳**。
6. **产品 live SSOT**（R3H-10 已闭合）：`DataSourceService.fetch` / `preview_route` → `fetch_ports/*` → `ResourceGuard`；`ops/*_pilot_*` 带 `REHEARSAL_ONLY`（`rehearsal_boundary.py`），**不得**作为 R3H-08 产品路径替身。

---

## 1. QMD 目标摘要（Wave 2 · LIVE-PROD）

| 维度         | 内容                                                                                                          |
| ------------ | ------------------------------------------------------------------------------------------------------------- |
| **目的**     | 24 业务源 **env-gated 产品 live**；经 `DataSourceService`；落库 Tier A/B/C（`R3H_PASS_EXECUTION_PLAN.md` §2） |
| **前置**     | R3H-10 CLOSED（C2 SSOT）· R3H-07 CLOSED @ `94ccd326`（CAL-US）· R3H-06 clean DDL                              |
| **串行**     | 单 agent：**08C → 08A → 08B → 08D**（PASS §4.1）                                                              |
| **不在范围** | web_search 真 API · 新 migration DDL · Round4 API · 删 pilot 模块                                             |

---

## 2. 参考项目 × R3H-08 切片矩阵（L1/L2/L3）

| 参考项目           | 核心源码锚点                                                                                                                      | 08C 宏观                            | 08A CN                | 08B validation            | 08D Tier C              | 等级                  | forbidden                                            |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- | --------------------- | ------------------------- | ----------------------- | --------------------- | ---------------------------------------------------- |
| **OpenBB**         | `fetcher.py` L36-85 `Fetcher.fetch_data`; `fred/__init__.py` Provider 注册表                                                      | credentials 门 · transform 管线灵感 | 同左                  | 同左                      | 无                      | **architecture_only** | runtime Provider/Fetcher copy                        |
| **digital-oracle** | `base.py` SignalProvider; `bis.py` L46-80 CSV parse; `kalshi.py` L43-96; `polymarket.py` L48-60; `concurrent.py` L70-143 `gather` | BIS CSV URL 形态 L2                 | —                     | yfinance 期权/Greeks L3   | kalshi/poly 概率字段 L2 | **L2/L3**             | 整包 import；无 central guard 的直连 HTTP 当产品路径 |
| **EasyXT**         | `unified_data_interface.py` L6,L29,L172-237 DuckDB→QMT 回退; `auto_data_updater.py` L31-32 sys.path, L87-97 绕过门面              | **反例**                            | **反例**              | **反例**                  | **反例**                | **forbidden**         | silent_fallback, auto_login, scheduler bypass        |
| **JQ2PTrade**      | `data_loader.py` 直连 DuckDB                                                                                                      | —                                   | —                     | rehearsal report shape L2 | —                       | **L3**                | default db path, broad universe                      |
| **QMD R3G-03**     | `limited_production_entry.py` L166-180 validation_only DB 隔离; `clean_write_targets.py`                                          | Tier A promote 链                   | Tier A bar/disclosure | Tier B pilot DB           | —                       | **L1 仓内复用**       | canonical main DB silent promote                     |
| **QMD R3H-10**     | `service.py` L40-41; `rehearsal_boundary.py`                                                                                      | 金路径                              | 金路径                | 金路径                    | probe 委托 service      | **L1 仓内复用**       | 新建 bypass                                          |

---

## 3. 分项目深读

### 3.1 OpenBB（architecture_only · AGPL）

**Fetcher 三阶段（可对照 QMD FetchPort）：**

```36:85:参考项目/OpenBB/openbb_platform/core/openbb_core/provider/abstract/fetcher.py
class Fetcher(Generic[Q, R]):
    require_credentials = True
    ...
    async def fetch_data(cls, params, credentials=None, **kwargs):
        query = cls.transform_query(params=params)
        data = await maybe_coroutine(cls.extract_data, query=query, credentials=credentials, **kwargs)
        return cls.transform_data(query=query, data=data, **kwargs)
```

**采纳（L3 自研对齐，非拷贝）：**

- `transform_query` → QMD `FetchRequest` + capability assert
- `extract_data` + credentials → QMD port `USER_AUTH_REQUIRED` / env key（已有 `fred_port.py` L95-109）
- `transform_data` → raw file + `FetchResult` 行集

**禁止：** 拷贝 `openbb_fred` Fetcher 类；AGPL runtime 依赖。

### 3.2 digital-oracle（L2 解析形态 · L3 编排）

**① Provider 元数据（L3 灵感）**

```22:32:参考项目/digital-oracle/digital_oracle/providers/base.py
class SignalProvider(ABC):
    provider_id: str
    display_name: str
    capabilities: tuple[str, ...] = ()
```

QMD 已有 `source_registry.yaml` + `capability_registry` — **不新建** SignalProvider 平行体系。

**② BIS CSV live（L2：URL/parse 对照，实现留在 `bis_port`）**

```46:66:参考项目/digital-oracle/digital_oracle/providers/bis.py
class BisProvider(SignalProvider):
    def get_policy_rates(self, query):
        url = f"{BIS_BASE_URL}/data/WS_CBPOL/M.{country_codes}"
        payload = self.http_client.get_text(url, params={...,"format": "csv"})
        return self._parse_policy_rates_csv(payload)
```

**③ Kalshi / Polymarket 概率（L2：字段语义，Tier C）**

- `KalshiMarket.yes_probability` L88-96：midpoint 或 last_price — QMD `kalshi_port` / `polymarket_port` 对齐 evidence 形，不经 rehearsal pilot。
- `PolymarketMarket` + `OutcomeQuote.probability` — Tier C manual_review 域。

**④ concurrent.gather（L3 不采纳本票）**

`gather()` 线程池并行适合 digital-oracle 批量探针；R3H-08 产品 live 须 **ResourceGuard 预算内串行/有界并行** — 并行 gather **defer** Wave 4 性能切片，本票 ponytail 单源 tracer bullet。

### 3.3 EasyXT（全面反采纳 · P0 forbidden）

**silent_fallback 铁证：**

```6:6:参考项目/EasyXT/data_manager/unified_data_interface.py
优先使用DuckDB本地数据，自动回退到QMT在线数据，并自动保存到DuckDB
```

```172:237:参考项目/EasyXT/data_manager/unified_data_interface.py
# Step 1: DuckDB → Step 2: 不全则 QMT（local_only=False）
# 查询失败 → 降级 _read_from_duckdb
```

**scheduler 旁路门面：**

```31:32:参考项目/EasyXT/data_manager/auto_data_updater.py
sys.path.insert(0, str(Path(__file__).parent))
```

```87:97:参考项目/EasyXT/data_manager/auto_data_updater.py
# 延迟初始化 DataManager — 非 DataSourceService
```

**QMD 替代：** `DataSyncOrchestrator` + `datasource_service=` + env `QMD_ALLOW_LIVE_FETCH=1`（拟 ADR-027）；**禁止** DuckDB miss 时 silent 切源。

### 3.4 QMD 仓内 L1（优先复用，非参考树）

| 模块                 | 路径                                                       | R3H-08 用途                            |
| -------------------- | ---------------------------------------------------------- | -------------------------------------- |
| DataSourceService    | `backend/app/datasources/service.py`                       | 唯一产品 fetch 门面                    |
| fetch_ports/\*       | `backend/app/datasources/fetch_ports/`                     | 各源 live 实现（多数已有 opt-in stub） |
| validation_only 隔离 | `limited_production_entry.py` L166-180                     | Tier B 仅 pilot DB                     |
| clean 域路由         | `clean_write_targets.py`                                   | Tier A bar/disclosure/macro            |
| rehearsal 边界       | `rehearsal_boundary.py`                                    | 与产品 live 测试负向分离               |
| Sync 金路径          | `orchestrator.py` `run_incremental` + `datasource_service` | 产品增量 live 接线                     |

---

## 4. 逐源采纳等级（24 业务源 · PASS §2.1）

| source_id                                                                       | Tier   | 参考对照                          | 等级         | qmd_target（Execute）                      |
| ------------------------------------------------------------------------------- | ------ | --------------------------------- | ------------ | ------------------------------------------ |
| fred, us_treasury, sec_edgar, cftc_cot, bis, world_bank, alpha_vantage, deribit | A      | OpenBB arch + digital-oracle HTTP | **L2/L3**    | `*_port.py` live 启用 + service 金路径测   |
| baostock, cninfo, mootdx                                                        | A      | EasyXT **反例**                   | **L3**       | `cn_*_port` / `baostock_port` product live |
| yahoo, akshare, stooq, coingecko, eastmoney, sina, tdx*pytdx, ths, qmt*\*       | B      | EasyXT validation 反例            | **L3**       | validation_only + pilot DB guard           |
| kalshi, polymarket                                                              | C      | digital-oracle L2 概率字段        | **L2/L3**    | probability domain + env gate              |
| web_search                                                                      | C mock | —                                 | **阶段外置** | post-Round4                                |

---

## 5. 调研结论（供架构设计）

1. **不新建**「第二套 live runner」旁路 `DataSourceService`；在 **Sync + `qmd data`** 上接 env-gated product live flag。
2. **不拷贝** 参考项目 Provider 类；仅在 port 内 L2 对齐 HTTP/CSV/概率 **解析语义**。
3. **Tier 路由** 扩展现有 `clean_write_targets` + `limited_production_entry` 守卫，不引入 EasyXT 式 DB 回退。
4. **08C 先行**：宏观/市场 primary 源 live 形态最齐，可验证 Tier A macro + market 金路径。
5. **R3H-10 阶段外置承接**：`run_reconcile` + `datasource_service=`、`interface_probe` 全 service 化 → 本票 S08-05 横切切片。

---

## 6. Caveats

- `参考项目/OpenBB` 部分路径与 R3H-10 审计版本略有差异；以实际 `fetcher.py` 为准。
- `alpha_vantage_port.py` live 仍部分 delegate mock（源码 L178-179）— 08C 须 RED 证明后 GREEN。
- `clean_write_targets.py` 当前仅 CN bar + macro + disclosure；US market bar 域 **defer Wave 3 R3-DCP** — 08C/08A 以 **raw + macro + 已有域** 为主，不扩 DDL。

---

## 7. Execute 强制门禁（参考项目源码 · 三等级）

> **用户补充 @ 2026-06-29：** Execute agent **必须**根据本节与 `EXTERNAL-INDEX.md` §D，在**每个切片 RED 之前**实际 Read 参考项目源码，再写 QMD 代码。  
> **禁止**不参考参考项目、直接从零臆造实现。  
> **只读：** `参考项目/**` 不得 runtime import；产出必须是 `qmd_owned` 代码。

### 7.1 等级执行规则

| 等级                  | Execute 动作                                         | 禁止                           |
| --------------------- | ---------------------------------------------------- | ------------------------------ |
| **L1**                | Read 源码 → 拷入 `qmd_target` 并登记 cite            | 未 Read 就写                   |
| **L2**                | Read 源码 → 拷改对齐 ConnectionManager/registry/gate | 整类 runtime 拷贝              |
| **L3**                | Read 源码 + 反例 → 最小自研；注释写明对照与拒绝项    | 无 cite 的 greenfield          |
| **architecture_only** | Read 架构锚点 → 仅对齐分层/字段名                    | 拷贝 Provider/Fetcher 类       |
| **forbidden**         | Read 反例锚点 → 负向测证明未渗入                     | 借鉴 EasyXT fallback/scheduler |

### 7.2 逐切片必 Read 源码（`参考项目/**` · RED 前）

| 切片           | 必 Read 文件（磁盘路径 · 只读）                                                          | 等级               | 用途                              |
| -------------- | ---------------------------------------------------------------------------------------- | ------------------ | --------------------------------- |
| **S08-BOOT**   | `specs/contracts/reference_adoption_guardrails.yaml`（非参考树但同级门禁）               | —                  | 矩阵列 cite 列                    |
| **S08-01 08C** | `参考项目/OpenBB/openbb_platform/core/openbb_core/provider/abstract/fetcher.py`          | arch               | Fetcher 三阶段                    |
|                | `参考项目/digital-oracle/digital_oracle/providers/bis.py`                                | L2                 | BIS CSV URL/parse                 |
|                | `参考项目/digital-oracle/digital_oracle/providers/base.py`                               | L3                 | Provider 元数据（不平行新建体系） |
| **S08-02 08A** | `参考项目/EasyXT/data_manager/unified_data_interface.py` L6,L172-237                     | **forbidden 反例** | 禁止 DuckDB→QMT 回退              |
|                | QMD `backend/app/datasources/fetch_ports/baostock_port.py` 等（仓内 L1）                 | L1                 | 在参考 Read 后扩展 live           |
| **S08-03 08B** | `参考项目/EasyXT/data_manager/unified_data_interface.py`（validation 反例）              | forbidden          | Tier B 不得升 primary             |
|                | `参考项目/digital-oracle/digital_oracle/providers/yfinance_provider.py`（若触 yahoo 域） | L2/L3              | HTTP 形态对照                     |
|                | QMD `limited_production_entry.py` L166-180                                               | L1                 | pilot DB 隔离                     |
| **S08-04 08D** | `参考项目/digital-oracle/digital_oracle/providers/kalshi.py` L43-96                      | L2                 | 概率字段                          |
|                | `参考项目/digital-oracle/digital_oracle/providers/polymarket.py` L48-60                  | L2                 | OutcomeQuote                      |
| **S08-05**     | `参考项目/OpenBB/openbb_platform/core/openbb_core/provider/abstract/fetcher.py`          | arch               | CLI/sync 边界对照                 |
|                | QMD `orchestrator.py` · `interface_probe.py`                                             | L1                 | defer 闭合                        |

### 7.3 证据要求

- BOOT 矩阵须含列：`reference_anchor` · `adoption_level` · `qmd_target`
- 每个新增/修改 `test_*` 的 docstring 或紧邻注释须含：**参考路径 + 采纳等级 + 验证点**
- Audit 可抽检：无 cite 的 port 改动 = **BLOCKING**

### 7.4 Execute 同流程（与主会话零差）

- SSOT：`research/execute-parity-contract.md`
- 子 agent Boot/切片/TDD/收尾 **=** 主会话 `trellis-execute` 全文；**仅** 不得 commit / finish-work
