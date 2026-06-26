# Batch 3G — Sandbox Clean Write and Limited Production Entry

> **Canonical status:** Round 3G batch package — **preconditions satisfied** (Batch 3F-R CLOSED, condition A).  
> **Roadmap:** `PROJECT_IMPLEMENTATION_ROADMAP.md` → Round 3G — **current next executable entrypoint**.  
> **3F-R deliverables consumed:** `run_data_health_profile` / `market_bar_p0`, `provider_catalog.yaml`, TDX delegate boundaries (R3FR-02..06).

---

## 1. Purpose

Round 3G moves from raw/staging/sandbox evidence toward sandbox clean-write rehearsal and then very small production clean-write entry.

It must not start while known duplicate-wheel risks remain unresolved in:

- data health profile quality
- `qmd data health` runtime wiring
- TDX provider separation from probe orchestration
- provider catalog metadata
- Round4 backtest/reference adoption planning

---

## 2. Canonical task cards

> **Structure rule:** one Task ID = one executable task card. This README is only the batch entrypoint. Detailed reference-project adoption instructions live in each `R3G_*` task card, not in a separate reference inventory file.

| Task ID  | Canonical card                               | Scope                                                                                                                        | Source roadmap section | Gate                                                                                            |
| -------- | -------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ---------------------- | ----------------------------------------------------------------------------------------------- |
| `R3G-01` | `R3G_01_SANDBOX_CLEAN_WRITE_REHEARSAL.md`    | Sandbox clean-write rehearsal for baostock daily bar, cninfo announcement metadata, and authorized FRED P0 macro sample only | Round 3G.1             | sandbox clean table row counts, WriteManager audit, DbValidationGate PASS, DataHealth PASS/WARN |
| `R3G-02` | `R3G_02_PRE_PRODUCTION_ADVERSARIAL_AUDIT.md` | Strict pre-production adversarial audit                                                                                      | Round 3G.2             | `PASS_ALLOW_LIMITED_PROD_WRITE`, `WARN_ALLOW_WITH_MANUAL_APPROVAL`, or `BLOCK_PRODUCTION_WRITE` |
| `R3G-03` | `R3G_03_LIMITED_PRODUCTION_CLEAN_WRITE.md`   | Limited production clean write, 1–3 sources, 3–10 symbols/series, 30–120 day window                                          | Round 3G.3             | user approval, before/after DB proof, rollback dry run                                          |

Batch package support files:

- `BATCH_3G_TASK_CARD_MANIFEST.md`
- `BATCH_3G_HARDENING_RULES.md`
- `BATCH_3G_COORDINATOR_PLAYBOOK.md`

---

## 3. Mandatory preconditions

Before any `R3G-*` work starts:

1. Round 3F-R is **complete** (condition A satisfied @ R3FR-07).
2. `qmd data health` uses `run_data_health_profile` for supported read-only profiles (R3FR-06).
3. EasyXT-style OHLCV/data-integrity profiles (`market_bar_p0`) cover write candidate domains or are deferred by ADR.
4. TDX must remain disabled/raw-only and must not participate in first clean-write candidates.
5. Provider catalog (`provider_catalog.yaml`, R3FR-05) identifies auth/cost/terms/quality role for write candidate sources or explicitly defers non-candidate sources.
6. No live source is enabled by default.
7. No production write occurs in R3G.1 or R3G.2.

---

## 4. Allowed first rehearsal candidates

Only:

- `baostock` → `cn_equity_daily_bar`
- `cninfo` → `cn_announcements` metadata
- `fred` → P0 macro series, only if authorization/evidence requirements are satisfied

Forbidden in first rehearsal:

- full market
- full history
- minute bars
- QMT / TDX / xqshare / Yahoo production primary
- full PDF downloads
- any Agent-triggered write

---

## 5. Batch-folder rule

This folder is the canonical future 3G package. Loose roadmap text remains the planning source of truth, but execution plans should be generated from this folder plus `PROJECT_IMPLEMENTATION_ROADMAP.md`.
