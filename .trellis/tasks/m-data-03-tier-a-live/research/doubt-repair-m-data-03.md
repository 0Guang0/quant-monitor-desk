# Doubt Review — M-DATA-03 Repair + Round Completion

## Verdict

**HONEST_FAIL**

Repair ledger 41/41 已修复与 `validate-repair-close` exit 0 仅证明 disposition 关账，**不能**支撑活卡 §5 AC#3（11/11 真网 acceptance）、AC#4（data health）、或诚实 R4。存在文档/代码/ledger 三向矛盾的 F0 关账、S-ACCEPT 派发链仅 mock 集成测、11/11 live 无本审查可复验证据。

**阻塞 `finish-work` / 诚实 R4：**

1. `tier_a_live_acceptance.py` 11/11 真网绿 — 无独立复跑证据（工作区无 `.audit-sandbox/m-data-03/`，`l4-tier-a-live-accept-evidence.md` 为文档自述）
2. F0 data health — ledger 四条 ID 用互斥方案均标「已修复」，plan-spec/l4 与代码不一致，且无 F0 pytest
3. S-ACCEPT dispatch「集成」测 — 全部 mock `_run_live_sync`，未满足 audit 要求的派发链/网络覆盖
4. `validate-repair-close` 不校验代码证据，仅扫 ledger disposition

---

## Findings (issues only)

