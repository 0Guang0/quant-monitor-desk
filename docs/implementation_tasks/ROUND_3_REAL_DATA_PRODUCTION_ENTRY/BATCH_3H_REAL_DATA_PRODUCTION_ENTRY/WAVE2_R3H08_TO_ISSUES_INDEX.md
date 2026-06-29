# Wave 2 — R3H-08 `/to-issues` 任务卡骨架

> **格式：** `/to-issues` · tracer-bullet 垂直切片  
> **波次：** `R3H_PASS_EXECUTION_PLAN.md` §3 Wave 2  
> **串行（单 agent）：** **08C → 08A → 08B → 08D**  
> **状态：** OPEN @ 2026-06-29 · 前置 Wave 1 **CLOSED**

---

## 0. Wave 级门控

| 项            | 内容                                                      |
| ------------- | --------------------------------------------------------- |
| **Wave 目标** | 24 源 env-gated 产品 live · Tier A/B/C · `LIVE-PROD-24`   |
| **前置**      | R3H-10 + R3H-07 CLOSED                                    |
| **Trellis**   | `.trellis/tasks/06-29-round3h-r3h08-live-productization/` |
| **活卡**      | `R3H_08_LIVE_PRODUCTIZATION.md`                           |
| **下游**      | Wave 3 R3-DCP-01..03                                      |

---

## 1. R3H-08 · 合并 Execute 包（08A–D）

**规划 ID：** R3H-08（子轨 08C/08A/08B/08D）  
**Module：** C3 · A3 · B\* · G6

### What to build

产品 live fetch：**仅** `DataSourceService` 金路径；`ProductLiveGate` + `LiveTierRouter`；各 `fetch_ports` env opt-in；Tier B 拒绝 canonical main；承接 R3H-10 defer（reconcile service · probe service）。

### Acceptance criteria

- [ ] `LIVE-PROD-24` 可登记 CLOSED（registry 无矛盾）
- [ ] 24 源（除 web_search 延后）各有 env-gated live 契约测或 tracer bullet
- [ ] rehearsal 路径 `REHEARSAL_ONLY` 与产品路径测试分离
- [ ] `uv run pytest -q` 全绿
- [ ] 无新 migration DDL

### Blocked by

R3H-10 · R3H-07 CLOSED ✅

### Vertical slices

Execute：`research/to-issues-slices.md` · 架构：`research/live-tier-architecture.md`

**Execute 强制：** 每切片 RED 前必 Read `参考项目/**` 源码（`reference-adoption-r3h08.md` §7 · `EXTERNAL-INDEX.md` §D）；禁止不参考从零造。

---

## 2. 子轨对照

| 子轨 | 源                                                                              | Tier |
| ---- | ------------------------------------------------------------------------------- | ---- |
| 08C  | fred, us_treasury, sec_edgar, cftc_cot, bis, world_bank, alpha_vantage, deribit | A    |
| 08A  | baostock, cninfo, mootdx                                                        | A    |
| 08B  | yahoo, akshare, stooq, coingecko, eastmoney, sina, tdx, ths, qmt\_\*            | B    |
| 08D  | kalshi, polymarket                                                              | C    |

---

## 3. Wave 2 Checklist

```text
[ ] reference-adoption-r3h08.md + live-tier-architecture.md
[ ] Plan freeze validate-plan-freeze exit 0
[ ] Execute S08-BOOT..05 RED→GREEN
[ ] Audit PASS → merge
[ ] 更新 R3H_PASS_EXECUTION_PLAN §3.1 Wave 2 = CLOSED
```
