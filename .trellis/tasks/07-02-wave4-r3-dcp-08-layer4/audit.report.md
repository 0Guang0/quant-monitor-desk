# Audit Report — R3-DCP-08 Layer4 US_EQ Clean Read

> Findings SSOT：`agents/audit-finding-schema.md` · 各维 `research/audit-a{n}-report.md` · Ledger：`research/audit-repair-ledger.md`

## 1. 元信息

| 字段 | 值 |
| --- | --- |
| 分支 | `feature/wave4-r3-dcp-08-layer4` |
| GitNexus 摘要 | `research/gitnexus-audit-summary.md` |
| 派发纪律 | A1–A8 一维一 agent |
| pytest（Repair 复验） | `uv run pytest -q` exit **0** |

---

## 2. 维度裁决汇总

| 维 | 报告 | 初审计 | findings |
| --- | --- | --- | --- |
| A1 | `research/audit-a1-report.md` | fail | 6 |
| A2 | `research/audit-a2-report.md` | fail | 2 |
| A3 | `research/audit-a3-report.md` | fail | 2 |
| A4 | `research/audit-a4-report.md` | fail | 9 |
| A5 | `research/audit-a5-report.md` | fail | 2 |
| A6 | `research/audit-a6-report.md` | fail | 3 |
| A7 | `research/audit-a7-report.md` | pass | 0 |
| A8 | `research/audit-a8-report.md` | fail | 5 |

**合计：** 29 findings · Repair 后 29/29 已修复

### INDEX §2.1 证据索引（Repair 复验）

| Tier | 证据 |
| --- | --- |
| US_EQ clean e2e | `uv run pytest tests/test_layer4_us_equity_clean_e2e.py -q` exit 0 |
| Layer4 clean read | `uv run pytest tests/test_layer4_clean_read.py -q` exit 0 |
| mootdx dry-run | `uv run pytest tests/test_qmd_data_sync_tier_a_router.py -k mootdx -q` exit 0 |
| 全量 | `uv run pytest -q` exit 0 |

---

## 3. 分维度详情（摘要）

### 3.1 A1 · Spec / Trace

INDEX code-first 修订、活卡 AC 同步、§2.1 Tier 矩阵、gitnexus summary 落盘。

### 3.2 A2 · Ponytail

`_fetch_clean_bar_rows` 合并重复 SQL；`_finalize_market_build` 抽取 staged/clean 共享 finalize。

### 3.3 A3 · Security

移除 mootdx `validation_only` runtime hack 与 dry-run post-override；registry SSOT apply。

### 3.4 A4 · 代码质量

Builder 负向、lineage 强断言、flat/NULL bar 边界、registry 路由一致性。

### 3.5 A5 · 完成情况

ACC-MOOTDX 迁入 RESOLVED；ACC-LAYER L4 US_EQ 子集 §4 注记。

### 3.6 A6 · Registry/Docs

eastmoney/mootdx registry 三件套 apply；capabilities 与 ops 语义对齐。

### 3.7 A7 · 运维隔离

初审计 PASS；Repair 无变更。

### 3.8 A8 · 测试缺口

tier_a_clean 负向、future 闸、eastmoney taxonomy pytest、无 monkeypatch mootdx 路由。

---

## 4. 风险与结论（A9）

### 4.1 Findings 合并

**29 条**全表见 `research/audit-repair-ledger.md`（disposition 均 **已修复**）。

### 4.2 结论

- [x] **PASS** — Repair 关账：29/29 已修复 · `uv run pytest -q` exit 0
- [ ] **FAIL**

### 4.3 修复项

**全部已关账**（见 `research/audit-repair-ledger.md`）。

### 4.4 阶段外置

无。`R3-B2.75-REQ2-EM` 正确保持 open（未误关）。

---

## 5. Repair 复验

| 项 | 结果 | 证据 |
| --- | --- | --- |
| §4.3 全部关闭 | **PASS** | ledger 29 行 disposition=已修复 |
| §4.4 阶段外置 | **0** | — |
| INDEX §2.1 Tier 复跑 | **PASS** | e2e + clean_read + mootdx + 全量 pytest |
| `uv run pytest -q` exit 0 | **PASS** | 2026-07-02 |
| `validate-repair-close` | **PASS** | 2026-07-02 |
