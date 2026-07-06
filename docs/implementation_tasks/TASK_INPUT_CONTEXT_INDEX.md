# Plan Input Context Bridge

## 1. 三层模型

```text
设计文档 / 规则 / 契约 / 定义
        ↓

```

## 2. Plan 阶段共同必读上下文

| 路径                                                  | Plan 使用原因                                                                            |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `README.md`                                           | 项目入口、docs/specs 非实现地址边界、旧口径禁止恢复、MANIFEST 角色说明                   |
| `MIGRATION_MAP.md`                                    | **全部任务**必读；定位模块设计文档、契约、规则、实现目录入口；Plan 冻结前回查遗漏        |
|                                                       |                                                                                          |
| `PROJECT_IMPLEMENTATION_ROADMAP.md`                   | 前向施工导航（地图不是工单）；Plan 冻结前核对批次与 gate，不得从 staged 证据推断生产就绪 |
|                                                       |                                                                                          |
| `specs/contracts/reference_adoption_guardrails.yaml`  | 参考采纳全局护栏 SSOT；任务卡本地 `reference_project:` 块为执行细节来源                  |
| `docs/INDEX.md`                                       | 文档导航入口                                                                             |
|                                                       |                                                                                          |
|                                                       |                                                                                          |
|                                                       |                                                                                          |
| `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md`  | 测试策略与命名约束；供 Plan 归并到 MASTER/AUDIT                                          |
| `docs/implementation_tasks/GLOBAL_RESOURCE_LIMITS.md` | 资源限制与低占用要求；供 Plan 归并到 MASTER §10                                          |
| `docs/implementation_tasks/GLOBAL_TASK_TEMPLATE.md`   | 原始任务结构、验收命令、阶段化验收要求                                                   |
| `specs/contracts/runtime_versions.md`                 | Python/Node/npm/锁文件与验收命令权威；若执行会用到则进入 implement/audit manifest        |
| `docs/quality/staged_acceptance_policy.md`            | docs-only/backend/frontend/release 分层验收策略                                          |
| `docs/quality/PENDING_USER_DECISIONS.md`              | 用户已拍板 D-01 至 D-12；Plan 不得让执行者重复询问                                       |
| `docs/AUDIT_DEFERRED_REGISTRY.md`                     | 延后项与 resolved gate 的权威登记                                                        |
| `docs/RESOLVED_ISSUES_REGISTRY.md`                    | 已解决问题登记，避免重复修复或误判仍 OPEN                                                |
| `docs/UNRESOLVED_ISSUES_REGISTRY.md`                  | 未解决问题登记，避免遗漏后续必须处理项                                                   |
