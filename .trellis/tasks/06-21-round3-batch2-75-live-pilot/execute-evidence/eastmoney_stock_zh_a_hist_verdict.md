# 东方财富原接口可用性判定 — `stock_zh_a_hist`

> **Date:** 2026-06-21  
> **Scope:** Batch 2.75 Request 2 · `akshare` / `fetch_daily_bar_validation`  
> **Endpoint:** `https://push2his.eastmoney.com/api/qt/stock/kline/get`  
> **AkShare API:** `ak.stock_zh_a_hist(symbol='600519', ...)`

## 判定结果

**不可用**

## 探测矩阵（本机，2026-06-21）

| 客户端                | 路由                             | 目标 host                | 结果                                        |
| --------------------- | -------------------------------- | ------------------------ | ------------------------------------------- |
| `curl.exe`            | 直连 `--noproxy *`               | `push2his.eastmoney.com` | **000**（连接失败，exit 56）                |
| `curl.exe`            | 经 7897 代理                     | `push2his.eastmoney.com` | **000**                                     |
| `curl.exe`            | 直连 + IPv4 pin `140.207.67.156` | `push2his.eastmoney.com` | **000**                                     |
| `curl.exe`            | 直连 + Browser UA/Referer        | `push2his.eastmoney.com` | **000**                                     |
| `curl.exe`            | 直连                             | `quote.eastmoney.com`    | **200**（对照）                             |
| `curl.exe`            | 直连                             | `push2.eastmoney.com`    | **200**（对照）                             |
| Python `requests`     | 系统代理（7897）                 | `push2his.eastmoney.com` | **ProxyError**                              |
| Python `requests`     | `trust_env=False` 直连           | `push2his.eastmoney.com` | **RemoteDisconnected**                      |
| Python `requests`     | IPv4-only + 直连                 | `push2his.eastmoney.com` | **RemoteDisconnected**                      |
| `ak.stock_zh_a_hist`  | 默认 / `_run_akshare_call`       | `push2his.eastmoney.com` | **失败**（同上）                            |
| `ak.stock_zh_a_daily` | 默认 / `_run_akshare_call`       | `finance.sina.com.cn`    | **可用**（5943 行，仅作对照，非原设计接口） |

## 结论说明

1. **问题不在 Clash 路由规则本身**：`push2` / `quote` 子域可通，仅 **`push2his` 子域**在当前网络环境下无法建立 HTTPS 连接。
2. **不是 akshare 包名或参数错误**：`stock_hist_em.py` 调用的 URL/params 与官方文档一致；失败发生在 TCP/TLS 层，未收到 HTTP 响应。
3. **DNS 可达但 API 不可达**：`push2his.eastmoney.com` 解析正常（含 IPv4 `140.207.67.156`），ping 有响应，但 HTTPS 到 kline API 全部失败。
4. **与最初设计对齐**：Request 2 预期为 akshare 东方财富 A 股日线 **validation** 路径（`fetch_daily_bar_validation`），对应 `stock_zh_a_hist` → `push2his`；**不应**以 `stock_zh_a_daily`（新浪）替代作为该接口可用性结论。

## 对 Batch 2.75 的影响

- Request 2 live fetch 在当前环境 **无法 GREEN**（除非改用非原设计的 sina 接口，已明确排除）。
- Request 1（baostock）与 Request 3（akshare macro `bond_zh_us_rate`）不受影响。
- 建议：在 Phase 4/closeout 中将 Request 2 记录为 **`PILOT_SOURCE_UNREACHABLE`** / eastmoney hist endpoint blocked，保留失败证据，不 silent fallback。
