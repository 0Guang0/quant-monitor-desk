# Audit A6 — Performance（R3-DCP-09 quick / nightly 分层）

> **维：** A6 performance（`agents/performance-engineer.md`；聚焦 quick profile / nightly CI 分层 perf）  
> **协议：** plan_protocol_version 4.1  
> **任务：** `07-02-wave4-r3-dcp-09-backfill-ci`  
> **日期：** 2026-07-02  
> **工作目录：** `quant-monitor-desk-wt-dcp09`

---

## 维度证据

### 冻结阈值（INDEX §2.1 / to-issues-slices S03）

| 台账 / AC                       | 阈值（冻结）                                | 实测                              | 证据（命令与输出）                                                                                      |
| ------------------------------- | ------------------------------------------- | --------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `WAVE3-ACC-OPT-01` quick 总时长 | **< 300s（5min）**                          | **无自动化 gate**；仅结构契约测绿 | `EXECUTION_INDEX.md` §2.1；`test_wave3_isolated_acceptance_quick_profile.py` 只断言 `_build_steps` 差分 |
| quick 跳过 `pytest_full`        | quick 步骤无 `pytest_full`                  | **PASS**                          | `uv run pytest -q tests/test_wave3_isolated_acceptance_quick_profile.py` → 2 passed                     |
| nightly network 子集            | 单 node id + `--run-network`；非全量 pytest | **PASS**（分层设计）              | `test_nightly_ci_manifest.py`；`.github/workflows/nightly.yml` L29–30                                   |
| PR `ci.yml` 无 network          | 不得 `--run-network`                        | **PASS**                          | `rg run-network .github/workflows/ci.yml` → 0 命中                                                      |
| `prod_equiv_smoke` 单步预算     | `elapsed_s_max: 180`                        | 契约存在；quick 仍执行该步        | `specs/contracts/production_equivalent_smoke_budget.yaml`                                               |

### Quick profile 步骤与 Audit 独立计时（sandbox）

| 步骤                           | quick 含？       | Audit 计时 / 备注                       |
| ------------------------------ | ---------------- | --------------------------------------- |
| `production_gate`              | ✓                | evidence 样本 0.46s                     |
| `init_db`                      | ✓                | 0.49s                                   |
| `sync_registry`                | ✓                | 0.76s                                   |
| `pytest_full`                  | **✗（仅 full）** | 文档 ~200s；quick 设计目标即跳过        |
| `prod_equiv_smoke`             | ✓                | 契约上限 **180s**；占 5min 预算 **60%** |
| `round3_gate_matrix`           | ✓                | **3.9s**（`uv run pytest` 五文件子集）  |
| `wave3_dcp_tests`              | ✓                | **27.0s**（七文件子集）                 |
| qmd ×3 + `loop_maintain_check` | ✓                | evidence 合计 ~3.8s                     |

Quick 共 **10** 步（full 11 步）；移除集合 `{'pytest_full'}`。

**粗算余量（步骤均成功时）：** 固定开销 ~6s + 子集 pytest ~31s + `prod_equiv_smoke` ≤180s → 最坏约 **217s < 300s**；余量约 **83s**，无回归测试绑定。

### Nightly 分层 perf 面

| 项              | 设计                                                                          | Audit 结论                                                        |
| --------------- | ----------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| 与 PR 分离      | `ci.yml` 无 network；`nightly.yml` 专责                                       | 符合 ADR-030 §3                                                   |
| Network 负载    | 单测 `test_livePilot_phase3RawOnly_threeRequestsLive`（`@network`/`slow`）    | 避免 integration-audit 所述「nightly 跑全量 pytest ~200s+ flake」 |
| Live acceptance | 第二步 `wave3_live_production_acceptance.py --fail-on-severity HIGH,CRITICAL` | 真网/profile 更重；**INDEX §2.1 无冻结时长**                      |
| Manifest 契约   | `workflow_dispatch` + node id + findings gate                                 | `uv run pytest -q tests/test_nightly_ci_manifest.py` → pass       |

### 独立复验命令

