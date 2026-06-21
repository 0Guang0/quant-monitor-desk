# PH-B4 Audit — Phase 4 Validation + Conflict

## 结论

FAIL

PH-B4 的表面证据文件齐全，且默认无 clean write、production DB 不变可由现有证据支持；但 B4-4「severe 阻断 clean write」没有被 Phase 4 validation evidence 直接证明。同时，MASTER / implement manifest 将 Phase 4 绑定到 `DataQualityValidator` 与 `SourceConflictValidator`，但 `backend/app/ops/live_pilot.py` 的 Phase 4 路径没有引用这两个 validator，当前 `phase4_validation_report.json` 与 `phase4_conflict_inspect.txt` 是自定义 raw-structure / informational sidecar 检查产物，不能等价证明 manifest 要求的 validator / severe gate 路径。

## B4 Checklist

| Item                                 | 结论             | 审计判断                                                                                                                                                                                                                                                               |
| ------------------------------------ | ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| B4-1 validation report on raw        | PASS with caveat | `phase4_validation_report.json` 存在，包含三个 pilot request 的 raw validation 结果；Request 1/3 为 `PASSED`，Request 2 为 `SOURCE_ENDPOINT_FAILURE`。Caveat: report 未体现 `DataQualityValidator` 的 `validation_report` / `quality_flags` / `can_write_clean` 形态。 |
| B4-2 conflict inspect 或 no-conflict | PASS with caveat | `phase4_conflict_inspect.txt` 存在，明确 Request 2 Sina sidecar comparison 仅为 informational/candidate，不关闭原 Eastmoney request。Caveat: 当前 inspect 不是 `SourceConflictValidator` / `source_conflict_rules.yaml` 路径产物。                                     |
| B4-3 默认无 clean write              | PASS             | `phase4_validation_report.json` 顶层 `allow_clean_write=false`, `clean_write_performed=false`；每个 validation item `allow_clean_write=false`；`8.6-green.txt` 记录 phase4 pytest PASS。                                                                               |
| B4-4 severe 阻断 clean write         | FAIL             | Phase 4 report 没有 severity / severe / `can_write_clean=false` 字段，也没有制造或读取 open severe `source_conflict` 的阻断证据。仓库中存在 severe block 规则与 gate 代码，但本 PH-B4 artifact 未证明 Phase 4 使用该路径。                                             |
| B4-5 production DB 仍不变            | PASS             | `phase4_no_production_mutation_proof.md` 与 report 内 `production_mutation_proof` 均显示 `db_hash_unchanged=true`、`row_counts_unchanged=true`；关键表 counts 前后一致。                                                                                               |

## 证据路径

- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/AUDIT.plan.md`
- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/audit.jsonl`
- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/MASTER.plan.md`
- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/implement.jsonl`
- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/research/gitnexus-audit-summary.md`
- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/execute-evidence/phase4_validation_report.json`
- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/execute-evidence/phase4_conflict_inspect.txt`
- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/execute-evidence/phase4_no_production_mutation_proof.md`
- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/execute-evidence/8.6-green.txt`
- `specs/contracts/data_quality_rules.yaml`
- `specs/contracts/source_conflict_rules.yaml`
- `specs/contracts/write_contract.yaml`
- `backend/app/validators/data_quality.py`
- `backend/app/validators/source_conflict.py`
- `backend/app/db/validation_gate.py`
- `backend/app/ops/live_pilot.py`
- `tests/test_batch275_live_pilot_gate.py`
- `tests/test_source_conflict_validator.py`

## Manifest 条目审计

- `implement.jsonl` includes `specs/contracts/data_quality_rules.yaml` for AC-P4 validation severity and `backend/app/validators/data_quality.py` for AC-P4 validation report shape.
- `implement.jsonl` includes `docs/modules/data_validation_and_conflict.md`, `specs/contracts/write_contract.yaml`, `backend/app/validators/source_conflict.py`, and `specs/contracts/source_conflict_rules.yaml` for AC-P4/AC-P4-5 clean-write and conflict behavior.
- `MASTER.plan.md` Source Context Index marks `data_quality_rules.yaml`, `data_quality.py`, `write_contract.yaml`, `source_conflict.py`, and `source_conflict_rules.yaml` as must-read originals for AC-P4 / AC-P4-5.
- `MASTER.plan.md` §4 code map states `backend/app/validators/data_quality.py` is called in Phase 4 and `backend/app/validators/source_conflict.py` is called for AC-P4-5.
- `audit.jsonl` contains `source_conflict_rules.yaml` and `backend/app/validators/source_conflict.py`, but does not contain `data_quality_rules.yaml` or `backend/app/validators/data_quality.py`; data_quality manifest coverage had to be recovered from MASTER / implement manifest rather than the audit manifest itself.

## 发现项

| Severity | ID    | Finding                                                                                                                                                                                                                                                                                                                                                                                   |
| -------- | ----- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| HIGH     | B4-F1 | B4-4 is not proven by Phase 4 evidence. `source_conflict_rules.yaml` defines `severe_diff: block_write_and_create_reconcile_job`, and `DbValidationGate` rejects open severe `source_conflict`; however `phase4_validation_report.json` contains no severity / severe / `can_write_clean` evidence and Phase 4 generated no severe-block artifact.                                        |
| HIGH     | B4-F2 | Phase 4 implementation evidence does not match MASTER / implement manifest claims that Phase 4 calls `DataQualityValidator` and `SourceConflictValidator`. `backend/app/ops/live_pilot.py` has no references to `DataQualityValidator`, `SourceConflictValidator`, `data_quality`, or `source_conflict`; it performs local structure checks and informational sidecar comparison instead. |
| MEDIUM   | B4-F3 | Audit manifest coverage is incomplete for PH-B4 validation: `audit.jsonl` lists source_conflict entries but omits the data_quality contract / validator entries that MASTER and implement manifest bind to AC-P4.                                                                                                                                                                         |
| LOW      | B4-F4 | `execute-evidence/8.6-red.txt` is absent while MASTER §8.6 declares it as RED evidence. This is not the direct B4-1..B4-5 failure, but it weakens Execute evidence completeness around Phase 4.                                                                                                                                                                                           |

## GitNexus 可用性限制

`research/gitnexus-audit-summary.md` records that live GitNexus MCP resources were not exposed in this Codex session, and `node .gitnexus/run.cjs status` failed under the network sandbox with npm registry `EACCES`. Therefore I could not run live `query()`, `impact()`, or `detect_changes()` for this PH-B4 audit. I used the frozen local index facts from the summary, the Execute GitNexus summary, manifest/source reads, tests, and Phase 4 evidence files. Any conclusion that would require a fresh live GitNexus graph query remains limited by that availability gap.
