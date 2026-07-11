# Create Skill — Reference

Rules and workflow: [SKILL.md](SKILL.md). Illustrations and path tables only.

## Storage locations

| Type                | Path                                    | Scope                                                  |
| ------------------- | --------------------------------------- | ------------------------------------------------------ |
| Personal (OpenCode) | `~/.config/opencode/skills/skill-name/` | All OpenCode projects                                  |
| Personal (shared)   | `~/.agents/skills/skill-name/`          | Codex, Copilot CLI, Gemini CLI; Cursor also scans      |
| Personal (Cursor)   | `~/.cursor/skills/skill-name/`          | All Cursor projects (optional; `.agents` often enough) |
| Project (OpenCode)  | `.opencode/skills/skill-name/`          | This repo in OpenCode                                  |
| Project (shared)    | `.agents/skills/skill-name/`            | This repo on agents-capable hosts                      |
| Project (Cursor)    | `.cursor/skills/skill-name/`            | This repo in Cursor                                    |

**Never** create skills in host-bundled dirs — e.g. Cursor `~/.cursor/skills-cursor/`, `node_modules/.../skills/`.

When you use **both** OpenCode and Codex/Cursor, duplicate the same skill to `~/.config/opencode/skills/` and `~/.agents/skills/` so both hosts discover it.

## Complete example

**Directory structure:**

```
code-review/
├── SKILL.md
├── STANDARDS.md
└── examples.md
```

**SKILL.md:**

```markdown
---
name: code-review
description: Review code for quality, security, and maintainability following team standards. Use when reviewing pull requests, examining code changes, or when the user asks for a code review.
---

# Code Review

## Quick Start

When reviewing code:

1. Check for correctness and potential bugs
2. Verify security best practices
3. Assess code readability and maintainability
4. Ensure tests are adequate

## Review Checklist

- [ ] Logic is correct and handles edge cases
- [ ] No security vulnerabilities (SQL injection, XSS, etc.)
- [ ] Code follows project style conventions
- [ ] Functions are appropriately sized and focused
- [ ] Error handling is comprehensive
- [ ] Tests cover the changes

## Providing Feedback

Format feedback as:

- 🔴 **Critical**: Must fix before merge
- 🟡 **Suggestion**: Consider improving
- 🟢 **Nice to have**: Optional enhancement

## Additional Resources

- For detailed coding standards, see [STANDARDS.md](STANDARDS.md)
- For example reviews, see [examples.md](examples.md)
```
