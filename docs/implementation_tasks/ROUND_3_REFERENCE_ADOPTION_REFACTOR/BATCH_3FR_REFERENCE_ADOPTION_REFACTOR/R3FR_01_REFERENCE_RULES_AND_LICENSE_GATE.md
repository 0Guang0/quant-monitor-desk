# R3FR-01 — Reference Governance Re-execution Plan

> **Batch:** Batch 3F-R — Mature Reference Adoption Refactor  
> **Status:** rewritten after production-completion planning audit; execute this card again before downstream reference-adoption work.  
> **Execution posture:** docs/contracts/tests planning gate only; no runtime fetch; no clean write; no source enablement.  
> **Business purpose:** make sure QMD can borrow mature ideas from reference projects without creating legal risk, unsafe trading behavior, or another confusing “central plan” that execution agents blindly follow.

---

## 1. Why this card is being rewritten

R3FR-01 was already completed with the correct core rule:

```text
Executable reference-adoption details must live in the task card that uses the reference source.
```

After the latest audit, a new file was added:

```text
docs/implementation_tasks/PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md
```

That file is useful because it shows the whole production-completion map in one place. But it creates a new risk: an executor may treat it as a new central executable inventory and skip the detailed task cards. That would violate R3FR-01's original rule.

This rewrite makes the rule explicit:

```text
The production-completion plan is a navigation and coverage checklist only.
It is not a replacement for concrete task cards.
A downstream task can be executed only from its owning task card after that card carries local reference paths, borrowable logic, forbidden semantics, QMD target files, tests, and not-done conditions.
```

For a non-technical reader: the new plan is like a city map. It helps you see all roads, but it is not the work order for fixing a specific bridge. The bridge repair team still needs the bridge-specific job card.

---

## 2. Files that must be checked or updated

Re-execution of R3FR-01 owns only governance/planning files:

```text
specs/contracts/reference_adoption_guardrails.yaml
MODULE_COMPLETION_RATING.md
PROJECT_IMPLEMENTATION_ROADMAP.md
docs/implementation_tasks/README.md
docs/implementation_tasks/PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md
docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_TASK_CARD_MANIFEST.md
docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_HARDENING_RULES.md
docs/implementation_tasks/ROUND_3_REFERENCE_ADOPTION_REFACTOR/BATCH_3FR_REFERENCE_ADOPTION_REFACTOR/README.md
docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/*.md
docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/*.md
docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/*.md
docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE/*.md
docs/generated/docs_specs_index.generated.md
```

Do not edit runtime code in this task.

---

## 3. Non-negotiable rules

1. **No central executable inventory.**
   - `reference_adoption_inventory.md` must not become a required execution source.
   - `PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md` must not become a required execution source by itself.
   - The production plan may be required as a coverage checklist, but each implementation still executes from the owning task card.

2. **Task-local reference adoption.**
   Any task that uses `参考项目/**` must carry local details:
   - exact reference paths;
   - what can be borrowed;
   - what dangerous capability must be deleted or forbidden;
   - QMD target files;
   - tests/gates;
   - not-done conditions.

3. **Reference projects are never runtime dependencies.**
   QMD backend/scripts must not import from `参考项目/**`, mutate `sys.path` to reference projects, or copy unsafe runtime code.

4. **No trading/action semantics.**
   JQ2PTrade/EasyXT/Agent references must not introduce orders, broker/account APIs, strategy execution, auto-login, terminal control, free SQL, or Agent-triggered writes.

5. **Production-grade claims require executable proof.**
   A module cannot be called production-grade because a plan, registry, or placeholder exists. It needs a working vertical slice, tests, evidence/lineage where data is involved, ResourceGuard/security posture, and release-manifest representation.

---

## 4. Re-execution slices using `/to-issues` style

The executor must complete these slices in order. Each slice is independently reviewable and must leave a clear diff.

### Slice R3FR-01-A — Guardrail contract refresh

**Blocked by:** None - can start immediately.

**User stories covered:** As a coordinator, I can tell the difference between a helpful coverage map and an executable task card, so agents do not work from the wrong source.

