# 005 Schema 初始化 — 需求摘要

> **完整内容见 `MASTER.plan.md` §1–§3。** 本文件仅为 Trellis hook 兼容的薄索引。

## 目标（摘要）

用幂等 migration 在 DuckDB 上建立 5 张 foundation 表并记录 `schema_version`。

## 验收（摘要）

见 MASTER §10：`pytest tests/test_schema_migration.py` 7 passed + 全库 lint/compile。

## 非目标

不整库执行 `specs/schema/schema.sql`（DECISIONS.md §3）。
