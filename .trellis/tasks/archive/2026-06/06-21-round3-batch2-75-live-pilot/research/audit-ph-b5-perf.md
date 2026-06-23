# PH-B5 对抗审计 — Phase 4.5 Perf Budget

## 结论

**FAIL**

`phase45_perf_budget.json` 的最小 schema 完整，且 closeout 文案明确说明本轮 `RE_DEFERRED` 不授权 live sources。但 B5 要求的 `AUDIT_DEFERRED` registry 行不存在；同时本轮没有 smoke log，无法证明 bounded smoke 实际在隔离 data-root 下执行，也无法证明 ResourceGuard 在 Phase 4.5 smoke 中被 exercise。因此 PH-B5 不通过。

## B5 Checklist

| 项                                          | 结论 | 审计判断                                                                                                                                                                                                                                   |
| ------------------------------------------- | ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------- |
| B5-1 `phase45_perf_budget.json` schema 完整 | PASS | JSON 含 `owner=batch275-execute`、`phase=4.5`、`status=RE_DEFERRED`、`closure_test=uv run python scripts/production_equivalent_smoke.py --data-root .audit-sandbox/batch275-perf-smoke`，且 `status` 在 `PASS                              | RE_DEFERRED` 范围内。 |
| B5-2 smoke 在隔离 data-root 或 re-defer     | FAIL | JSON/closeout 写了 re-defer，但 `docs/AUDIT_DEFERRED_REGISTRY.md` 中无 `R3-B25-PERF-BUDGET-01` 或 `R3-B25-HYG-03` 行；这不满足 AUDIT.plan §3.5 对 `AUDIT_DEFERRED row` 的证据要求。                                                        |
| B5-3 bounded + ResourceGuard                | FAIL | 本轮未执行 smoke，无 smoke log。`production_equivalent_smoke.py` 只有 `--use-service-path` 分支会设置 `guard_exercised=True`；当前 closure_test 未带 `--use-service-path`，即使后续按该命令跑完，也可能输出 `guard_status=not_exercised`。 |
| B5-4 不作 live 授权依据                     | PASS | `phase45_perf_budget.json` 明确写明 `Does not authorize live sources`；`final_pilot_closeout.md` / `final_registry_update.md` 也明确 closeout 为 `PILOT_FAIL_SOURCE`，不打开 production-live access/readiness。                            |

## 证据路径

- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/AUDIT.plan.md`：§3.5 B5-1..B5-4；B5-2 要求 `AUDIT_DEFERRED row`，B5-3 要求 smoke log。
- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/audit.jsonl`：列出 `docs/AUDIT_DEFERRED_REGISTRY.md` 等审计必读源。
- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/research/gitnexus-audit-summary.md`：GitNexus MCP/CLI live query 不可用，需记录限制。
- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/execute-evidence/phase45_perf_budget.json`：schema 完整，状态为 `RE_DEFERRED`，notes 声明不授权 live sources。
- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/execute-evidence/8.7-green.txt`：仅记录 `phase45_perf_budget.json status=RE_DEFERRED owner=batch275-execute`。
- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/execute-evidence/final_pilot_closeout.md`：记录 `phase45_perf_budget.json — RE_DEFERRED`，并将 `R3-B25-PERF-BUDGET-01` / `R3-B25-HYG-03` 留给 Execute / CI。
- `.trellis/tasks/06-21-round3-batch2-75-live-pilot/execute-evidence/final_registry_update.md`：表内写 `R3-B25-PERF-BUDGET-01`、`R3-B25-HYG-03` 仍为 OPEN，但它不是 registry 源文件。
- `docs/AUDIT_DEFERRED_REGISTRY.md`：存在 `R3-B2.75-REQ2-EM`，但不存在 `R3-B25-PERF-BUDGET-01` / `R3-B25-HYG-03`。
- `docs/UNRESOLVED_ISSUES_REGISTRY.md`：存在 `R3-B25-HYG-03` OPEN 行，但没有 `R3-B25-PERF-BUDGET-01` 独立行；且文件声明需与 `AUDIT_DEFERRED_REGISTRY.md` 同步。
- `docs/quality/ROUND3_BATCH25_PENDING_FIX_REGISTRY.md`：A08-P2-01 / A08-P2-02 仍要求 Batch 2.75 前或 CI nightly 刷新 smoke/perf 证据。
- `configs/resource_limits.yaml` 与 `specs/contracts/resource_limits.yaml`：默认 profile 为 `eco`，含线程、DuckDB memory/temp、API 行数/日期窗口限制。
- `scripts/production_equivalent_smoke.py`：接受 `--data-root` 并设置 `QMD_DATA_ROOT`，但当前 closure_test 不含 `--use-service-path`；ResourceGuard 可观察状态依赖 `pytest_resource_guard` step。

