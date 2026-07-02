# M-DATA-03 Technical Spec

## Objective

Deliver **live-network** incremental sync → clean → inspect for all 11 Tier A sources in an **isolated DuckDB sandbox**, honest R4 module rating for C3/D1/E1/E2/F0/B2.

## ASSUMPTIONS

1. All 11 sources can reach the public internet from dev/CI runner when keys are set (roadmap §0.3.4).
2. `FRED_API_KEY`, `ALPHA_VANTAGE_API_KEY`, and other env slots are provided for acceptance runs.
3. DCP-05 replay logic is correct; this ticket only changes **live acceptance path**, not orchestrator contracts.
4. No new schema migrations (015 is SSOT).
5. **借鉴三等级仅评 `参考项目/**`；仓内 DCP-05 代码 = 直接复用，禁止标 L1/L2/L3**（见 `reference-adoption-m-data-03.md` §0·§4）。

## Tech Stack

- Python 3.11+ · uv · pytest
- DuckDB isolated via `DATA_ROOT` / `.audit-sandbox`
- Existing: `DataSourceService`, `DataSyncOrchestrator`, `product_live_gate`

## Interface Contract（边界 API · 须稳定）

### `product_live_gate`（已有 · ADR-027）

| 函数                                                | 输入                       | 成功   | 失败                                                |
| --------------------------------------------------- | -------------------------- | ------ | --------------------------------------------------- |
| `is_product_live_fetch_allowed()`                   | env `QMD_ALLOW_LIVE_FETCH` | `True` | `False`                                             |
| `assert_product_live_allowed(source_id, operation)` | `source_id: str`           | 无返回 | `ProductLiveGateError` · `code=LIVE_FETCH_REJECTED` |
| `gate_live_fetch_port(source_id, operation)`        | 同上                       | 无返回 | `LIVE_FETCH_REJECTED` 或 `RESOURCE_GUARD_PAUSED`    |

**边界规则：** live port 入口 **必须** 调 `gate_live_fetch_port`；禁止绕过直接 HTTP。

### `run_*_incremental` ops runners（仓内 · 直接复用签名）

| 参数             | 语义                                 | live 本票                              |
| ---------------- | ------------------------------------ | -------------------------------------- |
| `use_mock: bool` | `True`=replay/fixture · `False`=live | live 切片强制 `False`                  |
| `service`        | `DataSourceService` 实例             | 必须 `build_product_live_service(...)` |
| 返回             | report / dict 含 `status`            | `COMPLETED` 为成功；其余 fail-closed   |

**禁止：** 为 live 新增平行 `fetch()` 旁路。

### `scripts/tier_a_live_acceptance.py`（S00-INFRA 新建 · 契约）

```text
tier_a_live_acceptance.py [--source-id ID] [--quick] [--data-root PATH]

退出码：
  0 — 请求范围内全部源 sync→clean→inspect(E2) 绿且 partial F0 非 FAIL（SKIP 可过）
  1 — 任一派发源失败、inspect P0 blocker（FAIL）或 partial F0 FAIL
  2 — 环境不合法（无 QMD_ALLOW_LIVE_FETCH / DATA_ROOT 指向主库 / 缺 KEY）

--source-id：可选；省略=11/11
--quick：试点子集（fred + baostock），供 CI nightly 分层
--data-root：必填或 env DATA_ROOT；必须 ≠ canonical main DB
```

**S-ACCEPT 每源链路（与 `tier_a_live_acceptance.py` / dispatch 一致）：**

1. `validate_live_acceptance_env` — env 闸 + 隔离 `DATA_ROOT` + per-source KEY 槽位
2. `run_tier_a_live_incremental` — live sync→clean（`use_mock=False`）+ `DbInspector.inspect()`（**E2 gate**）
3. `_run_f0_data_health` — **partial F0**（见下）；`FAIL` → exit 1
4. 汇总 pass：sync 绿 + inspect 非 `FAIL` + F0 非 `FAIL`（`SKIP` 可过）

**F0 data health（partial · S-ACCEPT scope）：**

S-ACCEPT **已接入** partial F0（`run_source_live_acceptance` → `_run_f0_data_health`），**不是**完整 `qmd data health --profile …` CLI 矩阵：

