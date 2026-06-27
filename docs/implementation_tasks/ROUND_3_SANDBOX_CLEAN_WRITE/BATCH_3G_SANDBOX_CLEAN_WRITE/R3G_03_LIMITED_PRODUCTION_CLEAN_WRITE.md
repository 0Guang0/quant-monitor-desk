# R3G-03 — Limited Production Clean Write

> **Batch:** Batch 3G — Sandbox Clean Write and Limited Production Entry  
> **Roadmap segment:** Round 3G.3  
> **Status:** Completed 2026-06-27 @ `23429ad8` — promote CLI + audit repair; Tier B execute defer to Coordinator  
> **Execution posture:** explicit user approval required; extreme caps; before/after proof and rollback dry run required.

---

## 1. Business purpose

Perform the first very small production clean-write entry only after R3G-01 sandbox rehearsal and R3G-02 adversarial audit prove that the path is bounded, reversible, and accurately reported.

This task does not broaden production ingestion. It authorizes only a capped pilot:

- 1–3 sources;
- 3–10 symbols/series total;
- 30–120 day window depending on source/domain;
- exact user approval artifact;
- before/after DB proof;
- rollback dry run.

---

## 2. Required preconditions

All must be true:

1. R3G-01 completed with sandbox report.
2. R3G-02 decision is `PASS_ALLOW_LIMITED_PROD_WRITE`, or `WARN_ALLOW_WITH_MANUAL_APPROVAL` plus explicit user approval.
3. `specs/contracts/sandbox_clean_write_contract.yaml` is present and matches this task.
4. `specs/contracts/reference_adoption_guardrails.yaml` includes Round3G scoped adoption rules.
5. Candidate sources are present in source registry and capability registry.
6. `qmd data health` supported profiles exist for candidate domains.
7. User approval artifact specifies exact source/domain/symbol/window/path.
8. **User Plan authorization ≠ production write authorization.** A coordinator may authorize Plan/Execute for R3G-03, but promote still requires a machine-readable §6 approval YAML plus aligned `audit_decision.json`; Plan approval alone must not open prod-path.
9. **Promote consumes `audit_decision.json` only**, not `audit.report.md`. R3G-02 `PASS_WITH_FIXES` on an audit report does not substitute for a decision file whose enum is `PASS_ALLOW_LIMITED_PROD_WRITE` or `WARN_ALLOW_WITH_MANUAL_APPROVAL`.
10. **Promote target DB is `production_db_path` from approval**, not the R3G-01 sandbox DB. Sandbox paths remain R3G-01/R3G-02 only.

---

## 3. Reference source implications

This task should not directly adapt reference project code. It consumes the QMD-owned implementation produced by R3G-01/R3G-02.

However, it must enforce the same source-specific guardrails:

### EasyXT-derived data-health requirements

From:

```text
参考项目/EasyXT/data_manager/data_integrity_checker.py
参考项目/EasyXT/data_manager/smart_data_detector.py
```

Production entry must prove the QMD-owned implementation checks:

- required-field nulls;
- non-positive OHLC;
- OHLC relations;
- duplicate primary keys;
- extreme returns;
- volume anomalies;
- missing trading days or explicit calendar-quality warning;
- completeness ratio.

Do not import EasyXT. Do not copy EasyXT DB/query/calendar implementation into production runtime.

### JQ2PTrade-derived loader/report requirements

From:

```text
参考项目/JQ2PTrade/ptrade_local/engine/data_loader.py
参考项目/JQ2PTrade/ptrade_local/engine/report.py
参考项目/JQ2PTrade/api_mapping.json
```

Production entry must prove:

- bounded data bundle is explicit;
- read stage and write stage are separate;
- report is generated from structured evidence;
- no strategy/backtest/order metrics are present;
- forbidden API names are not exposed.

Forbidden API names include:

```text
order
order_value
order_target
order_target_value
cancel_order
get_open_orders
get_portfolio
get_positions
get_orders
get_trades
run_daily
run_weekly
run_monthly
```

### OpenBB-derived provider metadata requirements

From:

```text
参考项目/OpenBB/openbb_platform/providers/
参考项目/OpenBB/openbb_platform/providers/fred/README.md
```

Production entry must prove candidate provider metadata is explicit and QMD-owned:

- provider/source id;
- allowed domain;
- auth/terms/cost notes;
- enabled-by-default posture;
- production default posture;
- explicit caps;
- OpenBB architecture reference only, no source copy.

### TradingAgents / agents-for-openbb exclusion

R3G-03 must not use TradingAgents, TradingAgents-astock, or agents-for-openbb. No Agent path may approve, trigger, expand, or summarize a production write in a way that replaces the required user approval artifact.

---

## 4. Suggested implementation files

```text
backend/app/ops/sandbox_clean_write/limited_production_entry.py
backend/app/ops/sandbox_clean_write/approval_contract.py
backend/app/ops/sandbox_clean_write/rollback_plan.py
backend/app/cli/data_commands.py
specs/contracts/sandbox_clean_write_contract.yaml
tests/test_round3g_limited_production_clean_write.py
tests/test_round3g_limited_production_rollback.py
tests/fixtures/sandbox_clean_write/r3g03/
```