| ID   | P   | Area                | Issue                                                                            | Evidence                                                                                                                                                                                                                                                                                | Suggested fix                                                                                                                                                |
| ---- | --- | ------------------- | -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| D-01 | P0  | AC / R4             | **11/11 live acceptance 未独立复验**；Repair 关账无新鲜可核对证据                | 活卡 §5 AC#3；`audit.report.md` L42「未在 A9 独立复跑」；`Glob .audit-sandbox/m-data-03/**` → 0 文件；`l4-tier-a-live-accept-evidence.md` 仅声称 exit 0、无 per-source 日志/时间戳                                                                                                      | 在隔离 `DATA_ROOT` + keys 下复跑 `uv run python scripts/tier_a_live_acceptance.py`，落盘 per-source 输出至 `research/` 或 sandbox 工件；Repair/A9 引用该证据 |
| D-02 | P1  | F0 / Repair theater | **F0 关账自相矛盾**：四条 ledger ID 用互斥叙事均标已修复                         | `plan-spec.md` L64–68、`l4-tier-a-live-accept-evidence.md` L30：`qmd data health` **不在** CLI 路径；`tier_a_live_acceptance.py` L188–219、L241–249 **已接入** `_run_f0_data_health`；ledger A1-P1-001=「ponytail 文档」、A4-P2-01/A5-P2-001=「代码接入」、A8-P2-002=「ponytail R-OPS」 | 二选一并统一 SSOT：要么从 acceptance 移除 F0 并 formal ponytail+任务 ID，要么更新 plan-spec/l4/活卡 AC#4 并补 F0 pytest；ledger 不得四条同标已修复           |
| D-03 | P1  | F0 / Test gap       | **`_run_f0_data_health` 零 pytest**；mock 路径绕过 F0                            | `rg _run_f0_data_health tests/` → 0；`test_runSourceLiveAcceptance_mockSync_returnsPass` monkeypatch 整个 `run_tier_a_live_incremental`，不触 F0；`test_runTierALiveSandbox_dbInspectorNonFail_afterMockSync` docstring 仍写「ponytail: F0 profile 由 R-OPS 接入」                      | 增 `test_runSourceLiveAcceptance_f0Fail_blocksPass`（有 raw + FAIL profile）及 SKIP 边界测；或回滚代码与 A8-P2-002 disposition                               |
| D-04 | P1  | S-ACCEPT / Test     | **派发链「集成」测全部为 mock sync**，非 audit 要求的 network/真实派发           | A4-P1-02 原 finding：「零集成/网络测试」；`tests/test_tier_a_live_dispatch.py` 无 `@pytest.mark.network`；三处集成测均 `monkeypatch.setattr(..., "_run_live_sync", _mock_sync)`                                                                                                         | 至少 1 条 `--run-network` 测走真实 `run_tier_a_live_incremental`（如 fred quick）；或 ledger 改回待修复/阶段外置并写明 mock-only 天花板                      |
| D-05 | P1  | Gate                | **`validate-repair-close` 仅校验 ledger disposition**，不验证修复证据            | `.trellis/scripts/common/validate_audit_handoff.py` L203–216：只 `_validate_ledger_dispositions`                                                                                                                                                                                        | 扩展 gate：spot-check P1 ID 证据命令或禁止无代码锚点的已修复                                                                                                 |
| D-06 | P2  | F0 / Semantics      | **F0 SKIP 不阻断 pass**；与活卡 AC#4「data health 无 blocker」口径弱对齐         | `_run_f0_data_health` 无 evidence → `SKIP`（L193–194）；`run_source_live_acceptance` 仅 `health_status == "FAIL"` 才 fail（L244）                                                                                                                                                       | 明确 SKIP 是否满足 AC#4；若否，无 raw 时应 fail 或强制 evidence 布局                                                                                         |
| D-07 | P2  | Isolation           | **主库零污染测仅覆盖 `ensure_isolated_db`**，非完整 acceptance/dispatch          | A7-P3-001 证据=`test_tierALiveOps_mainDbFingerprintUnchangedAfterSandbox`：只调 `ensure_isolated_db`，未跑 sync                                                                                                                                                                         | 在 mock-sync 或 `--quick` live 后复验主库 fingerprint                                                                                                        |
| D-08 | P2  | Ponytail / DCP-05   | **A2-P1-001「已修复」过度宣称**：重复逻辑迁至 registry，体量未收敛               | `_live_sync_registry()` L225–424（~200 行 import+lambda）；audit 要求 `_run_live_sync` <120 行 — 函数仅 2 行，但 DCP-05 平行维护仍在 registry                                                                                                                                           | 诚实标 ponytail 或继续收敛至 `data_commands` 单入口；ledger 证据应含行数/重复度指标                                                                          |
| D-09 | P2  | GitNexus            | **A1-P3-005 未真正修复**：新符号仍不可查                                         | `context("tier_a_live_acceptance", repo=quant-monitor-desk)` → Symbol not found（本审查 2026-07-03）                                                                                                                                                                                    | 复跑 analyze + 验证 context 命中；或 ledger 改阶段外置                                                                                                       |
| D-10 | P2  | Docs drift          | **`l4-tier-a-live-accept-evidence.md` 与代码不一致**（F0）                       | l4 L28–30：仅 E2 inspect；代码 L241 调 F0                                                                                                                                                                                                                                               | 同步 l4 或回滚代码                                                                                                                                           |
| D-11 | P3  | Pass semantics      | **`PASS_SYNC_STATUSES` 含 `PLANNED`**，acceptance 对 PLANNED 无 clean 行数 guard | `tier_a_live_status.py` L9；`run_source_live_acceptance` L263 仅对 `COMPLETED` 查 empty clean                                                                                                                                                                                           | 确认 bar/backfill 是否可返回 PLANNED+0 行；若可，收紧 status 集                                                                                              |
| D-12 | P3  | noSilentFallback    | **fred 无 per-source e2e `noSilentFallback`**（仅 harness exemplar）             | A8-P3-001 声称「5 源 e2e + exemplar」；`test_fred_macro_incremental_e2e.py` 无 `noSilentFallback` 用例                                                                                                                                                                                  | 补 fred e2e 负向或 ledger 标 ponytail 非已修复                                                                                                               |

---

## Ledger spot-check (≥5 IDs)

