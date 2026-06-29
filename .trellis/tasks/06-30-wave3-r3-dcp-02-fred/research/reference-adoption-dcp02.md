# R3-DCP-02 参考项目采纳调研（L1/L2/L3）

> **任务：** `.trellis/tasks/06-30-wave3-r3-dcp-02-fred`  
> **日期：** 2026-06-30  
> **方式：** 本地 `参考项目/**` + QMD 仓内源码 Read；GitNexus `query` 补链  
> **阶梯 SSOT：** `specs/contracts/reference_adoption_guardrails.yaml`

---

## 0. 调研铁律

1. `参考项目/**` **只读**；禁止 runtime import。
2. 每个结论须 **源码路径 + 符号**；README 仅线索。
3. **OpenBB = architecture_only**（AGPL）。
4. **EasyXT = forbidden**（silent_fallback / DuckDB→QMT 回退）。
5. 产品路径 SSOT：`DataSourceService` + `run_incremental`（R3H-10 / R3H-08 已闭合）。

---

## 1. 本票目标摘要

| 维度 | 内容 |
|------|------|
| **目的** | fred 宏观序列：读库水位 → 只拉新观测 → 写 `axis_observation` → CLI 可重复跑 |
| **前置** | R3H-08C CLOSED · R3H-06 clean DDL · R3H-10 金路径 |
| **不在范围** | 宏观六源全量 · 新 series UI · SEC/CFTC · 新 migration |

---

## 2. 三等级总表

| 组件 | 等级 | 证据 / 对照 | qmd_target |
|------|------|-------------|------------|
| `DataSourceService.fetch` | **L1** | `backend/app/datasources/service.py` | 增量 fetch 唯一门面 |
| `DataSyncOrchestrator.run_incremental` | **L1** | `orchestrator.py` L173-220 | 产品增量 job |
| `IncrementalJobRunner` | **L1** | `runners.py` L384-564 | staging → validate → write |
| `clean_write_targets` macro 路由 | **L1** | `clean_write_targets.py` L41-47 | `axis_observation` PK |
| `fred_port` mock/live | **L1** | `fred_port.py`（R3H-01 已 L2 迁入） | 扩展 `start_time` 窗口 |
| `product_live_gate` | **L1** | `product_live_gate.py` | env + ResourceGuard |
| `rehearsal_loader.populate_macro_from_bundle` | **L1** | `rehearsal_loader.py` L458-480 | evidence → staging 映射参照 |
| R3H-08 `reference-adoption-r3h08.md` fred 行 | **L1** | 归档调研 §4 fred Tier A | 不重复发明 live runner |
| **fred watermark reader** | **L3** | 仓内无 `watermark*.py`；GitNexus 无命中 | 新建 `ops/fred_incremental*.py` 或消费轨 A 模块 |
| **fred_port 增量窗** | **L2** | `fred_port.py` L101-121 `_window_start` 固定回溯 | 改接 `FetchRequest.start_time` → FRED `observation_start` |
| **qmd data sync fred 子路径** | **L2** | `data_commands.py` L59-77 `sync_plan` 仅 `--domain` dry-run；`main.py` L23-35 无 `--source-id` | 扩展 `--domain macro_series --source-id fred` 真跑 + watermark 窗（对齐 `live-fetch` 旗标） |
| OpenBB Fetcher 三阶段 | **architecture_only** | `C:\Users\Guang\Desktop\quant-monitor-desk\参考项目\OpenBB\openbb_platform\core\openbb_core\provider\abstract\fetcher.py` L36-85 | credentials/transform 分层对照 |
| digital-oracle BIS CSV | **L2**（本票不触） | `bis.py` L46-66 | Wave 4 宏观扩展 |
| EasyXT unified_data_interface | **forbidden** | L172-237 DuckDB→QMT 回退 | 负向测：禁止 silent 回退 |
| R3G-03 promote 链 | **L1** | `limited_production_entry.py` | 隔离写 / cap 守卫参照 |

---

## 3. 分项目深读

### 3.1 QMD 仓内 L1（直接复用）

#### DataSourceService + Orchestrator 金路径

```173:220:backend/app/sync/orchestrator.py
    def run_incremental(
        self,
        spec: SyncJobSpec,
        *,
        adapter: BaseDataAdapter | None = None,
        datasource_service=None,
        clean_table: str,
        ...
        primary_keys: tuple[str, ...] = ("instrument_id", "trade_date"),
```

**采纳：** Execute 必须 `datasource_service=DataSourceService(...)`，禁止 production adapter bypass。  
**本票差异：** `clean_table="axis_observation"`，`primary_keys=("observation_id",)`，`required_fields` 对齐 macro 契约（非 `close`/`trade_date`）。

#### fred_port（L1 基座 + L2 增量窗）

```101:121:backend/app/datasources/fetch_ports/fred_port.py
    def _window_start(self) -> date:
        days = min(MAX_WINDOW_DAYS, 365 * 3 if self.date_window == "3y" else MAX_WINDOW_DAYS)
        return datetime.now(UTC).date() - timedelta(days=days)
    ...
                "observation_start": start.isoformat(),
```

**现状：** 固定回溯窗，**未**读库水位。  
**L2 改动：** `FetchRequest.start_time`（ISO date）→ `observation_start`；无 start 时保持 capped 回溯（冷启动）。

#### macro clean 契约

