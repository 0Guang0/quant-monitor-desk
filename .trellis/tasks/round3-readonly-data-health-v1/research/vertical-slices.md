# Vertical slices — R3Y read-only data health v1 (Plan 3.5 / to-issues)

> 冻结为 MASTER §8.1–§8.9 · 对应任务卡 R3Y-DH-01..09

| 序 | ID | 垂直切片 | 交付物（完标准） | 依赖 | AC |
| --- | --- | --- | --- | --- | --- |
| 1 | R3Y-DH-01 | DataHealth rule model | `DataHealthCheckResult` / `DataHealthReport` dataclass；severity/domain/rule_id 枚举对齐 `data_quality_rules.yaml` | Boot | AC-DH-RULES |
| 2 | R3Y-DH-02 | Manifest loader | 只读加载 raw/staging manifest + staged pilot evidence JSON；project-relative 路径；sandbox-safe | DH-01 | AC-DH-BIZ |
| 3 | R3Y-DH-03 | Daily bar health | OHLC / volume / duplicate key / insufficient history 规则检查 | DH-02 | AC-DH-RULES |
| 4 | R3Y-DH-04 | Metadata health | cninfo metadata required fields / empty title-date-source | DH-02 | AC-DH-RULES |
| 5 | R3Y-DH-05 | Source lineage health | source_used / fetch_id / content_hash / as_of；validation-only misuse | DH-02 | AC-DH-RULES |
| 6 | R3Y-DH-06 | Staleness/window health | date window / max lag / empty response / STALE_DATA | DH-02 | AC-DH-RULES |
| 7 | R3Y-DH-07 | Report builder | JSON + markdown/text summary；`production_db_mutated: false` | DH-03..06 | AC-DH-BIZ |
| 8 | R3Y-DH-08 | CLI/service entrypoint | read-only entry（`data_health_cli` 或 `qmd_ops` 薄包装）；禁 free SQL | DH-07 | AC-DH-IMPL |
| 9 | R3Y-DH-09 | Staged pilot integration | 对 v2 evidence 目录跑全量检查 → PASS/WARN/FAIL + gate 充分性字段 | DH-08 | AC-DH-BIZ, MAP |

## 每切片证据

| ID | RED 证据 | GREEN 证据 | 测试焦点 |
| --- | --- | --- | --- |
| DH-01 | `execute-evidence/8.1-red.txt` | `8.1-green.txt` | model roundtrip / severity mapping |
| DH-02 | `8.2-red.txt` | `8.2-green.txt` | loader paths + missing manifest fail |
| DH-03 | `8.3-red.txt` | `8.3-green.txt` | bad OHLC fixture FAIL |
| DH-04 | `8.4-red.txt` | `8.4-green.txt` | empty metadata FAIL |
| DH-05 | `8.5-red.txt` | `8.5-green.txt` | missing lineage FAIL |
| DH-06 | `8.6-red.txt` | `8.6-green.txt` | stale window FAIL |
| DH-07 | `8.7-red.txt` | `8.7-green.txt` | JSON + text output |
| DH-08 | `8.8-red.txt` | `8.8-green.txt` | CLI exit code + read-only |
| DH-09 | `8.9-red.txt` | `8.9-green.txt` | v2 evidence integration |

## 复用（ponytail）

- `DataQualityValidator` / `SourceConflictValidator` — 规则语义，不复制 validator 全表扫描
- `DbInspector` — 只读 DuckDB 打开模式
- `staged_pilot` manifest 常量名 — evidence 文件名对齐
