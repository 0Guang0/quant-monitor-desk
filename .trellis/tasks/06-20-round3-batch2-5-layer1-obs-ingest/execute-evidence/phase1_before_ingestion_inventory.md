# Phase 1 — Before Ingestion Inventory

- **Phase:** phase1_before_ingestion
- **Mode:** read_only
- **Inspect status:** PASS
- **DB evidence classification:** `fixture_or_staged_evidence`
- **Phase 2 authorized:** True
- **Authorization source:** operator_classification_memo
- **Generated at:** 2026-06-20T11:41:57Z

## Operator classification

- classification: `fixture_or_staged_evidence`
- memo_path: `C:\Users\Guang\Desktop\quant-monitor-desk\.trellis\tasks\06-20-round3-batch2-5-layer1-obs-ingest\execute-evidence\phase1_data_classification.md`
- memo_sha256: `230e419a7cc6c1fcc0bf7fe62140f63f7a79387f9754877c45bd0c042dcb8657`
- operator_ack: phase1_data_classification_memo_present

## Baseline target (project)

- target_db_path: `C:\Users\Guang\Desktop\quant-monitor-desk\data\duckdb\quant_monitor.duckdb`
- target_db_exists_at_capture: True
- target_data_root: `C:\Users\Guang\Desktop\quant-monitor-desk\data`
- capture_strategy: `sandbox_copy_of_target_db`
- capture_note: Target project DB existed; read-only inspect used a sandbox copy with provenance.

## Database (inspected)

- Path: `.trellis\tasks\06-20-round3-batch2-5-layer1-obs-ingest\execute-evidence\.phase1-baseline-sandbox\duckdb\quant_monitor.duckdb`
- Exists: True
- Read-only open: True
- File size (bytes): 4468736

## Data root

- Path: `C:\Users\Guang\Desktop\quant-monitor-desk\data`
- raw_files_count: 1
- parquet_files_count: 1
- audit_files_count: 1
- report_files_count: 0

## Phase 1 minimum key table row counts

| table                          | row_count |
| ------------------------------ | --------- |
| `schema_version`               | 11        |
| `source_registry`              | 5         |
| `file_registry`                | 0         |
| `fetch_log`                    | 0         |
| `data_sync_job`                | 0         |
| `job_event_log`                | 0         |
| `validation_report`            | 0         |
| `data_quality_log`             | 0         |
| `source_conflict`              | 0         |
| `manual_review_queue`          | 0         |
| `write_audit_log`              | 0         |
| `resource_guard_log`           | 0         |
| `axis_observation`             | 0         |
| `axis_feature_snapshot`        | 0         |
| `axis_interpretation_snapshot` | 0         |
| `axis_snapshot_lineage`        | 0         |

## Staging table row counts

| table                  | row_count |
| ---------------------- | --------- |
| `stg_file_registry`    | 0         |
| `stg_foundation_smoke` | 0         |

## Data-root file samples (read-only)

- `raw/.gitkeep` size=0 sha256=`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `parquet/.gitkeep` size=0 sha256=`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `audit/.gitkeep` size=0 sha256=`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

## source_registry snapshot

```json
[
  {
    "source_id": "akshare",
    "source_name": "AkShare",
    "is_enabled": true,
    "allowed_domain": "[\"cn_equity_daily_bar\", \"cn_index\", \"macro_supplementary\", \"sector_board\"]"
  },
  {
    "source_id": "baostock",
    "source_name": "baostock",
    "is_enabled": true,
    "allowed_domain": "[\"cn_equity_basic_financial\", \"cn_equity_daily_bar\"]"
  },
  {
    "source_id": "cninfo",
    "source_name": "\u5de8\u6f6e\u8d44\u8baf CNINFO",
    "is_enabled": true,
    "allowed_domain": "[\"cn_announcements\", \"cn_filings\", \"cn_pdf_reports\"]"
  },
  {
    "source_id": "qmt_xtdata",
    "source_name": "QMT xtdata / miniQMT",
    "is_enabled": false,
    "allowed_domain": "[\"cn_equity_daily_bar\", \"cn_equity_minute_bar\", \"cn_equity_realtime\"]"
  },
  {
    "source_id": "yahoo_finance",
    "source_name": "Yahoo Finance / yfinance-compatible access",
    "is_enabled": false,
    "allowed_domain": "[\"etf_daily_bar\", \"global_asset_reference\", \"us_equity_daily_bar\"]"
  }
]
```

## Evidence summary

- Latest fetch: {'fetch_time': None, 'source_id': None, 'status': None, 'row_count': None}
- Job status counts: {}
- Validation status counts: {}

## Inspect status note

Inspect status `PASS` recorded for audit traceability.

## Classification note

Fetch log or data-root files present — classify as fixture/staged before Phase 2. Phase 2 route dry-run is authorized.

## Sandbox copy provenance

- copy_source: `C:\Users\Guang\Desktop\quant-monitor-desk\data\duckdb\quant_monitor.duckdb`
- copy_sha256: `5eb65e0edaaab223a77c5a5d2660603383836704b4c0ece1eb4aebb047f1682e`
- copy_size_bytes: 4468736
