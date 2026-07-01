# Research: FINAL_AUDIT_REPORT restore-or-replace

- **Query**: VR-DOC-001 — `FINAL_AUDIT_REPORT.md` missing vs MANIFEST/README/allowlist
- **Scope**: internal (git history + manifest checker + cross-doc grep)
- **Date**: 2026-06-25

## Findings

### Current state

| Artifact                                         | State                                                                                                                       |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| Repo root `FINAL_AUDIT_REPORT.md`                | **Missing** (0 files via glob)                                                                                              |
| `MANIFEST.json` entry                            | Present: path `FINAL_AUDIT_REPORT.md`, size 4948, sha256 `b8f003b7092c17cf023bfda067f732a031e6f46d0fb3a59d9716f73b2c2e2d1e` |
| `scripts/check_manifest_files.py`                | Exists; default run → `missing file: FINAL_AUDIT_REPORT.md` (exit 1)                                                        |
| `tests/test_manifest_files_check.py`             | Exists; expects missing report until restore (TDD baseline)                                                                 |
| `specs/contracts/release_cleanup_allowlist.yaml` | Lists `FINAL_AUDIT_REPORT.md`                                                                                               |
| `docs/quality/final_package_rules.md`            | Requires file in zip + MANIFEST                                                                                             |
| `README.md` §审计修复包                          | References `FINAL_AUDIT_REPORT.md` as imported package artifact                                                             |

### Git history

| Commit     | Event                                                                                                          |
| ---------- | -------------------------------------------------------------------------------------------------------------- |
| `416e74bc` | `docs: import repaired implementation package` — file **present** at repo root                                 |
| `e8799f3c` | `feat(round2.6): close Phase B contract gate with audit repair` — file **deleted** (`git log --diff-filter=D`) |
| `master`   | File **absent** (`git show master:FINAL_AUDIT_REPORT.md` → fatal)                                              |

### Hash verification (restore candidate)

```text
git show 416e74bc:FINAL_AUDIT_REPORT.md
→ size 4948 bytes
→ sha256 b8f003b7092c17cf023bfda067f732a031e6f46d0fb3a59d9716f73b2c2e2d1e
```

**Matches `MANIFEST.json` exactly** — restore path is viable without MANIFEST row edits.

### Replace path (alternative)

`docs/quality/quant_monitor_desk_verified_audit_report_2026-06-25_v3_INDEX.md` §4 proposes archival at:

`docs/quality/audits/quant_monitor_desk_verified_audit_report_2026-06-25_v3.md`

Replace would require updating **all** of: `MANIFEST.json`, `README.md`, `final_package_rules.md`, `release_cleanup_allowlist.yaml`, `staged_acceptance_policy.md`, and any task cards referencing root `FINAL_AUDIT_REPORT.md`. **Higher blast radius** than restore.

### Recommended Plan decision

| Option                                    | Verdict       | Rationale                                                                                 |
| ----------------------------------------- | ------------- | ----------------------------------------------------------------------------------------- |
| **A. Restore** from `416e74bc`            | **Preferred** | Hash match; satisfies allowlist/MANIFEST/README without narrative change; not fabrication |
| B. Replace with verified audit v3 archive | Fallback      | Use only if restore content is rejected by coordinator (e.g. stale vs Batch 3V closeout)  |

### Execute notes (not done in Plan)

1. Restore: `git show 416e74bc:FINAL_AUDIT_REPORT.md > FINAL_AUDIT_REPORT.md`
2. Verify: `uv run python scripts/check_manifest_files.py` then `--verify-hash`
3. TDD: existing `test_manifest_files_check.py` should flip to green (no missing FINAL_AUDIT)
4. **Forbidden**: invent new audit prose to satisfy manifest

### Related Specs

- `BATCH_3V_HARDENING_RULES.md` §5 — no fake closeout artifacts
- `BATCH_3V_COORDINATOR_PLAYBOOK.md` §8.5 — Done gate `check_manifest_files.py` exit 0

## Caveats / Not Found

- Restored file is **2026-06-19 implementation-docs audit**, not Batch 3V verified audit v3 full report — acceptable for VR-DOC-001 (manifest/doc consistency), not a substitute for archiving `quant_monitor_desk_verified_audit_report_2026-06-25_v3` (separate Round 5 / quality track).
- `codebase-memory` MCP: project `quant-monitor-desk` not indexed; findings from git + filesystem only.
