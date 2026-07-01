# Repair 计划 — R3-DCP-05 Tier A（Docs/Registry 切片）

> **读者：** Repair 执行者  
> **输入：** `audit.report.md` · `research/audit-repair-ledger.md`  
> **本切片范围：** DOCS/REGISTRY ONLY（A1/A5/A6 文档项）  
> **原则：** 修根因，不兜底

---

## 0. 元信息

| 字段       | 值                       |
| ---------- | ------------------------ |
| slug       | `wave4-r3-dcp-05-tier-a` |
| 切片       | Repair-Docs-Registry     |
| Audit 报告 | `audit.report.md`        |

---

## 1. 修复项清单（Docs/Registry）

| ID        | 维度 | 问题                                    | 根因修复方案                                                                   | 验证命令                                                                       | 通过条件                           | 证据 | 已修复 |
| --------- | ---- | --------------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------ | ---------------------------------- | ---- | ------ |
| A5-P2-001 | A5   | ACC-BAOSTOCK-NO-LIVE 台账未关           | §4/§8 迁入 §1 · `RESOLVED_ISSUES_REGISTRY.md` §Wave 4 DCP-05                   | `grep ACC-BAOSTOCK-NO-LIVE docs/quality/待修复清单.md` §1 命中 · §4 无 open 行 | 台账双 ID 关账 · REQ2-EM 未误关    | s13  | [x]    |
| A6-P2-001 | A6   | ACC-EASTMONEY registry 半交付           | eastmoney notes 增 ACC-EASTMONEY-TAXONOMY-001 cross-ref（validation-only）     | `grep ACC-EASTMONEY-TAXONOMY-001 specs/datasource_registry/*.yaml`             | 双 registry 命中 · REQ2-EM 仍 open | —    | [x]    |
| A6-P3-001 | A6   | registry/capabilities DCP-05 注释不对称 | source_registry 11 源 notes 对齐 clean 表名格式                                | `grep "-> .* clean" specs/datasource_registry/source_registry.yaml`            | 11 源 DCP-05 注释含 clean 表名     | —    | [x]    |
| A1-P2-001 | A1   | AUDIT.plan 缺 §0.1 Trace Authority      | 新增 §0.1 表（活卡 · ADR-028 · ENTRY · frozen · integration-audit · EXTERNAL） | `grep "§0.1 Trace Authority" AUDIT.plan.md`                                    | §0.1 六行追溯表                    | —    | [x]    |
| A1-P2-002 | A1   | 切片依赖图与表 S07–S13 漂移             | 依赖图重写：S02–S06 macro → S07–S11 源片 → **S12 CLI** → S13                   | 人工对读 `to-issues-slices.md` 依赖图 vs 切片总表                              | S12-CLI-ROUTER 在依赖图出现        | —    | [x]    |
| A1-P2-003 | A1   | 主库 silent 写禁令未下沉 ENTRY §2       | ENTRY §2 增「主库 · 禁止 silent 写 canonical data/duckdb/」行                  | `grep silent research/00-EXECUTION-ENTRY.md`                                   | §2 约束表命中                      | —    | [x]    |
| A1-P2-004 | A1   | EXTERNAL §A 与 ENTRY §5.2 不一致        | §5.2 声明 EXTERNAL-INDEX §A 为 SSOT 超集 + 第 6 项补读                         | Read §5.2 + EXTERNAL-INDEX §A                                                  | §A 每 path 可解析                  | —    | [x]    |

---

## 2. Repair 完成 DoD（本切片）

- [x] §1 全部 Docs/Registry 项已修复 + 证据列
- [ ] 代码 Repair 项（A2–A4/A7/A8）由后续切片承接
- [x] `uv run python scripts/loop_maintain.py`（specs/docs touched）
- [ ] `audit.report.md` §5 复验（全 Repair 完成后）
