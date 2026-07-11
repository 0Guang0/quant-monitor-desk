"""阶段性调试：World Bank live 矩阵失败根因（task-01.5 pytest 阻塞）
功能：复现 incremental 与 job_event_log 消息
业务价值：定位 sync_status=FAILED / rows_written 误计数；记录 api.worldbank.org SSL 环境证据
退役/清理：task-01.5 pytest 全绿且 WB 矩阵 policy 关账后删除（预计 task-02 Phase1 前）
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from backend.app.ops.matrix_live_handlers import _raw_orchestrator
from backend.app.ops.source_route_db_acceptance import _bootstrap_acceptance_db, _count_clean_rows
from backend.app.ops.world_bank_incremental_run import (
    build_world_bank_incremental_service,
    create_world_bank_incremental_port,
    run_world_bank_incremental,
)


def main() -> None:
    os.environ["QMD_ALLOW_LIVE_FETCH"] = "1"
    root = Path(tempfile.mkdtemp(prefix="wb-debug-")) / ".audit-sandbox" / "source-route-db-wb"
    root.mkdir(parents=True)
    cm = _bootstrap_acceptance_db(root)
    raw_root, orch = _raw_orchestrator(root, cm)
    port = create_world_bank_incremental_port(countries=("US",), use_mock=False)
    service = build_world_bank_incremental_service(
        data_root=raw_root,
        fetch_port=port,
        since_by_instrument={"US": "2000-01-01"},
        job_events=orch._jobs,
    )
    wr = run_world_bank_incremental(orch, service=service, countries=("US",), use_mock=False)
    print("overall_status:", wr.overall_status)
    print("instrument_results:", json.dumps(wr.instrument_results, indent=2, default=str))
    print("axis_observation total (misleading count):", _count_clean_rows(cm, "development_indicator"))
    job_id = wr.instrument_results[0]["job_id"]
    with cm.writer() as con:
        rows = con.execute(
            "SELECT event_type, message FROM job_event_log WHERE job_id = ? ORDER BY created_at",
            [job_id],
        ).fetchall()
    print("job events:")
    for event_type, message in rows:
        print(f"  {event_type}: {message}")


if __name__ == "__main__":
    main()