**What to build:** Update the reference-adoption guardrail contract so it explicitly says production-completion plans are non-executable coverage supplements unless copied into the owning task card.

**Acceptance criteria:**

- [ ] `specs/contracts/reference_adoption_guardrails.yaml` says executable reference details must stay task-card-local.
- [ ] It says `PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md` is a coverage/navigation supplement, not a standalone execution card.
- [ ] It says downstream tasks may cite the production plan only as a coverage checklist.
- [ ] It still blocks runtime import from `参考项目/**`, OpenBB runtime copy, JQ2PTrade execution hooks, trading/action APIs, auto-login, silent fallback, and Agent-triggered writes.

**Blocked by:** None - can start immediately.

---

### Slice R3FR-01-B — Production plan boundary fix

**Blocked by:** Slice R3FR-01-A.

**User stories covered:** As an implementer, I can use the production-completion plan to see missing work without mistaking it for the single source of truth for implementation.

**What to build:** Update `PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md` so its first page clearly explains its role.

**Acceptance criteria:**

- [ ] The file states in plain language that it is a navigation/coverage checklist.
- [ ] It states that implementation agents must execute from the owning canonical task card.
- [ ] It states that a slice in this plan is not executable until the owning task card contains local reference-adoption details and acceptance criteria.
- [ ] It preserves the to-issues-style slice breakdown as planning material.

**Blocked by:** Slice R3FR-01-A.

---

### Slice R3FR-01-C — Downstream task-card risk audit

**Blocked by:** Slice R3FR-01-B.

**User stories covered:** As a batch owner, I can verify that R3G, R3H, Batch04, and Batch05 cards do not accidentally say “see the plan” instead of giving executable details.

**What to build:** Audit canonical downstream task cards and patch wording where needed.

**Acceptance criteria:**

- [ ] R3G cards still contain local EasyXT/JQ2PTrade/OpenBB rewrite details and do not depend on a central inventory.
- [ ] R3H source cards still contain local provider/reference boundaries and per-source completion conditions.
- [ ] Batch04 cards that use reference projects point to local executable cards, especially B04_02, B04_03, B04_04, and B04_05.
- [ ] Batch05 cards treat missing production work as release blockers/limitations, not as features to implement silently during release.
- [ ] Historical loose cards such as `029_implement_backtest_and_review.md` clearly redirect to canonical Batch04 cards and cannot be used as standalone execution entrypoints.

**Blocked by:** Slice R3FR-01-B.

---

### Slice R3FR-01-D — Project planning file alignment in business language

**Blocked by:** Slice R3FR-01-C.

**User stories covered:** As a business/product reader, I can understand what is production-ready, what is only staged, and what must happen next without reading code.

**What to build:** Update project planning files in simple Chinese so they explain the latest status and avoid overstating readiness.

**Acceptance criteria:**

- [ ] `PROJECT_IMPLEMENTATION_ROADMAP.md` explains that the production-completion plan is a checklist/map, not a task replacement.
- [ ] `MODULE_COMPLETION_RATING.md` explains that modules can be upgraded only with working slices and proof, not docs alone.
- [ ] `docs/implementation_tasks/README.md` points readers to the production-completion plan as coverage aid while preserving task-card-local execution.
- [ ] Wording is understandable to a non-engineering stakeholder: “地图不是工单；任务卡才是工单”.
- [ ] No planning file claims that Round1/Round2/Round3 are already full production-grade.

**Blocked by:** Slice R3FR-01-C.

---

### Slice R3FR-01-E — Static verification gate

**Blocked by:** Slice R3FR-01-D.

**User stories covered:** As an auditor, I can catch future regressions where a central plan becomes an executable dependency again.

**What to build:** Update or require static tests/checks for the rewritten rules.

**Acceptance criteria:**

