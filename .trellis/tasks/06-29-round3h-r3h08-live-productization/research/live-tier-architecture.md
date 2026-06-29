# R3H-08 架构设计 — 产品 Live × Tier A/B/C

- **状态：** 调研后定稿（Plan 输入）
- **日期：** 2026-06-29
- **依据：** `reference-adoption-r3h08.md` · `R3H_PASS_EXECUTION_PLAN.md` §2 · R3H-10/07 CLOSED

---

## 1. 问题陈述

Wave 1 闭合 **C2 DataSourceService SSOT** 与 **CAL-US**，但 24 源仍停留在 **rehearsal**（`REHEARSAL_ONLY`）或 mock-opt-in。Wave 2 要在 **不破坏** R3H-10 金路径前提下，交付 **env-gated 产品 live**：Sync / CLI / 探针一律经 service，且每源写入 PASS 规定的 Tier A/B/C。

---

## 2. 架构总览

```text
                    ┌─────────────────────────────────────┐
  qmd data CLI ────►│                                     │
  DataSyncOrchestrator.run_* ──►│   DataSourceService (C2 SSOT)   │
                    │   preview_route / fetch             │
                    └──────────────┬──────────────────────┘
                                   │
                    ResourceGuard (env + budget)
                                   │
                    fetch_ports/* (per-source live opt-in)
                                   │
                    ┌──────────────┴──────────────┐
                    │   LiveTierRouter (新 · L3)   │
                    │   source_id → tier A|B|C     │
                    └──────────────┬──────────────┘
           ┌───────────────────────┼───────────────────────┐
           ▼                       ▼                       ▼
    Tier A clean/axis      Tier B pilot duckdb      Tier C probability/
    (approved promote      (validation_only         evidence domain
     path · R3G-03)         guard L166-180)          (kalshi/poly)
```

**刻意不做：**

- 不复用 `ops/live_pilot_phase3` / `staged_pilot` 作为产品入口（保持 `REHEARSAL_ONLY`）。
- 不引入 EasyXT 式 DuckDB→在线源 silent 回退。
- 不 runtime import `参考项目/**`。

---

## 3. 核心组件

### 3.1 ProductLiveGate（env-gated · 薄模块）

**职责：** 单一 fail-closed 开关链，供 CLI / Sync / 测试共用。

| 检查                                              | 失败行为                                 |
| ------------------------------------------------- | ---------------------------------------- |
| `QMD_ALLOW_LIVE_FETCH=1`（或等价 documented env） | `LIVE_FETCH_REJECTED`                    |
| `ResourceGuard` != HARD_STOP                      | blocked                                  |
| `source_id` 在 registry READY / env 授权          | `DISABLED_SOURCE` / `USER_AUTH_REQUIRED` |
| `staged_fixture_mode=False`                       | 拒绝 fixture service                     |
| rehearsal 入口未冒充 product                      | 契约测                                   |

**位置（拟）：** `backend/app/datasources/product_live_gate.py` — ponytail 单文件，Upgrade：拆 per-tier policy。

### 3.2 LiveTierRouter

**职责：** 将 `source_id` + registry `validation_only` / role 映射到 Tier A/B/C（SSOT = PASS §2.1 表）。

```python
# 概念 API（Plan 定稿，Execute 实现）
def resolve_live_tier(source_id: str, *, registry: SourceRegistry) -> Literal["A", "B", "C"]:
    ...
```

| Tier  | 写库目标                                                           | 守卫                                                             |
| ----- | ------------------------------------------------------------------ | ---------------------------------------------------------------- |
| **A** | clean 域表（`resolve_clean_write_target`）经 **批准 promote 路径** | R3G-03 approval + MAIN-DB-GATE；默认 isolated pilot DB           |
| **B** | `*r3g03_pilot*` / `.audit-sandbox` only                            | `limited_production_entry._assert_validation_source_isolated_db` |
| **C** | probability / evidence 表（现有 layer1 域）                        | env-gated · 无 clean promote                                     |

### 3.3 DataSourceService 接线（L1 复用）

产品 live fetch **不新造** service 子类；调用方构造：

```text
DataSourceService(
  fetch_port=create_<source>_fetch_port(..., live=True),  # 各 port 已有/扩展
  staged_fixture_mode=False,
  data_root=DATA_ROOT,
)
```

Sync 金路径（R3H-10 已闭合）：

```text
orchestrator.run_incremental(spec, datasource_service=service)
```

### 3.4 CLI 扩展（L3 最小）

`qmd data fetch --live`（或等价子命令）必须：

1. `ProductLiveGate.assert_allowed(source_id, domain, operation)`
2. `service.preview_route` → READY
3. `service.fetch` → raw paths
4. 可选 `--write-tier` 只读预览（默认 dry_run）

**不**在 CLI 内直连 `fetch_ports` bypass service。

---

## 4. 子轨架构（08C→08A→08B→08D）

| 子轨    | 源集合                                                                          | 架构焦点                                                                          |
| ------- | ------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| **08C** | fred, us_treasury, sec_edgar, cftc_cot, bis, world_bank, alpha_vantage, deribit | Tier A macro/market primary；启用 port live 分支；macro `axis_observation` 写路径 |
| **08A** | baostock, cninfo, mootdx                                                        | Tier A CN；`cn_equity_daily_bar` / disclosure 域；禁止 rehearsal port 冒充        |
| **08B** | yahoo, akshare, stooq, coingecko, eastmoney, sina, tdx, ths, qmt\_\*            | Tier B only；负向：拒绝写 canonical main                                          |
| **08D** | kalshi, polymarket                                                              | Tier C；概率 evidence；env-gated                                                  |

**横切 S08-05：** `run_reconcile(datasource_service=)` 金路径 + `interface_probe` 已 service 化复核（R3H-10 defer 关账）。

---

## 5. 测试策略（架构层）

| 层     | 证明什么                                                                        |
| ------ | ------------------------------------------------------------------------------- |
| 契约   | `test_production_live_pilot_policy` 扩展：产品路径 **不** 携带 `REHEARSAL_ONLY` |
| 负向   | validation_only 写 canonical main → RED                                         |
| 金路径 | `test_datasource_service` + `test_vendor_fetch_e2e` 经 service live mock/replay |
| Tier   | per-subtrack `test_r3h08_*` 五字段 tracer bullet                                |
| 回归   | 全量 `uv run pytest -q`                                                         |

---

## 6. ADR 需求

拟 **ADR-027**：Product live env gate + Tier router + rehearsal 硬边界（绑定 S08-BOOT / S08-05）。

---

## 7. 与参考项目的关系（摘要）

| 来源                  | 架构中的位置                                  |
| --------------------- | --------------------------------------------- |
| OpenBB Fetcher 三阶段 | port 内 extract/transform 组织方式（L3 自研） |
| digital-oracle        | kalshi/bis/poly HTTP 字段 L2 对照             |
| EasyXT                | **反模式清单**（fallback/scheduler）          |
| QMD R3H-10/R3G-03     | 金路径 + promote 链 L1                        |

---

## 8. 调研门禁通过

- [x] 三等级矩阵覆盖全部参考项目
- [x] 24 源逐源等级表
- [x] 组件边界与「刻意不做」
- [x] 子轨串行与横切 defer 承接
- [x] **Execute §7：RED 前必 Read 参考源码 · 禁止从零造**

**→ 可进入 Plan v4.1 正式流程（to-issues / 5a–5e）。**
