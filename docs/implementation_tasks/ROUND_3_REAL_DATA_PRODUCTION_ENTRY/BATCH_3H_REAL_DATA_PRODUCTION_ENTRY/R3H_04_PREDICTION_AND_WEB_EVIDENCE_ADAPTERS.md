# R3H-04 — Prediction and Web Evidence Adapters

## 1. Goal

Close every prediction-market and web-evidence source before Round4. These sources are not factual primary sources and must not write clean factual tables.

Required source coverage:

```text
kalshi
polymarket
web_search
```

Each listed source must end as executable evidence/probability path or `ADR_DISABLED_OUT_OF_SCOPE`.

### 1.1 Plan architecture decisions（2a brainstorm + 3 grill-me · 已内联）

| 选项 | 结论 |
| --- | --- |
| A. 单文件 `prediction_adapter.py` 藏三源 | **否决** — 违反 per-source auth/cap/evidence |
| B. kalshi + polymarket 共用 `probability_signal` | **采纳** |
| C. web_search 复用 macro evidence normalizer | **否决** — 输出类型不同（manual_review） |
| D. 新建 `manual_review_staging` 模块 | **采纳** — 与 layer5 对齐 |
| E. mock/replay-first READY | **采纳** — 对齐 R3H-01/02；live 须用户 gate |
| F. 预测价格写入 clean 表 | **否决** — hardening §4 |
| G. 拷贝 OpenBB agent 运行时 | **否决** — 仅 artifact 形状参考 |

| grill 锁定项 | 决定 |
| --- | --- |
| 三源终态 | `READY_WITH_EVIDENCE` **或** `ADR_DISABLED_OUT_OF_SCOPE` |
| 主库 | **禁止**写 `quant_monitor.duckdb` |
| 预测市场 | 输出 `probability_signal` / `event_contract`；**禁止** `factual_resolution` 字段 |
| web_search | `need_human_review=true` + `manual_review_state=queued` |
| registry 并行 | 只改 `kalshi`/`polymarket`/`web_search` 行；**禁止**碰 CN market 源（R3H-03 拥有） |
| R3H-05 | **禁止**提前做全层审计 |

### 1.2 ADR 收窄策略（grill-me · 已内联）

| 源 | ADR 允许？ | 说明 |
| --- | --- | --- |
| `kalshi` | 候选 | 默认须 mock/replay READY；仅 API/terms 真受阻时 ADR |
| `polymarket` | 候选 | 同上 |
| `web_search` | 候选 | 若无可接受搜索后端且用户拒绝 mock；默认 mock stub READY |

### 2.8 Plan vs Execute gates

1. **No main DB writes** — sandbox/replay/`.audit-sandbox` only；禁止写 `data/duckdb/quant_monitor.duckdb`。
2. **mock-first READY** — kalshi/polymarket/web_search 默认 replay/mock；live API 须用户显式 gate + API key。
3. **web_search 默认 mock stub** — Grill-me #1 未决不阻塞 mock 路径。
4. **Coordinator review** — 共享 registry/capability/route 变更须 `execute-evidence/9.5-manifest.md` 只列三源行；**禁止**改 R3H-03 CN 源（`baostock`、`akshare`、`cninfo`、`tdx_pytdx`、`mootdx`、`eastmoney`、`sina_finance`、`ths_ifind`、`qmt_xtdata`、`qmt_xqshare`）及其 port。
5. **resource_guard.py 禁止修改** — 端口内 `reject_over_cap`；本轨 BRANCH 未授权扩 shared profile。
6. **R3H-05 forbidden** — Layer 工作限于 §9.7 smoke。

---

## 2. QMD files to read

