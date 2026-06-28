# Project Map Omission Check — R3H-02

> Plan 5d 地图倒查 · 2026-06-28

## 对照项

| 地图/索引来源                                | R3H-02 相关条目        | Plan 覆盖               |
| -------------------------------------------- | ---------------------- | ----------------------- |
| `PROJECT_IMPLEMENTATION_ROADMAP.md` §5.0 H-B | 五源 market/crypto     | INDEX §3 + frozen §1    |
| `BATCH_3H_TASK_CARD_MANIFEST.md` R3H-02      | 五 source_id           | 活卡 §1                 |
| `MODULE_COMPLETION_RATING.md` data sources   | market adapters 未完成 | §4.2 baseline           |
| `MIGRATION_MAP.md` datasources               | fetch_ports 扩展       | §4 Target files         |
| `R3G_MASS_REHEARSAL_OPEN_GAPS.md` G2/G13/G16 | yahoo fixture          | grill Q3/Q10；§9.4      |
| `test_r3h_source_final_decisions.py`         | R3H_02 五源            | 活卡 §1 列表一致        |
| `test_provider_catalog.py`                   | proposed_disabled 五源 | Execute 9.6 更新 status |

## 遗漏项

无 Plan 级遗漏；Execute 须创建：

- `tests/test_market_data_adapters.py`
- `tests/test_crypto_market_adapters.py`
- `tests/fixtures/replay/market_data/**`
- `tests/fixtures/replay/crypto_market/**`

## 结论

地图与任务卡一致；无未登记 scope 扩张。

**Omission check complete**
