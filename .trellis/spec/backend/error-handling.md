# Error Handling

> How errors are handled in this project.

---

## Overview

<!--
Document your project's error handling conventions here.

Questions to answer:
- What error types do you define?
- How are errors propagated?
- How are errors logged?
- How are errors returned to clients?
-->

(To be filled by the team)

---

### SourceRegistry loader validation (Batch A)

**Load-time checks in `_validate_domain_roles`:**

- Primary source must exist, be enabled, and not have `license_type: unknown`
- Primary `allowed_domains` must include the bound `data_domain`
- Validation source (if set): enabled, license known, domain allowed
- Top-level YAML keys `shadow_source` / `emergency_source` → `LegacyRoleError`
- Role fields `Shadow` / `Emergency` → `LegacyRoleError`
- YAML booleans must be native YAML boolean (not `"false"` strings)

### BaseDataAdapter fetch guards

- `req.source_id != adapter.source_id` → `SourceMismatchError` (pre-impl, 0 fetch_log rows)
- `FetchResult` Pydantic validators enforce status/evidence contract before persist

**Tests:** `tests/test_source_registry.py` + `tests/test_data_adapter_contract.py`

---

## Error Types

<!-- Custom error classes/types -->

(To be filled by the team)

---

## Error Handling Patterns

<!-- Try-catch patterns, error propagation -->

(To be filled by the team)

---

## API Error Responses

<!-- Standard error response format -->

(To be filled by the team)

---

## Common Mistakes

<!-- Error handling mistakes your team has made -->

(To be filled by the team)
