# 对抗式审计报告：执行计划 vs 多轮 Plan CC / ADR-018

> **日期：** 2026-07-11  
> **对象：** task-01 执行计划（`task_plan.md` + `gate1-integration-spec.md`）相对 G1-01 多轮 completion-check 与 Accepted ADR-018  
> **结论：** 审计前计划**严重滞后**（§9 仍停在 r2 OPEN；工作包 3 仍「一层唯一接缝」语气）。**已优化落盘**（见下「已落地改动」）。  
> **≠** 实现关账 / R4。

## 分 skill 对抗结论

| Skill | 决定性发现 | 计划动作 |
|-------|------------|----------|
| **api-and-interface-design** | §4A 把整层 RoutePlan 与开关本揉一层 → 违反 ADR-018（弃用方案 A）；缺三键/三字段、One-Version、Hyrum | 拆 4A-1/4A-2；brief §1 |
| **source-driven-development** | 权威以 design ADR-018 + `data_sources.md` §5.2.1 为准；task 目录 `ADR-018-proposed-*` 仅为指针 | 研究文件逐条引用 primary；未改 design |
| **issue-triage** | T01-F03 = ready-for-agent（G1-02）；多轮 CC 入口 ID 未进工作包 = 执行必漏 | brief §3 逐 ID；新增 4x bridge |
| **research** | 见 [research-g1-02-enable-seam-sources.md](research-g1-02-enable-seam-sources.md) 缺口表 §6 | 全部吸收进 brief + task_plan |
| **observability-and-instrumentation** | 3A 有事件名但未强制 `overlay_revision` | 日志字段点名 overlay_revision |
| **deprecation-and-migration** | 缺 Strangler 顺序与「先删 watermark 拷贝」；FRED 合并易被当 G1-02 假关 | 4a 写删除顺序 + 台账不在本切片关 |
| **gitnexus-exploring** | OVERRIDE 共享根因在 `macro_incremental_common`；矩阵 live / backfill / mootdx 同链 | brief 锚定共享根 |
| **gitnexus-impact-analysis** | `enabled_source_registry` **CRITICAL**（~13 direct / ~12 processes）；backfill helper LOW 但业务关键；bridge 近死代码仍须处置 | §8 allow-list 扩大；开工前再 impact |
| **gitnexus-refactoring** | 改 ESR 须先接口后迁调用方再删；禁止 find-replace 散装 | brief §2 退役顺序 |

## 审计前决定性漂移（已修）

1. `task_plan` §9 仍写 r2 `PLAN-OPEN` → 执行者会以为清单未 READY。  
2. 工作包 4b 未写 E-CLI-20 **全金路径** → 会重演 r5 CC-5。  
3. 计划无 E-ACC-BRIDGE-01 → 会重演 r5 CC-3。  
4. gate1 G1-02 仅「三种同参」→ 缺沙箱 overlay / rg 清零 / 全金路径反证。  
5. ADR-018 未进 task_plan §3 权威列表。

## 已落地改动

| 文件 | 变更 |
|------|------|
| `g1-02-execution-brief.md` | **新建**防漂移 SSOT |
| `research-g1-02-enable-seam-sources.md` | 研究底稿 |
| `task_plan.md` | §3/§4A/工作包 3·4a·4b·**4x**/依赖图/§8/§9 |
| `gate1-integration-spec.md` | 两层接口 + G1-02 验证扩展 |
| `decision-map-enable-seam.md` | G1-01 READY 勾选 |
| `g1-01-increment-close.md` | 归档为历史补缺说明 |
| `progress.md` | 本轮动作 |

## 仍须 grill / design 的 UNVERIFIED

开关本 `reason_code` 完整枚举、Python 符号名、revision 算法、管理员写 overlay 的 CLI 字、沙箱标记专用列 — **不得假装已裁定**（research §7）。能复用 `ERROR_CODE_GUIDE` 则复用。

## 下一动作（给执行者）

1. Read `g1-02-execution-brief.md` 全文  
2. 工作包 3A RED（问开关）— TDD  
3. impact(`enabled_source_registry`) 再确认调用方表  
4. **禁止**未落地问开关就删 ESR  

*本报告不构成 PLAN-READY 之外的实现 PASS。*
