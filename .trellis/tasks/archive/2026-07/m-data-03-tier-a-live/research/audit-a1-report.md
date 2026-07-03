# Audit A1 — Spec（M-DATA-03 Plan R2）

## 元信息

| 字段                    | 值                                     |
| ----------------------- | -------------------------------------- |
| 维度                    | A1 — audit-spec                        |
| 任务                    | `.trellis/tasks/m-data-03-tier-a-live` |
| `plan_protocol_version` | 4.1                                    |
| 分支                    | `feature/m-data-03-tier-a-live`        |
| 审计日期                | 2026-07-03                             |

## 维度证据 §3.1

### trellis-check（1–7）

| 步骤           | 结果        | 证据                                                                                                                                                             |
| -------------- | ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 变更范围     | PASS        | `git diff master...HEAD` 含 `tier_a_live_*` · `data_health_profiles/*` · `live_tier_a_evidence_v1.yaml` · workflow · tier-a 测；`git status` 仅 Audit 产物未提交 |
| 2 任务工件     | PASS        | `plan-revision-r2.md` §2 · `plan-spec.md` · `to-issues-slices.md` · `00-EXECUTION-ENTRY.md` · `integration-audit.md` 已读                                        |
| 3 包上下文     | PASS        | `task.json` `plan_protocol_version: "4.1"` · `evidence_contract` 指向契约                                                                                        |
| 4 Spec Quality | PASS        | `plan-spec.md` F0 表 11 源与 `live_tier_a_evidence_v1.yaml` `source_bindings` 字段一致（`health_domain` · `health_profile_id` · `clean_table` · `rule_set_id`）  |
| 5 项目检查     | **PARTIAL** | tier-a 专项 `uv run pytest -q tests/test_live_tier_a_evidence_contract.py … test_tier_a_live_dispatch.py` exit 0；**全量** `uv run pytest -q` exit **1**（见下） |
| 6 跨层         | N/A         | 本维未改 UI；Storage→Ops 链由 A5 复验                                                                                                                            |
| 7 manifest     | PASS        | `check.jsonl` 点名 `frozen/M_DATA_03_TIER_A_LIVE.md` · `EXECUTION_INDEX.md`；`audit.jsonl` 三条与 `AUDIT.plan.md` Trace 一致                                     |

### GitNexus

| 查询                                                                             | 结果                                                                  | 处置                                                                                 |
| -------------------------------------------------------------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| `query` `live_tier_a_evidence run_acceptance_report`（repo: quant-monitor-desk） | 未命中 `run_acceptance_report` 进程；返回 live_pilot / ingestion 邻域 | 人工锚点 `tier_a_live_acceptance.py:611` `run_acceptance_report`；索引滞后记入 7.pre |

### Trace Authority（AUDIT.plan §0.1）

| 条目                                                 | 结果     | 证据                                                                                                                                                                                                                           |
| ---------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 用户 AC `plan-revision-r2.md` §2                     | PASS     | 10 条 AC 均可在 `to-issues-slices.md` R2 表 · `plan-spec.md` · `ENTRY` §1/§3 找到对应                                                                                                                                          |
| 切片 AC `to-issues-slices.md`                        | PASS     | S-R2-EVIDENCE…CI 六切片 + 每源 R2 AC 七项                                                                                                                                                                                      |
| 规格 `plan-spec.md` · `live_tier_a_evidence_v1.yaml` | PASS     | `required_tests` 三文件存在且 `loop_maintain` exit 0；契约 11 `source_bindings` 与 `test_liveTierAEvidenceContract_hasElevenSourceBindings`                                                                                    |
| Execute 入口 `00-EXECUTION-ENTRY.md`                 | PASS     | §1 完成条件指向 §2 AC；§5.1 登记 17 文件均存在                                                                                                                                                                                 |
| Plan 5d `integration-audit.md`                       | PASS     | 文档包 PASS；对抗 F-01…F-30 已关账                                                                                                                                                                                             |
| integration-ledger / 机器门禁                        | **FAIL** | `evidence_index.json` · `plan-revision-r2.md` §5 · `plan-boot.md` L33 → `archive/non-plan/execute/r2-tier-a-live-accept-evidence.md`；`validate_audit_handoff.py` D-05 仍查 `research/l4-tier-a-live-accept-evidence.md`（R1） |

### plan-revision-r2 §2 十条对抗审查

