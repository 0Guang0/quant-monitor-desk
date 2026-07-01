# 对抗性审计报告 — B01-FRED FRED Sandbox Pilot

> **Auditor:** B01-FRED 对抗性审计 Agent · `composer-2.5`  
> **工作区：** `quant-monitor-desk-wt-b01-fred`  
> **分支：** `feature/round3-fred-authorized-sandbox-pilot`  
> **日期：** 2026-06-25  
> **输入：** `agents/audit-adversarial-authority.md` · `BATCH_01_ADVERSARIAL_AUDIT.md` · `research/audit-evidence/a1–a8.md` · `research/b01-fred-audit-closures.md` · worktree diff  
> **注记：** 任务根目录 **无** `audit.report.md` / `audit_matrix.json`（A9/Repair 汇总未落盘）；本报告以 A1–A8 证据 + 2026-06-25 独立复跑为准，并**推翻**首轮维度报告中将「未 commit」标为 CLOSED 的流程结论。  
> **约束：** 只读审计 + sandbox 复跑；**禁止 commit**

---

## 总判定

| 项                        | 值                                                                                                 |
| ------------------------- | -------------------------------------------------------------------------------------------------- |
| **对抗性审计判定**        | **PASS_WITH_MERGE_GATE**                                                                           |
| **Repair / A9 状态**      | **未完成** — 无 `audit.report.md`；`AUDIT.plan.md` §1 勾选仍为 `[ ]`                               |
| **A1–A8 业务阻断复验**    | **CONFIRMED** — AC-FRED-01..07、B2.5-O-05 re-defer、FRED-07 CLOSED-SKIP-OPT-IN 与 Execute 证据一致 |
| **OPEN（BLOCKING）**      | **2**                                                                                              |
| **OPEN（NON-BLOCKING）**  | **1**                                                                                              |
| **Track A merge #3 就绪** | **否** — 须主会话 commit + A9 汇总 + 确认 WL 已合并                                                |

> **零遗留规则：** `BATCH_01_ZERO_OPEN_CLOSURE_POLICY.md` 要求 **0 OPEN 方可 PASS**。当前存在 BLOCKING OPEN → 不得标 **PASS**。

---

## Repair 状态与 A1–A8 摘要

| 维  | 维度报告判定  | 对抗性复验       | 备注                                       |
| --- | ------------- | ---------------- | ------------------------------------------ |
| A1  | PASS · OPEN 0 | **PASS（业务）** | 推翻 A1-UNCM「CLOSED」→ 见 ADV-FRED-B01    |
| A2  | PASS · OPEN 0 | **PASS**         | ponytail 最小 diff；无新依赖               |
| A3  | PASS · OPEN 0 | **PASS**         | 无密钥泄露；fail-closed 授权               |
| A4  | PASS · OPEN 0 | **PASS（业务）** | 推翻 A4-UNCM → ADV-FRED-B01                |
| A5  | PASS · OPEN 0 | **PASS（业务）** | AC 追溯链完整；§10 抽检一致                |
| A6  | SKIP · OPEN 0 | **SKIP（维持）** | caps 有界；3 项 NON-BLOCKING 已 CLOSED     |
| A7  | PASS · OPEN 0 | **PASS（业务）** | 零 migration/DB 写；推翻 A7-O5 流程 CLOSED |
| A8  | PASS · OPEN 0 | **PASS（业务）** | 五字段 docstring；语义负向测达标           |

**Repair 声称：** A1–A8 均 0 OPEN，但 **无** 汇总 `audit.report.md` 锚定 Repair 闭环。对抗性审计按 playbook §4.1「Audit→Repair→对抗性」视 Repair 为 **未正式收口**。

---

## Playbook §8.5 逐行复验

| §8.5 维度         | PASS？        | 对抗性证据 / 残留                                                                                                                                                         |
| ----------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Registry**      | **条件 PASS** | working tree 已增 `fred` 行：`enabled_by_default=false` · `sandbox_candidate` · `production_default=false`；**未 commit**                                                 |
| **B2.5-O-05**     | **PASS**      | `fred_pilot_closeout.json`: `b2_5_o_05_closed=false` · `macro_supplementary_cannot_close=true` · `fred_only_evidence=true`；`test_b250o05_reDeferred_closureRowClosed` 绿 |
| **边界**          | **PASS**      | `data_health.py` 无 diff；`fred_evidence_validator.py` pilot-local only                                                                                                   |
| **Tier A pytest** | **PASS**      | 见 §pytest 复跑                                                                                                                                                           |
| **全库 pytest**   | **PASS**      | `uv run pytest -q` exit **0**（1 skipped = FRED-07 live opt-in）                                                                                                          |
| **ruff scoped**   | **条件 PASS** | `tests/test_fred_*.py` + `fred_*.py` 绿；`backend/app/ops` 存量 **91** 违规（非 FRED 引入，AA-FRED-A8-03）                                                                |
| **已提交**        | **FAIL**      | 见 ADV-FRED-B01                                                                                                                                                           |

