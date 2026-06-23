# Thinking Guides

> **Purpose**: Expand your thinking to catch things you might not have considered.

---

## Why Thinking Guides?

**Most bugs and tech debt come from "didn't think of that"**, not from lack of skill:

- Didn't think about what happens at layer boundaries → cross-layer bugs
- Didn't think about code patterns repeating → duplicated code everywhere
- Didn't think about edge cases → runtime errors
- Didn't think about future maintainers → unreadable code

These guides help you **ask the right questions before coding**.

---

## Available Guides

| Guide                                                                 | Purpose                                                                | When to Use                       |
| --------------------------------------------------------------------- | ---------------------------------------------------------------------- | --------------------------------- |
| [Complex Task Planning Protocol](./complex-task-planning-protocol.md) | Plan 流程（Execute **6** / Audit **7** / Repair **8** / Finish **9**） | Plan 启动                         |
| [MASTER 模板](./templates/MASTER.plan.md)                             | **Execute** 入口（§8 证据、§9 四层、§10 Tier）                         | 建任务                            |
| [**AUDIT 模板**](./templates/AUDIT.plan.md)                           | **Audit** 任务可变项（Trace + §1 覆写）                                | Plan 冻结                         |
| [audit.report 模板](./templates/audit.report.md)                      | Audit 产出 + §4.3 修复项                                               | Phase 7                           |
| [Repair 模板](./templates/REPAIR.plan.md)                             | Audit 后修复                                                           | PASS_WITH_FIXES                   |
| [repair-skill-registry.md](./repair-skill-registry.md)                | Repair 候选 Skill                                                      | 填 REPAIR.plan                    |
| [plan.freeze 模板](./templates/plan.freeze.md)                        | Plan 冻结自检 + **§3.0 双契约 one-pager**                              | start 前                          |
| [Execute Skill 词典](./execute-skill-registry.md)                     | 填 MASTER §12                                                          | Plan                              |
| [**Audit Skill 路径**](./audit-skill-paths.yaml)                      | A1–A8 派发 + skill 冻结                                                | Audit                             |
| [**Audit Skill 词典**](./audit-skill-registry.md)                     | 填 AUDIT **§2** 任务行                                                 | Plan                              |
| [Code Reuse Thinking Guide](./code-reuse-thinking-guide.md)           | Identify patterns and reduce duplication                               | When you notice repeated patterns |
| [Cross-Layer Thinking Guide](./cross-layer-thinking-guide.md)         | Think through data flow across layers                                  | Features spanning multiple layers |

---

## Quick Reference: Thinking Triggers

### When to Think About Cross-Layer Issues

- [ ] Feature touches 3+ layers (API, Service, Component, Database)
- [ ] Data format changes between layers
- [ ] Multiple consumers need the same data
- [ ] You're not sure where to put some logic
- [ ] You are adding an event kind, JSONL record, RPC payload, or config field
- [ ] UI / command code starts casting raw payload fields directly

→ Read [Cross-Layer Thinking Guide](./cross-layer-thinking-guide.md)

### When to Think About Code Reuse

- [ ] You're writing similar code to something that exists
- [ ] You see the same pattern repeated 3+ times
- [ ] You're adding a new field to multiple places
- [ ] **You're modifying any constant or config**
- [ ] **You're creating a new utility/helper function** ← Search first!
- [ ] Two files read the same untyped payload field with local casts
- [ ] Multiple branches update the same derived state from `kind` / `action`

→ Read [Code Reuse Thinking Guide](./code-reuse-thinking-guide.md)

### When Verifying AI Cross-Review Results

- [ ] Reviewer claims "user input can be malicious" → Check the actual data source (internal manifest? user config? external API?)
- [ ] Reviewer flags "missing validation" → Is the data from a trusted internal source?
- [ ] Reviewer says "behavior change" → Read the code comments — is it intentional design?
- [ ] Reviewer identifies a "bug" in test → Mentally delete the feature being tested — does the test still pass? If yes → tautological test

**Common AI reviewer false-positive patterns**:

1. **Trust boundary confusion**: Treating internal data (bundled JSON manifests) as untrusted external input
2. **Ignoring design comments**: Flagging intentional behavior documented in code comments as bugs
3. **Variable misreading**: Not tracing a variable to its actual definition (e.g., Map keyed by path vs name)

**Verification rule**: Every CRITICAL/WARNING finding must be verified against the actual code before prioritizing. Budget ~35% false-positive rate for AI reviews.

---

## Pre-Modification Rule (CRITICAL)

> **Before changing ANY value, ALWAYS search first!**

```bash
# Search for the value you're about to change
grep -r "value_to_change" .
```

This single habit prevents most "forgot to update X" bugs.

---

## How to Use This Directory

1. **Before coding**: Skim the relevant thinking guide
2. **During coding**: If something feels repetitive or complex, check the guides
3. **After bugs**: Add new insights to the relevant guide (learn from mistakes)

---

## Contributing

Found a new "didn't think of that" moment? Add it to the relevant guide.

---

**Core Principle**: 30 minutes of thinking saves 3 hours of debugging.
