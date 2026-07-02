# Audit A5 — Completion（M-DATA-03 Tier A Live）

## 元信息

| 字段                    | 值                                     |
| ----------------------- | -------------------------------------- |
| 维度                    | A5 — audit-completion                  |
| 任务                    | `.trellis/tasks/m-data-03-tier-a-live` |
| `plan_protocol_version` | 4.1                                    |
| 模板                    | `agents/audit-a5-completion.md`        |
| 审计日期                | 2026-07-03                             |
| 模型                    | composer-2.5                           |

---

## 维度证据

### Boot 读序（A5 必触）

| #   | 文件                                         | 状态                        |
| --- | -------------------------------------------- | --------------------------- |
| 1   | `agents/audit-boot-v4.1.md`                  | 已读                        |
| 2   | `agents/audit-coverage-model.md`（链 B）     | 已读                        |
| 3   | `agents/audit-a5-completion.md`              | 已读                        |
| 4   | `agents/audit-finding-schema.md`             | 已读                        |
| 5   | `implement.jsonl`（6 行全文）                | 已读                        |
| 6   | `research/to-issues-slices.md`               | 已读                        |
| 7   | `EXECUTION_INDEX.md` §1–§2                   | 已读（**无 §2.1 Tier 表**） |
| 8   | `research/l4-tier-a-live-accept-evidence.md` | 已读                        |
| 9   | `AUDIT.plan.md` §0.1 / §1                    | 已读                        |
| 10  | `research/00-EXECUTION-ENTRY.md` §1–§3       | 已读                        |

### 独立复验（必做）

| 原 AC / 替代行               | 独立复跑命令                                                                                    | exit code                 | 与代码行为一致            |
| ---------------------------- | ----------------------------------------------------------------------------------------------- | ------------------------- | ------------------------- |
| INDEX §2「全量」             | `uv run pytest -q`                                                                              | **0**（~376s）            | 是；network 用例默认 skip |
| INDEX §2「harness + 负向测」 | `uv run pytest tests/test_tier_a_live_harness.py -q`                                            | **0**（14 pass + 1 skip） | 是                        |
| S-MERGE registry             | `uv run pytest tests/test_tier_a_live_dispatch.py tests/test_source_registry.py -q`             | **0**                     | 是                        |
| S-MERGE loop                 | `uv run python scripts/loop_maintain.py`                                                        | **0**                     | 是                        |
| acceptance exit 2 契约       | `uv run python scripts/tier_a_live_acceptance.py --source-id fred`（无 `QMD_ALLOW_LIVE_FETCH`） | **2**                     | 是                        |
| INDEX §2.1 最弱 2 行         | **EXECUTION_INDEX 无 §2.1**；未跑 Tier B/C prod-path                                            | —                         | 不适用                    |

**未在本会话复跑（需 `QMD_ALLOW_LIVE_FETCH=1` + API keys + network）：**

- 11 源 `-m network` live e2e
- `scripts/tier_a_live_acceptance.py` 11/11 或 `--quick`
- 对照依据：`research/l4-tier-a-live-accept-evidence.md`（Execute 自述 exit 0）

### git diff 范围抽查

- 已改：11 源 e2e/support、`conftest.py`、`test_catalog.yaml`、`deribit_port.py`、generated docs
- 未跟踪（实现核心）：`backend/app/ops/tier_a_live_acceptance.py`、`tier_a_live_incremental_dispatch.py`、`scripts/tier_a_live_acceptance.py`、`tests/test_tier_a_live_harness.py`、`tests/test_tier_a_live_dispatch.py`、`ADR-034`
- 未见新 migration / 主库写路径 / 参考项目 runtime import 扩大

---

### 切片 AC → 代码/测试追溯 + 评分（1–5）

