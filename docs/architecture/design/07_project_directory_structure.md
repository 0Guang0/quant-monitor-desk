# 项目目录结构

> 拆分说明：本文件由 `quant_monitor_design_document_v1_6.md` 拆分生成；当前步骤只做结构拆分与明显版本/编号残留修正，不删减原有细节。
> 来源：第 16 章

# 16. 项目目录结构

```text
quant-monitor/
  backend/
    app/
      api/
      datasources/
      db/
      etl/
      validators/
      layer1_axes/
      layer2_sensors/
      layer3_chains/
      layer4_markets/
      layer5_evidence/
      agents/
      notifications/

    scripts/
      init_db.py
      sync_daily.py
      sync_intraday.py
      sync_layer1_axes.py
      sync_layer2_sensors.py
      build_industry_graph.py
      calc_features.py
      gen_daily_report.py

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
