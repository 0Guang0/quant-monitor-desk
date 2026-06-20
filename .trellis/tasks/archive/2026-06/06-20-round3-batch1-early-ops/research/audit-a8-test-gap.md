# A8 audit-test-gap — §3.8

**Dimension:** A8 (audit-test-gap)  
**Skills:** testing-guidelines + doubt-driven-development  
**Environment:** `pytest --basetemp .audit-sandbox/r3b1-audit/pytest` (audit-sandbox isolated)  
**Verdict: PASS**

---

## 1. Mandatory reads completed

| Source                        | Takeaway                                                                    |
| ----------------------------- | --------------------------------------------------------------------------- |
| `implement.jsonl`             | Execute scope: `db_inspector.py`, `qmd_ops.py`, contract + registry closure |
| `audit.jsonl`                 | Audit entry points: contract, Phase A doc, registries, production_gate      |
| `AUDIT.plan.md` §2 A8         | Boundary tests: `--limit` hard cap, path outside `data_root` rejected       |
| `MASTER.plan.md` §7 Red Flags | Mutation, unbounded scan, QMT enable, scope creep — test mapping below      |
| `gitnexus-audit-summary.md`   | LOW blast radius; ops inspect path only                                     |
| `audit-boot.md`               | Sandbox `QMD_DATA_ROOT=.audit-sandbox/r3b1-audit/data`; handoff validated   |

---

## 2. Required boundary tests — existence & meaningfulness

### `test_dbInspect_limit_hardCapsAtContractMaximum`

| Criterion  | Assessment                                                                               |
| ---------- | ---------------------------------------------------------------------------------------- |
| Exists     | Yes (Execute + Audit)                                                                    |
| Contract   | `hard_cap: 100` in `ops_db_inspect_contract.yaml`                                        |
| Behavior   | 110 files under `data/raw`, `limit=500` → `raw_files_count==100`, `scan_limited==True`   |
| Meaningful | **Yes** — proves `min(max(limit,1),100)` upper bound and `_count_files_under` early stop |

### `test_dbInspect_pathOutsideDataRoot_rejectedFromScan`

| Criterion  | Assessment                                                                                                                                                              |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Exists     | Yes                                                                                                                                                                     |
| Contract   | `db_inspect_cli.md`: path scan must stay inside configured data root                                                                                                    |
| Behavior   | 5 `.parquet` files only under `tmp/outside-secrets`; counts remain 0                                                                                                    |
| Meaningful | **Yes** (after fix) — originally had weak tautology `outside not in data_root.path`; strengthened with sanity glob + explicit `path`/`exists`/`scan_limited` assertions |

Complement: `test_dbInspect_pathScan_staysUnderDataRoot` covers mixed inside/outside (1 raw inside, secret outside) — good overlap, not redundant.

---

## 3. Audit repairs (this run)

| ID    | Change                                                          | Rationale                                                                                                         |
| ----- | --------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| A8-01 | **Fixed** `test_dbInspect_pathOutsideDataRoot_rejectedFromScan` | Removed tautological path substring check; added outside-file sanity + `scan_limited is False`                    |
| A8-02 | **Added** `test_dbInspect_limit_floorClampsToMinimumOne`        | Lower bound: `limit=0` → clamp to 1 file, `scan_limited=True` (5 files present)                                   |
| A8-03 | **Added** `test_qmdOps_cli_limitHardCapsAtContractMaximum`      | CLI `--limit 500` end-to-end through `qmd_ops db-inspect` (API-only cap test was insufficient for `--limit` flag) |

---

## 4. Pytest evidence (audit-sandbox)

**Command:**

```text
python -m pytest tests/test_ops_db_inspector.py -q --basetemp .audit-sandbox/r3b1-audit/pytest
```

**Output:**

```text
............                                                             [100%]
12 passed in 2.38s
```

Prior Execute baseline: 10 passed. Audit adds 2 net tests + 1 assertion fix.

---

## 5. MASTER §7 Red Flags — adversarial coverage map

