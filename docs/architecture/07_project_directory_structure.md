# 项目目录结构

> 拆分说明：本文件由 `quant_monitor_design_document_v1_6.md` 拆分生成；当前步骤只做结构拆分与明显版本/编号残留修正，不删减原有细节。
> 来源：第 16 章

# 16. 项目目录结构

```text
quant-monitor-desk/
  backend/
    app/
      api/
      core/              # ResourceGuard 等
      datasources/
      db/
      storage/           # RawStore、FileRegistry
      etl/
      validators/
      layer1_axes/
      layer2_sensors/
      layer3_chains/
      layer4_markets/
      layer5_evidence/
      agents/
      notifications/

  scripts/               # 仓库根级 CLI（init_db.py 等）
  tests/
    smoke/               # Round 1 foundation smoke

  frontend/
    src/
      pages/
      components/
      api/
      charts/
      types/

  data/
    duckdb/
    raw/
    files/
    parquet/
    audit/
    reports/
    cache/

  configs/
    datasource.yml
    qmt.yml
    layer1_axes.yml
    market_registry.yml
    alert.yml

  specs/
    layer1_axes/
    layer3_industry_chains/
    layer3_global_industry_chains_v1/
    market_rules/

  docs/
    design/
    ops_and_performance.md
```

---