```41:47:backend/app/ops/sandbox_clean_write/clean_write_targets.py
    if domain in MACRO_DOMAINS:
        return CleanWriteTarget(
            target_table="axis_observation",
            staging_table="stg_axis_observation_smoke",
            write_mode="upsert_by_pk",
            primary_keys=("observation_id",),
```

**Watermark 读侧：** `indicator_id` = fred `series_id`（P0 whitelist）；`publish_timestamp` 承载 `observation_date`（`rehearsal_loader.py` L341-354）。

#### R3H-08 归档结论（L1 承接）

自 `reference-adoption-r3h08.md` §5：

1. 不新建旁路 live runner；在 Sync + `qmd data` 接 env-gated product live。
2. fred 已在 `fetch_ports/`；08C 验证 Tier A macro 金路径。
3. `gate_live_fetch_port(source_id="fred")` 已在 `create_fred_fetch_port(use_mock=False)` 调用。

### 3.2 OpenBB（architecture_only）

```36:85:参考项目/OpenBB/openbb_platform/core/openbb_core/provider/abstract/fetcher.py
class Fetcher(Generic[Q, R]):
    require_credentials = True
    async def fetch_data(cls, params, credentials=None, **kwargs):
        query = cls.transform_query(params=params)
        data = await maybe_coroutine(cls.extract_data, ...)
        return cls.transform_data(...)
```

**采纳（L3 对齐，非拷贝）：**

- `transform_query` → `FetchRequest` + watermark 计算的 `start_time`
- `extract_data` + credentials → `FredLiveFetchPort` + `FRED_API_KEY` / `USER_AUTH_REQUIRED`
- `transform_data` → `official_macro_evidence_v1` bundle

**禁止：** 拷贝 `openbb_fred` Fetcher 类。

### 3.3 EasyXT（forbidden 反例）

```172:237:参考项目/EasyXT/data_manager/unified_data_interface.py
# Step 1: DuckDB → Step 2: 不全则 QMT（local_only=False）
```

**本票负向约束：** 禁止「库无数据则 silent 扩大窗/换源」；冷启动须显式 capped 窗或 operator 指定 `--since`。

### 3.4 R3G watermark / promote 先例（L1 仓内）

R3G-03 `limited_production_entry` + `rehearsal_loader.populate_macro_from_bundle` 已证明：

- fred evidence → `stg_axis_observation_smoke` → `axis_observation` promote 链
- `observation_id` 确定性 UUID5（`indicator_id|obs_date|content_hash`）
- 隔离库 + cap（`sandbox_clean_write_contract.yaml` fred r3g03_max_series: 10）

**本票升级点：** 从一次性 promote 升级为 **可重复 incremental**（读水位 → 窄窗 fetch → upsert 幂等）。

---

## 4. L3 绿场说明（为何不能 L1/L2）

| 能力 | 为何 L3 |
|------|---------|
| **fred per-series watermark** | 仓内无 `sync/watermark*.py`（轨 A 可能新建 bar 域 API）；宏观语义是 `indicator_id` + `DATE(publish_timestamp)`（≠ baostock `trade_date`） | `ops/fred_incremental_watermark.py` 或消费轨 A 宏观专用 API |
| **增量 CLI 真跑** | `data_commands.sync_plan` 仅 dry-run（L72-77 USER_AUTH_REQUIRED）；需 L2 扩展 fred 专用 sync 执行路径 |
| **多 series 编排** | `IncrementalJobRunner` 单次 `instrument_id`；需 L3 薄编排（loop P0 series + 汇总 report） |

---

## 5. Execute 强制门禁（摘自 R3H-08 §7 · 本票适用）

| 等级 | RED 前动作 |
|------|------------|
| L1 | Read 仓内模块 → 直接扩展 |
| L2 | Read `fred_port.py` + `data_commands.py` + OpenBB fetcher arch → 拷改对齐契约 |
| L3 | Read EasyXT 反例 + 设计注释写明拒绝项 |
| forbidden | 负向测证明无 EasyXT 式回退 |

**必 Read（RED 前）— 主仓绝对路径（worktree 无 `参考项目/`）：**

| 路径 | 等级 |
|------|------|
| `C:\Users\Guang\Desktop\quant-monitor-desk\参考项目\OpenBB\openbb_platform\core\openbb_core\provider\abstract\fetcher.py` | architecture_only |
| `C:\Users\Guang\Desktop\quant-monitor-desk\参考项目\EasyXT\data_manager\unified_data_interface.py` L172-237 | forbidden |
| QMD `fred_port.py` · `clean_write_targets.py` · `orchestrator.py`（worktree 内） | L1/L2 |
| R3H-08 归档 `reference-adoption-r3h08.md` §3.1 · §3.4 | L1 承接 |

落盘：`research/execute-reference-read-evidence.md`（见 `EXECUTE-REFERENCE-READ-GATE.md`）。

---

## 6. 调研结论

1. **主体 L1**：金路径、port、clean 路由、live gate 均已存在；本票是「接线 + watermark + CLI」而非新源。
2. **关键 L2**：`fred_port` 增量窗、`qmd data sync` fred 真跑路径。
3. **关键 L3**：fred 专用 watermark（per-series `indicator_id`）+ 多 series 编排。
4. **禁止**：旁路 pilot/rehearsal、OpenBB runtime、EasyXT 回退、改 baostock/CN 域。
