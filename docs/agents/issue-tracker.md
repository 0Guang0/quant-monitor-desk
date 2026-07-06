# Issue tracker: GitHub + local markdown (dual)

Engineering skills (`to-issues`, `triage`, `to-prd`, `qa`) use **one workflow** that works in both places.

## Primary surfaces

| Surface            | Where                                                                   | Tooling                  |
| ------------------ | ----------------------------------------------------------------------- | ------------------------ |
| **GitHub**         | `https://github.com/0Guang0/quant-monitor-desk` issues (+ external PRs) | `gh` CLI                 |
| **Local markdown** | `.scratch/<feature-slug>/`                                              | read/write files in repo |

**Repo:** infer from `git remote -v` — `origin` → `0Guang0/quant-monitor-desk`.

## Dual-write convention

When a skill says **publish to the issue tracker**:

1. **Always** create/update the **local** artifact under `.scratch/<feature-slug>/` (create directory if needed).
2. **Also** create a **GitHub issue** (or comment/label on an existing one) with the same title/body and triage labels from `triage-labels.md`.
3. Cross-link: local issue file includes `GitHub: #<number>`; GitHub issue body includes `Local: .scratch/<feature-slug>/issues/<NN>-<slug>.md`.

When **fetching** a ticket: prefer the path or `#number` the user gave; if only one side exists, use that side.

## Local markdown layout

- One feature per directory: `.scratch/<feature-slug>/`
- PRD: `.scratch/<feature-slug>/PRD.md`
- Issues: `.scratch/<feature-slug>/issues/<NN>-<slug>.md` (numbered from `01`)
- Triage state: `Status:` line near top (use label strings from `triage-labels.md`)
- Thread: append under `## Comments`

## GitHub conventions

- **Create:** `gh issue create --title "..." --body "..."`
- **Read:** `gh issue view <number> --comments`
- **List:** `gh issue list` with `--label` / `--json` as needed
- **Labels:** `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **Close:** `gh issue close <number> --comment "..."`

## Pull requests as a triage surface

**PRs as a request surface: yes.**

External PRs use the **same triage labels** as issues (`triage-labels.md`).

- **Read PR:** `gh pr view <number> --comments` · `gh pr diff <number>`
- **List for triage:** `gh pr list --state open --json number,title,body,labels,author,authorAssociation,comments` — keep `authorAssociation` in `CONTRIBUTOR`, `FIRST_TIME_CONTRIBUTOR`, `NONE` (skip `OWNER`/`MEMBER`/`COLLABORATOR`).
- **Comment / label / close:** `gh pr comment`, `gh pr edit --add-label`/`--remove-label`, `gh pr close`

GitHub shares one number space for issues and PRs — resolve with `gh pr view N` then fall back to `gh issue view N`.

## Explicitly not the default tracker

| System                    | Path                         | Note                                                                                                  |
| ------------------------- | ---------------------------- | ----------------------------------------------------------------------------------------------------- |
| Module planning           | `docs/implementation_tasks/` | Thin task cards + `PROJECT_IMPLEMENTATION_ROADMAP.md` §3                                              |
| Implementation task cards | `docs/implementation_tasks/` | Planning SSOT (`PROJECT_IMPLEMENTATION_ROADMAP.md`); not auto-created by `to-issues` unless user asks |