## 发现项

### P1 — Re-defer 未写入权威 `AUDIT_DEFERRED_REGISTRY`

`AUDIT.plan.md` B5-2 明确把 re-defer 的证据定义为 `AUDIT_DEFERRED row`。实际 `docs/AUDIT_DEFERRED_REGISTRY.md` 不含 `R3-B25-PERF-BUDGET-01` / `R3-B25-HYG-03`；只有 task-local `final_registry_update.md` 和 `phase45_perf_budget.json` 叙述仍 OPEN。由于 registry policy 声明 registry 是 single source of truth，这属于未闭合延期登记，阻断 PH-B5 PASS。

### P1 — 无 Phase 4.5 smoke log，ResourceGuard 证据不足

执行证据是 `RE_DEFERRED` JSON，而非 smoke PASS log。B5-3 要求 `bounded + ResourceGuard` 的 smoke log；当前没有 elapsed、row count、guard decision、guard log rows 或 `guard_status=observable` 的实际运行证据。静态检查还显示 closure_test 缺少 `--use-service-path`，而脚本只有该分支包含 `pytest_resource_guard` 并将 `guard_exercised=True`。

### P2 — `R3-B25-PERF-BUDGET-01` 在 unresolved/registry 视图中不一致

`final_registry_update.md` 与 `phase45_perf_budget.json` 都提到 `R3-B25-PERF-BUDGET-01` 仍 OPEN，但 `docs/UNRESOLVED_ISSUES_REGISTRY.md` 只保留 `R3-B25-HYG-03` 行，`docs/AUDIT_DEFERRED_REGISTRY.md` 两者均缺失。该不一致会让后续 Batch 3/CI 误判 perf-budget 证据已经被某个别名吸收。

### P2 — Smoke 路径 bounded 约束主要靠调用者约定

`production_equivalent_smoke.py` 能设置 isolated `QMD_DATA_ROOT`，且计划给出的 closure_test 指向 `.audit-sandbox/batch275-perf-smoke`。但脚本本身接受任意 `--data-root` 并创建目录；本审计未发现它强制限制到 `AUDIT_SANDBOX` 或 `.audit-sandbox` 子树。作为执行脚本可接受，但作为审计闭环需要实际 smoke log 证明调用路径正确。

## GitNexus 可用性限制

读取 `.trellis/tasks/06-21-round3-batch2-75-live-pilot/research/gitnexus-audit-summary.md` 后确认：本 Codex 会话无 GitNexus MCP resources；`node .gitnexus/run.cjs status` 在网络沙箱下失败，`query()` / `impact()` / `detect_changes()` 无法作为 live MCP 调用。因此本 PH-B5 结论基于冻结的 GitNexus index summary、静态源码/配置读取和 Execute evidence；未把 GitNexus live query 当作 green evidence。

## 本审计未执行的命令

未运行 `uv run python scripts/production_equivalent_smoke.py --data-root .audit-sandbox/batch275-perf-smoke`，因为该命令会写入 data-root，且用户指令要求需要跑命令时只能用 `AUDIT_SANDBOX` 路径，不得写 production/data。本审计只做只读核对，并只输出本文件。
