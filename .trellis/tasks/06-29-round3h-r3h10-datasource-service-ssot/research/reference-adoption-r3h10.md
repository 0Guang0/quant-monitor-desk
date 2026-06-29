# R3H-10 参考项目采纳调研（源码权威）

- **任务：** `.trellis/tasks/06-29-round3h-r3h10-datasource-service-ssot/`
- **日期：** 2026-06-29
- **调研方式：** 本地 `参考项目/**`（`.gitignore` 本地-only）逐文件 Read；**禁止以 README 为结论依据**

---

## 0. 调研铁律（写入规划约束）

### 0.1 可粘贴到 `PROJECT_IMPLEMENTATION_ROADMAP.md` / 活卡的条文

> **规划前必查参考项目源码（R3H-10 铁律）**
>
> 1. `参考项目/**` 仅作 Plan/Execute 前的**只读**对照；**禁止** runtime `import`、`sys.path` 注入、或执行期读取参考路径（见 `reference_adoption_guardrails.yaml` · `reference_tree_retirement`）。
> 2. **禁止以 README 为权威**：每个采纳/反采纳结论必须引用**实际源码**（文件路径 + 行号/类名/函数名）；README 最多作线索。
> 3. **采纳阶梯**（L1 直拷 / L2 拷改 / L3 自研）以 `specs/contracts/reference_adoption_guardrails.yaml` 为准；活卡须记录 `reference_project.*` 全套字段。
> 4. **OpenBB = `architecture_only`**（AGPL）：可借鉴 Registry + Executor + Fetcher 分层与 metadata 字段；**禁止** runtime 拷贝 Provider/Fetcher 类。
> 5. **agents-for-openbb / TradingAgents / TradingAgents-astock = Round4 only**；R3H-10（C2 DataSourceService SSOT）**无 runtime 采纳**，仅登记原因。
> 6. **EasyXT 反模式**（`silent_fallback`、`auto_login`、硬编码 DB/表名、`sys.path`）不得进入产品 Sync / `DataSourceService` 路径；仅 `data_integrity_checker` / `smart_data_detector` 的**数据质量语义**可 L2 拷改至 QMD `data_health_profiles`。
> 7. R3H-10 产品 fetch **SSOT** = `DataSourceService.fetch` / `preview_route` → `route_planner` + `capability_registry` + `ResourceGuard` + `fetch_ports`；rehearsal（`ops/*_pilot_*`）不得成为 silent bypass（见 `bypass-baseline-matrix.md`）。

### 0.2 本次调研范围

| 参考项目          | 仓库存在         | 深读锚点                                                                                                                                |
| ----------------- | ---------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| OpenBB            | ✅               | `provider_interface.py`, `query_executor.py`, `fetcher.py`, `provider.py`, `registry.py`, `fred/__init__.py`                            |
| EasyXT            | ✅               | `unified_data_interface.py`, `auto_data_updater.py`, `data_integrity_checker.py`, `smart_data_detector.py`, `duckdb_connection_pool.py` |
| digital-oracle    | ✅               | `providers/base.py`, `yfinance_provider.py`, `stooq.py`, `bis.py`, `concurrent.py`                                                      |
| JQ2PTrade         | ✅               | `ptrade_local/engine/data_loader.py`                                                                                                    |
| agents-for-openbb | ✅               | `30-vanilla-agent-raw-widget-data/.../main.py`                                                                                          |
| TradingAgents     | ✅               | `tradingagents/dataflows/interface.py`                                                                                                  |
| tdx-quant         | ✅（Java/Maven） | `pom.xml` + `src/` — 无 Python data facade                                                                                              |

---

## 1. QMD C2/E4 目标摘要（来自 to-issues-slices + service.py 源码）

### 1.1 切片目标（`research/to-issues-slices.md`）

| 切片          | 核心交付                                                                                   |
| ------------- | ------------------------------------------------------------------------------------------ |
| **S10-BOOT**  | 入口旁路基线矩阵（`bypass-baseline-matrix.md`）                                            |
| **S10-01**    | Sync 生产路径仅经 `datasource_service`；`adapter=` 生产 fail-closed                        |
| **S10-02**    | `qmd data` CLI 与 `datasource_service_contract.yaml` active 对齐                           |
| **S10-03**    | Rehearsal vs 产品路径文档硬边界                                                            |
| **S10-04**    | `interface_probe` 等旁路负向守卫扩面                                                       |
| **S10-05**    | `ops/staged_pilot_fetch_ports` / `live_pilot_fetch_ports` 收敛到 `datasources/fetch_ports` |
| **S10-CLOSE** | STAGED-PILOT-SSOT 关账 + 解锁 R3H-07                                                       |

