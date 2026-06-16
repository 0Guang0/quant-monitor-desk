# 模块文档索引

`docs/modules/` 下每个文件对应一个实现模块。读代码前请先确认**权威文件**，避免重复或过时的合并文档。

## 权威 vs 兼容索引

| 主题 | 权威文件 | 兼容索引（勿作实现依据） |
|------|----------|------------------------|
| FastAPI 后端 | [`fastapi_backend.md`](fastapi_backend.md) | [`fastapi_and_frontend.md`](fastapi_and_frontend.md) |
| 前端 Dashboard | [`frontend_dashboard.md`](frontend_dashboard.md) | [`fastapi_and_frontend.md`](fastapi_and_frontend.md) |
| 数据质量与多源冲突 | [`data_validation_and_conflict.md`](data_validation_and_conflict.md) | [`data_validation_write_concurrency.md`](data_validation_write_concurrency.md) |
| 写入并发与 WriteManager | [`write_manager.md`](write_manager.md) | [`data_validation_write_concurrency.md`](data_validation_write_concurrency.md) |

拆分背景：P0 第一轮将原合并文档按职责拆开；兼容文件保留旧链接，内容指向上表权威文件。

## 其他模块

其余 `*.md` 均为该模块的权威设计文档，无重复索引。
