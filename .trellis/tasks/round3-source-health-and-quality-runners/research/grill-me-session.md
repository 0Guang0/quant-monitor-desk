# Grill Session — B3F-SH

> Plan Phase 3 · grill-me

## 质疑与答复

| # | 质疑 | 答复 / Plan 处置 |
| --- | ---- | ---------------- |
| 1 | SH 是否在 DH2 路径建 `source_health_snapshot`？ | **否** — SH-05 + hardening；writer 仅 Batch6 专用入口 |
| 2 | migration 与 MIG 并行冲突？ | SH-01 先 ADR + isolated test DB；SQL 文件等 MIG |
| 3 | sandbox FRED 证据能否关 B2.5-O-05？ | **否** — 须 SH-06 live + 授权 YAML |
| 4 | AkShare 失败能否用 TDX 关 REQ2-EM？ | **否** — SH-07 no-false-close |
| 5 | 能否单 PR 吞 SH-01..07？ | **否** — `/to-issues` 七切片 §9.1–9.7 |

## 未决 → MASTER

- MIG 合并时机：主会话 playbook §7.2 串行建议 MIG → SH
- Registry closeout：proposed delta；主会话合并

**grill closure:** 已写入 MASTER §1.5 / §7 / §3.2
