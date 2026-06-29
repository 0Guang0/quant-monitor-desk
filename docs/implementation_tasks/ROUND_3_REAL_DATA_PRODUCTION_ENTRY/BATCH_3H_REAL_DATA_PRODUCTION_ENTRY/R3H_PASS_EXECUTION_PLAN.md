# R3H PASS 路径执行计划 — Round4 前收口（模块轨）

> **Authority：** 用户裁决 @ 2026-06-28；**模块轨 SSOT：** `PROJECT_IMPLEMENTATION_ROADMAP.md` §3、§6.1。  
> **前提：** R3H-01～04、R3H-06、Batch 3V — **CLOSED**。  
> **Round4 门禁：** `PASS_ROUND4_REAL_DATA_READY`（**五轴 G12 全绿**为硬门禁 @ 2026-06-29）。  
> **当前下一入口（写死）：** **`R3H-10` → `R3H-07` 串行** — `WAVE1_R3H10_THEN_R3H07_TO_ISSUES_INDEX.md`  
> **不是工单替代：** 各轨 Trellis Plan/Execute/Audit；本文件为协调索引。

---

## 1. 用户裁决

| 议题              | 裁决                              |
| ----------------- | --------------------------------- |
| Round4 入口       | **PASS**（非 WARN 主路径）        |
| web_search 真 API | post-Round4 · `R3H-WEB-SEARCH`    |
| 24 源 live        | env-gated → Tier A/B/C（§2）      |
| 五轴 G12          | **PASS 前 pytest 全绿**（Wave 4） |
| 增量试点          | baostock + fred（Wave 3）         |
| Wave 1 执行       | **R3H-10 CLOSED 后** 才 R3H-07    |
| 主库              | denylist + promote 批准不变       |

---

## 2. 三层落库（LIVE-PROD SSOT）

| 层级  | 库 / 形态                              | 适用源                               |
| ----- | -------------------------------------- | ------------------------------------ |
| **A** | `quant_monitor.duckdb`（批准 promote） | Primary、非 validation_only          |
| **B** | `quant_monitor_r3g03_pilot.duckdb` 等  | `validation_only: true`              |
| **C** | probability / manual_review / evidence | kalshi, polymarket, web_search(mock) |

### 2.1 逐源落库与 live 要求（24 业务源）

| source_id       | registry 角色         | live→目标     | env-gated live PASS 要求 |
| --------------- | --------------------- | ------------- | ------------------------ |
| `fred`          | primary macro         | **A**         | ✅ 复核无 sidecar        |
| `us_treasury`   | primary               | **A**         | ✅ 真网                  |
| `sec_edgar`     | primary               | **A**         | ✅ 真网                  |
| `cftc_cot`      | primary               | **A**         | ✅ 真网                  |
| `bis`           | primary               | **A**         | ✅ 真网                  |
| `world_bank`    | primary               | **A**         | ✅ 真网                  |
| `alpha_vantage` | primary               | **A**         | ✅ 真网                  |
| `deribit`       | primary crypto        | **A**         | ✅ 真网                  |
| `baostock`      | CN primary            | **A**         | ✅ 产品化（非仅 pilot）  |
| `cninfo`        | CN primary disclosure | **A**         | ✅ 真网                  |
| `mootdx`        | CN primary 扩展       | **A**         | ✅ 真网                  |
| `yahoo_finance` | validation_only 永久  | **B**         | ✅ 真网→验证库           |
| `akshare`       | validation_only 永久  | **B**         | ✅ 真网→验证库           |
| `stooq`         | validation_only       | **B**         | ✅ 真网→验证库           |
| `coingecko`     | validation_only       | **B**         | ✅ 真网→验证库           |
| `eastmoney`     | validation            | **B**         | ✅ 真网→验证库           |
| `sina_finance`  | validation            | **B**         | ✅ 真网→验证库           |
| `tdx_pytdx`     | validation probe      | **B**         | ✅ env 授权时真网        |
| `ths_ifind`     | auth-disabled 默认    | **B** 或证据  | ✅ 授权正例 smoke        |
| `qmt_xtdata`    | license-disabled 默认 | **B** 或证据  | ✅ 授权正例 smoke        |
| `qmt_xqshare`   | auth-disabled 默认    | **B** 或证据  | ✅ 授权正例 smoke        |
| `kalshi`        | probability           | **C**         | ✅ env-gated live        |
| `polymarket`    | probability           | **C**         | ✅ env-gated live        |
| `web_search`    | manual_review         | **C**（mock） | ⏸ 真 API **延后**（§1）  |

| `openbb_provider_reference` | metadata | — | `ADR_DISABLED_OUT_OF_SCOPE` |

---

## 3. 波次总览（模块轨 · 2026-06-29）

