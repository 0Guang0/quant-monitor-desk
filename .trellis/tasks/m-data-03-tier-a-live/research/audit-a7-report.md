# Audit A7 — Ops（M-DATA-03 Plan R2）

## 元信息

| 字段                    | 值                                                            |
| ----------------------- | ------------------------------------------------------------- |
| 维度                    | A7 — audit-ops                                                |
| 任务                    | `.trellis/tasks/m-data-03-tier-a-live`                        |
| `plan_protocol_version` | 4.1                                                           |
| 模板                    | `agents/database-administrator.md` · `agents/sre-engineer.md` |
| 审计日期                | 2026-07-03                                                    |
| 分支                    | `feature/m-data-03-tier-a-live`                               |

## 维度证据 §3.7

**AUDIT.plan §2 A7 焦点：** dispatch 去重 · mootdx 入 `platform_source_matrix` · 零主库污染 · isolated `data_root`

### 追溯权威

| 来源    | 锚点                                                                                |
| ------- | ----------------------------------------------------------------------------------- |
| 用户 AC | `research/plan-revision-r2.md` §2 AC#6（dispatch 重构 + mootdx matrix + 无 bypass） |
| 切片 AC | `research/to-issues-slices.md` S-R2-DISPATCH                                        |
| 规格    | `specs/contracts/platform_source_matrix.yaml` · ADR-034 隔离                        |

### Checklist（代码 + 跑测，非文档自述）

| #   | 检查项                                                            | 裁决 | 证据                                                                                                                                                |
| --- | ----------------------------------------------------------------- | ---- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **dispatch 去重**：无 `_live_sync_registry` 平行轨                | PASS | 全仓 `*.py` grep 零命中；`test_dispatchModule_hasNoParallelLiveSyncRegistry` 绿                                                                     |
| 2   | **金路径 SSOT**：11 源经 `resolve_tier_a_incremental`             | PASS | `_live_sync_runner_for` L359–563；`test_liveSyncRunnerFor_coversAllTierASources` 绿                                                                 |
| 3   | **mootdx matrix**：三平台 `default_enabled: true`                 | PASS | `platform_source_matrix.yaml` L24–26 / L61–63 / L98–100；`test_platformMatrix_includesMootdxOnCurrentPlatform` 绿                                   |
| 4   | **mootdx 路由无 bypass**：bar live 走真实 `SourceRoutePlanner`    | PASS | `_bar_live_route_planner` L120–130 无 `_platform_allows` 覆写；`test_barLiveRoutePlanner_selectsMootdxPrimary` → `selected_source_id==mootdx`       |
| 5   | **isolated data_root**：仅 `.audit-sandbox/m-data-03`             | PASS | `assert_isolated_live_data_root` L86–100；`test_assertIsolatedLiveDataRoot_rejectsCanonicalMainDb` · `rejectsNonMdata03Sandbox` 绿                  |
| 6   | **dispatch 入口隔离闸**：`run_tier_a_live_incremental` 绑定隔离根 | PASS | `_bind_live_data_root` L48–53 → `assert_isolated_live_data_root` + `QMD_DATA_ROOT` env；R1 A7-P2-002 已闭合                                         |
| 7   | **fred 路径不分裂**：sync/inspect 同根                            | PASS | `_sync_fred_live` L271 `_prepare_sandbox(data_root)`；`test_runTierALiveIncremental_dataRootSplit_inspectUsesParamNotEnv` 绿（R1 A7-P1-001 已闭合） |
| 8   | **零主库污染**                                                    | PASS | `test_tierALiveOps_mainDbFingerprintUnchangedAfterSandbox` · `AfterMockAcceptance` 绿（主库存在时 size/mtime_ns 不变）                              |
| 9   | **ResourceGuard**                                                 | PASS | `_assert_resource_guard_ok` L42–45；dispatch 入口 L601 调用                                                                                         |
| 10  | **CI isolated sandbox**                                           | PASS | `.github/workflows/tier-a-live.yml` L38 `DATA_ROOT=".audit-sandbox/m-data-03/${RUN_ID}"`；失败 artifact L46–54                                      |
| 11  | **fixture 契约**                                                  | PASS | `conftest.py` `isolated_live_data_root` → `.audit-sandbox/m-data-03/pytest-*` + env 绑定                                                            |

### GitNexus

| 操作                                                                | 结果                                                                                                                                  |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `query(tier_a_live_incremental_dispatch …)` repo=quant-monitor-desk | 返回 live_pilot / platform_matrix 邻域；未直接命中 dispatch 进程（索引滞后）                                                          |
| `context(run_tier_a_live_incremental)`                              | Symbol not found（索引 stale，与 `gitnexus-audit-summary.md` 一致）                                                                   |
| 人工锚点                                                            | `tier_a_live_incremental_dispatch.py` · `tier_a_live_acceptance.py:assert_isolated_live_data_root` · `incremental_source_registry.py` |

### 独立复验命令

```bash
uv run pytest tests/test_tier_a_live_dispatch.py tests/test_tier_a_live_harness.py tests/test_platform_source_matrix.py -q
```

**结果：** exit 0（47 passed, 2 skipped — network 标记与 canonical main DB 缺席 skip）

### 关键代码锚点

| 符号                             | 文件                                      | 角色                                                       |
| -------------------------------- | ----------------------------------------- | ---------------------------------------------------------- |
| `run_tier_a_live_incremental`    | `tier_a_live_incremental_dispatch.py:598` | dispatch 入口；隔离闸 + ResourceGuard                      |
| `_bind_live_data_root`           | 同上 `:48`                                | ADR-034 隔离 env 绑定                                      |
| `_live_sync_runner_for`          | 同上 `:359`                               | DCP-05 金路径；baostock/mootdx bar + 9 macro/port 源       |
| `_bar_live_route_planner`        | 同上 `:120`                               | mootdx/baostock 矩阵路由（无 `_platform_allows` ponytail） |
| `assert_isolated_live_data_root` | `tier_a_live_acceptance.py:86`            | 拒绝 canonical main DB；强制 m-data-03 段                  |
| `resolve_tier_a_incremental`     | `incremental_source_registry.py:49`       | 11 源 SSOT registry                                        |

## §维度裁决

**PASS**

## 计划内问题

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| —   | —   | 无   | —    | —    | —        | —    |

## 计划外发现

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| —   | —   | 无   | —    | —    | —        | —    |

已对抗搜索：`DATA_ROOT` env/param 分裂路径 · `_live_sync_registry` 全仓 grep · `_platform_allows` bypass 在 bar/mootdx dispatch 路径 · dispatch 直调非 m-data-03 根 · CI workflow secrets/sandbox 路径 · 主库 stat 指纹 · macro `load_incremental_route_bundle` 内 `_platform_allows` ponytail（仅 macro incremental 通用路径，非 mootdx bar live；不在 A7 §2 焦点范围内）。