| Slice                    | AC 摘要                                                      | 代码/测试锚点                                                                                                                             | 分    | 说明                                                                             |
| ------------------------ | ------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- | ----- | -------------------------------------------------------------------------------- |
| **S00-ELIGIBILITY**      | 11/11 真网；KEY 槽位；无 ADR 例外                            | `research/tier-a-live-eligibility.md` · `test_tierALiveEligibility_docListsElevenLiveSources`                                             | **4** | 11 源齐全；`SEC_EDGAR_USER_AGENT` 在 acceptance 强制但资格表未列（见 A5-P3-001） |
| **S00-INFRA**            | 隔离 fixture；network 标记；acceptance exit 0/1/2；负向 3 项 | `tests/conftest.py` `isolated_live_data_root` · `test_tier_a_live_harness.py`（14 项） · `scripts/tier_a_live_acceptance.py`              | **5** | 主库拒绝 / 无 env 闸 / silent fallback / CLI exit 2 均可测且绿                   |
| **S-LIVE-FRED**          | live e2e 写 `axis_observation`；幂等；L3                     | `test_fred_macro_incremental_e2e.py` `@pytest.mark.network` ×2 · `test_fredIncremental_live_smoke_envGated`                               | **4** | 测试链完整；本审计未 `--run-network` 复跑                                        |
| **S-LIVE-BAOSTOCK**      | live e2e；幂等；EasyXT forbidden                             | `test_baostock_incremental_e2e.py` network ×2 · `test_baostockIncremental_liveRejectedWithoutOptIn`                                       | **4** | 同上                                                                             |
| **S-LIVE-US-TREASURY**   | live clean 绿                                                | `test_us_treasury_incremental_e2e.py` network ×2 · forbidden gate test                                                                    | **4** | 同上                                                                             |
| **S-LIVE-BIS**           | live 绿；禁止 `BisProvider` import                           | `test_bis_incremental_e2e.py` network ×2 · `test_bisIncremental_forbidden_noBisProviderRuntimeImport`                                     | **4** | L2 负向测存在                                                                    |
| **S-LIVE-WORLDBANK**     | live 绿                                                      | `test_world_bank_incremental_e2e.py` network ×2 · forbidden gate                                                                          | **4** | 同上                                                                             |
| **S-LIVE-CFTC**          | live 周频绿                                                  | `test_cftc_incremental_e2e.py` network ×2 · forbidden gate                                                                                | **4** | 同上                                                                             |
| **S-LIVE-SEC-EDGAR**     | `us_disclosure_clean` 绿                                     | `test_sec_edgar_incremental_e2e.py` network ×2                                                                                            | **4** | dispatch 覆盖 `data_domain=us_filings`                                           |
| **S-LIVE-ALPHA-VANTAGE** | `security_bar_1d` 绿                                         | `test_alpha_vantage_incremental_e2e.py` network ×2                                                                                        | **4** | 同上                                                                             |
| **S-LIVE-DERIBIT**       | `crypto_derivative_clean` 绿                                 | `test_deribit_incremental_e2e.py` network ×2 · `deribit_port.py` live 分支                                                                | **4** | 同上                                                                             |
| **S-LIVE-CNINFO**        | `cn_announcement_clean` 绿                                   | `test_cninfo_incremental_e2e.py` network ×2                                                                                               | **4** | 同上                                                                             |
| **S-LIVE-MOOTDX**        | `security_bar_1d` 绿                                         | `test_mootdx_incremental_e2e.py` network ×2                                                                                               | **4** | 同上                                                                             |
| **S-MERGE**              | registry 三件套；`loop_maintain` 绿                          | `test_catalog.yaml` 登记 harness/dispatch · `loop_maintain.py` OK · registry 测绿                                                         | **4** | 无独立 S-MERGE 模块测；catalog + loop 覆盖                                       |
| **S-ACCEPT**             | 11/11 sync→clean→**inspect + data health** 无 P0；exit 0     | `tier_a_live_incremental_dispatch.py` → `DbInspector.inspect()` only · `run_source_live_acceptance` · `l4-tier-a-live-accept-evidence.md` | **3** | **F0 data health 未接入**（见 A5-P2-001）；11/11 仅文档证据                      |

### 每源 live AC 细项（#1–7）抽查