### 1.2 QMD `DataSourceService` 金路径（`backend/app/datasources/service.py`）

```40:41:backend/app/datasources/service.py
class DataSourceService:
    """Single production fetch facade: route → capability → guard → adapter → fetch_log."""
```

关键依赖链（构造 + fetch）：

| 组件                           | 源码锚点                            | 职责                                     |
| ------------------------------ | ----------------------------------- | ---------------------------------------- |
| `SourceRegistry`               | `service.py:55-57`                  | YAML 源目录加载                          |
| `SourceCapabilityRegistry`     | `service.py:58-60`                  | domain × operation 能力门                |
| `SourceRoutePlanner`           | `service.py:61-64`, `fetch:149-155` | 可审计 route plan                        |
| `ResourceGuard`                | `service.py:160-174`                | 生产拉网前 pause/hard_stop               |
| `FetchPort` + `create_adapter` | `service.py:221-256`                | 实际拉数；生产须注入 port + FileRegistry |
| `preview_route`                | `service.py:79-96`                  | CLI `route-preview` 只读 SSOT            |

### 1.3 OPEN 旁路（`research/bypass-baseline-matrix.md`）

1. `run_interface_probe` — ❌ 直连 `interface_probe_fetch_ports`（S10-04/05）
2. `staged/live pilot` — ⚠️ 双轨 `ops/*_fetch_ports` vs `datasources/fetch_ports`（S10-05）
3. 契约 `draft_round2_6`（S10-02）

---

## 2. 参考项目 × 切片矩阵

| 参考项目              | 核心源码锚点                                                                                                      | S10-01                                 | S10-02                                  | S10-03              | S10-04                                  | S10-05                          | L1/L2/L3                                       | forbidden                                                 |
| --------------------- | ----------------------------------------------------------------------------------------------------------------- | -------------------------------------- | --------------------------------------- | ------------------- | --------------------------------------- | ------------------------------- | ---------------------------------------------- | --------------------------------------------------------- |
| **OpenBB**            | `ProviderInterface` L70-172; `QueryExecutor.execute` L65-97; `Fetcher.fetch_data` L74-85; `fred_provider` L59-103 | 架构对照：executor 无 production guard | metadata/params 合并模式可对照 CLI 契约 | 无 rehearsal 概念   | 无统一 bypass 扫描                      | Fetcher≈FetchPort 概念对齐      | **architecture_only**                          | runtime copy Provider/Fetcher; AGPL dep                   |
| **EasyXT**            | `UnifiedDataInterface` L24-301; `auto_data_updater` L87-178; `data_integrity_checker` L64-150                     | **反例**：scheduler 绕过统一门面       | 无 CLI SSOT                             | rehearsal 边界无    | **反例**：多入口 bypass facade          | 无 fetch_ports 分层             | **L2** 仅 data_health 规则; facade **L3 禁止** | silent_fallback, auto_login, hardcoded db/table, sys.path |
| **digital-oracle**    | `SignalProvider` L22-32; `gather` L70-143; `BisProvider` L46-66                                                   | 无 Sync orchestrator                   | 无 qmd CLI                              | 弱相关              | 各 provider 直连 HTTP，无 central guard | provider 独立实现，非 port 双轨 | **L3**（metadata/gather 灵感）                 | sys.path in yfinance fetcher L301-305                     |
| **JQ2PTrade**         | `DataLoader` L19-111                                                                                              | 直接 DuckDB，无 service                | 无                                      | 回测 loader，非产品 | 旁路典型                                | 无 fetch_ports                  | **L3**（report shape L2 见 guardrails）        | default db path, broad universe SQL                       |
| **agents-for-openbb** | `main.py` L13-79 `get_widget_data`                                                                                | —                                      | —                                       | —                   | —                                       | —                               | **none (Round4)**                              | agent UI; 非 C2                                           |
| **TradingAgents**     | `interface.py` L168-247 `route_to_vendor`                                                                         | —                                      | —                                       | —                   | —                                       | —                               | **none (Round4)**                              | vendor router ≠ DataSourceService                         |
| **tdx-quant**         | Java `pom.xml`                                                                                                    | —                                      | —                                       | —                   | —                                       | —                               | **none**                                       | 非 Python 栈                                              |

