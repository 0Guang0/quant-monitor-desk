# Repair/Debt Lite Plan — fix/r3y-registry-lineage-defer (α-2)

## Source of truth

| 项            | 值                                                                                                         |
| ------------- | ---------------------------------------------------------------------------------------------------------- |
| Registry IDs  | `ADV-R3X-LINEAGE-001`, `R3Y-*` rows, wave-A resolved rows                                                  |
| Audit         | `.trellis/tasks/archive/2026-06/06-23-round3-post-r3x-strict-audit/review-evidence/R3Y-AUD-08-go-no-go.md` |
| Map slice     | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §2.4.5                                                                |
| base branch   | `master` @ `527d6506`                                                                                      |
| target branch | `fix/r3y-registry-lineage-defer`                                                                           |
| worktree      | `../quant-monitor-desk-wt-fix-r3y-registry`                                                                |
| owner agent   | merge-coordinator-α2                                                                                       |
| Trellis track | `debt-lite`                                                                                                |

## Boundary

**Allowed files**

- `docs/AUDIT_DEFERRED_REGISTRY.md`, `docs/UNRESOLVED_ISSUES_REGISTRY.md`, `docs/RESOLVED_ISSUES_REGISTRY.md`
- `docs/implementation_tasks/UNRESOLVED_ITEM_TASK_COVERAGE.md`
- `ROUND3_BATCH_IMPLEMENTATION_MAP.md`, `docs/ROUND3_HANDOFF.md`（checkpoint 一句，若需）
- `.trellis/tasks/archive/2026-06/06-22-round3-batch3-staged-gate/**`（bootstrap 归档重定位）
- `.trellis/workspace/Guang/round3-wave-a-slice-plans.md`（协调者 slice 索引一句）
- `tests/test_round3_audit_registry_alignment.py`, `tests/test_unresolved_item_task_coverage.py`
- `.trellis/tasks/fix-r3y-registry-lineage-defer/**`

**Forbidden files**

- `backend/**`（runtime）
- `frontend/**`, `scripts/**`（除只读验证）
- 其他 agent 并行分支上的 registry 同时编辑

**Production / data boundary**

- Docs/tests only；无 DB / live fetch / production-live 声称

**Explicit non-goals**

- 不实现 L3/L4 lineage runtime（属 `021`+）
- 不闭合 `R3Y-SYNC-001` / `R3Y-MUT-PROOF-001`（属 α-1 / B-19）

## Execute 工程纪律（用户强制）

**Boot 前 MUST Read（全文，不可摘要跳过）：**

1. `.cursor/rules/ponytail.mdc`（或 `/ponytail` skill）
2. karpathy-guidelines（项目 `.trellis/spec/` 与 Execute 约定）
3. `.claude/skills/testing-guidelines/SKILL.md`（testing-guidelines）

**执行顺序：**

1. **TDD**：若需新增/修改 registry 对齐测试 → 先 RED → `execute-evidence/α2-red.txt` → 再改 docs → GREEN → `α2-green.txt`
2. **Ponytail**：只改 registry/coverage 必要行；禁止新建无关 markdown；禁止重复登记
3. **测试注释**：每个新增/修改测试须 docstring 写明：**覆盖范围**、**测试对象**、**目的/目标**
4. **完整 pytest**：任何 GREEN 后必须 `uv run pytest -q` 全绿；证据 `execute-evidence/full-pytest-green.txt`
5. **禁止改测试目的**：可改断言实现以匹配 SSOT，不可削弱验收目标或删除 ID 覆盖

**无 MASTER.plan**：本切片不走 complex Execute gate；仍遵守 TDD + ponytail + testing-guidelines。

## Vertical slices

| Slice | Source ID             | AC                                                                                  | Verification                                        |
| ----- | --------------------- | ----------------------------------------------------------------------------------- | --------------------------------------------------- |
| α2-1  | R3Y row SSOT          | 三 registry + COVERAGE 与 Map §1 aliases 一致；`Last reconciled` 更新               | `test_unresolved_item_task_coverage.py`             |
| α2-2  | `ADV-R3X-LINEAGE-001` | DEFERRED 行含 owner `021`+、closure test                                            | registry alignment tests                            |
| α2-3  | Wave-A resolved       | `R3-TASK-019/020/023A`, `R3Y-AUDIT-GATE-18`, `R3-B3-STAGED-DOWNSTREAM-GATE` 在 RESOLVED 可追溯 | `test_round3_audit_registry_alignment.py`           |
| α2-4  | Map checkpoint        | `527d6506` / §2.4 准确                                                              | `test_round3Map_checkpointReflectsPost14AuditMerge` |
| α2-5  | OPEN 项 owner         | `R3Y-SYNC-001` 等 OPEN 行指向 α-1 / B-19 / β-2 branch                               | COVERAGE §4.5                                       |

## Merge gate

```bash
uv run pytest tests/test_round3_audit_registry_alignment.py tests/test_unresolved_item_task_coverage.py -q
uv run python scripts/check_doc_links.py
uv run pytest -q
```

**Evidence path:** `.trellis/tasks/fix-r3y-registry-lineage-defer/execute-evidence/merge_gate_report.md`

**Remaining deferred:** 列出仍 OPEN 的 R3Y 项及 owner branch（α-1 / B-19 / β-2）
