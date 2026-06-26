# Project Map Omission Check — R3FR-03

> Plan 冻结前运行 `check_docs_specs_indexed.py`。

## 命令

```bash
uv run python scripts/check_docs_specs_indexed.py
```

## 结果（2026-06-26）

- Plan 阶段仅新增/修改 Trellis 任务目录与活任务卡 §8–§14；无新 `docs/`/`specs/` 根文件需索引。
- Execute 若新建 `backend/app/datasources/fetch_ports/` 包，收尾须 `uv run python scripts/loop_maintain.py --fix` 更新 `authority_graph.yaml`。

**结论：** Plan 期无 omission 阻塞；Execute 新包后 loop_maintain 待办已记入 `PLAN_REVIEW.md`。
