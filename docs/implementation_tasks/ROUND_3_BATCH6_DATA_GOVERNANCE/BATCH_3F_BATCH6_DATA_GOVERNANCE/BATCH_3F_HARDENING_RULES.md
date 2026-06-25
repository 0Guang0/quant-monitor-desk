# Batch 3F Hardening Rules

> Applies to every Round 3F / Batch6 task and follow-up Trellis issue.

---

## 1. Planning source-of-truth rule

`PROJECT_IMPLEMENTATION_ROADMAP.md` Round 3F is the forward plan. Older map files, registries, and pending-fix lists are inputs for reconciliation, not competing batch plans.

If a registry and RESOLVED registry disagree, do not guess. Create a registry reconciliation task and cite exact evidence.

---

## 2. Production-safety rule

Batch 3F must not enable production clean write or production-live defaults. It may prepare gates, runbooks, migrations, and tests needed before Round 3G.

---

## 3. Live-source rule

Live source work requires explicit user authorization. `B2.5-O-05` can close only with FRED-only live primary evidence and sandbox/no-production-mutation proof. Batch 01 FRED sandbox evidence is not enough.

---

## 4. Validation-source rule

AkShare remains validation-only. `R3-B2.75-REQ2-EM` and `R3-PROMPT14-AKSHARE-VAL-01` must not be closed by TDX, Sina, or unrelated sidecar evidence.

---

## 5. Already-resolved rule

Do not reimplement or reopen resolved items (`R3-PARTIAL-5`, `R2-RISK-3`, `R3-AUDIT-DEF-03`) unless a regression test proves they are no longer valid. Otherwise handle only registry/document consistency.

---

## 6. Test-quality rule

New/changed tests must state coverage scope, test object, and purpose. Gate tests must verify behavior and business constraints, not only file existence.
