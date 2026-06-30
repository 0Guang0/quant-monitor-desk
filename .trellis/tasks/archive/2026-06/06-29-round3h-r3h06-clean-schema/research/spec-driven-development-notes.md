# Spec-Driven Development Notes — R3H-06

## 契约 → 测试映射

| 契约 / SSOT                                 | 字段 / 规则                                                                | 测试锚点                      |
| ------------------------------------------- | -------------------------------------------------------------------------- | ----------------------------- |
| `specs/schema/schema.sql` `security_bar_1d` | OHLCV + PK(instrument_id, trade_date, adjustment_type)                     | `test_r3h06_*` bar_ddl        |
| `source_capabilities.yaml` cn_announcements | announcement_id, instrument_id, title, publish_timestamp, url, source_used | `test_r3h06_*` disclosure_ddl |
| `011_layer1_tables.sql` axis_observation    | observation_id PK; macro 序列                                              | `test_r3h06_*` domain_router  |
| WriteManager SUPPORTED_MODES                | upsert_by_pk on PK tables                                                  | `test_r3h06_*` idempotency    |
| `sandbox_clean_write_contract.yaml`         | domain caps                                                                | 回归 `test_round3g_*`         |
| `MIGRATION_COVERAGE.md`                     | 013 DONE 行                                                                | `test_migration_coverage.py`  |

## cn_announcement_clean 草案列（Plan 冻结 · 用户 2026-06-29）

```text
announcement_id       VARCHAR PRIMARY KEY
instrument_id         VARCHAR NOT NULL
title                 VARCHAR NOT NULL
publish_timestamp     TIMESTAMP NOT NULL
announcement_url      VARCHAR          -- capabilities.url
announcement_type     VARCHAR          -- 可空；源未分类则 NULL
data_domain           VARCHAR NOT NULL -- cn_announcements | cn_filings | cn_pdf_reports
source_used           VARCHAR NOT NULL
pdf_file_id           VARCHAR          -- → file_registry（PDF 已登记时）
extracted_text_file_id VARCHAR         -- → file_registry（未来摘要/全文；本卡 NULL）
content_status        VARCHAR NOT NULL DEFAULT 'metadata_only'
  -- metadata_only | pdf_registered | text_pending | summary_ready | full_text_ready
batch_id              VARCHAR
source_fetch_id       VARCHAR
content_hash          VARCHAR
schema_hash           VARCHAR
quality_flags         VARCHAR
created_at            TIMESTAMP
```

**未来管道（本卡不实现）：** 抓取原文/摘要 → 写 `file_registry` + 更新 `extracted_text_file_id` + `content_status`；clean 行仍是一行一公告。

## rollback

- migration down：本仓库若无可逆 down，rollback = 恢复 pilot DB 快照 + 不 promote；文档 §8 写明。

**Phase 2b complete**
