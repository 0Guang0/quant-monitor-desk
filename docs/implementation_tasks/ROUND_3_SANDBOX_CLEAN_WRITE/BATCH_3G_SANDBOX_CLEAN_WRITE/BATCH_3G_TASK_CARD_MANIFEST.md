# Batch 3G Task Card Manifest — Sandbox Clean Write and Limited Production Entry

> **Canonical batch folder:** `docs/implementation_tasks/ROUND_3_SANDBOX_CLEAN_WRITE/BATCH_3G_SANDBOX_CLEAN_WRITE/`  
> **Roadmap:** `PROJECT_IMPLEMENTATION_ROADMAP.md` → Round 3G.  
> **Structural rule:** one Task ID = one executable task card. README is an entrypoint, not the task body.

---

## 1. Canonical Batch 3G cards

| Task ID  | Card                                         | Scope                                                                                | Primary gates                                                                                   | Reference-adoption details location |
| -------- | -------------------------------------------- | ------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------- | ----------------------------------- |
| `R3G-01` | `R3G_01_SANDBOX_CLEAN_WRITE_REHEARSAL.md`    | sandbox rehearsal for baostock daily bar, cninfo metadata, authorized FRED P0 sample | sandbox DB only, WriteManager audit, DbValidationGate PASS, data-health PASS/WARN               | in the task card                    |
| `R3G-02` | `R3G_02_PRE_PRODUCTION_ADVERSARIAL_AUDIT.md` | strict audit of R3G-01 evidence                                                      | `PASS_ALLOW_LIMITED_PROD_WRITE`, `WARN_ALLOW_WITH_MANUAL_APPROVAL`, or `BLOCK_PRODUCTION_WRITE` | in the task card                    |
| `R3G-03` | `R3G_03_LIMITED_PRODUCTION_CLEAN_WRITE.md`   | extremely small approved production entry                                            | explicit user approval, before/after proof, rollback dry run                                    | in the task card                    |

---

## 2. Reference-detail placement rule

Do not create a separate `reference_adoption_inventory.md` for Batch 3G. Reference-source decisions must be written directly into the relevant task card:

- R3G-01 owns detailed EasyXT/JQ2PTrade/OpenBB adaptation plan for the rehearsal implementation.
- R3G-02 owns adversarial audit criteria derived from those same source files.
- R3G-03 owns enforcement requirements for the approved limited entry.

This keeps the execution context local to each task card.

---

## 3. Reference projects allowed in Batch 3G

| Reference project                                        | Allowed use in Batch 3G                                                                                                                                                | Forbidden use                                                                                   |
| -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| EasyXT                                                   | scoped adaptation of data-quality rule ideas from `data_integrity_checker.py` and missing-data shape from `smart_data_detector.py` into QMD-owned data-health profiles | runtime import, hardcoded DB/table, SQL interpolation, copied holiday calendar as authoritative |
| JQ2PTrade                                                | scoped adaptation of frozen-data loader/report separation from `ptrade_local/engine/data_loader.py` and `report.py`; `api_mapping.json` as deny-list source            | strategy execution, order API compatibility, broad stock/index loader, default DB path          |
| OpenBB                                                   | architecture-only provider metadata layout reference from `openbb_platform/providers/` and FRED README                                                                 | copying AGPL runtime source, provider fetcher classes, package code                             |
| TradingAgents / TradingAgents-astock / agents-for-openbb | no active use in Batch 3G; only explicit exclusion and guardrail                                                                                                       | Agent-triggered write, Agent-expanded candidate set, Agent approval substitute                  |

---

## 4. Execution order

1. `R3G-01` creates sandbox rehearsal only.
2. `R3G-02` audits R3G-01 evidence and emits the strict decision enum.
3. `R3G-03` can run only if R3G-02 allows it and the user approval artifact matches exactly.

---

## 5. Batch 3G close criteria

Batch 3G cannot close unless:

- all Task IDs have individual task cards;
- every reference-adoption detail needed by execution is in the relevant task card;
- `specs/contracts/reference_adoption_guardrails.yaml` includes Round3G scoped rules;
- `specs/contracts/sandbox_clean_write_contract.yaml` or equivalent contract exists;
- no runtime imports from `参考项目/**`;
- no OpenBB runtime source copy;
- no JQ2PTrade execution/trading API surface;
- no Agent-triggered write path.
