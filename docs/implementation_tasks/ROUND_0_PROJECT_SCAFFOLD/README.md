# ROUND 0 PROJECT SCAFFOLD

本目录包含 5 个正式 implementation task 文件。必须按文件编号顺序执行。

执行前读取：

- `../GLOBAL_EXECUTION_RULES.md`
- `../GLOBAL_TESTING_POLICY.md`
- `../GLOBAL_RESOURCE_LIMITS.md`
- `../GLOBAL_TASK_TEMPLATE.md`

本目录文件不是临时文件，最终交付包应保留。

## 评估报告跟进（2026-06 三次修复）

Round 0 任务本身无未完成项；三次审计发现的跨 Round 0 治理项已处理：

| 项 | 修复 |
|----|------|
| `scripts/__init__.py` 使 CLI 目录变 package | 已删除 |
| `tests/conftest.py` 未使用的 `project_root` fixture | 已移除 |
| `docs/architecture/07_project_directory_structure.md` 与实布局漂移 | 已同步 `core/`、`storage/`、根级 `scripts/`、`tests/smoke/` |