---

## 3. 分项目深读

### 3.1 OpenBB（`architecture_only` · AGPL）

#### 架构要点（源码）

**① ProviderInterface 单例门面**

```70:105:参考项目/OpenBB/openbb_platform/core/openbb_core/app/provider_interface.py
class ProviderInterface(metaclass=SingletonMeta):
    ...
    def __init__(
        self,
        registry_map: RegistryMap | None = None,
        query_executor: QueryExecutor | None = None,
    ) -> None:
        self._registry_map = registry_map or RegistryMap()
        self._query_executor = query_executor or QueryExecutor
```

- 单例持有 `RegistryMap` + `QueryExecutor` 工厂；`create_executor()`（L170-172）把 registry 注入 executor。

**② RegistryLoader — entry point 插件注册**

```34:55:参考项目/OpenBB/openbb_platform/core/openbb_core/provider/registry.py
class RegistryLoader:
    @staticmethod
    @lru_cache
    def from_extensions() -> Registry:
        registry = Registry()
        for name, entry in ExtensionLoader().provider_objects.items():
            ...
            registry.include_provider(provider=entry)
```

**③ Provider + fetcher_dict**

```6:45:参考项目/OpenBB/openbb_platform/core/openbb_core/provider/abstract/provider.py
class Provider:
    def __init__(..., fetcher_dict: dict[str, type[Fetcher]] | None = None, ...):
        ...
        self.fetcher_dict = fetcher_dict or {}
```

**④ QueryExecutor.execute 管线**

```65:97:参考项目/OpenBB/openbb_platform/core/openbb_core/provider/query_executor.py
    async def execute(self, provider_name, model_name, params, credentials=None, **kwargs):
        provider = self.get_provider(provider_name)
        fetcher = self.get_fetcher(provider, model_name)
        filtered_credentials = self.filter_credentials(...)
        return await fetcher.fetch_data(params, filtered_credentials, **kwargs)
```

**⑤ Fetcher TET 管道**

```74:85:参考项目/OpenBB/openbb_platform/core/openbb_core/provider/abstract/fetcher.py
    async def fetch_data(cls, params, credentials=None, **kwargs):
        query = cls.transform_query(params=params)
        data = await maybe_coroutine(cls.extract_data, query=query, credentials=credentials, **kwargs)
        return cls.transform_data(query=query, data=data, **kwargs)
```

**⑥ 具体 provider 注册示例（fred）**

```59:66:参考项目/OpenBB/openbb_platform/providers/fred/openbb_fred/__init__.py
fred_provider = Provider(
    name="fred",
    ...
    fetcher_dict={
        "BalanceOfPayments": FredBalanceOfPaymentsFetcher,
        ...
        "FredSeries": FredSeriesFetcher,
```

#### 与 QMD 差异

| 维度       | OpenBB                                    | QMD C2                                                       |
| ---------- | ----------------------------------------- | ------------------------------------------------------------ |
| 注册       | Entry point 动态加载                      | `SourceRegistry` YAML + DB sync                              |
| 路由       | 调用方显式 `provider_name` + `model_name` | `SourceRoutePlanner` 按 domain/operation/market 规划         |
| 执行前守卫 | credential filter only                    | capability + license gate + **ResourceGuard** + route_status |
| 拉数抽象   | `Fetcher`（TET 三阶段）                   | `FetchPort` + `BaseDataAdapter` + `FetchLogWriter`           |
| 旁路审计   | 无等价 `forbidden_direct_callers`         | 契约 + pytest 扫描                                           |

#### 可采纳点（architecture_only）

- **三件套心智模型**：Registry（catalog）→ Executor（dispatch）→ Fetcher/Port（vendor pull）— 与 QMD `SourceRegistry` → `DataSourceService` → `FetchPort` 对照写 ADR。
- **Provider metadata 字段**：`name`, `description`, `website`, `credentials`, `instructions`（`provider.py` L10-41）→ 可启发 QMD `source_registry` 文档字段，**不拷类**。
- **fetcher_dict 按 model 名索引** → 类比 QMD `capability_registry` 的 operation 映射，非 runtime 拷贝。

