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
- Top-level YAML keys `shadow_source` / `emergency_source` → `LegacyRoleError`
- Role fields `Shadow` / `Emergency` → `LegacyRoleError`

**Tests:** `tests/test_source_registry.py` + `tests/fixtures/bad_*.yaml`

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
