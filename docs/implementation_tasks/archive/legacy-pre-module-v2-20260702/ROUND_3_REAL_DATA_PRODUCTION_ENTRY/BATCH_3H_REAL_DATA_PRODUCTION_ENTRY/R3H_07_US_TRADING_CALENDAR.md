# R3H-07 — US Trading Calendar L2（CAL-US）

> **Wave:** 1b（**blocked by R3H-10 CLOSED**）  
> **Module ID:** **G4**（主）· **C3**（US 源拉数窗）  
> **评级移动:** `R3_STAGED_FIXTURE_CLOSED` → `R4_SANDBOX_REAL_DATA_OR_REHEARSAL`  
> **INDEX:** `WAVE1_R3H10_THEN_R3H07_TO_ISSUES_INDEX.md` §2  
> **PASS 登记:** `CAL-US`  
> **Trellis:** complex · **禁止** 在 R3H-10 未 CLOSED 时 Plan/Execute

---

## 1. 业务目标

闭合 **CAL-US**：`yahoo_finance`、`stooq`、`alpha_vantage` 等使用 **交易日历** 而非自然日窗；Layer4 `market_structure` 与 C3 拉数计划共用 US 日历权威。

## 2. 不在范围

- R3H-08 live 产品化（Wave 2）
- CN 日历（R3H-03 已闭合，须回归）
- 新 clean DDL（除非 ADR 另开 Batch6 轨）

## 3. 验收

见 INDEX §2 Acceptance criteria。

## 4. 阻塞

- **`R3H-10` CLOSED**（硬门禁）

## 5. 追溯

R3H-02 CLOSED 时 US 日历开放 → 本卡闭合。
