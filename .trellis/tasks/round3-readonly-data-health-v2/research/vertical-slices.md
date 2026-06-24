# Vertical slices — R3E data health v2 (/to-issues · Plan 3.5)

> 冻结为 MASTER §8 · 对应任务卡 §9 DH2-01..06 + 基线修复 DH2-BASE

| 序 | ID | 垂直切片 | 交付物（完标准） | 依赖 | AC |
| --- | --- | --- | --- | --- | --- |
| 0 | DH2-BASE | v1 集成基线修复 | `tests/fixtures/data_health/v2_integration_bundle/` 自包含 manifest+payload；`test_dataHealthIntegration_v2Evidence_bundle` PASS/WARN + 日 K 规则断言 | Boot | AC-DH2-BASELINE |
| 1 | DH2-01 | Whitelist profile | `data_health_profile=model_input_whitelist`；缺/坏 whitelist → BLOCKED/FAIL + owner 文案 | BASE | AC-DH2-BLOCKED |
| 2 | DH2-02 | FRED sandbox profile | 检查 series_id/date/value/fetch/hash/as_of/retrieved_at；macro_supplementary 不关 FRED primary | BASE | AC-DH2-FRED |
| 3 | DH2-03 | TDX manual probe profile | 授权/validation-only/非 production primary；无授权 → FAIL/BLOCKED | BASE | AC-DH2-TDX |
| 4 | DH2-04 | Staged pilot v3 profile | baostock/cninfo/akshare caps/role/schema/conflict summary | DH2-01 | AC-DH2-SP3 |
| 5 | DH2-05 | Source readiness rollup | 多 source 混合 → PASS/WARN/FAIL/BLOCKED 汇总 | DH2-01..04 | AC-DH2-ROLLUP |
| 6 | DH2-06 | Rehearsal gate statement | `sandbox_clean_write_gate_ready` 仅在 safety+role+schema+conflict 齐全时为 true | DH2-05 | AC-DH2-GATE |
| 7 | DH2-07 | CLI profile 暴露（可选薄改） | `data_health_cli --profile` 路由到 v2 checker；默认保持 v1 bundle 行为 | DH2-05 | AC-DH2-CLI |

## 证据路径（Execute 对齐）

| 兄弟卡 | 开发期 fixture | 合并前 SSOT |
| --- | --- | --- |
| B01-WL | `tests/fixtures/data_health/whitelist/` | `specs/model_inputs/**` |
| B01-FRED | `tests/fixtures/data_health/fred_sandbox/` | `.trellis/tasks/round3-fred-authorized-sandbox-pilot/execute-evidence/` |
| B01-TDX | `tests/fixtures/data_health/tdx_probe/` | `.trellis/tasks/round3-tdx-manual-probe/execute-evidence/` |
| B01-SP3 | `tests/fixtures/data_health/staged_pilot_v3/` | `.trellis/tasks/round3-real-data-staged-pilot-v3/execute-evidence/` |

## 每切片 RED/GREEN

| ID | RED 焦点 | GREEN 焦点 | 测试文件 |
| --- | --- | --- | --- |
| DH2-BASE | integration 已 FAIL | 自包含 bundle PASS/WARN | `test_ops_data_health.py` |
| DH2-01 | 缺 whitelist BLOCKED | 合法 whitelist PASS | `test_data_health_v2.py` |
| DH2-02 | 缺 fetch/hash/as_of FAIL | 完整 FRED evidence PASS | `test_data_health_v2.py` |
| DH2-03 | 无授权 FAIL | validation-only PASS | `test_data_health_v2.py` |
| DH2-04 | cap/role 违规 FAIL | v3 manifest PASS/WARN | `test_data_health_v2.py` |
| DH2-05 | 混合 staged-only → WARN | rollup 字段齐全 | `test_data_health_v2.py` |
| DH2-06 | 缺 mutation proof → gate false | 全证据 → gate 文案 | `test_data_health_v2.py` |
| DH2-07 | CLI 未知 profile exit 2 | `--profile` 路由 | `test_ops_data_health.py` |