#### 禁止直拷点

- 整个 `Provider` / `Fetcher` / `QueryExecutor` 类（AGPL + `forbidden_adoption.copied_openbb_runtime_source`）。
- `ProviderInterface` 单例 + FastAPI pydantic 动态模型生成（L500-541）— 与 QMD monitor-desk 定位不符。

#### 建议 ADR 一句

> R3H-10 不引入 OpenBB runtime；仅在活卡/ADR 中记录「Registry + Executor + Port」分层与 QMD `route+capability+guard` 的对照表，provider catalog metadata 字段对齐 `source_registry.yaml` 已有列。

---

### 3.2 EasyXT

#### 架构要点（源码）

**① UnifiedDataInterface — DuckDB 优先 + QMT 静默回退**

```24:34:参考项目/EasyXT/data_manager/unified_data_interface.py
class UnifiedDataInterface:
    """
    ...
    1. 优先从DuckDB读取原始数据
    2. 如无数据或数据不全，使用QMT在线获取
    3. 获取后自动保存到DuckDB
```

- 默认 DB：`get_default_db_path()`（L22-44）— 硬编码路径查找。
- **auto-login**（L72-100）：`QMTAutoLogin().login()` 在 QMT 不可用时自动恢复。
- **silent fallback 链**（L239-287）：DuckDB 无数据 → QMT 在线 → 合并失败则「降级：只使用 QMT 数据」（L284-285）；无 `source_route_log` 或显式 route flag。

**② auto_data_updater — bypass 统一门面**

```87:93:参考项目/EasyXT/data_manager/auto_data_updater.py
    def initialize_data_manager(self):
        ...
            sys.path.insert(0, str(Path(__file__).parent.parent / 'gui_app' / 'backtest'))
            from data_manager import DataManager
            self.data_manager = DataManager()
```

- 定时 sync（`schedule` L21）经 **GUI backtest DataManager**，非 `UnifiedDataInterface` 单一 SSOT。
- `update_single_stock`（L173-178）直接 `data_manager.get_stock_data()`。

**③ data_integrity_checker — 可 L2 借鉴的质量语义**

```64:87:参考项目/EasyXT/data_manager/data_integrity_checker.py
class DataIntegrityChecker:
    ...
    def __init__(self, duckdb_path: str = None):
        ...
        self.detector = SmartDataDetector(duckdb_path)
        self.calendar = TradingCalendar()
```

- 检查流水线：缺失交易日 → OHLCV 质量 → 价格关系 → 异常值（L112-148）。

**④ smart_data_detector — 日历 + 缺失检测**

```27:35:参考项目/EasyXT/data_manager/smart_data_detector.py
class TradingCalendar:
    """A股交易日历管理器"""
    def __init__(self):
        self.holidays = self._load_holidays()
```

```256:264:参考项目/EasyXT/data_manager/smart_data_detector.py
        query = f"""
            SELECT date
            FROM stock_daily
            WHERE stock_code = '{stock_code}'
            ...
        """
```

- 硬编码表名 `stock_daily` + 插值 SQL（guardrails `easyxt_data_quality_rules.required_rewrites` 已列）。

**⑤ duckdb_connection_pool — 连接单例**

```22:42:参考项目/EasyXT/data_manager/duckdb_connection_pool.py
class DuckDBConnectionManager:
    _instance = None
    def __new__(cls, duckdb_path: str = None):
        if cls._instance is None:
            ...
```

#### 与 QMD 切片对照

| 切片       | EasyXT 启示                                                               |
| ---------- | ------------------------------------------------------------------------- |
| **S10-01** | `auto_data_updater` = **反例**：生产 sync 不得有第二条 `DataManager` 入口 |
| **S10-03** | EasyXT 无 rehearsal 标记；QMD 须显式 `REHEARSAL_ONLY`                     |
| **S10-04** | `UnifiedDataInterface` 与 `AutoDataUpdater` 双入口 = bypass 扩面测试灵感  |
| **S10-05** | EasyXT 无 `fetch_ports` 分层；QMD 双轨问题无直接解法，仅负向对照          |

