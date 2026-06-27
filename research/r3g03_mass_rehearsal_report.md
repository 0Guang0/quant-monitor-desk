# R3G-03 大规模预演报告

> 日期：2026-06-27 · 隔离库：`data/duckdb/quant_monitor_r3g03_pilot.duckdb`  
> 脚本：`scripts/r3g03_isolated_pilot_dry_run.py`（dry-run + `--execute`）

## 1. 四路对抗性审计与修复摘要

| 维度      | Agent            | 关键发现                                                                    | 修复状态         |
| --------- | ---------------- | --------------------------------------------------------------------------- | ---------------- |
| 代码质量  | code-reviewer    | after_proof 用全表 COUNT；akshare/yahoo 缺 DH fixture                       | ✅ 已修          |
| ponytail  | code-reviewer    | 删除 `_bars_json_staging_rows` 别名；promote 去掉误用 `_ensure_clean_table` | ✅ 已修          |
| 安全/缺口 | security-auditor | promote 未拒主库；validation_only 需隔离库                                  | ✅ 已修          |
| 主库风险  | security-auditor | 四件套可写 `quant_monitor.duckdb`                                           | ✅ 主库 denylist |

**仍属本阶段可接受（已文档化）：** 三源同表 `market_bar_clean`、无正式 PK、fixture 非 120d 全量、append 叠行风险。

**用户拍板已纳入：** akshare / yahoo_finance（`validation_only`，仅 `r3g03_pilot` 或 `.audit-sandbox` 路径）。

---

## 2. 预演执行结果

### dry-run（5 源）

| 源            | 状态 | validation |
| ------------- | ---- | ---------- |
| baostock      | PASS | PASSED     |
| cninfo        | PASS | PASSED     |
| fred          | PASS | PASSED     |
| akshare       | PASS | PASSED     |
| yahoo_finance | PASS | WARNING    |

证据：`.audit-sandbox/round3g/r3g03_pilot/dry_run_summary.json`

### execute（5 源，隔离库）

| 源            | 状态 | validation | inserted（本次 WM 增量） |
| ------------- | ---- | ---------- | ------------------------ |
| baostock      | PASS | PASSED     | 2                        |
| cninfo        | PASS | PASSED     | 5                        |
| fred          | PASS | PASSED     | 1                        |
| akshare       | PASS | PASSED     | 3                        |
| yahoo_finance | PASS | WARNING    | 3                        |

证据：`.audit-sandbox/round3g/r3g03_pilot/execute_summary.json`  
主库：`key_table_row_counts` + mtime 均未变。

---

## 3. 符合预期 vs 偏离

### 符合预期

- 门禁链 DSS→Route→RG→DH→DbValidation→WM 五源均通过（yahoo WARNING 可接受）。
- `load_rehearsal_bundle` + `staging_rows_from_bundle` 灌 staging，非 smoke `close=10.0` 占位。
- `inserted_updated_row_count` 使用 `WriteManager.rows_inserted` 增量语义。
- promote **硬拒** canonical `quant_monitor.duckdb`。
- validation_only 源（akshare/yahoo）仅允许 pilot / audit-sandbox 目标库。

### 偏离（已知，下轮）

| 偏离                    | 说明                                                                                    |
| ----------------------- | --------------------------------------------------------------------------------------- |
| 同表 `market_bar_clean` | 五源 bar 形落同一表；cninfo 公告 / fred 宏观语义未分表                                  |
| fixture 体量            | r3g01 evidence 小样本（非 120d×10 标的满 cap）                                          |
| 日期窗 vs fixture       | staged fixture 用 `2024-*` 日期；approval 窗 `2026-*`；fixture 路径允许 window fallback |
| yahoo WARNING           | DH profile 结构检查 WARN，不阻断 pilot                                                  |
| 重复 execute            | `append_only` 无 PK，重复跑会叠行（rollback identify-only）                             |

---

## 4. 测试证据

```bash
uv run pytest tests/test_round3g_limited_production_clean_write.py -q   # 含 staging/execute/主库拒止
uv run pytest -q                                                       # 全绿 @ 2026-06-27
```

新增测：

- `test_StagingRowsFromBundle_baostock_*` / `akshare_*`
- `test_PromoteRunner_execute_writesEvidenceRows_notSmokePlaceholder`
- `test_PromoteRunner_refusesCanonicalProductionDbPath`

---

## 5. 待用户拍板（未扩大范围）

- baostock **live fetch** on promote（当前 staged fixture only）
- FRED live 全 10 series + 真 120d API 拉取
- 域分表 / `market_bar_clean` 正式 schema + PK
- 一次 approval 多候选批量 promote

---

## 6. 腿 A/B/C 联跑（2026-06-27）

### 6.1 仅 fixture（未接线）

| 腿        | 结果                 |
| --------- | -------------------- |
| A execute | 14 行 fixture        |
| B/C       | 真网证据未进 promote |

### 6.2 `--live-wire` 接线后（2026-06-27 23:10）

新增 `live_evidence_bridge.py` + `scripts/r3g03_isolated_pilot_dry_run.py --live-wire`。

| 源       | 证据来源                 | promote | inserted                 | validation |
| -------- | ------------------------ | ------- | ------------------------ | ---------- |
| baostock | 腿 B 真网 34 行          | ✅      | **34**（真收盘价 ~1168） | WARNING    |
| fred     | 腿 C 真 API DGS10+VIXCLS | ✅      | **165**                  | PASSED     |
| cninfo   | fixture                  | ✅      | 5                        | PASSED     |
| akshare  | fixture                  | ✅      | 3                        | PASSED     |
| yahoo    | fixture                  | ✅      | 3                        | WARNING    |

**练习库合计 ~210 行**；主库未变。

**首次接线失败（已修）：** DH 缺 `pilot_v2_closeout.json`；FRED 缺 `retrieved_at`；baostock 重复行 → 桥接层去重 + gate sidecar。

**FRED 侧新认知（已同步 `R3G_MASS_REHEARSAL_OPEN_GAPS.md` G10）：** 腿 C（R3E `fred_sandbox_pilot`）产出 `fred_live_fetch_evidence.json`，腿 A promote 只认 `fred_evidence.json` 形态；字段名（`observation_date` vs `date`）、多 series 扁平、DH 门禁文件均不一致，**不能直连**，必须经 `live_evidence_bridge`；闭合归属 Batch 3H fred 活卡（统一证据契约），非再扩 R3G。

证据：`.audit-sandbox/round3g/r3g03_pilot/live_wire_execute_summary.json`
