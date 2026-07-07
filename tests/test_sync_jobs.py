"""同步作业状态机测试（Batch D）。

覆盖范围：合法/非法状态迁移、各作业类型骨架路径及重复创建的幂等语义。
"""

from __future__ import annotations

from datetime import date

import pytest
from backend.app.db.connection import ConnectionManager
from backend.app.db.migrate import apply_migrations
from backend.app.sync.jobs import (
    InvalidTransitionError,
    SyncJobSpec,
    SyncJobStateMachine,
)


def _machine(tmp_path) -> SyncJobStateMachine:
    db = tmp_path / "jobs.duckdb"
    cm = ConnectionManager(db_path=db)
    with cm.writer() as con:
        apply_migrations(con)
    return SyncJobStateMachine(cm)


def _base_spec(**overrides) -> SyncJobSpec:
    defaults = dict(
        run_id="run-1",
        job_id="job-1",
        job_type="incremental",
        data_domain="market_bar_1d",
        market_id="CN_A",
        source_id="baostock",
        adapter_id=None,
        date_start=None,
        date_end=None,
        instrument_id=None,
        partition_key=None,
        trigger_reason=None,
    )
    defaults.update(overrides)
    return SyncJobSpec(**defaults)


def test_syncJob_transition_createdToPlanned_recordsEvent(tmp_path) -> None:
    """覆盖范围：CREATED → PLANNED 合法状态迁移及事件落库
    测试对象：SyncJobStateMachine.transition
    目的/目标：任务从「已创建」推进到「已规划」时，状态和事件都要同步记下来
    验证点：status=PLANNED；事件含 (CREATED, PLANNED, message)
    失败含义：状态变了却没留痕，编排审计链会断
    """
    sm = _machine(tmp_path)
    sm.create_job(_base_spec())
    sm.transition("job-1", "PLANNED", message="planned")
    with sm._cm.writer() as con:
        row = con.execute("SELECT status FROM data_sync_job WHERE job_id = ?", ["job-1"]).fetchone()
        events = con.execute(
            """
            SELECT old_status, new_status, message
            FROM job_event_log WHERE job_id = ? ORDER BY created_at
            """,
            ["job-1"],
        ).fetchall()
    assert row[0] == "PLANNED"
    assert ("CREATED", "PLANNED", "planned") in events


def test_syncJob_invalidTransition_raises(tmp_path) -> None:
    """覆盖范围：跳过中间态的非法迁移
    测试对象：SyncJobStateMachine.transition
    目的/目标：不能从「已创建」直接跳到「写入中」，必须按状态图一步步走
    验证点：抛出 InvalidTransitionError（invalid transition）
    失败含义：非法跳转被放行，任务可能绕过抓取或校验阶段
    """
    sm = _machine(tmp_path)
    sm.create_job(_base_spec())
    with pytest.raises(InvalidTransitionError, match="invalid transition"):
        sm.transition("job-1", "WRITING")


def test_syncJob_terminalState_cannotTransition(tmp_path) -> None:
    """覆盖范围：终态 COMPLETED 之后禁止再迁移
    测试对象：SyncJobStateMachine.transition
    目的/目标：已经完成的任务不能再被拉回「抓取中」等活跃状态
    验证点：走完完整链路至 COMPLETED 后，再 transition 抛 InvalidTransitionError（invalid transition）
    失败含义：终态还能回退，重复执行会破坏幂等和审计一致性
    """
    sm = _machine(tmp_path)
    sm.create_job(_base_spec())
    for status in ("PLANNED", "FETCHING", "STAGED", "VALIDATING", "READY_TO_WRITE", "WRITING"):
        sm.transition("job-1", status)
    sm.transition("job-1", "COMPLETED")
    with pytest.raises(InvalidTransitionError, match="invalid transition"):
        sm.transition("job-1", "FETCHING")