#### forbidden_semantics（P0）

| 语义              | 源码证据                                                         |
| ----------------- | ---------------------------------------------------------------- |
| `silent_fallback` | `unified_data_interface.py` L242-287 DuckDB→QMT 无 route 日志    |
| `auto_login`      | `unified_data_interface.py` L90-96 `QMTAutoLogin`                |
| `hardcoded db`    | `get_default_db_path()` 多处默认                                 |
| `sys.path`        | `auto_data_updater.py` L32, L91; `data_integrity_checker.py` L24 |
| `scheduler hook`  | `auto_data_updater.py` `schedule` + 后台线程                     |

#### 可采纳点（L2 · guardrails 已登记）

- `DataIntegrityChecker.check_integrity` 报告形状 → QMD `DataHealthCheckResult` / `calendar_gap_rules`（须去 duckdb 直查、去硬编码表名）。
- `TradingCalendar.get_missing_trading_days`（L166-183）→ R3H-07 日历切片输入，**非 R3H-10 C2 本体**。

#### 建议 ADR 一句

> R3H-10 不采纳 EasyXT 数据门面；将 `auto_data_updater`/`UnifiedDataInterface` 多入口与 silent QMT fallback 写入 S10-04 负向测清单；数据质量规则仅通过已登记的 L2 路径进入 `data_health_profiles`。

---

### 3.3 digital-oracle

#### 架构要点（源码）

**① SignalProvider 基类 + metadata**

```15:32:参考项目/digital-oracle/digital_oracle/providers/base.py
@dataclass(frozen=True)
class ProviderMetadata:
    provider_id: str
    display_name: str
    capabilities: tuple[str, ...]

class SignalProvider(ABC):
    provider_id: str
    display_name: str
    capabilities: tuple[str, ...] = ()
    def describe(self) -> ProviderMetadata: ...
```

**② 扁平导出，无中央 Registry**

`digital_oracle/providers/__init__.py` L1-188 — 各 `*Provider` 显式 import/export，**无**类似 QMD `SourceRegistry.load()` 的统一加载器。

**③ 典型 fetch 模式**

| Provider             | 模式                             | 锚点                                      |
| -------------------- | -------------------------------- | ----------------------------------------- |
| **BisProvider**      | HTTP GET + CSV parse             | `bis.py` L46-66 `get_policy_rates`        |
| **StooqProvider**    | 兼容层委托 Yahoo                 | `stooq.py` L44-75 `_provider.get_history` |
| **YFinanceProvider** | 可注入 `OptionsFetcher` Protocol | `yfinance_provider.py` L362-374           |

**④ 并行 gather**

```70:106:参考项目/digital-oracle/digital_oracle/concurrent.py
def gather(tasks: dict[str, Callable[[], Any]], *, max_workers=None, ...):
    with concurrent.futures.ThreadPoolExecutor(max_workers=effective_workers) as pool:
        ...
```

#### 与 QMD C2 关系

- **弱相关**：digital-oracle 面向 signal/analysis provider，无 Sync orchestrator、无 `route_planner`、无 production guard。
- **微弱正借鉴**：`ProviderMetadata` + `capabilities` tuple ≈ QMD source_registry 元数据；`gather()` 可用于未来多源 probe **rehearsal** 并行（非 R3H-10 必做）。

#### 建议 ADR 一句

> digital-oracle 不进入 R3H-10 实现；若后续多源 interface_probe 需并行拉网，可参考 `gather()` 模式，但仍须委托 `DataSourceService.fetch`。

---

### 3.4 JQ2PTrade

#### 架构要点（源码）

```19:55:参考项目/JQ2PTrade/ptrade_local/engine/data_loader.py
class DataLoader:
    def __init__(self, duckdb_path: str = 'D:/StockData/stock_data.ddb'):
        ...
    def load(self, start_date, end_date) -> DataBundle:
        ...
        con = duckdb.connect(self.duckdb_path, read_only=True)
        sql = f"""SELECT ... FROM stock_daily WHERE ... date >= '{extended_start...}' ..."""
        df = con.execute(sql).fetchdf()
```