| Red Flag                        | Test coverage                                                                                                                                      | Gap                                                                                                               |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| 调用 writer/migration           | `test_dbInspect_dbFile_unchanged` (byte-identical DB after inspect)                                                                                | None for Phase A                                                                                                  |
| 实现 source probe / data health | No probe code in ops module; A1 scope check                                                                                                        | N/A — negative by design                                                                                          |
| 在 inspect 中启用 QMT           | No `--enable-qmt` in `qmd_ops.py`; forbidden in contract                                                                                           | **Low:** no CLI negative test for forbidden flags in this file                                                    |
| 全表扫描 raw/parquet 无 limit   | `test_dbInspect_limit_hardCapsAtContractMaximum`, `test_qmdOps_cli_limitHardCapsAtContractMaximum`, `test_dbInspect_limit_floorClampsToMinimumOne` | **Low:** cap exercised on `raw/` only; `parquet/audit/report` subdirs share `_count_files_under` — same code path |
| 把 docs 当实现路径              | Scaffold/contract tests elsewhere                                                                                                                  | N/A here                                                                                                          |
| 合并 017 axis loader            | Out of batch scope                                                                                                                                 | N/A                                                                                                               |
| R3-PARTIAL-2 live vendor 无授权 | `test_vendor_fetch_e2e.py` (separate AC)                                                                                                           | N/A in inspector suite                                                                                            |

**Boundaries still not covered (documented, not §4.3 blockers):**

1. `include_path_check=False` — skips scan (contract flag); eco default is enabled.
2. Symlink escape under `data_root` — doc says no arbitrary traversal; no symlink fixture test (OS/portability risk).
3. Forbidden CLI flags (`--enable-qmt`, `--full-scan`) — contract forbids; no argparse rejection test in this module.

These are **medium/low** priority; none violate Phase A safety invariants given static A3 review.

---

## 6. §4.3 Repair items

| Item                                       | Status                               |
| ------------------------------------------ | ------------------------------------ |
| Missing `--limit` cap boundary test        | **Resolved** — API + CLI tests green |
| Missing path-outside-`data_root` rejection | **Resolved** — exists + strengthened |
| Weak assertion in path-outside test        | **Resolved** — A8-01 fix             |
| CLI vs API limit parity                    | **Resolved** — A8-03                 |

**§4.3 remaining: None.** No open repair items for A9 synthesis.

---

## 7. Test inventory (`tests/test_ops_db_inspector.py`)

| #   | Test                                                  | Category                          |
| --- | ----------------------------------------------------- | --------------------------------- |
| 1   | `test_dbInspect_missingDb_returnsFail`                | Error path                        |
| 2   | `test_dbInspect_deferredItemMapping_nonEmpty`         | Contract shape                    |
| 3   | `test_dbInspect_dbFile_unchanged`                     | Red Flag: no mutation             |
| 4   | `test_dbInspect_emptySchemaDb_returnsWarn`            | Status derivation                 |
| 5   | `test_dbInspect_outputJsonShape_hasRequiredFields`    | JSON contract                     |
| 6   | `test_dbInspect_fixtureWithEvidence_reportsCounts`    | Evidence block                    |
| 7   | `test_dbInspect_pathScan_staysUnderDataRoot`          | Path boundary (mixed)             |
| 8   | `test_dbInspect_limit_hardCapsAtContractMaximum`      | Limit upper cap (API)             |
| 9   | `test_dbInspect_pathOutsideDataRoot_rejectedFromScan` | Path boundary (outside only)      |
| 10  | `test_dbInspect_limit_floorClampsToMinimumOne`        | Limit lower clamp **(Audit)**     |
| 11  | `test_qmdOps_cli_limitHardCapsAtContractMaximum`      | Limit upper cap (CLI) **(Audit)** |
| 12  | `test_qmdOps_cli_invokesSameInspector`                | CLI integration                   |

---

## 8. Code changes summary

**File:** `tests/test_ops_db_inspector.py`

- Strengthened `test_dbInspect_pathOutsideDataRoot_rejectedFromScan` assertions.
- Added `test_dbInspect_limit_floorClampsToMinimumOne`.
- Added `test_qmdOps_cli_limitHardCapsAtContractMaximum`.

No production code changes required.
