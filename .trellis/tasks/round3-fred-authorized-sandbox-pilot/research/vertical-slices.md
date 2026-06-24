# Vertical Slices — Phase 3.5 /to-issues（冻结）

> 工单 ID = FRED-01..07；Execute 不得合并为单脚本水平实现（`BATCH_01_ADVERSARIAL_AUDIT` §6）

| ID | 标题 | 建设内容 | 验收标准 | 依赖 | 证据输出 | 测试计划 |
| --- | --- | --- | --- | --- | --- | --- |
| FRED-01 | Registry & capability guard | `fred` 行：disabled-by-default、sandbox-candidate；capability 无 production-live | RED: 无 fred 行或默认可 live → FAIL；GREEN: registry/capability 测试绿 | WL 只读引用 | `proposed_registry_delta.yaml`（主会话合并） | `test_fred_source_registry.py` |
| FRED-02 | Route preview only | P0 series dry-run / route preview；拒绝未列 series | RED: 未列 series 可路由；GREEN: sandbox/raw-only plan | FRED-01 | `route_preview_fred.json` | `test_source_route_planner.py` 子集 |
| FRED-03 | Mocked fetch port | `FredSandboxFetchPort`（或窄扩展 `staged_pilot_fetch_ports`）；raw/staging manifest | RED: 缺 hash/fetch_id；GREEN: 必需字段齐全 | FRED-02 | `fred_raw_manifest.json` | `test_fred_sandbox_pilot.py` |
| FRED-04 | Failure taxonomy | `FRED_PILOT_*` 状态枚举；auth/network/schema/validation 显式失败 | RED: 失败静默 PASS；GREEN: 各失败路径断言 | FRED-03 | `fred_pilot_status_report.json` | `test_fred_sandbox_pilot.py` |
| FRED-05 | Pilot-local evidence health | `fred_evidence_validator.py` 检查 stale/missing/malformed；**不改** `data_health.py` | RED: 坏 evidence 未检出；GREEN: validator 报告 WARN/FAIL | FRED-03 | `fred_evidence_health.json` | `test_fred_sandbox_pilot.py` |
| FRED-06 | Registry closeout | `B2.5-O-05` 关闭或 re-defer 决策 + proposed registry 更新 | RED: 无 FRED-only 证据却关闭；GREEN: closeout 字段完整 | FRED-03..05 | `fred_pilot_closeout.json` | `test_fred_staged_semantics.py` |
| FRED-07 | Authorized live fetch（可选） | hardening §3 授权 YAML + live 小样本；仅 sandbox 写 | RED: 无授权 live 成功；GREEN: cap 内 evidence + no-mutation | FRED-03 + auth | `fred_live_fetch_evidence.json` · `authorization.yaml` | skip 或 isolated live test |

## 默认 caps（与 R3E §7 一致）

| 项 | 值 |
| --- | --- |
| max series | 5 |
| max rows per series | 100 |
| max network calls | 10 |
| window | 1–3y（按月序列可窄化） |
| write_target | raw/staging/sandbox only |
| production_clean_write | false |
