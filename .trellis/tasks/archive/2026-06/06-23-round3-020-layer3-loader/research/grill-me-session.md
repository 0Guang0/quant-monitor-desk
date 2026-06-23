# Grill-me session — 020 Layer3 loader (Plan Phase 3)

## CLAIM（需求陈述）

020 只需 staged fixture loader + 硬校验，不碰 snapshot/lineage 写库；021 依赖本输出。

## DOUBT（质问）

| #   | 质问                         | 处置                                                           |
| --- | ---------------------------- | -------------------------------------------------------------- |
| D1  | 是否加载全量 v1.2 registry？ | **否** — fixture 最小可证子集；结构对齐 spec                   |
| D2  | 是否需要 WriteManager sync？ | **defer** — 任务卡聚焦 loader；slice 允许 sandbox 但非 AC 必须 |
| D3  | lineage §15 是否本批？       | **defer `021`** — 本任务只读 `snapshot_lineage_contract`       |
| D4  | 能否读生产 registry 路径？   | **禁止** — `staged_fixture_only` 同 019                        |
| D5  | `R3-B2.75-REQ2-EM` 阻塞？    | **否** — DEFERRED；不得作 live 前提                            |

## RECONCILE（冻结结论）

- staged-only + fixture-backed
- 五表加载 + contract 六条硬规则 + event_only + P0 source_keys
- 测试语义断言；禁止仅 assert called
- MASTER §7 Red Flags 已吸收 D1–D5

## PASS

Plan 可冻结；待用户/协调者 approve 后 `task.py start`。
