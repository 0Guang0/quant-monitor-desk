# Batch 04 Hardening Rules

## 1. Roadmap and reference-adoption authority

Batch 04 must follow:

- `PROJECT_IMPLEMENTATION_ROADMAP.md` Round 4
- R3H-05 admission: `PASS_ROUND4_REAL_DATA_READY` or `WARN_ROUND4_ALLOWED_WITH_NARROWED_SCOPE_ADR` is required before any Batch04 branch starts; `BLOCK_ROUND4_DATA_ENTRY_INCOMPLETE` blocks all Batch04 work.
- `PROJECT_IMPLEMENTATION_ROADMAP.md` §1.4 mature reference adoption rules
- `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/R3FR_04_JQ2PTRADE_BACKTEST_ADOPTION_PLAN.md`
- `docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_HARDENING_RULES.md`

If a Batch 04 implementer wants to design backtest, Agent artifact, or dashboard artifact logic from scratch, they must first write an ADR explaining why the relevant reference project cannot be adapted.

## 2. API and data boundary

- API must remain read-only unless a future explicitly-approved write endpoint exists.
- No free SQL endpoint.
- No API route may bypass `DataSourceService`, source registry/capability metadata, evidence chain, or ResourceGuard.
- API pagination, truncation, and query budget must be bounded.

## 3. Agent boundary

- Agent tools are read-only unless explicitly marked safe in the allowlist.
- Agent text is never a fact source.
- Agent must not generate executable action instructions.
- Agent must not have unrestricted DB access, filesystem access, or source fetch access.
- Agent/UI artifact design must evaluate TradingAgents, TradingAgents-astock, and agents-for-openbb before from-scratch implementation.

## 4. Frontend boundary

- Frontend route shells may render deferred states, but must not fake data.
- Frontend must use API contracts, not direct DB access.
- Error boundaries must not hide data-quality/source-health failures as success states.
- Dashboard/report artifact layout should evaluate agents-for-openbb examples where relevant.

## 5. Notification/report boundary

- Notifications must be deduplicated and bounded.
- Reports must cite QMD evidence/fetch/hash lineage where available.
- Notification/report runtime must not become a source of facts independent from QMD evidence.

## 6. Backtest/review boundary

Batch 04 backtest/review must adapt, not reinvent (R3FR-04 / B04_05 are the execution SSOT):

- JQ2PTrade `DataBundle`, bounded loader, daily replay loop shape, report separation, `api_mapping.json` deny-list
- EasyXT metric grouping (return / risk / risk-adjusted), daily result shape, analyzer boundary (architecture only)
- QMD evidence refs (`input_evidence_ids`), deterministic report hash, `no_action_semantics: true`, MIT attribution in report metadata

**Three implementation batches to full stable scope:**

1. **Batch A — read-only vertical slice:** B04_05-A..D (scenario registry, frozen loader, no-action guard, runner, report artifact).
2. **Batch B — production-complete scope:** B04_05-E, event sets, evidence-chain review, reproducibility manifests, expanded metrics (Sharpe, Calmar, win-rate, profit/loss ratio from QMD-owned series).
3. **Batch C — hardening/regression:** ResourceGuard caps, reproducibility drift tests, report limitations enforcement, API auth boundaries.

Each slice **B04_05-A** through **B04_05-E** must satisfy its **Not done if:** condition in `B04_05_backtest_review_runtime.md`.

Forbidden:

- executable user strategy code in first implementation
- broker connection
- copied JQ2PTrade execution API symbols in QMD runtime
- broad historical scan by default
- output that claims live readiness

Allowed:

- event-study review
- evidence-chain review
- historical metric comparison
- risk warning
- observation-list suggestion
- human-review recommendation

## 7. Loose card handling

Loose `024`–`030` cards are historical inputs. Canonical execution should use `BATCH_04_TASK_CARD_MANIFEST.md` and `B04_*` cards.

Do not delete loose cards until references in docs/tests are audited and redirect notes are added.

## 8. Anti-overengineering closure rule

Batch 04 cards are first implementation batches for their modules. They must not close by adding only a shell, placeholder, policy note, deferred route, or schema-only migration.

Required first vertical slices:

- API: at least one real read-only HTTP endpoint backed by QMD registry/capability/readiness data, with auth and budget enforcement.
- Agent: at least one allowed read-only tool executed through `AgentExecutionPolicy`, plus a forbidden-tool rejection path.
- Frontend: at least one API-bound page or panel with loading/error/empty states; deferred states are allowed only for pages outside the owned first slice.
- Notification/report: one source/data-health/report event transformed into persisted report/notification state with dedup/cooldown tests.
- Backtest/review: one executable read-only review scenario producing a bounded report artifact.

Each Round4 module uses **at most three implementation batches total** to reach full production-stable supported scope: the canonical card’s first vertical slice counts as batch 1, plus at most two follow-up batches (production-complete scope, then hardening/regression).
