# Batch 3H Hardening Rules

## 1. All target sources before Round4

Round4 productization is blocked until Batch 3H proves that every target source in `source_registry.yaml` / `source_capabilities.yaml` has a final production-entry decision.

A final decision is either:

- `READY_WITH_EVIDENCE`: adapter/gate/replay/route/evidence exists; or
- `ADR_DISABLED_OUT_OF_SCOPE`: the source is explicitly removed from the current product promise, remains disabled, and is listed as a release limitation.

It is not acceptable to complete only one sample source family and leave the rest as vague proposed-disabled work.

## 2. Adapter enablement rule

A source can move from `DISABLED_SOURCE` to `READY` only when all are true:

1. QMD-owned adapter or fetch port exists.
2. Auth/license decision is recorded.
3. ResourceGuard limits symbol/series/window/row count.
4. SourceRoutePlan has READY and negative DISABLED tests.
5. Replay fixture or sandbox sample exists.
6. fetch_log, content_hash, schema_hash, source_fetch_id are written.
7. Data health and source conflict checks run.
8. Layer evidence binding is tested where the source feeds Layer1–5.

## 3. No micro-slice closure

Adding one registry field, one source note, one capability declaration, or one disabled route test is not a completion unit. Each R3H task must close every source it owns to `READY_WITH_EVIDENCE` or `ADR_DISABLED_OUT_OF_SCOPE`.

## 4. Source class boundaries

- Official/regulator/filing sources may become factual primary candidates after gates.
- Aggregators are validation/fallback unless a contract explicitly marks them primary for a domain.
- Prediction markets output probability signals only.
- Web search outputs evidence/manual_review only.
- CN validation sources must not silently replace baostock/CNINFO/QMT authorized primary roles.

## 5. Production caps

No R3H task may default to full market, full history, minute-level scans, full option-chain scans, account-control APIs, or trading actions.
