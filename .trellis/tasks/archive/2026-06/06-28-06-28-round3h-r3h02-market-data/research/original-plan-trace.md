# Original Plan Trace — R3H-02

> 活任务卡 §2 AC ↔ EXECUTION_INDEX Step ↔ 验证链

| 活卡 §2 / §6 Done criteria             | INDEX Step | §2 AC ID         | 验证链 |
| -------------------------------------- | ---------- | ---------------- | ------ |
| 五源 READY_WITH_EVIDENCE 或 ADR        | 9.6        | AC-REGISTRY      | §2     |
| market_data evidence envelope          | 9.1        | AC-EVIDENCE      | §2     |
| alpha_vantage adapter/gate/route       | 9.2        | AC-ALPHA         | §2     |
| stooq validation global/FX/commodity   | 9.3        | AC-STOOQ         | §2     |
| yahoo validation-only + fixture 迁移   | 9.4        | AC-YAHOO         | §2     |
| deribit/coingecko crypto paths + caps  | 9.5        | AC-CRYPTO        | §2     |
| aggregators not silent primary         | 9.3–9.5    | AC-NO-SILENT-PRI | §2     |
| option-chain / derivatives strict caps | 9.2, 9.5   | AC-CAPS          | §2     |
| Layer2/L4/L5 consume evidence envelope | 9.7        | AC-LAYER         | §2     |
| tests + contract coverage updated      | 9.8        | AC-MERGE         | §2.1   |

**Plan trace complete**
