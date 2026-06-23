# R3Y-AUD-03 — Write / validation / conflict

**Result: WARN**

Clean write via WriteManager + DbValidationGate. Documented bypass in `register_staged_file_registry_rows`; reconcile path skips full ValidationGate.

Evidence: `backend/app/db/validation_gate.py`, `backend/app/storage/staged_evidence.py`, `backend/app/layer1_axes/ingestion_commit.py`
