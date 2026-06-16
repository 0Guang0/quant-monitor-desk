# 外部依据与参考资料

> 拆分说明：本文件由 `quant_monitor_design_document_v1_6.md` 拆分生成；当前步骤只做结构拆分与明显版本/编号残留修正，不删减原有细节。
> 来源：第 20 章

# 20. 外部依据与参考资料

以下资料用于支撑架构选择和工程边界，后续实现时应优先参考官方文档：

1. DuckDB 官方：并发模型。说明 DuckDB read-write 模式适合一个进程读写；read-only 模式允许多个进程读取。  
   https://duckdb.org/docs/current/connect/concurrency.html
2. DuckDB 官方：Parquet 读写与查询。说明 DuckDB 支持高效读写 Parquet，并支持过滤下推和列裁剪。  
   https://duckdb.org/docs/current/data/parquet/overview.html
3. DuckDB 官方：SQL on Pandas。说明 DuckDB 可直接查询 Pandas DataFrame，并转换回 DataFrame。  
   https://duckdb.org/docs/current/guides/python/sql_on_pandas.html
4. FRED 官方 API：series observations。用于第一层大量宏观与市场指标的固定 API 抓取。  
   https://fred.stlouisfed.org/docs/api/fred/series_observations.html
5. xtdata / QMT 文档：行情模块。说明 xtdata 提供历史和实时 K 线、分笔、财务数据、合约基础信息、板块和行业分类等。  
   https://dict.thinktrader.net/nativeApi/xtdata.html
6. FastAPI 官方文档。适合作为 Python API 服务层。  
   https://fastapi.tiangolo.com/
7. Vite 官方文档。适合作为轻量 React + TypeScript 前端构建工具。  
   https://vite.dev/guide/
8. React 官方文档。React 适合通过组件构建交互式 UI。  
   https://react.dev/
9. MSCI Quality Indexes Methodology。示例说明机构方法中常使用 winsorized variables 和 z-score。  
   https://www.msci.com/index/methodology/latest/Quality
10. S&P DJI 研究：比较 z-score 与百分位排名转换方法。说明 z-score 与 percentile rank 都是常见评分方法，但应按指标特性选择。  
   https://www.spglobal.com/spdji/en/documents/research/research-effective-scoring-to-capture-quality-and-value-in-china.pdf
11. Airbyte 官方：Incremental sync。说明增量同步只同步自上次同步以来新增或变化的数据，避免重复抓取全部历史。
   https://docs.airbyte.com/platform/connector-development/connector-builder-ui/incremental-sync
12. Dagster 官方：Backfills。说明 backfill 可按 partition 或 partition 子集补跑，用于补齐缺失或重算数据。
   https://docs.dagster.io/guides/build/partitions-and-backfills/backfilling-data
13. DuckDB 官方：Partitioned Writes。说明 COPY ... PARTITION_BY 可把 Parquet 写成 Hive 分区目录。
   https://duckdb.org/docs/current/data/partitioning/partitioned_writes.html
14. DuckDB 官方：Hive Partitioning。说明 Hive 分区可按目录键组织文件，便于按市场、年份、月份读取。
   https://duckdb.org/docs/current/data/partitioning/hive_partitioning.html
15. Great Expectations 官方：Data Validation workflow。用于参考数据质量检查、checkpoint 与 validation 的工程边界。
   https://docs.greatexpectations.io/docs/0.18/oss/guides/validation/validate_data_overview
16. dbt 官方：Data tests。用于参考 not_null、unique、accepted_values、relationships 等确定性数据测试思想。
   https://docs.getdbt.com/docs/build/data-tests
17. OpenAI 官方：Structured Outputs。用于约束 Agent 输出符合 JSON Schema，使 Layer 1 解释结果可结构化落表。
   https://developers.openai.com/api/docs/guides/structured-outputs
18. OpenAI 官方：2026 年融资公告。用于 Layer 3 私有模型公司事件锚 `openai_2026_funding`。
   https://openai.com/index/accelerating-the-next-phase-ai/
19. Anthropic 官方：Series H funding announcement。用于 Layer 3 私有模型公司事件锚。
   https://www.anthropic.com/news/series-h
20. IEA 官方：Energy and AI 数据中心电力需求。用于 Layer 3 AI 电力与冷却链。
   https://www.iea.org/reports/energy-and-ai/energy-demand-from-ai
21. Arm 官方：FY2026 results。用于 Layer 3 EDA/IP 与芯片 IP 锚点 `arm_fy2026`。
   https://newsroom.arm.com/news/arm-holdings-plc-reports-results-for-the-fourth-quarter-and-fiscal-year-ended-2026
22. NVIDIA 官方：FY2027 Q1 financial results。用于 Layer 3 AI 算力核心锚点 `nvidia_q1_fy27`。
   https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-first-quarter-fiscal-2027
23. Microsoft 官方：FY26 Q3 results。用于 Layer 3 AI Capex 买方锚点 `microsoft_fy26_q3`。
   https://www.microsoft.com/en-us/investor/earnings/fy-2026-q3/press-release-webcast
24. Meta 官方：Q1 2026 results。用于 Layer 3 AI Capex 买方锚点 `meta_q1_2026`。
   https://investor.atmeta.com/investor-news/press-release-details/2026/Meta-Reports-First-Quarter-2026-Results/default.aspx
25. Counterpoint：Q1 2026 HBM market share。用于 Layer 3 HBM 锚点 `counterpoint_hbm_q1_2026`。
   https://counterpointresearch.com/en/insights/global-dram-and-hbm-market-share

---
