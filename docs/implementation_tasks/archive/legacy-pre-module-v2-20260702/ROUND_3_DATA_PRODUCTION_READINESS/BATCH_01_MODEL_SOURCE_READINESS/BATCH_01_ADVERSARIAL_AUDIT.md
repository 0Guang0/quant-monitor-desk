# Batch 01 Adversarial Audit

> Audit target: first-batch task cards and included legacy/original cards.  
> Batch: `BATCH_01_MODEL_SOURCE_READINESS`.  
> Audit posture: planning-level adversarial review; no code execution, no live source access, no production DB access.  
> Verdict after hardening: `PASS_WITH_BATCH_HARDENING_RULES`.

---

## 1. Cards audited

### Forward cards

- `../R3D_model_input_whitelist.md`
- `../R3E_fred_authorized_sandbox_pilot.md`
- `../R3E_tdx_manual_probe_addendum.md`
- `../R3E_real_data_staged_pilot_v3.md`
- `../R3E_readonly_data_health_v2.md`

### Legacy/original cards included in audit

- `../../ROUND_3_MODELING_LAYERS/018C_tdx_pytdx_low_cost_probe.md`
- `../../ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_real_data_staged_pilot_v2.md`
- `../../ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_readonly_data_health_v1.md`
- `../../ROUND_3_PARALLEL_PROMPTS/PROMPT_04_debt_r3b275_fred_staged_semantics.md`
- `../../ROUND_3_MODELING_LAYERS/018B_production_live_pilot_gate.md`
- `../../ROUND_3_ADVERSARIAL_AND_DATA_PILOT/R3Y_staged_pilot_v2_execution_addendum.md`

---

## 2. Audit method

Checked each card for:

1. Ambiguous production-live wording.
2. Possible production clean-write loophole.
3. Full-market/full-history accidental scope creep.
4. Source role escalation risk.
5. Live-source authorization ambiguity.
6. Registry row closure-by-analogy risk.
7. Legacy/new card conflict risk.
8. Missing evidence fields.
9. Test weakness or implementation-detail-only assertions.
10. Missing stop conditions for API keys, dependencies, network failures, and cap expansion.

---

## 3. Findings and hardening actions

| Finding ID   | Severity | Finding                                                                                                                                                               | Affected cards                                                         | Hardening action                                                                                                                                                                                    | Status    |
| ------------ | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- |
| `B01-AUD-01` | HIGH     | Legacy cards are scattered across older Round folders. Executors could read only a new card and miss old constraints, or read only old cards and miss new boundaries. | All                                                                    | Added `README.md` and `BATCH_01_TASK_CARD_MANIFEST.md` to bind forward + legacy cards into one batch entrypoint.                                                                                    | CLOSED    |
| `B01-AUD-02` | HIGH     | Legacy TDX 018C and new TDX addendum may have different default caps. This can be misread as permission to use the larger/newer cap.                                  | `018C`, `R3E_tdx_manual_probe_addendum.md`                             | Added hardening rule: stricter/smaller cap wins unless user explicitly approves.                                                                                                                    | CLOSED    |
| `B01-AUD-03` | HIGH     | v2 staged pilot can be reused by future executors to bypass model input whitelist and hand-pick symbols.                                                              | `R3Y_real_data_staged_pilot_v2.md`, `R3E_real_data_staged_pilot_v3.md` | Manifest states v3 must not reuse v2 to bypass whitelist; hardening rules require whitelist trace.                                                                                                  | CLOSED    |
| `B01-AUD-04` | HIGH     | FRED staged semantics can be closed incorrectly using `macro_supplementary` evidence.                                                                                 | FRED card, PROMPT_04                                                   | Hardening rules require FRED-only evidence for `B2.5-O-05`; macro supplementary is insufficient.                                                                                                    | CLOSED    |
| `B01-AUD-05` | HIGH     | Data health v2 could be mistaken as permission to create `source_health_snapshot`, which belongs to later Batch6 work.                                                | v1/v2 health cards                                                     | Hardening rules and v2 card forbid DB write and `source_health_snapshot`; batch README reiterates no production entry.                                                                              | CLOSED    |
| `B01-AUD-06` | HIGH     | Source readiness could be reported as production readiness.                                                                                                           | All                                                                    | Added allowed/forbidden output language in hardening rules.                                                                                                                                         | CLOSED    |
| `B01-AUD-07` | HIGH     | Registry rows could be closed by similarity or sidecar evidence.                                                                                                      | FRED, TDX, v3                                                          | Added exact registry closure rule with row-specific evidence requirements.                                                                                                                          | CLOSED    |
| `B01-AUD-08` | MEDIUM   | Legacy cards sometimes use `python -m pytest`, while newer project convention prefers `uv run pytest`.                                                                | Legacy v1/v2/018C                                                      | Batch hardening does not rewrite legacy cards; forward cards use `uv`. Executors should follow the card being executed and global runtime versions; if conflict, current `uv` convention wins.      | MITIGATED |
| `B01-AUD-09` | MEDIUM   | First-batch cards live one level above the batch folder, so users may wonder which path is canonical.                                                                 | Forward cards                                                          | Batch README/manifest designate canonical cards by path and batch folder as entrypoint. Physical moves avoided to preserve references.                                                              | CLOSED    |
| `B01-AUD-10` | MEDIUM   | Live authorization could be interpreted from a task card rather than explicit session evidence.                                                                       | FRED, TDX, v3                                                          | Added required authorization evidence schema.                                                                                                                                                       | CLOSED    |
| `B01-AUD-11` | MEDIUM   | Evidence fields vary across cards; missing `source_fetch_id`, `content_hash`, `as_of` may slip through.                                                               | FRED, TDX, v3, health v2                                               | Added batch evidence rule requiring common evidence fields.                                                                                                                                         | CLOSED    |
| `B01-AUD-12` | MEDIUM   | Tests may verify file existence or parser shape but not business safety.                                                                                              | All implementation cards                                               | Added required negative tests: AkShare not Primary, TDX not production primary, FRED not closed by macro supplementary, missing auth blocks fetch, missing evidence blocks clean-write eligibility. | CLOSED    |
| `B01-AUD-13` | MEDIUM   | External dependency or API key needs could silently expand scope.                                                                                                     | FRED, TDX                                                              | Added stop-and-escalate rule for dependencies, API keys, credentials, and cap expansion.                                                                                                            | CLOSED    |
| `B01-AUD-14` | LOW      | Duplicating legacy task cards would create stale copies.                                                                                                              | Batch organization                                                     | Chose manifest binding instead of copying/moving old cards; old paths remain canonical.                                                                                                             | CLOSED    |

