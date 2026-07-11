# Gate 1 跨模块接线规格与执行切片

> **状态：** G1-01 Plan r6 = **`PLAN-READY`**；最终执行计划集合 Plan（`completion-check-plan-execution-set.md`）= **`PLAN-READY`**；G1-02～G1-08 待实施（实现 R4 仍 OPEN）
> **权威输入：** ADR-017、ADR-018、`source_provenance_quality_contract.yaml`、Source Registry／RoutePlan／WriteManager 设计；执行索引 [`EXECUTION-DOC-INDEX.md`](EXECUTION-DOC-INDEX.md)。
> **目的：** 让 task-01、02、17、18 的正式入口对同一请求作出同一受控决定；随后让所有消费面诚实显示数据风险。

## 问题与目标

目前正式 CLI、增量任务和调度路径可能通过内存覆盖 registry、替换角色查询或强制平台允许来绕过
Source Registry 的失败关闭边界。这样即使 RoutePlan 或 capability 正确，实际运行仍可能选择未授权、
禁用或能力不匹配的数据源。

完成后，管理员只经受控覆盖层改变有效启用状态；RoutePlan 是唯一选源决定；CLI 与 scheduler 只执行
该决定。主源失败时监控不断线，但次源、质量异常、人工复核和修复事件一路可追溯；主源恢复后仅替换
同一事实位置的默认可信版本。

## 已确认决策与待核实事项

| 分类         | 内容                                                                                           | 处理方式                                                                           |
| ------------ | ---------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| 已确认       | 稳定注册表 + 持久化管理员启用覆盖层；Validation 不升格为 Primary；三层数据；风险标签；恢复归档 | 直接实现，不再重新讨论。                                                           |
| 受控配置核实 | 各领域的固定 fallback 优先级、更新频率、回补前后缓冲窗口                                       | 先从现有权威配置和 registry 读取；若没有唯一值或相互冲突，再向用户提一个精确问题。 |
| 后续 UI 决策 | 风险标签的页面布局、颜色和交互                                                                 | 不阻塞策略接线；阻塞生产前端成品发布。                                             |

## 唯一策略接口

**两层（ADR-018；禁止揉成一层）：**

1. **问开关：** 输入仅 `source_id` + `data_domain` + `operation` → `is_allowed` / `reason_code` / `overlay_revision`。  
2. **安检 + RoutePlan：** 输入 platform、data_domain、operation、frequency、授权上下文，以及只读有效启用（含 overlay）；输出持久化 RoutePlan（候选顺序、selected source/role、route status、机器原因码、来源/质量等级、人工复核、主源失败原因、registry/`overlay_revision`、恢复关联）。

**兼容规则：** 仅新增字段；不得改义既有原因码、候选排序或状态。未登记、未审核、未启用、未授权或 capability 不匹配的来源始终失败关闭。  
**防漂移：** [g1-02-execution-brief.md](g1-02-execution-brief.md) · [g1-01-wiring-inventory.md](g1-01-wiring-inventory.md)。

## 用户故事与验收

1. 作为管理员，我修改受控启用覆盖层后，服务、CLI 与 scheduler 对同一输入获得同一策略结果。
2. 作为监控用户，所有主源失败时仍得到经质量检查的次源数据，并能看到它是 `DEGRADED`。
3. 作为风险使用者，我能区分“次源但质量通过”和“质量失败、需人工复核”。
4. 作为运维人员，我能看到主源失败的来源、异常类型、影响领域和开始时间；代码/适配器/schema 缺陷自动产生高优先级修复事件。
5. 作为回测用户，我默认读取可信最终库，不会把异常历史当成可信历史；需要时可审计异常版本。
6. 作为 CLI 用户，预览、sync、backfill 与 full-load 都不能借由测试 helper 或 `force_enable` 绕过策略。
7. 作为调度用户，daily 与 recovery job 只执行 RoutePlan，并按领域频率回补，不使用全项目固定天数。
8. 作为发布审批者，我能重放“主源失败→降级→标签→恢复→回补→归档”的完整证据链。