```text
[✅] 历史  Batch 3V · R3H-01～04 · R3H-06
  ↓
Wave 1  R3H-10 → R3H-07（串行）                    【1a CLOSED · 1b 当前】
  ↓
Wave 2  R3H-08A / 08B / 08C / 08D（24 源 live）    【CLOSED @ 2026-06-29】
  ↓
Wave 3  R3-DCP-01..03（baostock+fred 增量）        【IN_PROGRESS @ 2026-06-30】
  ↓
Wave 4  R3-DCP-05..10（五轴全绿 + 后端加厚）       【OPEN】
  ↓
Wave 5  R3H-05A..E → R3H-05-GATE                   【OPEN】
  ↓
Round4  B04-01 先
```

### 3.1 波次状态表

| Wave | 内容                         | 状态 @ 2026-06-29                             |
| ---- | ---------------------------- | --------------------------------------------- |
| 历史 | 3V, R3H-01～04, R3H-06       | ✅ CLOSED                                     |
| 1    | R3H-10 → R3H-07              | ✅ CLOSED @ 2026-06-29                        |
| 2    | R3H-08A–D                    | ✅ CLOSED @ 2026-06-29                        |
| 3    | R3-DCP-01..03                | 🔄 IN_PROGRESS（双轨 DCP-01∥02 @ 2026-06-30） |
| 4    | R3-DCP-05..10 + **G12 五轴** | 🔴 OPEN                                       |
| 5    | R3H-05 + GATE                | 🔴 OPEN                                       |

---

## 4. 各波次任务（规划 ID · Module ID）

| Wave | ID                | 主 Module      | 评级移动  | Trellis           | `/to-issues`           |
| ---- | ----------------- | -------------- | --------- | ----------------- | ---------------------- |
| 1a   | **R3H-10**        | C2, E4         | R3→R4     | complex           | `WAVE1_...INDEX.md` §1 |
| 1b   | **R3H-07**        | G4, C3         | R3→R4     | complex           | `WAVE1_...INDEX.md` §2 |
| 2a   | R3H-08A           | C3, A3, B1     | R3→R4     | complex           | 待建                   |
| 2b   | R3H-08B           | C3, B2, B3     | R3→R4     | complex           | 待建                   |
| 2c   | R3H-08C           | C3, A3         | R3→R4     | complex           | 待建                   |
| 2d   | R3H-08D           | C3, G6         | R3→R4     | complex           | 待建                   |
| 3    | R3-DCP-01..03     | D1, E1, E2     | R3→R4     | debt-lite         | 待建                   |
| 4a   | R3-DCP-05         | D1, E1         | R3→R4     | debt-lite         | Tier A 增量扩展        |
| 4b   | **R3-DCP-06**     | **G1, K2**     | **R3→R4** | complex           | **五轴全绿**           |
| 4c–f | R3-DCP-07..10     | G2, G4, G5, D1 | R3→R4     | debt-lite/complex | 见路线图 §3.5          |
| 5    | R3H-05A..E + GATE | 全表           | PASS      | complex           | `R3H_05_*.md`          |

### 4.1 Wave 2 单 agent 建议串行

```text
08C（宏观/fred）→ 08A（CN/baostock）→ 08B（validation）→ 08D（Tier C）
```

---

## 5. Round4 PASS 检查清单

1. Batch 3V + R3H-01～04 + R3H-06 — **CLOSED** ✅
2. Wave 1–2：R3H-07、R3H-10、R3H-08A–D — **CLOSED**
3. Wave 3：R3-DCP-01..03 — baostock+fred 增量产品路径
4. Wave 4：R3-DCP-05..10 — **CLOSED**
5. **G12 五轴：** `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5.1 清单 **全部 [x]**
6. R3H-05-GATE → **`PASS_ROUND4_REAL_DATA_READY`**
7. 25 行 registry 审计 + §7 全 CLOSED（web_search 真 API = DEFERRED）
8. 每 READY 源：env-gated live + 正确 Tier 测试引用
9. `MAIN-DB-GATE` 绿；无 pilot silent merge 主库

**不要求 PASS：** Batch6 全集、24 源 cron 矩阵、web_search 真 API、R6。

---

## 6. 协调与合并

- **Registry 三件套：** 主会话排队 merge。
- **DDL：** R3H-06 已封板；新 migration → Batch6 门禁。
- **Wave 1：** 禁止 10∥07 双开（除非主会话多 agent 调度）。
- **索引：** `WAVE1_R3H10_THEN_R3H07_TO_ISSUES_INDEX.md`；后续波次 INDEX 随开工增补。

---

## 7. 关联文件

```text
PROJECT_IMPLEMENTATION_ROADMAP.md
MODULE_COMPLETION_RATING.md
BATCH_3H_TASK_CARD_MANIFEST.md
BATCH_3H_COORDINATOR_PLAYBOOK.md
WAVE1_R3H10_THEN_R3H07_TO_ISSUES_INDEX.md
R3H_05_LAYER_BINDING_AND_PRODUCTION_ENTRY_AUDIT.md
R3G_MASS_REHEARSAL_OPEN_GAPS.md
PROJECT_IMPLEMENTATION_ROADMAP.legacy-20260629.md  # §2.1 逐源表、§5.0.6 DataSync
```
