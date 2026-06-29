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

## Plan gate (complex tasks: v4/v4.1 `EXECUTION_INDEX` + frozen card)

When authoring or freezing a complex task plan (`status=planning`):

**Protocol v4 / v4.1** (`EXECUTION_INDEX.md` + `frozen/*.md`; v4.1 adds `research/00-EXECUTION-ENTRY.md`):

1. **MUST Read first:** `agent-toolchain.md`（根目录）+ `.cursor/skills/trellis-plan/SKILL.md` — complete **Phase P0 Boot** (including **P0o** `docs/implementation_tasks/`).
2. Follow **Phases 1a→5d** in `complex-task-planning-protocol.md` §4；`EXECUTION_INDEX.md` 为唯一人工索引（§1 步骤、§2 AC、§3 manifest）。
3. Produce `research/original-plan-trace.md` mapping `NNN_*.md` → `EXECUTION_INDEX` §2 AC.
4. Before `task.py start`: `python .trellis/scripts/task.py validate-plan-freeze <task-dir>` exit 0.
5. Optional per phase: `python .trellis/scripts/task.py validate-plan-phase <task-dir> <phase>`.

**Legacy v3**（仅 `tasks/archive/` 只读，或 `in_progress` + `plan_protocol_version: "3"` 在途 shim）:

1. 新任务 **不得** 新建 `MASTER.plan.md`；须迁移 v4 或移入 `tasks/archive/`。
2. 在途 v3：`validate-plan-freeze` 拒绝；`validate-execute-handoff` 允许 legacy shim。
3. 归档 v3：`validate-plan-freeze` / `validate-plan-phase` / handoff **全跳过**（只读）。

## Execute gate (complex tasks in progress)

When the active task status is `in_progress`:

**Protocol v4 / v4.1** — SSOT: `frozen/*.md` + `implement.jsonl` (slot 1 = frozen; slot 2 = ENTRY or INDEX):

1. **MUST Read first:** `agent-toolchain.md` + `.cursor/skills/trellis-execute/SKILL.md` + `principles.md` — Phase 0 Boot.
2. **MUST Read `implement.jsonl` every line**; do not skip by summarizing the frozen task card.
3. Read frozen card §9 / `EXECUTION_INDEX` §1 state machine; skill table in `execute-skill-paths.yaml`.
4. Execute **one §9.x step at a time**: `test-driven-development` RED → `execute-evidence/{step}-red.txt` → GREEN → `{step}-green.txt` → SLICE (`incremental-implementation`) → `[x]`.

**Legacy v3**（`in_progress` + `MASTER.plan.md` only）:

1. Same boot; **MUST Read `implement.jsonl` every line** + MASTER §0.1 / §12.
2. Execute **one §8.x step at a time** (evidence paths as MASTER §8).
3. Optional: `validate-execute-step <task-dir> 8.x`
4. Before Audit: `validate-execute-handoff`; no `finish-work` until Audit PASS.

## Audit gate (complex tasks with `AUDIT.plan.md`)

1. **MUST Read first:** `agent-toolchain.md`（根目录）+ `.trellis/spec/guides/audit-skill-paths.yaml` + 任务 `AUDIT.plan.md` + `audit.jsonl`.
2. 按 `audit-skill-paths.yaml` 派发 A1–A8；各维读 `agents/` 对应模板（skill 另 Read；派发者指定 model）。
3. 产出 `audit.report.md`；PASS 前勿 `finish-work`。

## Loop engineering context (Trellis complex-task layer)

Complex tasks (`meta.task_track: "complex"`, or v4 `EXECUTION_INDEX.md`+`frozen/`) use machine-readable routing — **do not ask the user for docs/specs paths**.

1. Plan freeze: `validate-plan-freeze` auto-runs `context_router` if `context_pack.json` missing
2. Execute: **MUST Read `implement.jsonl` every line** before business code (`task.py current` → task dir); v4.1 slot 2 = `research/00-EXECUTION-ENTRY.md`; slot 3 = `context_pack.json`
3. Handoff gates: `validate-execute-handoff` → `check_task_evidence.py`
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
