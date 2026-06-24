# 公共约束（所有桶 agent 必读）

## 任务

Debt Lite 临时批次 **Phase A（align-ponytail）**：在 allowed 测试文件内，使测试代码完全符合注释描述，并用 `/ponytail full` 提升简洁性与可维护性。

## 硬约束

1. **禁止修改任何测试注释**（模块 docstring、用例 docstring、意图性 `#` 注释）
2. **禁止修改** `backend/` 及本桶 allowed 列表外的任何文件
3. **禁止** `git commit` / `git push`
4. 发现注释与 `tests/test_catalog.yaml` 或契约文档明显矛盾：**以注释为准改代码**，并写入 `execute-evidence/bucket-{ID}-comment-conflicts.md`
5. 需要改 `tests/conftest.py` 或共享 helper：只写 `bucket-{ID}-conftest-requests.md` 提案，不要直接改
6. **测试价值守恒（DEBT.plan.md §1.1）：** 禁止为性能或简洁而删除/弱化测试，禁止用 mock 或「等价路径」替代注释要求的真实环境（含真实网络、live fetch、subprocess CLI、真实 DB 写路径等）

## Phase A 与 ponytail 的边界

- ponytail **可以**删注释未声称的冗余代码、合并重复 setup、复用已有 helper
- ponytail **不可以**删断言、合并 parametrize 导致覆盖变弱、把 live/network 测改成 mock
- 若某用例注释声明的验证点无法在不 mock 的前提下加速 → **Phase A 不动该路径**；Phase B 标记 `no-perf-without-value-loss`

## Phase B（性能）附加约束

见 DEBT.plan.md §1.1、§4.3。Phase B 必交：

```
execute-evidence/bucket-{ID}-perf-value-checklist.md
execute-evidence/bucket-{ID}-perf-notes.md
```

### perf-value-checklist 模板（每个被改动的用例一行）

| 用例       | 原测试价值（摘自注释） | 优化手段              | 价值仍完整（Y/N） | network/live 仍真实（Y/N/NA） |
| ---------- | ---------------------- | --------------------- | ----------------- | ----------------------------- |
| `test_foo` | …                      | fixture scope session | Y                 | Y                             |

任一行 `价值仍完整` 为 N → 不得 merge 该改动。

## 必读 Skill

- `.claude/plugins/cache/ponytail/ponytail/4.7.0/skills/ponytail/SKILL.md`（或项目内 ponytail 规则）
- `.claude/skills/testing-guidelines/SKILL.md`（测试规范；不得为通过而改测试目的）
- `C:\Users\Guang\Desktop\quant-monitor-desk\.trellis\tasks\debt-test-hygiene-batch\DEBT.plan.md` §3 禁止删清单、**§1.1 测试价值守恒**

## 每个用例必答五问（写入 align-checklist）

1. 注释中的**被测对象**是否就是代码 import/call 的对象？
2. 注释中的**验证点**是否被 assert/raises/match 覆盖？
3. **失败含义**是否与 assertion 粒度一致？
4. 是否有注释**未声称**的额外行为？（有则删代码，不改注释）
5. 是否已复用 `tests/conftest.py` / `tests/db_helpers.py` / 同桶已有模式？（ponytail 第 2 梯级）

## 产出（全部相对 repo 根）

```
.trellis/tasks/debt-test-hygiene-batch/execute-evidence/
  bucket-{ID}-align-checklist.md
  bucket-{ID}-pytest-green.txt
  bucket-{ID}-comment-conflicts.md   # 无则写 "none"
  bucket-{ID}-deletion-candidates.yaml  # Phase C 候选，本阶段只列不移除
```

## Phase C 删除候选格式（本阶段只收集，不删）

```yaml
candidates:
  - path: tests/test_example.py
    reason: "一次性 Round2 audit 回归，verifies 为空且无 authority_graph 引用"
    replacement_coverage: tests/test_audit_remediation.py::test_foo
    risk: low|medium|high
```

**禁止**将 DEBT.plan.md §3 列表中任何文件写入 candidates。  
**禁止**以运行慢/占资源为理由提议删除（§3.5 第 5 条）。

## 完成定义

- 桶内 pytest 全绿
- align-checklist 全部 Y（或 N 项已在 conflicts 中解释且代码已修）
- git diff 仅 touching allowed files
- 未改任何注释文本
