# Repair/Debt Lite Plan — fix/r3y-sync-adapter-guard (α-1)

## Source of truth

| 项            | 值                                                                  |
| ------------- | ------------------------------------------------------------------- |
| Registry ID   | `R3Y-SYNC-001`（ADV-R3X-SYNC-001 partial）                          |
| Audit         | `R3Y-AUD-01` F-02 · `R3Y-AUD-02` HIGH · `R3Y-AUD-03` reconcile WARN |
| Map slice     | `ROUND3_BATCH_IMPLEMENTATION_MAP.md` §2.4（repair-debt α-1 row）    |
| base branch   | `master` @ `527d6506`                                               |
| target branch | `fix/r3y-sync-adapter-guard`                                        |
| worktree      | `../quant-monitor-desk-wt-fix-r3y-sync-adapter-guard`               |
| owner agent   | fix-agent-r3y-sync                                                  |
| Trellis track | `debt-lite`                                                         |

## Boundary

**Allowed files**

- `backend/app/sync/orchestrator.py`, `backend/app/sync/runners.py`
- `tests/test_sync_orchestrator.py`, `tests/test_sync_jobs.py`
- `.trellis/tasks/fix-r3y-sync-adapter-guard/**`

**Forbidden files**

- `backend/app/ops/**`, `backend/app/datasources/**`（除 guard 所需单行 import）
- `backend/app/layer3_chains/**`
- registry trio（α-2 独占）
- `data/duckdb/quant_monitor.duckdb`

**Production / data boundary**

- 仅 fail-closed guard + 测试；不扩大 live fetch；测试 profile 仍可用 `adapter=` 若显式 test-only hook

**Explicit non-goals**

- 不重写 reconcile 全链路（`R3-PARTIAL-3`）
- 不修改 `DataSourceService` 本体

## Execute 工程纪律（用户强制）

**Boot 前 MUST Read（全文）：**

1. `.cursor/rules/ponytail.mdc`（或 `/ponytail` skill）
2. karpathy-guidelines
3. `.claude/skills/testing-guidelines/SKILL.md`

**执行顺序（每 slice 重复）：**

1. **TDD 严格**：先 RED → `execute-evidence/α1-red.txt`（必须 FAIL）→ Read karpathy-guidelines + testing-guidelines + ponytail ladder → 最小实现 GREEN → `α1-green.txt`
2. **Ponytail**：在 `orchestrator`（或 `runners`）**单点 guard**；复用现有 profile/env 检测；禁止新抽象层/新依赖
3. **测试注释**：每个测试 docstring：**覆盖范围**、**测试对象**、**目的/目标**（含 `test_r3ySync001_*`）
4. **完整 pytest**：每个 slice GREEN 后 `uv run pytest -q`；最终 merge gate 附 `full-pytest-green.txt`
5. **禁止改测试目的**：现有 `datasource_service=` 路径测试必须仍绿；不可为通过而删除 route 断言

**GitNexus：** 编辑 `run_incremental` / `run_backfill` / `run_reconcile` 前 `impact()` upstream。

## Vertical slices

| Slice | AC                                                                       | RED       | GREEN                   |
| ----- | ------------------------------------------------------------------------ | --------- | ----------------------- |
| α1-1  | production profile `run_incremental(..., adapter=X)` 无 service → reject | 新测 FAIL | guard + 测绿            |
| α1-2  | `run_backfill` 同上                                                      | 新测 FAIL | 同上                    |
| α1-3  | `run_reconcile` adapter-only 生产入口 reject（test hook 保留）           | RED       | GREEN                   |
| α1-4  | `test_r3ySync001_*` 映射 `R3Y-SYNC-001`                                  | RED       | GREEN                   |
| α1-5  | 现有 service-path 与 adapter test 套件仍绿                               | —         | full sync + full pytest |

## Merge gate

```bash
uv run pytest tests/test_sync_orchestrator.py tests/test_sync_jobs.py -q
uv run pytest tests/test_datasource_service.py tests/test_source_route_planner.py -q
uv run pytest -q
uv run ruff check backend/app/sync tests/test_sync_orchestrator.py tests/test_sync_jobs.py
```

**Evidence:** `execute-evidence/merge_gate_report.md` · `α1-red.txt` · `α1-green.txt` · `full-pytest-green.txt`

**Registry:** 不修改三 registry（α-2）；merge_gate 注明 `R3Y-SYNC-001` 待 α-2 登记 CLOSED
