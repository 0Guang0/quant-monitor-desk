# REPAIR.plan — M-DATA-03 Tier A Live

> **来源：** `audit.report.md` §4.3 · `research/audit-repair-ledger.md`（41 findings · 全部待修复）
> **全局规则：** `c:\Users\Guang\Desktop\全局规则.txt`（ponytail · TDD · 无遗留 · 阶段外置门槛）

## 本批契约

| 字段             | 内容                                                                                                                                                          |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **本批交付**     | M-DATA-03 Audit Repair 全量关账：41 findings → ledger {已修复, 阶段外置} + `uv run pytest -q` exit 0                                                          |
| **本批 AC**      | ① P1 全部根因修复 ② F0 data health 接入 acceptance 或 formal 文档+代码一致 ③ harness/dispatch 集成测补齐 ④ Trellis manifest/INDEX §2.1 对齐 ⑤ ledger 无待修复 |
| **本批不做什么** | 新 migration / 新 Tier A 源 / 参考项目 runtime import / 主库写路径                                                                                            |
| **阶段外置配额** | 默认 ≤2；本批优先 **待修复**，仅文档 hygiene（如 A2-P3-001 bootstrap 泛化）可 ponytail 本批修                                                                 |

## §1 修复切片（并行 · 无核心文件冲突）

| 切片        | Owner agent  | 范围 findings                                           | 允许改                                                                                                                                                                                                     |
| ----------- | ------------ | ------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **R-OPS**   | repair-ops   | P1 安全/正确性 + dispatch/acceptance 生产路径 + F0 接线 | `backend/app/ops/tier_a_live_*.py` · `scripts/tier_a_live_acceptance.py` · 新建 `tier_a_live_status.py`（若需）                                                                                            |
| **R-TESTS** | repair-tests | 测试缺口 + e2e 同构 + harness/dispatch 集成测           | `tests/test_tier_a_live_*.py` · `tests/test_*_incremental_e2e.py` · `tests/*_incremental_support.py` · 可新建 `tests/live_incremental_support.py`                                                          |
| **R-DOCS**  | repair-docs  | Trellis/manifest/INDEX/eligibility/plan-spec            | `.trellis/tasks/m-data-03-tier-a-live/**` · `docs/decisions/ADR-034*` · `research/tier-a-live-eligibility.md` · `research/plan-spec.md` · `implement.jsonl` · `loop_manifest.json` · `evidence_index.json` |

**串行依赖：** R-OPS 完成 F0/acceptance 语义后 R-TESTS 补集成测；R-DOCS 可与 R-OPS 并行，但 plan-spec F0 条文须与 R-OPS 代码一致。

## §2 复验（关账必跑）

```bash
uv run pytest -q
uv run pytest tests/test_tier_a_live_harness.py tests/test_tier_a_live_dispatch.py -q
uv run python scripts/loop_maintain.py
python .trellis/scripts/task.py validate-repair-close .trellis/tasks/m-data-03-tier-a-live
```

## §3 Finding → 切片路由（摘要）

| 优先级        | IDs                                                                                  |
| ------------- | ------------------------------------------------------------------------------------ |
| P1            | A3-P1-01 · A4-P1-01 · A4-P1-02 · A7-P1-001 · A8-P1-001 · A2-P1-001 · A2-P1-002       |
| F0 主题       | A1-P1-001 · A4-P2-01 · A5-P2-001 · A8-P2-002 → **R-OPS** 代码 + **R-DOCS** plan-spec |
| 测试          | A8-P2-_ · A7-P2-_ · A7-P3-001 · A4-P1-02 · A4-P2-03 → **R-TESTS**                    |
| 文档/manifest | A1-P2-_ · A1-P3-_ · A5-P3-001 → **R-DOCS**                                           |
