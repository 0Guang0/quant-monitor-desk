# GitNexus 摘要 — Round 0 Plan 阶段（retrospective）

> Phase 1 回填 · 代码库分析

## 模块触点

| 区域 | 路径 | 说明 |
|------|------|------|
| 应用入口 | `backend/app/main.py` | FastAPI `/health` 占位 |
| 配置 | `backend/app/config.py` | DATA_ROOT、resource_profile |
| 骨架包 | `backend/app/layer{1-5}_*/` | 空 `__init__.py` 占位 |
| 测试 | `tests/test_*` (000–004) | 5 个 Round 0 测试文件 |
| 文档 | `docs/INDEX.md` | 004 索引 |

## 调用链（Round 0 范围）

```text
test_backend_smoke → import backend.app.main → FastAPI app
test_config_templates → configs/*.yaml + .env.example
test_project_scaffold → 目录存在性 vs docs/architecture/07
```

## 与 Round 1 边界

Round 0 **不含** `backend/app/db/`、`core/resource_guard`、`storage/` 实现（Round 1 增量）。
