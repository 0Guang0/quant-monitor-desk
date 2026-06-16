# 部署与本地运维入口

> 本文件是部署/运维入口，完整运维细节见 `docs/ops/ops_and_performance_v1_2.md`。

## 当前阶段部署形态

- 本地优先。
- DuckDB 单写多读。
- 前端与 Agent 只通过 FastAPI 读取。
- 文件系统保存原始文件、审计日志、缓存、备份和 Parquet 归档。

## 运维文件

- 完整运维手册：`docs/ops/ops_and_performance_v1_2.md`
- 自检与审计清单：`docs/quality/self_check_and_audit.md`
