# R3H PASS 路径执行计划 — Round4 前收口

> **Authority：** 用户裁决 @ 2026-06-28；路线图 SSOT：`PROJECT_IMPLEMENTATION_ROADMAP.md` §5.0.2–§5.0.5。  
> **前提：** R3H-01～04 **CLOSED** @ 2026-06-28；adapter/replay/registry 已交付。  
> **Round4 门禁目标：** `PASS_ROUND4_REAL_DATA_READY`（**唯一**允许的范围 ADR：`web_search` 真 API 延后至独立模块）。  
> **不是工单替代：** 各波次仍须 Trellis Plan/Execute/Audit；本文件是协调索引。

---

## 1. 用户裁决（Grill-me 锁定）

| 议题                    | 裁决                                                                                                                                                    |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Round4 入口**         | 坚持 **PASS**，尽量少 WARN ADR                                                                                                                          |
| **`web_search` 真 API** | **延后**；独立功能模块（Round4 后单独做）；Round4 前保持 mock/replay `READY_WITH_EVIDENCE` + **一条** scope ADR                                         |
| **官方宏观五源 live**   | `us_treasury`, `sec_edgar`, `cftc_cot`, `bis`, `world_bank`（及 `fred`）须 **env-gated 真网 live** smoke + 产品化 live→目标库                           |
| **kalshi / polymarket** | **须 env-gated 真网 live**（probability/evidence 路径）；**禁止** factual clean write                                                                   |
| **LIVE-PROD 范围**      | 凡 registry 终态为 `READY_WITH_EVIDENCE` 的源（24 业务源）均须 **live→目标库**；落库目标按 §2 三层，**不得**违反 `validation_only` / 授权 disabled 设计 |
| **主库**                | `quant_monitor.duckdb` 仍受 denylist + promote 批准门禁；PASS 证明 **路径存在** + 测试绿，不默认可无批准写主库                                          |

---

## 2. 三层落库目标（LIVE-PROD SSOT）

| 层级              | 库 / 形态                                                                             | 适用源                                         | Round4 消费                                                |
| ----------------- | ------------------------------------------------------------------------------------- | ---------------------------------------------- | ---------------------------------------------------------- |
| **A 主计算库**    | `data/duckdb/quant_monitor.duckdb`（经 WriteManager + 批准 promote）                  | Primary 角色、非 `validation_only` 的 READY 源 | Layer 计算、前端展示、回测 frozen loader                   |
| **B 验证库**      | `data/duckdb/quant_monitor_r3g03_pilot.duckdb` 或等价 validation schema               | `validation_only: true` 的 READY 源            | 校验、冲突诊断、对照；**不得**冒充 primary 进 Layer 主路径 |
| **C 证据/信号轨** | probability bundle / manual_review staging / evidence JSON（**无** factual clean 表） | `kalshi`, `polymarket`, `web_search`（mock）   | Agent/人工复核/概率展示；Round4 API 只读暴露               |

### 2.1 逐源落库与 live 要求（24 业务源）

| source_id       | registry 角色         | live→目标                | env-gated live PASS 要求        |
| --------------- | --------------------- | ------------------------ | ------------------------------- |
| `fred`          | primary macro         | **A**                    | ✅（已有 SSOT；复核无 sidecar） |
| `us_treasury`   | primary               | **A**                    | ✅ 真网                         |
| `sec_edgar`     | primary               | **A**                    | ✅ 真网                         |
| `cftc_cot`      | primary               | **A**                    | ✅ 真网                         |
| `bis`           | primary               | **A**                    | ✅ 真网                         |
| `world_bank`    | primary               | **A**                    | ✅ 真网                         |
| `alpha_vantage` | primary（声明域）     | **A**                    | ✅ 真网                         |
| `deribit`       | primary crypto        | **A**                    | ✅ 真网                         |
| `baostock`      | CN primary            | **A**                    | ✅ 产品化（非仅 pilot 脚本）    |
| `cninfo`        | CN primary disclosure | **A**（disclosure 分表） | ✅ 真网                         |
| `mootdx`        | CN primary 扩展       | **A**                    | ✅ 真网                         |
| `yahoo_finance` | validation_only 永久  | **B**                    | ✅ 真网→验证库                  |
| `akshare`       | validation_only 永久  | **B**                    | ✅ 真网→验证库                  |
| `stooq`         | validation_only       | **B**                    | ✅ 真网→验证库                  |
| `coingecko`     | validation_only       | **B**                    | ✅ 真网→验证库                  |
| `eastmoney`     | validation            | **B**                    | ✅ 真网→验证库                  |
| `sina_finance`  | validation            | **B**                    | ✅ 真网→验证库                  |
| `tdx_pytdx`     | validation probe      | **B**                    | ✅ env 授权时真网→验证库        |
| `ths_ifind`     | auth-disabled 默认    | **B** 或证据             | ✅ 授权正例 live smoke          |
| `qmt_xtdata`    | license-disabled 默认 | **B** 或证据             | ✅ 授权正例 live smoke          |
| `qmt_xqshare`   | auth-disabled 默认    | **B** 或证据             | ✅ 授权正例 live smoke          |
| `kalshi`        | probability           | **C**                    | ✅ env-gated live               |
| `polymarket`    | probability           | **C**                    | ✅ env-gated live               |
| `web_search`    | manual_review         | **C**（mock）            | ⏸ 真 API **延后**（§1）         |

