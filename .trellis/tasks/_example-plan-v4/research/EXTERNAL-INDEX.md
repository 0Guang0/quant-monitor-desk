# 外部索引 — Plan v4.1 样板

> **§A** 开工必读 · **§B** 情境路由 · **§C** 源码字典

---

## §A — 切片开工前必读（外部）

| #   | 路径                                                 | 内容     |
| --- | ---------------------------------------------------- | -------- |
| A1  | `docs/implementation_tasks/GLOBAL_TASK_TEMPLATE.md`  | 活卡模板 |
| A2  | `docs/implementation_tasks/GLOBAL_TESTING_POLICY.md` | 测试策略 |
| A3  | `docs/decisions/README.md`                           | ADR 目录 |

---

## §B — 执行情境路由（外部）

| 情境           | 路径                                                     |
| -------------- | -------------------------------------------------------- |
| Plan 协议全文  | `.trellis/spec/guides/complex-task-planning-protocol.md` |
| Skill 产出契约 | `.trellis/spec/guides/plan-skill-outputs.yaml`           |

---

## §C — 源码 · 测试字典

| 模块                 | 路径                                              |
| -------------------- | ------------------------------------------------- |
| manifest 协议测试    | `tests/test_execution_index_protocol.py`          |
| validate_plan_freeze | `.trellis/scripts/common/validate_plan_freeze.py` |
| generate_manifests   | `.trellis/scripts/common/execution_index.py`      |
