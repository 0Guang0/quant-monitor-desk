# Audit A4 — 代码质量 / live dispatch / e2e

| 字段                  | 值                                          |
| --------------------- | ------------------------------------------- |
| 维度                  | A4（audit-quality）                         |
| 任务                  | m-data-03-tier-a-live（M-DATA-03 全 scope） |
| plan_protocol_version | 4.1                                         |
| 日期                  | 2026-07-03                                  |
| 模板                  | `agents/code-reviewer.md`                   |

---

## 维度证据

### A4 对抗动作（`audit-adversarial-authority.md`）

- 已 Read：`agents/audit-boot-v4.1.md` · `agents/audit-finding-schema.md` · `agents/code-reviewer.md` · `AUDIT.plan.md` §2 A4 · `research/to-issues-slices.md` S-ACCEPT/S-LIVE-\* · ADR-028 · ADR-034 · `research/integration-audit.md`
- 已审核心实现：`backend/app/ops/tier_a_live_incremental_dispatch.py` · `tier_a_live_acceptance.py` · `deribit_port.py` · `scripts/tier_a_live_acceptance.py`
- 已 Glob/阅读 11 源 `tests/test_*incremental_e2e.py` + `*_incremental_support.py` 变更；`tests/test_tier_a_live_dispatch.py` · `tests/test_tier_a_live_harness.py`
- 已对照 ADR-028：`incremental_source_registry.py` · `clean_write_targets.py`（本票 diff 未改矩阵 SSOT）
- 验证基于代码/测试阅读；本维未独立 `pytest` 复跑（A5 职责）

### 11 源 live e2e 覆盖矩阵（`-m network`）

| source_id     | e2e 模块                                | live 用例数 | clean 表（ADR-028）       | 幂等 live | 隔离 fixture |
| ------------- | --------------------------------------- | ----------- | ------------------------- | --------- | ------------ |
| fred          | `test_fred_macro_incremental_e2e.py`    | 2           | `axis_observation`        | ✓         | ✓            |
| baostock      | `test_baostock_incremental_e2e.py`      | 2           | `security_bar_1d`         | ✓         | ✓            |
| mootdx        | `test_mootdx_incremental_e2e.py`        | 2           | `security_bar_1d`         | ✓         | ✓            |
| us_treasury   | `test_us_treasury_incremental_e2e.py`   | 2           | `axis_observation`        | ✓         | ✓            |
| bis           | `test_bis_incremental_e2e.py`           | 2           | `axis_observation`        | ✓         | ✓            |
| world_bank    | `test_world_bank_incremental_e2e.py`    | 2           | `axis_observation`        | ✓         | ✓            |
| cftc_cot      | `test_cftc_incremental_e2e.py`          | 2           | `axis_observation`        | ✓         | ✓            |
| sec_edgar     | `test_sec_edgar_incremental_e2e.py`     | 2           | `us_disclosure_clean`     | ✓         | ✓            |
| alpha_vantage | `test_alpha_vantage_incremental_e2e.py` | 2           | `security_bar_1d`         | ✓         | ✓            |
| deribit       | `test_deribit_incremental_e2e.py`       | 2           | `crypto_derivative_clean` | ✓         | ✓            |
| cninfo        | `test_cninfo_incremental_e2e.py`        | 2           | `cn_announcement_clean`   | ✓         | ✓            |

**结论：** 11/11 均有 `@pytest.mark.network` live 变体（各 2 用例：写 clean + 幂等）。默认 CI skip 由 `conftest.py` + `test_networkMark_skippedInDefaultPytestRun` 覆盖。

### ADR-028 clean 矩阵（本票须不变）

| 检查项                                     | 结果     | 证据                                                                                               |
| ------------------------------------------ | -------- | -------------------------------------------------------------------------------------------------- |
| `incremental_source_registry.py` 11 行矩阵 | **未改** | 与 ADR-028 L17–29 一致；`TIER_A_SOURCES` 漂移 guard L34–38                                         |
| `clean_write_targets.py` 域路由            | **未改** | BAR/MACRO/US_DISCLOSURE/CRYPTO 全集含 ADR §Decision-2 别名                                         |
| dispatch 路由                              | **对齐** | `run_tier_a_live_incremental` L447–448 `resolve_tier_a_incremental` → `resolve_clean_write_target` |
| 新 migration DDL                           | **无**   | 符合活卡 / ADR-034 §5                                                                              |

### live dispatch 架构审查

