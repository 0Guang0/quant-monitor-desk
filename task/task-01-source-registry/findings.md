# task-01-source-registry · Findings

> **planning-with-files 外部记忆** · 本票只记本步问题。
> 全局索引：`task-19-phase1-gate/PHASE1_COMPLETION_INVENTORY.md`

## Requirements

- R4 成品：数据源注册模块（Source Registry / Capability）
- 范围：源注册与 capability
- 权威：见 `README.md` → **权威文件**（`**/design/**` only）

## Research Findings

- 2026-07-11：完整的权威倒查、正式入口复现、反证和 CC-0～CC-7 结论，以 [completion-check-audit.md](/C:/Users/Guang/Desktop/quant-monitor-desk/task/task-01-source-registry/completion-check-audit.md:1) 为唯一详细记录；本文件只保留可执行的短台账与审计后新增发现。
- task-19 F-15 经核验属 Phase-1 的 production-live 决议，不是当前 task-01 design 的已审阅变更；当前权威 YAML 仍规定 `macro_series` 默认禁用，因此未迁入。F-16 的 Tier A 启用清单当前确实缺失，但它是 Phase-1 运营治理要求、非本票 design 的原子交付，也未迁入。F-17 的大量默认禁用与权威一致，非缺陷。
- 2026-07-11 G1-01：正式入口与 OVERRIDE 消费者全量见 [g1-01-wiring-inventory.md](g1-01-wiring-inventory.md)。新增运行时事实：YAML `validation` 多源列表在 `_normalize_validation_source` 只保留首项（→ G1-03）；无 per-domain 回补缓冲天数字面量（ADR-017 规则足够，→ G1-07）。
- 2026-07-11 G1-01 补缺：`sync_to_db` 调用方补登 `qmd-init-db --sync-registry`（E-REG-03）、`DataSyncOrchestrator.bootstrap(sync_registry=True)`（E-REG-04，当前仅测试调用但仍可写）、`ensure_isolated_db`（E-ACC-ISO-01，gate_live only）。
- 2026-07-11 G1-01 Plan 复审：首版清单遗漏 `qmd-init-db --sync-registry` 与 `DataSyncOrchestrator.bootstrap(sync_registry=True)` 两个 `SourceRegistry.sync_to_db` 调用方；因此 `PLAN-OPEN`，不得进入 RED。完整 CC-0～CC-7 记录见 [completion-check-plan-g1-01.md](completion-check-plan-g1-01.md)。

## 审计索引（2026-07-11）

| Findings 条目 | 详细审计记录 | 去重规则 |
|---|---|---|
| T01-F01 | [CC-2 验真](/C:/Users/Guang/Desktop/quant-monitor-desk/task/task-01-source-registry/completion-check-audit.md:18) | capability 成品性、运行时证据与闭环条件只在审计记录展开。 |
| T01-F03 | [CC-1 证伪](/C:/Users/Guang/Desktop/quant-monitor-desk/task/task-01-source-registry/completion-check-audit.md:17)、[CC-3 同路](/C:/Users/Guang/Desktop/quant-monitor-desk/task/task-01-source-registry/completion-check-audit.md:19)、[CC-4～CC-7](/C:/Users/Guang/Desktop/quant-monitor-desk/task/task-01-source-registry/completion-check-audit.md:20) | 入口覆盖、档位、权威偏离与技术债只在审计记录展开。 |
| T01-F04 | [Plan CC-3/CC-4](completion-check-plan-g1-01.md) | G1-01 入口盘点缺口只在本轮 Plan 审计记录展开。 |
| T01-F02 | 无（审计后新增） | 保留本条的当前配置与 RoutePlan 复现事实。 |
| T01-D01 | [CC-7 守闸](/C:/Users/Guang/Desktop/quant-monitor-desk/task/task-01-source-registry/completion-check-audit.md:23) | 保留“按设计”的结论；入口绕过的反证以审计记录为准。 |

## Technical Decisions

| Decision | Rationale |
|----------|-----------|
| [ADR-017](/C:/Users/Guang/Desktop/quant-monitor-desk/docs/decisions/design/ADR-017-dynamic-source-fallback-and-exception-data-lifecycle.md:1)（Accepted） | 用户已确认动态启用覆盖层、按领域自动降级、来源/质量独立标签、连续监控、回补与异常归档生命周期；已同步至索引 design 与共享契约，后续实现必须遵守。 |

## 开放项（ledger）

| ID | 现象 | 标签 | disposition | 证据 |
|----|------|------|-------------|------|
| T01-F03 | CLI/增量仍以内存 OVERRIDE（ESR / 强制 platform）破坏启用 SSOT；**3A 问开关 API 已落地**，安检接线与调用方迁移未完成 | enable policy / 跨模块依赖 | 待修复（3A 已切；余 3B/3C/4a/4b/4x） | 3A：`activation_overlay.py` + `017_*.sql` + `completion-check-execute.md` CLOSED；余：`macro_incremental_common.py` ESR、`data_commands.py` 金路径；票 04–08 |

## 已关闭 / 按设计

| ID | 摘要 | disposition | 证据 |
|----|------|-------------|------|
| T01-D01 | 大量 `enabled_by_default: false` 是 fail-closed 设计：不得 mass-enable；缺授权、资格或配置时应返回 `DISABLED_SOURCE` / `USER_AUTH_REQUIRED` | 按设计 | `data_sources.md` 默认启用与 domain gating；`qmt_xqshare_setup.md` §3-4；详见审计索引 CC-7 |
| T01-F01 | capability 顶层 draft / implementation_gap 作放行依据 | 已修复 | 票 01 · `capability_registry._validate_capability_document`；YAML `status: active`；load 边界测试 |
| T01-F02 | macro_supplementary 默认启用但 validation_only Primary → VALIDATION_ONLY_BLOCKED | 已修复 | 票 02 · `_validate_domain_roles` + 三域失败关闭；默认路由 DISABLED_SOURCE |
| T01-F03-3A | 问开关三键→三字段 + `source_activation_overlay` 持久化 + 隔离根可测；禁 setattr 撬门 | 已修复（切片） | 票 03 · `completion-check-execute.md`；`tests/test_activation_overlay.py`；≠ G1-02 整包 |
| T01-F04 | G1-01 入口清单曾漏 E-REG-03/04 等 | 已修复（清单） | `g1-01-wiring-inventory.md`；Plan r6 `PLAN-READY` |

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| — | — |

## Resources

- `README.md` — 模块职责与权威/运行时文件
- `../TASK_PIPELINE_INDEX.md` — 流水线顺序
- [completion-check-audit.md](/C:/Users/Guang/Desktop/quant-monitor-desk/task/task-01-source-registry/completion-check-audit.md:1) — 2026-07-11 的独立 R4 审计与 CC-0～CC-7 判定

## Visual/Browser Findings

- （无则留空）

---
*每 2 次查看/搜索后更新本节，防止上下文丢失*
