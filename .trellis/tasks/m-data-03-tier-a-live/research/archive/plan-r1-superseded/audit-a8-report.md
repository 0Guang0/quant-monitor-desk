# Audit A8 — 测试缺口（audit-test-gap）

## 元信息

| 字段                    | 值                               |
| ----------------------- | -------------------------------- |
| 维度                    | A8 — audit-test-gap              |
| 任务                    | M-DATA-03 Tier A live acceptance |
| `plan_protocol_version` | 4.1                              |
| 模板                    | `agents/qa-expert.md`            |
| 日期                    | 2026-07-03                       |
| 审计员                  | composer-2.5                     |

---

## 维度证据 §3.8

### 执行命令与结果

| 命令                                                                                                  | 结果                        | 说明                                                          |
| ----------------------------------------------------------------------------------------------------- | --------------------------- | ------------------------------------------------------------- |
| `uv run pytest tests/test_tier_a_live_harness.py tests/test_tier_a_live_dispatch.py -q`               | exit 0                      | 17 passed, 1 skipped（network smoke）                         |
| `uv run pytest tests/test_*_incremental_e2e.py（11 模块）-q -rs`                                      | exit 0                      | 45 passed, **22 skipped**（`need --run-network`）             |
| `uv run pytest tests/test_docstring_quadruple_coverage.py -q`                                         | exit 0                      | 五字段门禁全绿                                                |
| `uv run pytest tests/test_fred_macro_incremental_e2e.py::test_fredIncremental_live_smoke_envGated -v` | **exit 0, 1 passed, 2.15s** | **未** `--run-network` 即执行（环境有 `FRED_API_KEY` 时真网） |

### 切片 ↔ 测试追溯

| 切片 / AC                                       | 建议测试（`to-issues-slices.md`）                                       | 覆盖状态                                                                |
| ----------------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| S00-INFRA                                       | `test_tier_a_live_harness.py`；负向：无 env 闸 / 主库 / silent fallback | **绿** — 15 用例含 3 类负向                                             |
| S-LIVE-FRED … S-LIVE-MOOTDX（11 源）            | 各 `test_*_incremental_e2e.py` `-m network` write + idempotent          | **绿** — 11 文件 × 2 = **22** `@pytest.mark.network`                    |
| S-MERGE                                         | `test_catalog.yaml` + `loop_maintain`                                   | **绿** — 11 e2e + 2 新模块已登记                                        |
| S-ACCEPT                                        | `tier_a_live_acceptance.py` 11/11 exit 0                                | **部分** — 仅 exit 2 负向 subprocess；无派发链 pytest                   |
| 默认 `pytest -q` skip network                   | `conftest.py` `pytest_collection_modifyitems`                           | **FAIL** — `test_fredIncremental_live_smoke_envGated` 绕过 network 标记 |
| 五字段 docstring                                | `testing-guidelines` §9.1                                               | **绿** — `test_docstringQuadruple_allPytestFunctionsDocumented`         |
| E2 inspect + F0 health（INDEX §2 / ADR-034 §4） | acceptance + e2e                                                        | **部分** — DbInspector（E2）有；**F0 data health 无 pytest**            |

### Red Flag 映射

| Red Flag / 契约                                | 测试 / 证据                                                 | 状态                                                           |
| ---------------------------------------------- | ----------------------------------------------------------- | -------------------------------------------------------------- |
| 默认 CI 无 live 真网（`integration-audit.md`） | `conftest.py` + 22 network marks                            | **缺口** — fred `live_smoke` 例外                              |
| `QMD_ALLOW_LIVE_FETCH` fail-closed             | harness + 5 源 per-source `noSilentFallback` + fred harness | 绿（S00 级覆盖）                                               |
| 主库路径拒绝（ADR-034）                        | `test_assertIsolatedLiveDataRoot_*`                         | 绿                                                             |
| 11/11 live e2e 隔离写 clean                    | 22 network tests                                            | 绿（须 `--run-network` + KEY）                                 |
| S-ACCEPT sync→clean→inspect                    | `run_tier_a_live_incremental`                               | **无 pytest**；仅 `l4-tier-a-live-accept-evidence.md` 手工证据 |
| inspect/health non-blocker（ADR-034 §4）       | DbInspector in e2e/dispatch                                 | E2 绿；**F0 未测**                                             |
| `tier_a_live_acceptance.py` exit 0/1/2         | harness exit 2 only                                         | exit 0/1 **无自动化**                                          |

### test_catalog.yaml 新模块

| 模块                                 | `purpose`              | `type`           | 缺口                                        |
| ------------------------------------ | ---------------------- | ---------------- | ------------------------------------------- |
| `tests/test_tier_a_live_harness.py`  | S00-INFRA harness      | contract         | `verifies.docs` 未链 ADR-034                |
| `tests/test_tier_a_live_dispatch.py` | S-ACCEPT dispatch 单测 | runtime-contract | 未覆盖 `run_tier_a_live_incremental` 主路径 |

---

## §维度裁决

**FAIL**

---

## 计划内问题

