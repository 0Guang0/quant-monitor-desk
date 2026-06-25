# R3FR-04 — Round4 Backtest/Review Adoption Rewrite

> **Batch:** Batch 3F-R — Mature Reference Adoption Refactor  
> **Module movement:** Round4 backtest/review planning must move from blank-engine risk to a reference-adapted first vertical slice plan.  
> **Execution posture:** planning/task rewrite only in 3F-R; no backend backtest runtime unless explicitly authorized.

---

## 1. Purpose

Rewrite Round4 backtest/review task cards so the first implementation batch delivers a working read-only review/backtest vertical slice, and the full stable shape is reached within at most three implementation batches. Do not allow “add one metric per task” micro-slicing.

---

## 2. Reference source files

Read and cite directly inside the Round4 task cards:

```text
参考项目/JQ2PTrade/api_mapping.json
参考项目/JQ2PTrade/ptrade_local/engine/data_loader.py
参考项目/JQ2PTrade/ptrade_local/engine/context.py
参考项目/JQ2PTrade/ptrade_local/engine/backtester.py
参考项目/JQ2PTrade/ptrade_local/engine/report.py
参考项目/JQ2PTrade/ptrade_local/run_backtest.py
参考项目/EasyXT/easyxt_backtest/
```

---

## 3. What can be adapted

From JQ2PTrade:

- bounded historical data-loader shape;
- context/run lifecycle separation;
- report generation separation;
- run log / scenario inputs / deterministic replay ideas;
- `api_mapping.json` as forbidden API name source.

From EasyXT backtest:

- metric/report organization;
- strategy-independent result summary shape;
- reusable analysis/report boundaries.

---

## 4. What must be rewritten

- No order/action/account API surface.
- No broker/runtime strategy execution surface.
- No arbitrary user code execution.
- No portfolio action recommendation semantics.
- No Agent metric mutation.
- Replace reference runtime with QMD-owned read-only review modules.
- Bind all factual inputs to QMD evidence/source lineage.

---

## 5. Target files

Update:

```text
docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/B04_05_backtest_review_runtime.md
docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/BATCH_04_TASK_CARD_MANIFEST.md
docs/implementation_tasks/ROUND_4_API_FRONTEND_AGENT_BACKTEST/BATCH_04_VERIFIED_AUDIT_PRODUCTIZATION/BATCH_04_HARDENING_RULES.md
specs/contracts/backtest_contract.yaml
specs/contracts/backtest_reproducibility_contract.yaml
specs/contracts/review_sandbox_contract.yaml
```

Round4 task cards must carry the detailed source-path adaptation instructions locally. Do not move executable details into a separate inventory.

---

## 6. Round4 required batch structure

Round4 backtest/review must fit at most three implementation batches:

1. **Batch A — read-only vertical slice:** scenario registry, bounded loader, deterministic run, report artifact, no action semantics.
2. **Batch B — production-complete supported scope:** event sets, metrics, evidence-chain review, reproducibility, API binding.
3. **Batch C — hardening/regression:** resource limits, reproducibility drift tests, report limitations, security boundaries.

The first batch cannot be a shell; it must run end-to-end against a bounded QMD evidence dataset.

---

## 7. Done criteria

R3FR-04 is done when Round4 backtest/review cards no longer describe a from-scratch engine and instead require JQ2PTrade/EasyXT-informed QMD-owned implementation with no action semantics and a three-batch ceiling to full stable shape.
