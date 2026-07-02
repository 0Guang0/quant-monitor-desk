# Audit Report — m-data-03-tier-a-live

> Findings SSOT：`agents/audit-finding-schema.md` · 各维 `research/audit-a{n}-report.md` · Ledger：`research/audit-repair-ledger.md`

## 1. 元信息

| 字段                     | 值                                                                  |
| ------------------------ | ------------------------------------------------------------------- |
| 任务                     | M-DATA-03 — 11 源 Tier A live incremental→clean→inspect             |
| 分支                     | `feature/m-data-03-tier-a-live`（工作区含未提交实现）               |
| 协议                     | `plan_protocol_version: 4.1`                                        |
| GitNexus 7.pre           | `research/gitnexus-audit-summary.md`                                |
| 派发纪律                 | A1–A8 **一维一 agent** · **composer-2.5**（非 fast）                |
| pytest（A5/A8 独立复验） | `uv run pytest -q` exit **0**（A5 ~376s）；harness 14 pass + 1 skip |

---

## 2. 维度裁决汇总

| 维  | 报告                          | 裁决     | findings |
| --- | ----------------------------- | -------- | -------- |
| A1  | `research/audit-a1-report.md` | **fail** | 8        |
| A2  | `research/audit-a2-report.md` | **fail** | 8        |
| A3  | `research/audit-a3-report.md` | **fail** | 4        |
| A4  | `research/audit-a4-report.md` | **fail** | 9        |
| A5  | `research/audit-a5-report.md` | **fail** | 2        |
| A6  | `research/audit-a6-report.md` | **skip** | 0        |
| A7  | `research/audit-a7-report.md` | **fail** | 4        |
| A8  | `research/audit-a8-report.md` | **fail** | 6        |

**合计：** 41 findings · 7 维 fail · 1 维 skip

### Execute INDEX §2.1 证据索引（A5 独立复验）

| Tier                  | 证据                                                                                                                                 |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| 全量                  | `uv run pytest -q` exit 0                                                                                                            |
| S00 harness           | `uv run pytest tests/test_tier_a_live_harness.py -q` exit 0                                                                          |
| S-MERGE               | `uv run python scripts/loop_maintain.py` exit 0                                                                                      |
| CLI exit 2            | `uv run python scripts/tier_a_live_acceptance.py --source-id fred`（无 `QMD_ALLOW_LIVE_FETCH`）exit 2                                |
| §2.1 Tier 表          | `EXECUTION_INDEX.md` §2.1（harness · 全量 · loop · handoff · live 11/11）                                                            |
| 11/11 live acceptance | post-Repair **exit 0**（`doubt-final-20260703` · 2026-07-03）· `l4-tier-a-live-accept-evidence.md` · `research/doubt-live-final.log` |

---

## 3. 分维度详情（摘要）

### 3.1 A1 · Spec（链 A）

活卡/ADR-034/11 源 e2e 结构大体对齐；**FAIL** 因 F0 data health 未下沉 `plan-spec` Interface Contract、execute-evidence 目录缺失、INDEX 缺 §2.1、manifest/loop 工件不全。

### 3.2 A2 · Ponytail

`deribit_port` live 修复必要；**FAIL** 因 `tier_a_live_incremental_dispatch._run_live_sync` ~300 行重复 DCP-05、双份 sandbox 初始化、死代码/重复常量/测试样板。

### 3.3 A3 · Security

参考项目 runtime import **0**；**FAIL** 因 fred `QMD_FRED_INCREMENTAL_USE_MOCK` 可静默 mock 绕过 live 闸、fred `data_root` 分裂、SEC UA 校验弱于 port。

### 3.4 A4 · 代码质量

11/11 live e2e + ADR-028 矩阵未改；**FAIL** 因 deribit dispatch 仪器不一致、S-ACCEPT dispatch 无集成测、F0 缺失、e2e/acceptance DB 路径不同构、pass 逻辑过宽。

### 3.5 A5 · 完成情况

S00-INFRA + 11 源 e2e 结构评分 4–5；默认 CI pytest 绿；**FAIL** 因 S-ACCEPT F0 data health 未接入（与活卡/slices 冲突）。

### 3.6 A6 · 性能

本票未冻结 perf SLO；11 源串行验收与 network 默认 skip 为显式设计 → **SKIP**（无 finding）。

