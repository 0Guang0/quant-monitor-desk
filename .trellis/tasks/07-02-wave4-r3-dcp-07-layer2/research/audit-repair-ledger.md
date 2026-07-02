# Audit Repair Ledger — R3-DCP-07

> **源：** `research/audit-a1-report.md` … `audit-a8-report.md`（23 findings）  
> **关账：** 2026-07-02 · **disposition：** 20 **已修复** · 3 **阶段外置**

| ID | P | 维度 | 标题 | disposition | 绑定任务 | 依赖/承接 | 登记位置 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A1-P2-001 | P2 | A1 | Execute 完成声明与 git 追溯断裂 | 阶段外置 | Wave 4 merge 协调 | `DCP-07-MERGE-GATE-001` | `docs/quality/待修复清单.md` §8 · `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5.2 |
| A1-P2-002 | P2 | A1 | 活卡状态/AC 与 Execute 台账漂移 | 已修复 | R3-DCP-07 Repair | `R3_DCP_07_LAYER2_CROSS_ASSET.md` | 活卡 §5 全 `[x]` · 状态 Repair 关账 |
| A1-P2-003 | P2 | A1 | 缺 7.pre gitnexus-audit-summary.md | 已修复 | R3-DCP-07 Repair | audit-boot #15 | `research/gitnexus-audit-summary.md` |
| A1-P3-001 | P3 | A1 | GitNexus 未索引 Layer2 clean reader | 阶段外置 | Wave 4 merge 协调 | `DCP-07-MERGE-GATE-001` | `docs/quality/待修复清单.md` §8 · `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5.2 |
| A2-P2-001 | P2 | A2 | Layer2 e2e 重复 WM/VR 测试 helper | 已修复 | R3-DCP-07 Repair | layer1_clean_e2e_support 模式 | `tests/layer2_e2e_support.py`；sensor_loader + vix e2e import |
| A3-P2-001 | P2 | A3 | clean replay lineage source_dataset_ids 仍标 staged | 已修复 | R3-DCP-07 Repair | ADR-032 fred 溯源 | `snapshot_builder._lineage_source_dataset_id` + e2e 断言 |
| A3-P3-001 | P3 | A3 | source_switched / macro_supplementary 无对称 pytest | 已修复 | R3-DCP-07 Repair | Layer1 先例 | `test_layer2CleanReader_rejectsSourceSwitched` · `rejectsMacroSupplementaryPrefix` |
| A4-P2-001 | P2 | A4 | source_switched=True 无 L2 单测 | 已修复 | R3-DCP-07 Repair | A3-P3-001 同修 | `test_layer2CleanReader_rejectsSourceSwitched` |
| A4-P2-002 | P2 | A4 | macro_supplementary forbidden 无 L2 单测 | 已修复 | R3-DCP-07 Repair | A3-P3-001 同修 | `test_layer2CleanReader_rejectsMacroSupplementaryPrefix` |
| A4-P2-003 | P2 | A4 | 非 fred source_used 无拒绝单测 | 已修复 | R3-DCP-07 Repair | no EasyXT fallback | `test_layer2CleanReader_rejectsNonFredSourceUsed` |
| A4-P2-004 | P2 | A4 | assert_observation_source fred 绑定无单测 | 已修复 | R3-DCP-07 Repair | snapshot builder 入口 | `test_layer2AssertObservationSource_rejectsStagedForFredPrimary` |
| A4-P2-005 | P2 | A4 | production_clean_replay 非 L2-VIX fred 白名单无负向测 | 已修复 | R3-DCP-07 Repair | plan-doubt Q3 | `test_layer2CleanReplayRegistry_rejectsNonP0FredPrimary` |
| A4-P3-001 | P3 | A4 | as_of_end publish_timestamp 过滤无 L2 单测 | 已修复 | R3-DCP-07 Repair | Layer1 对称 | `test_layer2CleanReader_respectsAsOfEndFilter` |
| A4-P3-002 | P3 | A4 | P0 白名单常量在 loader/reader 双份镜像 | 已修复 | R3-DCP-07 Repair | SSOT | `clean_observation_reader` import `P0_CLEAN_REPLAY_ASSET_IDS` from sensor_loader |
| A4-P3-003 | P3 | A4 | registry 负向测 docstring 仍写仅 staged_fixture_only | 已修复 | R3-DCP-07 Repair | production_clean_replay | `test_crossAssetRegistryLoader_rejectsNonStagedMode` · `test_layer2Loader_defaultRejectsProductionLiveMode` docstring |
| A4-P3-004 | P3 | A4 | P0_ROW_CAPS 与 Layer1 VIXCLS cap 无程序化对账 | 已修复 | R3-DCP-07 Repair | cross-layer cap | `test_layer2CleanReader_rowCapMatchesLayer1Vixcls` |
| A5-P2-001 | P2 | A5 | ENTRY/活卡全量 pytest 一次复验未稳定绿 | 已修复 | R3-DCP-07 Repair | loop sandbox 根因 | `uv run pytest -q` 连续 2× exit 0 |
| A5-P2-002 | P2 | A5 | loop 工程测污染任务 .audit-sandbox | 已修复 | R3-DCP-07 Repair | MASTER.plan 夹具 | `check_active_master_tasks.py` · `check_verification_matrix.py` 跳过 `.audit-sandbox`；清理 task sandbox |
| A5-P3-001 | P3 | A5 | GitNexus 索引滞后新符号 | 阶段外置 | Wave 4 merge 协调 | `DCP-07-MERGE-GATE-001` | `docs/quality/待修复清单.md` §8 · `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5.2 |
| A8-P0-001 | P0 | A8 | 全量 uv run pytest -q 未绿 | 已修复 | R3-DCP-07 Repair | A5-P2-002 根因 | `uv run pytest -q` exit 0 |
| A8-P2-001 | P2 | A8 | production_clean_replay P0 白名单缺 loader 负向测 | 已修复 | R3-DCP-07 Repair | A4-P2-005 同修 | `test_layer2CleanReplayRegistry_rejectsNonP0FredPrimary` |
| A8-P2-002 | P2 | A8 | Layer2CleanObservationReader 非白名单 asset 缺负向测 | 已修复 | R3-DCP-07 Repair | P0 whitelist | `test_layer2CleanReader_rejectsNonWhitelistAsset` |
| A8-P3-001 | P3 | A8 | test_catalog.yaml e2e purpose 陈旧 | 已修复 | R3-DCP-07 Repair | loop catalog | `tests/test_catalog.yaml` purpose 对齐 S01 AC |

**关账核对：** 23/23 有 disposition · 20 已修复 · 3 阶段外置（merge gate）· 0 待修复
