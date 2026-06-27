# R3G-01 Audit Repair Closure

**日期：** 2026-06-27 · **分支：** `feature/round3g-sandbox-rehearsal`

## P0 — CLOSED

| ID            | 状态       | 证据                                                                                                                                                                                                                           |
| ------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| R3G-REP-P0-01 | **CLOSED** | `_assert_data_health_admission` 在 `_process_candidate` 写前检查 `sandbox_clean_write_gate_ready` 与 `overall_status`；`test_RehearsalRunner_rejectsWriteWhenDataHealthGateNotReady`                                           |
| R3G-REP-P0-02 | **CLOSED** | `validation_status` 由 `_validation_status_from_dh` 映射；`synthetic_admission=True`；DB `validation_report` 使用 `REHEARSAL_SYNTHETIC_QUALITY_FLAG`；`test_RehearsalRunner_validationStatusReflectsDataHealthNotSilentPassed` |
| R3G-REP-P0-03 | **CLOSED** | `rollback_artifact_{source_id}.json` 分源落盘；`test_RehearsalRunner_perSourceRollbackArtifactsAreDistinct` + dryRun 交叉断言 write_id                                                                                         |
| R3G-REP-P0-04 | **CLOSED** | `execute-evidence/9.0-green.txt`–`9.6-green.txt` 真实 pytest 终端输出                                                                                                                                                          |

## P1 — CLOSED

| ID            | 状态       | 证据                                                                                                                                                                       |
| ------------- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| R3G-REP-P1-01 | **CLOSED** | `staging_semantics=smoke_only_bar_table` 显式标注；`test_RehearsalRunner_smokeOnlyStagingSemanticsExplicit`                                                                |
| R3G-REP-P1-02 | **CLOSED** | `evidence/{source_id}/route_plan.json` 落盘；`test_RehearsalRunner_writesPerSourceRoutePlanOnDisk`                                                                         |
| R3G-REP-P1-03 | **CLOSED** | `required_report_fields()` 全字段 per-source 校验；`test_RehearsalRunner_perSourceReportsSatisfyContractFields`                                                            |
| R3G-REP-P1-04 | **CLOSED** | spy `run_data_health_profile` + `DataHealthService.check_evidence_dir`；`test_RehearsalRunner_perSourceDataHealthProfiles`                                                 |
| R3G-REP-P1-05 | **CLOSED** | `canonical_prod` + runtime `config.DATA_ROOT` 拒绝；`test_RehearsalRunner_refusesDataRootProductionDbPath` · `test_RehearsalCli_dataRootProductionDbPathRejected`          |
| R3G-REP-P1-06 | **CLOSED** | runner 级无 artifact fail-closed；`test_RehearsalRunner_fredWithoutAuthorizationArtifactFails`                                                                             |
| R3G-REP-P1-07 | **CLOSED** | `validate_source_caps` 读契约 `metadata_only`；`test_RehearsalPlan_cninfoRequiresMetadataOnlyPerContract` · `test_RehearsalPlan_fredContractRequiresUserAuthorizationFlag` |
| R3G-REP-P1-08 | **CLOSED** | loader 复用 `validate_source_caps`；`test_rehearsalLoader_reusesContractCapsNotMagicNumber`                                                                                |
| R3G-REP-P1-09 | **CLOSED** | `test_RehearsalRunner_resourceGuardHardStopBlocks` · `test_RehearsalRunner_rejectsWriteWhenDataHealthOverallFails` · dryRun rollback 交叉断言                              |
| R3G-REP-P1-10 | **CLOSED** | `validate_fred_authorization(require_live_credentials=True)` 校验 `FRED_API_KEY`；runner `allow_live_fetch` 接线；`test_RehearsalPlan_fredLivePathRequiresFredApiKey`      |

## P2 — CLOSED

| ID            | 状态       | 证据                                                                                                               |
| ------------- | ---------- | ------------------------------------------------------------------------------------------------------------------ |
| R3G-REP-P2-01 | **CLOSED** | `test_RehearsalPlan_rejectsOverWindowDays`                                                                         |
| R3G-REP-P2-02 | **CLOSED** | cninfo loader `staged_row_count == 5`；`test_rehearsalLoader_cninfoMetadata_only`                                  |
| R3G-REP-P2-03 | **CLOSED** | FRED fixture 在 `tests/fixtures/sandbox_clean_write/r3g01/fred/`；`FIXTURE_EVIDENCE_DIRS`                          |
| R3G-REP-P2-04 | **CLOSED** | `config.py` dotenv · `fred_fetch_ports.py` key normalize · `.env.example` FRED_API_KEY 登记为 P1-10 支撑（非回滚） |
| R3G-REP-P2-05 | **CLOSED** | 契约 `required_report_fields` 补 `data_health_summary`；version `sandbox_clean_write_contract_v1_1`                |
| R3G-REP-P2-06 | **CLOSED** | `test_RehearsalRunner_dryRun_composesGatesAndWritesEvidence` conflict payload 断言                                 |
| R3G-REP-P2-07 | **CLOSED** | GitNexus index stale（`validate_source_caps` not found）；全库 pytest exit 0 替代                                  |

## P3 — CLOSED

| ID            | 状态       | 证据                                                                                         |
| ------------- | ---------- | -------------------------------------------------------------------------------------------- |
| R3G-REP-P3-01 | **CLOSED** | 删 `rehearsal_plan._resolve_path` 死代码；`__init__.py` 桶精简为 runner 导出                 |
| R3G-REP-P3-02 | **CLOSED** | SKIP-OPT-IN：mutation proof 薄包装保留（frozen 可接受）                                      |
| R3G-REP-P3-03 | **CLOSED** | 契约 version bump `sandbox_clean_write_contract_v1_1` + `data_health_summary` 字段           |
| R3G-REP-P3-04 | **CLOSED** | loader `ponytail` 注释 evidence row cap 上游约束                                             |
| R3G-REP-P3-05 | **CLOSED** | `_dry_run_rehearsal_paths` fixture；弱断言收紧（cninfo row count、DH spy、conflict payload） |

## 全库验证

- `uv run pytest -q`：exit 0（2026-06-27 repair 轮次）
- `validate-execute-handoff`：exit 0
- R3G Tier A：40 passed（`test_round3g_sandbox_*` 三文件）
