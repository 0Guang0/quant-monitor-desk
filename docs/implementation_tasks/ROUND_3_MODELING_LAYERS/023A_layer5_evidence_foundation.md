# 023A_layer5_evidence_foundation — Layer5 Minimal Evidence Foundation

## 1. Round / batch / branch

| Field                | Value                                                                                                                   |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Round                | Round 3                                                                                                                 |
| Batch                | Batch 5A foundation slice, allowed immediately after Batch 3 staged gate closes                                         |
| Branch               | `feature/round3-023a-evidence-foundation`                                                                               |
| Can run in parallel? | Yes, with `feature/round3-019-layer2-sensor` after `R3-B3-STAGED-DOWNSTREAM-GATE` is closed and merged.                 |
| Must not do          | Full Layer5 implementation, broad bars/events/financials/valuation ingestion, production DB writes, or source fetching. |

## 2. Mission

Create the minimal Layer5 evidence foundation needed by Layer2-4 without implementing full `023`.

This task is a foundation slice for:

- evidence identity
- instrument identity references
- source fetch IDs
- source content hashes
- rule/code/parameter hash surfaces
- manual-review flags
- tests proving Agent text is not a fact source

## 3. Source of truth

This task is derived from:

- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/023_implement_layer5_evidence_chain.md` §16
- `docs/modules/layer5_security_evidence.md`
- `specs/contracts/layer5_evidence_contract.yaml`

It does not replace the full `023` task. Full `023` remains `feature/round3-023b-evidence-chain-full` after Layer3/4 integration readiness.

## 4. Required Plan-stage input index

Plan must read and summarize:

- `AGENTS.md`
- `CLAUDE.md`
- `.trellis/workflow.md`
- `.trellis/spec/guides/complex-task-planning-protocol.md`
- `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/023_implement_layer5_evidence_chain.md`
- `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`
- `docs/modules/layer5_security_evidence.md`
- `docs/modules/write_manager.md`
- `docs/modules/data_validation_and_conflict.md`
- `docs/modules/duckdb_and_parquet.md`
- `specs/contracts/layer5_evidence_contract.yaml`
- `specs/contracts/snapshot_lineage_contract.yaml`
- `specs/contracts/runtime_versions.md`
- `docs/implementation_tasks/GLOBAL_EXECUTION_RULES.md`
- `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`
- `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md`
- `docs/quality/staged_acceptance_policy.md`
- `docs/quality/BATCH3_STAGED_DOWNSTREAM_GATE.md`
- `docs/quality/production_live_pilot_policy.md`

If the branch touches adapter/storage boundaries, also read:

- `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md` entries `R3-PARTIAL-4` and `R2-RISK-2`
- relevant adapter/storage contracts in `specs/contracts/`

## 5. Allowed files

Allowed only after a written plan names them:

- `backend/app/layer5_evidence/`
- `tests/test_layer5_evidence_foundation.py` or narrow equivalent
- `specs/contracts/layer5_evidence_contract.yaml` only for minimal foundation additions
- `specs/contracts/snapshot_lineage_contract.yaml` only if this branch is the sole owner of that contract at the time
- task-local Trellis plan/evidence files

## 6. Forbidden files / behavior

- No full `023` Layer5 evidence chain.
- No broad security bars, futures bars, options chain, financial statements, valuation snapshots, or event registry ingestion.
- No production DB mutation.
- No source/network fetch.
- No trading/order semantics.
- No Agent text as fact source.
- No simultaneous write ownership of `specs/contracts/snapshot_lineage_contract.yaml` with `feature/round3-019-layer2-sensor`.
- No public interface consumed by multiple layers unless a mini ADR or contract decision is recorded.

## 7. Required behavior

- Evidence records must distinguish factual source evidence from Agent interpretation.
- Every evidence identity must be traceable to source fetch IDs or content hashes.
- Manual-review state must be explicit and testable.
- Snapshot lineage fields must remain compatible with Layer2/3/4.
- No future-data leakage.

## 8. Verification commands

Run relevant commands for changed files:

- `pytest tests/test_layer5_evidence_foundation.py -q` if created
- `pytest tests/test_round3_audit_registry_alignment.py -q`
- `pytest tests/test_unresolved_item_task_coverage.py -q`
- `pytest tests/test_trellis_audit_trace_authority.py -q`
- `pytest tests/test_batch3_staged_downstream_gate.py -q`
- `python scripts/check_doc_links.py`
- `ruff check backend/app/layer5_evidence tests/test_layer5_evidence_foundation.py` if code is changed
- `python -m compileall backend/app/layer5_evidence tests` if code is changed

If `uv` is unavailable, use the project-approved direct Python equivalent and record the reason.

## 9. Done criteria

- Minimal evidence foundation is implemented or explicitly planned with no broad Layer5 scope creep.
- Agent-text-not-fact-source behavior is tested.
- Manual-review flag behavior is tested.
- No production DB or source fetch occurred.
- Merge report lists changed files, allowed scope, forbidden scope honored, tests, and any remaining full-023 deferred work.
