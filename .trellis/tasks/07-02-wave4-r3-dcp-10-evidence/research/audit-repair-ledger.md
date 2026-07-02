# Audit Repair Ledger — 07-02-wave4-r3-dcp-10-evidence

> **SSOT：** `agents/audit-finding-schema.md` · **Repair 关账：** 2026-07-02

## disposition 生命周期

| 阶段 | disposition 允许值 |
| --- | --- |
| **A9 建账** | **待修复** \| **阶段外置** |
| **Repair 关账** | **已修复** \| **阶段外置** |

| ID | P | 维度 | 标题 | disposition | 绑定任务 | 依赖/承接 | 登记位置 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A1-P2-001 | P2 | A1 | 活卡路径在 worktree 不可读 | 已修复 | R3-DCP-10 Repair | docs/implementation_tasks 活卡 | `docs/implementation_tasks/.../R3_DCP_10_LAYER5_EVIDENCE_BINDING.md` |
| A1-P3-001 | P3 | A1 | 活卡状态与 Execute 进度不一致 | 已修复 | R3-DCP-10 Repair | 活卡 L11 · task.json | 同上活卡 §状态 |
| A1-P2-002 | P2 | A1 | 缺 gitnexus-audit-summary.md（Boot 7.pre） | 已修复 | R3-DCP-10 Repair A9 | 7.pre 摘要 | `research/gitnexus-audit-summary.md` |
| A1-P3-002 | P3 | A1 | GitNexus 索引滞后 detect_changes 低信号 | 已修复 | R3-DCP-10 Repair | analyze 刷新 | Repair 后 `node .gitnexus/run.cjs analyze` |
| A2-P2-001 | P2 | A2 | S02 e2e 重复 mootdx incremental bootstrap | 已修复 | R3-DCP-10 Repair | incremental_mootdx_support | `tests/incremental_mootdx_support.py` `run_mootdx_replay_incremental` |
| A4-P2-01 | P2 | A4 | e2e 未断言 schema_hash / source_dataset_ids | 已修复 | R3-DCP-10 Repair | S02 e2e | `tests/test_layer5_mootdx_bar_clean_e2e.py` `_assert_adr031_dataset_ids` |
| A4-P2-02 | P2 | A4 | 缺 content_hash fail-closed 单测 | 已修复 | R3-DCP-10 Repair | S01 bridge | `test_layer5Provenance_missingContentHash_raises` |
| A4-P2-03 | P2 | A4 | raw bundle 选取逻辑脆弱 | 已修复 | R3-DCP-10 Repair | fetch_log 路径 | `load_mootdx_raw_bundle_from_fetch_log` |
| A4-P3-01 | P3 | A4 | bundle 缺 schema_version 默认 macro 版 | 已修复 | R3-DCP-10 Repair | bundle_layer5_provenance | `evidence_bundle.py` + `test_layer5Provenance_missingSchemaVersion_skipsMacroSchemaId` |
| A8-P0-01 | P0 | A8 | S02 e2e 在 audit `--basetemp` 下失败 | 已修复 | R3-DCP-10 Repair | tmp_path data_root + path_compat | audit basetemp pytest exit 0 |
| A8-P1-01 | P1 | A8 | S02 raw bundle 加载未绑定 mootdx 源 | 已修复 | R3-DCP-10 Repair | fetch_log + source_id 过滤 | `load_mootdx_raw_bundle_from_fetch_log` |
| A8-P2-01 | P2 | A8 | S02 e2e 未断言 schema_hash 三件套 | 已修复 | R3-DCP-10 Repair | 同 A4-P2-01 | 同上 |
| A8-P2-02 | P2 | A8 | 缺 content_hash 空值 fail-closed 单测 | 已修复 | R3-DCP-10 Repair | 同 A4-P2-02 | 同上 |
| A8-P3-01 | P3 | A8 | audit sandbox 父目录未 bootstrap | 已修复 | R3-DCP-10 Repair | conftest mkdir | `tests/conftest.py` `_ensure_audit_sandbox_pytest_basetemp` |
