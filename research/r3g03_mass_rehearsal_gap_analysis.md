# R3G-03 大规模预演 Gap 分析

> 生成：2026-06-27 · 分支 `master` · 隔离库 `data/duckdb/quant_monitor_r3g03_pilot.duckdb`  
> 范围：合同内三源（baostock / cninfo / fred）+ Layer1–4 建模输入对照

## Debt-Lite 切片计划（Phase B）

| 项            | 内容                                                                                                                                                                 |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Source ID     | 上轮已确认偏离：promote smoke 单行占位                                                                                                                               |
| Owner         | 主会话                                                                                                                                                               |
| Base branch   | `master`                                                                                                                                                             |
| Target branch | `master`（同 worktree 直改）                                                                                                                                         |
| Allowed files | `rehearsal_loader.py`, `rehearsal_runner.py`, `limited_production_entry.py`, `tests/test_round3g_limited_production_clean_write.py`, `research/*`, `scripts/r3g03_*` |
| Forbidden     | `specs/contracts/*`, 主库 `quant_monitor.duckdb`, cap 扩张                                                                                                           |
| Verification  | 新增 RED→GREEN 测 + `uv run pytest` 全绿 + 隔离库 pilot dry-run/execute                                                                                              |
| Evidence      | `.audit-sandbox/round3g/r3g03_pilot/*`, `research/r3g03_mass_rehearsal_report.md`                                                                                    |

---

## 1. 当前可 live / staged 抓取源清单

### 合同允许（R3G-03 `candidate_caps` + 用户 2026-06-27 授权）

| source_id         | domain                    | r3g03 cap                        | 默认启用 | 授权                                 |
| ----------------- | ------------------------- | -------------------------------- | -------- | ------------------------------------ |
| baostock          | cn_equity_daily_bar       | ≤10 symbols, 120d                | yes      | 无                                   |
| cninfo            | cn_announcements          | ≤10 symbols, 120d, metadata_only | yes      | 无                                   |
| fred              | macro_series              | ≤10 series, 120d                 | **no**   | 用户授权 YAML                        |
| **akshare**       | cn_equity_daily_bar       | ≤10 symbols, 120d                | yes      | **用户授权 validation 源；仅隔离库** |
| **yahoo_finance** | us_equity_daily_bar / etf | ≤10 symbols, 120d                | false    | **用户授权 validation 源；仅隔离库** |

### Registry 状态（`source_registry.yaml` + `source_capabilities.yaml`）

| source_id                                     | enabled_by_default | readiness / 备注                                                   |
| --------------------------------------------- | ------------------ | ------------------------------------------------------------------ |
| **baostock**                                  | true               | sandbox_candidate；`fetch_daily_bar` READY                         |
| **cninfo**                                    | true               | sandbox_candidate；`fetch_announcement_index` READY，metadata_only |
| **fred**                                      | false              | sandbox_candidate；live primary RE-DEFERRED Batch 6                |
| akshare                                       | true               | **validation_only**，非 R3G 合同源                                 |
| qmt_xtdata                                    | false              | 需本机授权                                                         |
| yahoo_finance                                 | false              | validation_only，合同禁止                                          |
| tdx_pytdx                                     | false              | PROBE_REDEFERRED                                                   |
| us_treasury / sec_edgar / bis / world_bank 等 | false              | 官方 API，未进 Round3G 合同                                        |

**本轮可纳入预演：** 仅合同三源；live 仅 fred 在 `live_fetch_authorized` + `FRED_API_KEY` + 授权 YAML 时可选。

---

## 2. Layer1–4 推导的本轮应覆盖全集（r3g03 cap 内）

### Layer4（`layer4_market_source_plan.yaml`）

| input_id                   | 源             | 状态              | 本轮                              |
| -------------------------- | -------------- | ----------------- | --------------------------------- |
| L4-CN-A-CALENDAR / BREADTH | baostock, CN_A | sandbox_candidate | **纳入**（通过 A 股日线标的代理） |
| L4-US/HK/FUT/OPTIONS       | none           | deferred          | 不纳入                            |

### Layer3（`layer3_anchor_source_plan.yaml`）

| input_id      | 源             | 状态        | 本轮                     |
| ------------- | -------------- | ----------- | ------------------------ |
| MSFT / OPENAI | staged_fixture | staged_only | 不纳入（合同无 L3 live） |
| NVDA / TSMC   | none           | deferred    | 不纳入                   |

### Layer2（`layer2_source_whitelist.yaml`）

| input_id               | 源             | 状态                  | 本轮        |
| ---------------------- | -------------- | --------------------- | ----------- |
| VIX/HYG/COPPER/HG-MAIN | staged_fixture | fixture_only / staged | 不纳入 live |
| IDX:MISSING            | none           | deferred              | 不纳入      |

