# Audit A5 — AC 追溯 / 证据抽检 / 完成度 · R3H-06

> **维度：** A5（audit-completion）  
> **任务：** `06-29-round3h-r3h06-clean-schema`  
> **权威：** `agents/audit-a5-completion.md` · `agents/audit-adversarial-authority.md` · `frozen/R3H_06_CLEAN_SCHEMA.md` · `EXECUTION_INDEX.md`  
> **审计日期：** 2026-06-29  
> **模式：** 只读 + sandbox 抽检（未改生产库、未 commit）

---

## 总裁决

**PASS_WITH_FIXES**

实现侧 AC 追溯链在代码与测试中 **可复现且闭环**（A5 独立抽检 `idempotency` / `domain_router` / 全库 pytest / `loop_maintain` 均 exit 0，与 Execute 声称一致）。  
**但** Execute 证据纪律存在 **2 项 BLOCKING 流程缺口**：9.1–9.9 **缺 RED 落盘**、多数 `*-green.txt` **非真实终端输出**（仅一行自述）。`validate-execute-handoff` 虽 exit 0，主会话 merge 前须补证据或书面 waive，否则 finish-work 依据不足。

---

## Handoff 门禁

```bash
uv run python .trellis/scripts/task.py validate-execute-handoff .trellis/tasks/06-29-round3h-r3h06-clean-schema
```

| 项     | 结果                                |
| ------ | ----------------------------------- |
| 退出码 | **0**                               |
| 输出   | `Execute handoff validation passed` |

**注：** handoff 通过 **不抵消** RED 缺失与 green 证据薄弱（见 §4.3）。

---

## §9.0–9.10 证据清单

| Step               | RED 证据                                                  | GREEN 证据                           | 其他                                  | 判定                    |
| ------------------ | --------------------------------------------------------- | ------------------------------------ | ------------------------------------- | ----------------------- |
| 9.0 boot           | `execute-evidence/9.0-red.txt` ✓（ModuleNotFound exit 4） | `9.0-green.txt`                      | `research/execute-evidence/` 双份 9.0 | GREEN 弱（见下）        |
| 9.1 bar_ddl        | **缺失**                                                  | `9.1-green.txt`（一行自述）          | —                                     | **RED 缺口**            |
| 9.2 disclosure_ddl | **缺失**                                                  | `9.2-green.txt`                      | —                                     | **RED 缺口**            |
| 9.3 stg_bar_ohlcv  | **缺失**                                                  | `9.3-green.txt`                      | —                                     | **RED 缺口**            |
| 9.4 stg_disclosure | **缺失**                                                  | `9.4-green.txt`                      | —                                     | **RED 缺口**            |
| 9.5 domain_router  | **缺失**                                                  | `9.5-green.txt`                      | —                                     | **RED 缺口**            |
| 9.6 cninfo_no_bar  | **缺失**                                                  | `9.6-green.txt`                      | —                                     | **RED 缺口**            |
| 9.7 idempotency    | **缺失**                                                  | `9.7-green.txt`                      | —                                     | **RED 缺口**            |
| 9.8 pilot_compat   | **缺失**                                                  | `9.8-green.txt`（rg + promote 自述） | —                                     | **RED 缺口**            |
| 9.9 docs_coverage  | **缺失**                                                  | `9.9-green.txt`                      | —                                     | **RED 缺口**            |
| 9.10 merge_gate    | **缺失**                                                  | **缺失**（无 `9.10-green.txt`）      | `9.10-full.txt`（一行「exit 0」）     | RED/GREEN 均缺；full 弱 |

**RED 缺口汇总：** `EXECUTION_INDEX.md` §1 要求每步 `9.x-{red,green}.txt`；`frozen` §8「每步先 RED」。磁盘上 **仅** `9.0-red.txt`（`research/` 与 `execute-evidence/` 各一份）。9.1–9.9 无 RED；9.10 无 RED 亦无独立 GREEN。

---

## green.txt 真实性抽检（必做 2 份）

| 文件                             | 内容摘要                                             | 真实性                                              | §4.3               |
| -------------------------------- | ---------------------------------------------------- | --------------------------------------------------- | ------------------ |
| `execute-evidence/9.0-green.txt` | `12 passed` + `Resume 2026-06-29: boot module loads` | **非**完整 pytest 终端输出；无 `===` 摘要行、无耗时 | **是** — 自述 PASS |
| `execute-evidence/9.7-green.txt` | 单行 `idempotency promote green (...)`               | **非**终端输出                                      | **是** — 自述 PASS |

