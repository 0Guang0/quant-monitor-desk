# A4 Code Quality — R3H-06 Clean Schema

| 字段 | 值                                                                                                                         |
| ---- | -------------------------------------------------------------------------------------------------------------------------- |
| 维度 | A4 — Code Quality                                                                                                          |
| 分支 | `feature/round3h-r3h06-clean-schema`                                                                                       |
| 任务 | `.trellis/tasks/06-29-round3h-r3h06-clean-schema`                                                                          |
| 权威 | `frozen/R3H_06_CLEAN_SCHEMA.md` · `AUDIT.plan.md` A4 · `agents/code-reviewer.md` · `agents/audit-adversarial-authority.md` |
| 日期 | 2026-06-29                                                                                                                 |

## Review Summary

**Verdict:** REQUEST CHANGES

**Overview:** R3H-06 在 bar/cninfo 两域上完成了三域 DDL、`clean_write_targets` 路由、`upsert_by_pk` 与 `market_bar_clean` 清除；12 条 `test_r3h06_clean_schema.py` 全绿。对抗性探针发现 **fred/macro promote execute 路径在写库前即因 `_non_target_row_count` 硬编码 `instrument_id` 而 SQL 崩溃**（`axis_observation` 无此列），三域路由在 macro 域未闭合。另有多处 AUDIT.plan A4 关注点（OHLCV clean 端到端、cninfo/macro 幂等、契约字段校验深度）仅部分覆盖。

---

## 五维评审

### 1. Correctness — REQUEST CHANGES

| 项                             | 结论        | 证据                                                                                                                           |
| ------------------------------ | ----------- | ------------------------------------------------------------------------------------------------------------------------------ |
| bar 域 DDL + 路由 + promote    | ✅          | `013`/`014`；`limited_production_entry._production_clean_write` 走 `resolve_clean_write_target` + `upsert_by_pk`               |
| cninfo 不写 bar 表             | ✅          | `limited_production_entry.py:548-603` 前后 `security_bar_1d` COUNT 门禁；`test_cninfo_no_bar_promote_leavesSecurityBar1dEmpty` |
| bar 重复 promote 幂等          | ✅          | `test_idempotency_duplicatePromote_rowCountStable` 两次 execute 后 COUNT 不变                                                  |
| **macro/fred promote execute** | ❌ BLOCKING | 见 A4-01：`_non_target_row_count` 对 `axis_observation` 查 `instrument_id` → DuckDB `BinderException`                          |
| OHLCV 写入 clean 表            | ⚠️ 未证     | staging 有测；**无** promote 后 `security_bar_1d.open/high/low/volume` 非空断言                                                |
| cninfo/macro 幂等              | ⚠️ 缺口     | 仅 baostock 有重复 execute 测；disclosure/macro 无 G6 对抗测                                                                   |
| `populate_macro_from_bundle`   | ⚠️ 无测     | 仅 rehearsal/promote 代码引用，零 pytest                                                                                       |

**对抗探针（本审执行）：**

```text
run_limited_production_entry(execute=True, source=fred, domain=macro_series,
  target=axis_observation, fred_auth=fred_user_authorization_fixture.yaml)
→ BinderException: Referenced column "instrument_id" not found
   (Candidate bindings: indicator_id, observation_id, ...)
```

### 2. Readability — PASS（含 NON-BLOCKING 债）

- `clean_write_targets.py`（48 行）职责清晰，三域常量 + `resolve_clean_write_target` 单一入口，符合 ponytail。
- `rehearsal_loader.py` 膨胀至 ~627 行：bar/disclosure/macro 三套 populate 同文件，可读但边界变厚；`_fred_staging_rows` 仍注册在 `_STAGING_ROW_BUILDERS` 却与 macro 域实际路径（`populate_macro_from_bundle`）不一致，增加误用风险（A4-08）。
- `limited_production_entry._production_clean_write` 与 `rehearsal_runner._sandbox_clean_write` 并行维护，注释已标注 mirror，长期 drift 风险（A4-09）。

### 3. Architecture — PASS（macro 域例外）

