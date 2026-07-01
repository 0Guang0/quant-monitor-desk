# R3-DCP-05 — `/to-issues` 垂直切片

> **SSOT：** 切片 AC 仅本文件 · Plan v4.1  
> **依赖：** Wave 1–3 CLOSED · ADR-028 · 用户 11/11 clean 裁决

---

## 垂直切片规则

1. 每片 tracer-bullet：单源或单共享基础设施；可独立 pytest 绿。
2. RED → GREEN 证据：`research/execute-evidence/sNN-red.txt` → `sNN-green.txt`
3. 共享文件 `data_commands.py` / `clean_write_targets.py`：**S00 独占 merge 后** 各源片只追加路由。
4. registry 三件套：**S13 主会话**。

---

## 依赖图

```text
S00 (migration 015 + clean targets + incremental registry)
  → S01 (baostock live) ∥ S02–S07 (macro×5 + fred regress) ∥ S08 (cninfo) ∥ S09 (mootdx)
  → S10 (sec_edgar) ∥ S11 (alpha_vantage) ∥ S12 (deribit)
  → S13 (registry + eastmoney SSOT + catalog)
```

---

## 切片总表

| Slice                   | What to build                                                                                                                                | Acceptance criteria                                             | Blocked by | 测试 / 证据                                                   |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- | ---------- | ------------------------------------------------------------- |
| **S00-SCHEMA-REGISTRY** | migration `015_dcp05_tier_a_clean.sql`；`clean_write_targets` ADR-028 矩阵；`sync/incremental_source_registry.py`（表驱动 canonical domain） | 015 应用绿；registry 解析 11 源；`test_migration_coverage` 更新 | —          | `test_schema_migration` · `test_tierA_incremental_registry_*` |
| **S01-BAOSTOCK-LIVE**   | `sync_baostock_incremental`：`QMD_ALLOW_LIVE_FETCH=1` → `use_mock=False` / `build_product_live_service`                                      | `ACC-BAOSTOCK-NO-LIVE` 关；失败非 exit 0                        | S00        | `test_qmd_data_sync_baostock.py` · optional `--run-network`   |
| **S02-FRED-REGRESS**    | fred 增量回归；确认仍写 `axis_observation`                                                                                                   | DCP-02 测全绿；live primary 仍 open                             | S00        | `test_fred_macro_incremental_*.py`                            |
| **S03-US-TREASURY**     | `ops/us_treasury_incremental_*`；CLI sync；watermark → `axis_observation`                                                                    | replay e2e clean 写绿                                           | S00        | `test_us_treasury_incremental_*`                              |
| **S04-BIS**             | `ops/bis_incremental_*`；`startPeriod` 来自水位（digital-oracle L2）                                                                         | replay e2e clean 绿                                             | S00        | `test_bis_incremental_*`                                      |
| **S05-WORLDBANK**       | `ops/world_bank_incremental_*`                                                                                                               | replay e2e clean 绿                                             | S00        | `test_world_bank_incremental_*`                               |
| **S06-CFTC**            | `ops/cftc_incremental_*`；周频水位                                                                                                           | replay e2e clean 绿                                             | S00        | `test_cftc_incremental_*`                                     |
| **S07-CNINFO**          | metadata watermark `cn_announcement_clean`；`cninfo` incremental run                                                                         | replay e2e clean 绿                                             | S00        | `test_cninfo_incremental_*`                                   |
| **S08-MOOTDX**          | bar 增量仿 baostock；`mootdx` port 窗过滤                                                                                                    | replay e2e `security_bar_1d` 绿                                 | S00        | `test_mootdx_incremental_*`                                   |
| **S09-SEC-EDGAR**       | `us_disclosure_clean` staging adapter；`sec_edgar` incremental                                                                               | replay e2e `us_disclosure_clean` 绿                             | S00        | `test_sec_edgar_incremental_*`                                |
| **S10-ALPHA-VANTAGE**   | `us_equity_daily_bar` incremental → `security_bar_1d`                                                                                        | replay e2e clean 绿                                             | S00        | `test_alpha_vantage_incremental_*`                            |
| **S11-DERIBIT**         | `crypto_derivative_clean` adapter；`deribit` incremental                                                                                     | replay e2e clean 绿                                             | S00        | `test_deribit_incremental_*`                                  |
| **S12-CLI-ROUTER**      | `qmd data sync --source-id` 统一路由 11 源；dry-run JSON 可审计                                                                              | 11 源 help/route 测绿                                           | S01–S11    | `test_qmd_data_sync_tier_a_router.py`                         |
| **S13-REGISTRY-DOCS**   | capabilities/registry 行；`ACC-EASTMONEY-TAXONOMY-001` 文档；`test_catalog.yaml`                                                             | loop_maintain 绿                                                | S12        | loop_maintain · ops 文档                                      |

---

## Issue 骨架（GitHub 可选）

```markdown
### [S0N] <source> incremental clean write

**What:** watermark + incremental CLI + clean upsert per ADR-028
**AC:** replay e2e writes clean; watermark unit; idempotent repeat run
**Blocked by:** S00
**Verify:** 见切片命名（Execute 新建 per-source incremental e2e 测，先例 baostock/fred）
```

---

## Wave 4 并行 worktree 建议

| Worktree           | Slices        | 拥有文件                                                                    |
| ------------------ | ------------- | --------------------------------------------------------------------------- |
| wt-dcp05-core      | S00, S12      | migrations, clean_write_targets, incremental_registry, data_commands router |
| wt-dcp05-baostock  | S01           | baostock_port, baostock tests                                               |
| wt-dcp05-macro-a   | S03, S04      | us_treasury, bis ops                                                        |
| wt-dcp05-macro-b   | S05, S06, S02 | world_bank, cftc, fred regress                                              |
| wt-dcp05-cn        | S07, S08      | cninfo, mootdx                                                              |
| wt-dcp05-us-crypto | S09, S10, S11 | sec_edgar, alpha_vantage, deribit                                           |

**合并顺序：** S00 → 并行源片 → S12 → S13（主会话）
