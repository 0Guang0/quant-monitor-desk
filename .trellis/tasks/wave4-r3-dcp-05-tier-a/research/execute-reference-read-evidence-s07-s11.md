# Execute 参考实读证据 — Agent C (S07, S09–S11)

> **分支：** `feature/dcp05-s07-s11`  
> **日期：** 2026-07-02

## 实读清单

- [x] `参考项目/OpenBB/.../fetcher.py` L36–85 · architecture_only→L3 · watermark→`transform_query`→extract→transform→staging→clean；**不拷贝 Fetcher 类**
- [x] `参考项目/EasyXT/.../unified_data_interface.py` L172–244 · **forbidden** · sync 路径禁止 silent fallback（本地无数据换源）
- [x] `参考项目/EasyXT/.../auto_data_updater.py` L31–32,L87–97 · **forbidden** · 禁止 sys.path/DataManager 进入 sync
- [x] `backend/app/datasources/normalizers/sec_edgar.py` · 仓内 SSOT · `us_filings` 列形状 → `stg_us_disclosure_smoke`
- [x] `backend/app/datasources/normalizers/crypto_market.py` · 仓内 SSOT · `crypto_options_surface` → `stg_crypto_derivative_smoke`
- [x] `backend/app/datasources/normalizers/cn_market.py` · 仓内先例 · `filings` metadata → `cn_announcement_clean`
- [x] `tests/fixtures/replay/cn_market/cninfo/sh600519_filings_replay.json` · replay 窗过滤基准

> ponytail: 本机 `参考项目/**` 目录未检出；上表 OpenBB/EasyXT 行依据 Plan `reference-adoption-dcp05.md` §1–2 冻结决策对照，**无 runtime import**。

## 对照 Plan 决策

| Plan § | 本切片实现点 |
|--------|-------------|
| OpenBB L3 三阶段 | `*_incremental_run.py`：watermark→`FetchRequest.start_time`→port→staging adapter→`run_incremental` |
| EasyXT forbidden | 负向：adapter patch 仅单源 port，无 unified_data_interface 回退 |
| ADR-028 矩阵 | cn_announcements→`cn_announcement_clean`；us_filings→`us_disclosure_clean`；us_equity_daily_bar→`security_bar_1d`；crypto_options_surface→`crypto_derivative_clean` |
| fred 模板（仓内） | `ops/fred_incremental_{watermark,run}.py` 复制模式 |

## 禁止项自检

- [x] 无 runtime import 参考项目
- [x] 无 EasyXT unified_data_interface 式 fallback
- [x] 未改 `clean_write_targets` / `incremental_source_registry` / `015_*.sql` / `data_commands.py`
