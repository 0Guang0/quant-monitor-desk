# ADR-015：隔离沙箱 live 验收与双轨测试

- **状态：** 已接受（2026-07-02）；2026-07-09 修订 — 删已退役 tier harness 与旧沙箱段主叙事
- **日期：** 2026-07-02
- **背景：** 产品 live 验收必须在隔离库内完成，且不得污染 canonical 主库。22 源矩阵诚实关账见 [ADR-016](ADR-016-source-route-matrix-honest-closure.md)。

## 决策（Decision）

1. **验收环境：** 所有 live 验收使用独立 `QMD_DATA_ROOT`，路径须含 `source-route-db` 段（典型 `.audit-sandbox/source-route-db/`）。**禁止**指向 canonical 主库 `data/duckdb/quant_monitor.duckdb`。
2. **环境门：** Live 抓取须 `QMD_ALLOW_LIVE_FETCH=1`（或 `true`/`yes`）。未 opt-in 的测试须 skip 或 fail-closed，**禁止**在宣称 live 时静默走 mock。实现：`backend/app/datasources/product_live_gate.py`。
3. **双轨测试：** 默认 `uv run pytest -q` 走 replay/mock 路径（跳过网络）。Live 证明使用 `@pytest.mark.network` 与隔离库 + 环境门组合。
4. **22 源矩阵关账 SSOT：** `qmd-ops accept-source-route-db` + `SourceRouteDbAcceptanceSpine` + `scripts/production_gate.py`（ADR-016）。**不再**使用已退役的 Tier A/B/C harness 脚本路径。
5. **生产等价验收库：** 形态与主库 schema/migrations 一致，数据根隔离；允许在用户授权下开启 live fetch 与 API key；完整链路 route → fetch → staging → validation → WriteManager → clean → Layer read；mock/replay 成功**不得**冒充 live 通过。

## 曾考虑的替代方案（Alternatives Considered）

| 替代方案                           | 拒绝原因                                                      |
| ---------------------------------- | ------------------------------------------------------------- |
| 对主库 `data/duckdb/` 做 live 测试 | 违反 MAIN-DB-GATE / 用户隔离规则                              |
| 删除 replay 测试                   | 破坏无 key 的 CI 与快速 PR 反馈                               |
| 保留 legacy 独立沙箱段名（已退役） | 与 source-route-db 双轨并存造成歧义；已统一为 source-route-db |

## 后果（Consequences）

- Live 关账入口：`backend/app/ops/source_route_db_acceptance.py` · `scripts/qmd_ops.py accept-source-route-db`
- 模块是否达 R4：**以 `MIGRATION_MAP.md` 索引 design 与实现一致为准**（非任务票 MCR 表）
- 22 源矩阵报告：`scripts/production_gate.py --live-authorized --source-matrix-report`

## 生产等价验收报告字段（最低要求）

```text
source_id · data_domain · route_grade · implementation_mode · write_grade
source_used · source_role · source_switched · quality_flags
schema_hash / content_hash · validation_status · conflict_status
failure_class / external blocker（如有）· downstream_layer_read_status
```

**Fallback / degraded clean 口径：** Validation 源不得无标记升级为 Primary；降级写入须带 `source_role=fallback`、`source_switched=true`、`SOURCE_FALLBACK_USED` / `VALIDATION_SOURCE_USED`。

## 相关权威

| 主题              | 路径                                                     |
| ----------------- | -------------------------------------------------------- |
| 22 源矩阵诚实关账 | [ADR-016](ADR-016-source-route-matrix-honest-closure.md) |
| 22 源完整枚举     | `docs/modules/design/data_sources.md` §5.9.1             |
| 部署与隔离运维    | `docs/modules/design/06_deployment_and_local_ops.md`     |
| 夜间 live CI      | `docs/ops/nightly_ci.md`（ADR-011 链入）                 |