**其余 green 文件（9.1–9.6、9.8–9.9）：** 均为单行「subset green」自述，**无** pytest/rg 原始输出 → 统一记入 §4.3。

**`9.10-full.txt`：** 仅 `uv run pytest -q: exit 0 (full suite, 2026-06-29 resume)`，无 passed 计数 → §4.3。

---

## §10 最弱 2 行 — 独立复跑（audit-sandbox）

选取规则：tier 非 smoke 全绿；证据仅自述；与 Red Flag / 幂等相关。

| 原 §10 / INDEX 行                                                 | 复跑命令                                                             | exit              | 与 Execute 一致？                    |
| ----------------------------------------------------------------- | -------------------------------------------------------------------- | ----------------- | ------------------------------------ |
| **G6 幂等** · `tests/test_r3h06_clean_schema.py` `-k idempotency` | `uv run pytest tests/test_r3h06_clean_schema.py -q -k idempotency`   | **0**（1 passed） | **是** — 与 `9.7-green.txt` 声称一致 |
| **三域路由** · `-k domain_router`（含 9.5b macro 表名）           | `uv run pytest tests/test_r3h06_clean_schema.py -q -k domain_router` | **0**（1 passed） | **是** — 与 `9.5-green.txt` 声称一致 |

**附加抽检（9.8 / 9.9 / 9.10）：**

| 命令                                                                         | exit                    | 与 Execute              |
| ---------------------------------------------------------------------------- | ----------------------- | ----------------------- |
| `rg market_bar_clean` backend/scripts/tests/specs/ROUND_3 docs（INDEX §1.1） | **零匹配**（grep 复核） | 与 `9.8-green.txt` 一致 |
| `uv run pytest tests/test_migration_coverage.py -q` + `loop_maintain.py`     | **0**                   | 与 `9.9-green.txt` 一致 |
| `uv run pytest -q`（全库）                                                   | **0**                   | 与 `9.10-full.txt` 一致 |

**结论：** 行为层 Execute 声称 **可信**；证据文件层 **不可作独立审计凭证**。

---

## audit-prod-path（registry §2.1）

| 项                                          | 结论                                                                          |
| ------------------------------------------- | ----------------------------------------------------------------------------- |
| `AUDIT.plan.md` / `EXECUTION_INDEX.md` §2.1 | 仅冻结 Tier A / A+ / **D（禁止主库）**；**未**冻结 `AUDIT_PROD_ROOT` 副本流程 |
| 本任务                                      | **SKIP** — schema 任务在 temp/pilot DB 验证；无 prod-path 复制要求            |
| 主库                                        | 未触碰 `quant_monitor.duckdb`（与 frozen §8 / Tier D 一致）                   |

---

## §3.5 AC 追溯与评分

| AC#                 | 追溯链（原始→INDEX→§9→证据）                                                    | 分    | 抽检/复验                                      |
| ------------------- | ------------------------------------------------------------------------------- | ----- | ---------------------------------------------- |
| AC-BOOT             | 活卡 §9.0 → INDEX 9.0 → `test_r3h06_clean_schema.py` import → `9.0-{red,green}` | **4** | RED 有；GREEN 弱；模块存在且可跑               |
| AC-SCHEMA-G3G4-BAR  | §5.0.1 SCHEMA-G3G4 → 9.1 → `-k bar_ddl` + 013 → `9.1-green`                     | **4** | 无 RED；A8 子集绿；OHLCV 列断言偏弱（A8）      |
| AC-CNINFO-SHAPE     | §5.0.1 CNINFO → 9.2 → `-k disclosure_ddl` + §6.1 DDL → `9.2-green`              | **4** | 无 RED；capabilities ⊆ DDL 有测                |
| AC-SCHEMA-G4-OHLCV  | 9.3 → 014 + `-k ohlcv` → `9.3-green`                                            | **4** | 无 RED；staging 列有；promote 值弱断言         |
| AC-STG-DISCLOSURE   | 9.4 → `filing_id`→`announcement_id` → `9.4-green`                               | **4** | 无 RED                                         |
| AC-SCHEMA-G3-ROUTER | 9.5+9.5b → `clean_write_targets.py` → `-k domain_router` → `9.5-green`          | **4** | **A5 复跑 0**；macro populate E2E 缺（A8 P0）  |
| AC-CNINFO-NO-BAR    | 9.6 / G5 → `-k cninfo_no_bar` → `9.6-green`                                     | **5** | 负向 E2E 充分（A8 确认）                       |
| AC-G6-IDEMPOTENCY   | §5.0.1 G6 → 9.7 → `-k idempotency` → `9.7-green`                                | **4** | **A5 复跑 0**；仅 bar 域；无 RED               |
| AC-PILOT-COMPAT     | 9.8 → rg 零匹配 + r3g03 回归 → `9.8-green`                                      | **4** | rg 零匹配确认；无 RED；无 pytest 封装 rg       |
| AC-DOCS             | 9.9 → MIGRATION_COVERAGE + loop → `9.9-green`                                   | **4** | **A5 复跑 0**；disclosure 表未进 L5 常量（A8） |
| AC-MERGE            | 9.10 → 全库 pytest → `9.10-full`                                                | **4** | **A5 全库 0**；证据文件无计数行                |

