# Tier B 真网验收 — 网络路径二证据（M-DATA-03 AC-7）

> **日期：** 2026-07-04（UTC+8）  
> **分支：** `feature/m-data-03-tier-a-live`  
> **契约：** `specs/contracts/live_tier_b_evidence_v1.yaml` · ADR-034 §Tier B FAIL_EXTERNAL  
> **诊断方法：** debugging-and-error-recovery（先路径一环境/配置，再路径二客观外因）

---

## 1. 结论摘要

**Amendment @ 2026-07-04（用户确认 · ADR-034 §Tier B）：** Tier B **沙箱关账** — **10/10 源均有验收结论**（6 `PASS` + 4 `FAIL_EXTERNAL`+ADR-034）。允许「Tier B 沙箱验收完成」；**禁止**「10/10 真网 fetch SUCCESS」。后续改链须修订 ADR。

| source_id        | 路径                 | disposition                           | ADR     |
| ---------------- | -------------------- | ------------------------------------- | ------- |
| **stooq**        | **路径二（已接受）** | `FAIL_EXTERNAL` · 站点 JS 反爬        | ADR-034 |
| **akshare**      | **路径二（已接受）** | `FAIL_EXTERNAL` · push2his 链间歇 TLS | ADR-034 |
| **eastmoney**    | **路径二（已接受）** | 同上（与 akshare 同 API 链）          | ADR-034 |
| **sina_finance** | **路径二（已接受）** | 同上（含 sina；push2his 链）          | ADR-034 |

**Tier B 关账口径（rev 2026-07-04）：** 10 源中 6 源 `PASS` · 4 源 **路径二已接受**（stooq + CN 三源）· sandbox `tier-b-closeout` exit 0。

Sandbox 报告：`.audit-sandbox/m-data-03/tier-b-closeout/tier-b-report.json`（2026-07-03）· 网络复测：`.audit-sandbox/m-data-03/tier-b-proxy-retest/`（2026-07-04）

---

## 2. 环境基线（Clash Verge · 7897）

| 项            | 实测值                                                                                          |
| ------------- | ----------------------------------------------------------------------------------------------- |
| mixed-port    | **7897**（`verge.yaml` · `clash-verge.yaml`）                                                   |
| 系统代理      | **开启** — `ProxyEnable=1`，`ProxyServer=127.0.0.1:7897`                                        |
| TUN           | **开启**                                                                                        |
| 东财/新浪规则 | `push2his.eastmoney.com` · `DOMAIN-SUFFIX,eastmoney.com` · `sina.com.cn` → **DIRECT**           |
| 国内 GEOIP    | `GEOIP,CN,DIRECT`                                                                               |
| 代码侧        | `cn_rehearsal_live_ports._bypass_system_proxy()` — `trust_env=False`，绕过 Windows 代理环境变量 |

**路径一判定（代理）：** Clash 对东财/新浪的 DIRECT 规则与代码 bypass **已就位**；三源失败**不能**归因于「国内站被错误送进 7897 代理节点」这一典型配置错误。

---

## 3. stooq — 路径二（已接受 · 客观外因）

### 3.1 现象

- `tier_b_validation_live.StooqLiveFetchPort` 请求 `https://stooq.com/q/d/l/?s=aapl.us&i=d`
- 返回 **HTML**，非 CSV；错误类：`NETWORK_ERROR` · `Stooq returned HTML instead of CSV (bot/geo block)`

### 3.2 复现（2026-07-04 · 多路径一致失败）

| 路径                                       | 结果                                                                                     |
| ------------------------------------------ | ---------------------------------------------------------------------------------------- |
| Python `urllib` 直连（`ProxyHandler({})`） | HTML                                                                                     |
| 系统代理（7897）                           | HTML                                                                                     |
| 显式 `http://127.0.0.1:7897`               | HTML                                                                                     |
| `curl -4` + 浏览器 UA                      | HTML + **JavaScript PoW 挑战**（`This site requires JavaScript to verify your browser`） |

DNS：`stooq.com` → Clash fake-ip `198.18.0.26`（经规则走统一出口后仍为 HTML）。

### 3.3 根因（客观）

**Stooq 站点对非浏览器/无 JS 客户端实施反爬验证**（SHA-256 PoW + `POST /__verify`），不属于本仓库可单靠换代理/DIRECT 规则修复的配置问题；亦非付费登录类，但属于 **站点侧访问控制**。

### 3.4 路径二登记