- **绕过任何统一 fetch facade**：策略回测直接从 DuckDB 宽表加载全市场。
- 默认路径 `D:/StockData/stock_data.ddb`（L20）— guardrails `jq2ptrade_loader_report_shapes.required_rewrites`。
- `print` 控制台报告（L40-106）— 非 structured evidence。

#### 与 QMD

- **弱相关 L3**：与 C2 SSOT 无关；仅 3G sandbox rehearsal loader **形状**参考（已 CLOSED）。
- S10-01/05：**无采纳**；作为「旁路 loader」反例记入 S10-03 文档边界。

#### 建议 ADR 一句

> JQ2PTrade `DataLoader` 不参与 R3H-10；回测 frozen-data 形状已在 3G 消化，C2 继续禁止类似 broad-universe DuckDB 直读进入产品 Sync 链。

---

### 3.5 agents-for-openbb（Round4 only · 无采纳）

#### 源码要点

```13:14:参考项目/agents-for-openbb/30-vanilla-agent-raw-widget-data/vanilla_agent_raw_context/main.py
from openbb_ai import WidgetRequest, get_widget_data, message_chunk
```

```78:79:参考项目/agents-for-openbb/30-vanilla-agent-raw-widget-data/vanilla_agent_raw_context/main.py
        async def retrieve_widget_data():
            yield get_widget_data(widget_requests).model_dump()
```

- 数据经 **OpenBB Terminal Pro widget API**（`get_widget_data`），非自建 `DataSourceService`。
- FastAPI agent 端点；与 Sync / `qmd data` / fetch_ports **无交集**。

#### 无采纳原因

`reference_adoption_guardrails.yaml` L126-133：`agents_round4_only` · `round3g_allowed_use: none`。

---

### 3.6 TradingAgents / tdx-quant（Round4/none · 快速扫描）

#### TradingAgents

```168:193:参考项目/TradingAgents/tradingagents/dataflows/interface.py
def route_to_vendor(method: str, *args, **kwargs):
    """Route method calls to appropriate vendor implementation with fallback support."""
    ...
    # The configured vendor list IS the chain: we do NOT silently fall back to
    # vendors the user did not choose
```

- **工具向 vendor 路由器**（`VENDOR_METHODS` 字典 L95-144），服务 LLM agent 工具调用，不是 production `DataSourceService`。
- 显式 vendor chain 设计**反而可作 S10-01 正面参照**（配置外 vendor 不静默切换）— 但代码本身 **Round4 only，不拷**。

#### tdx-quant

- 仓库为 **Java Maven**（`pom.xml`），`src/` 下无 Python data facade。
- 与 C2/E4 **无采纳**。

---

## 4. 综合建议（Execute 前 Plan 必读）

### 4.1 OpenBB architecture_only → QMD 映射

```text
OpenBB                          QMD R3H-10
─────────────────────────────────────────────────────
RegistryLoader (entry points)   SourceRegistry (YAML SSOT)
Provider.fetcher_dict           SourceCapabilityRegistry (domain×op)
QueryExecutor.execute           DataSourceService.fetch
Fetcher TET pipeline            FetchPort + normalizer + adapter
ProviderInterface singleton     DataSourceService (非单例，可注入)
(credential filter)             ResourceGuard + license_gate + route_status
```

**Plan 应写清**：R3H-10 收敛的是 **QMD 已有** `route+capability+guard+fetch_ports` 链上的旁路，**不**引入 OpenBB 插件体系。

### 4.2 EasyXT 反模式清单 → S10-03/S10-04 负向测灵感

| #   | 反模式                                              | 建议负向断言                                                            |
| --- | --------------------------------------------------- | ----------------------------------------------------------------------- |
| E1  | 第二条 sync 入口（`AutoDataUpdater`→`DataManager`） | 生产包扫描：sync 链不得 import `gui_app/backtest/data_manager` 等价路径 |
| E2  | DuckDB→QMT silent fallback 无 route log             | fetch 失败/换源须写 `FetchLog` + `route_status` / explicit flag         |
| E3  | `QMTAutoLogin`                                      | `test_noAutoLoginCopied` 延续                                           |
| E4  | `get_default_db_path()` 硬编码                      | `test_noEasyxtHardcodedTableInDataHealth` 延续                          |
| E5  | `sys.path.insert` 参考树/旁路包                     | `test_noReferenceProjectRuntimeImport`                                  |

