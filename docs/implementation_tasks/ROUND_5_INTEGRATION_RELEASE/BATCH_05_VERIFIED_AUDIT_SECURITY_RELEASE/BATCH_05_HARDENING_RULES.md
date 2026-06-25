# Batch 05 Hardening Rules

## 1. Canonical batch authority

Batch 05 execution should start from:

- `PROJECT_IMPLEMENTATION_ROADMAP.md` → Round 5+
- `docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE/README.md`
- `BATCH_05_TASK_CARD_MANIFEST.md`
- this hardening rules file

Loose `031`–`036` cards are historical inputs until rehomed into canonical `B05_*` cards.

## 2. Security/release gate boundary

Batch 05 may add or harden CI/release gates. It must not implement product features that belong to Round 3G or Round4.

Forbidden:

- enabling production-live sources
- enabling production clean write
- expanding source/domain/symbol/window caps
- hiding unresolved registry items in release packaging
- deleting historical evidence paths without redirect

## 3. Integration and resource smoke boundary

Integration/resource tests must be bounded:

- no full-market scan
- no full-history scan
- no minute-level default scan
- no uncontrolled network/live source access
- tests must state caps and failure meaning

## 4. Documentation consistency boundary

Docs consistency checks must respect the new hierarchy:

```text
PROJECT_IMPLEMENTATION_ROADMAP.md = forward planning SSOT
docs/implementation_tasks/README.md = task inventory / entrypoint index
batch folders = canonical execution packages
loose task cards = historical inputs unless marked active
```

## 5. Release manifest boundary

Final release manifest must include:

- current production posture
- source enablement posture
- clean-write status
- unresolved/deferred registry status
- test command evidence
- package contents
- reference adoption status if 3F-R is not fully complete

## 6. Acceptance

Batch 05 cannot close unless:

- security CI gate is documented and runnable;
- resource/integration smoke tests are bounded;
- release manifest does not overstate production readiness;
- historical evidence is preserved or redirected;
- loose-card/canonical-folder status is consistent in README and roadmap.
