# R3H-08 — 24 源 Live 产品化（Wave 2）

> **Wave:** 2 · **Module ID:** **C3**（主）· **A3** · **B\*** · **G6**  
> **评级移动:** `R3_STAGED_FIXTURE_CLOSED` → `R4_SANDBOX_REAL_DATA_OR_REHEARSAL`  
> **INDEX:** `WAVE2_R3H08_TO_ISSUES_INDEX.md`  
> **PASS 登记:** `LIVE-PROD-24`  
> **Trellis:** complex · **blocked by** R3H-10 + R3H-07 CLOSED  
> **Execute SSOT:** `.trellis/tasks/06-29-round3h-r3h08-live-productization/research/00-EXECUTION-ENTRY.md`

---

## 1. 业务目标

交付 **env-gated 产品 live**：Sync、`qmd data` CLI、探针 **一律经 `DataSourceService`**；24 业务源按 PASS §2.1 写入 Tier **A/B/C**；消除 rehearsal（`REHEARSAL_ONLY`）冒充产品路径。

子轨（单 agent 串行）：**08C → 08A → 08B → 08D**。

## 2. 不在范围

- `web_search` 真 API（post-Round4）
- 新 clean migration DDL（R3H-06 已封板）
- Round4 API
- 删除 `ops/*_pilot_*` 模块

## 3. 验收

见 `WAVE2_R3H08_TO_ISSUES_INDEX.md` Acceptance criteria；切片见 Execute 包 `to-issues-slices.md`。

## 4. 阻塞

- **R3H-10** CLOSED ✅
- **R3H-07** CLOSED @ `94ccd326` ✅
- **R3H-06** CLOSED ✅

## 5. 下游

Wave 3 `R3-DCP-01..03`（baostock+fred 增量产品路径）

## 6. 参考采纳（活卡级摘要）

| 参考              | 等级              | 说明                               |
| ----------------- | ----------------- | ---------------------------------- |
| OpenBB            | architecture_only | Fetcher 三阶段 · credentials 门    |
| digital-oracle    | L2/L3             | HTTP/概率解析对照                  |
| EasyXT            | **forbidden**     | silent_fallback · scheduler bypass |
| QMD R3H-10/R3G-03 | L1 仓内           | service 金路径 · Tier B DB 隔离    |

详表：`research/reference-adoption-r3h08.md` · 架构：`research/live-tier-architecture.md`

## 7. Execute 子 agent 强制双铁律

**派发 SSOT：** Execute 包 `research/execute-parity-contract.md`

| 铁律               | 要求                                                                                                                                                                |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A · 同流程**     | 与主会话亲自 Execute（`trellis-execute` 全文）**完全一致**；仅禁止 commit/finish-work                                                                               |
| **B · 参考三等级** | 每切片 RED 前 Read `reference-adoption-r3h08.md` §7 + `EXTERNAL-INDEX.md` §D 的 `参考项目/**` 源码；严格 L1/L2/L3；**禁止不参考从零造**；禁止 runtime import 参考树 |

证据：矩阵/测试 cite `参考路径 + 行号 + 等级`。
