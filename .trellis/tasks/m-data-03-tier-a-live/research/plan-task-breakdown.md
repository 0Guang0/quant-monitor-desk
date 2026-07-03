# M-DATA-03 Plan — Task Breakdown（R2）

> **SSOT 切片 AC：** `to-issues-slices.md`  
> **用户口径：** `plan-revision-r2.md` §2（不可改）

## Overview

Plan R2：将 11 源 Tier A live 验收从 **partial F0 + SKIP** 升级为 **完整 R4 sandbox** — 统一证据信封、F0 四族、B2 主路径、dispatch 去重、CI。

**前置基线（已交付，非本 Plan 切片）：** DCP-05 replay 增量 + R1 live harness。证据见 `research/archive/non-plan/execute/`。

## Architecture Decisions

| ID      | Decision                                 | Rationale                                     |
| ------- | ---------------------------------------- | --------------------------------------------- |
| D-R2-01 | `live_tier_a_evidence_v1` 为证据 SSOT    | 用户题8；非 staged_pilot manifest v2 产品定义 |
| D-R2-02 | 11 源同一验收层                          | 统一信封 + 分域 `source_bindings`             |
| D-R2-03 | F0 四族 profile；**禁 SKIP**             | 用户 F0 裁决                                  |
| D-R2-04 | B2 `DataQualityValidator` 主路径         | 用户 B2→R4                                    |
| D-R2-05 | dispatch 全量去重                        | 用户 D-08                                     |
| D-R2-06 | mootdx 进 platform matrix                | 用户题10                                      |
| D-R2-07 | CI nightly `--quick` + workflow_dispatch | 用户 CI 裁决                                  |
| D-R2-08 | `FAIL_FIXABLE` / `FAIL_EXTERNAL` + ADR   | 用户题9                                       |
| D-R2-09 | 无新 DDL                                 | ADR-028 封板                                  |
| D-R2-10 | EasyXT health 模板 L2 扩展 F0            | 用户调整2                                     |

## Task List — Plan R2 切片

| Task              | Description                                  | Acceptance criteria       | Verify                                  | Dependencies            |
| ----------------- | -------------------------------------------- | ------------------------- | --------------------------------------- | ----------------------- |
| **S-R2-EVIDENCE** | 实现 `live_tier_a_evidence_v1` manifest 落盘 | 11 源字段齐全；契约测绿   | `test_live_tier_a_evidence_contract.py` | —                       |
| **S-R2-F0**       | 四族 `run_data_health_profile`；删 SKIP      | 每源非 FAIL/BLOCKED       | `test_data_health_*`                    | S-R2-EVIDENCE           |
| **S-R2-B2**       | acceptance 接 `validate_table`               | 11 源按 `source_bindings` | `test_tier_a_live_b2_acceptance.py`     | S-R2-EVIDENCE           |
| **S-R2-DISPATCH** | 去重 + mootdx matrix                         | 无平行 registry           | impact + dispatch 测                    | —                       |
| **S-R2-ACCEPT**   | `--report` JSON + 11/11 live                 | exit 0；报告 11 行        | acceptance 脚本 + 证据 md               | S-R2-F0 · B2 · DISPATCH |
| **S-R2-CI**       | GitHub workflow                              | nightly + manual artifact | workflow 文件                           | S-R2-ACCEPT 本地绿      |

**说明：** S-R2-LEDGER（诚实度回滚）为 Execute/Repair 动作；Plan 阶段已完成文档口径统一，不保留 Repair 产物于 Plan 包。

## Checkpoints

| CP   | 条件                          |
| ---- | ----------------------------- |
| CP-1 | `validate-plan-freeze` exit 0 |
| CP-2 | S-R2-EVIDENCE 契约测绿        |
| CP-3 | S-R2-F0 + S-R2-B2 并行完成    |
| CP-4 | 11/11 R2 live + pytest 全绿   |
| CP-5 | Audit PASS（Execute 后）      |

## Risks

| Risk              | Mitigation                                           |
| ----------------- | ---------------------------------------------------- |
| 外部 API 不稳定   | 有限重试 → `FAIL_EXTERNAL` + ADR                     |
| dispatch 冲击面大 | GitNexus impact 先于改码                             |
| F0 profile 缺口   | EasyXT L2 模板对照；`data_quality_rules.yaml` 已扩展 |

## Open Questions

**无** — 用户 grill 2026-07-03 已关闭。