### Layer1 宏观 FRED 序列（indicator_spec 抽样）

合同 fred cap 内可选序列（与 pilot 脚本对齐）：

- **环境轴：** DGS10, T10Y3M, M2SL, CPIAUCSL …
- **风险偏好：** VIXCLS, VXVCLS, SP500 …
- **信用压力：** BAA10Y, BAMLH0A0HYM2 …

**Pilot 脚本当前选取：** `DGS10`, `VIXCLS`, `BAA10Y`（3/10 series cap）

### A 股标的（baostock + cninfo 共用）

Pilot：`sh.600000`, `sh.600519`, `sz.000001`, `sh.601318`, `sz.300750`（5/10 symbols）

### 窗口

`2026-02-28` → `2026-06-27`（120 天，符合 r3g03）

---

## 3. 设计预期 vs 现状对照

| 维度                      | 设计预期                                  | 当前实现                              | 判定                                         |
| ------------------------- | ----------------------------------------- | ------------------------------------- | -------------------------------------------- |
| 门禁链                    | DSS→Route→RG→DH→DbValidation→WM           | promote 已走 gates.py 复用            | ✅ 符合                                      |
| Staging 灌数              | 真实 evidence 行 → `stg_foundation_smoke` | **单行 close=10.0 占位**              | ❌ 偏离（本轮修）                            |
| Clean 表                  | 域语义分表（bar / 公告 / 宏观）           | 三源均 `market_bar_clean`             | ⚠️ 偏离（本阶段可接受）                      |
| `market_bar_clean` schema | `schema.sql` 正式定义 + PK                | CTAS 动态创建，无 PK                  | ⚠️ 偏离（本阶段可接受，重复 execute append） |
| Layer2 live               | 无合同源                                  | staged_fixture only                   | ✅ 符合合同                                  |
| L3 NVDA/TSMC              | deferred                                  | 合同无 us_equity                      | ✅ 符合                                      |
| 单候选/次 promote         | approval 一条 candidate                   | 每源一次 promote                      | ✅ 符合                                      |
| cap 双轨                  | r3g03 profile                             | loader `cap_profile="r3g03"`          | ✅ 符合                                      |
| 主库隔离                  | pilot DB only                             | 脚本校验 main mtime                   | ✅ 符合                                      |
| Fixture 体量              | cap 内尽可能满                            | r3g01 fixture 很小（baostock 2 行等） | ⚠️ 证据薄，非代码 bug                        |

---

## 4. 偏离项分级

### 必须本轮修（Blocking for mass rehearsal fidelity）

1. **Smoke 非全量：** `_production_clean_write` / `_sandbox_clean_write` 忽略 `load_rehearsal_bundle` 行数，只插 1 行占位 → 修 `staging_rows_from_bundle` + 共享灌 staging。

### 本阶段可接受（Document + 下轮）

2. **三源同表 `market_bar_clean`：** R3G-03 活卡未要求分表；Layer 语义未落地。
3. **无正式 clean schema / PK：** append 叠行风险已知；rollback dry-run 识别 key range。
4. **Fixture 非 120d 全 bars：** 预演用 staged evidence；真 120d 需 live fetch（baostock 未接 promote live 路径）或扩充 fixture。
5. **Layer2/L3 deferred：** 合同边界正确。

### 阻塞项（需用户拍板才可扩大）

| 项                             | 说明                                        |
| ------------------------------ | ------------------------------------------- |
| Yahoo / NVDA live              | 合同禁止或未登记                            |
| 一次 YAML 多源多候选           | 当前 approval 单 candidate；可多次 promote  |
| baostock live fetch on promote | 未实现；本轮仍 staged fixture               |
| FRED live 全 10 series         | 需 API key + 授权；fixture 仅单 series 样本 |

---

## 5. 建议修复优先级

1. **P0** — bundle → staging 多行灌数（共享 `rehearsal_loader.staging_rows_from_bundle`）
2. **P1** — execute 集成测：clean 行数 = evidence 行数（cap 内），`source_used` 正确
3. **P2** — 隔离库 mass rehearsal 执行 + 偏差报告
4. **P3（defer）** — 域分表、正式 clean DDL、baostock live on promote

---

## 6. 验证命令

```bash
uv run pytest tests/test_round3g_limited_production_clean_write.py -q -k "StagingRows or execute_writesEvidence"
uv run pytest -q
uv run python scripts/r3g03_isolated_pilot_dry_run.py
uv run python scripts/r3g03_isolated_pilot_dry_run.py --execute
```
