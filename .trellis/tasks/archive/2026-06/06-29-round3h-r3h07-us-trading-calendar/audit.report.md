# Audit Report — R3H-07 US Trading Calendar

> Findings SSOT：`agents/audit-finding-schema.md` · 各维 `research/audit-a{n}-report.md`  
> **A9 合并：** 2026-06-29 · 基线 `git diff 231b5798`

## 1. 元信息

| 字段          | 值                                            |
| ------------- | --------------------------------------------- |
| slug          | `06-29-round3h-r3h07-us-trading-calendar`     |
| protocol      | `4.1`                                         |
| GitNexus 刷新 | `research/gitnexus-audit-summary.md`（7.pre） |
| finding 计数  | **23**（P1×3 · P2×14 · P3×6）                 |

---

## 2. 维度裁决汇总

| 维  | 报告 | 裁决 | 证据路径                    |
| --- | ---- | ---- | --------------------------- |
| A1  |      | fail | research/audit-a1-report.md |
| A2  |      | fail | research/audit-a2-report.md |
| A3  |      | pass | research/audit-a3-report.md |
| A4  |      | pass | research/audit-a4-report.md |
| A5  |      | fail | research/audit-a5-report.md |
| A6  |      | skip | research/audit-a6-report.md |
| A7  |      | fail | research/audit-a7-report.md |
| A8  |      | fail | research/audit-a8-report.md |

**规则：** 任维 `fail` 或 §4.1 非占位 → 总裁决 **FAIL**。

### Execute INDEX §2.1 证据索引（只读引用）

| Tier        | Execute 证据路径/摘要                                                                                                                                                                                                                        |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CAL-US 专项 | `uv run pytest -q tests/test_us_trading_calendar.py tests/test_market_data_adapters.py tests/test_layer4_market_structure.py -k "calendar or trading or usEquity or windowKind or calUs or evidence_contract"` → 20 passed（Audit 独立复验） |
| 全量回归    | `uv run pytest -q` → Audit 时点 FAIL（`test_syncRegistry_cli_syncsYamlToDb`）；主会话 `8602a8eb` 已修 hygiene，Repair 须复验 exit 0                                                                                                          |

---

## 3. 分维度详情（摘要）

### 3.1 A1 · Spec — FAIL

链 A ADR-026 span cap 未闭合；SSOT 新文件 untracked；全量 pytest 单点红。

### 3.2 A2 · 过度工程 — FAIL

6 项 ponytail：死代码/拷贝粘贴/重复测/空壳 adapter/测膨胀。

### 3.3 A3 · 安全 — PASS

单 SSOT · CN 隔离 · 无 per-source 假日表；0 finding。

### 3.4 A4 · 代码质量 — PASS

变更面静态基线绿；0 finding。

### 3.5 A5 · 完成情况 — FAIL

链 B 交付未跟踪；AC-CLOSE 未闭合；2 项 P3 测缺口。

### 3.6 A6 · 性能 — SKIP

AUDIT.plan 冻结无独立 perf SLO。

### 3.7 A7 · 运维 — FAIL

GitNexus/loop 工程与 untracked 交付物不同步。

### 3.8 A8 · 测试缺口 — FAIL

S07-01 证据链、registry、authority_graph、全量 pytest。

---

## 4. 风险与结论（A9）

### 4.1 Findings 合并（→ `research/audit-repair-ledger.md`）

