<!-- TRELLIS:START -->

# Trellis Instructions

These instructions are for AI assistants working in this project.

This project is managed by Trellis. The working knowledge you need lives under `.trellis/`:

- **`agent-toolchain.md`**（仓库根目录）— 全员场景工具路由；歧义消解
- **角色必做表：** `plan-skill-paths.yaml` · `execute-skill-paths.yaml` · `audit-skill-paths.yaml`（均在 `.trellis/spec/guides/`）
- `.trellis/workflow.md` — development phases, when to create tasks, skill routing
- `.trellis/spec/` — package- and layer-scoped coding guidelines (read before writing code in a given layer)
- `.trellis/workspace/` — per-developer journals and session traces
- `.trellis/tasks/` — active and archived tasks (PRDs, research, jsonl context)
- **`agents/`**（项目根）— 可派发子 agent 模板；`_upstream/` 为 VoltAgent 原文
- `.trellis/agents/` — 仅 Trellis channel：`check.md`、`implement.md`

If a Trellis command is available on your platform (e.g. `/trellis:finish-work`, `/trellis:continue`), prefer it over manual steps. Not every platform exposes every command.

If you're using Codex or another agent-capable tool, additional project-scoped helpers may live in:

- `.agents/skills/` — reusable Trellis skills
- `.codex/agents/` — optional custom subagents

Managed by Trellis. Edits outside this block are preserved; edits inside may be overwritten by a future `trellis update`.

## Plan gate (complex tasks · v4.1 only)

When authoring or freezing a complex task plan (`status=planning`):

1. **MUST Read first:** `agent-toolchain.md` + `.cursor/skills/trellis-plan/SKILL.md` — complete **Phase P0 Boot** (including **P0o** `docs/implementation_tasks/`).
2. Follow **Phases 1a→5e** in `complex-task-planning-protocol.md` §4.
3. Set `meta.plan_protocol_version: "4.1"` · `meta.execute_entry` → ENTRY.
4. Before `task.py start`: `validate-plan-freeze` exit 0 · `plan.freeze.md` §3 全勾。

**Legacy v3/v4.0** — 只读 `templates/plan.freeze.legacy-v3-v40.md` · `tasks/archive/`；**不得**新建活跃 MASTER。

## Execute gate (complex tasks · v4.1)

When the active task status is `in_progress`:

1. **MUST Read first:** `agent-toolchain.md` + `.cursor/skills/trellis-execute/SKILL.md` + **`reference.md`** + `principles.md` + **`project-global.mdc`** — Phase 0 Boot.
2. **读清 Execution Bundle：** ENTRY（路由地图）+ §5.1 全部 `research/*` + 路由表（`EXTERNAL-INDEX.md` §A + `implement.jsonl` 每一行）+ 当前切片 §。
3. **直接执行：** INDEX §1 逐步 · **必做** Read `/test-driven-development`（见 `reference.md`）→ 代码/测试 → `[x]`；**条件 skill** 见 `agent-toolchain.md` §Execute（总表 + 细则）；**不**写 handoff 长文、txt、jsonl。
4. **收尾：** 对抗性自检（发现缺口先修，不落盘表）→ `validate-execute-handoff` → 交 Audit（勿 `finish-work` 直到 Audit PASS）。

**Legacy v3** — `MASTER.plan.md` only · 见上 Plan gate legacy 说明。

## Audit gate (complex tasks with `AUDIT.plan.md` · v4.1)

1. **MUST Read first:** `agent-toolchain.md` + `agents/audit-boot-v4.1.md` + `agents/audit-coverage-model.md` + `.trellis/spec/guides/audit-skill-paths.yaml` + 任务 `AUDIT.plan.md` + `audit.jsonl` + ENTRY + §5.1 全部 `research/*` + INDEX §3/§5 相关行。
2. **文档仅建上下文**；验证 **只信代码 + 跑测 + 独立复验**，不信任何文档自述。
3. 确认 `meta.plan_protocol_version: "4.1"`；7.pre → `gitnexus-audit-summary.md` 后再派发 A1–A8。
4. 按 `audit-skill-paths.yaml` 派发 A1–A8；各维读 `agents/` 对应模板 + `agents/audit-finding-schema.md`.
5. 产出 `audit.report.md` + 各维 `research/audit-a{n}-report.md`；PASS 前勿 `finish-work`。

## Repair gate (Audit FAIL · v4.1)