---

## 4. Residual risks after hardening

These are acceptable planning-stage residual risks and must be handled during execution:

1. **Actual FRED API behavior is not proven by these cards.**  
   Execution must still use mocked tests plus optional authorized live evidence.

2. **Actual TDX connectivity may fail.**  
   The TDX task must return fail/defer taxonomy without blocking default CI.

3. **Model input whitelist may require business prioritization.**  
   If Layer1–Layer5 source needs conflict, whitelist executor must ask for owner/coordinator decision instead of guessing.

4. **Docs index may need updating.**  
   Batch files are new; future documentation consistency checks may require index updates.

5. **Production-entry cards are still not created in this batch.**  
   Sandbox clean-write rehearsal and limited production clean write remain out of scope.

---

## 5. Required updates performed by this audit

Created:

- `BATCH_01_MODEL_SOURCE_READINESS/README.md`
- `BATCH_01_MODEL_SOURCE_READINESS/BATCH_01_TASK_CARD_MANIFEST.md`
- `BATCH_01_MODEL_SOURCE_READINESS/BATCH_01_HARDENING_RULES.md`
- `BATCH_01_MODEL_SOURCE_READINESS/BATCH_01_ADVERSARIAL_AUDIT.md`

Updated / hardened by reference:

- The batch folder is now the entrypoint for first-batch execution.
- Legacy cards are included by manifest rather than copied or moved.
- Forward cards inherit hardening rules from this audit package.

---

## 6. Executor checklist after audit

Before executing any Batch 01 card, the agent must confirm:

- [ ] I read the batch README.
- [ ] I read the manifest.
- [ ] I read this adversarial audit.
- [ ] I read `BATCH_01_HARDENING_RULES.md`.
- [ ] I read the specific canonical task card.
- [ ] I read the included legacy card(s) listed for that task.
- [ ] I will use `/to-issues` before implementation.
- [ ] I will use `/tdd` with one RED → GREEN tracer bullet at a time.
- [ ] I will not use a task card as live-source authorization.
- [ ] I will not claim production readiness from staged/raw/sandbox evidence.

---

## 7. Final verdict

`PASS_WITH_BATCH_HARDENING_RULES`.

The original and newly created task cards are safe to proceed to `/to-issues` planning only if future executors treat the batch manifest and hardening rules as mandatory. Without these batch-level rules, the main residual risks would be stale legacy-card interpretation, source role escalation, and registry closure-by-analogy.