- 采纳冻结卡选项 B：三域分表 + `upsert_by_pk`；`market_bar_clean` 在 `backend/`、`scripts/`、`tests/` 零匹配（9.8 门禁满足）。
- **域路由 SSOT** 集中在 `clean_write_targets.py`，promote 路径已删除硬编码 `append_only`/`market_bar_clean`。
- **有意分叉：** `rehearsal_runner` bar 域仍写 `security_bar_smoke_clean` + `append_only`（L237-241），与 promote 的 `security_bar_1d` + `upsert_by_pk` 不同轨；注释说明 r3g01 预演遗留，但 bar 域 upsert 行为仅 promote 测覆盖（A4-09）。
- `BAR_DOMAINS` 仅含 `cn_equity_daily_bar`；契约允许 `yahoo_finance` → `us_equity_daily_bar`，promote 将 `CleanWriteTargetError`（A4-10，计划外）。

### 4. Security — PASS（局部）

- promote 仍拒 canonical 主库（`_assert_production_db_allowed`）、DATA_ROOT/.audit-sandbox 边界、validation_only 源隔离。
- staging INSERT 使用 `?` 占位符；表名经 `quote_ident`。
- cninfo synthetic metadata 仅 rehearsal fixture，无 BLOB/正文进 clean。
- 无 diff 内密钥/凭证。

### 5. Performance — PASS（A6 SKIP 对齐）

- migration + 小批量 promote；逐行 INSERT staging（ponytail 已知 O(n)）；无全市场 scan。schema 任务无 hot path 回归。

---

## Test Review

| 测试模块                                           | purpose 五字段  | 行为强度              | 缺口                                                   |
| -------------------------------------------------- | --------------- | --------------------- | ------------------------------------------------------ |
| `test_r3h06_clean_schema.py`（12）                 | ✅ 全中文五字段 | DDL/路由/staging 较强 | 缺 macro populate/promote；缺 clean OHLCV；幂等仅 bar  |
| `test_idempotency_duplicatePromote_rowCountStable` | ✅              | 真实双 execute        | 仅 COUNT；不验 OHLCV/lineage 不变                      |
| `test_ohlcv_populateStaging_passesAdjustmentType`  | ✅              | staging 单行          | 未断言 volume/amount；未走 WriteManager→clean          |
| `test_round3g_limited_production_clean_write` 回归 | ✅              | execute 集成          | baostock execute 只断言 `close`，未断言 OHLCV（A4-06） |
| `_table_columns_from_sql` 辅助                     | —               | 正则解析 DDL          | 嵌套括号/多语句时易假阳/假阴（A4-07）                  |

**A8 子集复跑（本审）：**

```text
uv run pytest tests/test_r3h06_clean_schema.py -q --basetemp=.audit-sandbox/pytest
→ 12 passed, exit 0
```

---

## DOUBT（对抗性 · 必填）

| ID       | 级别         | 位置                                          | 发现                                                                                                                                                     | 建议                                                                                                            |
| -------- | ------------ | --------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| DOUBT-01 | **BLOCKING** | `limited_production_entry.py:224-239,546,589` | `_non_target_row_count` 对所有 target 使用 `WHERE instrument_id NOT IN (...)`；`axis_observation` 仅有 `indicator_id`，fred promote execute **写前即崩** | 按域/表选择 key 列（macro→`indicator_id`，disclosure/bar→`instrument_id`），或 macro 域跳过/改用 `indicator_id` |
| DOUBT-02 | IMPORTANT    | `test_r3h06_clean_schema.py`（缺失）          | AUDIT.plan A4「OHLCV 列非空路径」：无 promote 后 `security_bar_1d` OHLCV 非空测                                                                          | 在 idempotency 或新测中 assert `open/high/low/volume IS NOT NULL`                                               |
| DOUBT-03 | IMPORTANT    | `test_r3h06_clean_schema.py`（缺失）          | G6 幂等仅 baostock；cninfo `cn_announcement_clean`、fred `axis_observation` 无重复 execute 测                                                            | 补 disclosure/macro 各 1 条 duplicate promote 测（macro 需先修 DOUBT-01）                                       |
| DOUBT-04 | IMPORTANT    | `rehearsal_loader.py:66-71`                   | `to_bar_staging_values` 在 open/high/low 缺失时用 `close` 回填，可能把「仅 close」源伪装成完整 OHLCV                                                     | 文档化 ponytail 上限；或在 clean 写前对 bar 域 fail-closed（视 Wave 3 需求）                                    |
| DOUBT-05 | NON-BLOCKING | `test_r3h06_clean_schema.py:17-28`            | `_table_columns_from_sql` 非 DDL 解析器，`(…)` 内逗号/嵌套约束可误判                                                                                     | 改用 `PRAGMA table_info` 或 DuckDB `information_schema` 对照                                                    |
| DOUBT-06 | NON-BLOCKING | `test_r3h06_clean_schema.py:179-181`          | `stg_cols == bar_cols` 全列序相等，migration 增列即脆断                                                                                                  | 改为 OHLCV+PK 列集合断言                                                                                        |
| DOUBT-07 | NON-BLOCKING | `limited_production_entry.py:346-377`         | `_validate_before_proof_payload` 不校验 `target_table_row_count`/`affected_key_range_count` 与 DB 实况                                                   | 可选 execute 前 COUNT 对齐，防 stale before_proof                                                               |
| DOUBT-08 | NON-BLOCKING | `rehearsal_loader.py:378-383,222-253`         | `_fred_staging_rows` 注册为 bar staging builder，fred 实际走 macro populate                                                                              | 从 `_STAGING_ROW_BUILDERS` 移除 fred 或显式 raise 防误调用                                                      |

