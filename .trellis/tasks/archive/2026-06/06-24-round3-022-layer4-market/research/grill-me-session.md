# Grill-me session — 022 Layer4 market structure (Plan Phase 3)

## CLAIM（需求陈述）

022 在 staged fixture 上构建 Layer4 market registry / calendar / breadth / snapshot + contract-scoped lineage；推进 `ADV-R3X-LINEAGE-001` 的 **L4 子集**；不改三 registry；不碰 ops/staged 核心文件。

## DOUBT（质问）

| #   | 质问                                     | 处置                                                         |
| --- | ---------------------------------------- | ------------------------------------------------------------ |
| D1  | 是否需要 live 行情 API？                 | **否** — staged market fixture bundle                        |
| D2  | 是否本任务实现全部 8 个 MarketAdapter？  | **否** — 最小 staged adapter（如 `CN_A`）+ registry 全量种子 |
| D3  | 是否写 DuckDB clean 表？                 | **defer** — 聚焦 builder；WriteManager 仅对照/可选 sandbox   |
| D4  | 是否关闭 ADV-R3X-LINEAGE-001 全量项？    | **部分** — L4 contract pytest + envelope；跨层 DB 写回 defer |
| D5  | 是否本任务改三 registry？                | **否** — coordinator batch only                              |
| D6  | `R3-B2.75-REQ2-EM` 阻塞？                | **否** — DEFERRED                                            |
| D7  | 是否复制 Layer1 全套标准化字段？         | **否** — D-09；仅 contract 必需子集                          |
| D8  | playbook 列的 `layer3_loader_contract`？ | **纠偏** — 文件缺失；以 `loader.py` + L3 snapshot 为上游口径 |

## RECONCILE（冻结结论）

- staged-only + fixture-backed market rows
- 复用 L2/L3 snapshot/lineage 模式；`layer_id=layer4`
- §3.2 显式 register ADV-R3X L4 边界 + R3Y registry hygiene
- MASTER §7 Red Flags 已吸收 D1–D8

## PASS

Plan 可冻结；待用户/协调者 approve 后 `task.py start`。
