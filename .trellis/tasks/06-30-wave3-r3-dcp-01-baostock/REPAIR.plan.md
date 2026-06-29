# REPAIR Plan — R3-DCP-01

> **前置：** A1–A8 齐 · `audit.report.md` FAIL · ledger 已建账

## 修复顺序（根因优先）

1. **RB-01** caught-up：`compute_incremental_window` + runner/CLI no-op when `date_start > date_end`
2. **RB-02/03** dry-run 无 migration；真跑 `assert_sandbox_db_allowed` / canonical denylist
3. **RB-04** cn_equity 真跑 operator 确认（对齐其它 domain）
4. **RB-05/06** main.py `--instrument-id`；CliFailure 非法输入
5. **RB-07/08/09/10** attribution · SQL allowlist · adapter · since/parse
6. **RB-11–13** 测试 + evidence txt；靶向 then 全量 pytest

## 边界

- **allowed：** `DEBT.plan.md` allowed files
- **forbidden：** fred · orchestrator · migrations · canonical DB 写

## 验证

```bash
uv run pytest tests/test_baostock_incremental*.py tests/test_qmd_data_sync_baostock.py tests/test_sync_runners.py -q
uv run pytest -q   # exit 0
python .trellis/scripts/task.py validate-repair-close .trellis/tasks/06-30-wave3-r3-dcp-01-baostock
```

## 关账

ledger 无 **待修复** · `audit.report.md` §5 PASS
