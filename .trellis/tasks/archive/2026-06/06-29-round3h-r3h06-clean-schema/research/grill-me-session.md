# Grill Session — R3H-06（Plan Phase 3）

> Skill: `grill-me` · 2026-06-29  
> **注：** 用户 @ 2026-06-28 已锁定 PASS 路径（`R3H_PASS_EXECUTION_PLAN.md` §1–§2）；本 session 只锁 **schema 形态** 未决点。

## 质问与回答

**Q1：Wave 1 能否跳过直接做 R3H-08 live？**  
A：**否**。计划写明 Wave 3 **依赖 Wave 1** clean DDL；live 写 clean 会重复 pilot 偏离。

**Q2：能否继续只用 `market_bar_clean` 无 migration？**  
A：**否**。G3/G4/G6 在 §5.0.1 须 **CLOSED**；预演偏离已登记，PASS 不接受 ADR 收窄为同表。

**Q3：宏观 fred 是否新建 `macro_series_clean`？**  
A：**否**。`axis_observation` @ migration 011 已是宏观 clean 落点；fred promote 改路由即可。

**Q4：表名用 `security_bar_daily` 还是 `security_bar_1d`？**  
A：**`security_bar_1d`**（`specs/schema/schema.sql` SSOT）。模块文档 `security_bar_daily` 为命名漂移；本卡不 rename migration 表。

**Q5：cninfo PDF 字节是否进 clean 表？**  
A：**否**。`cn_pdf_reports` 走 file_registry + raw；clean 仅 **metadata**（capabilities 字段集）。

**Q6：本卡能否写主库？**  
A：**否**。与 R3H-01～04 一致；DDL 在 migrate runner + pilot/temp DB 验证。

**Q7：`market_bar_clean` 如何处理？**  
A：**否决 VIEW** @ 用户 2026-06-29。Execute **全量**改 `security_bar_1d`（脚本、测、fixture、promote 常量）；**禁止**保留 `market_bar_clean` 实体表或 VIEW。

**Q7b：cninfo 表要加哪些列？**  
A：见活卡 §6.1 — **必加** `announcement_type`、`data_domain`、`content_status`、`pdf_file_id`、`extracted_text_file_id`；正文/摘要不进 clean，走 `file_registry` 指针；当前只写 `metadata_only`。

**Q8：G6 幂等策略？**  
A：有 PK 的 clean 表 **`upsert_by_pk`**；禁止对有 PK 表默认 `append_only` 叠行。

**Q9：谁能改 migration？**  
A：**仅 R3H-06** 分支；R3H-07/08/10 禁止提交 DDL。

**Q10：Layer3/4 表是否一并迁移？**  
A：**否**。B3V-L5R 矩阵仍 DEFERRED Round 3F；本卡只闭合 G3/G4/G5/G6 + bar/disclosure 最小集。

## 结论（Plan 锁定）

| 维度      | 决定                                                             |
| --------- | ---------------------------------------------------------------- |
| 三域      | `security_bar_1d` / `cn_announcement_clean` / `axis_observation` |
| OHLCV     | bar DDL + staging 必含列                                         |
| cninfo    | 禁止 bar 形 clean                                                |
| 幂等      | upsert_by_pk                                                     |
| 主库      | 禁止                                                             |
| pilot     | **无 VIEW**；`market_bar_clean` 删除，统一 `security_bar_1d`     |
| cninfo 列 | §6.1 metadata + 类型 + file_registry 指针；正文后续接 MCP/爬虫   |

**Phase 3 complete**