- [ ] `tests/test_reference_adoption_guardrails.py` or an equivalent static check verifies the guardrail contract.
- [ ] Checks cover both forbidden central `reference_adoption_inventory.md` and the new production-completion plan boundary.
- [ ] Checks cover local `reference_project:` declarations for adapting task cards.
- [ ] `docs/generated/docs_specs_index.generated.md` includes new planning files or is regenerated.
- [ ] If tests cannot run because of environment issues, the executor records the exact error and performs static search review.

**Blocked by:** Slice R3FR-01-D.

---

## 5. Downstream task-card audit checklist

During Slice R3FR-01-C, audit these files at minimum:

```text
docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_01_SANDBOX_CLEAN_WRITE_REHEARSAL.md
docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_02_PRE_PRODUCTION_ADVERSARIAL_AUDIT.md
docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/R3G_03_LIMITED_PRODUCTION_CLEAN_WRITE.md
docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_01_OFFICIAL_MACRO_DISCLOSURE_ADAPTERS.md
docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_02_MARKET_DATA_ADAPTERS.md
docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_03_CN_MARKET_ADAPTERS.md
docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_04_PREDICTION_AND_WEB_EVIDENCE_ADAPTERS.md
docs/implementation_tasks/ROUND_3_REAL_DATA_PRODUCTION_ENTRY/BATCH_3H_REAL_DATA_PRODUCTION_ENTRY/R3H_05_LAYER_BINDING_AND_PRODUCTION_ENTRY_AUDIT.md
docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/B04_01_api_runtime_security.md
docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/B04_02_agent_policy_runtime.md
docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/B04_03_frontend_error_boundary_and_routes.md
docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/B04_04_notification_report_runtime.md
docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/B04_05_backtest_review_runtime.md
docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE/B05_01_security_ci_release_gate.md
docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE/B05_02_integration_and_resource_smoke.md
docs/implementation_tasks/ROUND_5_INTEGRATION_RELEASE/BATCH_05_VERIFIED_AUDIT_SECURITY_RELEASE/B05_03_release_manifest_and_package_cleanup.md
```

Patch a downstream card if it has any of these problems:

- It says only “参考/借鉴某项目” but does not say what can be borrowed, what must be deleted, target files, tests, and not-done conditions.
- It sends executors to a central inventory or the production-completion plan instead of local instructions.
- It lets release/security work implement missing product features silently.
- It allows staged/fixture/proposed-disabled status to be described as production-ready.
- It omits ResourceGuard/evidence/source_fetch_id/content_hash/schema_hash where data is involved.

---

## 6. Tests / gates

Required when environment supports them:

```bash
uv sync --locked
uv run pytest tests/test_reference_adoption_guardrails.py -q
uv run pytest tests/test_documentation_index.py tests/test_docs_specs_indexed.py -q
uv run python scripts/loop_maintain.py
```

Static search fallback if test execution is blocked:

```text
Search for central inventory dependency:
- reference_adoption_inventory.md
- PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md
- execution dependency
- SSOT
- must read

Search for unsafe reference adoption:
- 参考项目/** runtime import
- sys.path.insert
- compile(..., 'exec')
- exec(...)
- order / order_value / run_daily
- OpenBB runtime dependency
```

---

## 7. Done criteria

R3FR-01 re-execution is done when:

- global guardrails explicitly protect against both old and new central-plan risks;
- the production-completion plan is clearly marked as coverage/navigation, not a task-card replacement;
- downstream canonical task cards remain executable in their own right;
- project planning files explain the latest status in business-readable Chinese without overstating production readiness;
- static tests/checks exist or are explicitly required;
- no runtime code is changed by this governance task.

---

## 8. Not done if

This task is not complete if any of the following is true:

- an executor must read a central inventory or the production-completion plan to know how to implement a specific reference adoption;
- a task card refers to JQ2PTrade/EasyXT/OpenBB/agents-for-openbb/TradingAgents without local rewrite details;
- `PRODUCTION_COMPLETION_VERTICAL_SLICE_PLAN.md` sounds like the only execution source;
- planning files imply the project is already full production-grade;
- release/security cards are allowed to hide unfinished product features instead of listing blockers/limitations;
- tests are skipped and the result claims verification passed.