| `openbb_provider_reference` | metadata | — | `ADR_DISABLED_OUT_OF_SCOPE` |

---

## 3. 波次总览（Round4 前）

```text
Wave 0  Batch 3V（6 卡，trust 底座）                    【✅ CLOSED @ 2026-06-28 · integration/round3-batch3v @ 45759eea】
        → `/to-issues` 骨架：`BATCH_3V_VERIFIED_AUDIT_CLEANUP/WAVE0_BATCH3V_TO_ISSUES_INDEX.md`
  ↓
Wave 1  R3H-06 Clean Schema（G3/G4/G5/G6）             【串行；阻塞 Wave 3 写 clean】
  ↓
Wave 2  R3H-07 US Calendar ∥ R3H-10 Staged SSOT 收敛   【可并行】
  ↓
Wave 3  R3H-08 Live 产品化（4 子轨 A/B/C/D）           【子轨可并行；均依赖 Wave 1】
  ↓
Wave 4  R3H-05 审计（A/B/C/D/E + GATE）                【GATE 串行最后；产出 PASS】
  ↓
Round4  Batch04（B04-01 先，余者并行）
```

**不在 Round4 前：** `web_search` 真 API 模块（**R3H-WEB-SEARCH**，Round4 后独立 Trellis）。

---

## 4. 各波次任务卡（规划 ID）

| 波次 | ID                 | 拥有                                           | 并行                 | 闭合 §5.0.1 ID                           | 活卡 / Trellis                               |
| ---- | ------------------ | ---------------------------------------------- | -------------------- | ---------------------------------------- | -------------------------------------------- |
| 0    | Batch3V B3V-01..06 | VR-\* trust                                    | ✅ Done @ 2026-06-28 | G6 部分、schema_hash                     | CLOSED                                       |
| 1    | **R3H-06**         | 域分表、OHLCV、cninfo disclosure 形、PK/upsert | 单轨                 | SCHEMA-G3G4, CNINFO-DISCLOSURE-SHAPE, G6 | `R3H_06_CLEAN_SCHEMA.md` · Plan @ 2026-06-29 |
| 2a   | **R3H-07**         | US TradingCalendar L2                          | 与 2b 并行           | CAL-US                                   | 待建                                         |
| 2b   | **R3H-10**         | fetch_ports SSOT；staged 仅 rehearsal          | 与 2a 并行           | STAGED-PILOT-SSOT                        | 待建                                         |
| 3a   | **R3H-08A**        | CN primary live→A；G14 sidecar 去除            | 与 3b/c/d 并行       | G14, G11, LIVE-PROD(CN primary)          | 待建                                         |
| 3b   | **R3H-08B**        | validation 源 live→B；G16 wire                 | 并行                 | G16, LIVE-PROD(validation)               | 待建                                         |
| 3c   | **R3H-08C**        | 宏观五源 + fred env-gated live→A               | 并行                 | MACRO-LIVE-DEFER, LIVE-PROD(macro)       | 待建                                         |
| 3d   | **R3H-08D**        | kalshi/polymarket env-gated live→C             | 并行                 | KALSHI-POLY-LIVE                         | 待建                                         |
| 4    | **R3H-05A..E**     | 分轨审计 slice                                 | A–E 并行             | REF-ADOPT, G13, REGISTRY-ORPHAN, …       | `R3H_05_*.md`                                |
| 4    | **R3H-05-GATE**    | 合并 audit + **PASS** 裁决                     | **串行最后**         | 全部 §7                                  | Wave 4 最后                                  |

---

## 5. Round4 PASS 通过条件（检查清单）

1. Batch 3V **CLOSED**（六卡 archive + registry 主会话 reconcile）。
2. R3H-06～10 + R3H-08 子轨 **CLOSED**（每轨 audit 零遗留 + pytest 全绿）。
3. `round3h_real_data_production_entry_audit.md`：25 行终态 + §7 **全部 CLOSED**（`web_search` 真 API 行 = **DEFERRED_POST_ROUND4** + 单 ADR，不算 WARN 收窄 Round4）。
4. §1 决策 = **`PASS_ROUND4_REAL_DATA_READY`**。
5. 每 READY 源：env-gated live 证据 + 正确 Tier A/B/C 落库测试引用。
6. `MAIN-DB-GATE` 复核绿；无 pilot 数据 silent merge 主库。
7. Layer1–5 smoke 绿（**不含** G12 全量指标）。
8. 下游：路线图 §10、Batch3H manifest **CLOSED**、Round4 manifest 可开工。

---

## 6. 协调与合并

- **Registry 三件套：** 主会话排队 merge（同 R3H-01～04 playbook）。
- **共享 migration：** 仅 R3H-06 拥有 DDL；他轨禁止改 schema。
- **索引文件：** 主会话维护 `R3H-PASS-MERGE-MANIFEST.md`（与 `_tmp-r3h03-r3h04-parallel/` 同模式）。

---

## 7. 关联文件

```text
PROJECT_IMPLEMENTATION_ROADMAP.md §5.0.2–§5.0.5
BATCH_3H_COORDINATOR_PLAYBOOK.md §5（PASS 波次）
R3G_MASS_REHEARSAL_OPEN_GAPS.md §2
R3H_05_LAYER_BINDING_AND_PRODUCTION_ENTRY_AUDIT.md
docs/implementation_tasks/ROUND_3_VERIFIED_AUDIT_CLEANUP/BATCH_3V_VERIFIED_AUDIT_CLEANUP/README.md
```