---

## pytest 复跑（对抗性 sandbox · 2026-06-25）

| 命令                                                                                                                                                     | exit  | 摘要                                         |
| -------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- | -------------------------------------------- |
| `uv run pytest tests/test_fred_source_registry.py tests/test_fred_sandbox_pilot.py tests/test_fred_staged_semantics.py tests/test_ops_data_health.py -q` | **0** | **39 passed, 1 skipped**                     |
| `uv run pytest tests/test_source_capabilities.py tests/test_source_route_planner.py -q`                                                                  | **0** | **18 passed**                                |
| `uv run pytest -q`（Tier B）                                                                                                                             | **0** | 全库绿（含 `test_catalog.yaml` staged 状态） |

---

## diff 对抗核对（计划外搜索）

| 检查                                | 结果       | 证据                                                                                  |
| ----------------------------------- | ---------- | ------------------------------------------------------------------------------------- |
| `data_health.py` 主体               | **未触及** | `rg fred data_health.py` → 0                                                          |
| production clean write              | **无路径** | `production_clean_write=False`；`allow_production_clean_write` 拒绝                   |
| macro 误关 B2.5-O-05                | **守卫**   | closeout JSON + `test_fredCloseout_macroCannotClose_*`                                |
| FRED 接入 DataSourceService live 链 | **未接线** | 仅 `ops/fred_*` sandbox pilot                                                         |
| registry 与 proposed delta 一致性   | **PASS**   | `proposed_registry_delta.yaml` 与 yaml diff 语义对齐                                  |
| 任务卡作 live 授权                  | **未犯**   | `execute-evidence/authorization.yaml` 落盘；无 key → `FRED_PILOT_FAIL_AUTH`           |
| BATCH_01 hardening 负向测           | **PASS**   | AkShare not Primary（staged semantics）· macro 不能关 B2.5-O-05 · 缺授权 blocks fetch |

---

## OPEN / CLOSED / DEFERRED

| ID                | 级别                     | 发现                                                                                                                              | 对抗性裁决                                                                                                         | 主会话 Must-fix                                                        |
| ----------------- | ------------------------ | --------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------- |
| **ADV-FRED-B01**  | **OPEN（BLOCKING）**     | 实现 + 任务工件 + registry yaml + 大部分测试 **未 commit**；仅 `tests/test_catalog.yaml` + `scripts/check_test_catalog.py` staged | `BATCH_01_ZERO_OPEN_CLOSURE_POLICY` §闭合定义：「未 commit → BLOCKING」；A1/A4/A7 将 UNCM 标 CLOSED **本报告推翻** | 主会话按 allowed 清单 commit 全交付物后复跑 `uv run pytest -q`         |
| **ADV-FRED-B02**  | **OPEN（BLOCKING）**     | 缺 `audit.report.md` · `audit_matrix.json`；`AUDIT.plan.md` A1–A9 勾选未更新                                                      | A9 汇总未做 → Repair 无 SSOT 锚点；对抗性不得代写 PASS                                                             | 主会话或 Repair agent 产出 `audit.report.md` + matrix，勾选 AUDIT.plan |
| **ADV-FRED-NB01** | **OPEN（NON-BLOCKING）** | `fred_evidence_validator` 的 `MALFORMED_ROW` / `MALFORMED_VALUE` / `MALFORMED_DATE` / `MISSING_ROWS` 无独立 pytest                | A8 AA-FRED-A8-01 仅记建议、未书面 CLOSED                                                                           | 增 1 条 mutation 测或 ADR/wont-fix + closure test 引用                 |
| FRED-07           | **CLOSED-SKIP-OPT-IN**   | 无 `FRED_API_KEY`                                                                                                                 | `test_fred07_liveFetch_closureClosedSkipOptIn_withoutApiKey`                                                       | —                                                                      |
| B2.5-O-05         | **CLOSED（re-defer）**   | live FRED primary → Batch 6                                                                                                       | `b01-fred-audit-closures.md` + closeout JSON + staged semantics 三测                                               | —                                                                      |
| AA-FRED-A8-02     | **CLOSED**               | S3 schema mutation                                                                                                                | `run_failure_scenario("schema")`                                                                                   | —                                                                      |
| AA-FRED-A8-03     | **CLOSED**               | ops ruff 存量 91                                                                                                                  | 非 FRED 引入                                                                                                       | —                                                                      |
| A6-NB-1..3        | **CLOSED**               | RG 旁路 / rows cap / live body read                                                                                               | 记入 Batch 6 复评                                                                                                  | —                                                                      |

