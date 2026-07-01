# Execute 参考实读证据 — Agent B (S02–S06)

> worktree: `quant-monitor-desk-wt-dcp05-s02-s06` · branch: `feature/dcp05-s02-s06`

## 实读清单

- [x] `参考项目/digital-oracle/digital_oracle/providers/bis.py` L46–66 · **L2** · `startPeriod` 来自 query.start_year；QMD 用 `FetchRequest.start_time` → `bis_port` start_year
- [x] `参考项目/OpenBB/.../fetcher.py` L36–85 · **L3 对齐** · watermark→transform_query→extract→transform；不拷贝 Fetcher 类，走 `DataSyncOrchestrator.run_incremental`
- [x] `参考项目/EasyXT/.../unified_data_interface.py` L172–244 · **forbidden** · sync 路径禁止 silent fallback 到在线源
- [x] `参考项目/EasyXT/.../auto_data_updater.py` L31–32, L87–97 · **forbidden** · 禁止 sys.path / DataManager 进入 sync
- [x] 仓内 `backend/app/ops/fred_incremental_run.py` + `fred_incremental_watermark.py` · 承接模板 · 宏观五源复制金路径
- [x] 仓内 `tests/test_fred_macro_incremental_e2e.py` · e2e 先例 · replay + idempotent + EMPTY_RESPONSE

## 对照 Plan 决策

- `reference-adoption-dcp05.md` §2.2 BIS L2 → `bis_incremental_*` + `bis_port` startPeriod 来自 macro watermark 年
- `reference-adoption-dcp05.md` §2.1 OpenBB L3 → 各源 `MacroIncrementalFetchProxy` 注入 `start_time`
- `to-issues-slices.md` S02–S06 → fred 回归 + us_treasury/bis/world_bank/cftc incremental ops + e2e
- ADR-028 → canonical domain → `axis_observation` clean upsert

## 禁止项自检

- [x] 无 runtime import 参考项目
- [x] 无 EasyXT unified_data_interface 式 fallback
- [x] 未改 `clean_write_targets.py` / `incremental_source_registry.py` / `015_*.sql` / `data_commands.py`