### 3.7 A7 · 运维隔离

隔离闸 + harness 负向测基本落地；**FAIL** 因 fred env/param 分裂、registry sync 无单测、dispatch 缺隔离复验、缺主库指纹断言。

### 3.8 A8 · 测试缺口

五字段门禁绿；22 network marks；**FAIL** 因 fred `live_smoke` 未标 network、S-ACCEPT 派发链/F0/exit1 缺 pytest。

---

## 4. 风险与结论（A9）

### 4.1 Findings 合并

**41 条**全表见 `research/audit-repair-ledger.md`（Repair 关账：**41/41 已修复**；A9 建账时 disposition 均 **待修复**）。

**P1 优先（关账阻塞）：**

| ID        | 维度 | 标题                                                     |
| --------- | ---- | -------------------------------------------------------- |
| A1-P1-001 | A1   | F0 data health 未下沉 plan-spec Interface Contract       |
| A2-P1-001 | A2   | dispatch `_run_live_sync` 三重重复 DCP-05                |
| A2-P1-002 | A2   | acceptance 与 dispatch 双份 sandbox 初始化               |
| A3-P1-01  | A3   | fred 可经 `QMD_FRED_INCREMENTAL_USE_MOCK` 静默 mock      |
| A4-P1-01  | A4   | deribit dispatch 硬编码 BTC-PERPETUAL 与 live API 不匹配 |
| A4-P1-02  | A4   | S-ACCEPT dispatch 层零集成/网络测试                      |
| A7-P1-001 | A7   | fred dispatch sync/inspect 路径可分裂                    |
| A8-P1-001 | A8   | fred `live_smoke` 未标 network，默认 pytest 可打真网     |

**跨维去重主题（Repair 一次修根因）：**

| 主题                      | 关联 ID                                      |
| ------------------------- | -------------------------------------------- |
| F0 data health            | A1-P1-001 · A4-P2-01 · A5-P2-001 · A8-P2-002 |
| S-ACCEPT dispatch 测试    | A4-P1-02 · A8-P2-001                         |
| fred data_root 分裂       | A3-P2-01 · A7-P1-001                         |
| 死代码/重复 if L454–459   | A2-P2-002 · A4-P2-02                         |
| SEC_EDGAR_USER_AGENT 文档 | A1-P3-001 · A5-P3-001                        |
| 未使用 import L240        | A2-P3-002 · A4-P3-02                         |

### 4.2 结论

- [x] **PASS** — Repair 关账：41/41 **已修复** · 0 阶段外置 · `validate-repair-close` exit 0
- [ ] **FAIL**

### 4.3 修复项（→ REPAIR.plan）

**已全部关账**（见 `research/audit-repair-ledger.md`）：[R-OPS](a2cda1eb-9181-4197-8c3e-a2b716bdfb12) 生产路径 · [R-TESTS](a04b0183-8f96-4130-86c5-122acda7b1fb) 测试 · [R-DOCS](17dd546c-8f80-4c6e-9d88-f9b2b764cbba) 文档/manifest。

### 4.4 阶段外置

| ID  | 问题                | 登记 |
| --- | ------------------- | ---- |
| —   | A9 建账无阶段外置行 | —    |

---

## 5. Repair 复验（Phase 8）

| 项                         | 结果     | 证据                                                                               |
| -------------------------- | -------- | ---------------------------------------------------------------------------------- |
| ledger 关账                | **PASS** | 41/41 **已修复** · 无待修复                                                        |
| `uv run pytest -q`         | **PASS** | exit 0（~486s，2026-07-03 主会话复验）                                             |
| harness + dispatch         | **PASS** | 29 passed, 1 skipped                                                               |
| `validate-repair-close`    | **PASS** | exit 0                                                                             |
| `validate-execute-handoff` | **PASS** | R-DOCS 复验 exit 0                                                                 |
| GitNexus analyze           | **PASS** | exit 0；untracked ops 文件待 commit 后复索引                                       |
| R-DOUBT-DOCS（D-05）       | **PASS** | §2 11/11 行 post-Repair 占位；§4.1 disposition 快照对齐 §4.2                       |
| R-DOUBT-DOCS（D-06）       | **PASS** | `plan-spec.md` F0 partial + SKIP caught-up 契约与 `tier_a_live_acceptance.py` 一致 |
