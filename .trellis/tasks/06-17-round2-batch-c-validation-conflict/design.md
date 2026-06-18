# Design 索引 — Round 2 Batch C

见 `MASTER.plan.md` §4–§7。

- 设计链路：staging/raw evidence → DataQualityValidator → SourceConflictValidator → DbValidationGate → WriteManager。
- 数据结构：validation_report、data_quality_log、source_conflict、manual_review_queue。
- 路径修正：使用 `backend/app/validators/*`，不得创建 `backend/validation/*`。
