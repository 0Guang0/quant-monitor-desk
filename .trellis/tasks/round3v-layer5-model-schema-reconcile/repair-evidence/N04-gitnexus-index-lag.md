# N04 — GitNexus index lag (EvidenceChainBuilder)

**Status:** CLOSED (reconcile-only; no runtime edit)

**Finding:** `BLK-L5R-04` — GitNexus `context(EvidenceChainBuilder)` miss vs codebase-memory hit.

**Resolution:** Reconcile used direct file read + pytest; staged runtime verified post `376e30e6`. No `layer5_evidence/**` edits on this branch (boundary honored).

**Matrix row:** `research/l5-reconcile-matrix.md` §2 VR-L5-001 capability matrix — all closure capabilities **implemented (staged)** with test pointers.

**Evidence:** `execute-evidence/b03-l5-02-pytest.txt` — 13 passed (`test_layer5_evidence_chain` + `test_layer5_evidence_foundation`).