**§5.0.1 交叉项（AUDIT.plan §3）：**

| ID                      | Step 链                                                    | 分数  | 备注                                               |
| ----------------------- | ---------------------------------------------------------- | ----- | -------------------------------------------------- |
| SCHEMA-G3G4             | 9.1+9.3+9.5（AUDIT 写 9.4；实现以 INDEX 9.1/9.3/9.5 为准） | **4** | 实现闭环；ROADMAP §5.0.0/§5.0.1 文档矛盾（A1-B02） |
| CNINFO-DISCLOSURE-SHAPE | 9.2+9.5（AUDIT）/ 9.2+9.4+9.6（INDEX）                     | **4** | IMPL 可追溯                                        |
| G6-IDEMPOTENCY          | 9.7（AUDIT 误写 9.6；应以 9.7 upsert 测为准）              | **4** | bar 幂等已证；披露/宏观幂等未测                    |

---

## A5 Checklist

- [x] 每条 AC 追溯链 + 1–5 分（§3.5）
- [x] 抽检复跑与 Execute 一致（idempotency / domain_router / 全库 — **一致**）
- [ ] green.txt 非占位符 — **未满足**（多数为单行自述 → §4.3）
- [x] prod-path — **SKIP**（未冻结）
- [ ] registry / deferred — ROADMAP 矛盾、RED 缺口须 closeout 或 §4.3 书面处理

---

## §4.3 登记（证据纪律）

| ID         | 严重度       | 发现                                                                  | 要求                                                                 |
| ---------- | ------------ | --------------------------------------------------------------------- | -------------------------------------------------------------------- |
| **A5-B01** | **BLOCKING** | 9.1–9.9 **无** `*-red.txt`；违反 frozen §8 TDD 与 INDEX §1            | 补跑各步 RED 命令落盘，或主会话引用 GLOBAL_TESTING_POLICY 书面 waive |
| **A5-B02** | **BLOCKING** | 全部 `*-green.txt` + `9.10-full.txt` 为自述摘要，**无**可审计终端输出 | 补粘 pytest/rg 完整输出，或 waive 并注明 A5 独立复跑为唯一凭证       |
| A5-NB01    | LOW          | `research/execute-evidence/` 与 `execute-evidence/` 双份 9.0          | 删重复或加 README 说明 SSOT 目录                                     |
| A5-NB02    | LOW          | `AUDIT.plan.md` §3 G6 指向 9.6（应为 9.7）                            | coordinator 修正 AUDIT.plan                                          |

---

## 计划外发现

> 已对抗搜索：§9 步骤外 runtime 路径、`execute-evidence` 全量、`implement.jsonl`（无 manifest-amend）、A2/A8 交叉核对。

