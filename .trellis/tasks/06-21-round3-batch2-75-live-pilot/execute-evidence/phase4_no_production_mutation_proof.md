# Phase 4 — No Production Mutation Proof

- **Generated at:** 2026-06-22T12:44:00Z
- **Production DB:** `C:\Users\Guang\Desktop\quant-monitor-desk-wt-fix-r3-r3x-residual-closure\data\duckdb\quant_monitor.duckdb`
- **allow_clean_write:** false
- **can_write_clean:** false
- **clean_write_performed:** false
- **clean_write_block_reasons:** ('ALLOW_CLEAN_WRITE_FALSE_DEFAULT', 'SEVERE_FINDINGS_PRESENT')
- **declared_validation_conflict_paths:** {'data_quality_validator': 'backend.app.validators.data_quality.DataQualityValidator', 'source_conflict_validator': 'backend.app.validators.source_conflict.SourceConflictValidator', 'clean_write_gate': 'backend.app.db.validation_gate.DbValidationGate', 'data_quality_rules': 'specs/contracts/data_quality_rules.yaml', 'source_conflict_rules': 'specs/contracts/source_conflict_rules.yaml', 'write_contract': 'specs/contracts/write_contract.yaml', 'freeze_note': 'Batch 2.75 Phase 4 remains raw/sandbox validation only. Any future clean write must pass DataQualityValidator, SourceConflictValidator, and DbValidationGate; local raw structure checks cannot independently authorize clean writes.'}
- **severe_findings_block_clean_write:** True
- **db_hash_unchanged:** True
- **row_counts_unchanged:** True

