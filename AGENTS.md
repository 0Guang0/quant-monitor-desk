<!-- TRELLIS:START -->
# Trellis Instructions

These instructions are for AI assistants working in this project.

This project is managed by Trellis. The working knowledge you need lives under `.trellis/`:

- `.trellis/workflow.md` — development phases, when to create tasks, skill routing
- `.trellis/spec/` — package- and layer-scoped coding guidelines (read before writing code in a given layer)
- `.trellis/workspace/` — per-developer journals and session traces
- `.trellis/tasks/` — active and archived tasks (PRDs, research, jsonl context)

If a Trellis command is available on your platform (e.g. `/trellis:finish-work`, `/trellis:continue`), prefer it over manual steps. Not every platform exposes every command.

If you're using Codex or another agent-capable tool, additional project-scoped helpers may live in:
- `.agents/skills/` — reusable Trellis skills
- `.codex/agents/` — optional custom subagents

Managed by Trellis. Edits outside this block are preserved; edits inside may be overwritten by a future `trellis update`.

## Plan gate (complex tasks with `MASTER.plan.md`, `status=planning`)

When authoring or freezing a complex task plan:

1. **MUST Read first:** `.cursor/skills/trellis-plan/SKILL.md` — complete **Phase P0 Boot** (including **P0o** `docs/implementation_tasks/` original plan package) before MASTER §8–§12.
2. Follow **Phases 1a→5d** in `complex-task-planning-protocol.md` §4；append `research/plan-skill-reads.jsonl` per Read.
3. Produce `research/original-plan-trace.md` mapping `NNN_*.md` → MASTER §2 AC.
4. Before `task.py start`: `python .trellis/scripts/task.py validate-plan-freeze <task-dir>` exit 0.
5. Optional per phase: `python .trellis/scripts/task.py validate-plan-phase <task-dir> <phase>`.

## Execute gate (complex tasks with `MASTER.plan.md`)

When the active task status is `in_progress` and the task directory contains `MASTER.plan.md`:

1. **MUST Read first:** `.cursor/skills/trellis-execute/SKILL.md` — complete **Phase 0 Boot** before any business code.
2. Read **MASTER §0.1** state machine and **§12** Skill table (paths in `.trellis/spec/guides/execute-skill-paths.yaml`).
3. Execute **one §8.x step at a time**: Read TDD skill → RED (must FAIL) → `execute-evidence/{step}-red.txt` → GREEN → `{step}-green.txt` → `[x]`.
4. After each GREEN: Read **incremental-implementation**; full pytest must pass before next §8 step.
5. After RED, before GREEN implementation: Read **karpathy-guidelines** (§5 ladder + §1-4) and **testing-guidelines** (§12 + paths yaml).
6. Run GitNexus **`impact()`** before editing symbols; **`detect_changes()`** before commit.
7. Do **not** run `trellis-check` during Execute — Audit Phase 7 / A1 replaces it.
8. Optional per step: `python .trellis/scripts/task.py validate-execute-step <task-dir> 8.x`
9. Before §11 Audit handoff: `python .trellis/scripts/task.py validate-execute-handoff <task-dir>`.
10. Do **not** `finish-work` until Audit PASS.

<!-- TRELLIS:END -->

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **quant-monitor-desk** (3045 symbols, 4452 relationships, 67 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

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

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/quant-monitor-desk/context` | Codebase overview, check index freshness |
| `gitnexus://repo/quant-monitor-desk/clusters` | All functional areas |
| `gitnexus://repo/quant-monitor-desk/processes` | All execution flows |
| `gitnexus://repo/quant-monitor-desk/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
