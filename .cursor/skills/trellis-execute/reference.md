# trellis-execute — 条件 skill

> [principles.md](principles.md) · [SKILL.md](SKILL.md) · 路径：`.trellis/spec/guides/execute-skill-paths.yaml`

## 相位总表

| Phase     | 必做 Read                                                                | 条件（触发则必 Read）                                                            |
| --------- | ------------------------------------------------------------------------ | -------------------------------------------------------------------------------- |
| Boot      | `agent-toolchain` · `trellis-execute` · `principles` · `impact()`        | `grill-me` + **[grill-gate](../../../.trellis/spec/guides/grill-gate.md) block** |
| RED       | `test-driven-development` · `karpathy-guidelines` · `testing-guidelines` | —                                                                                |
| DEBUG     | —                                                                        | `systematic-debugging` → `diagnosing-bugs` → `gitnexus-debugging`                |
| GREEN     | `karpathy-guidelines` · `testing-guidelines`                             | `source-driven-development` · `deprecation-and-migration`                        |
| SLICE     | `incremental-implementation`                                             | `observability-and-instrumentation`                                              |
| pre-merge | —                                                                        | `shipping-and-launch`（主会话）                                                  |

**`/implement` 禁止** · **`incremental-implementation` SLICE 必做** · **`trellis-implement` 子 agent 不 commit**（见 SKILL.md）

---

## DEBUG

**触发：** RED 意外 PASS · GREEN 后仍 FAIL · 同错修 ≥2 轮 · 栈与 INDEX 不符

**顺序：** `systematic-debugging` → `diagnosing-bugs` → `gitnexus-debugging` → 回到 RED

**完成条件：** 根因已写明；`execute-skill-reads.jsonl` 含已 Read 的 DEBUG skill。

---

## source-driven-development

**GREEN 前 Read：** 外部 API/契约/SDK 语义；`specs/contracts` 新字段；adapter 与第三方对齐。

**不必：** 纯内部 refactor、仅改测试/注释。

**完成条件：** 实现或 `-green.txt` 含可追溯文档引用。

---

## deprecation-and-migration

**GREEN 前 Read：** deprecate/remove/rename/migrate/双轨；public API 破坏性变更；registry tombstone。

**完成条件：** 旧路径显式可用或失败关闭；green 证据写迁移步骤。

---

## observability-and-instrumentation

**SLICE 前 Read：** ops/写路径/pipeline；AC 要求 log/metric/trace；`backend/app/ops/` 等。

**完成条件：** 变更路径有可检索信号；无无引用全局指标。

---

## shipping-and-launch (pre-merge)

主会话；handoff 绿 + Audit PASS 后、merge/PR 前可选。**不替代** handoff 与 Audit。
