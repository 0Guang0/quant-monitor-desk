# Execute Boot — 06-19-round2-6-routing-service-gate

## AC 摘要（来自 MASTER §2）

| ID | 摘要 |
|---|---|
| AC-PRE | 父任务 `06-19-round2-6-contract-gate` PASS（archived audit.report §4） |
| AC-C1 | SourceCapabilityRegistry 加载 YAML 并在 fetch 前校验 |
| AC-C2 | Adapter domain 与 capability 对齐 |
| AC-C3 | SourceRoutePlanner 实现 READY/DISABLED/NO_SOURCE 等状态 |
| AC-C4 | DataSourceService 生产 fetch facade |
| AC-C5 | Sync runner 使用 service/fetch callable |
| AC-C6 | Module boundary checker green |
| AC-C7 | RoutePlan 写入 job_event_log.payload_json |
| AC-C8 | QMT/Yahoo/xqshare 默认禁用 |
| AC-D1–D4 | prod smoke、ResourceGuard 指标、docs gate、self-check 清理 |

## §8 执行顺序

8.0 → 8.1 → 8.2 → 8.3 → 8.4 → 8.5 → 8.6 → 8.7 → 8.8 → 8.9 → 8.10 → 8.11 → 8.12 → §9 → §10

## Red Flags（来自 MASTER §7）

- 禁止无 ADR 新增 migration
- 禁止启用 qmt_xqshare
- RoutePlan 必须在 adapter 构造前生成
- 禁止 silent fallback
- smoke 使用 `.audit-sandbox` 隔离

## §10 验收命令清单

- Tier A: capability/route/service tests + module boundaries + ruff
- Tier B/C: init_db + production_equivalent_smoke --use-service-path + pytest -q

## Parent gate

Contract Gate audit.report PASS (2026-06-19, PR #17 merged). User explicit execute override for plan-freeze v3 drift.

## Phase 0 complete