| 组件                      | 评估   | 要点                                                                                                                                   |
| ------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| **隔离**                  | 良     | `tier_a_live_acceptance.assert_isolated_live_data_root` 拒绝 canonical main DB；`ensure_isolated_db` → `quant_monitor.duckdb`          |
| **gate**                  | 良     | 各源分支调 `assert_product_live_allowed`；fred 经 `data_commands._sync_fred_macro_incremental` 二次 gate + `assert_sandbox_db_allowed` |
| **dispatch 正确性**       | **差** | deribit 硬编码 `BTC-PERPETUAL` 与 live port option API 语义冲突（见 A4-P1-01）                                                         |
| **S-ACCEPT 可测性**       | **差** | `run_tier_a_live_incremental` / `run_source_live_acceptance` 零网络/集成测（见 A4-P1-02）                                              |
| **e2e ↔ acceptance 同构** | **中** | live e2e 用 `*_live_incr.duckdb`；acceptance 用 `quant_monitor.duckdb`（见 A4-P2-03）                                                  |
| **错误处理**              | **中** | `run_source_live_acceptance` 宽 `except Exception`；`_clean_row_count` 吞异常（见 findings）                                           |
| **可读性**                | 中     | `_run_live_sync` 400+ 行 source 分支；baostock/mootdx 近重复；`_run_macro_live` 抽取合理                                               |

### §3.4 轴表

| 轴     | 发现                                                | 证据                                                                                                                  |
| ------ | --------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| 正确性 | deribit dispatch 仪器/水位不一致；S-ACCEPT 路径未测 | `tier_a_live_incremental_dispatch.py` L359–364 · `deribit_port.py` L134–177 · `deribit_incremental_support.py` L48–68 |
| 可读性 | 死代码重复 if                                       | `tier_a_live_incremental_dispatch.py` L454–459                                                                        |
| 架构   | e2e 与 acceptance DB 文件名分裂                     | `fred_macro_incremental_support.py` L92 · `tier_a_live_acceptance.py` L140                                            |
| 安全   | —                                                   | gate + 隔离路径 OK                                                                                                    |
| 性能   | —                                                   | 单源串行；验收规模可接受                                                                                              |

### 做得好的地方

- `tier_a_live_acceptance.py` 环境契约清晰（exit 0/1/2、KEY 槽位、`TierALiveEnvError.code`）
- `test_tier_a_live_harness.py` 负向测覆盖主库拒绝、无 opt-in、缺 KEY、默认 skip network
- `DeribitLiveFetchPort._book_summary_mark_iv` 补齐 `get_instruments` 缺 `mark_iv` 的 live 缺口
- `LiveIncrementalOutcome` + EMPTY_RESPONSE 归一化语义与 e2e caught-up 对齐

---

## §维度裁决

**FAIL**

（§计划内 + §计划外 共 8 条非占位 finding）

---

## 计划内问题

| ID       | P   | 标题                                                            | 锚点                                                                                                                                                      | 根因                                                                                                                                                                                               | 修复方案                                                                                                                                                                                                                             | 验证                                                                                                                                                                                                                   |
| -------- | --- | --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A4-P1-01 | P1  | deribit dispatch 硬编码 BTC-PERPETUAL 与 live option API 不匹配 | `tier_a_live_incremental_dispatch.py` L359–364 · `deribit_port.py` L134–177 · `deribit_incremental_support.py` L48–68                                     | dispatch 固定 `BTC-PERPETUAL` 读水位；`DeribitLiveFetchPort._live_instruments` 只拉 `kind=option`，找不到 perpetual 时 fallback `rows[0]`，与 e2e 的 `_resolve_deribit_live_instrument` 路径不一致 | dispatch 复用 support 的 live 探针选当前 option 名，或改 dispatch 与 e2e 共用 `bootstrap_deribit_live_e2e_ctx` 仪器解析；水位 `since_map` 与 `instruments` 须同一 instrument                                                         | `QMD_ALLOW_LIVE_FETCH=1 uv run pytest tests/test_deribit_incremental_e2e.py -m network -q`；`uv run python scripts/tier_a_live_acceptance.py --source-id deribit --data-root .audit-sandbox/m-data-03/audit-a4` exit 0 |
| A4-P1-02 | P1  | S-ACCEPT dispatch 层零集成/网络测试                             | `tests/test_tier_a_live_dispatch.py`（仅 `_extract_sync_status`/`passed`）· `tier_a_live_acceptance.py` L175–182 · `to-issues-slices.md` S-ACCEPT         | 11 源 live e2e 直调 `run_*_incremental`，不经过 `run_tier_a_live_incremental`；A4-P1-01 类缺陷 e2e 无法检出                                                                                        | 在 `test_tier_a_live_dispatch.py` 或 harness 增 `@pytest.mark.network` 用例：至少 `--quick`（fred+baostock）与 deribit 调 `run_source_live_acceptance`/`run_tier_a_live_incremental`，断言 `quant_monitor.duckdb` + ADR-028 clean 表 | `QMD_ALLOW_LIVE_FETCH=1 uv run pytest tests/test_tier_a_live_dispatch.py -m network -q`                                                                                                                                |
| A4-P2-01 | P2  | S-ACCEPT 未跑 data health（F0）                                 | `to-issues-slices.md` S-ACCEPT AC#5 · `tier_a_live_acceptance.py` L185–190 · `plan-spec.md` L48–50（exit 1 含 inspect P0）                                | 仅 `DbInspector.inspect()`；`l4-tier-a-live-accept-evidence.md` L30 口头 defer health，未绑 ponytail/任务 ID                                                                                       | 在 `run_source_live_acceptance` 调用现有 data health runner（或 `qmd data health` 等价 API），FAIL/P0 blocker → `status=fail`；或修订 `to-issues-slices.md` S-ACCEPT AC 并 ADR-034 ponytail 登记 nightly 关闭条件                    | `uv run pytest tests/test_tier_a_live_harness.py -q`；acceptance 单源跑后断言 health 无 P0                                                                                                                             |
| A4-P2-02 | P2  | `run_tier_a_live_incremental` 死代码重复 if                     | `tier_a_live_incremental_dispatch.py` L454–459                                                                                                            | 第一次 `COMPLETED`+0 行已归一化为 `EMPTY_RESPONSE`；第二次同条件永假                                                                                                                               | 删除 L458–459 或合并为单分支 detail 拼接                                                                                                                                                                                             | `uv run pytest tests/test_tier_a_live_dispatch.py -q`                                                                                                                                                                  |
| A4-P2-03 | P2  | live e2e 与 acceptance DuckDB 路径不同构                        | `fred_macro_incremental_support.py` L92 · `incremental_baostock_support.py` L24 · `deribit_incremental_support.py` L80 · `tier_a_live_acceptance.py` L140 | e2e 用 `*_live_incr.duckdb`；S-ACCEPT 用 `duckdb/quant_monitor.duckdb`；ops 金路径在 e2e 绿不等于 acceptance 绿                                                                                    | live e2e bootstrap 统一改用 `quant_monitor.duckdb`（与 `ensure_isolated_db` 一致），或增 dispatch 层 network 测（与 A4-P1-02 合并）                                                                                                  | 对比 e2e 与 `run_tier_a_live_incremental` 后同一 `db_path` 下 clean 行数一致                                                                                                                                           |