### 4.3 digital-oracle 有限价值

- **Provider metadata**：`describe()` → 对齐 QMD registry 已有字段即可，无需新依赖。
- **gather 并行**：仅当 S10-04 改造 `interface_probe` 需多 cap 并行时参考；实现仍委托 `DataSourceService`。

### 4.4 Execute 优先级（与切片一致）

1. S10-01 复核现有 `test_r3ySync001_*`（EasyXT/JQ2PTrade 反例作文档引用，不改测目的）
2. S10-02 契约 active
3. S10-04 `interface_probe` 委托 service（digital-oracle gather 可选）
4. S10-05 fetch_ports 单实现收敛（OpenBB Fetcher 概念仅 ADR 对照）

---

## 5. 与 guardrails.yaml 一致性核对

| guardrails 条目                                            | 本次调研结论                                                             |
| ---------------------------------------------------------- | ------------------------------------------------------------------------ |
| `openbb_provider_architecture` · architecture_only         | ✅ 仅记录三件套架构；无 runtime copy 建议                                |
| `easyxt_data_quality_rules` · L2                           | ✅ `data_integrity_checker`/`smart_data_detector` 语义可 L2；facade 禁止 |
| `jq2ptrade_loader_report_shapes`                           | ✅ L3/已消化；R3H-10 不扩 scope                                          |
| `agents_round4_only`                                       | ✅ agents-for-openbb、TradingAgents 登记 none                            |
| `forbidden_adoption.silent_fallback`                       | ✅ EasyXT `UnifiedDataInterface` 标 P0 反例                              |
| `forbidden_adoption.auto_login`                            | ✅ EasyXT L90-96 标 P0                                                   |
| `forbidden_adoption.runtime_import_from_reference_project` | ✅ 全部参考仅 Plan Read                                                  |
| `reference_tree_retirement`                                | ✅ 调研结论不依赖参考树 runtime 存在                                     |

---

## 6. 未覆盖 / 需用户裁决项

| #      | 项                                                       | 说明                                                                                            |
| ------ | -------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| ~~U1~~ | ~~S10-01 无 service 时 fail-closed vs 默认构造 service~~ | **已裁决 @ 2026-06-29：fail-closed**（见 `to-issues-slices.md` §3）                             |
| U2     | **EasyXT `TradingCalendar` 完整节假日**                  | 属 R3H-07/CAL-US，非 R3H-10；本调研仅引用源码存在性                                             |
| U3     | **digital-oracle `gather` 是否用于 interface_probe**     | 可选优化，非 PASS 阻塞；默认单线程委托 service 即可                                             |
| U4     | **参考树本地缺失时**                                     | 本次环境 `参考项目/**` 存在；若 CI/其他机器缺失，Plan 须注明「Execute 前本地 clone 参考树只读」 |
| U5     | **tdx-quant**                                            | Java 项目，与 C2 无交集；是否保留在 R3H 参考清单由主会话决定                                    |

---

## 附录：源码文件清单

| 项目              | 已读文件                                                                                                                                                                                                                                                   |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| OpenBB            | `openbb_core/app/provider_interface.py`, `provider/query_executor.py`, `provider/abstract/fetcher.py`, `provider/abstract/provider.py`, `provider/registry.py`, `providers/fred/openbb_fred/__init__.py`, `providers/yfinance/openbb_yfinance/__init__.py` |
| EasyXT            | `data_manager/unified_data_interface.py`, `auto_data_updater.py`, `data_integrity_checker.py`, `smart_data_detector.py`, `duckdb_connection_pool.py`                                                                                                       |
| digital-oracle    | `digital_oracle/providers/base.py`, `yfinance_provider.py`, `stooq.py`, `bis.py`, `concurrent.py`, `providers/__init__.py`                                                                                                                                 |
| JQ2PTrade         | `ptrade_local/engine/data_loader.py`                                                                                                                                                                                                                       |
| agents-for-openbb | `30-vanilla-agent-raw-widget-data/vanilla_agent_raw_context/main.py`                                                                                                                                                                                       |
| TradingAgents     | `tradingagents/dataflows/interface.py`                                                                                                                                                                                                                     |
| QMD               | `backend/app/datasources/service.py`, `source_registry.py`, `route_planner.py`                                                                                                                                                                             |