**搜索范围：** `clean_write_targets.py`、`rehearsal_loader.py`、`limited_production_entry.py`、`rehearsal_runner.py`、`013`/`014`、`test_r3h06_clean_schema.py`、`test_round3g_limited_production_clean_write.py`、fred promote 对抗探针、`market_bar_clean` rg（backend/scripts/tests/specs）、`ops_db_inspect_contract.yaml` key_tables、`WriteManager._build_merge_sql` upsert 语义。

---

## 计划外发现

> 已对抗搜索：macro promote 运行时、rehearsal/promote 双轨、yahoo 域、ops key_tables、`_fred_staging_rows` 死路径、before_proof 字段校验深度。

| ID        | 级别         | 位置                                   | 发现                                                                                                                  |
| --------- | ------------ | -------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| AA-R3H-01 | **BLOCKING** | `limited_production_entry.py:224-239`  | 与 DOUBT-01 同根因：macro 域 promote **完全不可用**（非「未测」而是「必失败」）                                       |
| AA-R3H-02 | NON-BLOCKING | `rehearsal_runner.py:237-241`          | r3g01 bar 预演仍 `append_only`→`security_bar_smoke_clean`，不验证 R3H-06 bar upsert 语义                              |
| AA-R3H-03 | NON-BLOCKING | `ops_db_inspect_contract.yaml:164-185` | `cn_announcement_clean` 未入 `key_tables`；promote dry_run 的 `key_table_row_counts` 突变检测覆盖不到 disclosure 表   |
| AA-R3H-04 | NON-BLOCKING | `clean_write_targets.py:7-8`           | `yahoo_finance` 契约域 `us_equity_daily_bar` 未注册，`resolve_clean_write_target` 将 fail-closed                      |
| AA-R3H-05 | NON-BLOCKING | `db_inspector.py:77`                   | 注释已更新 013 migration，与 `instrument_registry`/`security_bar_1d` 入 key_tables 一致；`cn_announcement_clean` 仍缺 |

---

## 全部发现项汇总

