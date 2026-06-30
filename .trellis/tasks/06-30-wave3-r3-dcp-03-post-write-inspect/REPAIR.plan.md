# REPAIR Plan — R3-DCP-03 post-write inspect

> **前置：** A1–A8 齐 · `audit.report.md` **FAIL** · `research/audit-repair-ledger.md` 5 项 **待修复**  
> **原则：** P0–P3 **全部修完**，一项不留；禁止仅修 P1 跳过 P2/P3

## 修复顺序（根因优先）

| 序 | ID | 修复 |
| --- | --- | --- |
| 1 | **A1-P1-001** | `build_evidence_bundle_from_fetch_log`：manifest `relative_paths` → `["bars.json"]`（已写 `rows`）；`test_postWriteHealth` 断言 `overall_status in {"PASS","WARN"}` |
| 2 | **A2-P2-01** | 新建 `tests/incremental_baostock_support.py`；`test_baostock_incremental_e2e.py` + `post_write_inspect_support.py` import 共享 bootstrap |
| 3 | **A2-P2-02** | 新建 `tests/support/qmd_ops_cli.py`；`test_ops_db_inspector.py` + `test_incremental_post_write_inspect.py` 共用 |
| 4 | **A5-P2-01** | DEBT S01 验证 `-k postWriteInspect`；更新 `s01-green.txt`；`--collect-only -k inspect` 仅 1 测或改模块名 |
| 5 | **A5-P3-01** | 补 `research/execute-evidence/s01-red.txt` `s02-red.txt` `s03-red.txt`（RED 失败摘要 + 命令） |

## allowed files（Repair 扩展）

```text
tests/incremental_baostock_support.py          # 新建
tests/support/qmd_ops_cli.py                   # 新建
tests/post_write_inspect_support.py
tests/test_incremental_post_write_inspect.py
tests/test_baostock_incremental_e2e.py         # 去重 import only
tests/test_ops_db_inspector.py                 # 去重 import only
tests/test_catalog.yaml                        # 若 loop 要求
.trellis/tasks/06-30-wave3-r3-dcp-03-post-write-inspect/DEBT.plan.md
.trellis/tasks/06-30-wave3-r3-dcp-03-post-write-inspect/research/execute-evidence/*
.trellis/tasks/06-30-wave3-r3-dcp-03-post-write-inspect/research/audit-repair-ledger.md
.trellis/tasks/06-30-wave3-r3-dcp-03-post-write-inspect/audit.report.md
```

## forbidden（同 DEBT.plan）

`backend/app/sync/**` · ports · migrations · canonical DB · `data_health_profiles/**` 生产改动

## 验证

```bash
uv run pytest tests/test_baostock_incremental_e2e.py tests/test_incremental_post_write_inspect.py tests/test_ops_db_inspector.py -q
uv run pytest tests/test_incremental_post_write_inspect.py --collect-only -q -k postWriteInspect  # 1 item
uv run pytest -q   # exit 0
uv run python scripts/loop_maintain.py
python .trellis/scripts/task.py validate-repair-close .trellis/tasks/06-30-wave3-r3-dcp-03-post-write-inspect
```

## 关账

ledger 5 行 → **已修复** · `audit.report.md` §4.2/§5 **PASS** · 无 **待修复**