### 4.1 Architecture and reuse (Execute SSOT)

**Target flow:**

```text
approval.yaml + audit_decision.json
  → validate_approval_contract()
  → build_before_proof(production_db)
  → build_rollback_plan(dry_run only)
  → LimitedProductionEntry.run(dry_run default)
  → build_after_proof()
  → promote_report.json
```

**ponytail reuse (do not reinvent):**

| Need              | Reuse                                                                                              | Do not add                     |
| ----------------- | -------------------------------------------------------------------------------------------------- | ------------------------------ |
| row-count proof   | `mutation_proof.key_table_row_counts` / `build_production_mutation_proof`                          | full-DB scan helper            |
| auth YAML shape   | `staged_pilot.validate_authorization` pattern                                                      | second auth format             |
| gate chain        | extract shared compose from `rehearsal_runner` **or** minimal mirror + `ponytail:` ceiling comment | third write orchestrator       |
| rollback identity | new small `rollback_plan.py`                                                                       | WriteManager built-in rollback |

**GitNexus `impact()` before editing:** `run_rehearsal` / rehearsal runner symbols, `write_audit_decision`, `build_production_mutation_proof`, `data_commands` sandbox-clean-write group.

**Blast radius:** direct callers = new promote modules + CLI; R3G-01/02 rehearse/audit CLIs must **keep** `production_mutation_allowed=false`. Opening `DEFAULT_PRODUCTION_DB` to rehearse/audit is a **stop condition**.

---

## 5. Required command shape

Suggested CLI shape:

```bash
qmd data sandbox-clean-write promote \
  --approval-file approvals/r3g_limited_write_YYYYMMDD.yaml \
  --audit-decision .audit-sandbox/round3g/audit_decision.json \
  --before-proof .audit-sandbox/round3g/before_proof.json \
  --after-proof .audit-sandbox/round3g/after_proof.json \
  --rollback-plan .audit-sandbox/round3g/rollback_plan.json
```

The command must fail closed unless approval file and audit decision agree exactly on:

- source id;
- domain;
- symbol/series list;
- start/end date;
- target table;
- max rows;
- production DB path;
- rollback plan path;
- approver identity or explicit user authorization marker.

---

## 6. Approval file minimum schema

```yaml
approval_id: ""
approver: ""
approved_at: ""
audit_decision_file: ""
source_candidates:
  - source_id: baostock
    domain: cn_equity_daily_bar
    symbols: []
    start_date: ""
    end_date: ""
    max_rows: 0
  - source_id: cninfo
    domain: cn_announcements
    symbols: []
    start_date: ""
    end_date: ""
    metadata_only: true
    max_rows: 0
  - source_id: fred
    domain: macro_series
    series: []
    start_date: ""
    end_date: ""
    max_rows: 0
    live_fetch_authorized: false
production_db_path: ""
rollback_required: true
no_agent_triggered_write: true
no_cap_expansion: true
```

---

## 7. Required before/after proof

Before proof must include:

- target table row count;
- affected key range count;
- target schema hash;
- latest write operation id if any;
- backup or snapshot pointer;
- ResourceGuard decision.

After proof must include:

- inserted/updated row count;
- unchanged row count for non-target range;
- validation status;
- source_fetch_id coverage;
- content_hash/schema_hash coverage;
- WriteManager operation id;
- rollback plan id;
- data-health status.

Rollback dry run must prove affected rows can be identified and removed/reverted without touching non-target keys.

---

## 8. Forbidden scope

- No cap expansion beyond approval file.
- No broad source fallback.
- No full-market or full-history write.
- No minute bars.
- No QMT, TDX, xqshare, Yahoo production primary.
- No Agent-triggered write.
- No full PDF downloads.
- No runtime import from `参考项目/**`.
- No OpenBB runtime source copy.
- No JQ2PTrade trading API compatibility layer.

### 8.1 Execute stop conditions (fail-closed)

Stop and fix before continuing if any of these occur:

1. **Default prod write:** promote implementation or CLI performs production mutation without explicit `--execute` (or equivalent) **and** validated §6 approval + Tier B coordinator gate.
2. **Missing quadruple lock:** any promote run without approval file + allowing audit decision + before proof + rollback plan artifact.
3. **Regression on R3G-01/02:** `sandbox-clean-write rehearse` or `audit` accepts production DB path or sets `production_mutation_allowed=true`.
4. **Rollback overreach:** rollback dry-run deletes or mutates rows outside the approved key range (dry-run must identify only).
5. **Cap / agent drift:** approval expands symbols, window, or sources beyond `candidate_caps` r3g03 or sets `no_agent_triggered_write=false`.
6. **Mis-touch high blast-radius symbols** without prior `impact()` on rehearsal runner / data_commands (see §4.1).