```text
PROJECT_IMPLEMENTATION_ROADMAP.md
MODULE_COMPLETION_RATING.md
docs/modules/data_sources.md
docs/modules/source_route_plan.md
specs/datasource_registry/source_registry.yaml
specs/datasource_registry/source_capabilities.yaml
specs/contracts/source_capability_contract.yaml
specs/contracts/source_route_contract.yaml
specs/contracts/datasource_service_contract.yaml
specs/contracts/layer5_evidence_contract.yaml
specs/contracts/user_input_privacy_contract.yaml
specs/verification/contract_coverage.yaml
tests/test_source_registry.py
tests/test_source_capabilities.py
tests/test_source_route_planner.py
tests/test_catalog.yaml
```

---

## 3. Reference project use

Use agents-for-openbb only as artifact-shape reference when formatting evidence summaries:

```text
参考项目/agents-for-openbb/30-vanilla-agent-raw-widget-data/vanilla_agent_raw_context/main.py
参考项目/agents-for-openbb/40-vanilla-agent-dashboard-widgets/vanilla_agent_dashboard_widgets/main.py
```

Allowed ideas:

- separating source data from generated summary;
- presenting bounded table/dashboard artifact shape;
- not piling unlimited context.

Forbidden:

- copying OpenAI/client loop runtime;
- using Agent output as fact source;
- web search clean write;
- resolving factual event outcomes from prediction prices;
- bypassing manual review.

---

## 4. Target QMD files

Implement or update QMD-owned files such as:

```text
backend/app/datasources/fetch_ports/kalshi_port.py
backend/app/datasources/fetch_ports/polymarket_port.py
backend/app/datasources/fetch_ports/web_search_evidence_port.py
backend/app/datasources/normalizers/probability_signal.py
backend/app/evidence/manual_review_staging.py
specs/datasource_registry/source_registry.yaml
specs/datasource_registry/source_capabilities.yaml
specs/contracts/source_route_contract.yaml
specs/contracts/source_capability_contract.yaml
specs/contracts/layer5_evidence_contract.yaml
specs/verification/contract_coverage.yaml
tests/test_prediction_market_adapters.py
tests/test_web_evidence_adapter.py
tests/test_source_route_planner.py
tests/test_no_clean_write_for_web_evidence.py
tests/fixtures/replay/prediction_market/**
tests/fixtures/replay/web_evidence/**
```

**禁止修改：** `backend/app/core/resource_guard.py`（只读参照 `reject_over_cap` 模式；cap 在 port 内实现）。

### 4.1 Data flow and impact targets（Plan 1b）

```text
FetchRequest → kalshi_port / polymarket_port / web_search_evidence_port (mock/replay default)
  → probability_signal.py (kalshi/polymarket) / web evidence bundle (web_search)
  → manual_review_staging.py (web_search only)
  → route_planner evidence-only route
  → Layer5 foundation (need_human_review for web)
```

**GitNexus impact before edit（Execute 每步前 `impact()`）：**

| 符号 / 模块 | 风险 | 触发 Step |
| --- | --- | --- |
| `DataSourceService.fetch` | MEDIUM | 9.2–9.4 |
| `route_planner` / `capability_registry` | MEDIUM | 9.5 |
| `EvidenceFoundationValidator` | LOW | 9.7 |
| `source_registry.yaml`（三行） | MEDIUM | 9.5 |
| `evidence_bundle.finalize_bundle` | LOW | 9.1 |

### 4.2 Baseline state（Plan 1a）

| 维度 | 当前 |
| --- | --- |
| 三 fetch port | **不存在** |
| `probability_signal.py` | **不存在** |
| `manual_review_staging.py` | **不存在** |
| registry 三源 | `proposed_disabled_source` |
| replay fixtures | **不存在** `prediction_market/**`、`web_evidence/**` |

**并行冲突面：** 与 R3H-03 **无 adapter 文件重叠**；共享 registry 文件只改三源行。

### 4.3 GitNexus Execute boot（Plan 1b）

- 改码前：`impact()` 锚定 `DataSourceService.fetch`、`route_planner`、`capability_registry`。
- **风险预判：** 新模块为主 + 共享 registry 切片 = **MEDIUM**；须 coordinator manifest。

---

## 5. Required implementation per source

For each source, implement:

