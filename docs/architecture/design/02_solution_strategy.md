# 总体架构与解决策略

> 拆分说明：本文件由 `quant_monitor_design_document_v1_6.md` 拆分生成；当前步骤只做结构拆分与明显版本/编号残留修正，不删减原有细节。
> 来源：第 1 章 + 第 3 章

# 1. 总体架构

系统采用本地优先架构：

```text
固定数据源 / 授权数据源 / 白名单来源
        ↓
Fetcher CLI / Sync Jobs / QMT Adapter
        ↓
Raw 原始数据层 + 本地文件系统留痕
        ↓
Normalizer + Validator + Source Priority
        ↓
DuckDB 标准数据层 + Parquet 归档
        ↓
FastAPI / Repository / Agent Tools
        ↓
Vite React TypeScript 看板 / Agent 日报 / 盘中提醒 / 回测复盘
```

第一阶段不建议上 PostgreSQL、Next.js、Airflow、多 Agent 编排或复杂微服务。当前少数人使用、低门槛优先，最优技术栈为：

- 后端：Python 3.11+、FastAPI、Pydantic、pytest、ruff、uv；pip-tools 仅作为备用方案，Poetry 第一版不采用。
- 数据库：DuckDB 作为本地核心分析库。
- 文件归档：本地文件系统；Parquet 作为可选但推荐的历史行情 / 原始数据归档格式。
- 前端：Vite + React + TypeScript。
- 调度：APScheduler 起步；稳定后可升级 Prefect。
- Agent：Python Agent Service，只能调用受控查询工具，不能自由上网、不能直接写库。
- 数据源：QMT/xtdata、baostock、AkShare、巨潮、东方财富为第一优先组合；Yahoo、同花顺、腾讯财经、百度股市通作为补充源插入数据源注册表。

---

# 3. 技术栈选型

## 3.1 默认本地优先技术栈

```text
Python + FastAPI
DuckDB
本地文件系统
Parquet 可选归档
Vite + React + TypeScript
APScheduler / Prefect
Agent 只读工具层
```

## 3.2 DuckDB 使用规则

DuckDB 用于本地分析库和结构化状态表，不作为多进程高并发业务数据库。规则：

1. 单写多读。
2. 所有写入统一走 WriteManager。
3. Agent 不直接写 DuckDB。
4. 前端不直接连 DuckDB，只通过 FastAPI 访问。
5. 大表历史归档优先 Parquet，DuckDB 直接查询 Parquet 或生成聚合表。

## 3.3 DuckDB + Pandas 定位

DuckDB + Pandas 用于研究、ETL 临时处理、样本拼装和 Agent 输入前数据整理。

允许：

```python
df = con.execute("SELECT * FROM stock_bar_1d WHERE trade_date >= '2024-01-01'").df()
con.register("tmp_features", df)
result = con.execute("SELECT * FROM tmp_features WHERE close > 100").df()
```

禁止：

```text
Pandas 临时结果直接覆盖标准表。
Agent 生成 DataFrame 后直接写主库。
绕过 staging / validation / WriteManager。
```

正确流程：

```text
Pandas / DuckDB Research Workspace
        ↓
Staging Table
        ↓
Validation
        ↓
WriteManager
        ↓
Clean Standard Table
```

---

## D-01 依赖锁定决策

用户已拍板：第一版采用 `uv.lock` 作为主锁文件，执行任务和 CI 默认使用 `uv sync --locked` 与 `uv run ...`；`pip-tools` 只作为用户不愿安装 uv 时的备用方案；`Poetry` 第一版不采用，避免给 Claude Code / Codex 引入额外配置复杂度。权威文件见 `specs/contracts/runtime_versions.md`。