| ID        | P   | 标题                                                 | 锚点                                                                                                                                                                                                                         | 根因                                                                                                                     | 修复方案                                                                                                                                                                                  | 验证                                                                                                                                                                                                   |
| --------- | --- | ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| A8-P1-001 | P1  | fred `live_smoke` 未标 network，默认 pytest 可打真网 | `tests/test_fred_macro_incremental_e2e.py::test_fredIncremental_live_smoke_envGated` L87–113；`plan-spec.md` Live pytest 约定；ADR-034 §3                                                                                    | 用 `@pytest.mark.skipif(FRED_API_KEY)` 替代 `@pytest.mark.network`，与 ADR-034「network 标记 + 默认 skip」双轨策略不一致 | 为该用例加 `@pytest.mark.network` 并删除/合并与 `-m network` 正式 live e2e 重复的路径；或改为纯 replay 并移除 `use_mock=False`                                                            | `uv run pytest tests/test_fred_macro_incremental_e2e.py::test_fredIncremental_live_smoke_envGated -q -rs` → skipped；`uv run pytest tests/test_fred_macro_incremental_e2e.py -q` 全绿且无 network 请求 |
| A8-P2-001 | P2  | S-ACCEPT 派发链无 pytest 集成覆盖                    | `backend/app/ops/tier_a_live_incremental_dispatch.py::run_tier_a_live_incremental`；`tier_a_live_acceptance.py::run_source_live_acceptance`；`to-issues-slices.md` S-ACCEPT；`test_tier_a_live_dispatch.py`（仅 3 辅助单测） | Execute 以手工 `l4-tier-a-live-accept-evidence.md` 关账，未将 acceptance 主路径纳入可复跑 pytest                         | 在 `test_tier_a_live_dispatch.py` 或 harness 中增加：mock `_run_live_sync` + 真实 `DbInspector` sandbox，断言 `LiveIncrementalOutcome`/`SourceAcceptanceResult`；至少覆盖 fred quick 子集 | `uv run pytest tests/test_tier_a_live_dispatch.py -q` 含新用例绿                                                                                                                                       |
| A8-P2-002 | P2  | F0 data health 未在验收路径断言                      | ADR-034 §4「inspect/health non-blocker」；`EXECUTION_INDEX.md` §2「E2 inspect + F0 data health」；`tier_a_live_acceptance.py`；`l4-tier-a-live-accept-evidence.md` L30                                                       | `run_source_live_acceptance` 仅调 `DbInspector`（E2），未调用 data health profile runner；证据文档口头 defer F0          | 在 `run_source_live_acceptance` 或 acceptance CLI 中接入现有 health runner（或明确 ponytail 边界 + 绑后续任务）；补 sandbox pytest 断言无 P0 blocker                                      | 新 pytest 断言 health status；或 ADR/INDEX 修订并登记阶段外置（须绑任务 ID）                                                                                                                           |
| A8-P2-003 | P2  | acceptance CLI exit 1 无自动化测试                   | `plan-spec.md` exit 0/1/2 契约；`test_tier_a_live_harness.py` 仅 `returncode == 2`                                                                                                                                           | 负向覆盖不完整，source failure 路径无回归网                                                                              | 用 monkeypatch 注入必败 `run_source_live_acceptance`，subprocess 断言 `returncode == 1`                                                                                                   | `uv run pytest tests/test_tier_a_live_harness.py -q` 含 exit 1 用例绿                                                                                                                                  |

---

## 计划外发现

| ID        | P   | 标题                                          | 锚点                                                                                                                                                               | 根因                                                         | 修复方案                                                                                  | 验证                                                  |
| --------- | --- | --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------ | ----------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| A8-P2-004 | P2  | `LiveIncrementalOutcome.passed` WARN 路径未测 | `tier_a_live_incremental_dispatch.py::LiveIncrementalOutcome.passed` L32–36；`test_tier_a_live_dispatch.py`                                                        | 仅测 FAIL/EMPTY_RESPONSE，未测 `inspect_status=WARN` 应 pass | 补 `test_liveIncrementalOutcome_passedAllowsInspectWarn`                                  | `uv run pytest tests/test_tier_a_live_dispatch.py -q` |
| A8-P3-001 | P3  | 6 源缺 per-source `noSilentFallback` 负向     | `test_sec_edgar/alpha_vantage/deribit/cninfo/mootdx_incremental_e2e.py`；对比 `test_baostock_incremental_e2e.py::test_baostockLive_noSilentFallbackWhenGateClosed` | S00 harness 以 fred port 泛化覆盖；各 port 未独立断言        | 按 baostock 模式为 6 源各加 1 条 gate-closed 负向（或文档声明 S00 泛化足够并绑 ponytail） | 对应 e2e 模块 `-q` 绿                                 |

已对抗搜索：`tests/test_*_incremental_e2e.py`（11 源）、`test_tier_a_live_*.py`、`conftest.py` network 收集、`test_catalog.yaml` M-DATA-03 条目、`tier_a_live_acceptance.py` / `tier_a_live_incremental_dispatch.py` 派发与 exit 码路径、`test_docstring_quadruple_coverage.py`、ADR-034 / plan-spec / to-issues-slices / EXECUTION_INDEX §2。

[REDACTED]