1. **MUST Read first:** `agents/repair-boot-v4.1.md` + `REPAIR.plan.md` + `research/audit-repair-ledger.md`.
2. 修根因；ledger 每项 disposition ∈ {已修复, 阶段外置}（`project-global.mdc` §无遗留）。
3. 收尾复验：**INDEX §2.1** + `uv run pytest -q` exit 0 → 更新 audit.report §5。

## Loop engineering context (Trellis complex-task layer)

Complex tasks (`meta.task_track: "complex"`, or v4 `EXECUTION_INDEX.md`+`frozen/`) use machine-readable routing — **do not ask the user for docs/specs paths**.

1. Plan freeze: `validate-plan-freeze` auto-runs `context_router` if `context_pack.json` missing
2. Execute (v4.1): Boot 读 ENTRY + research + 路由表（§A + `implement.jsonl` 每行）→ `/test-driven-development` per slice → 代码/测试即证据；**不写** txt/jsonl
3. Handoff gates: `validate-execute-handoff`（v4.1：`[x]` + complex 时 `context_pack.json` · `loop_manifest.json` · `evidence_index.json` · `check_task_evidence`；legacy：仍验 txt）
4. Repo CI: `check_test_catalog.py`, `check_verification_matrix.py`, `check_docs_specs_indexed.py`, `generate_project_map.py --check`, `check_active_master_tasks.py`
5. `debt-lite` / simple tasks: set `meta.task_track: "debt-lite"` or `"simple"` — loop not required
6. **New test module:** `uv run python scripts/loop_maintain.py --fix` (or `check_test_catalog.py --write-defaults`)
7. **New docs/specs file:** same `loop_maintain.py --fix` (refreshes `docs/generated/docs_specs_index.generated.md`)
8. **New backend package:** extend `specs/context/authority_graph.yaml` — `loop_maintain.py` reports unmapped `backend/app/*`
9. **Before commit** (when touching `backend/`, `docs/`, `specs/`, or `authority_graph.yaml`): run `uv run python scripts/loop_maintain.py` (check) or `--fix` to refresh project map + docs index; CI enforces the same

See `docs/quality/LOOP_ENGINEERING_TASK_FLOW_REFACTOR_PLAN.md` and `docs/ops/user_intervention_policy.md`.

<!-- TRELLIS:END -->

## Repair/Debt Lite Worktree Protocol

When a user asks to close already-audited findings, registry debt, or repair follow-ups, do not restart the full complex Plan by default. First check `.trellis/spec/guides/complex-task-planning-protocol.md` Phase 8D.

Use Repair/Debt Lite only when the item already has an audit/registry source of truth, can be sliced independently, does not add schema/public API/new production source behavior, and does not require production DB writes. The main session must produce a lightweight slice plan with owner, base branch, target branch, allowed files, forbidden files, verification, evidence path, and merge gate before implementation or worktree creation.

For parallel agents: one worktree per agent, one branch per slice or tightly related slice group, and no two active branches may own the same core file group. Registry files should normally be reconciled by a merge coordinator rather than edited concurrently by many agents.

<!-- gitnexus:start -->

# GitNexus — Code Intelligence

This project is indexed by GitNexus as **quant-monitor-desk** (6263 symbols, 10281 relationships, 276 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> Index stale? Run `node .gitnexus/run.cjs analyze` from the project root — it auto-selects an available runner. No `.gitnexus/run.cjs` yet? `npx gitnexus analyze` (npm 11 crash → `npm i -g gitnexus`; #1939).

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows. For regression review, compare against the default branch: `detect_changes({scope: "compare", base_ref: "master"})`.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `rename` which understands the call graph.
- NEVER commit changes without running `detect_changes()` to check affected scope.

## Resources

| Resource                                            | Use for                                  |
| --------------------------------------------------- | ---------------------------------------- |
| `gitnexus://repo/quant-monitor-desk/context`        | Codebase overview, check index freshness |
| `gitnexus://repo/quant-monitor-desk/clusters`       | All functional areas                     |
| `gitnexus://repo/quant-monitor-desk/processes`      | All execution flows                      |
| `gitnexus://repo/quant-monitor-desk/process/{name}` | Step-by-step execution trace             |

## CLI

| Task                                         | Read this skill file                                        |
| -------------------------------------------- | ----------------------------------------------------------- |
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md`       |
| Blast radius / "What breaks if I change X?"  | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?"             | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md`       |
| Rename / extract / split / refactor          | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md`     |
| Tools, resources, schema reference           | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md`           |
| Index, status, clean, wiki CLI commands      | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md`             |

<!-- gitnexus:end -->
