# Audit A5 — Completion（M-DATA-03 Plan R2）

## 元信息

| 字段                    | 值                                     |
| ----------------------- | -------------------------------------- |
| 维度                    | A5 — audit-completion                  |
| 任务                    | `.trellis/tasks/m-data-03-tier-a-live` |
| `plan_protocol_version` | 4.1                                    |
| 模板                    | `agents/audit-a5-completion.md`        |
| 审计日期                | 2026-07-03                             |

---

## 维度证据

### Boot 读序（A5 必触）

| #   | 文件                                                                  | 状态 |
| --- | --------------------------------------------------------------------- | ---- |
| 1   | `agents/audit-boot-v4.1.md`                                           | 已读 |
| 2   | `agents/audit-coverage-model.md`（链 B）                              | 已读 |
| 3   | `agents/audit-a5-completion.md`                                       | 已读 |
| 4   | `agents/audit-finding-schema.md`                                      | 已读 |
| 5   | `implement.jsonl`（4 行全文）                                         | 已读 |
| 6   | `research/plan-revision-r2.md` §2                                     | 已读 |
| 7   | `research/to-issues-slices.md` S-R2-F0                                | 已读 |
| 8   | `research/gitnexus-audit-summary.md`                                  | 已读 |
| 9   | `research/archive/non-plan/execute/r2-tier-a-live-accept-evidence.md` | 已读 |
| 10  | `AUDIT.plan.md` §2 A5                                                 | 已读 |

### 独立复验（必做）

| AC / 行                       | 独立复跑命令                                                                                                                                                                            | exit code | 与代码/证据一致                                                 |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- | --------------------------------------------------------------- |
| plan-revision-r2 §2 AC#8 全量 | `uv run pytest -q`                                                                                                                                                                      | **1**     | **否** — `test_validateRepairClose_mData03SpotChecks_pass` FAIL |
| tier-a / F0 专项              | `uv run pytest tests/test_data_health_tier_a_profiles.py tests/test_tier_a_live_dispatch.py tests/test_tier_a_live_acceptance_report.py tests/test_live_tier_a_evidence_contract.py -q` | **0**     | 是                                                              |
| loop_maintain                 | `uv run python scripts/loop_maintain.py`                                                                                                                                                | **0**     | 是                                                              |
| Repair close gate             | `uv run python .trellis/scripts/task.py validate-repair-close .trellis/tasks/m-data-03-tier-a-live`                                                                                     | **1**     | 否 — 缺 `research/l4-tier-a-live-accept-evidence.md`            |
| INDEX §2.1 最弱 2 行          | `EXECUTION_INDEX.md` 无 §2.1 Tier 表                                                                                                                                                    | —         | 不适用（R2 INDEX 未冻结 §2.1）                                  |

**pytest 失败摘录：**

```
FAILED tests/test_validate_audit_handoff.py::test_validateRepairClose_mData03SpotChecks_pass
AssertionError: ['D-05 spot-check: missing research/l4-tier-a-live-accept-evidence.md']
```

**说明：** Audit 环境未 `--run-network` 重跑 11/11 live；Execute 真网 log 见 `r2-tier-a-live-accept-evidence.md`（11/11 PASS · exit 0）；mock/契约测覆盖 F0→B2→E2 pipeline。

### git diff 抽查

| 范围        | 结论                                                                               |
| ----------- | ---------------------------------------------------------------------------------- |
| 未提交变更  | `EXECUTION_INDEX.md` status · `project_map.generated.*` · `test_catalog.yaml`      |
| F0 生产路径 | 无本审计会话 diff；`data_health_profiles/*` · `tier_a_live_acceptance.py` 已在分支 |
| scope 扩大  | 未见新 migration / 主库写 / 参考项目 runtime import                                |

### AUDIT.plan §2 A5 焦点 — F0 四族 · 禁 SKIP

| 检查项                | 结果 | 锚点                                                                                                    |
| --------------------- | ---- | ------------------------------------------------------------------------------------------------------- |
| 四族 profile 注册     | PASS | `data_health_profiles/__init__.py` `_SUPPORTED_PROFILES` 含 market_bar / layer1 / disclosure / crypto   |
| 11 源 binding 路由    | PASS | `test_allTierASources_bindingRoutesToSupportedProfile` · `live_tier_a_evidence_v1.yaml` source_bindings |
| acceptance 接入 F0    | PASS | `_run_f0_data_health` ← `run_source_live_acceptance` · `_process_source_for_report`                     |
| 无 raw → FAIL 非 SKIP | PASS | `_run_f0_data_health` L243–244；`test_runF0DataHealth_failsWhenNoRawEvidence`                           |
| 残缺证据 → FAIL       | PASS | `test_f0_partialFredPayload_returnsFail` · `test_runF0DataHealth_failsOnIncompleteFredEvidence`         |
| 契约 forbidden skip   | PASS | `live_tier_a_evidence_v1.yaml` acceptance.forbidden: skip/skipped/inspect_only_without_health           |
| F0 FAIL 阻断 pass     | PASS | `test_runSourceLiveAcceptance_f0Fail_blocksPass`                                                        |
| 生产代码无 SKIP 符号  | PASS | `rg SKIP tier_a_live_acceptance.py data_health_profiles/` 0 命中                                        |

