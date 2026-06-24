# Agent 派发 — MERGE-C（Merge Coordinator）

> **角色：** 主会话或专用 merge agent  
> **分支：** `debt/test-hygiene/integration`（集成）；各桶 feature 分支 merge 目标  
> **不写 Phase A 业务测试逻辑**（除非收口 conftest/db_helpers 提案）

## 职责

1. **派发前 Baseline**：执行 DEBT.plan.md §4.1，写入 `execute-evidence/baseline-*.txt`
2. **Worktree 创建**：为 9 个桶各建 worktree + 分支（用户 gate 后）
3. **锁文件协调**：唯一可改 `tests/conftest.py`、`tests/test_catalog.yaml`、`tests/db_helpers.py`
4. **按序 merge**：SMK → LOOP → AUD → OPS → VAL → L1 → L23 → DS → G
5. **每桶 merge 后** §4.4 merge gate；失败退回对应桶分支
6. **Phase C 汇总**：合并各桶 `bucket-*-deletion-candidates.yaml` → `research/deletion_candidates/MERGED-deletion_candidates.yaml`
7. **Phase B 审查**：逐条核对各桶 `perf-value-checklist.md` 与 git diff；§1.1 违规（删测、弱 assert、mock 偷换真实网络/DB/CLI）→ 退回该桶
8. **Phase D**（用户批准后）：执行删除 + `loop_maintain.py --fix` + §4.5
9. **产出** `execute-evidence/merge_gate_report.md`

## merge_gate_report.md 必含

- changed files 列表（按桶）
- baseline vs post-merge pytest 结果
- `check_test_catalog` / `loop_maintain` / `generate_project_map --check` 结果
- conftest 变更摘要（若有）
- MERGED deletion candidates 条数与 §3 冲突检查结果
- Phase B perf-value-checklist 审查结果（通过/退回项）
- 剩余 deferred / 未合并 conftest 请求

## 禁止

- 在 Phase C 汇总完成且用户批准前删除任何测试文件
- 批准任何违反 DEBT.plan.md §1.1 的 Phase B 优化 merge
- 修改 `docs/ops/verification_commands.md`
- force-push `master`

## Baseline 命令

见 DEBT.plan.md §4.1。

## Merge gate 命令

见 DEBT.plan.md §4.4。
