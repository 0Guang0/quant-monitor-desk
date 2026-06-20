# A5 audit-completion — trace-ac, sandbox, evidence spot-check

**Overall A5 verdict: PASS** (post-repair)

## trace-ac

All AC ≥4 after repair. Previously failing AC-017-5, AC-LINEAGE-1, AC-LINEAGE-4 closed via engineering rules validation, full lineage field test, agent_outputs guard.

## cli-sandbox

`QMD_DATA_ROOT=.audit-sandbox/r3b2-audit/data` → **33 passed** (layer1 suite).

## audit-prod-path

Copy `data/` → `.audit-sandbox/r3b2-audit-prod-equiv/data` → **33 passed**.

| Field              | Value                                                              |
| ------------------ | ------------------------------------------------------------------ |
| Prod SHA256 before | `5EB65E0EDAAAB223A77C5A5D2660603383836704B4C0ECE1EB4AEBB047F1682E` |
| Prod SHA256 after  | `5EB65E0EDAAAB223A77C5A5D2660603383836704B4C0ECE1EB4AEBB047F1682E` |
| Unchanged          | **true**                                                           |

## Evidence spot-check

| File            | Real?               |
| --------------- | ------------------- |
| `8.2-green.txt` | Yes — pytest output |
| `8.5-green.txt` | Yes — pytest output |

**§4.3 count: 0 open**
