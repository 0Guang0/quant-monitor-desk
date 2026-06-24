# Repair/Debt Lite Plan — fix/r3y-prompt15-evidence (α-3)

## Source of truth

| 项            | 值                                                                                  |
| ------------- | ----------------------------------------------------------------------------------- |
| Registry ID   | `R3Y-PROMPT15-EVID-001`                                                             |
| Audit         | AUD-01 F-01 · AUD-07 · `R3Y-AUD-01-closed-claims.md`                                |
| Map slice     | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §2.2 α-3 row                                    |
| Playbook      | `WAVE_C_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` §3.1 + §3.4                           |
| base branch   | `master` @ `555fd33b`                                                               |
| target branch | `fix/r3y-prompt15-evidence`                                                         |
| worktree      | `../quant-monitor-desk-wt-fix-r3y-prompt15-evidence`                                |
| owner agent   | fix-agent-r3y-evidence                                                              |
| Trellis track | `debt-lite`                                                                         |

## Boundary

**Allowed files**

- `.trellis/tasks/fix-r3y-prompt15-evidence/**`
- `.trellis/tasks/archive/2026-06/fix-round3-r3x-residual-open-items-closure/**`（evidence 补链）
- `tests/test_r3x_residual_open_items_closure.py`（窄改）

**Forbidden files**

- `backend/**` 生产代码
- registry 三件套（`AUDIT_DEFERRED_REGISTRY.md` / `UNRESOLVED_ISSUES_REGISTRY.md` / `RESOLVED_ISSUES_REGISTRY.md`）
- `docs/quality/*REGISTRY*.md`

**Production / data boundary**

- 仅 evidence + 测试；无 DB / live fetch / runtime 变更

**Explicit non-goals**

- 不扩展 18 条伞测 runtime 深度（属 `R3Y-TEST-DEPTH-001` Batch 6）
- 不修改 registry 行（主会话 Wave C 合并后批处理）

## Execute 工程纪律

**Boot 前 MUST Read：**

1. `.cursor/rules/ponytail.mdc`
2. `.claude/skills/testing-guidelines/SKILL.md`
3. `WAVE_C_MAIN_SESSION_COORDINATOR_PLAYBOOK.md` §3.4

**执行顺序：**

1. **TDD RED** → `execute-evidence/α3-red.txt`（evidence index 缺失必 FAIL）
2. **GREEN** → 归档 `closed_claim_evidence_index.yaml` + `*-green.txt` + 更新 merge_gate
3. **Ponytail**：最小 YAML 索引；复用已有 pytest 命令分组；无新依赖
4. **测试五字段 + §2.2.2**：`test_r3yPrompt15_closedClaimEvidenceIndexMapsToGreenTxt`
5. **完整 pytest**：GREEN 后 `uv run pytest -q` 全绿

## Vertical slices

| Slice | AC                                                          | RED              | GREEN                         |
| ----- | ----------------------------------------------------------- | ---------------- | ----------------------------- |
| α3-1  | 归档 evidence index + 9 green.txt 存在                      | 新测 FAIL        | 补链 + 测绿                   |
| α3-2  | 73 claim_id 可审计映射                                      | count 断言 FAIL  | YAML 73 IDs + 测绿            |
| α3-3  | 18 伞测 cross-ref 完整                                      | umbrella 子集 FAIL | index umbrella_tests 完整   |
| α3-4  | merge_gate 引用 evidence 路径                               | —                | merge_gate_report 更新        |
| α3-5  | 全量 pytest 绿                                              | —                | full-pytest-green.txt         |

## Merge gate

```bash
uv run pytest tests/test_r3x_residual_open_items_closure.py -q
uv run pytest -q
```

**Evidence:** `.trellis/tasks/fix-r3y-prompt15-evidence/execute-evidence/merge_gate_report.md`

**Registry:** 不修改三 registry；closure 由主会话批处理

**Remaining deferred:** `R3Y-TEST-DEPTH-001`（Batch 6 per-ID runtime depth）
