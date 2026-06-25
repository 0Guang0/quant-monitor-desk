# Batch Folder Rehome Plan

> **Purpose:** normalize future unfinished task cards into one-batch-one-folder packages without silently invalidating historical task cards.  
> **Authority:** `PROJECT_IMPLEMENTATION_ROADMAP.md` remains the forward-planning SSOT. This file is an implementation-tasks maintenance plan.

---

## 1. Rule going forward

Every unfinished executable batch should have a canonical folder:

```text
docs/implementation_tasks/<ROUND_OR_THEME>/<BATCH_ID>/
```

Each canonical batch folder should contain:

```text
README.md
BATCH_*_TASK_CARD_MANIFEST.md
BATCH_*_COORDINATOR_PLAYBOOK.md   # or explicit no-playbook note
BATCH_*_HARDENING_RULES.md        # or explicit inherited-rules note
individual task cards
```

Loose historical task cards may remain temporarily, but they must be treated as historical inputs once a canonical batch folder exists.

---

## 2. Current canonical packages

| Batch      | Canonical folder                                                              | Status                                  |
| ---------- | ----------------------------------------------------------------------------- | --------------------------------------- |
| Batch 3F   | `ROUND_3_BATCH6_DATA_GOVERNANCE/BATCH_3F_BATCH6_DATA_GOVERNANCE/`             | completed, historical/evidence input    |
| Batch 3F-R | `ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/`  | current executable package              |
| Batch 3G   | `ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/`                   | future package, blocked by 3F-R         |
| Batch 04   | `ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/` | future canonical productization package |
| Batch 05   | `ROUND_5_INTEGRATION_RELEASE/BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE/`       | future canonical release package        |

---

## 3. Rehome order

Do not move/delete all loose files in one change. Use staged migration:

1. Add canonical batch package.
2. Update `docs/implementation_tasks/README.md` inventory.
3. Update `PROJECT_IMPLEMENTATION_ROADMAP.md` entrypoint and ordering.
4. Mark loose task cards as historical inputs or add redirect notes.
5. Only later remove loose task cards if tests/docs references are updated.

---

## 4. First loose-card groups to rehome or redirect

### Round 4

Loose cards:

```text
ROUND_4_API_FRONTEND_AGENT_BACKTEST/024_implement_fastapi_routes.md
ROUND_4_API_FRONTEND_AGENT_BACKTEST/025_implement_agent_tool_layer.md
ROUND_4_API_FRONTEND_AGENT_BACKTEST/026_implement_frontend_shell.md
ROUND_4_API_FRONTEND_AGENT_BACKTEST/027_implement_frontend_layer_pages.md
ROUND_4_API_FRONTEND_AGENT_BACKTEST/028_implement_reports_and_notifications.md
ROUND_4_API_FRONTEND_AGENT_BACKTEST/029_implement_backtest_and_review.md
ROUND_4_API_FRONTEND_AGENT_BACKTEST/030_implement_no_action_semantics_guard.md
```

Canonical destination:

```text
ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/
```

Important: `029_implement_backtest_and_review.md` must be updated or redirected so future execution sees the roadmap §1.4 requirement to adapt JQ2PTrade/EasyXT instead of designing from scratch.

### Round 5

Loose cards:

```text
ROUND_5_INTEGRATION_RELEASE/031_implement_integration_smoke_tests.md
ROUND_5_INTEGRATION_RELEASE/032_implement_resource_limit_tests.md
ROUND_5_INTEGRATION_RELEASE/033_implement_security_and_boundary_tests.md
ROUND_5_INTEGRATION_RELEASE/034_implement_docs_consistency_check.md
ROUND_5_INTEGRATION_RELEASE/035_implement_final_package_cleanup.md
ROUND_5_INTEGRATION_RELEASE/036_create_final_release_manifest.md
```

Canonical destination:

```text
ROUND_5_INTEGRATION_RELEASE/BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE/
```

---

## 5. Do not rehome historical completed rounds now

Do not move Round 0, Round 1, Round 2, Round 2.6, Round 3 modeling, Round 3 data production readiness, or completed 3V/3F historical evidence cards in this maintenance pass. They are already cited by tests/docs/registries and moving them now would create avoidable reference churn.

---

## 6. Acceptance for a rehome PR

A rehome PR must prove:

- root roadmap and implementation README agree on the current executable entrypoint;
- all canonical batch packages have README files;
- no active future task exists only as a loose card without a canonical batch pointer;
- tests or static checks that reference task paths are updated;
- no historical evidence path is deleted without a redirect or ADR.
