# Project overview — R3G-01（Phase 1a）

## 模块地图

| 区域         | 路径                                                | R3G-01 关系                         |
| ------------ | --------------------------------------------------- | ----------------------------------- |
| 契约         | `specs/contracts/sandbox_clean_write_contract.yaml` | cap + 报告字段 SSOT                 |
| 编排（待建） | `backend/app/ops/sandbox_clean_write/`              | 本任务主交付                        |
| 参考编排     | `backend/app/ops/staged_pilot.py`                   | compose gates 样板（sandbox-first） |
| FRED 授权    | `backend/app/ops/fred_sandbox_pilot.py`             | `load_authorization_yaml` 形态复用  |
| 写链         | `write_manager.py` + `validation_gate.py`           | 必经                                |
| 路由         | `datasources/service.py` + `route_planner.py`       | fetch 证据                          |
| 门禁         | `core/resource_guard.py`                            | 排练 job 前                         |
| Data health  | `ops/data_health.py` + `data_health_profiles/`      | 写前 profile                        |
| CLI          | `cli/data_commands.py`                              | 新增子命令                          |
| L1 ingest    | `layer1_axes/ingestion.py`                          | **不**扩展 allowlist；勿误用        |

## Batch 3G 串行

R3G-01 → R3G-02 → R3G-03；本任务仅第一步。

## 测试现状

- `test_round3g_sandbox_clean_write_rehearsal.py` — 契约门禁（已存在）
- `test_round3g_sandbox_rehearsal_loader.py` / `test_round3g_sandbox_rehearsal_report.py` — Execute 创建并实现
