# Audit Repair Ledger — R3-DCP-08 Layer4

> **SSOT：** `agents/audit-finding-schema.md` · **Repair 关账：** 2026-07-02

## disposition 生命周期

| 阶段 | disposition 允许值 |
| --- | --- |
| **A9 建账** | **待修复** \| **阶段外置** |
| **Repair 关账** | **已修复** \| **阶段外置** |

| ID | P | 维度 | 标题 | disposition | 绑定任务 | 依赖/承接 | 登记位置 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A1-P1-001 | P1 | A1 | INDEX §1 证据路径虚假完成 | 已修复 | R3-DCP-08 Repair | v4.1 code-first INDEX | `EXECUTION_INDEX.md` §1 |
| A1-P2-002 | P2 | A1 | 活卡 status/AC 未与 Execute 同步 | 已修复 | R3-DCP-08 Repair | 活卡 §5 | `R3_DCP_08_LAYER4_MARKET_STRUCTURE.md` |
| A1-P2-003 | P2 | A1 | INDEX 缺 §2.1 Tier 验证矩阵 | 已修复 | R3-DCP-08 Repair | audit-boot §2.1 | `EXECUTION_INDEX.md` §2.1 |
| A1-P2-004 | P2 | A1 | 缺 gitnexus-audit-summary.md | 已修复 | R3-DCP-08 Repair | audit-boot 7.pre | `research/gitnexus-audit-summary.md` |
| A1-P3-001 | P3 | A1 | evidence_index.json 空壳 | 已修复 | R3-DCP-08 Repair | loop_maintain | `loop_maintain.py --fix` |
| A1-P3-002 | P3 | A1 | GitNexus 索引未收录新 Layer4 符号 | 已修复 | R3-DCP-08 Repair | post-merge analyze | `research/gitnexus-audit-summary.md` |
| A2-P2-001 | P2 | A2 | clean read 双次扫描 security_bar_1d | 已修复 | R3-DCP-08 Repair | `_fetch_clean_bar_rows` | `clean_read.py` |
| A2-P2-002 | P2 | A2 | staged/clean 重复 lineage 组装 | 已修复 | R3-DCP-08 Repair | `_finalize_market_build` | `market_structure.py` |
| A3-P1-001 | P1 | A3 | mootdx runtime 覆写 registry SSOT | 已修复 | R3-DCP-08 Repair | registry apply | `source_registry.yaml` · `data_commands.py` |
| A3-P2-001 | P2 | A3 | dry-run JSON 强制 selected_source_id 覆写 | 已修复 | R3-DCP-08 Repair | organic routing | `data_commands.py` |
| A4-P2-001 | P2 | A4 | tier_a_clean Builder 负向无 pytest | 已修复 | R3-DCP-08 Repair | test_layer4_clean_read | `test_tierAClean_*` |
| A4-P2-002 | P2 | A4 | e2e lineage 断言过弱 | 已修复 | R3-DCP-08 Repair | e2e assertions | `test_layer4_us_equity_clean_e2e.py` |
| A4-P3-001 | P3 | A4 | flat bar 聚合语义无单测 | 已修复 | R3-DCP-08 Repair | flat bar test | `test_cleanRead_flatBar_*` |
| A4-P2-003 | P2 | A4 | _build_tier_a_clean 重复 SQL | 已修复 | R3-DCP-08 Repair | `_fetch_clean_bar_rows` | `clean_read.py` |
| A4-P2-004 | P2 | A4 | mootdx dry-run 强制覆盖 selected_source_id | 已修复 | R3-DCP-08 Repair | registry routing | `data_commands.py` |
| A4-P2-005 | P2 | A4 | validation_only runtime hack 未移除 | 已修复 | R3-DCP-08 Repair | registry apply | `data_commands.py` |
| A4-P3-002 | P3 | A4 | build_calendar_row 不校验 market_id | 已修复 | R3-DCP-08 Repair | US_EQ guard | `clean_read.py` |
| A4-P3-003 | P3 | A4 | lineage 空 bar fail-closed 无单测 | 已修复 | R3-DCP-08 Repair | lineage test | `test_cleanRead_lineageNoBars_*` |
| A4-P3-004 | P3 | A4 | NULL pre_close 抛 TypeError | 已修复 | R3-DCP-08 Repair | Layer4MarketError | `clean_read.py` |
| A5-P2-001 | P2 | A5 | ACC-MOOTDX registry/台账未关 | 已修复 | R3-DCP-08 Repair | RESOLVED registry | `docs/RESOLVED_ISSUES_REGISTRY.md` |
| A5-P2-002 | P2 | A5 | ACC-LAYER L4 子集台账未记关账 | 已修复 | R3-DCP-08 Repair | §4 更新 | `docs/quality/待修复清单.md` §4 |
| A6-P2-001 | P2 | A6 | DCP-08 eastmoney registry delta 未落地 | 已修复 | R3-DCP-08 Repair | registry YAML | `source_registry.yaml` · `source_capabilities.yaml` |
| A6-P3-001 | P3 | A6 | 待修复清单未反映 DCP-08 部分关账 | 已修复 | R3-DCP-08 Repair | §4 EM 行 | `docs/quality/待修复清单.md` |
| A6-P3-002 | P3 | A6 | ops/registry capabilities SSOT 不对称 | 已修复 | R3-DCP-08 Repair | capabilities notes | `source_capabilities.yaml` |
| A8-P2-001 | P2 | A8 | tier_a_clean Builder 负向未测 | 已修复 | R3-DCP-08 Repair | test_layer4_clean_read | `test_tierAClean_*` |
| A8-P2-002 | P2 | A8 | clean 未来观测闸无 pytest | 已修复 | R3-DCP-08 Repair | future test | `test_tierAClean_rejectsFuture*` |
| A8-P2-003 | P2 | A8 | S08-REG-EM 无 pytest | 已修复 | R3-DCP-08 Repair | eastmoney test | `test_sourceRegistry_eastmoney_*` |
| A8-P3-001 | P3 | A8 | mootdx 测依赖 registry monkeypatch | 已修复 | R3-DCP-08 Repair | registry SSOT | `test_qmd_data_sync_tier_a_router.py` |
| A8-P3-002 | P3 | A8 | e2e 未断言 lineage rule_version | 已修复 | R3-DCP-08 Repair | e2e assert | `test_layer4_us_equity_clean_e2e.py` |
