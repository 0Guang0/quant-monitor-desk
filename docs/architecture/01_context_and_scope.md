# 系统上下文与范围

> 本文件是拆分后的导航文件，不替代模块原文。详细内容见对应模块文件。

## 系统目标

少数人使用、低门槛、本地优先、可逐步扩展的量化监控系统。核心不是第一天做全自动交易，而是建立“可信数据 → 多层建模 → 证据链监控 → Agent 汇总解释 → 人工确认”的监控系统。

## 范围内

- 多源数据注册、抓取、标准化、质量检查、冲突治理。
- DuckDB + 本地文件系统 + Parquet 的本地优先数据底座。
- Layer 1 到 Layer 5 的五层分析框架。
- FastAPI 后端、React 前端、Agent 只读解释层。
- 运维、备份、性能、健康检查。

## 范围外 / 第一阶段不做

- 不做全自动交易。
- 不让 Agent 自由上网、直接写库或输出交易动作。
- 第一阶段不上 PostgreSQL、Next.js、Airflow、多 Agent 编排或复杂微服务。

## 详细来源

- `docs/architecture/00_project_overview.md`
- `docs/architecture/02_solution_strategy.md`
- `docs/architecture/05_module_map.md`