| 条件                                       | 行为                                                                                                                                                       |
| ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 有 latest raw evidence dir                 | bar 源：`run_data_health_profile(profile_id=market_bar_p0, …)`；其余：`DataHealthService().check_evidence_dir`（`fred_sandbox_pilot` / `staged_pilot_v3`） |
| 无 raw evidence（caught-up）               | 返回 **`SKIP`**（`no raw evidence; caught-up inspect-only gate`）；**不**阻断 acceptance                                                                   |
| health `FAIL` / `BLOCKED` / gate not ready | → source **fail**；CLI exit 1                                                                                                                              |

- **E2** `DbInspector.inspect()` 仍是 post-write schema/clean P0 blocker 主门
- **SKIP** 路径：sync + inspect 绿即可 pass；语义 = caught-up 无新 raw 时仅靠 sync/inspect 门
- 完整 `qmd data health --profile …` CLI 矩阵 → **ponytail** · M-PASS nightly（本票不承诺）

### Live pytest 约定

| 元素                              | 契约                                  |
| --------------------------------- | ------------------------------------- |
| `@pytest.mark.network`            | 真网；默认 `pytest -q` **skip**       |
| fixture `isolated_live_data_root` | S00-INFRA 提供；自动拒绝 main DB 路径 |
| 五字段 docstring                  | 每个 `test_*` 必填                    |

## Official API Sources（source-driven-development · RED 前必读）

| source_id     | 权威文档（实现前 fetch）                                                   |
| ------------- | -------------------------------------------------------------------------- |
| fred          | https://fred.stlouisfed.org/docs/api/fred/series_observations.html         |
| us_treasury   | https://fiscaldata.treasury.gov/api-documentation/                         |
| sec_edgar     | https://www.sec.gov/search-filings/edgar-application-programming-interface |
| cftc_cot      | https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm          |
| bis           | https://stats.bis.org/api-doc/v1                                           |
| world_bank    | https://datahelpdesk.worldbank.org/knowledgebase/articles/889392           |
| alpha_vantage | https://www.alphavantage.co/documentation/                                 |
| deribit       | https://docs.deribit.com/                                                  |
| baostock      | http://baostock.com/baostock/index.php/Python_API文档                      |
| cninfo        | 巨潮资讯公开接口（实现前读仓内 port 注释 + 官方说明）                      |
| mootdx        | pytdx / 通达信协议（仓内 `mootdx_port` + R3FR 归档）                       |

**SDD 规则：** 第三方响应 **不可信** — port 内 validate 形状后再写 staging。

## Commands

```bash
# Default CI (no network)
uv run pytest -q

# Live acceptance (isolated)
export QMD_ALLOW_LIVE_FETCH=1
export DATA_ROOT=.audit-sandbox/m-data-03
uv run pytest tests/test_fred_macro_incremental_e2e.py -m network -q
uv run python scripts/tier_a_live_acceptance.py --quick
uv run python scripts/tier_a_live_acceptance.py

uv run python scripts/loop_maintain.py
```

## Project Structure (touch surface)

```text
backend/app/datasources/fetch_ports/*_port.py    # live 路径（L3 绿场 / L2 改造）
backend/app/datasources/product_live_*.py        # 仓内直接复用
backend/app/ops/*_incremental_*.py               # use_mock=False
tests/test_*_incremental_e2e.py                  # + network marks
tests/test_tier_a_live_harness.py                # 含 silent-fallback 负向
scripts/tier_a_live_acceptance.py
tests/test_catalog.yaml                          # S-MERGE
```

## Testing Strategy

| Layer                       | Policy                                                                          |
| --------------------------- | ------------------------------------------------------------------------------- |
| Default `pytest -q`         | replay/mock 绿；`network` skipped                                               |
| `-m network`                | live 隔离 e2e；须 env + KEY                                                     |
| `tier_a_live_acceptance.py` | 运营 11/11 门禁                                                                 |
| Negative（S00-INFRA）       | 无 `QMD_ALLOW_LIVE_FETCH` fail-closed；`DATA_ROOT` 主库拒绝；无 silent fallback |

## Boundaries

- **In:** 11 Tier A live incremental clean + E2 inspect（S-ACCEPT）；F0 全 profile 见 ponytail 说明
- **Out:** Layer modeling, Round4, main DB, new DDL, Tier B/C cron

## Success Criteria

1. `tier-a-live-eligibility.md` 与 env 槽位一致
2. 每源：live e2e + SDD 引用 + 借鉴等级行可核对
3. `tier_a_live_acceptance.py` 11/11 exit 0
4. `uv run pytest -q` exit 0
5. Audit PASS；MCR → R4 live scope

## Open Questions

None blocking Plan freeze.
