# Audit A6 — Performance（M-DATA-03 Plan R2）

> **维：** A6 · audit-perf  
> **任务：** `.trellis/tasks/m-data-03-tier-a-live`  
> **协议：** plan_protocol_version 4.1  
> **日期：** 2026-07-03  
> **模式：** Audit（只读；无 commit、无改码）

---

## 维度证据

### Boot / 权威对照

| 级别   | 来源                                                                                                               | 与本维结论                                                                     |
| ------ | ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------ |
| 第一级 | `docs/ops/performance_limits.md` · `specs/contracts/production_equivalent_smoke_budget.yaml`（仓内 SSOT）          | 定义 ResourceGuard / eco 模式；**本票未挂载** smoke 预算或 acceptance 延迟 SLA |
| 第二级 | `AUDIT.plan.md` §2 · `plan-revision-r2.md` §2 · `plan-spec.md` · `to-issues-slices.md` · `performance-engineer.md` | **无冻结 perf 阈值**；验收委托正确性（F0/B2/E2/11 源 manifest）与 pytest 全绿  |
| 第三级 | `frozen/M_DATA_03_TIER_A_LIVE.md` · `EXECUTION_INDEX.md` · `integration-audit.md`                                  | 活卡禁止 SKIP 当过关（**功能语义**）；INDEX **无 §2.1 perf 复验行**            |

### AUDIT.plan §2 A6 与 perf 维度关系

| 项                         | 内容                                                                                     |
| -------------------------- | ---------------------------------------------------------------------------------------- |
| AUDIT.plan §2 A6 原文      | `B2 validate_table 11/11` — **功能/数据质量**门禁，非 smoke/ResourceGuard/延迟/吞吐 SLA  |
| `plan-revision-r2.md` §2   | 10 条用户 AC：证据契约 · F0 四族 · B2 主路径 · dispatch · CI · pytest — **零条 perf AC** |
| `plan-spec.md` Success     | 同上 + `uv run pytest -q`；**无** `--durations` / smoke / 内存峰值门槛                   |
| `to-issues-slices.md`      | S-R2-EVIDENCE/F0/B2/DISPATCH/ACCEPT/CI 切片 AC — **零条 perf AC**                        |
| PASS 门槛（AUDIT.plan §1） | 11/11 live · pytest 全绿 · 零主库污染 — **正确性**，非性能                               |
| `audit-skill-paths.yaml`   | A6 = audit-perf；note「无性能要求时 Plan 标 SKIP」                                       |

**结论：** 本票 perf 维度无可对照的冻结指标；按 `audit-finding-schema.md`（A6 Plan 冻结 SKIP）及 `performance-engineer.md` DOUBT 纪律，A6 perf **SKIP**。

### SKIP 五条证实

1. **无 hot path / SLA** — 交付为 `tier_a_live_acceptance.py` 统一验收层 + 11 源 evidence manifest；无 FastAPI 路由、无调度热环、无 `production_equivalent_smoke_budget.yaml` 挂载点。
2. **串行 11 源为显式设计** — `run_acceptance_report` L629 `for sid in sources` 串行 `_process_source_for_report`；R4 sandbox 隔离验收 scope；Plan 未要求并行或 wall-clock 上限。
3. **ResourceGuard 已覆盖 dispatch 入口** — `run_tier_a_live_incremental` L601 调用 `_assert_resource_guard_ok()`（L42–45 `ResourceGuard().check()`）；非 fred-only 旁路（R1 A4-P3-01 关切已消除）。
4. **网络重试有界** — `plan-spec.md` Retry policy：最多 3 次指数退避；contract `network_timeout: limited_retry_then_classify`；非无界 fetch。
5. **INDEX / AUDIT 无 perf 冻结行** — `EXECUTION_INDEX.md` 无 §2.1 Tier perf 复验；无法填可 PASS/FAIL 的「指标 | 阈值 | 实测」perf 表。

### 实现路径 vs 性能特征（计划外扫描）

| 组件                          | 触发时机        | I/O / CPU                                | 数据量级上界                            |
| ----------------------------- | --------------- | ---------------------------------------- | --------------------------------------- |
| `run_acceptance_report`       | CLI `--report`  | 11 源**串行** sync→F0→B2→manifest        | R4 sandbox；每源 isolated db            |
| `run_tier_a_live_incremental` | 每源 dispatch   | ResourceGuard + live fetch + clean write | 单源 incremental 窗（contract binding） |
| `_run_f0_data_health`         | 每源 post-write | `run_data_health_profile` profile 扫描   | 四族 profile；非全市场                  |
| `_run_b2_data_validation`     | 每源 post-write | `DataQualityValidator.validate_table`    | 单 clean_table / rule_set               |
| CI `--quick`                  | nightly         | fred + baostock smoke only               | `plan-spec.md` 显式缩小 scope           |
| 默认 pytest                   | CI/本地         | `@pytest.mark.network` 默认 skip         | `conftest.py` + harness 负向测          |

