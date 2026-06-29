# trellis-execute — 必做 skill 与相位（Execute SSOT）

> **条件 skill（触发才 Read）：** [`agent-toolchain.md`](../../agent-toolchain.md) §Execute — 条件 skill  
> **工程契约：** [project-global.mdc](../../rules/project-global.mdc) · [principles.md](principles.md)  
> **磁盘路径：** `.trellis/spec/guides/execute-skill-paths.yaml`

---

## 必做 — 相位总表

| Phase     | 必做 Read                                                                                         | 条件（触发则 Read · 见 agent-toolchain）                          |
| --------- | ------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| Boot      | `agent-toolchain` · `trellis-execute/SKILL.md` · `principles` · `project-global.mdc` · `impact()` | `grill-me` + **grill-gate** block                                 |
| RED       | **`/test-driven-development`** · `karpathy-guidelines` · `testing-guidelines`                     | —                                                                 |
| DEBUG     | —                                                                                                 | `systematic-debugging` → `diagnosing-bugs` → `gitnexus-debugging` |
| GREEN     | **`/test-driven-development`** · `karpathy-guidelines` · `testing-guidelines`                     | `source-driven-development` · `deprecation-and-migration`         |
| SLICE     | `incremental-implementation`                                                                      | `observability-and-instrumentation`                               |
| pre-merge | —                                                                                                 | `shipping-and-launch`（主会话）                                   |

**禁止：** `/implement` · `trellis-implement` 不 commit · 未走 RED/GREEN 勾 `[x]`

---

## 必做 — skill 路径（与 yaml 对齐）

| Skill                        | 相位        | 路径                                                   |
| ---------------------------- | ----------- | ------------------------------------------------------ |
| `/test-driven-development`   | RED / GREEN | `execute-skill-paths.yaml` → `test-driven-development` |
| `karpathy-guidelines`        | RED / GREEN | 见 yaml                                                |
| `testing-guidelines`         | RED / GREEN | `.cursor/skills/testing-guidelines/SKILL.md`           |
| `incremental-implementation` | SLICE       | 见 yaml                                                |
| `trellis-execute`            | Boot        | `.cursor/skills/trellis-execute/SKILL.md`              |
| `trellis-execute-principles` | Boot        | `.cursor/skills/trellis-execute/principles.md`         |
| `project-global`             | Boot        | `.cursor/rules/project-global.mdc`                     |
| `agent-toolchain`            | Boot        | `agent-toolchain.md`                                   |
| `gitnexus-impact`            | Boot        | MCP `impact()`（见 AGENTS.md）                         |

TDD 分轨 · karpathy/testing 步骤 → [principles.md](principles.md)。

---

## 条件 skill

**不在此文件展开** — 触发/完成条件见 [`agent-toolchain.md`](../../agent-toolchain.md) §Execute — 条件 skill（总表 + **细则**）。
