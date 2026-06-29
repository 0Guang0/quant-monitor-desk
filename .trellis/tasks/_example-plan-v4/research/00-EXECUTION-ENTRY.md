# Plan v4.1 样板 — 执行入口（Execute SSOT）

> **角色：** 唯一 Execute 读入口  
> **协议：** Plan v4.1 Execution Bundle · `plan-skill-outputs.yaml`

---

## 1. 任务目的 · 价值 · 完成条件

| 维度         | 内容                                                              |
| ------------ | ----------------------------------------------------------------- |
| **目的**     | 演示 v4.1 Execution Bundle 结构与 `validate-plan-phase 5e` 机械门 |
| **价值**     | 新复杂任务可复制目录布局与 freeze 流程                            |
| **完成条件** | EX-01 绿 · `validate-plan-freeze` 零错误                          |

---

## 2. 约束 · 规则 · 铁律

| 类别 | 约束                       | 详述位置                           |
| ---- | -------------------------- | ---------------------------------- |
| 测试 | 遵守 GLOBAL_TESTING_POLICY | EXTERNAL-INDEX §A                  |
| 样板 | 不引入生产行为变更         | `to-issues-slices.md` Out of scope |

---

## 3. 验证命令

```bash
uv run pytest tests/test_execution_index_protocol.py -q
python .trellis/scripts/task.py validate-plan-phase .trellis/tasks/_example-plan-v4 5e
python .trellis/scripts/task.py validate-plan-freeze .trellis/tasks/_example-plan-v4
```

---

## 4. ADR 索引

| ADR | 标题           | 绑定                          |
| --- | -------------- | ----------------------------- |
| —   | 本样板无新 ADR | 见 `docs/decisions/README.md` |

> 有架构决策时登记 `docs/decisions/ADR-NNN-*.md` 并在此索引。

---

## 5. 执行包阅读规则

### 5.1 文件地图

| 文件                            | 用途                  |
| ------------------------------- | --------------------- |
| `to-issues-slices.md`           | 垂直切片 AC           |
| `plan-task-breakdown.md`        | Plan Document         |
| `plan-spec.md`                  | Spec 模板产出         |
| `plan-context.md`               | 上下文层次            |
| `plan-doubt-review.md`          | Doubt cycle           |
| `reference-adoption-example.md` | trellis-research 产出 |
| `plan-consolidation.md`         | 5e 分流对照           |
| `EXTERNAL-INDEX.md`             | 包外路径 §A/B/C       |

（Plan-only：`plan-boot.md` · `project-overview.md` · `gitnexus-summary.md`）

### 5.2 切片开工前必读

1. 上表全部包内文件（除 Plan-only）
2. `EXTERNAL-INDEX.md` §A
3. `to-issues-slices.md` 当前切片 §

### 5.3 执行阶段情境路由

| 情境             | 路由                                             |
| ---------------- | ------------------------------------------------ |
| 测 manifest 槽位 | `tests/test_execution_index_protocol.py`         |
| freeze 失败      | `plan-consolidation.md` · `validate-plan-freeze` |
| 协议字段         | `task.json` `meta.execute_entry`                 |

---

## 6. GAP

| GAP               | 时机                    |
| ----------------- | ----------------------- |
| `implement.jsonl` | `generate-manifests` 后 |

---

## 7. 当前切片指针

默认：`to-issues-slices.md` §1 **EX-01**

## D. 机器路由

权威数据在 **`context_pack.json`**（本任务根目录）。 由 `context_router.py --task` 写入；本段不重复列举。
