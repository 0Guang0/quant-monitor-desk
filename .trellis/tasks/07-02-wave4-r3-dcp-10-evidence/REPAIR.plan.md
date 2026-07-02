# REPAIR.plan — 07-02-wave4-r3-dcp-10-evidence

> **来源：** `audit.report.md` §4.3 · **Ledger：** `research/audit-repair-ledger.md`

## §1 修复行（A9 → Repair）

| ID | 修复动作 | 验证 |
| --- | --- | --- |
| A1-P2-001 | 活卡 commit 到 feature 分支 worktree | `Test-Path docs/implementation_tasks/.../R3_DCP_10_LAYER5_EVIDENCE_BINDING.md` |
| A1-P3-001 | 活卡状态对齐 Audit/Repair | 活卡 L11 · AC §5 `[x]` |
| A1-P2-002 | 落盘 `gitnexus-audit-summary.md` | 文件存在 |
| A1-P3-002 | GitNexus analyze 刷新索引 | `context(build_source_provenance_from_bundle)` 可选 |
| A2-P2-001 | `run_mootdx_replay_incremental` 共享 helper | 两 e2e 模块复用 |
| A4-P2-01 / A8-P2-01 | S02 e2e 断言 ADR-031 dataset ids | `test_layer5_mootdx_bar_clean_e2e.py` |
| A4-P2-02 / A8-P2-02 | content_hash fail-closed 单测 | `test_layer5_provenance_bridge.py` |
| A4-P2-03 / A8-P1-01 | fetch_log 加载 mootdx bundle | `load_mootdx_raw_bundle_from_fetch_log` |
| A4-P3-01 | 缺 schema_version 不写 macro schema id | `evidence_bundle.py` |
| A8-P0-01 | audit basetemp 长路径绿 | `--basetemp=.trellis/tasks/.../.audit-sandbox/pytest` exit 0 |
| A8-P3-01 | conftest 预建 task audit sandbox | `tests/conftest.py` |

## §2 复验

```bash
uv run pytest tests/test_layer5_evidence_foundation.py tests/test_mootdx_incremental_e2e.py -q
uv run pytest tests/test_layer5_provenance_bridge.py tests/test_layer5_mootdx_bar_clean_e2e.py -q --basetemp=.trellis/tasks/07-02-wave4-r3-dcp-10-evidence/.audit-sandbox/pytest
uv run pytest -q
python .trellis/scripts/task.py validate-repair-close .trellis/tasks/07-02-wave4-r3-dcp-10-evidence
```