| ID        | P   | 维度 | 标题                                 | 锚点                                  | 根因                             | 修复方案                             | 验证                                        |
| --------- | --- | ---- | ------------------------------------ | ------------------------------------- | -------------------------------- | ------------------------------------ | ------------------------------------------- |
| A1-P2-01  | P2  | A1   | 核心 SSOT 交付物未纳入 git 变更集    | `git status` untracked SSOT + test    | Execute 未 git add               | git add + loop_maintain --fix        | `git diff 231b5798` 含两文件                |
| A1-P2-02  | P2  | A1   | ADR-026 显式窗口 span 仍按自然日计界 | ADR-026 §3 · S07-02                   | 显式窗 cap 未切 trading sessions | US port 接入 session span 校验 + TDD | 120 自然日≤120 交易日窗测绿                 |
| A1-P3-01  | P3  | A1   | 全量 pytest 单点失败                 | `test_syncRegistry_cli_syncsYamlToDb` | Windows GBK 子进程               | 直接调 main 或 utf-8 encoding        | `uv run pytest -q` exit 0                   |
| A2-P2-01  | P2  | A2   | recent_trading_window_start 死代码   | `fetch_window.py:30-46`               | 未接入 span cap                  | 随 A1-P2-02 接入，勿单独删除         | `rg recent_trading_window_start` 有 US 调用 |
| A2-P2-02  | P2  | A2   | 三 port mock 拷贝粘贴                | 三 US ports                           | 未抽共享 helper                  | fetch_window 增共享 helper           | 三 port 各减 ≥10 行                         |
| A2-P3-03  | P3  | A2   | mock 二次 filter                     | alpha/stooq fetch_payload             | `_mock_*` 已滤交易日             | 移除 fetch_payload 内二次 filter     | 假日负向测仍绿                              |
| A2-P2-04  | P2  | A2   | BOOT 与 S07-02 测重复                | `test_us_trading_calendar.py`         | RED→GREEN 未收敛                 | 合并 window_kind 测                  | 净减 ≥25 行                                 |
| A2-P2-05  | P2  | A2   | StagedUSEquityMarketAdapter 空壳     | `market_structure.py`                 | 复制 CNA 类                      | 单 StagedFixtureMarketAdapter        | usEquity 测绿                               |
| A2-P2-06  | P2  | A2   | DataSourceService 测膨胀             | `test_us_trading_calendar.py:245+`    | 未复用 service_path_support      | enable_source_route + patch helper   | setup 净减 ≥30 行                           |
| A5-P1-001 | P1  | A5   | SSOT 与专项测未纳入 git              | 同 A1-P2-01                           | 同左                             | 同 A1-P2-01                          | 同左                                        |
| A5-P2-001 | P2  | A5   | CAL-US registry PENDING              | round3h audit §7                      | S07-CLOSE 未执行                 | CAL-US → CLOSED                      | `rg CAL-US.*CLOSED`                         |
| A5-P3-001 | P3  | A5   | get_missing_trading_days 无测        | S07-01                                | TDD 缺口                         | 增 missing 行为测                    | `pytest -k missing` 绿                      |
| A5-P3-002 | P3  | A5   | stooq 假日负向无专用测               | S07-02/04                             | 仅 yahoo/alpha 有                | 增 stooq 假日测                      | `pytest -k stooq` 绿                        |
| A7-P2-01  | P2  | A7   | detect_changes 未覆盖 untracked      | gitnexus-audit-summary                | 同 A1-P2-01                      | git add + re-analyze                 | detect_changes 含新符号                     |
| A7-P2-02  | P2  | A7   | impact 无法锚定                      | AUDIT A7                              | 索引缺新符号                     | 同 A7-P2-01 + impact                 | impactedCount > 0                           |
| A7-P3-01  | P3  | A7   | context_pack tests[] 缺登记          | context_pack.json                     | freeze 后未刷新                  | loop_maintain --fix                  | context_pack 含新测路径                     |
| A7-P3-02  | P3  | A7   | loop_manifest 全 pending             | loop_manifest.json                    | 未同步 INDEX                     | 标 closed/pass                       | manifest 与 INDEX 一致                      |
| A8-P1-001 | P1  | A8   | SSOT 未进 git 证据链                 | 同 A1-P2-01                           | 同左                             | 同左                                 | 同左                                        |
| A8-P1-002 | P1  | A8   | 专项测未进 git 证据链                | 同 A1-P2-01                           | 同左                             | 同左                                 | 同左                                        |
| A8-P2-001 | P2  | A8   | CAL-US registry PENDING              | 同 A5-P2-001                          | 同左                             | 同左                                 | 同左                                        |
| A8-P2-002 | P2  | A8   | 全量 pytest 未绿                     | 同 A1-P3-01                           | 同左                             | 同左                                 | 同左                                        |
| A8-P2-003 | P2  | A8   | authority_graph 未登记               | authority_graph.yaml                  | loop §8 缺口                     | loop_maintain --fix                  | loop_maintain exit 0                        |
| A8-P3-001 | P3  | A8   | GitNexus 索引缺 SSOT                 | gitnexus-audit-summary                | untracked                        | commit 后 analyze                    | query 命中 SSOT                             |

### 4.2 结论

- [ ] **PASS**
- [x] **FAIL** — 5 维 fail + 23 finding → REPAIR.plan → Phase 8

### 4.3 修复项（→ REPAIR.plan §1）

与 §4.1 同 ID 全集；合并为 6 修复包见 `REPAIR.plan.md`。

### 4.4 阶段外置

A9 建账 **0** 项阶段外置。

| ID  | 问题 | 绑定阶段/任务 | 依赖/承接 | 登记位置 |
| --- | ---- | ------------- | --------- | -------- |
| —   | —    | —             | —         | —        |

---

## 5. Repair 复验（Phase 8 后）

| 项                             | 结果     | 证据                                                                                                                                                                                                           |
| ------------------------------ | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| §4.3 全部关闭                  | **PASS** | ledger 23/23 已修复                                                                                                                                                                                            |
| CAL-US 专项 pytest             | **PASS** | `uv run pytest -q tests/test_us_trading_calendar.py tests/test_market_data_adapters.py tests/test_layer4_market_structure.py -k "calendar or trading or usEquity or windowKind or calUs or evidence_contract"` |
| `uv run pytest -q` exit 0      | **PASS** | 2026-06-29 主会话复验                                                                                                                                                                                          |
| `validate-repair-close` exit 0 | **PASS** | task.py validate-repair-close                                                                                                                                                                                  |
