# `/to-issues` 竖切 — M-G1-03

> **SSOT：** `EXECUTION_PLAN.md` §7 · Plan frozen @ 2026-07-04  
> **派发标签：** `ready-for-agent`（`docs/agents/triage-labels.md`）

| Slice   | Phase       | Blocked by | Triage            | What to build                             |
| ------- | ----------- | ---------- | ----------------- | ----------------------------------------- |
| **S01** | P1          | None       | `ready-for-agent` | 62 行矩阵骨架 + boundary 契约 RED         |
| **S02** | P1          | S01        | `ready-for-agent` | watermark + mappers + BindingSyncExecutor |
| **S03** | P1          | S02        | `ready-for-agent` | FullLoad runner + contract + CLI          |
| **S04** | P1          | S02        | `ready-for-agent` | Backfill 扩 Tier A；ops → executor        |
| **S05** | P1          | S03,S04    | `ready-for-agent` | facade + Layer1 ingestion 迁出 fetch      |
| **S06** | P1          | S05        | `ready-for-agent` | CLI 余量 + scheduler + 五 job             |
| **—**   | **P1-GATE** | S06        | `ready-for-human` | pytest 全绿 · boundaries · macro e2e      |
| **S07** | P2          | P1-GATE    | `ready-for-agent` | 矩阵 strict + ADR 关账                    |
| **S08** | P2          | S07        | `ready-for-agent` | macro/policy 源批次真链                   |
| **S09** | P2          | S07        | `ready-for-agent` | COT 批次                                  |
| **S10** | P2          | S07        | `ready-for-agent` | CN bar 批次                               |
| **S11** | P2          | S07        | `ready-for-agent` | US/crypto bar 批次                        |
| **S12** | P2          | S07        | `ready-for-agent` | filings 批次                              |
| **S13** | P2          | S08+       | `ready-for-agent` | 特征/解读/读模型 + P2-GATE                |

Issue 正文模板见 `EXECUTION_PLAN.md` §7。
