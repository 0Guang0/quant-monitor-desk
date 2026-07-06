# 生产 Live 试点政策

> 适用于 Round 3 Batch 2.75（`R3-B2.75-PROD-LIVE-PILOT`）及在正式发布前触及 live/生产数据的任何未来任务。
>
> 本政策仅在试点被显式授权、沙箱优先、证据充分且 fail-closed 时，允许窄范围的 live 数据试点。**不**默认启用生产数据。

## 1. 政策意图

生产/live 数据有价值，因为它能暴露夹具或 staged 数据难以发现的：源漂移、缺字段、时间戳差异、vendor 失败、校验缺口、冲突行为与血缘缺陷。

试点必须在不污染生产 clean DB、不绕过源授权、不让 staged 证据被提升为 production-live 就绪的前提下暴露这些问题。

## 2. 默认立场

| 控制项                     | 默认值                  |
| -------------------------- | ----------------------- |
| Live 源访问                | 禁用                    |
| QMT/xqshare/Yahoo/FRED     | 禁用，除非试点显式授权  |
| `dry_run`                  | `true`                  |
| `raw_only`                 | 首次 live 通过为 `true` |
| `write_target`             | `sandbox`               |
| `allow_clean_write`        | `false`                 |
| 生产 clean DB 变更         | 禁止                    |
| 全市场/全历史/backfill     | 禁止                    |
| 静默回退到夹具/staged 数据 | 禁止                    |

## 3. 授权要求

Live 试点必须在任务证据中记录以下全部字段，否则 fail-closed：

| 字段                     | 要求                                             |
| ------------------------ | ------------------------------------------------ |
| `source_id`              | 恰好一个源，除非当前任务卡显式命名极小 allowlist |
| `data_domain`            | 恰好一个域                                       |
| `operation`              | 恰好一个操作                                     |
| `symbols_or_indicators`  | 默认一个指标/标的                                |
| `as_of` 或 `date_window` | 单日或短有界窗口                                 |
| `max_rows`               | 硬行数上限；目标默认 `<= 100`                    |
| `dry_run`                | 必须默认为 `true`                                |
| `raw_only`               | 首次 live 通过必须默认为 `true`                  |
| `write_target`           | 必须默认为 `sandbox`                             |
| `allow_clean_write`      | 必须默认为 `false`；若变更则仅 sandbox           |
| `authorization_evidence` | 证明用户批准的人类可读路径或配置标记             |

## 4. 源限制

1. QMT 与 xqshare 必须默认禁用。
2. Yahoo 必须保持辅助/仅校验角色，除非未来政策变更其角色。
3. FRED primary live 访问（`ENV-E1-DGS10`）仍延期（`B2.5-O-05`），直到**单独**的用户授权 FRED 试点记录授权证据与沙箱/无生产变更证明。Batch 2.75 Request 3（`akshare` / `macro_supplementary` / `fetch_macro_series` / `DGS10`）**不**闭合 `B2.5-O-05`，不得作为 live FRED primary 或 production-live 宏观证据引用。
4. Akshare 等聚合源可用于小形态试点，但当源 registry 另有规定时不得作为唯一权威生产 Primary。`macro_supplementary` 是 Layer 1 桥接测试的 **staged 补充路由**，不是生产发布的 FRED primary 替代。
5. 路由/能力结果为 `DISABLED_SOURCE`、`CAPABILITY_MISSING`、`USER_AUTH_REQUIRED` 或 ResourceGuard 失败时，试点必须停止。

## 5. 必备阶段门禁

### Phase 0 — 授权

- 记录确切的源/域/操作/窗口/行数上限/写入目标。
- 记录为何所选源适合首次试点。
- 记录用户授权证据。

### Phase 1 — 只读基线

- 捕获只读 DB 清单。
- 捕获 data-root 清单。
- 捕获源 registry/能力状态。
- 证明无生产 DB 变更。

### Phase 2 — dry-run 路由门禁

- 抓取前必须先 route preview。
- 所选路由必须为 `READY`。
- 夹具/staged 回退不能满足本阶段。