```text
# 契约测（结构 + manifest）
uv run pytest -q tests/test_wave3_isolated_acceptance_quick_profile.py tests/test_nightly_ci_manifest.py
→ .. [100%] exit 0

# quick 步骤枚举
uv run python -c "… mod._build_steps(quick=True) …"
→ QUICK 10 steps; REMOVED {'pytest_full'}

# 子集耗时（QMD_DATA_ROOT=.audit-sandbox/a6-perf）
round3_gate_matrix → 3.9s exit 0
wave3_dcp_tests    → 27.0s exit 0
```

### DOUBT 核对

| 问题                                | 结论                                                         |
| ----------------------------------- | ------------------------------------------------------------ |
| 指标在声明 sandbox 量级下是否成立？ | quick 子集计时在本地 sandbox 可复现；**但总时长 <5min 未测** |
| Execute evidence 与 Audit 同命令？  | 契约测一致；**无 execute 侧 `--quick` 端到端 elapsed 证据**  |
| nightly 是否误跑全量 pytest？       | **否**；workflow 仅 1 个 network node + live script          |

---

## §维度裁决

**FAIL**

---

## 计划内问题

| ID        | P   | 标题                           | 锚点                                                                                                                             | 根因                                                                                                                                                    | 修复方案                                                                                                                                                                                       | 验证                                                                                                                                                                                                    |
| --------- | --- | ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A6-P2-001 | P2  | quick `<5min` AC 无 perf gate  | `EXECUTION_INDEX.md` §2.1 `WAVE3-ACC-OPT-01`；`to-issues-slices.md` S03 AC；`test_wave3_isolated_acceptance_quick_profile.py`    | Execute 仅以 `_build_steps` 差分关账；未复跑 `wave3_isolated_production_acceptance.py --quick` 或断言 evidence 总 `elapsed_s ≤ 300`                     | 新增契约测（或扩展现有测）：在 sandbox 跑 `--quick`，解析 `acceptance_evidence.json` 对各步 `elapsed_s` 求和（或脚本顶层计时）并 `assert total_s <= 300`；失败写清超阈值步骤                   | `uv run pytest tests/test_wave3_isolated_acceptance_quick_profile.py -q` 含时长断言；或 `uv run python scripts/wave3_isolated_production_acceptance.py --quick` + jq 校验 `sum(steps[].elapsed_s)<=300` |
| A6-P2-002 | P2  | quick 余量窄且无 perf 回归护栏 | `scripts/wave3_isolated_production_acceptance.py` `_build_steps`；`production_equivalent_smoke_budget.yaml` `elapsed_s_max: 180` | quick 只删 `pytest_full`；仍串行 `prod_equiv_smoke`（上限 180s）+ `wave3_dcp_tests`（Audit ~27s）+ `round3_gate_matrix`（~4s）；子集文件膨胀即可破 5min | 在 A6-P2-001 时长 gate 基础上：将 quick 子集登记入 `test_catalog.yaml`/`EXECUTION_INDEX.md` §2.1 冻结文件列表；`prod_equiv` 超预算即 fail acceptance；或 ponytail 再拆「smoke-only quick」tier | 同上时长 gate；故意临时调低 `elapsed_s_max` 或增 1 个 slow 测文件 → gate **RED**                                                                                                                        |

---

## 计划外发现

| ID        | P   | 标题                          | 锚点                                                              | 根因                                                                               | 修复方案                                                                                                                                      | 验证                                                                      |
| --------- | --- | ----------------------------- | ----------------------------------------------------------------- | ---------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| A6-P3-001 | P3  | nightly tier 无冻结 perf 阈值 | ADR-030 §3 nightly 两步；`nightly.yml`；`EXECUTION_INDEX.md` §2.1 | 仅 quick 有 `<5min`；network 子集 + live acceptance 串行无 job 时长/重试预算文档化 | 在 ADR-030 或 `docs/ops/nightly_ci.md` 增补参考 SLA（如 network 子集 p95、live script 上限）及 GH job `timeout-minutes`；或绑任务 ID 阶段外置 | `rg timeout-minutes .github/workflows/nightly.yml` 命中；文档含可核对上限 |

已对抗搜索：`wave3_isolated_production_acceptance.py` · `nightly.yml` · `nightly_ci.md` · `production_equivalent_smoke_budget.yaml` · `ci.yml` network 隔离 · `integration-audit.md` nightly 全量 pytest 风险 · Execute `s03-green.txt`/`s04-green.txt`（无 elapsed 数字）。
