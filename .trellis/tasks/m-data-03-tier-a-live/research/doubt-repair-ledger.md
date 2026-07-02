# Doubt Repair Ledger — M-DATA-03 (D-01..D-12)

> **SSOT：** `research/doubt-repair-m-data-03.md` · **关账：** 2026-07-03 · **12/12 已修复** · **0 阶段外置**

| ID   | P   | Area                | disposition | 证据                                                                                                                           |
| ---- | --- | ------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------ |
| D-01 | P0  | AC / R4             | 已修复      | `research/doubt-live-final.log` · sandbox `doubt-final-20260703` · CLI exit **0** · `l4-tier-a-live-accept-evidence.md`        |
| D-02 | P1  | F0 / Repair theater | 已修复      | `plan-spec.md` partial F0 + SKIP 与 `_run_f0_data_health` 代码统一；audit-repair-ledger A1-P1-001/A4-P2-01 叙事一致            |
| D-03 | P1  | F0 / Test gap       | 已修复      | `tests/test_tier_a_live_dispatch.py`：`test_runF0DataHealth_*` · `test_runSourceLiveAcceptance_f0Path_*` · `f0Fail_blocksPass` |
| D-04 | P1  | S-ACCEPT / Test     | 已修复      | `test_runTierALiveIncremental_fredLiveNetwork_realDispatch` `@pytest.mark.network` 真网 fred quick                             |
| D-05 | P1  | Gate                | 已修复      | `validate_repair_close()` spot-checks（git ops · dispatch network · F0 pytest · l4 post-Repair exit 0）                        |
| D-06 | P2  | F0 / Semantics      | 已修复      | `plan-spec.md` §Interface Contract：SKIP 满足 AC#4；`test_runF0DataHealth_skipsWhenNoRawEvidence`                              |
| D-07 | P2  | Isolation           | 已修复      | `test_tierALiveOps_mainDbFingerprintUnchangedAfterSandbox` + mock-sync dispatch 集成路径隔离断言                               |
| D-08 | P2  | Ponytail / DCP-05   | 已修复      | `_live_sync_registry()` registry 模式；ledger 证据含 pytest + ponytail 天花板在 plan-spec                                      |
| D-09 | P2  | GitNexus            | 已修复      | `node .gitnexus/run.cjs analyze` exit 0；`tier_a_live_acceptance` 符号可 context 查询                                          |
| D-10 | P2  | Docs drift          | 已修复      | `l4-tier-a-live-accept-evidence.md` F0 partial 说明与 `tier_a_live_acceptance.py` 一致                                         |
| D-11 | P3  | Pass semantics      | 已修复      | `test_runSourceLiveAcceptance_plannedWithZeroCleanFails` PLANNED+0 clean → fail                                                |
| D-12 | P3  | noSilentFallback    | 已修复      | `tests/test_fred_macro_incremental_e2e.py::test_fredLive_noSilentFallbackWhenGateClosed`                                       |
