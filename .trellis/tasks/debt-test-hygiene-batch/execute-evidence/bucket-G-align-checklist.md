# bucket-G align-checklist (Phase A align-ponytail)

**Owner:** agent-G  
**Branch:** `debt/test-hygiene/bucket-g-gate`  
**Date:** 2026-06-24  
**Modules:** 13 gate/policy test files (150 tests)

## 五问汇总

| 模块                                       | 用例数 | Q1 对象 | Q2 验证点 | Q3 失败含义 | Q4 额外行为          | Q5 复用 | 备注                                                                             |
| ------------------------------------------ | ------ | ------- | --------- | ----------- | -------------------- | ------- | -------------------------------------------------------------------------------- |
| test_batch3_staged_downstream_gate.py      | 2      | Y       | Y         | Y           | Y（无）              | Y       | 合并重复 `_read`                                                                 |
| test_batch25_production_data_gate.py       | 4      | Y       | Y         | Y           | Y（无）              | Y       | `_read_json`→`_read_text`                                                        |
| test_batch275_live_pilot_gate.py           | 27     | Y       | Y         | Y           | Y（无）              | Y       | `_fetch_call_tracker`、`_phase3_evidence_with_hitl`；`@pytest.mark.network` 保留 |
| test_production_live_pilot_policy.py       | 9      | Y       | Y         | Y           | Y（无）              | Y       | `_read_three_registries`                                                         |
| test_fred_staged_semantics.py              | 3      | Y       | Y         | Y           | Y（无）              | Y       | `map(_read, …)` 批量读档                                                         |
| test_round3_audit_registry_alignment.py    | 21     | Y       | Y         | Y           | Y（无）              | Y       | 已对齐，本批无逻辑变更                                                           |
| test_round3_verification_command_matrix.py | 5      | Y       | Y         | Y           | Y（无）              | Y       | 已对齐，本批无逻辑变更                                                           |
| test_trellis_audit_trace_authority.py      | 7      | Y       | Y         | Y           | Y（无）              | Y       | 已对齐，本批无逻辑变更                                                           |
| test_unresolved_item_task_coverage.py      | 5      | Y       | Y         | Y           | Y（无）              | Y       | 已对齐，本批无逻辑变更                                                           |
| test_global_execution_rules.py             | 5      | Y       | Y         | Y           | Y（无）              | Y       | `contract_gate_support.PROJECT_ROOT`                                             |
| test_staged_pilot.py                       | 48     | Y       | Y         | Y           | Y（删未用常量/导入） | Y       | `_fresh_migrated_db`；移除 `TASK_EVIDENCE*`                                      |
| test_production_gate.py                    | 1      | Y       | Y         | Y           | Y（无）              | Y       | `contract_gate_support.PROJECT_ROOT`                                             |
| test_manifest_protocol.py                  | 13     | Y       | Y         | Y           | Y（无）              | Y       | `REPO`←`PROJECT_ROOT`                                                            |

**全局：** 150/150 五问均为 Y；无注释-契约冲突（见 `bucket-G-comment-conflicts.md`）。

## ponytail 变更摘要（价值守恒）

- 仅删注释未声称的冗余：未使用 `TASK_EVIDENCE`/`TASK_EVIDENCE_V2`、重复 `import json`/`datetime`、重复 DuckDB migrate 样板。
- 合并重复 setup：fetch-not-called tracker、HITL evidence 目录、三份 registry 批量读取、mutation proof DB 初始化。
- **未**合并 parametrize、**未**削弱断言、**未** mock 掉 `@pytest.mark.network` live 路径。

## 跳过用例（预期）

| 用例                                                                       | 原因                               |
| -------------------------------------------------------------------------- | ---------------------------------- |
| `test_current_target_db_has_no_clean_layer1_production_observations`       | 本地无 `quant_monitor.duckdb`      |
| `test_current_raw_data_root_contains_only_staged_batch25_fixture_payloads` | `data/raw` 无 staged JSON          |
| `test_livePilot_phase3RawOnly_threeRequestsLive`                           | 默认无 `--run-network`（门控保留） |

## conftest 请求

无。本桶改动均在 allowed 模块内完成，无需改 `tests/conftest.py`。