### Phase 3 — 仅 raw 微抓取

- 首次 live 抓取仅 raw。
- Raw 证据仅写入沙箱控制路径或等价沙箱证据存储。
- 证据含源、请求参数、内容哈希、抓取时间戳、raw 路径、`file_registry` 行、`fetch_log` 行。
- 生产 clean DB 保持不变。

### Phase 4 — 沙箱校验与可选 clean 写入

- 校验通过后才能 clean 写入。
- 源冲突或严重校验失败阻止 clean 写入。
- WriteManager 是唯一允许的 clean 写入边界。
- Clean 写入目标仅为沙箱 DB 或隔离沙箱 schema。
- 快照血缘必须使用真实 fetch ID/内容哈希。
- production/live 试点禁止合成血缘。

### Phase 5 — 结案

- 以显式试点状态结束。
- 更新 `docs/AUDIT_DEFERRED_REGISTRY.md` 与 `docs/UNRESOLVED_ISSUES_REGISTRY.md`。
- 不得仅凭试点证据闭合广泛的 Batch 6 生产项。

## 6. 证据清单

已关闭试点必须保留：

- 授权证据
- 源/能力快照
- 路由 preview JSON
- ResourceGuard 决策
- DB/data-root 变更前清单
- Raw 文件证据与内容哈希
- `file_registry` 证据
- `fetch_log` 证据
- 校验报告
- 冲突报告或显式无冲突证据
- 若启用 clean 写入：沙箱写入审计与血缘证据
- 证明无变更的生产 DB 变更后清单
- Registry 更新或显式 re-deferral

## 7. 提升规则

通过 Batch 2.75 **不**意味着正式生产数据访问已开放。

通过的试点可让 Batch 3–5 引用真实源形态证据，但正式发布仍属 Batch 6 结案：生产 CLI、backfill/reconcile 闭合、源健康、migration/CHECK 覆盖、打包、runbook 与全量回归证据。

## 8. 验证

规划与政策变更必须由以下测试覆盖：

```bash
pytest tests/test_production_live_pilot_policy.py tests/test_batch25_production_data_gate.py -q
```

未来实现必须增加测试证明：

- 无授权则无 live 抓取
- 禁用源则无 live 抓取
- 路由非 `READY` 则无 live 抓取
- 首次通过为 raw-only
- 强制沙箱目标
- 生产 DB 行数不变
- 夹具/staged 回退不能满足 live 试点证据

## 9. Rehearsal 与产品抓取 SSOT（R3H-10）

| 路径                                                                                           | 角色                  | R3H-08 产品 live？         |
| ---------------------------------------------------------------------------------------------- | --------------------- | -------------------------- |
| `DataSourceService` → `datasources/fetch_ports/*`                                              | **产品抓取 SSOT**     | 是（授权时）               |
| `ops/staged_pilot_*`、`ops/live_pilot_*`、`scripts/run_staged_pilot.py`、`ops/interface_probe` | **仅 rehearsal** 证据 | **否** — 不得替代产品 live |

Rehearsal 模块在模块 docstring 中带 `REHEARSAL_ONLY` 或导入 `backend.app.ops.rehearsal_boundary`（`staged_pilot`、`interface_probe`；`live_pilot` 为 docstring）。它们仅是沙箱/staged 证据路径，**不在** Sync orchestrator 默认导入链上。

### 9.1 沙箱门禁的 ops 抓取（非 forbidden_direct_callers 扫描面）

| 模块                                  | 角色                | 产品 live？ |
| ------------------------------------- | ------------------- | ----------- |
| `ops/prediction_market_live_smoke.py` | 环境门禁沙箱 smoke  | **否**      |
| `ops/fred_sandbox_pilot.py`           | FRED 沙箱 rehearsal | **否**      |
| `ops/tdx_manual_probe.py`             | 仅 TDX 手工校验     | **否**      |

登记目的：审计可见性；R3H-08 产品化时评估是否经 `DataSourceService` 或保持 rehearsal 例外。
