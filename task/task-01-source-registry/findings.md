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

## 审计索引（2026-07-11）

| Findings 条目 | 详细审计记录 | 去重规则 |
|---|---|---|
| T01-F01 | [CC-2 验真](/C:/Users/Guang/Desktop/quant-monitor-desk/task/task-01-source-registry/completion-check-audit.md:18) | capability 成品性、运行时证据与闭环条件只在审计记录展开。 |
| T01-F03 | [CC-1 证伪](/C:/Users/Guang/Desktop/quant-monitor-desk/task/task-01-source-registry/completion-check-audit.md:17)、[CC-3 同路](/C:/Users/Guang/Desktop/quant-monitor-desk/task/task-01-source-registry/completion-check-audit.md:19)、[CC-4～CC-7](/C:/Users/Guang/Desktop/quant-monitor-desk/task/task-01-source-registry/completion-check-audit.md:20) | 入口覆盖、档位、权威偏离与技术债只在审计记录展开。 |
| T01-F02 | 无（审计后新增） | 保留本条的当前配置与 RoutePlan 复现事实。 |
| T01-D01 | [CC-7 守闸](/C:/Users/Guang/Desktop/quant-monitor-desk/task/task-01-source-registry/completion-check-audit.md:23) | 保留“按设计”的结论；入口绕过的反证以审计记录为准。 |

## Technical Decisions

| Decision | Rationale |
|----------|-----------|
| [ADR-017](/C:/Users/Guang/Desktop/quant-monitor-desk/docs/decisions/design/ADR-017-dynamic-source-fallback-and-exception-data-lifecycle.md:1)（Accepted） | 用户已确认动态启用覆盖层、按领域自动降级、来源/质量独立标签、连续监控、回补与异常归档生命周期；已同步至索引 design 与共享契约，后续实现必须遵守。 |

## 开放项（ledger）

| ID | 现象 | 标签 | disposition | 证据 |
|----|------|------|-------------|------|
| T01-F01 | `source_capabilities.yaml` 顶层仍是 `status: draft`，并明确声明 adapter domain 与 registry domain 的 production alignment 尚有缺口 | capability / R4 缺口 | 待修复 | `source_capabilities.yaml:2,12`；详见审计索引 CC-2 |
| T01-F02 | `macro_supplementary` 标为 `domain_enabled_by_default: true`，但唯一 Primary `akshare` 为 `validation_only`；实际 RoutePlan 返回 `VALIDATION_ONLY_BLOCKED`，使默认启用域没有可调度主路径 | registry role / 可调度性 | 待修复 | `source_registry.yaml:431-438`；2026-07-11 只读 RoutePlan 复现；`data_sources.md` §5.3、§5.10 |
| T01-F03 | CLI/增量辅助以内存覆盖 registry 的 source/domain 状态并强制平台允许，破坏 `source_registry` / platform matrix 作为启用策略 SSOT 的边界；其 scheduler/RoutePlan 修复仍由 task-19/task-02 负责 | enable policy / 跨模块依赖 | 待修复 | `macro_incremental_common.py:133-155,429-438`；`data_commands.py:304-323`；详见审计索引 CC-1/3 |

## 已关闭 / 按设计

| ID | 摘要 | disposition | 证据 |
|----|------|-------------|------|
| T01-D01 | 大量 `enabled_by_default: false` 是 fail-closed 设计：不得 mass-enable；缺授权、资格或配置时应返回 `DISABLED_SOURCE` / `USER_AUTH_REQUIRED` | 按设计 | `data_sources.md` 默认启用与 domain gating；`qmt_xqshare_setup.md` §3-4；详见审计索引 CC-7 |

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
