# R3H-08 `/to-issues` 垂直切片

> **架构 SSOT：** `live-tier-architecture.md`  
> **参考采纳：** `reference-adoption-r3h08.md`  
> **串行：** 08C → 08A → 08B → 08D（横切 S08-05 在 08D 后）

---

## 0. 切片原则（含 Execute 强制约束）

| 原则          | 本任务                                                                                     |
| ------------- | ------------------------------------------------------------------------------------------ |
| **双铁律**    | **A** `execute-parity-contract.md` = 主会话同流程 · **B** §7+§D 参考源码三等级，禁止从零造 |
| Tracer bullet | 每切片端到端可验证                                                                         |
| SSOT          | 产品 live 仅 `DataSourceService` 金路径                                                    |
| 只读参考树    | 禁止 runtime import `参考项目/**`                                                          |

---

## 1. 切片总表

| 序  | ID            | 标题                            | 子轨 | Step  | 阻塞   |
| --- | ------------- | ------------------------------- | ---- | ----- | ------ |
| 0   | **S08-BOOT**  | Live-tier 基线矩阵              | —    | `9.0` | —      |
| 1   | **S08-01**    | 08C 宏观/市场 primary live      | 08C  | `9.1` | BOOT   |
| 2   | **S08-02**    | 08A CN primary live             | 08A  | `9.2` | S08-01 |
| 3   | **S08-03**    | 08B validation Tier B           | 08B  | `9.3` | S08-02 |
| 4   | **S08-04**    | 08D Tier C 概率源               | 08D  | `9.4` | S08-03 |
| 5   | **S08-05**    | 横切：reconcile + probe service | —    | `9.5` | S08-04 |
| 6   | **S08-CLOSE** | LIVE-PROD-24 关账               | —    | Audit | S08-05 |

```text
S08-BOOT → S08-01(08C) → S08-02(08A) → S08-03(08B) → S08-04(08D) → S08-05 → S08-CLOSE
```

---

## 2. S08-BOOT — Live-tier 基线矩阵

### What to build

盘点 24 源：当前 mock/rehearsal/live 状态、目标 Tier、对应 port、缺口测试。

### 交付物

- `research/live-tier-baseline-matrix.md`
- RED 测：产品 live 入口不存在或 env 默认 fail-closed

### 验收

- [x] 矩阵 24 行 + web_search 延后注记
- [x] 每行：source · tier · port · 当前状态 · 目标切片 · **reference_anchor · adoption_level**
- [x] RED 证明 `QMD_ALLOW_LIVE_FETCH` 未设时 live 被拒绝
- [x] **RED 前已 Read `reference-adoption-r3h08.md` §7 + `EXTERNAL-INDEX.md` §D（BOOT 行）**

---

## 3. S08-01 — 08C 宏观/市场 primary

### What to build

`ProductLiveGate` + 启用 fred/us_treasury/sec_edgar/cftc_cot/bis/world_bank/alpha_vantage/deribit port live 分支；macro Tier A 经 service fetch。

### 验收

- [x] 每源至少 1 个五字段 live 契约测（mock HTTP 或 env skip）
- [x] `staged_fixture_mode=False` 金路径
- [x] 无 EasyXT 式 silent fallback
- [x] **§7.2 08C 参考源码已 Read；port 改动含 cite**

### Blocked by

S08-BOOT · **§7.2 源码 Read 完成**

---

## 4. S08-02 — 08A CN primary

### What to build

baostock/cninfo/mootdx 产品 live；CN bar/disclosure 域；禁止 `cn_rehearsal_live_ports` 冒充产品。

### 验收

- [x] 三源 port live opt-in 绿
- [x] rehearsal 负向：rehearsal 模块仍 `REHEARSAL_ONLY`

---

## 5. S08-03 — 08B validation Tier B

### What to build

validation_only 源 live → **仅** pilot/audit-sandbox DB；负向拒绝 canonical main。

### 验收

- [x] `limited_production_entry` 守卫测扩展
- [x] yahoo 等 permanent validation_only 不被提升 primary

---

## 6. S08-04 — 08D Tier C

### What to build

kalshi/polymarket env-gated live；概率 evidence 域；digital-oracle 概率字段 L2 对齐。

### 验收

- [x] Tier C 不写 clean bar 表
- [x] ResourceGuard 预算内

---

## 7. S08-05 — 横切关账

### What to build

- `run_reconcile` + `datasource_service=` 金路径（ADR-025 defer 闭合）
- `interface_probe` 全经 service（R3H-10 defer）
- `qmd data` live 子命令或等价 flag（dry_run 默认）

### 验收

- [x] reconcile/probe 负向 bypass RED→GREEN
- [x] ADR-027 与契约测一致

---

## 8. Out of scope

web_search 真 API · 新 migration · 删 pilot 模块 · Wave 3 增量 watermark