| ID    | 级别         | 轴                 | 位置                                                       | 摘要                                                     | 建议                                      |
| ----- | ------------ | ------------------ | ---------------------------------------------------------- | -------------------------------------------------------- | ----------------------------------------- |
| A4-01 | **BLOCKING** | Correctness        | `limited_production_entry.py:224-239,546`                  | macro promote 查 `axis_observation.instrument_id` 不存在 | 域感知 non-target key 或 macro 专用 guard |
| A4-02 | IMPORTANT    | Correctness / Test | `test_r3h06_clean_schema.py`                               | 无 promote→`security_bar_1d` OHLCV 非空路径测            | 补 execute 后 OHLCV 列断言                |
| A4-03 | IMPORTANT    | Correctness / Test | `test_r3h06_clean_schema.py`                               | cninfo/macro 无重复 promote 幂等测                       | 对齐 G6 三域各 1 测                       |
| A4-04 | IMPORTANT    | Correctness        | `rehearsal_loader.py:66-71`                                | close 回填 OHLCV 掩盖缺列源                              | 文档化或 bar 域校验                       |
| A4-05 | NON-BLOCKING | Test               | `test_r3h06_clean_schema.py:359-455`                       | 幂等测仅 COUNT，不验 upsert 后字段稳定                   | 可选 hash/列快照                          |
| A4-06 | NON-BLOCKING | Test               | `test_round3g_limited_production_clean_write.py:1013-1019` | execute 回归只 assert close                              | 扩展 OHLCV 断言                           |
| A4-07 | NON-BLOCKING | Test               | `test_r3h06_clean_schema.py:17-28`                         | DDL 正则解析脆弱                                         | PRAGMA/information_schema                 |
| A4-08 | NON-BLOCKING | Readability        | `rehearsal_loader.py:378-383`                              | fred bar staging builder 与 macro 路径不一致             | 删除或 guard                              |
| A4-09 | NON-BLOCKING | Architecture       | `rehearsal_runner.py:237-241`                              | bar 预演与 promote upsert 双轨                           | 文档或后续统一                            |
| A4-10 | NON-BLOCKING | Architecture       | `clean_write_targets.py:7`                                 | `us_equity_daily_bar` 未路由                             | Wave 3 或显式 defer                       |
| A4-11 | NON-BLOCKING | Architecture       | `ops_db_inspect_contract.yaml`                             | `cn_announcement_clean` 非 key_table                     | 013 后补登记                              |
| A4-12 | NON-BLOCKING | Correctness        | `limited_production_entry.py:346-377`                      | before_proof 行数/符号数不校验                           | execute 前可选对齐                        |

---

## What's Done Well

- **`clean_write_targets.py`** 小而准的域→表/write_mode/PK SSOT，promote 路径已接入并校验 `target_table` 与 router 一致（`limited_production_entry.py:541-545`）。
- **cninfo 负向门禁** 在 promote 路径内联 assert `security_bar_1d` 不变，比纯测试更 fail-closed。
- **migration 014** 重建 `stg_foundation_smoke` 与 `security_bar_1d` 列序对齐，降低 WriteManager 列映射风险。
- **测试文档**：`test_r3h06_clean_schema.py` 12 测均含中文五字段 purpose，符合 GLOBAL_TESTING_POLICY。
- **9.8 清除**：实现路径 `market_bar_clean` 已归零；fixture 已切 `security_bar_1d`。

---

## Verification Story

| 项                  | 结果                                                                                                            |
| ------------------- | --------------------------------------------------------------------------------------------------------------- |
| Tests reviewed      | ✅ 读完 `test_r3h06_clean_schema.py` 全 12 测 + 抽样 `test_round3g_limited_production_clean_write` execute 路径 |
| Build verified      | ✅ `pytest tests/test_r3h06_clean_schema.py` 12 passed                                                          |
| Security checked    | ✅ 主库拒写、路径边界、参数化 SQL；无密钥 diff                                                                  |
| Adversarial runtime | ✅ fred promote 探针复现 BLOCKING（BinderException）                                                            |
| Contract fields     | ⚠️ promote before/after REQUIRED\_\* 与实现一致；YAML 契约未枚举逐字段，before_proof 深校验不足（A4-12）        |

---

## §3.4 摘要（主会话 `audit.report.md`）

| 轴           | 发现                                           | 阻塞?           | 证据             |
| ------------ | ---------------------------------------------- | --------------- | ---------------- |
| Correctness  | macro promote `_non_target_row_count` SQL 错误 | **是**          | A4-01 / 对抗探针 |
| Correctness  | OHLCV clean 端到端、cninfo/macro 幂等未测      | 否（IMPORTANT） | A4-02, A4-03     |
| Readability  | loader 体积 + fred staging 误导                | 否              | A4-08            |
| Architecture | rehearsal/promote bar 双轨；yahoo 域缺口       | 否              | A4-09, A4-10     |
| Security     | promote 边界保持 fail-closed                   | 否              | 代码审阅         |
| Performance  | 无回归                                         | 否              | A6 SKIP          |
| Test         | 12 绿但 macro 路径零覆盖；脆弱 DDL 解析        | 否              | A4-07, A4-03     |

**A4 判定：REQUEST CHANGES — 1 BLOCKING（A4-01）须修复并补 macro promote/幂等测后再 PASS。**