---

## 计划外发现（对抗搜索后）

| ID          | 发现                                                                   | 级别 | 说明                                                                                                                                                           |
| ----------- | ---------------------------------------------------------------------- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| OOB-FRED-01 | A1–A8 证据与 `AUDIT.plan.md` 勾选不同步                                | P3   | 证据在 `research/audit-evidence/` 但 plan 仍 `[ ]`；commit 时一并刷新                                                                                          |
| OOB-FRED-02 | `test_fred_source_registry.py` **硬依赖** registry yaml 已含 `fred` 行 | P2   | feature 分支 **须** 携带 registry delta（与 `proposed_registry_delta.yaml` 一致）；Track A #3 合并时 coordinator 批处理 reconciled，非「只交 delta 不测 yaml」 |
| OOB-FRED-03 | GitNexus 未索引新 `fred_sandbox_pilot` 符号                            | P3   | post-merge `gitnexus analyze`；不阻断                                                                                                                          |

**对抗搜索声明：** 已对照 `audit-adversarial-authority.md` 各维最低动作 · R3E `R3E_fred_authorized_sandbox_pilot.md` · `BATCH_01_HARDENING_RULES.md` · `BATCH_01_ADVERSARIAL_AUDIT.md` B01-AUD-04/07/10/12 · MASTER §2 AC-FRED-\* · `fred_sandbox_pilot.py` / `fred_fetch_ports.py` / `fred_evidence_validator.py` 全文 · A1–A8 计划外发现表；除上表 OPEN 项外，**未发现**新的 production-live 声称、data_health 主体改写或 macro 误关 B2.5-O-05 路径。

---

## Track A merge #3 就绪性

| 门禁                                    | 状态             | 说明                                                          |
| --------------------------------------- | ---------------- | ------------------------------------------------------------- |
| Playbook §7.2 顺序 #3 前置「WL 已合并」 | **待主会话确认** | 本 worktree 未验证 `master` 是否已含 B01-WL                   |
| 对抗性审计 0 OPEN                       | **FAIL**         | OPEN **3**（2 BLOCKING + 1 NON-BLOCKING）                     |
| §8.5 验证命令                           | **PASS**         | 全库 pytest 绿；FRED 切片绿                                   |
| B2.5-O-05 / FRED-07 闭合                | **PASS**         | 书面 re-defer + CLOSED-SKIP-OPT-IN                            |
| 分支已提交                              | **FAIL**         | ADV-FRED-B01                                                  |
| `audit.report.md` + A9                  | **FAIL**         | ADV-FRED-B02                                                  |
| Registry 三件套                         | **条件就绪**     | yaml 内容正确；须随 feature commit，由主会话 Track A #3 merge |

**结论：** 实现质量与 sandbox 边界 **达标**，但 **尚不可 merge**。主会话须：(1) commit 交付物；(2) 补 `audit.report.md`；(3) 闭合 ADV-FRED-NB01 或书面 defer；(4) 确认 WL 已合并；(5) 复跑对抗性审计至 **0 OPEN** 后标 **PASS**。

---

## 主会话 Must-Fix（按优先级）

1. **ADV-FRED-B01** — commit allowed 文件（`backend/app/ops/fred_*.py` · `tests/test_fred_*.py` · registry yaml fred 行 · `service.py` macro_series 映射 · task 工件 · catalog）。
2. **ADV-FRED-B02** — 产出 `audit.report.md` + `audit_matrix.json`；更新 `AUDIT.plan.md` 勾选。
3. **ADV-FRED-NB01** — 补 `MALFORMED_VALUE` mutation 测或 wont-fix 闭合。
4. 合并前：`gitnexus detect_changes()` · playbook §6 九项 closure checklist。

---

## Verification Story

| 项                 | 结果                                                       |
| ------------------ | ---------------------------------------------------------- |
| Tests reviewed     | **是** — FRED 三文件 + registry + data_health 回归         |
| Build verified     | **是** — Tier A + Tier B 全绿                              |
| Security checked   | **是** — 静态 rg + A3 威胁面复验                           |
| Repair report read | **否** — `audit.report.md` 不存在；已读 A1–A8              |
| Diff reviewed      | **是** — staged + unstaged + untracked 与 A1 manifest 一致 |
| Adversarial search | **是** — 见 §计划外发现                                    |

---

## Final Verdict

**PASS_WITH_MERGE_GATE**

业务 AC、sandbox 边界、B2.5-O-05 re-defer 与 FRED-07 opt-in 闭合 **可信**；A1–A8 首轮结论在实现面上 **成立**。但零遗留策略下 **OPEN = 3**（含 2 BLOCKING 流程项），**不满足 PASS**；Track A merge #3 **未就绪**，待主会话 commit + A9 汇总 + NB01 闭合后复验。
