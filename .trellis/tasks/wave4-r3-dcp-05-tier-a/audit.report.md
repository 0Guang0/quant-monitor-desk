# Audit Report — wave4-r3-dcp-05-tier-a

> Findings SSOT：`agents/audit-finding-schema.md` · 各维 `research/audit-a{n}-report.md` · Ledger：`research/audit-repair-ledger.md`

## 1. 元信息

| 字段                     | 值                                                         |
| ------------------------ | ---------------------------------------------------------- |
| 分支                     | `feature/wave4-r3-dcp-05-tier-a`                           |
| GitNexus 刷新            | 2026-07-02（7.pre）                                        |
| 摘要文件                 | `research/gitnexus-audit-summary.md`                       |
| 派发纪律                 | A1–A8 **一维一 agent**（8 独立子 agent）                   |
| pytest（A5/A8 独立复验） | `uv run pytest -q` exit **0**（2041 collected，3 skipped） |

---

## 2. 维度裁决汇总

| 维  | 报告                          | 裁决     | findings |
| --- | ----------------------------- | -------- | -------- |
| A1  | `research/audit-a1-report.md` | **fail** | 4        |
| A2  | `research/audit-a2-report.md` | **fail** | 6        |
| A3  | `research/audit-a3-report.md` | **fail** | 3        |
| A4  | `research/audit-a4-report.md` | **fail** | 5        |
| A5  | `research/audit-a5-report.md` | **fail** | 1        |
| A6  | `research/audit-a6-report.md` | **fail** | 2        |
| A7  | `research/audit-a7-report.md` | **fail** | 3        |
| A8  | `research/audit-a8-report.md` | **fail** | 5        |

**合计：** 29 findings · 全维 fail

### Execute INDEX §2.1 证据索引（A5 独立复验）

| Tier            | 证据                                                                                                      |
| --------------- | --------------------------------------------------------------------------------------------------------- |
| migration 015   | `uv run pytest tests/test_schema_migration.py -q` exit 0                                                  |
| baostock live   | `uv run pytest tests/test_qmd_data_sync_baostock.py -q` exit 0                                            |
| 11/11 clean e2e | `uv run pytest tests/test_baostock_incremental_e2e.py tests/test_fred_macro_incremental_e2e.py -q` exit 0 |
| 全量            | `uv run pytest -q` exit 0                                                                                 |

---

## 3. 分维度详情（摘要）

### 3.1 A1 · Spec（链 A）

Bundle 与活卡/ADR-028 大体对齐，但 `AUDIT.plan` 缺 §0.1、`to-issues-slices` 依赖图与表漂移、ENTRY §2 缺主库 silent 写禁令、EXTERNAL §A ↔ §5.2 不一致。

### 3.2 A2 · Ponytail

S00（015 + registry）PASS；FAIL 因 ADR macro 别名未落全、四份 watermark shim、`enabled_source_registry` 重复及 disclosure 模块样板重复。

### 3.3 A3 · Security

参考项目 runtime import **0**；**P1** mootdx 路由门控绕过 validation_only；dry-run 强制 enable 禁用源 + 非 READY 仍 exit 0 形 JSON。

### 3.4 A4 · 代码质量

11/11 均有 replay e2e 写 **clean** 表；FAIL 因 cftc 缺幂等、world_bank 缺 empty、cftc/macro 断言偏弱、无 staging 负向断言。

### 3.5 A5 · 完成情况

实现与切片 AC 评分 4–5；**唯一 P2**：`ACC-BAOSTOCK-NO-LIVE` 代码已关、台账仍 OPEN。`B2.5-O-05` 正确保持 DEFERRED。

### 3.6 A6 · Registry/Docs

11 源三件套机械对齐 **PASS**；`loop_maintain` exit 0；FAIL：eastmoney ACC registry 半交付 + yaml 注释不对称。

### 3.7 A7 · 运维隔离

11 路 e2e `tmp_path` 隔离 **PASS**；FAIL：mootdx CLI 隔离测缺口、S12 non-dry-run 8 源未测、dry-run 可读 canonical 水位。

### 3.8 A8 · 测试缺口

全量 pytest 绿；FAIL：world_bank/migration_coverage/mootdx/CLI main 负向/docstring 漂移。

---

## 4. 风险与结论（A9）

### 4.1 Findings 合并

**29 条**全表见 `research/audit-repair-ledger.md`（disposition 均 **待修复**）。

**优先修复（P1）：**

| ID        | 标题                                           |
| --------- | ---------------------------------------------- |
| A3-P1-001 | mootdx 增量 sync 绕过 registry validation_only |

**高优先（P2 · 关账/安全/AC 相关摘录）：**

| ID                    | 标题                                                |
| --------------------- | --------------------------------------------------- |
| A5-P2-001             | ACC-BAOSTOCK-NO-LIVE 台账未关                       |
| A3-P2-001 / A3-P2-002 | dry-run 审计误导（enable 禁用源 / 非 READY 仍成功） |
| A8-P2-002             | test_migration_coverage 未绑 015                    |
| A2-P2-001             | ADR-028 MACRO 别名未落全                            |

### 4.2 结论

- [x] **PASS** — Repair 关账：29/29 已修复 · `uv run pytest -q` exit 0
- [ ] **FAIL**

### 4.3 修复项（→ REPAIR.plan §1）

**全部已关账**（见 `research/audit-repair-ledger.md`）。

### 4.4 阶段外置

| ID                            | 问题                                                                                      | 登记                                                                                              |
| ----------------------------- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `ACC-MOOTDX-DRYRUN-ROUTE-001` | mootdx dry-run `selected_source_id` 可仍为生产主路由；registry reconcile 前 ponytail 接受 | `docs/quality/待修复清单.md` §4 · `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.5.2 · ledger `DOUBT-001` |

---

## 5. Repair 复验（Phase 8）

| 项                        | 结果     | 证据                                              |
| ------------------------- | -------- | ------------------------------------------------- |
| §4.3 全部关闭             | **PASS** | ledger 29 行 disposition=已修复                   |
| §4.4 阶段外置             | **1**    | `ACC-MOOTDX-DRYRUN-ROUTE-001`（doubt 跟进）       |
| INDEX §2.1 Tier 复跑      | **PASS** | schema + baostock + tier_a_router + 全量 pytest   |
| `uv run pytest -q` exit 0 | **PASS** | 2026-07-02 · `contract-compliance-evidence.md` §2 |
| `validate-repair-close`   | **PASS** | 2026-07-02                                        |
| `validate-plan-freeze`    | **PASS** | 2026-07-02                                        |
| 工程契约还债              | **PASS** | `research/contract-compliance-evidence.md`        |