| #   | 发现                                                                                  | 证据                                     | 分类                                           |
| --- | ------------------------------------------------------------------------------------- | ---------------------------------------- | ---------------------------------------------- |
| O1  | **handoff 绿但 RED 不全** — `validate-execute-handoff` exit 0 与磁盘仅 `9.0-red` 并存 | 本报告 §9 证据表 + handoff 输出          | **计划外 · 门禁口径**                          |
| O2  | **9.10 证据形态偏离 INDEX** — 仅有 `9.10-full.txt`，无 `{red,green}` 对               | `execute-evidence/` glob                 | **计划外**                                     |
| O3  | **fred macro promote E2E 无测** — `populate_macro_from_bundle` tests 零引用           | A8 P1；`rehearsal_loader.py`             | **计划外 · AC 链薄弱环**（路由表名有、写入无） |
| O4  | **FRED 回归仍走 bar 形 staging** — 与 9.5b 目标分叉                                   | A8 P2；`test_LiveEvidenceBridge_fred_*`  | **计划外 · 假绿风险**                          |
| O5  | **G6 仅 bar 域幂等** — cninfo/fred 重复 promote 未测                                  | A8 矩阵；`9.7-green` 仅 idempotency 一词 | **计划外**                                     |
| O6  | **9.8 rg 门禁无 pytest 封装** — 依赖 Execute 人工 rg + 自述                           | A8 P6；本报告 rg grep 复核               | **计划外**                                     |
| O7  | **核心交付未 commit** — 分支 `master..HEAD` 空（A1）                                  | git 状态                                 | **计划外 · merge 阻塞**（非 A5 行为层）        |

**manifest-amend.md：** 不存在；`implement.jsonl` 24 条 manifest 无 post-freeze 修正。

---

## 全部发现项汇总

| 优先级 | ID      | 分类       | 发现                                   | 判定                    | 责任                  |
| ------ | ------- | ---------- | -------------------------------------- | ----------------------- | --------------------- |
| **P0** | A5-B01  | TDD 证据   | 9.1–9.9 RED 缺失                       | **BLOCKING**            | Execute / 主会话      |
| **P0** | A5-B02  | 证据真实性 | green/full 无终端输出                  | **BLOCKING**            | Execute / 主会话      |
| P0     | O7      | 流程       | 未 commit                              | **BLOCKING**（A1 已报） | 主会话                |
| P1     | O3      | AC 覆盖    | fred→`axis_observation` promote E2E 缺 | NON-BLOCKING            | debt-lite / follow-up |
| P1     | O4      | 假绿       | FRED bridge 测 bar 形                  | NON-BLOCKING            | A8 建议               |
| P1     | O5      | G6         | 披露/宏观幂等未测                      | NON-BLOCKING            | follow-up             |
| P2     | O1      | 门禁       | handoff 与 RED 要求不一致              | NON-BLOCKING            | Trellis 工具链        |
| P2     | O6      | 9.8        | rg 无 pytest                           | NON-BLOCKING            | 可选加固              |
| P3     | A5-NB01 | 漂移       | 双份 9.0 证据                          | NON-BLOCKING            | 清理                  |
| P3     | A5-NB02 | 文档       | AUDIT.plan G6 step 笔误                | NON-BLOCKING            | coordinator           |

---

## A5 维度结论

| 项                    | 结论                                                                                       |
| --------------------- | ------------------------------------------------------------------------------------------ |
| AC 行为闭环           | **PASS** — 活卡 §2 七项预期 + §5.0.1 三项在实现与 A5 抽检中可复现                          |
| 证据追溯链            | **FAIL（流程）** — RED 缺口 + green 自述；不得以 evidence 文件 alone 签 PASS               |
| 独立复跑              | **PASS** — 与 Execute 声称一致                                                             |
| 对抗 BLOCKING（实现） | **0** — macro E2E / 多域幂等为 NON-BLOCKING 测试债                                         |
| 建议主会话裁决        | **PASS_WITH_FIXES** — 闭合 A5-B01/B02（或 waive）+ commit + ROADMAP 统一后再 `finish-work` |

---

## 交叉引用

| 维度 | 关联                                         |
| ---- | -------------------------------------------- |
| A1   | A5-B01 与 A1-B03 同源；ROADMAP 矛盾          |
| A8   | O3–O6 测试缺口；65 测子集已绿                |
| A2   | `clean_write_targets.py` in-scope；FRED 双轨 |

**不以自述为 PASS** — 本报告 PASS_WITH_FIXES 依据为 **A5 独立复跑 + 代码/测追溯**，非 `execute-evidence/*` 文件内容。
