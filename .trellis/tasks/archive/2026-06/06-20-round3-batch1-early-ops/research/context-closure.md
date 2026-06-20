# Context Closure (E16) — Round 3 Batch 1 Early Ops

> L2 upstream impact for MASTER §4/§6 touchpoints

| Touchpoint                                   | impact(upstream)                       | Risk | Execute action                          |
| -------------------------------------------- | -------------------------------------- | ---- | --------------------------------------- |
| `ConnectionManager.reader`                   | 1 direct caller (`ci_ingestion_smoke`) | LOW  | Read-only consumer only; no edit        |
| `backend/app/db/sql_identifiers.quote_ident` | Used by validators/write_manager       | LOW  | Use for key_tables COUNT queries        |
| `scripts/production_equivalent_smoke.py`     | Standalone smoke                       | LOW  | Run only in §8.5; no edit unless broken |
| `scripts/qmd_ops.py`                         | **New**                                | LOW  | Create transitional CLI wrapper         |
| `backend/app/ops/db_inspector.py`            | **New**                                | LOW  | Core inspect implementation             |

No HIGH/CRITICAL risks. Proceed with §8.1.
