# Audit A2 — Ponytail / 过度工程

> **维：** A2 (audit-ponytail)  
> **任务：** `.trellis/tasks/06-30-wave3-r3-dcp-02-fred`  
> **协议：** debt-lite Phase 8D · `plan_protocol_version: 4.1`  
> **Worktree：** `../quant-monitor-desk-wt-dcp02` · branch `feature/wave3-r3-dcp-02-fred`  
> **审计日期：** 2026-06-30  
> **模板：** `agents/audit-a2-ponytail.md`

---

## 维度证据

### git diff --stat（相对 master · 已跟踪 · 独立复验）

```text
 backend/app/cli/data_commands.py                 | 180 ++++++++++++++++++++---
 backend/app/cli/main.py                          |   2 +
 backend/app/datasources/fetch_ports/fred_port.py |  37 ++++-
 3 files changed, 189 insertions(+), 30 deletions(-)
```

**说明：** `tests/test_catalog.yaml` 已由协调者 revert，**不在**当前 diff；本维不记 catalog 问题。

**未跟踪（本任务核心实现）：**

| 文件                                             | 行数 | 角色                       |
| ------------------------------------------------ | ---- | -------------------------- |
| `backend/app/ops/fred_incremental_run.py`        | 347  | 金路径编排 + runtime patch |
| `backend/app/ops/fred_incremental_watermark.py`  | 90   | 宏观水位 reader            |
| `tests/test_fred_macro_incremental_watermark.py` | 114  | S02-01                     |
| `tests/test_fred_macro_incremental_port.py`      | 118  | S02-02                     |
| `tests/test_fred_macro_incremental_e2e.py`       | 181  | S02-03/04                  |
| `tests/test_fred_macro_incremental_cli.py`       | 92   | S02-05                     |
| `tests/fred_macro_incremental_support.py`        | 10   | 测试 helper                |

**新依赖：** 无（`urllib` / `duckdb` / 现有 sync 栈复用）。

### 独立读码 — ponytail 梯级摘要

| 区域                                                    | 最深梯级                           | 判定                                                                                                              |
| ------------------------------------------------------- | ---------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `fred_port.py` `_resolve_observation_start` + mock 过滤 | 2（复用 `MAX_WINDOW_DAYS`）        | AC 必需；+37 行合理；`ponytail:` 在 live legacy mock                                                              |
| `fred_incremental_watermark.py`                         | 2（本地 ops，待轨 A macro API）    | 模块头 + 升级路径注释                                                                                             |
| `fred_incremental_run.py` runtime patch                 | 6（DEBT 禁写 `sync/*` 后最小绕行） | `_macro_incremental_validation_patch` / `_fred_staging_adapter_patch` 有 `ponytail:`                              |
| `macro_staging_rows_from_bundle`                        | 6                                  | 输入为 `official_macro_evidence_v1` bundle，与 `observation_mapper.MicroFetchResult` 路径不同；硬复用会拉更多依赖 |
| `enabled_fred_source_registry`                          | 6                                  | registry yaml 本轨 forbidden；runtime enable 为协调约束下最简                                                     |
| CLI `_sync_fred_macro_incremental`                      | 2                                  | guard 形态对齐 `live_fetch`；非新框架                                                                             |
| 测试 duplicate setup                                    | 2                                  | **可合并**（见 findings）                                                                                         |

### 维度证据 §3.2 — 候选删改

| 候选删改（file:line）                                                                         | ponytail 梯级                               | 备注                                                                          |
| --------------------------------------------------------------------------------------------- | ------------------------------------------- | ----------------------------------------------------------------------------- |
| `fred_incremental_run.py:313-318` 循环内重复 `build_fred_incremental_service`                 | 2（loop 外单例 proxy）                      | `since_map` 静态；`FredIncrementalFetchProxy.fetch` 已按 `instrument_id` 查表 |
| `data_commands.py:72-93` dry-run fred 路由预览内联                                            | 2（薄 preview helper 或复用 registry 装配） | 与 `build_fred_incremental_service` 重复 registry/caps/planner ~22 行         |
| `test_fred_macro_incremental_watermark.py:19-54` + `test_fred_macro_incremental_e2e.py:34-63` | 2（并入 support）                           | 各 ~35 行 AXIS_OBSERVATION DDL 组装相同                                       |
| `tests/fred_macro_incremental_support.py:8-9`                                                 | 2                                           | 单消费者 re-export，无第二语义                                                |
| `test_fred_macro_incremental_e2e.py:76-97,113-131,157-176`                                    | 2（pytest fixture）                         | 三段 ~20 行相同 monkeypatch + bootstrap                                       |

**不算候选（AC / 协调约束）：**

- `_macro_incremental_validation_patch` / `_fred_staging_adapter_patch`（DEBT 禁写 `runners.py` / `orchestrator.py`）
- `enabled_fred_source_registry` 生产侧 monkeypatch（registry yaml forbidden）
- `macro_staging_rows_from_bundle` 独立实现（证据形态与 `observation_mapper` 不同）

### A2 checklist

- [x] `git diff --stat` 已记录 Lxx / net lines
- [x] 每候选附 `file:line` + ponytail 梯级
- [x] 与 A4 交叉：runtime patch 内 `emit_custom_event` + validate 包装可能与 A4 重复样板（本维仅记候选，不重复开 P1）
- [x] 阻塞 vs 建议已区分（P2/P3；无 P0/P1 级生产 bloat）

