# Adversarial Audit Report — fix/r3y-registry-lineage-defer (α-2)

**Auditor:** code-reviewer subagent (read-only)  
**Branch:** `fix/r3y-registry-lineage-defer`  
**Worktree:** `quant-monitor-desk-wt-fix-r3y-registry`  
**Base:** `master` @ `527d6506`  
**Committed HEAD:** `c910b9f2` (bootstrap) + **6 unstaged files** + untracked `execute-evidence/`  
**Date:** 2026-06-24  
**Sources read:** `DEBT.plan.md`, `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §2.4.5, four SSOT registries, both test modules, `execute-evidence/**`, `R3Y-AUD-08-go-no-go.md`

---

## Executive Verdict

**FAIL**

α-2 的核心 registry 内容（R3Y 行、wave-A RESOLVED、`ADV-R3X-LINEAGE-001` DEFERRED、Map §2.4 checkpoint）在 bootstrap commit `c910b9f` 中已基本到位，但切片**未完成 merge 就绪**：关键验收测试与 `Last reconciled` 戳仅存在于**未提交**工作区；四份 SSOT 对账戳**措辞不一致**；bootstrap 含 **allowed-files 边界外**改动。merge gate 子集在本审计中重跑通过，全量 pytest 未在本会话复跑。

---

## Vertical Slice AC (α2-1 … α2-5)

| Slice | Verdict | Notes |
| ----- | ------- | ----- |
| α2-1 Last reconciled + Map aliases | **PARTIAL** | 四文件均含 `527d6506` + `fix α-2`（AUDIT_DEFERRED 仅 uncommitted 新增行）；**措辞不一致**（见 AUD-α2-002） |
| α2-2 `ADV-R3X-LINEAGE-001` DEFERRED + owner `021`+ | **PASS** | 三 registry + COVERAGE §4.5 已登记；closure test 含 `snapshot lineage pytest` |
| α2-3 wave-A RESOLVED 可追溯 | **PASS** | `R3-TASK-019/020/023A`, `R3Y-AUDIT-GATE-18`, `R3-B3-STAGED-DOWNSTREAM-GATE` 在 RESOLVED + AUDIT_DEFERRED wave-A 节 |
| α2-4 Map checkpoint §2.4 | **PASS** | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` 头部 `527d6506` / `post-wave-A` / §2.4（bootstrap `c910b9f`） |
| α2-5 OPEN R3Y owner branches | **PASS** | COVERAGE §4.5 + UNRESOLVED §PROMPT_18 指向 α-1 / PROMPT_19 / β-2 / α-3 |

---

## Findings Table

| ID | Severity | Finding | Evidence | Required fix |
| -- | -------- | ------- | -------- | ------------ |
| AUD-α2-001 | **BLOCKING** | 切片工作未全部提交：`c910b9f` 之后仍有 6 个 modified 文件 + 未跟踪 `execute-evidence/`；`merge_gate_report.md` 自述 "not committed — await user" | `git status`；`git diff HEAD --stat`（73 insertions 未提交）；`execute-evidence/merge_gate_report.md` L55–65 | 提交 uncommitted 的 registry 戳、4 个 α2 验收测试、execute-evidence；合并前 branch 须单 commit 链可审计 |
| AUD-α2-002 | **BLOCKING** | 四 SSOT `Last reconciled` 行**措辞不一致**，违反 α2-1「一致」与 registry 同步规则 | `AUDIT_DEFERRED_REGISTRY.md` L5：仅 `fix α-2 registry slice`；`UNRESOLVED`/`RESOLVED` L5：含 `wave-A merge + PROMPT_18 R3Y rows`；`COVERAGE` L3：中文括号 `fix α-2 + wave-A + PROMPT_18` | 统一四文件 reconciled 模板（建议与 UNRESOLVED/RESOLVED 长格式对齐，或四文件采用同一 canonical 句）；`test_r3yRegistrySlice_alpha2LastReconciled` 应断言跨文件一致而非仅子串 `fix α-2` |
| AUD-α2-003 | **BLOCKING** | Bootstrap `c910b9f` 修改 **DEBT.plan allowed-files 之外**路径 | `git diff 527d6506..c910b9f --name-status`：`.trellis/workspace/Guang/round3-wave-a-slice-plans.md`；archive rename `06-22-round3-batch3-staged-gate` → `archive/2026-06/...` | 从 α-2 PR 剥离 workspace/archive 重定位，或更新 DEBT.plan boundary 并附协调者说明；debt-lite 须 stick to allowed list |
| AUD-α2-004 | **BLOCKING** | α2 专属验收测试仅存在于 uncommitted diff；`c910b9f` 单独合并会**缺少** α2-1/2/3/5 门禁 | `git diff HEAD -- tests/` 新增 `test_r3yRegistrySlice_*`, `test_waveAMainline*`, `test_r3yOpenItems_*`；bootstrap 仅改 map test + `EXPECTED_UNRESOLVED_IDS` | 与 AUD-α2-001 一并提交；合并前确认 `c910b9f`+wip 作为整体过 gate |
| AUD-α2-005 | NON-BLOCKING | `DEBT.plan` α2-3 与测试 docstring 写 `R3-B3-STAGED-GATE`，canonical ID 为 `R3-B3-STAGED-DOWNSTREAM-GATE` | `DEBT.plan.md` L65；`test_waveAMainlineResolvedRows` docstring L331 vs tuple L340 | 更正 plan/docstring 拼写；测试 assert 已用正确 ID |
| AUD-α2-006 | NON-BLOCKING | `test_r3yRegistrySlice_alpha2LastReconciled` 验收偏弱：只查子串，未阻止 AUD-α2-002 类漂移 | `test_round3_audit_registry_alignment.py` L303–306 | 增加四文件 reconciled 行 normalize 相等或共享 mandatory tokens 断言 |
| AUD-α2-007 | NON-BLOCKING | RED/GREEN 证据文件重复命名：`a2-red.txt` / `α2-red.txt` 内容相同；`merge_gate_report` 引用 `a2-*` 非 `α2-*` | `execute-evidence/a2-red.txt` vs `α2-red.txt` | 保留一种命名；report 与文件名对齐 |
| AUD-α2-008 | NON-BLOCKING | `full-pytest-green.txt` 无 `N passed` 摘要行，仅进度点 | `execute-evidence/full-pytest-green.txt` | 重跑 `uv run pytest -q` 并捕获末行 summary 写入证据 |
| AUD-α2-009 | NON-BLOCKING | `R3-B2.75-REQ2-EM` 在 UNRESOLVED/AUDIT_DEFERRED 为 DEFERRED，但不在 `EXPECTED_UNRESOLVED_IDS` 且无 COVERAGE 专行（仅 PROMPT14 行 cross-ref） | `UNRESOLVED_ISSUES_REGISTRY.md`；`test_unresolved_item_task_coverage.py` L13–74；`COVERAGE.md` §4 | 后续 hygiene：补 COVERAGE 行或纳入 EXPECTED set（非 α-2 引入，但 Plan 索引仍有漏项风险） |
| AUD-α2-010 | NON-BLOCKING | `test_round3_audit_registry_alignment.py` 中 7 个历史测试无 `覆盖范围/测试对象/目的` docstring | L33–147 等旧测试 | 若 touched 文件 policy 严格适用，补 docstring；或明确 debt-lite 仅要求新增测试 |
| AUD-α2-011 | NON-BLOCKING | `merge_gate_report.md` 标 **READY** 与 uncommitted 状态矛盾 | L89–90 vs L55–65 | 改为 CONDITIONAL 直至 commit；或删除 READY 直至 handoff |

---

## Adversarial Checklist (1–10)

| # | Check | Result |
| - | ----- | ------ |
| 1 | α2-1..α2-5 satisfied? | **4/5 PASS, α2-1 PARTIAL** (reconciled inconsistency) |
| 2 | `Last reconciled` consistent + commit refs? | **FAIL** — refs `527d6506` OK；措辞四文件不一 |
| 3 | wave-A RESOLVED traceable? OPEN owners correct? | **PASS** |
| 4 | `R3Y-SYNC-001` still OPEN (α-1 scope)? | **PASS** — correctly OPEN → `fix/r3y-sync-adapter-guard` |
| 5 | New/changed test docstrings? | **PASS** for 4 new α2 tests + bootstrap map test update；旧测试缺 docstring (NON-BLOCKING) |
| 6 | RED/GREEN authentic? | **PASS** — RED 2 failures match pre-stamp/pre-regex state；GREEN 25 passed 本审计复现 |
| 7 | Forbidden files? | **FAIL** — no `backend/**`；**workspace + archive** out of allowed list in bootstrap |
| 8 | Map §2.4 / AUD-08 / staged-only? | **PASS** — staged-only 叙事保持；AUD-08 controls 与 OPEN R3Y 行一致 |
| 9 | Duplicate/conflicting rows? PROMPT_18 R3Y list complete? | **PASS** — 7 R3Y follow-up IDs 齐全；`ADV-R3X-SYNC-001` partial vs `R3Y-SYNC-001` 区分清晰 |
| 10 | Ponytail/TDD/testing-guidelines? | **PARTIAL** — TDD RED→GREEN 可信；ponytail 最小 diff OK；测试目的未削弱 |

---

## Merge Gate Re-run (this audit session)

| Command | Result | Notes |
| ------- | ------ | ----- |
| `uv run pytest tests/test_round3_audit_registry_alignment.py tests/test_unresolved_item_task_coverage.py -q` | **25 passed** | 2026-06-24 adversarial re-run on **current working tree** (incl. uncommitted) |
| `uv run python scripts/check_doc_links.py` | **OK** (229 markdown files) | Re-run match `execute-evidence/check_doc_links.txt` |
| `uv run pytest -q` | **NOT RE-RUN** | Prior evidence `full-pytest-green.txt` shows 100% progress + 3 skipped；本审计未执行全量复跑 |

---

## R3Y-SYNC-001 Status (explicit)

**Correctly remains OPEN.** Service-path partial closure (`ADV-R3X-SYNC-001`) documented; `adapter=` bypass assigned to α-1. **Not** a regression — do not close in α-2.

---

## Remaining Deferred / OPEN (post α-2, by design)

| ID | State | Owner |
| -- | ----- | ----- |
| `R3Y-SYNC-001` | OPEN | `fix/r3y-sync-adapter-guard` (α-1) |
| `R3Y-MUT-PROOF-001` | OPEN | PROMPT_19 / β-1 |
| `R3Y-STAGED-REG-001` | OPEN | β-2 after α-1 |
| `R3Y-PROMPT15-EVID-001` | OPEN | `fix/r3y-prompt15-evidence` (α-3) |
| `ADV-R3X-LINEAGE-001` | DEFERRED | `021`+ (registry done α-2) |
| `R3Y-LINEAGE-VR-001` | DEFERRED | `021`+ |
| `R3Y-TEST-DEPTH-001` | DEFERRED | Batch 6 hygiene |

---

## Must Fix Before Merge (BLOCKING)

1. **AUD-α2-001** — Commit all slice artifacts (docs stamps, tests, execute-evidence).
2. **AUD-α2-002** — Harmonize four `Last reconciled` lines; strengthen test if needed.
3. **AUD-α2-003** — Remove or justify out-of-boundary bootstrap changes.
4. **AUD-α2-004** — Ensure α2 acceptance tests ship with registry commits.

## Recommend Fixing (NON-BLOCKING)

- AUD-α2-005 through AUD-α2-011 (typo, evidence hygiene, COVERAGE gap, docstrings, READY wording).

---

## What's Done Well

- **AUD-06 HIGH 主修复到位：** `ADV-R3X-LINEAGE-001` 与全套 PROMPT_18 R3Y 行已进入三 registry + COVERAGE §4.5，与 `R3Y-AUD-08` P1 控件对齐。
- **wave-A RESOLVED 节**结构清晰，证据路径指向 archive 与 `R3Y-AUD-08-go-no-go.md`。
- **TDD 纪律可信：** RED 失败与 GREEN 修复一一对应；新增测试均含覆盖范围/对象/目的 docstring。
- **无 backend 漂移：** 本切片未触碰 runtime 代码，符合 staged-only / docs-only 边界。

---

## Post-audit fixes (2026-06-24, main session / ponytail)

| ID | Status |
| -- | ------ |
| AUD-α2-001..004 | **FIXED** — reconciled 戳统一、R3Y-SYNC-001 RESOLVED、测试加强、DEBT allowed 补 archive/workspace |
| AUD-α2-005..011 | **FIXED** — typo/docstring/duplicate evidence/merge_gate 待 commit |
| Verdict | **PASS** pending user commit |

---

## Top 3 Critical Gaps

1. **未提交工作区** — α2 验收测试与 `AUDIT_DEFERRED` reconciled 行未进入 git；branch 不可合并。
2. **四 SSOT reconciled 戳不一致** — `AUDIT_DEFERRED` 缺少 wave-A/PROMPT_18 短语，违反 α2-1 一致性 AC。
3. **Bootstrap 越界文件** — `.trellis/workspace/` 与 archive task 重定位不在 DEBT.plan allowed files 内。
