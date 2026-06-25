# Research: Layer5 evidence chain vs audit VR-L5-001

- **Query**: Cross-check Layer5 runtime/tests vs `VR-L5-001` post `376e30e6`
- **Scope**: internal (GitNexus + codebase-memory)
- **Date**: 2026-06-25

## Findings

### Files Found

| File Path                                            | Description                         |
| ---------------------------------------------------- | ----------------------------------- |
| `backend/app/layer5_evidence/evidence_chain.py`      | 023b chain builder (staged)         |
| `backend/app/layer5_evidence/foundation.py`          | Provenance + agent-text guards      |
| `backend/app/layer5_evidence/lineage.py`             | Layer5 lineage envelope builder     |
| `backend/app/layer5_evidence/evidence_validator.py`  | Staged bar validation               |
| `backend/app/layer5_evidence/instrument_registry.py` | Registry validator                  |
| `backend/app/layer5_evidence/ports.py`               | `EvidenceReadPort` DI boundary      |
| `tests/test_layer5_evidence_chain.py`                | 7 tests — chain AC                  |
| `tests/test_layer5_evidence_foundation.py`           | 6 tests — foundation + lineage hash |
| `docs/AUDIT_DEFERRED_REGISTRY.md`                    | `R3-TASK-023` RESOLVED @ `376e30e6` |

### Code Patterns

- `EvidenceChainBuilder.build` validates foundation record, requires non-empty `upstream_snapshot_ids` and L3/L4 context strings (`evidence_chain.py:37-70`).
- Severe conflict forces `manual_review_state=QUEUED` (`evidence_chain.py:91-97`).
- `reject_agent_text_as_fact` delegates to `EvidenceFoundationValidator.reject_agent_text_as_fact_source` (`evidence_chain.py:168-170`).
- Lineage uses shared `LINEAGE_REQUIRED_FIELDS` from `snapshot_lineage_contract` (`lineage.py:7-14`).

### GitNexus vs codebase-memory

| Tool                                     | Result                                                                 |
| ---------------------------------------- | ---------------------------------------------------------------------- |
| GitNexus `query`                         | Returned foundation/lineage definitions; process ranking weak for L5   |
| GitNexus `context(EvidenceChainBuilder)` | **Symbol not found** — index stale                                     |
| codebase-memory `search_code`            | **Found** `EvidenceChainBuilder` @ `evidence_chain.py:23`, in_degree 5 |

**裁定:** Trust codebase-memory + direct file read; refresh GitNexus before Execute edits (`BLK-L5R-04`).

### External References

- Task card `B03_01` §2 `VR-L5-001` checklist
- `PROJECT_IMPLEMENTATION_ROADMAP.md` `R3V-B03-L5-01`

### Related Specs

- `specs/contracts/layer5_evidence_contract.yaml`
- `specs/contracts/snapshot_lineage_contract.yaml`

## Caveats / Not Found

- Full verified audit PDF not in repo — only `quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` routing row.
- `tests/test_migration_coverage.py` not applicable to VR-L5-001 closure (MODEL track).
- Production DB write path for evidence chain **not** implemented — intentional staged scope.