1. adapter/fetch port with explicit source_id;
2. auth/license/terms decision;
3. ResourceGuard caps for query count, markets/events, rows, and time window;
4. route planner READY/evidence-only tests and clean-write negative tests;
5. replay fixture or sandbox sample;
6. fetch_log/content_hash/schema_hash/source_fetch_id evidence;
7. output type: `probability_signal`, `event_contract`, `supplemental_web_evidence`, or `manual_review_evidence`;
8. Layer5/manual-review binding, not clean factual table binding.

Minimum domain expectations:

| Source       | Expected role                                             |
| ------------ | --------------------------------------------------------- |
| `kalshi`     | regulated event contract / probability signal             |
| `polymarket` | prediction-market probability / event contract validation |
| `web_search` | supplemental evidence/manual review only                  |

### 5.1 Contract schema and spec→test map（Plan 2b · 已内联）

**新增 schema：**

1. `probability_signal_evidence_v1` — kalshi/polymarket bundle
2. `web_evidence_staging_v1` — web_search bundle + staging metadata

**共有必填：** `source_fetch_id`, `content_hash`, `schema_hash`, `schema_version`, `fetch_log`, `source_id`, `retrieved_at`

**probability 专有：** `market_ticker`/`market_slug`, `yes_bid`, `yes_ask`, `probability`, `volume`, `liquidity`；polymarket 还须 `spread`, `resolution_source`（URL 元数据占位，**非事实判定**）

**web 专有：** `query`, `results[]`, `need_human_review=true`, `manual_review_state=queued`

**禁止字段（Red Flag）：** `resolved_outcome`, `fact_confirmed`, `clean_write_target`, `factual_resolution`

| 契约 / AC | 测试锚点 |
| --- | --- |
| probability evidence fields | `-k evidence_contract` |
| kalshi port + route | `-k kalshi` |
| polymarket port + liquidity/spread | `-k polymarket` |
| web manual_review staging | `test_web_evidence_adapter` |
| 三源 clean-write 负例 | `test_no_clean_write_for_web_evidence` |
| 预测不 resolve 事实 | 同上 `-k resolve` |
| 三源 registry/route | §9.5 + `9.5-manifest.md` |
| Layer5 manual_review | `-k layer` |

---

## 6. Done criteria

- Every listed source has executable evidence/probability path or ADR-disabled status.
- No listed source writes clean factual tables.
- Prediction markets cannot resolve factual outcomes.
- Web evidence always remains manual-review/evidence-staging only.
- Tests and contract coverage are updated.

---

## 7. Resource caps（Plan · ponytail 默认）

| 源 | cap 维度 | 默认上限 | 说明 |
| --- | --- | --- | --- |
| `kalshi` | `max_markets` / `max_window_days` | 5 / 30 | 监管事件合约概率；禁止全市场扫描 |
| `polymarket` | `max_markets` / `max_window_days` | 5 / 30 | 须记录 liquidity/volume/spread |
| `web_search` | `max_queries` / `max_results` | 3 / 10 | 仅 evidence staging；每次查询硬 cap |

端口内 `reject_over_cap` + replay fixture；**不**改 `resource_guard.py`（本轨 BRANCH 边界）。

---

## 8. Plan architecture decisions

> 已内联 **§1.1–§1.2、§2.8**；Execute 以 frozen 内联章节为准。

---

## 9. 实现步骤（垂直切片 · Plan 3.5）

| Step | 切片 | 交付物 |
| --- | --- | --- |
| 9.0 | boot_test_skeleton | 三测试模块空壳 + import 绿 |
| 9.1 | probability_evidence_contract | `probability_signal.py` + evidence v1 契约测 |
| 9.2 | kalshi_port | `kalshi_port.py` + replay + route |
| 9.3 | polymarket_port | `polymarket_port.py` + replay + route |
| 9.4 | web_search_evidence | `web_search_evidence_port.py` + `manual_review_staging.py` |
| 9.5 | registry_coordinator | 三源 registry/capability/route + manifest |
| 9.6 | clean_write_negative | `test_no_clean_write_for_web_evidence.py` |
| 9.7 | layer5_smoke | L5 manual-review 绑定 smoke |
| 9.8 | merge_gate | 全库 pytest + loop_maintain |