| #   | AC                     | Bundle 下沉                                      | 代码/测                                                                                                           |
| --- | ---------------------- | ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| 1   | 契约 11 源 manifest    | contract + S-R2-EVIDENCE                         | `test_liveTierAEvidenceContract_hasElevenSourceBindings`                                                          |
| 2   | 统一 report · 无 SKIP  | plan-spec Forbidden · contract `no_skip_as_pass` | `tier_a_live_acceptance.py` 无 SKIP/`_live_sync_registry`（`rg` 0 命中）                                          |
| 3   | F0 四族 profile        | plan-spec §F0 表 · ENTRY §2                      | `data_health_profiles/__init__.py` `_SUPPORTED_PROFILES` 四族                                                     |
| 4   | B2 validate_table      | S-R2-B2 · contract `source_bindings`             | `test_runB2ValidateTable_usesSourceBindings`                                                                      |
| 5   | E2 inspect 非 FAIL     | S-R2-ACCEPT · 每源 AC#4                          | `test_reportRun_e2InspectNonFailForElevenSources`                                                                 |
| 6   | dispatch 去重 · mootdx | S-R2-DISPATCH · plan-spec matrix 模板            | `test_dispatchModule_hasNoParallelLiveSyncRegistry`；`platform_source_matrix.yaml` mootdx `default_enabled: true` |
| 7   | CI nightly + dispatch  | S-R2-CI · plan-spec CI                           | `.github/workflows/tier-a-live.yml` schedule + `workflow_dispatch` + failure artifact upload                      |
| 8   | pytest 全绿            | ENTRY §3 · AUDIT.plan §1                         | **全量 pytest exit 1**（`test_validateRepairClose_mData03SpotChecks_pass`）                                       |
| 9   | MCR R4                 | S-R2-ACCEPT AC#9                                 | `r2-tier-a-live-accept-evidence.md` §MCR                                                                          |
| 10  | Execute 关账证据       | §5 归档路径 · `evidence_index.json`              | 文件在 `research/archive/non-plan/execute/r2-tier-a-live-accept-evidence.md`；**D-05 gate 未同步**                |

### 独立复验命令

```text
uv run python scripts/loop_maintain.py                          → exit 0
uv run pytest -q tests/test_live_tier_a_evidence_contract.py \
  tests/test_tier_a_live_acceptance_report.py \
  tests/test_tier_a_live_b2_acceptance.py \
  tests/test_tier_a_live_dispatch.py \
  tests/test_data_health_tier_a_profiles.py                     → exit 0
uv run pytest -q                                                → exit 1
  FAILED tests/test_validate_audit_handoff.py::
    test_validateRepairClose_mData03SpotChecks_pass
```

## §维度裁决

**FAIL**

## 计划内问题

| ID        | P   | 标题                                                    | 锚点                                                                                                                                                                                                                                                     | 根因                                                                                                                                                                                                                                                                                   | 修复方案                                                                                                                                                                                                                                                | 验证                                                                                                                                       |
| --------- | --- | ------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| A1-P2-001 | P2  | R2 关账证据路径未下沉至 D-05 validate_repair_close gate | `plan-revision-r2.md` §2#10 · §5 · `to-issues-slices.md` S-R2-ACCEPT · `evidence_index.json` L4 · `.trellis/scripts/common/validate_audit_handoff.py` L255–264 · `tests/test_validate_audit_handoff.py::test_validateRepairClose_mData03SpotChecks_pass` | Plan R2 将关账证据迁至 `archive/non-plan/execute/r2-tier-a-live-accept-evidence.md` 并写入 `evidence_index.json`，但 `validate_repair_close` D-05 spot-check 仍硬编码 R1 路径 `research/l4-tier-a-live-accept-evidence.md` + `post-Repair` 关键字；integration-ledger 与 Bundle 不一致 | 更新 `validate_audit_handoff.py` D-05：读取 `evidence_index.json` `accept_evidence` 或显式 `archive/non-plan/execute/r2-tier-a-live-accept-evidence.md`；断言含 R2 关账关键字（如 `11/11 PASS` · `exit 0`）；同步 `test_validate_audit_handoff.py` 期望 | `uv run pytest tests/test_validate_audit_handoff.py::test_validateRepairClose_mData03SpotChecks_pass -q` exit 0；`uv run pytest -q` exit 0 |

## 计划外发现

| ID  | P   | 标题 | 锚点 | 根因 | 修复方案 | 验证 |
| --- | --- | ---- | ---- | ---- | -------- | ---- |
| —   | —   | 无   | —    | —    | —        | —    |

已对抗搜索：`plan-revision-r2.md` §2 · `plan-spec.md` Interface · `live_tier_a_evidence_v1.yaml` `source_bindings`/`failure_class_canonical` · `to-issues-slices.md` R2 表 · `EXECUTION_INDEX.md` · `integration-audit.md` · `evidence_index.json` · `validate_audit_handoff.py` · `git diff master...HEAD` 生产路径 · GitNexus query · 全量 pytest。
