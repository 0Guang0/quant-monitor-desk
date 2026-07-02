# Tier A Live Eligibility Matrix（M-DATA-03 S00）

> **固化自：** `PROJECT_IMPLEMENTATION_ROADMAP.md` §0.3.4 @ 2026-07-02  
> **ADR 例外：** 无 — 11/11 须真网验收

---

## 十一源资格表

| source_id       | 真网   | 凭证 / 备注                                    | clean 目标表族            |
| --------------- | ------ | ---------------------------------------------- | ------------------------- |
| `fred`          | **须** | `FRED_API_KEY`                                 | `axis_observation`        |
| `us_treasury`   | **须** | 公开 API                                       | `axis_observation`        |
| `sec_edgar`     | **须** | 公开 API + `SEC_EDGAR_USER_AGENT` + rate limit | `us_disclosure_clean`     |
| `cftc_cot`      | **须** | 公开周频文件                                   | `axis_observation`        |
| `bis`           | **须** | 公开 CSV API                                   | `axis_observation`        |
| `world_bank`    | **须** | 公开 API                                       | `axis_observation`        |
| `alpha_vantage` | **须** | `ALPHA_VANTAGE_API_KEY`                        | `security_bar_1d`         |
| `deribit`       | **须** | 公开 REST                                      | `crypto_derivative_clean` |
| `baostock`      | **须** | 公开（会话）                                   | `security_bar_1d`         |
| `cninfo`        | **须** | 公开 disclosure                                | `cn_announcement_clean`   |
| `mootdx`        | **须** | pytdx 行情                                     | `security_bar_1d`         |

## 验收环境

- `DATA_ROOT` → `.audit-sandbox/m-data-03/`（或 Plan 指定隔离路径）
- `QMD_ALLOW_LIVE_FETCH=1`
- **禁止** 写 `data/duckdb/quant_monitor.duckdb` 主库

## 环境变量（验收必填槽位）

| 变量                    | 源            | 说明                                                     |
| ----------------------- | ------------- | -------------------------------------------------------- |
| `QMD_ALLOW_LIVE_FETCH`  | 全部          | `1` / `true` / `yes`（ADR-027）                          |
| `DATA_ROOT`             | 全部          | 隔离库根；**≠** `data/duckdb` 主库                       |
| `FRED_API_KEY`          | fred          | 用户可提供                                               |
| `ALPHA_VANTAGE_API_KEY` | alpha_vantage | 用户可提供                                               |
| `SEC_EDGAR_USER_AGENT`  | sec_edgar     | SEC fair-access 联系身份（与 `SOURCE_API_KEY_ENV` 一致） |
| （其余 8 源）           | —             | 公开 API；无 KEY 槽位                                    |

## ADR 登记

当前 **无** ADR 例外源。若 Execute 发现某源不可真网，须 **grill-me** 用户后新建 ADR（不得口头 defer）。
