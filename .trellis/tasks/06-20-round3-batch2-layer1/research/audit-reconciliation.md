# Audit Reconciliation — 逐项核对 (2026-06-20 复验)

> 主会话对 A1–A8 全部 agent 报告逐条核对 + 补修 + 全量验收

## 验收命令（本轮复验）

| 命令                                           | 结果          |
| ---------------------------------------------- | ------------- |
| `pytest tests/test_layer1_*.py -q`             | **35 passed** |
| `pytest -q`                                    | **PASS**      |
| `production_gate.py`                           | **PASS**      |
| `QMD_DATA_ROOT=.audit-sandbox/...` layer1 复跑 | **35 passed** |
| `data/duckdb/quant_monitor.duckdb` SHA256 前后 | **unchanged** |

---

## A1 audit-spec (§3.1)

| ID         | Sev  | 状态   | 证据                                                           |
| ---------- | ---- | ------ | -------------------------------------------------------------- |
| A1-F01     | P2   | CLOSED | `implement.jsonl` + `config.py`                                |
| A1-F02     | P2   | CLOSED | `implement.jsonl` + `connection.py`                            |
| A1-F03     | P2   | CLOSED | `test_axisSpecLoader_observableIndicators_matchContractFields` |
| A1-F04     | P2   | CLOSED | `_validate_engineering_rules_file` + test                      |
| A1-F05     | P2   | CLOSED | `_validate_source_dataset_ids` + test                          |
| A1-F06     | P3   | CLOSED | `layer1_axis_contract.yaml` + `ROBUST_Z_UNAVAILABLE`           |
| A1-F07     | P3   | CLOSED | `interpretation.py` 全 forbidden terms 脱敏                    |
| A1-F08–F10 | INFO | CLOSED | scope 负向确认；GitNexus 再索引                                |

## A2 ponytail (§3.2)

| ID          | Sev        | 状态              | 说明                                                                 |
| ----------- | ---------- | ----------------- | -------------------------------------------------------------------- |
| A2-01–A2-07 | Suggestion | **N/A (非 §4.3)** | Round1 先例：可选 trim；A2-01 已由测试使用 `LINEAGE_REQUIRED_FIELDS` |

## A3 security (§3.3)

| ID                      | Sev    | 状态   | 证据                                                                                   |
| ----------------------- | ------ | ------ | -------------------------------------------------------------------------------------- |
| A3-01                   | MEDIUM | CLOSED | `write_lineage` → WriteManager + `test_layer1Snapshot_writeLineageViaWriteManager`     |
| A3 LOW spec_root        | LOW    | CLOSED | `_assert_spec_root_allowed` + `test_axisSpecLoader_rejectsSpecRootOutsideAllowedRoots` |
| A3 INFO agent_outputs   | INFO   | CLOSED | builder guard                                                                          |
| A3 INFO \_execute_write | INFO   | CLOSED | `WriteManager.write()` 公开 API                                                        |
| A8-01/02 cross-ref      | —      | CLOSED | A8 边界测试已绿                                                                        |

## A4 quality (§3.4)

| ID       | Sev  | 状态                                                  |
| -------- | ---- | ----------------------------------------------------- |
| A4-01    | P1   | CLOSED                                                |
| A4-02    | P1   | CLOSED                                                |
| A4-03    | P1   | CLOSED                                                |
| A4-04    | P2   | CLOSED                                                |
| A4-05    | P2   | CLOSED                                                |
| A4-06    | P2   | CLOSED                                                |
| A4-07    | P2   | CLOSED                                                |
| A4-08    | P3   | CLOSED                                                |
| A4-09    | P3   | CLOSED                                                |
| A4-10    | INFO | CLOSED — `AxisFeatureEngine` docstring 注明 WARN 策略 |
| A4-11/12 | INFO | PASS — 回归锚点保留                                   |

## A5 completion (§3.5)

| ID             | Sev   | 状态                               |
| -------------- | ----- | ---------------------------------- |
| A5-01–05 trace | P1/P2 | CLOSED — AC ≥4                     |
| A5-06/07       | P1    | CLOSED — sandbox + prod-path 35/35 |

## A6 perf (§3.6)

| ID       | Sev | 状态                                                           |
| -------- | --- | -------------------------------------------------------------- |
| A6-01/02 | P1  | CLOSED — `a6-perf-output.json`                                 |
| A6-03    | P2  | CLOSED — AUDIT.plan 注释与 `ResourceGuard(profile='eco')` 一致 |

## A7 ops (§3.7)

| ID         | Sev | 状态                |
| ---------- | --- | ------------------- |
| init_db ×2 | —   | CLOSED — idempotent |
| prod hash  | —   | CLOSED              |

## A8 test-gap (§3.8)

| ID            | Sev     | 状态       | 测试                                                                           |
| ------------- | ------- | ---------- | ------------------------------------------------------------------------------ |
| A8-R01 / G-01 | P2/HIGH | CLOSED     | `test_axisSpecLoader_emptySpecRoot_rejects`                                    |
| A8-R02 / G-02 | P2/HIGH | CLOSED     | `test_axisSpecLoader_allForbiddenAxis_registersNoneObservable`                 |
| A8-R03 / G-03 | P2/HIGH | CLOSED     | `test_axisSpecLoader_missingQualityRulesKey_appliesContractDefaults`           |
| A8-R04 / G-04 | P2/MED  | CLOSED     | `test_layer1Snapshot_forbiddenSubstitute_blocksWriteWithQualityError`          |
| A8-R05 / G-06 | P2/MED  | CLOSED     | `test_snapshotLineage_agentOutputsNotSource_rejectsAgentProse`                 |
| A8-D01 / G-05 | MED     | **CLOSED** | `AxisObservation.fallback_policy` → `stale_reason` + 增强 SOURCE_SWITCHED 测试 |
| A8-D02 / G-07 | LOW     | CLOSED     | `LINEAGE_REQUIRED_FIELDS` 全字段断言                                           |

---

## 开放项

**0** — 无 P0/P1/P2/P3、无 HIGH/MEDIUM/LOW/INFO 阻塞项遗留。
