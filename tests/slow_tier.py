"""SSOT for pytest slow-tier auto-marking (perf P1 / A08-P1-02)."""

from __future__ import annotations

import re
from pathlib import Path

_SLOW_MODULE_SUFFIXES = ("_incremental_e2e.py",)

_SLOW_MODULE_BASENAMES = frozenset(
    {
        "test_bounded_backfill_cli_e2e.py",
        "test_incremental_post_write_inspect.py",
        "test_layer1_five_axis_panel_clean_smoke.py",
        "test_qmd_ops_source_route_db_acceptance.py",
        "test_sync_binding_executor.py",
    }
)

_SLOW_TEST_NAME_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^test_sourceRouteDbAcceptanceMatrix_dryRun"),
    re.compile(r"^test_qmdData_syncBaostock_nonDryRun_"),
    re.compile(r"^test_qmdData_syncBaostock_failedFinal_"),
    re.compile(r"^test_layer1CleanReader_.*WhitelistRowCap$"),
    re.compile(r"^test_partialSuccess_eachItemWritesAuditEvent$"),
    re.compile(r"^test_backfillJob_"),
    re.compile(r"^test_reconcileJob_"),
    re.compile(r"^test_plannedJobWritesRoutePlanBeforeFetching$"),
    re.compile(r"^test_servicePath_guardBlocked_"),
    re.compile(r"^test_servicePath_disabledRoute_"),
    re.compile(r"^test_runIncremental_pytestProfile_allowsAdapterBypass$"),
    re.compile(r"^test_syncJob_fullLoad_completesWithShards$"),
    re.compile(r"^test_syncFullLoad_"),
    re.compile(r"^test_syncJob_terminalState_cannotTransition$"),
    re.compile(r"^test_.*_liveSmoke_"),
    re.compile(r"^test_sourceRouteDbAcceptance_fredMacroTracer_"),
)


def is_slow_test(path: Path | None, test_name: str) -> bool:
    if path is None:
        return False
    basename = path.name
    if basename.endswith(_SLOW_MODULE_SUFFIXES):
        return True
    if basename in _SLOW_MODULE_BASENAMES:
        return True
    return any(pattern.search(test_name) for pattern in _SLOW_TEST_NAME_PATTERNS)
