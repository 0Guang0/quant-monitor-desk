<!-- FROZEN: Plan protocol v4 · source: docs/implementation_tasks/{{ROUND}}/{{NNN}}_*.md -->

# {{任务标题}}（冻结执行卡）

> **读者：Execute + Audit**  
> **活文档（Plan 可继续改）：** `docs/implementation_tasks/{{ROUND}}/{{NNN}}_*.md`  
> **索引（步骤/必读原文）：** `EXECUTION_INDEX.md`  
> **禁止**在冻结后编辑本文件；变更须重新 `task.py freeze-task-card` + `validate-plan-freeze`。

---

## 1. 任务目标

（从仓库任务卡 §1 加固复制；Plan 阶段可内联合并模块设计/契约要点。）

## 2. 预期结果 / AC

| ID   | 可验证结果 |
| ---- | ---------- |
| AC-1 | {{…}}      |

## 3. 输入文件（Plan 已读；可总结项已内联到 §5–§8）

| 路径                  | 处理                              |
| --------------------- | --------------------------------- |
| `specs/contracts/...` | 已内联 §6 或见 EXECUTION_INDEX §3 |

## 4. 相关代码文件

## 5. 现有模式 / 参考（含 GitNexus Phase 1b 结论）

## 6. 技术约束（含 Phase 4 设计决策）

## 7. 资源约束

## 8. 边界约束 / 停止条件

| #   | 条件          | 动作          |
| --- | ------------- | ------------- |
| 1   | {{…}}         | 停止并回 Plan |
| 5+  | 自定义：{{…}} | {{…}}         |

## 9. 实现步骤（Phase 3.5 to-issues 垂直切片）

### 9.0 Boot

- Read `EXECUTION_INDEX.md` + `implement.jsonl` 每条 + `context_pack.json`

### 9.1 {{切片名}}

- 交付物：{{…}}
- 依赖：{{…}}

## 10. 测试要求

| 文件        | 目的  | 成功  | 失败意味着 |
| ----------- | ----- | ----- | ---------- |
| `tests/...` | {{…}} | {{…}} | {{…}}      |

## 11. 验收命令

## 12. 完成标准

## 13. Red Flags

## 14. Execute Skill 冻结（原 MASTER §12）

| Skill                   | 本任务 | 绑定 Step | 触发    |
| ----------------------- | ------ | --------- | ------- |
| test-driven-development | 必做   | 每步      | 每 §9.x |
