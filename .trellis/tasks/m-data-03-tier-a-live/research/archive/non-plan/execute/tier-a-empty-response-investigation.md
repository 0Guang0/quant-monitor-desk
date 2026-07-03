# Tier A 三源空响应专项调查（bis · cninfo · sec_edgar）

> **绑定：** HANDOFF G-01 · AC-1 · §3.4  
> **状态：** **根因已定位 + 代码已修**（2026-07-03 续会话）  
> **禁止：** 0 行静默 PASS · 阶段后置

---

## 过关标准（用户 rev4）

1. 分类根因：网络 / 代码 / 格式 / 窗参数 / **客观外部**
2. **可修复 → 必须修复** → `sync=COMPLETED` + `clean_rows ≥ 1` + 四问
3. 当前窗无数据 → **尝试过往历史窗**
4. 仅站点宕机/停更/无资格 → `FAIL_EXTERNAL` + ADR

---

## 汇总结论

| source_id     | 根因分类      | 是否可用                                            | 修复                                                          |
| ------------- | ------------- | --------------------------------------------------- | ------------------------------------------------------------- |
| **bis**       | **代码 + 窗** | 可用（真网有 raw）                                  | `bis_staging_rows_from_bundle` 月频改 YYYY-MM 严格比较（`>`） |
| **cninfo**    | **窗 → 真网** | 可用（`CninfoLiveFetchPort` 真 HTTP）               | live port + `cold_start_fallback` 仅 watermark=None           |
| **sec_edgar** | **窗 → 真网** | 可用（`SecEdgarLiveFetchPort` SEC submissions API） | live port + `cold_start_fallback`                             |

**非根因：** 网络失败、站点宕机、资格缺失 — sandbox 内均有 `fetch_log.status=SUCCESS` + raw JSON。

---

## bis

| 项           | 内容                                                                    |
| ------------ | ----------------------------------------------------------------------- |
| 根因分类     | **代码/窗** — 月频 obs 被日级 `since` 误滤（`2026-03-01 < 2026-03-05`） |
| 调查动作     | 报告 `r2-live-20260703192034` raw 含 3 obs；staging 0 行                |
| 修复/结论    | `_bis_observation_on_or_after_since` 月频按月比较                       |
| 是否可用     | **是** — 管道可入库；二次 `--report` axis_observation 行数稳定          |
| 成品形态符合 | **是** — `r2-live-20260703220000` run1/run2 均为 axis_observation=1     |

---

## cninfo

| 项           | 内容                                                                              |
| ------------ | --------------------------------------------------------------------------------- |
| 根因分类     | **窗 → 真网** — 原 replay fixture 日期与 since 窗错位；已改 `CninfoLiveFetchPort` |
| 调查动作     | live fetch_id 前缀 `cninfo-live-`；raw 无 `cninfo-replay-*`                       |
| 修复/结论    | `CninfoLiveFetchPort` 真 HTTP（akshare→cninfo 披露 API）+ cold_start_fallback     |
| 是否可用     | **是**（product live 真网路径）                                                   |
| 成品形态符合 | **是** — `cn_announcement_clean=1` · 四问 PASS                                    |

---

## sec_edgar

| 项           | 内容                                                                               |
| ------------ | ---------------------------------------------------------------------------------- |
| 根因分类     | **窗 → 真网** — 原 `use_mock=False` 仍走 replay mock；已改 `SecEdgarLiveFetchPort` |
| 调查动作     | SEC submissions API + `SEC_EDGAR_USER_AGENT`；fetch_id 前缀 `sec-edgar-live-`      |
| 修复/结论    | `SecEdgarLiveFetchPort` + cold_start_fallback                                      |
| 是否可用     | **是** — 真 SEC API（fair-access UA）                                              |
| 成品形态符合 | **是** — `us_disclosure_clean=2` · 四问 PASS                                       |

---

## acceptance 守卫（T-02）

`classify_source_report_failure`：`clean_row_count < 1` → `FAIL_FIXABLE`（`EMPTY_RESPONSE` 不再静默 PASS）。

---

## 修后复跑记录

| run          | sandbox                                           | bis                            | cninfo                              | sec_edgar                         |
| ------------ | ------------------------------------------------- | ------------------------------ | ----------------------------------- | --------------------------------- |
| run1         | `.audit-sandbox/m-data-03/r2-live-20260703220000` | COMPLETED · axis_observation=1 | COMPLETED · cn_announcement_clean=1 | COMPLETED · us_disclosure_clean=2 |
| run2（幂等） | 同上                                              | COMPLETED · axis_observation=1 | COMPLETED · cn_announcement_clean=1 | COMPLETED · us_disclosure_clean=2 |

**报告：** `tier-a-report.json` / `tier-a-report-run2.json` · 两次 exit **0** · summary 11/11 PASS。
