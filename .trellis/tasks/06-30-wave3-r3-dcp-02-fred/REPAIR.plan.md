# REPAIR Plan — R3-DCP-02

> **前置：** A1–A8 齐 · `audit.report.md` FAIL · ledger 已建账

## 修复顺序

1. **RB-01** reference-adoption cite（port/CLI/run 顶部 L1/L2 锚点）
2. **RB-02** `_sync_fred_macro_incremental` 调用 `assert_sandbox_db_allowed`
3. **RB-03/04/05/06** 错误处理：partial failure · JSON · skip empty value · total_rows sum
4. **RB-07/08** ponytail：hoist service · 测试 support/fixture 合并
5. **RB-09/10** live_smoke 断言 · 补测缺口
6. **RB-11** jsonl manifest
7. **RB-13** registry bypass ponytail 注释
8. **RB-16** commit（用户未要求 push）

## 禁止

- `tests/test_catalog.yaml`（RB-12 主会话 P7）
- `baostock_port` · `sync/runners.py` · `sync/orchestrator.py`

## 验证

```bash
uv run pytest tests/test_fred_macro_incremental*.py -q
# 全绿依赖主会话 catalog + canonical 清理；本轨靶向必绿
python .trellis/scripts/task.py validate-repair-close .trellis/tasks/06-30-wave3-r3-dcp-02-fred
```

## 关账

ledger 无 **待修复**（阶段外置除外）· §5 PASS
