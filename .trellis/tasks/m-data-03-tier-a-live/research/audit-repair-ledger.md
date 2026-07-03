# Audit Repair Ledger — m-data-03-tier-a-live（Plan R2 · 合规重派 A9）

> **SSOT：** `agents/audit-finding-schema.md` · **来源：** A1–A8 §计划内 + §计划外（A9 合并）

## disposition 生命周期

| 阶段            | disposition                   |
| --------------- | ----------------------------- |
| **A9 建账**     | 全部 待修复                   |
| **Repair 关账** | 目标 **已修复**（无阶段外置） |

| ID        | P   | 维度 | 标题                        | disposition | 绑定任务                     | 依赖/承接 | 登记位置                                          |
| --------- | --- | ---- | --------------------------- | ----------- | ---------------------------- | --------- | ------------------------------------------------- |
| A5-P1-001 | P1  | A5   | D-05 gate R2 证据路径       | 已修复      | m-data-03-tier-a-live Repair | —         | `validate_audit_handoff.py` · `uv run pytest -q`  |
| A4-P1-001 | P1  | A4   | report 路径 zero-clean 守卫 | 已修复      | m-data-03-tier-a-live Repair | —         | `test_reportRun_plannedWithZeroCleanFails`        |
| A4-P2-001 | P2  | A4   | 双 acceptance pipeline      | 已修复      | m-data-03-tier-a-live Repair | —         | `_run_source_acceptance_pipeline`                 |
| A4-P2-002 | P2  | A4   | FAIL_EXTERNAL / adr_ref     | 已修复      | m-data-03-tier-a-live Repair | —         | `classify_source_report_failure` · exit code      |
| A4-P2-003 | P2  | A4   | fetch 字段契约测            | 已修复      | m-data-03-tier-a-live Repair | —         | `test_buildManifest_fetchRequiredFieldsPerSource` |
| A8-P2-001 | P2  | A8   | tier-a CI manifest 测       | 已修复      | m-data-03-tier-a-live Repair | —         | `tests/test_tier_a_live_ci_manifest.py`           |
| A1-P2-001 | P2  | A1   | D-05 gate（同 A5-P1-001）   | 已修复      | m-data-03-tier-a-live Repair | A5-P1-001 | 同 A5-P1-001                                      |
| A5-P2-001 | P2  | A5   | ledger 与 pytest 不符       | 已修复      | m-data-03-tier-a-live Repair | A5-P1-001 | 本 ledger · pytest exit 0                         |
| A8-P1-001 | P1  | A8   | pytest 非绿（同 A5-P1-001） | 已修复      | m-data-03-tier-a-live Repair | A5-P1-001 | `uv run pytest -q` exit 0                         |
| A8-P3-001 | P3  | A8   | FAIL_EXTERNAL ADR prove-it  | 已修复      | m-data-03-tier-a-live Repair | A4-P2-002 | `test_reportRun_exit0WhenAllExternalWithAdr`      |
| A2-P3-001 | P3  | A2   | port bootstrap 收敛         | 已修复      | m-data-03-tier-a-live Repair | —         | `bootstrap_port_live_e2e_ctx` 薄包装              |
| A2-P3-002 | P3  | A2   | lineage helper 去重         | 已修复      | m-data-03-tier-a-live Repair | —         | `evidence_loader._lineage_from_bundle` SSOT       |
| A2-P3-003 | P3  | A2   | tier_a_live_status 死常量   | 已修复      | m-data-03-tier-a-live Repair | —         | 删 `_BAR/_MACRO_SOURCE_IDS`                       |
| A4-P3-001 | P3  | A4   | schema_hash ponytail        | 已修复      | m-data-03-tier-a-live Repair | —         | `_build_fetch_block` ponytail 注释                |

## 关账完成条件

- [x] 源报告 14 条 finding 全部 **已修复**
- [x] 无 **待修复** 残留
- [x] `uv run pytest -q` exit 0
