# Grill Session — R3H-02（Plan Phase 3）

> Skill: `grill-me` · 2026-06-28

## 质问与回答

**Q1：3G yahoo fixture 存在，是否等于 yahoo `READY_WITH_EVIDENCE`？**  
A：**否**。仅有 skeleton adapter + pilot bundle；缺 fetch port、route READY 测、replay 标准路径、evidence 字段链。

**Q2：R3H-02 能否写 `quant_monitor.duckdb`？**  
A：**否**。sandbox/replay/`.audit-sandbox` only（路线图 §5.0）。

**Q3：yahoo 能否在本卡升格 primary 以闭合 G16？**  
A：**否**。registry `validation_only: true` 是产品承诺；G16 live-wire 可用 replay-first 闭合；live 为 optional，不改 primary 角色。

**Q4：market evidence canonical schema 以谁为准？**  
A：**以 `source_capabilities.yaml` daily bar fields 为准**（`trade_date`, OHLCV, `source_used`, `content_hash`）；`schema_version: market_data_evidence_v1`；crypto 用 `crypto_market_evidence_v1`。

**Q5：`YahooFinanceAdapter` 与 `yahoo_finance_port.py` 冲突？**  
A：**L2 迁 port**；adapter 薄 re-export 或标记 deprecated；`adapters/__init__.py` 注册指向 port 边界。

**Q6：五源都要真网 live fetch 吗？**  
A：**否**。`READY_WITH_EVIDENCE` = port + gate + route + replay + evidence；mock/replay 默认；alpha_vantage live 需 `ALPHA_VANTAGE_API_KEY`；deribit/coingecko public API 可 optional live smoke。

**Q7：能否只交付 alpha_vantage + yahoo，其余 defer？**  
A：**否**（Batch 3H hardening）。每源终态只能是 `READY_WITH_EVIDENCE` 或 **书面 ADR**。

**Q8：哪些源适合 ADR 收窄？**  
A：Plan 默认 **五源全实现**；若 Execute 受阻，**仅** `coingecko`（纯聚合验证）或 `stooq`（低频验证）可作 ADR 候选；`alpha_vantage`/`deribit` **禁止 ADR**（registry Primary 承诺域）；`yahoo` **禁止 ADR 升格**，但允许 ADR 完全禁用（须书面，默认实现 validation READY）。

**Q9：Layer2/L4/L5 binding 深度？**  
A：**smoke only**（§9.7）；禁止 R3H-05 cross-layer PASS。

**Q10：G2 交易日窗本卡闭合吗？**  
A：**部分**。ponytail：自然日 `MAX_WINDOW_DAYS` + evidence `window_kind: calendar_days`；完整 TradingCalendar SSOT → **R3H-03 协调**，不阻塞本卡 replay-first READY。

**Q11：共享 registry 谁改？**  
A：**Coordinator 审查**（PLAYBOOK §3）；本卡 PR 附五源 manifest；禁止未协调改 R3H-01/03/04 拥有的 source。

**Q12：OpenBB provider 能拷吗？**  
A：**架构借鉴 only**；AGPL runtime 禁止；urllib/mock 自建。

**Q13：与 R3G promote 链关系？**  
A：**不扩展** promote 范围；yahoo replay 可兼容既有 bundle 形状；promote 仍 pilot-only。

**Q14：最小垂直切片顺序？**  
A：**9.1 证据契约 → 9.2 alpha_vantage → 9.3 stooq → 9.4 yahoo → 9.5 crypto → 9.6 registry → 9.7 layer → 9.8 merge**。

## 结论（Plan 锁定）

| 维度  | 决定                               |
| ----- | ---------------------------------- |
| 范围  | 五源终态闭环                       |
| 主库  | 禁止写入                           |
| yahoo | validation-only 保持               |
| 架构  | 双 normalizer + 五 port            |
| G2    | ponytail 自然日窗；完整日历 R3H-03 |
| Layer | smoke only；R3H-05 不做            |
| ADR   | 默认五源实现；仅显式收窄           |

**Phase 3 complete**