### performance-engineer checklist

| 检查项                       | 状态        | 说明                                                     |
| ---------------------------- | ----------- | -------------------------------------------------------- |
| Baseline 有证据来源          | **N/A**     | Plan 未冻结 perf 命令                                    |
| EXPLAIN/profile/smoke        | **N/A**     | 无 smoke 挂载；B2/F0 委托功能维                          |
| 优化后同一命令对比           | **N/A**     | 无优化项                                                 |
| sandbox 数据量级与 Plan 一致 | **PASS**    | `.audit-sandbox/m-data-03/` 隔离；mock 测 11 源 manifest |
| 全量 pytest 无无关回归       | **委托 A8** | 本维 durations 参考 only                                 |

### §3.6 证据表（参考 · 非门禁）

| 指标                                                                    | 阈值（Plan 冻结） | 实测                                     | 证据                                                                                                                     |
| ----------------------------------------------------------------------- | ----------------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `test_tier_a_live_harness.py` + `test_tier_a_live_acceptance_report.py` | exit 0（A8）      | 27 passed, 1 skipped                     | Audit 独立复跑                                                                                                           |
| 两模块合并 `--durations=10`                                             | **未冻结**        | 最慢 call **4.04s**（mock 11 源 report） | `uv run pytest tests/test_tier_a_live_harness.py tests/test_tier_a_live_acceptance_report.py --durations=10 -q` → exit 0 |
| `production_equivalent_smoke.py`                                        | **未冻结**        | **未测**                                 | Plan 未挂载 acceptance 路径                                                                                              |
| 内存峰值 / ResourceGuard HARD_STOP                                      | **未冻结**        | **未测**                                 | dispatch 入口有 guard；e2e 测可 monkeypatch                                                                              |
| 11 源 live wall-clock                                                   | **未冻结**        | **未测**                                 | 需 `QMD_ALLOW_LIVE_FETCH=1` + 真网；非本维门禁                                                                           |

### GitNexus

`query(tier_a_live_acceptance run_acceptance_report ResourceGuard, repo=quant-monitor-desk)` → 未直接命中 acceptance 进程（索引 stale，与 `gitnexus-audit-summary.md` 一致）。Audit 以 **代码 Read + pytest 独立复跑** 为准。

---

## §维度裁决

**SKIP**

**SKIP 理由：** M-DATA-03 R2 为 11 源 R4 sandbox **功能验收**（统一 evidence + F0 + B2 + dispatch + CI）；`AUDIT.plan` §2 A6 行写「B2 validate_table 11/11」属**功能矩阵错位**（非 performance 冻结阈值）；`plan-revision-r2.md` §2、`plan-spec.md`、`to-issues-slices.md`、`EXECUTION_INDEX.md` 均无 perf AC / §2.1 perf 复验。无法建立可 PASS/FAIL 的 perf 对照表，故 perf 维 SKIP（非遗漏）。11 源串行、CI `--quick` 缩小、network 默认 skip 均为 plan-spec 显式设计。

---

## 计划内问题

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| —   | —   | 无   | —    | —    | —        | —    |

---

## 计划外发现

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| —   | —   | 无   | —    | —    | —        | —    |

已对抗搜索：`backend/app/ops/tier_a_live_acceptance.py`（`run_acceptance_report` 串行环 · `_process_source_for_report`）· `backend/app/ops/tier_a_live_incremental_dispatch.py`（`ResourceGuard` 入口 · retry 路径）· `tests/test_tier_a_live_*.py` · `plan-spec.md` Retry/Forbidden · `docs/ops/performance_limits.md` · `specs/contracts/live_tier_a_evidence_v1.yaml` · CI `--quick` · pytest `--durations=10` 独立复跑。

**扫描结论：** 无新增生产 hot path 无界 I/O；ResourceGuard 已统一于 dispatch 入口；mock 11 源 report 最慢 ~4s **无冻结基线**，仅作参考，**不构成 finding**。真网 11 源 wall-clock 未在本维度量（Plan 未冻结，且属 ops 手动/`workflow_dispatch` 路径）。
