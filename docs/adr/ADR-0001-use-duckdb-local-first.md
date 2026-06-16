# ADR-0001: use-duckdb-local-first

- 状态：accepted
- 来源：从 v1.6 设计文档已确认结论拆分生成

## 背景

系统定位为少数人使用、本地优先、低门槛。

## 决策

使用 DuckDB 作为本地核心分析库，结构化状态、索引、快照和证据链进入 DuckDB；原始文件、大历史和审计留痕放入文件系统或 Parquet。

## 影响

必须遵守单写多读，所有写入走 WriteManager，前端和 Agent 不直连数据库。

## 详细参考

`docs/architecture/02_solution_strategy.md`、`docs/modules/local_file_system.md`、`docs/ops/ops_and_performance_v1_2.md`
