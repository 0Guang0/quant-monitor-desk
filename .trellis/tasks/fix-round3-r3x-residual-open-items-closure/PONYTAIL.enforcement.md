# PROMPT_15 — Ponytail enforcement (coordinator mandatory)

**Mode:** `/ponytail` **full** — active for all remaining work on this branch.

## Ladder (every checklist item)

1. Need to exist at all? (YAGNI)
2. Stdlib / existing project utility?
3. Native platform / contract / DB constraint?
4. Installed dependency already covers it?
5. One line?
6. Minimum code that works.

## Rules

- No interface-with-one-impl, factory-for-one-product, config for static values.
- Shortest diff wins; refactor down over-built code already in this branch.
- `// ponytail:` / `# ponytail:` only when naming a deliberate ceiling + upgrade path.
- One small test per non-trivial fix group — no fixture forests.
- Do NOT ponytail away: validation at trust boundaries, data-loss prevention, security, Master Checklist explicit fixes.

## Deliverable note

`merge_gate_report.md` must state ponytail compliance per fix area.
