# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Layout

**Single-context** — one glossary at the repo root + system-wide ADRs.

```
/
├── CONTEXT.md          ← domain glossary (create lazily if missing)
├── docs/adr/           ← architectural decisions (exists)
├── docs/modules/       ← module design authority
├── specs/              ← contracts and registries
└── PROJECT_IMPLEMENTATION_ROADMAP.md  ← live planning SSOT
```

## Before exploring, read these

- **`CONTEXT.md`** at the repo root when it exists.
- **`docs/adr/`** — read ADRs that touch the area you're about to work in.
- For QMD-specific module scope: `docs/modules/*.md`, `MODULE_COMPLETION_RATING.md`, `PROJECT_IMPLEMENTATION_ROADMAP.md` §3.

If `CONTEXT.md` does not exist yet, **proceed silently**. Don't flag its absence or insist on creating it upfront. The `/domain-modeling` skill creates it lazily when terms or decisions get resolved.

## Use the glossary's vocabulary

When output names a domain concept (issue title, refactor proposal, test name), use terms as defined in `CONTEXT.md` once it exists. Until then, prefer terms from `docs/modules/` and `specs/contracts/`.

## Flag ADR conflicts

If output contradicts an existing ADR under `docs/adr/`, surface it explicitly:

> _Contradicts ADR-0002 (agent-readonly-boundary) — but worth reopening because…_