---

## 计划外发现

| ID       | P   | 标题                                         | 锚点                                                                             | 根因                                                                                         | 修复方案                                                                                                       | 验证                                                                     |
| -------- | --- | -------------------------------------------- | -------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| A4-P2-04 | P2  | `_clean_row_count` 静默吞异常                | `tier_a_live_incremental_dispatch.py` L432–440                                   | `except Exception: pass` 后 fallback 全表 COUNT，掩盖 `source_used` 列缺失/SQL 错误          | 收窄为 `duckdb.Error` 或记录 detail；列不存在时显式 fallback 并写 `detail`                                     | 单测：缺列 mock 连接断言 detail 含 warning 而非 silent pass              |
| A4-P2-05 | P2  | acceptance 在非 PASS sync_status 时仍可 pass | `tier_a_live_acceptance.py` L191–200                                             | `clean_row_count >= 1` 即 pass，可掩盖 `PARTIAL_FAILURE`/`FAILED` 残留行                     | 仅当 `sync_status in _PASS_SYNC_STATUSES` 或显式 `EMPTY_RESPONSE`+raw 证据（L206–216 路径）才 pass；否则 fail  | 单测：注入 `sync_status=FAILED` + `clean_row_count=1` 断言 `status=fail` |
| A4-P3-01 | P3  | ResourceGuard 仅 fred/data_commands 路径检查 | `data_commands.py` L185–192 · `tier_a_live_incremental_dispatch.py` 非 fred 分支 | macro/bar 源 dispatch 绕过 ResourceGuard；fred 与余源行为不一致                              | 在 `run_tier_a_live_incremental` 入口统一 `ResourceGuard().check()`，或 `_run_macro_live` / bar 分支各加 guard | monkeypatch guard HARD_STOP 时 dispatch 应 fail-closed                   |
| A4-P3-02 | P3  | 未使用 import                                | `tier_a_live_incremental_dispatch.py` L240                                       | `create_world_bank_fetch_port` 导入未用（`port_factory=create_world_bank_incremental_port`） | 删除 L240 无用 import                                                                                          | `ruff check backend/app/ops/tier_a_live_incremental_dispatch.py`         |

已对抗搜索：`tier_a_live_incremental_dispatch.py` · `tier_a_live_acceptance.py` · `deribit_port.py` · `tests/test_tier_a_live_*` · `tests/test_*incremental_e2e.py` · `tests/*_incremental_support.py` · `incremental_source_registry.py` · `clean_write_targets.py` · ADR-028/034 · `data_commands._sync_fred_macro_incremental` · `research/l4-tier-a-live-accept-evidence.md`。

---

## Verification Story

| 项               | 结果                                                      |
| ---------------- | --------------------------------------------------------- |
| 测试 reviewed    | 是 — 11 源 live e2e + harness + dispatch 单测             |
| Build verified   | 否 — A4 只读，未跑 pytest                                 |
| ADR-028 矩阵     | 是 — registry/clean_write_targets 未改；dispatch 路由对齐 |
| Security checked | 是 — 无密钥进 diff；隔离 + live gate                      |

[REDACTED]
