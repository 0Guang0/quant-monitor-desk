# Audit A1 — Spec / Trace Authority（R3-DCP-08）

> **维：** A1 trellis-check · Trace Authority · GitNexus  
> **任务：** `.trellis/tasks/07-02-wave4-r3-dcp-08-layer4/`  
> **协议：** `plan_protocol_version: 4.1`  
> **工作区：** `quant-monitor-desk-wt-dcp08` · branch `feature/wave4-r3-dcp-08-layer4`  
> **日期：** 2026-07-02  
> **审计范围：** 仅 A1；未审 A2–A8

---

## 维度证据（§3.1）

| 检查项                           | 结果              | 证据                                                                                                                                                                                                                  |
| -------------------------------- | ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **trellis-check 1 变更范围**     | PASS              | `git status`：7 modified + 8 untracked（`clean_read.py`、`test_layer4_*_clean*`、任务目录等）；`git diff --name-only HEAD` 列 7 路径                                                                                  |
| **trellis-check 2 任务工件**     | PASS              | 已 Read `prd.md`（隐含 task.json）、`frozen/R3_DCP_08_LAYER4_MARKET_STRUCTURE.md`、`00-EXECUTION-ENTRY.md`、`to-issues-slices.md`、`plan-consolidation.md`；`get_context.py --mode packages` → `Spec layers: backend` |
| **trellis-check 3 项目检查**     | PASS              | `uv run pytest -q` exit 0（全量）；靶向 `test_layer4_us_equity_clean_e2e` / `clean_read` / `mootdx -k` 7 passed；`loop_maintain.py` OK                                                                                |
| **trellis-check 4 Spec Quality** | PASS              | 触及 `backend/app/layer4_markets/`；无独立 package spec index，对照 `docs/modules/layer4_market_structure.md` + ADR-033                                                                                               |
| **trellis-check 5 测试覆盖登记** | PASS              | `tests/test_catalog.yaml` 已改（untracked diff）；新测 `test_layer4_clean_read.py`、`test_layer4_us_equity_clean_e2e.py` 存在                                                                                         |
| **trellis-check 6 跨层**         | PASS（本票 2 层） | Storage（DuckDB clean）→ `clean_read.py` → `market_structure.py` → pytest；无新 UI/API 面；`data_commands.py` mootdx dry-run 与 registry 片正交                                                                       |
| **trellis-check 7 manifest**     | FAIL              | `check.jsonl` 2 行（frozen + INDEX）均在磁盘；**INDEX §1 证据路径与 `execute-evidence/` 不一致**（见 A1-P1-001）                                                                                                      |
| **diff vs audit/check manifest** | PASS              | `audit.jsonl` 3 行 + `check.jsonl` 2 行路径均可解析；代码 diff 覆盖 ENTRY 声明触点                                                                                                                                    |
| **Trace / 原始任务卡**           | PARTIAL           | 活卡 §1–§7 scope/AC/Red Flags 已下沉 ENTRY §1–§2、`to-issues-slices.md`、ADR-033；**活卡正文 §5 AC 与 status 未回写**（A1-P2-002）                                                                                    |
| **Trace / task README·input**    | PASS              | `task.json` `plan_protocol_version: 4.1`；`execute_entry` → `00-EXECUTION-ENTRY.md`                                                                                                                                   |
| **Trace / unresolved coverage**  | PASS              | integration-audit doc-gap（clean e2e/registry）在 Execute 有代码或 explicit coordinator defer（`registry_proposed_delta.yaml`）                                                                                       |
| **Trace / round map**            | PASS              | Wave 4 G4 · P0 `US_EQ`；ENTRY §2「不在范围」与活卡 §6 一致（CN_A full、REQ2-EM、L3/L5）                                                                                                                               |
| **Trace / source-index**         | PASS              | ENTRY §5.1 登记 14 份 research/\*.md + `registry_proposed_delta.yaml`；`plan-consolidation.md` 机械自检一致                                                                                                           |
| **Trace / omission-check**       | FAIL              | INDEX §1 标 [x] 的 s08-01/03/04/05 证据文件缺失；INDEX 缺 audit-boot 要求的 §2.1 Tier                                                                                                                                 |
| **Trace / integration-ledger**   | PASS              | `integration-audit.md` PASS_WITH_GAPS 三项 Execute 缺口中 clean_read/e2e 已落地；registry apply 仍 coordinator（Plan 已定案）                                                                                         |
| **活卡 / ENTRY / ADR-033 一致**  | PASS              | P0 `US_EQ`、tier_a_clean、无 migration、REQ2-EM 不关、mootdx 双轨 primary — 三处一致                                                                                                                                  |
| **DOUBT / Red Flags 下沉**       | PASS              | REQ2-EM、参考项目 L 梯、`staged` 禁止冒充 — ENTRY §2 + `reference-adoption-dcp08.md` + `plan-doubt-review.md` Cycle 1–4                                                                                               |
| **GitNexus**                     | PARTIAL           | `query(repo=quant-monitor-desk, "Layer4 US_EQ tier_a_clean…")` 返回进程但未命中 `clean_read`/`USEquityCleanMarketAdapter`；`context(USEquityCleanMarketAdapter)` → **not found**（索引滞后，A1-P3-002）               |
| **validate-execute-handoff**     | PASS              | `python .trellis/scripts/task.py validate-execute-handoff …` exit 0（v4.1 仅验 frozen §9 [x]，**不**验 INDEX 所列 txt 路径）                                                                                          |

