# Execute 参考项目实读证据 — R3-DCP-03（Execute 填表）

> **状态：** Execute 已填 · 2026-06-30  
> **MAIN_REPO_REFERENCE_ROOT:** `C:\Users\Guang\Desktop\quant-monitor-desk\参考项目`  
> **规则：** 仅登记 **参考项目/** 文件；仓内 `backend/`、`tests/` 写在「仓内复用」节，**不得**标 L1/L2/L3

---

## 1. 参考项目实读表（L1/L2/L3 只填本节）

| #   | 参考项目文件                                                                         | 等级      | 关键符号/行                                      | 本轨处置（复用已落地 / 禁止 / 无需二次拷贝）                                                                                    |
| --- | ------------------------------------------------------------------------------------ | --------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| R1  | `MISSING_REFERENCE_TREE` — `参考项目/` 目录存在但无 EasyXT 源码树（2026-06-30 实查） | L2 已落地 | N/A（仓内 `market_bar_p0` / `ohlcv_rules`)       | 不二次拷贝；对照 `docs/implementation_tasks/ROUND_3_REFERENCE_LANDING/R3D_ops_db_data_health_reference.md` §3 EasyXT 完整性类别 |
| R2  | `MISSING_REFERENCE_TREE` — `unified_data_interface.py` 不可实读                      | **禁止**  | R3D §3 EasyXT boundary                           | 不得 runtime；不得 silent 换源                                                                                                  |
| R3  | `MISSING_REFERENCE_TREE` — JQ2PTrade CLI 段不可实读                                  | L1 已落地 | `ops_db_inspect_contract.yaml` `v1_arguments.db` | 已在 `qmd_ops db-inspect --db`；不二次拷贝                                                                                      |

**替代权威：** `docs/implementation_tasks/ROUND_3_REFERENCE_LANDING/R3D_ops_db_data_health_reference.md` §3 URL + `docs/ops/db_inspect_cli.md` reference_landing

---

## 2. 仓内复用确认（非三等级）

| 文件                                               | Execute 已 Read |
| -------------------------------------------------- | --------------- |
| `backend/app/ops/db_inspector.py`                  | [x]             |
| `backend/app/ops/data_health_profiles/__init__.py` | [x]             |
| `tests/test_baostock_incremental_e2e.py`           | [x]             |
| `tests/test_ops_db_inspector.py`                   | [x]             |
| `tests/fixtures/data_health/good_bundle/`          | [x]             |

---

## 3. 自检

- [x] 本节无把仓内路径标成 L1/L2/L3
- [x] 无 `import` / 运行时依赖 `参考项目/**`
- [x] 与 `reference-adoption-dcp03.md` §2 一致
