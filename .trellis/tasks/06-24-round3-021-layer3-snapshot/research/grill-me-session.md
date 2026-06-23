# Grill-me session — 021 Layer3 snapshot builder (Plan Phase 3)

## CLAIM（需求陈述）

021 在 staged fixture 上构建 Layer3 daily snapshot + L5 mapping view + contract-scoped lineage；不关闭 ADV-R3X 全量项；不改三 registry。

## DOUBT（质问）

| #   | 质问                                | 处置                                                            |
| --- | ----------------------------------- | --------------------------------------------------------------- |
| D1  | 是否需要 live Layer5 API？          | **否** — staged L5 bar fixture                                  |
| D2  | 是否写 DuckDB clean 表？            | **defer** — 聚焦 builder 纯函数 + 测试；WriteManager 非 AC 必须 |
| D3  | 是否关闭 ADV-R3X-LINEAGE-001？      | **否** — §3.2 登记边界；全量 → `022`/Batch 5                    |
| D4  | 是否本任务改三 registry？           | **否** — R3Y-LINEAGE-VR-001 → hygiene slice                     |
| D5  | `R3-B2.75-REQ2-EM` 阻塞？           | **否** — DEFERRED                                               |
| D6  | 是否复制 Layer1 全套 lineage 字段？ | **否** — D-09；仅 contract 必需子集                             |

## RECONCILE（冻结结论）

- staged-only + fixture-backed L5
- 复用 L2 snapshot/lineage 模式
- §3.2 显式 register ADV-R3X + R3Y 边界
- MASTER §7 Red Flags 已吸收 D1–D6

## PASS

Plan 可冻结；待用户/协调者 approve 后 `task.py start`。
