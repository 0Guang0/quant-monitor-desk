# Execute Boot — 06-22-round3-023a-evidence-foundation

## AC 摘要（来自 MASTER §1）

- evidence identity + instrument ref + fetch/hash provenance
- manual-review flags + Agent-text-not-fact-source tests
- Layer5 lineage compatible with snapshot contract (read-only)

## §8 执行顺序

8.1 provenance → 8.2 agent-not-fact → 8.3 manual-review → 8.4 lineage

## Red Flags

- No full 023 / no production DB / no network fetch
- No snapshot_lineage_contract.yaml edits (019 owner)

## §10 验收命令清单

- pytest tests/test_layer5_evidence_foundation.py -q
- pytest tests/test_unresolved_item_task_coverage.py -q
- pytest tests/test_round3_audit_registry_alignment.py -q
- pytest tests/test_trellis_audit_trace_authority.py -q
- ruff check backend/app/layer5_evidence tests/test_layer5_evidence_foundation.py

## Phase 0

- implement.jsonl 全读（MASTER.plan.md）
- staged-only / 023A foundation scope confirmed
- 基线 pytest gate matrix green

**Phase 0 complete**