**Risk mitigations (summary):** default `dry_run`; approval+audit field equality; rollback dry-run is identify-only; Tier B prod-path is manual and out of CI.

---

## 9. Implementation steps

1. **approval_contract** — `approval_contract.py`：解析活卡 §6 YAML；校验 `audit_decision.json` 决策为 `PASS_ALLOW_LIMITED_PROD_WRITE` 或 `WARN_ALLOW_WITH_MANUAL_APPROVAL`；approval 与 audit 在 source/domain/symbol/window/max_rows/production_db_path 上**逐字段一致**；`no_agent_triggered_write` / `no_cap_expansion` 必须为 true。
2. **before_proof** — 复用 `mutation_proof.key_table_row_counts` / `build_production_mutation_proof`；产出活卡 §7 before 字段（target table row count、key range、schema hash、latest write op id、backup pointer、ResourceGuard decision）。
3. **rollback_plan** — `rollback_plan.py`：基于 before proof + approval 候选生成 rollback plan id；dry-run 仅识别 affected keys，**不**执行生产删除（Execute prod-path 由用户单独授权时再跑真写）。
4. **limited_production_entry** — `limited_production_entry.py`：复用 §4.1 门禁链（DSS → RoutePlanner → ResourceGuard → DH profile → DbValidationGate → WriteManager）。**ponytail:** 优先从 `rehearsal_runner` 提取共享 compose 函数；若镜像则须 `ponytail:` 注释双维护天花板。`production_mutation_allowed=true` 仅当四门全通过且非默认 dry_run；live fetch 仅当 approval `live_fetch_authorized: true` 且 FRED authorization artifact 存在。
5. **after_proof** — 写后产出活卡 §7 after 字段；非目标 key range row count 不变；附 WriteManager operation id 与 rollback plan id。
6. **CLI promote** — `qmd data sandbox-clean-write promote`（活卡 §5 形状）；缺任一输入文件 fail-closed；拒绝 `DATA_ROOT` 外未批准路径。
7. **contract tests** — 扩展 `test_round3g_limited_production_clean_write.py` / `test_round3g_limited_production_rollback.py` 从静态契约到 runner/CLI 对抗测；**必须**覆盖 §10.1 `block_if` 矩阵与 §8.1 停止条件 3（rehearse/audit 不回退）。
8. **guardrails** — `test_reference_adoption_guardrails.py` 增 R3G-03 扫描；禁止 Agent 路径、参考项目 runtime import、OpenBB/JQ2PTrade 违规面。
9. **merge gate** — 全库 pytest + `loop_maintain.py`；release note 片段记录 exact source/domain/symbol/window。

---

## 10. Tests / gates

Required verification:

```bash
uv run pytest tests/test_round3g_limited_production_clean_write.py -q
uv run pytest tests/test_round3g_limited_production_rollback.py -q
uv run pytest tests/test_reference_adoption_guardrails.py -q
```

Test expectations:

- missing approval file blocks;
- mismatched approval and audit decision blocks;
- cap expansion blocks;
- missing before proof blocks;
- missing rollback plan blocks;
- Agent-triggered write marker blocks;
- forbidden source/domain blocks;
- WriteManager/DbValidationGate bypass blocks;
- runtime import from `参考项目/**` blocks;
- OpenBB/JQ2PTrade unsafe copy blocks.

### 10.1 `block_if` adversarial test matrix (Execute required)

| `r3g03_limited_entry.block_if` / expectation                | Test focus (§9 step 7)                           |
| ----------------------------------------------------------- | ------------------------------------------------ |
| `missing_approval_file`                                     | `ApprovalContract` / `PromoteCli`                |
| `audit_decision_not_allowing_entry`                         | `ApprovalContract`                               |
| `approval_audit_mismatch`                                   | `ApprovalContract`                               |
| `cap_expansion`                                             | `ApprovalContract` + contract caps               |
| `missing_before_proof`                                      | `BeforeProof` / `PromoteCli`                     |
| `missing_after_proof`                                       | `AfterProof` / `PromoteRunner`                   |
| `missing_rollback_plan`                                     | `RollbackPlan` / `PromoteCli`                    |
| `agent_triggered_write_path`                                | `ApprovalContract` + guardrails                  |
| WriteManager/DbValidationGate bypass (task §10 bullet)      | `PromoteRunner` synthetic bypass                 |
| forbidden source/domain (task §10 bullet)                   | `PromoteRunner`                                  |
| runtime import / OpenBB / JQ2PTrade (task §10 + guardrails) | `test_reference_adoption_guardrails.py -k r3g03` |
| rehearse/audit prod-path regression (§8.1 #3)               | extend or run existing R3G-01/02 CLI tests       |

---

## 11. Done criteria

R3G-03 is done only when:

- every production write is explicitly approved and capped;
- before/after proof is generated and machine-checkable;
- rollback dry run is generated and machine-checkable;
- no reference project runtime code is imported or copied unsafely;
- no Agent/UI path can initiate or broaden the write;
- release notes state the exact source/domain/symbol/window and limitations.