def test_syncJob_fullLoad_createdToPlanned_recordsEvent(tmp_path) -> None:
    """覆盖范围：全量加载类型作业的创建与首次规划
    测试对象：SyncJobStateMachine 对 job_type=full_load 的处理
    目的/目标：全量加载任务类型要正确保存，并能进入「已规划」状态
    验证点：data_sync_job 行 job_type=full_load、status=PLANNED
    失败含义：全量任务类型识别错，调度器分不清增量和全量
    """
    sm = _machine(tmp_path)
    sm.create_job(_base_spec(job_id="job-fl", job_type="full_load"))
    sm.transition("job-fl", "PLANNED")
    with sm._cm.writer() as con:
        row = con.execute(
            "SELECT job_type, status FROM data_sync_job WHERE job_id = ?",
            ["job-fl"],
        ).fetchone()
    assert row == ("full_load", "PLANNED")


def test_syncJob_incremental_createdToPlanned_recordsEvent(tmp_path) -> None:
    """覆盖范围：增量类型作业的创建与首次规划
    测试对象：SyncJobStateMachine 对 job_type=incremental 的处理
    目的/目标：日常增量任务要正确落库，并能进入「已规划」状态
    验证点：data_sync_job.status == PLANNED
    失败含义：增量任务状态落库异常，日常同步无法启动
    """
    sm = _machine(tmp_path)
    sm.create_job(_base_spec(job_id="job-inc", job_type="incremental"))
    sm.transition("job-inc", "PLANNED")
    with sm._cm.writer() as con:
        status = con.execute(
            "SELECT status FROM data_sync_job WHERE job_id = ?", ["job-inc"]
        ).fetchone()[0]
    assert status == "PLANNED"


def test_syncJob_revisionAudit_skeletonReachesStaged(tmp_path) -> None:
    """覆盖范围：修订审计类型作业的骨架状态链路
    测试对象：SyncJobStateMachine 对 job_type=revision_audit
    目的/目标：修订审计任务能按 已创建→已规划→抓取中→已暂存 推进
    验证点：最终 status == STAGED
    失败含义：修订审计卡在早期状态，后续校验和写入接不上
    """
    sm = _machine(tmp_path)
    sm.create_job(_base_spec(job_id="job-rev", job_type="revision_audit"))
    sm.transition("job-rev", "PLANNED")
    sm.transition("job-rev", "FETCHING")
    sm.transition("job-rev", "STAGED")
    with sm._cm.writer() as con:
        status = con.execute(
            "SELECT status FROM data_sync_job WHERE job_id = ?", ["job-rev"]
        ).fetchone()[0]
    assert status == "STAGED"


def test_syncJob_createJob_idempotent(tmp_path) -> None:
    """覆盖范围：相同 job_id 重复 create_job 的幂等语义
    测试对象：SyncJobStateMachine.create_job
    目的/目标：同一个任务 ID 重复创建不应插第二行，应返回同一个 ID
    验证点：两次 create_job 均返回 job-idem；表中 COUNT=1
    失败含义：重试或并发创建出重复任务行，调度和去重都会失效
    """
    sm = _machine(tmp_path)
    spec = _base_spec(job_id="job-idem")
    assert sm.create_job(spec) == "job-idem"
    assert sm.create_job(spec) == "job-idem"
    with sm._cm.writer() as con:
        count = con.execute(
            "SELECT COUNT(*) FROM data_sync_job WHERE job_id = ?", ["job-idem"]
        ).fetchone()[0]
    assert count == 1


def test_syncJob_dataQuality_skeletonCompletes(tmp_path) -> None:
    """覆盖范围：数据质量类型作业的确定性骨架链路
    测试对象：SyncJobStateMachine 对 job_type=data_quality
    目的/目标：数据质量巡检任务能走 已规划→校验中→已完成 的最短路径
    验证点：带 instrument_id 与日期范围的 spec 落库后 status=COMPLETED
    失败含义：质量巡检走不完状态机，门禁报告挂不上任务
    """
    sm = _machine(tmp_path)
    sm.create_job(
        _base_spec(
            job_id="job-dq",
            job_type="data_quality",
            instrument_id="000001",
            date_start=date(2026, 1, 1),
            date_end=date(2026, 1, 31),
        )
    )
    sm.transition("job-dq", "PLANNED")
    sm.transition("job-dq", "VALIDATING")
    sm.transition("job-dq", "COMPLETED")
    with sm._cm.writer() as con:
        status = con.execute(
            "SELECT status FROM data_sync_job WHERE job_id = ?", ["job-dq"]
        ).fetchone()[0]
    assert status == "COMPLETED"
