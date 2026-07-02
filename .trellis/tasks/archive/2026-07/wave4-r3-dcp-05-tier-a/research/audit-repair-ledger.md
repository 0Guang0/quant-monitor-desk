# Audit Repair Ledger — wave4-r3-dcp-05-tier-a

> **SSOT：** `agents/audit-finding-schema.md` · **Repair 关账：** 2026-07-02

## disposition 生命周期

| 阶段            | disposition 允许值         |
| --------------- | -------------------------- |
| **A9 建账**     | **待修复** \| **阶段外置** |
| **Repair 关账** | **已修复** \| **阶段外置** |

| ID        | P   | 维度  | 标题                                               | disposition | 绑定任务                    | 依赖/承接                   | 登记位置                                                                     |
| --------- | --- | ----- | -------------------------------------------------- | ----------- | --------------------------- | --------------------------- | ---------------------------------------------------------------------------- |
| A1-P2-001 | P2  | A1    | AUDIT.plan 缺 §0.1 Trace Authority                 | 已修复      | R3-DCP-05 Repair            | AUDIT.plan 模板             | `AUDIT.plan.md` §0.1                                                         |
| A1-P2-002 | P2  | A1    | 切片依赖图与切片表 S07–S13 漂移                    | 已修复      | R3-DCP-05 Repair            | to-issues-slices SSOT       | `to-issues-slices.md` 依赖图                                                 |
| A1-P2-003 | P2  | A1    | 活卡主库 silent 写禁令未下沉 ENTRY §2              | 已修复      | R3-DCP-05 Repair            | ENTRY §2                    | `00-EXECUTION-ENTRY.md` §2                                                   |
| A1-P2-004 | P2  | A1    | EXTERNAL §A 与 ENTRY §5.2 不一致                   | 已修复      | R3-DCP-05 Repair            | EXTERNAL-INDEX              | `00-EXECUTION-ENTRY.md` §5.2                                                 |
| A2-P2-001 | P2  | A2    | ADR-028 MACRO 别名矩阵未落全                       | 已修复      | R3-DCP-05 Repair            | clean_write_targets         | `clean_write_targets.py` MACRO_DOMAINS                                       |
| A2-P2-002 | P2  | A2    | 四份宏观 watermark 薄 shim 可删                    | 已修复      | R3-DCP-05 Repair            | \*\_incremental_run.py      | 删除 4 watermark shim                                                        |
| A2-P2-003 | P2  | A2    | enabled_source_registry 五处复制                   | 已修复      | R3-DCP-05 Repair            | macro_incremental_common    | watermark/run 一行 wrapper                                                   |
| A2-P3-001 | P3  | A2    | SEC FetchProxy 重复 Macro 代理                     | 已修复      | R3-DCP-05 Repair            | sec_edgar_incremental_run   | MacroIncrementalFetchProxy                                                   |
| A2-P3-002 | P3  | A2    | 三份 disclosure/crypto validation patch 重复       | 已修复      | R3-DCP-05 Repair            | macro_incremental_common    | incremental_validation_patch_factory                                         |
| A2-P3-003 | P3  | A2    | _load_\*\_route_bundle 四重复制                    | 已修复      | R3-DCP-05 Repair            | macro_incremental_common    | load_incremental_route_bundle                                                |
| A3-P1-001 | P1  | A3    | mootdx sync 绕过 registry validation_only          | 已修复      | R3-DCP-05 Repair            | sync_mootdx_incremental     | mootdx 显式路由 + validation_only 提升                                       |
| A3-P2-001 | P2  | A3    | dry-run 预览强制 enable 禁用源                     | 已修复      | R3-DCP-05 Repair            | tier_a_sync_router          | 生产 SourceRegistry                                                          |
| A3-P2-002 | P2  | A3    | \_dry_run_shell route 非 READY 仍成功 JSON         | 已修复      | R3-DCP-05 Repair            | tier_a_sync_router          | error_for_route_status                                                       |
| A4-P2-01  | P2  | A4    | cftc 缺幂等 replay e2e                             | 已修复      | R3-DCP-05 Repair            | S06                         | test_cftc_incremental_e2e                                                    |
| A4-P2-02  | P2  | A4    | world_bank 缺 EMPTY_RESPONSE e2e                   | 已修复      | R3-DCP-05 Repair            | S05                         | test_world_bank_incremental_e2e                                              |
| A4-P2-03  | P2  | A4    | macro 五源 e2e 仅 COUNT≥1                          | 已修复      | R3-DCP-05 Repair            | S02–S06                     | raw_value 断言                                                               |
| A4-P2-04  | P2  | A4    | 无 staging 终点负向断言                            | 已修复      | R3-DCP-05 Repair            | fred e2e                    | staging 行为断言 + 注释                                                      |
| A4-P3-01  | P3  | A4    | dry-run 容忍 route_status≠READY                    | 已修复      | R3-DCP-05 Repair            | tier_a_sync_router          | 与 A3-P2-002 同修                                                            |
| A5-P2-001 | P2  | A5    | ACC-BAOSTOCK-NO-LIVE 台账未关                      | 已修复      | R3-DCP-05 Repair S13        | 待修复清单/RESOLVED         | `docs/quality/待修复清单.md` §1 · `docs/RESOLVED_ISSUES_REGISTRY.md`         |
| A6-P2-001 | P2  | A6    | ACC-EASTMONEY registry 半交付                      | 已修复      | R3-DCP-05 Repair S13        | eastmoney notes             | `source_registry.yaml` · `source_capabilities.yaml`                          |
| A6-P3-001 | P3  | A6    | registry/capabilities DCP-05 注释不对称            | 已修复      | R3-DCP-05 Repair S13        | source_registry.yaml        | 11 源 clean 表名 notes                                                       |
| A7-P2-001 | P2  | A7    | mootdx CLI 缺隔离门控测                            | 已修复      | R3-DCP-05 Repair S08        | test_qmd_data_sync_mootdx   | 新建测模块                                                                   |
| A7-P2-002 | P2  | A7    | S12 缺 8 源 non-dry-run 测                         | 已修复      | R3-DCP-05 Repair S12        | tier_a router tests         | parametrize USER_AUTH_REQUIRED                                               |
| A7-P3-001 | P3  | A7    | dry-run 可读 canonical 主库水位                    | 已修复      | R3-DCP-05 Repair S12        | tier_a_sync_router          | \_sandbox_db_readable + sandbox 要求                                         |
| A8-P2-001 | P2  | A8    | world_bank 测试薄于 peer                           | 已修复      | R3-DCP-05 Repair S05        | watermark + empty e2e       | test*world_bank_incremental*\*                                               |
| A8-P2-002 | P2  | A8    | test_migration_coverage 未绑 015                   | 已修复      | R3-DCP-05 Repair S00        | test_migration_coverage     | dcp05 015 断言                                                               |
| A8-P2-003 | P2  | A8    | mootdx 缺 watermark-current e2e                    | 已修复      | R3-DCP-05 Repair S08        | mootdx e2e                  | emptyResponse 测                                                             |
| A8-P2-004 | P2  | A8    | CLI main 未知 source-id 未测                       | 已修复      | R3-DCP-05 Repair S12        | tier_a router tests         | cliMain unknown source                                                       |
| A8-P3-001 | P3  | A8    | schema_migration docstring 版本漂移                | 已修复      | R3-DCP-05 Repair S00        | test_schema_migration       | docstring 含 015                                                             |
| DOUBT-001 | P3  | doubt | mootdx dry-run selected_source_id 与生产路由不一致 | 阶段外置    | Wave 4 registry / R3-DCP-08 | ACC-MOOTDX-DRYRUN-ROUTE-001 | `docs/quality/待修复清单.md` §4 · `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5.2 |
