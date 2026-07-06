"""Live pilot — constants (split from live_pilot.py, OP-01)."""

from __future__ import annotations

from backend.app.config import DATA_ROOT, PROJECT_ROOT

DEFAULT_PRODUCTION_DB = DATA_ROOT / "duckdb" / "quant_monitor.duckdb"
LIVE_PILOT_AUTHORIZATION_ENV = "QMD_LIVE_PILOT_AUTHORIZATION"

PHASE1_BASELINE_JSON = "phase1_baseline_inventory.json"
PHASE1_BASELINE_MD = "phase1_baseline_inventory.md"
PHASE1_NO_MUTATION_MD = "phase1_no_mutation_proof.md"
PHASE1_CAPABILITY_JSON = "phase1_capability_snapshot.json"
PHASE2_ROUTE_MATRIX_JSON = "phase2_route_preview_matrix.json"
PHASE3_RAW_EVIDENCE_JSON = "phase3_raw_micro_fetch_evidence.json"
PHASE3_NO_PRODUCTION_MUTATION_MD = "phase3_no_production_mutation_proof.md"
PHASE3_REQUEST2_RECONCILIATION_MD = "phase3_request2_evidence_reconciliation.md"
EASTMONEY_VERDICT_MD = "eastmoney_stock_zh_a_hist_verdict.md"
PHASE4_VALIDATION_REPORT_JSON = "phase4_validation_report.json"
PHASE4_CONFLICT_INSPECT_TXT = "phase4_conflict_inspect.txt"
PHASE4_NO_PRODUCTION_MUTATION_MD = "phase4_no_production_mutation_proof.md"
PHASE45_PERF_BUDGET_JSON = "phase45_perf_budget.json"
HITL_CONFIRMATION_MD = "phase3_hitl_user_confirmation.md"
DEFAULT_SANDBOX_ROOT = PROJECT_ROOT / ".audit-sandbox/batch275-live-pilot"

ORIGINAL_REQUEST2_VENDOR_API = "stock_zh_a_hist"
ORIGINAL_REQUEST2_ENDPOINT_HOST = "push2his.eastmoney.com"
SIDECAR_REQUEST2_VENDOR_API = "stock_zh_a_daily"
SIDECAR_REQUEST2_ENDPOINT_HOST = "finance.sina.com.cn"

FRED_PRIMARY_DEFERRED_NOTE = (
    "B2.5-O-05: Request 3 akshare macro shape only; does not close FRED primary for ENV-E1-DGS10"
)

DISABLED_PILOT_SOURCE_IDS = frozenset(
    {
        "fred",
        "qmt_xtdata",
        "qmt_xqshare",
        "yahoo_finance",
    }
)

MAX_PILOT_ROW_CAP = 100

APPROVED_PILOT_REQUESTS: frozenset[tuple[str, str, str]] = frozenset(
    {
        ("baostock", "cn_equity_daily_bar", "fetch_daily_bar"),
        ("akshare", "cn_equity_daily_bar", "fetch_daily_bar_validation"),
        ("akshare", "macro_supplementary", "fetch_macro_series"),
    }
)

APPROVED_PILOT_REQUEST_ENVELOPES: frozenset[tuple[str, str, str, tuple[str, ...], str, int]] = (
    frozenset(
        {
            (
                "baostock",
                "cn_equity_daily_bar",
                "fetch_daily_bar",
                ("sh.600519",),
                "recent 5 trading days",
                10,
            ),
            (
                "akshare",
                "cn_equity_daily_bar",
                "fetch_daily_bar_validation",
                ("sh.600519",),
                "recent 5 trading days",
                10,
            ),
            (
                "akshare",
                "macro_supplementary",
                "fetch_macro_series",
                ("DGS10",),
                "recent 7 calendar days",
                20,
            ),
        }
    )
)
