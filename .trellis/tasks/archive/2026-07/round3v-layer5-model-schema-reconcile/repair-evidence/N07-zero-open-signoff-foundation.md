# N07 — Zero-open signoff foundation (6) row

**Status:** CLOSED

**Finding:** `repair-evidence/zero-open-signoff.md` VR closure listed only `test_layer5_evidence_chain.py` (7); omitted explicit `test_layer5_evidence_foundation.py` (6) row despite matrix §1 and DEBT.plan L5-02 requiring both.

**Action:** Added foundation (6) closure row to zero-open-signoff §VR closure; aligns with `l5-reconcile-matrix.md` §1 closure test column.

**Re-run verification (2026-06-28):**

```text
uv run pytest tests/test_layer5_evidence_chain.py tests/test_layer5_evidence_foundation.py -q  → 13 passed (7 chain + 6 foundation)
```
