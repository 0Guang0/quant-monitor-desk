# PROMPT_08 — feature/round3-023a-evidence-foundation

Use this prompt in a fresh session. The session must create the branch/worktree first, then execute the 023A foundation slice.

## 1. Branch / worktree setup

- Branch to create: `feature/round3-023a-evidence-foundation`
- Base branch: `master` after `integration/round3` has merged, or `integration/round3` if explicitly instructed before merge-back
- Suggested worktree path: `../quant-monitor-desk-wt-round3-023a-evidence-foundation`
- Target merge branch: `integration/round3`

Before creating the branch, confirm:

- `R3-B3-STAGED-DOWNSTREAM-GATE` is closed in the chosen base.
- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/023A_layer5_evidence_foundation.md` exists.
- If `feature/round3-019-layer2-sensor` is active, only one branch owns `specs/contracts/snapshot_lineage_contract.yaml`.

## 2. Mission

Implement the minimal Layer5 evidence foundation needed by Layer2-4 without implementing full Layer5.

Scope:

- evidence identity
- instrument/evidence reference shape
- source fetch IDs and content hashes
- manual-review flags
- Agent-text-not-fact-source tests
- compatibility with snapshot lineage contract

## 3. Required Plan-stage input index

Read and summarize before writing a plan:

- `AGENTS.md`
- `CLAUDE.md`
- `.trellis/workflow.md`
- `.trellis/spec/guides/complex-task-planning-protocol.md`
- `.trellis/spec/guides/round3-repair-debt-worktree-plan.md`
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md`
- `docs/implementation_tasks/ROUND_3_MODELING_LAYERS/023A_layer5_evidence_foundation.md`
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

## 4. Allowed files

Only after plan approval:

- `backend/app/layer5_evidence/`
- `tests/test_layer5_evidence_foundation.py`
- `specs/contracts/layer5_evidence_contract.yaml`
- `specs/contracts/snapshot_lineage_contract.yaml` only if this branch is contract owner
- task-local Trellis plan/evidence files

## 5. Forbidden files / behavior

- No full `023` implementation.
- No broad bars/events/financials/valuation ingestion.
- No production DB mutation.
- No source/network fetch.
- No trading/order semantics.
- No Agent text as fact source.
- No snapshot lineage contract edit if 019 owns it.
- No public cross-layer API without contract/ADR note.

## 6. Required safeguards

- Start with RED tests for Agent-text-not-fact-source and manual-review behavior.
- Evidence records must distinguish raw factual evidence, derived validation status, and Agent interpretation.
- Every evidence identity must be traceable to fetch IDs or content hashes.
- Manual-review queue/severity semantics must be explicit or deferred with `R3-PARTIAL-4` reference.
- If adapter/storage decoupling appears necessary, handle via port injection or explicit `R2-RISK-2` re-deferral.

## 7. Verification commands

- `pytest tests/test_layer5_evidence_foundation.py -q` if created
- `pytest tests/test_unresolved_item_task_coverage.py -q`
- `pytest tests/test_round3_audit_registry_alignment.py -q`
- `pytest tests/test_trellis_audit_trace_authority.py -q`
- `python -m compileall backend/app/layer5_evidence tests`
- `ruff check backend/app/layer5_evidence tests/test_layer5_evidence_foundation.py` if code changed
- `python scripts/check_doc_links.py` if docs changed

## 8. Done criteria

- 023A remains a minimal foundation slice.
- Full 023 work is explicitly deferred.
- Agent-text-not-fact-source and manual-review behavior are tested or explicitly re-deferred.
- No production DB/source fetch occurred.
- Merge report includes core file ownership and compatibility statement for 019/020/021.