| 字段        | 值                                                                                                                                                                |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 台账 ID     | `M-DATA-03-STOOQ-EXTERNAL-001`                                                                                                                                    |
| disposition | **阶段外置（已接受）**                                                                                                                                            |
| ADR         | `docs/decisions/ADR-034-m-data-03-tier-a-live-acceptance.md` §Tier B FAIL_EXTERNAL                                                                                |
| 待修复清单  | `docs/quality/待修复清单.md` §8                                                                                                                                   |
| Roadmap     | `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.1.1                                                                                                                        |
| 关闭条件    | (a) 替代 CSV 源/官方 API 接入并 Tier B 单测绿；或 (b) nightly/CI 非封锁 IP 连续 3 次 `stooq` live PASS；或 (c) 产品决策废弃 stooq validation_fetch 绑定并修订契约 |

**本批不得：** 用 mock HTML 冒充 CSV；不得在未关闭条件满足时标 `disposition=pass`。

---

## 4. akshare / eastmoney / sina_finance — 路径二已接受（2026-07-04）

> **当前阶段（用户确认）：** 三源与 stooq 同级 **路径二已接受** @ ADR-034 §Tier B。下列 §4.1–4.4 为关账前诊断证据（路径一排查）；§4.4 路径一动作仍为 **后续升级 ADR 的可选路线**，非当前关账前置。

### 4.1 现象

三源 Tier B live 均经 `_cn_equity_live_bars_from_akshare` → `ak.stock_zh_a_hist` → 东财 `push2his.eastmoney.com` API。

报告错误（典型）：

```
NETWORK_ERROR · direct: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
```

### 4.2 路径一排查结果（非代理主因）

| 检查项                                  | 结果                                                               |
| --------------------------------------- | ------------------------------------------------------------------ |
| Clash 东财 DIRECT 规则                  | 已配置                                                             |
| `_bypass_system_proxy`                  | 已启用                                                             |
| `push2his` DNS                          | 真实 IP `101.226.30.221`（非 fake-ip）                             |
| `curl` 东财主站 `www.eastmoney.com`     | TLS 可达                                                           |
| `curl` `push2his.eastmoney.com/api/...` | **TLS 被对端掐断**（`schannel: server closed abruptly` / exit 56） |
| 显式走 7897 代理                        | `ProxyError` / 失败（与「应 DIRECT」一致，非修复方向）             |
| _burst 复测_（5 次直连）                | **1 成功 / 4 失败** — **间歇性**，非稳定 PASS                      |

### 4.3 根因归类（当前）

1. **东财 `push2his` API 边缘**对本机出口间歇 TLS 断开 / 连接重置（频控、TLS 指纹、时段或线路质量），**不是** Clash 7897 误路由单一根因。
2. 三源共享同一 API 链 — **eastmoney / sina_finance 与 akshare 同缺口**，非三独立外部源。
3. **Tier A `baostock` 可通**与 Tier B CN validation 路径不同 — 不得用 baostock PASS 掩盖 Tier B akshare hist 链未关账。

### 4.4 路径一剩余动作（历史 · 后续升级 ADR 可选路线）

> 2026-07-04 用户已确认 **路径二已接受**，下列动作 **非** 当前关账前置；若任一路径一成功，可修订 ADR 将该源升为真网 PASS。

| #   | 路径一动作                                                            | 通过标准                            |
| --- | --------------------------------------------------------------------- | ----------------------------------- |
| 1   | Clash **关闭 TUN**（保留或关闭系统代理均可）后单源 `--report`         | 连续 3 次 `akshare` fetch `SUCCESS` |
| 2   | **交易时段**（工作日 09:30–15:00 CST）重跑三源                        | 各源至少 1 次 `SUCCESS`             |
| 3   | **换网络**（无 Clash / 手机热点 / CI runner）重跑                     | 三源 `SUCCESS`                      |
| 4   | 代码切换 validation_fetch 至 **baostock 真网 hist**（与 Tier A 同源） | Tier B 三源契约修订 + pytest 绿     |

**历史注：** 关账前曾要求完成路径一后方能升级 ADR；2026-07-04 用户确认直接接受路径二（见 §4.5）。

### 4.5 登记（路径二已接受 · 2026-07-04 用户确认）

| 字段        | 值                                                                                 |
| ----------- | ---------------------------------------------------------------------------------- |
| 台账 ID     | `M-DATA-03-TIERB-CN-HIST-001`（含 akshare / eastmoney / sina_finance）             |
| disposition | **路径二已接受**（ADR-034 §Tier B · 当前阶段）                                     |
| 关联既有    | `ACC-LIVE-NETWORK-AKSHARE-ENV` · `R3-PROMPT14-AKSHARE-VAL-01` · `R3-B2.75-REQ2-EM` |
| 阻塞        | **不阻塞** Tier B 沙箱关账；**禁止**宣称 10/10 fetch SUCCESS                       |
| 升级路径    | §4.4 路径一动作或 baostock hist 链 — 实现后 **修订 ADR-034**                       |

---

## 5. 命令（复现）

```bash
# 单源报告（需 QMD_ALLOW_LIVE_FETCH=1 + .env keys）
QMD_ALLOW_LIVE_FETCH=1 uv run python scripts/tier_b_live_acceptance.py \
  --source-id stooq \
  --data-root .audit-sandbox/m-data-03/tier-b-proxy-retest \
  --report .audit-sandbox/m-data-03/tier-b-proxy-retest/report-stooq.json

# CN 三源
for s in akshare eastmoney sina_finance; do
  QMD_ALLOW_LIVE_FETCH=1 uv run python scripts/tier_b_live_acceptance.py \
    --source-id $s --data-root .audit-sandbox/m-data-03/tier-b-proxy-retest \
    --report .audit-sandbox/m-data-03/tier-b-proxy-retest/report-$s.json
done
```

---

## 6. 与契约 / CLI 的关系

- `live_tier_b_evidence_v1`：`FAIL_EXTERNAL` + `adr_ref` → CLI/report **exit 0**（ADR-034 产品边界）。
- **诚实口径：** exit 0 **不等于** 该源真网 fetch `SUCCESS`；报告行 `disposition=fail` + `failure_class=FAIL_EXTERNAL` 须保留。
- stooq + CN 三源：**用户已接受路径二** @ ADR-034（2026-07-04）。
- **诚实口径：** exit 0 **不等于** 该源真网 fetch `SUCCESS`；允许「Tier B 沙箱验收完成」，禁止「10/10 真网 fetch SUCCESS」。