---

## §维度裁决

**FAIL**

（§计划内 4 行非占位 finding；GitNexus 索引滞后 1 行计划外。）

---

## 计划内问题

| ID        | P   | 标题                                  | 锚点                                                                                                    | 根因                                                                                                                                                                                                                       | 修复方案                                                                                                                                                                                          | 验证                                                                                                                               |
| --------- | --- | ------------------------------------- | ------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| A1-P1-001 | P1  | INDEX §1 证据路径虚假完成             | `EXECUTION_INDEX.md` L20–22；`to-issues-slices.md` L12；`00-EXECUTION-ENTRY.md` L50                     | §1 声明 `s08-01-{red,green}.txt`、`s08-03/04/05` 证据且标 `[x]`，但 `research/execute-evidence/` 仅存在 `s08-02-{red,green}`、`s08-06-{red,green}` 及 reg/close green；违反 slices「每片 RED→GREEN」与 ENTRY §3 证据链自述 | **二选一关账：** (a) 补全缺失 `s08-01/03/04/05` RED/GREEN txt；或 (b) 修订 INDEX §1 + ENTRY §3 + slices §2 明确 v4.1 code-first（删虚假路径/[x]），保留现有 s08-02/06 代表 READ/E2E 两片 TDD 证据 | `Get-ChildItem research/execute-evidence/` 列全文件；若走 (a) 每片 `validate-execute-step` 或手工确认 red 含 FAIL、green 含 passed |
| A1-P2-002 | P2  | 活卡 status/AC 未与 Execute 同步      | `docs/implementation_tasks/.../R3_DCP_08_LAYER4_MARKET_STRUCTURE.md` L11、L62–69；`frozen/...` §9 `[x]` | Execute 已完成（frozen §9.0–9.4 全 [x]、pytest 绿），但 Trace Authority 活卡仍 `OPEN · Plan 阶段`，§5 AC 全 `[ ]`                                                                                                          | S08-CLOSE 或 Audit Repair：更新活卡 status（如 IN_PROGRESS/DONE 按仓库惯例）、§5 AC 勾选与 frozen/ENTRY 对齐                                                                                      | 活卡 §5 勾选与 `uv run pytest tests/test_layer4_us_equity_clean_e2e.py -q` 绿一致                                                  |
| A1-P2-003 | P2  | INDEX 缺 §2.1 Tier 验证矩阵           | `EXECUTION_INDEX.md`（全文无 `## 2.1`）；`agents/audit-boot-v4.1.md` L60、L104                          | v4.1 Boot/Repair 引用 INDEX §2.1 最弱 pytest 行，本任务 Bundle 未登记                                                                                                                                                      | 在 INDEX §2 后补 §2.1（至少：`test_layer4_us_equity_clean_e2e.py` + `uv run pytest -q`）                                                                                                          | `rg "## 2\\.1" EXECUTION_INDEX.md` 有命中且命令可复跑 exit 0                                                                       |
| A1-P2-004 | P2  | 缺 gitnexus-audit-summary.md（7.pre） | `agents/audit-boot-v4.1.md` L36、L75；`research/` 目录 listing                                          | Audit 派发 A1–A8 前 Boot #15 要求 `gitnexus-audit-summary.md`，任务目录不存在                                                                                                                                              | A9 主会话在合并前运行 GitNexus `query`/`impact` 落盘 `research/gitnexus-audit-summary.md`                                                                                                         | `Test-Path research/gitnexus-audit-summary.md` 为真且含 Layer4 clean read 触点                                                     |

---

## 计划外发现

| ID        | P   | 标题                              | 锚点                                                                    | 根因                                                                                 | 修复方案                                                                                   | 验证                                                                                         |
| --------- | --- | --------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------- |
| A1-P3-001 | P3  | evidence_index.json 空壳          | `evidence_index.json` L2–3 `"execute": {}`, `"audit": {}`               | loop handoff 文件存在但未填 execute/audit 条目                                       | `uv run python scripts/loop_maintain.py --fix` 或按 loop 规范填入本任务证据路径            | `jq '.execute \| length' evidence_index.json` > 0                                            |
| A1-P3-002 | P3  | GitNexus 索引未收录新 Layer4 符号 | `backend/app/layer4_markets/clean_read.py` L136；ENTRY §2 GitNexus 铁律 | 新加 `USEquityCleanMarketAdapter` / `clean_read.py` 未 analyze；`context` 查无此符号 | 工作区根执行 `node .gitnexus/run.cjs analyze`（或 `npx gitnexus analyze`）后复验 `context` | `context({name:"USEquityCleanMarketAdapter", repo:"quant-monitor-desk"})` 返回定义与 callers |

已对抗搜索：`research/execute-evidence/` 全文件 listing；活卡 vs frozen vs ENTRY §1–§2 vs ADR-033 Decision 1–6；`integration-audit.md` doc-gap 三项；`reference-adoption-dcp08.md` L 梯与 `execute-reference-read-evidence-s08.md`；`rg "s08-0" .trellis/tasks/07-02-wave4-r3-dcp-08-layer4`；GitNexus `query` + `context`（repo=`quant-monitor-desk`）；`validate-execute-handoff` 与 v4.1 handoff 源码 `_validate_v41_handoff` 行为对照。