**依赖：** 9.1 阻塞 9.2–9.4/9.7；9.2–9.4 可并行（9.1 后）；9.5 须 9.2–9.4 + coordinator manifest；9.6 须 9.5（route 已注册后再跑 clean-write 负例）；9.7 须 9.4；9.8 最后。

**单步 TDD 边界：** 每步 RED 仅引入本步 `-k` 过滤的新测；9.5 RED 仅 registry/capability/route 三源增量；9.6 RED 仅 clean-write/resolve 负例。

---

## 10. 测试要求

| 文件 | 目的 |
| --- | --- |
| `tests/test_prediction_market_adapters.py` | kalshi/polymarket port、probability normalizer、route |
| `tests/test_web_evidence_adapter.py` | web_search port、manual_review staging |
| `tests/test_no_clean_write_for_web_evidence.py` | 三源 clean-write 负例 + 预测市场不得 resolve 事实 |
| `tests/test_source_route_planner.py` | 三源 evidence-only route（本轨增量用例） |
| `tests/test_source_capabilities.py` | 三源 capability 终态 |

### 10.1 三源负例与 manual-review 最低用例（§9.6 必覆盖）

| 源 | 负例 / 断言 |
| --- | --- |
| `kalshi` | route 不得选 clean-table writer；bundle 无 `factual_resolution`/`resolved_outcome` |
| `polymarket` | 同上 + `resolution_source` 仅为 URL 元数据（非 `resolved=true`） |
| `web_search` | route evidence-only；`need_human_review=true`；staging 不得 promote 到 clean 表 |
| 三源共用 | `-k resolve`：预测市场 port 输出不得 resolve 事实事件结果 |

### 10.2 Adversarial 攻击面闭包（Plan 5d · 已内联）

1. web_search 路由误选 clean writer → §9.6 负例 + `source_route_contract`
2. 预测价格升格为事实 → §5.1 禁止字段 + `-k resolve`
3. registry 并行覆盖 CN 源 → §9.5 manifest 白名单三源 + §2.8 gate #4
4. OpenBB runtime 混入 → Red Flag + A3 rg 禁止 import

---

## 11. 验收命令

```bash
uv run pytest tests/test_prediction_market_adapters.py tests/test_web_evidence_adapter.py tests/test_no_clean_write_for_web_evidence.py -q
uv run pytest tests/test_source_route_planner.py tests/test_source_capabilities.py -q -k "kalshi or polymarket or web_search"
uv run pytest -q
uv run python scripts/loop_maintain.py
```

---

## 12. 完成标准

- 三源 registry `READY_WITH_EVIDENCE` 或 ADR + route 可解释 DISABLED。
- replay fixture 存在于 `tests/fixtures/replay/prediction_market/**` 与 `web_evidence/**`。
- `test_r3h_source_final_decisions.py` 三源段通过。

---

## 13. Red Flags

- 预测价格字段命名为 `resolved_outcome` / `fact` / `confirmed`
- web_search 路由选中 clean-table writer
- 修改 R3H-03 拥有的 CN market port/registry 行
- 运行时 import `参考项目/agents-for-openbb/**` 的 OpenAI client

---

## 14. Reference project（重申）

仅借鉴 bounded table/dashboard artifact 形状；禁止 agent loop 与 fact 升格。

---

## 15. Execute Skill 冻结

| Skill | 本任务 | 绑定 Step |
| --- | --- | --- |
| test-driven-development | 必做 | 每 §9.x |
| karpathy-guidelines | 必做 | 每步 |
| testing-guidelines | 必做 | 每步 |
| ponytail | 必做 | 每步 |
| gitnexus-impact-analysis | 必做 | 改符号前 |
| incremental-implementation | 必做 | 每 GREEN 后 |