### DOUBT

≥1 处 ≥20 行可简化：**是** — 测试 duplicate `_insert_observation`（~70 行合计）、dry-run 路由装配重复（~22 行）、loop 内 service 重建（每次 ~15 行装配 × N series）。

**搜索范围：** `backend/app/ops/fred_*` · `backend/app/cli/data_commands.py` L59-238 · `backend/app/datasources/fetch_ports/fred_port.py` · `tests/test_fred_macro_incremental_*` · `tests/fred_macro_incremental_support.py` · `backend/app/layer1_axes/observation_mapper.py`（证据形态不同，不宜硬复用）· `tests/service_path_support.py`（已有 enable_source_route，无 fred incremental 专用 helper）。

### 定向 pytest（A2 引用 findings 验证命令）

```text
uv run pytest tests/test_fred_macro_incremental_watermark.py \
  tests/test_fred_macro_incremental_port.py \
  tests/test_fred_macro_incremental_e2e.py \
  tests/test_fred_macro_incremental_cli.py -q
→ 13 passed, 1 skipped (live_smoke 无 FRED_API_KEY)
```

---

## §维度裁决

**FAIL**

（§计划内 + §计划外 findings 表均有非占位行；按 `audit-finding-schema.md` 须 FAIL。）

---

## 计划内问题

| ID        | P   | 标题                                      | 锚点                                                                                          | 根因                                                                                                                                                                                               | 修复方案                                                                                                                       | 验证                                                                                                                   |
| --------- | --- | ----------------------------------------- | --------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| A2-P2-001 | P2  | 循环内重复构建 incremental service        | `fred_incremental_run.py:296-318`                                                             | `run_fred_macro_incremental` 每 series 调用 `build_fred_incremental_service`，但 `since_map` / `fetch_port` / `job_events` 在循环内不变；`FredIncrementalFetchProxy` 已按 `instrument_id` 查 since | 将 `build_fred_incremental_service(...)` hoist 到 `for` 前一次；循环内仅 `orch.run_incremental(..., datasource_service=proxy)` | `uv run pytest tests/test_fred_macro_incremental_e2e.py -q`；读码确认 loop 内无第二次 `build_fred_incremental_service` |
| A2-P2-002 | P2  | 测试 duplicate `_insert_observation` 膨胀 | `test_fred_macro_incremental_watermark.py:19-54` · `test_fred_macro_incremental_e2e.py:34-63` | 两处独立复制 AXIS_OBSERVATION 行组装（~35 行×2）                                                                                                                                                   | 合并为 `fred_macro_incremental_support.insert_axis_observation(...)`；两测 import 复用                                         | `uv run pytest tests/test_fred_macro_incremental_watermark.py tests/test_fred_macro_incremental_e2e.py -q`             |
| A2-P2-003 | P2  | dry-run fred 路由预览内联重复装配         | `data_commands.py:72-93`                                                                      | `sync_plan` dry-run 分支手写 registry/caps/planner/`_platform_allows`，与 `build_fred_incremental_service` 逻辑重复                                                                                | 提取 `_fred_incremental_preview_service()` 或 dry-run 复用 registry 装配 helper（仅 preview，不写库）                          | `uv run pytest tests/test_fred_macro_incremental_cli.py -q -k dryRun`                                                  |

---

## 计划外发现

| ID        | P   | 标题                           | 锚点                                                       | 根因                                                                          | 修复方案                                                                                                 | 验证                                                                        |
| --------- | --- | ------------------------------ | ---------------------------------------------------------- | ----------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| A2-P3-001 | P3  | 单消费者测试 re-export wrapper | `tests/fred_macro_incremental_support.py:8-9`              | `enabled_fred_registry()` 仅包装 `enabled_fred_source_registry()`，无第二语义 | e2e 直接 import ops；删 wrapper 或扩展 support 承接 P2-002 合并 helper                                   | `rg enabled_fred_registry` 无命中或 support 含共享 insert/fixture           |
| A2-P3-002 | P3  | e2e 三段相同 bootstrap 块      | `test_fred_macro_incremental_e2e.py:76-97,113-131,157-176` | 三测重复 monkeypatch + `_bootstrap_db` + service 构建（各 ~20 行）            | `@pytest.fixture` `fred_incremental_e2e_ctx(tmp_path, monkeypatch)` 返回 `(cm, orch, service, registry)` | 读码单 fixture；`uv run pytest tests/test_fred_macro_incremental_e2e.py -q` |

已对抗搜索：`observation_mapper` 复用路径（证据形态不同）· `service_path_support.enable_source_route`（无 incremental 专用 helper）· baostock incremental ops 先例（worktree 无对应轨 B 实现）· 新 pip/uv 依赖（无）· `test_catalog.yaml`（已 revert，非本 diff）· 除上表外未发现额外 ≥20 行可删的生产路径。

---

## A2 关账 checklist

- [x] ponytail-review 覆盖 `fred_port` · `fred_incremental*` · CLI 切片
- [x] 无新依赖
- [x] 协调强制 runtime patch 均有 `ponytail:` 注释与升级路径
- [ ] 最简 diff — **未满足**（上表 P2/P3 候选未收敛）
