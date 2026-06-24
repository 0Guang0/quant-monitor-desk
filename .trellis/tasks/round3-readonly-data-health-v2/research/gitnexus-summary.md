# GitNexus summary — data health v2 (Plan 1b)

## 符号与爆炸半径

| 符号                                   | 角色           | 直接调用方                    | 风险                         |
| -------------------------------------- | -------------- | ----------------------------- | ---------------------------- |
| `DataHealthService.check_evidence_dir` | 集成入口       | `data_health_cli.main`, tests | MEDIUM — 所有 profile 汇聚点 |
| `_checks_from_bundle`                  | v1 bundle 规则 | `check_evidence_dir`          | MEDIUM — BASE 切片修改点     |
| `_resolve_payload_path`                | raw JSON 定位  | `_checks_from_bundle`         | LOW — BASE 切片              |
| `build_report` / `evaluate_gate`       | 报告+gate      | service                       | LOW                          |
| `check_lineage_entry`                  | lineage 规则   | bundle + 新 profile           | LOW                          |

## 执行流

```text
CLI/service → check_evidence_dir(evidence_dir)
  → load_evidence_bundle
  → profile router (v2 新增)
  → profile-specific checks + v1 bundle checks
  → evaluate_gate → DataHealthReport
```

## 变更建议

- 新增 `check_profile_*` 函数族，避免膨胀 `check_evidence_dir` 单体
- v2 测试放 `tests/test_data_health_v2.py`，保留 v1 回归在 `test_ops_data_health.py`
- 改 `_resolve_payload_path` 前跑 `impact(DataHealthService)`

## 基线失败根因（已验证）

`test_dataHealthIntegration_v2Evidence_bundle` → `overall_status=FAIL`  
规则：`MISSING_REQUIRED_FIELD` — `raw payload not found: .audit-sandbox/mock/baostock.json`  
归档 manifest 引用路径在仓库中不存在。