### 切片 AC 评分（R2 · A5 相关）

| Slice                    | AC 摘要               | 代码/测试锚点                                                                                           | 分    | 说明                                      |
| ------------------------ | --------------------- | ------------------------------------------------------------------------------------------------------- | ----- | ----------------------------------------- |
| **S-R2-F0**              | 四族 profile；删 SKIP | `test_fourProfileFamilies_registeredInContract` · `test_data_health_tier_a_profiles.py`                 | **5** | 四族齐全；无 SKIP 路径；11 源路由闭合     |
| **S-R2-ACCEPT**          | F0 在 report 路径     | `test_runSourceLiveAcceptance_f0Path_exercisesHealthWithMockSync` · `r2-tier-a-live-accept-evidence.md` | **5** | F0/B2/E2 编排完整；Execute 11/11 证据齐备 |
| **S-R2-EVIDENCE**        | manifest + forbidden  | `test_buildManifest_*` forbidden 断言                                                                   | **5** | manifest 不含 skip 词汇                   |
| plan-revision-r2 §2 AC#8 | pytest exit 0         | `uv run pytest -q`                                                                                      | **1** | gate 路径漂移致全量红                     |

### plan-revision-r2 §2 用户 AC 追溯（F0 / 完成度相关）

| #   | AC                        | 追溯                                                         | 分    |
| --- | ------------------------- | ------------------------------------------------------------ | ----- |
| 2   | 无 SKIP                   | 契约 forbidden + 实现 FAIL-closed                            | **5** |
| 3   | F0 四族                   | `run_data_health_profile` 四路由                             | **5** |
| 8   | `uv run pytest -q` exit 0 | 独立复验 **exit 1**                                          | **1** |
| 10  | Execute 证据              | `archive/non-plan/execute/r2-tier-a-live-accept-evidence.md` | **5** |

---

## §维度裁决

**FAIL**

---

## 计划内问题

| ID        | P   | 标题                                           | 锚点                                                                                                                         | 根因                                                                                                                                                                               | 修复方案                                                                                                                                                                                      | 验证                                                                                                                                  |
| --------- | --- | ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| A5-P1-001 | P1  | D-05 gate 仍要求 R1 证据路径，全量 pytest 不绿 | `validate_audit_handoff.py` L255–264 · `plan-revision-r2.md` §2 AC#8/#10 · `test_validateRepairClose_mData03SpotChecks_pass` | Plan R2 将关账证据迁至 `archive/non-plan/execute/r2-tier-a-live-accept-evidence.md`，但 `_spot_check_m_data_03_repair_close` 仍硬编码 `research/l4-tier-a-live-accept-evidence.md` | 更新 `validate_audit_handoff.py`：接受 `r2-tier-a-live-accept-evidence.md`（`research/` 或 `archive/non-plan/execute/`）并校验含 `exit 0`/`11/11`；同步 `test_validate_audit_handoff.py` 断言 | `uv run pytest -q` exit 0；`uv run python .trellis/scripts/task.py validate-repair-close .trellis/tasks/m-data-03-tier-a-live` exit 0 |

## 计划外发现

| ID        | P   | 标题                                               | 锚点                                                                  | 根因                                                                     | 修复方案                                                                             | 验证                                               |
| --------- | --- | -------------------------------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ | -------------------------------------------------- |
| A5-P2-001 | P2  | audit-repair-ledger 自述 pytest 全绿与独立复验不符 | `research/audit-repair-ledger.md` L17 · 本报告独立 `uv run pytest -q` | A9 合并时 ledger 勾选 `[x] pytest exit 0` 但未绑定 gate 漂移后的真实结果 | Repair 关账前重跑 pytest；修正 ledger 关账条件勾选；或先修 A5-P1-001 后再更新 ledger | `uv run pytest -q` exit 0 后 ledger 关账条件可核对 |

已对抗搜索：`plan-revision-r2.md` §2 · `to-issues-slices.md` S-R2-F0 · `data_health_profiles/**` · `tier_a_live_acceptance.py` · `live_tier_a_evidence_v1.yaml` forbidden · `r2-tier-a-live-accept-evidence.md` · `validate_audit_handoff.py` D-05 · git diff · R1 `audit-a5-report.md` A5-P2-001（F0 未接入，**已闭合**）。