## Gate 1A：策略接线（task-01 / 02 / 17 / 18）

| 责任任务 | 正式职责                                                         | 必须验收的外部行为                                                |
| -------- | ---------------------------------------------------------------- | ----------------------------------------------------------------- |
| task-01  | 发布有效启用、能力与统一拒绝语义；移除本票直接消费者的内存绕过。 | 同参策略查询稳定、失败关闭、审计可追溯。                          |
| task-02  | 生成并持久化唯一 RoutePlan。                                     | 固定候选链、`FallbackPolicy + DEGRADED`、原因/版本/恢复关系完整。 |
| task-17  | CLI 只执行 RoutePlan。                                           | sync/backfill/full-load 与服务预览给出同源、同状态、同原因码。    |
| task-18  | Scheduler 调用同一语义并触发恢复回补。                           | 不自选 source；按领域窗口重拉，任务结果诚实聚合。                 |

## Gate 1B：风险标签消费

Layer1–5、API、前端、通知和 Agent 只读取受治理的可信最终库或连续监控视图。它们必须传播
`source_grade`、`quality_grade`、`manual_review_required`、`route_plan_id`、实际来源和失败原因；
审计归档区不属于默认读取或默认回测。

## 具有阻塞边的垂直切片

| 切片                     | 交付行为                                                            | Blocked by   | 验证证据                                              |
| ------------------------ | ------------------------------------------------------------------- | ------------ | ----------------------------------------------------- |
| G1-01 接线清单与配置核实 | 列出所有正式入口、已有 fallback 顺序/窗口、责任与同参命令。         | 无           | ✅ Plan r6 `PLAN-READY`（`completion-check-plan-g1-01-r6.md`）；可开 G1-02 RED |
| G1-02 task-01 策略接缝   | 问开关 + 安检只读成为唯一启用路径；删除 CLI/宏观/matrix OVERRIDE（含 E-CLI-20 全金路径）；处置 E-ACC-BRIDGE-01；沙箱正规 overlay 测。 | G1-01        | 允许／未授权／能力缺失 + 沙箱 overlay 反证 + rg 清零 ESR/强制 platform + E-CLI-20「只清 fred 漏 else」变红；见 `g1-02-execution-brief.md` §7 |
| G1-03 task-02 RoutePlan  | 持久化固定候选链与完整来源/质量/恢复证据。                          | G1-02        | 主源失败后只选合格次源，未授权候选不被尝试。          |
| G1-04 task-17 CLI        | 四类 CLI 命令只执行 RoutePlan。                                     | G1-03        | CLI 与服务预览同 source/status/reason。               |
| G1-05 task-18 Scheduler  | Scheduler 不自选 source，并按领域窗口发起恢复任务。                 | G1-04        | parent/child 报告和恢复任务可重放。                   |
| G1-06 风险标签消费       | Layer/API/前端/告警消费并显示完整风险。                             | G1-03        | 可信、降级、质量失败、MISSING 四种端到端断言。        |
| G1-07 回补归档闭环       | 主源验证写入后替换默认版本、归档旧异常版。                          | G1-05, G1-06 | 同一事实位置的恢复回放与留存断言。                    |
| G1-08 商业发布门         | 独立审计、运行演练和运维证据证明可发布。                            | G1-02～G1-07 | 完整 completion-check、生产等价演练、回滚与观测证据。 |

## 商业级发布定义

本模块只有在 R1–R10、T01-F01～F03、Gate 1A、Gate 1B 和 G1-08 全部通过后，才可称为“商业级
生产稳定可用”。这要求：正式入口无绕过、所有失败关闭路径可重放、主源故障不断监控但不掩盖代码
缺陷、恢复与归档不丢可信历史、可观测性/备份/回滚可实际演练、全回归与独立 completion-check
均通过。任何仅 mock、fixture 覆盖、未接线消费者或“后续补”的状态均为发布阻断。