| #   | 验证点                                    | 覆盖                                                  | 缺口                                                             |
| --- | ----------------------------------------- | ----------------------------------------------------- | ---------------------------------------------------------------- |
| 1   | `QMD_ALLOW_LIVE_FETCH` + 隔离 `DATA_ROOT` | harness + conftest + dispatch `_prepare_sandbox`      | fred dispatch 依赖外层 `ensure_isolated_db`（不对称但 env 已设） |
| 2   | sync `COMPLETED` / caught-up              | dispatch + acceptance `_PASS_SYNC_STATUSES`           | —                                                                |
| 3   | clean 行数 ≥1                             | e2e + `_clean_row_count`                              | caught-up 归一化 `EMPTY_RESPONSE`（ponytail 已注释）             |
| 4   | 幂等                                      | 11 源各 1 条 `idempotentSecondRun` network test       | 未 audit 复跑                                                    |
| 5   | **inspect (E2) + data health (F0)**       | `DbInspector.inspect()` only                          | **F0 缺失**                                                      |
| 6   | 无 silent fallback                        | S00 harness + 5 源 forbidden e2e                      | 其余源依赖 S00 通用测                                            |
| 7   | L2/L3 借鉴证据                            | `reference-adoption` 文档 + bis forbidden import test | 文档型，无自动化 SDD URL 断言                                    |

---

## §维度裁决

**FAIL**

（§计划内 ≥1 非占位 finding）

---

## §计划内问题

| ID        | P   | 标题                               | 锚点                                                                                                                                                        | 根因                                                                                                                                                                                | 修复方案                                                                                                                                                                                                                                                                             | 验证                                                                                                                                                                               |
| --------- | --- | ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A5-P2-001 | P2  | S-ACCEPT 未跑 F0 data health       | `to-issues-slices.md` S-ACCEPT · 活卡 §5.4 · ADR-034 §Consequences F0 · `tier_a_live_incremental_dispatch.py:451` · `l4-tier-a-live-accept-evidence.md` L30 | `run_tier_a_live_incremental` 仅调用 `DbInspector.inspect()`；acceptance 未调用 `run_source_data_health` / `qmd data health`；证据 md 将 F0 defer 至 nightly 但 slices/活卡 AC 未改 | 在 `run_source_live_acceptance` 或 dispatch 末尾对每个源调用现有 F0 runner（如 `sandbox_clean_write.gates.run_source_data_health` 或 `data_health_cli` 等价路径）；P0 blocker 则 acceptance exit 1；更新 `l4-tier-a-live-accept-evidence.md` 或修 AC 文档二选一（Repair 优先修代码） | `QMD_ALLOW_LIVE_FETCH=1 uv run python scripts/tier_a_live_acceptance.py --quick --data-root .audit-sandbox/m-data-03/audit-repair` exit 0；新增/扩展 harness 断言 F0 被调用且无 P0 |
| A5-P3-001 | P3  | 资格表缺 SEC_EDGAR_USER_AGENT 槽位 | `tier-a-live-eligibility.md` L38 · `tier_a_live_acceptance.py` `SOURCE_API_KEY_ENV` L24                                                                     | 文档写「其余 9 源无 KEY」但 acceptance 对 `sec_edgar` 强制 `SEC_EDGAR_USER_AGENT`                                                                                                   | 在 `tier-a-live-eligibility.md` 环境变量表增加 `SEC_EDGAR_USER_AGENT` 行；同步 `test_tierALiveEligibility_docListsElevenLiveSources` 断言                                                                                                                                            | `uv run pytest tests/test_tier_a_live_harness.py::test_tierALiveEligibility_docListsElevenLiveSources -q` exit 0                                                                   |

---

## §计划外发现

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| —   | —   | 无   | —    | —    | —        | —    |

已对抗搜索：`backend/app/ops/tier_a_live_*.py` · 11 源 `test_*incremental_e2e.py` · `data_commands.py` fred live 路径 · `incremental_source_registry.py` 11 源枚举 · acceptance exit 码分支 · git diff 范围。未发现 Bundle 未登记且需 A5 关账的额外执行偏差（F0 已在计划内登记）。

---

## 摘要

- **链 B 主路径**：S00-INFRA + 11 源 live e2e 结构 + 默认 CI pytest 全绿，Execute `[x]` 与代码大体一致。
- **阻断项**：S-ACCEPT 的 F0 data health AC 未实现，与 slices / 活卡 / ADR-034 模块 F0 声明冲突。
- **审计局限**：live network 与 11/11 acceptance 未在本会话独立复跑；评分 4 的 live 切片基于测试存在性 + 默认 CI，非 live 复验。

[REDACTED]