| Ledger ID | Claim                                                     | Code/test evidence                                                                                    | Honest?                                        |
| --------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| A1-P1-001 | plan-spec F0/E2 ponytail + l4 对齐                        | `plan-spec.md` L64–68 明确 F0 **不在** acceptance CLI；与 `_run_f0_data_health` 代码矛盾              | **否** — 文档 defer 与代码接入未统一           |
| A2-P1-001 | source_id→runner registry                                 | `_live_sync_registry()` ~200 行；`_run_live_sync` 2 行；pytest 绿但无 `--quick` live 证据             | **部分** — 结构改进，DCP-05 重复未消除         |
| A3-P1-01  | `validate_live_acceptance_env` fail-closed + fred mock 禁 | `tier_a_live_acceptance.py` L118–122；`test_validateLiveAcceptanceEnv_rejectsFredMockEnv`             | **是**                                         |
| A4-P1-02  | `test_tier_a_live_dispatch.py` 集成测                     | 三测均 mock `_run_live_sync`；零 network mark                                                         | **否** — mock 集成 ≠ audit 要求的派发/网络覆盖 |
| A4-P2-01  | `_run_f0_data_health in run_source_live_acceptance`       | 代码存在 L241；**零** F0 pytest；plan-spec/l4 仍 defer F0                                             | **否** — repair theater                        |
| A7-P3-001 | 主库指纹零污染                                            | `test_tierALiveOps_mainDbFingerprintUnchangedAfterSandbox` 仅 `ensure_isolated_db`                    | **部分** — 未覆盖完整 acceptance 路径          |
| A8-P2-002 | E2 测 + F0 ponytail R-OPS                                 | `test_runTierALiveSandbox_dbInspectorNonFail_afterMockSync` docstring 仍写 F0 未接入；ledger 标已修复 | **否** — 测试自述与 ledger 冲突                |

---

## Commands run + exit codes

| Command                                                                                             | Exit | Notes                       |
| --------------------------------------------------------------------------------------------------- | ---: | --------------------------- |
| `uv run pytest tests/test_tier_a_live_harness.py tests/test_tier_a_live_dispatch.py -q`             |    0 | 29 passed, 1 skipped        |
| `uv run pytest -q`                                                                                  |    0 | 全量 ~436s                  |
| `uv run python .trellis/scripts/task.py validate-repair-close .trellis/tasks/m-data-03-tier-a-live` |    0 | 仅 disposition 校验         |
| GitNexus `context("tier_a_live_acceptance", repo=quant-monitor-desk)`                               |    — | Symbol not found            |
| `Glob **/.audit-sandbox/m-data-03/**`                                                               |    — | 0 files（无 live 验收工件） |
| `rg _run_f0_data_health tests/`                                                                     |    — | 0 matches                   |
| `rg _sync_result_passed`                                                                            |    — | 0 matches（A2-P2-001 可信） |

**未跑（需 keys/真网，且非本审查 pass 依据）：** `QMD_ALLOW_LIVE_FETCH=1 uv run python scripts/tier_a_live_acceptance.py` 11/11

---

## Explicit non-issues (only if searched and clean)

| 项                                       | 核查                                                                                          | 结论                                  |
| ---------------------------------------- | --------------------------------------------------------------------------------------------- | ------------------------------------- |
| A2-P2-001 死函数 `_sync_result_passed`   | `rg _sync_result_passed` 全仓 0                                                               | 已删除，可信                          |
| A2-P2-002 重复 COMPLETED 分支            | `run_tier_a_live_incremental` L487–489 单处 normalize                                         | 可信                                  |
| A3-P1-01 fred mock env 静默退回          | `validate_live_acceptance_env` + `test_validateLiveAcceptanceEnv_rejectsFredMockEnv`          | 可信                                  |
| A8-P1-001 fred `live_smoke` network 标记 | `test_fred_macro_incremental_e2e.py` L87 `@pytest.mark.network`                               | 可信                                  |
| 默认 CI pytest 全绿                      | `uv run pytest -q` exit 0                                                                     | 可信（不证明 11/11 live）             |
| SEC_EDGAR UA env 校验                    | `test_validateLiveAcceptanceEnv_rejectsMissingSecEdgarUserAgent` + `rejectsBareSecEdgarUa`    | 可信                                  |
| ADR-034 隔离路径拒绝                     | `test_assertIsolatedLiveDataRoot_*` harness 负向                                              | 可信                                  |
| deribit live instrument 探测             | `_resolve_deribit_live_instrument` + `_live_instruments()` fallback（非硬编码 BTC-PERPETUAL） | A4-P1-01 代码层可信；未独立 live 复验 |
