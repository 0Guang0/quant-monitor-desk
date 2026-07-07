"""ResourceGuard 资源守护（Round 1 task 006）：阈值评估、日志与快照缓存。"""

from __future__ import annotations

import duckdb
import pytest
from backend.app.core.resource_guard import (
    Decision,
    ResourceGuard,
    ResourceSnapshot,
    evaluate,
    format_pause_event,
)
from backend.app.db.migrate import apply_migrations

THRESH = {
    "profiles": {
        "eco": {
            "process_rss_warn_mb": 800,
            "process_rss_pause_mb": 1200,
            "process_rss_hard_stop_mb": 1800,
            "duckdb_temp_max_gb": 2,
        },
    },
    "system_thresholds": {
        "available_memory_warn_gb": 4,
        "available_memory_pause_gb": 2,
        "available_memory_hard_stop_gb": 1,
        "system_memory_usage_warn_pct": 70,
        "system_memory_usage_pause_pct": 80,
        "system_memory_usage_hard_stop_pct": 90,
        "disk_free_warn_gb": 30,
        "disk_free_pause_gb": 20,
        "disk_free_hard_stop_gb": 10,
        "system_disk_usage_warn_pct": 75,
        "system_disk_usage_pause_pct": 85,
        "system_disk_usage_hard_stop_pct": 92,
    },
    "project_size_thresholds": {
        "project_warn_gb": 15,
        "project_pause_gb": 25,
        "project_hard_stop_gb": 40,
        "cache_warn_gb": 1,
        "cache_pause_gb": 2,
        "cache_hard_stop_gb": 4,
    },
}


def _memory_guard(monkeypatch, **snap_overrides) -> tuple[ResourceGuard, duckdb.DuckDBPyConnection]:
    con = duckdb.connect(":memory:")
    apply_migrations(con)
    guard = ResourceGuard(profile="eco", con=con)
    snap = _snap(**snap_overrides)
    monkeypatch.setattr(guard, "snapshot", lambda: snap)
    return guard, con


def _snap(**overrides) -> ResourceSnapshot:
    defaults = {
        "available_memory_gb": 8,
        "disk_free_gb": 100,
        "process_rss_mb": 300,
        "project_size_gb": 1,
        "duckdb_temp_size_gb": 0.1,
        "cache_size_gb": 0.1,
        "system_memory_usage_pct": 50.0,
        "system_disk_usage_pct": 50.0,
    }
    defaults.update(overrides)
    return ResourceSnapshot(**defaults)


def test_evaluate_healthyResources_returnsOk() -> None:
    """覆盖范围：evaluate 在健康指标下的决策
    测试对象：evaluate(ResourceSnapshot, THRESH)
    目的/目标：各指标均在 warn 以下时应返回 OK
    验证点：decision == Decision.OK
    失败含义：正常环境误报暂停/硬停，编排被不必要阻断
    """
    snap = _snap()
    decision, _ = evaluate(snap, THRESH)
    assert decision == Decision.OK


@pytest.mark.parametrize(
    "snap_overrides,reason_substr",
    (
        ({"available_memory_gb": 1.5}, "memory"),
        ({"project_size_gb": 30}, "project"),
        ({"system_memory_usage_pct": 85.0}, "memory usage"),
        ({"cache_size_gb": 2.5}, "cache"),
        ({"cache_size_gb": 3.0}, "cache"),
    ),
)
def test_evaluate_pauseThresholds_returnsPause(
    snap_overrides: dict, reason_substr: str
) -> None:
    """覆盖范围：evaluate 多类指标超 pause 阈值（参数化）
    测试对象：evaluate 对 memory/project/cache/system usage
    目的/目标：各类 pause 边界应返回 PAUSE 且 reason 含对应关键词
    验证点：decision=PAUSE；reason 含 reason_substr
    失败含义：某类资源压力不触发暂停，编排保护缺口
    """
    snap = _snap(**snap_overrides)
    decision, reason = evaluate(snap, THRESH)
    assert decision == Decision.PAUSE
    assert reason_substr in reason.lower()


def test_evaluate_criticalDisk_returnsHardStop() -> None:
    """覆盖范围：磁盘剩余空间低于 hard_stop
    测试对象：evaluate 对 disk_free_gb
    目的/目标：磁盘危急时应 HARD_STOP
    验证点：decision == Decision.HARD_STOP
    失败含义：磁盘将满仍允许写入，数据损坏风险
    """
    snap = _snap(disk_free_gb=5)
    decision, _ = evaluate(snap, THRESH)
    assert decision == Decision.HARD_STOP


def test_evaluate_multipleSignals_picksMostSevere() -> None:
    """覆盖范围：多指标同时超阈时的严重度合并
    测试对象：evaluate 多信号输入
    目的/目标：须取最严重决策（WARN < PAUSE < HARD_STOP）
    验证点：内存 warn + 磁盘 hard_stop → HARD_STOP
    失败含义：多信号时降级为较轻决策，保护不足
    """
    snap = _snap(available_memory_gb=3.5, disk_free_gb=5)
    decision, _ = evaluate(snap, THRESH)
    assert decision == Decision.HARD_STOP


def test_evaluate_warnMemory_returnsWarn() -> None:
    """覆盖范围：可用内存处于 warn 区间
    测试对象：evaluate 对 available_memory_gb=3.5
    目的/目标：介于 warn 与 pause 之间应 WARN
    验证点：decision=WARN；reason 含 memory
    失败含义：预警区间被忽略，无法提前限流
    """
    snap = _snap(available_memory_gb=3.5)
    decision, reason = evaluate(snap, THRESH)
    assert decision == Decision.WARN
    assert "memory" in reason.lower()


def test_evaluate_rssAboveWarnNotPause_returnsWarn() -> None:
    """覆盖范围：进程 RSS 处于 warn 但未达 pause
    测试对象：evaluate 对 process_rss_mb（eco profile）
    目的/目标：RSS 超 warn 线应 WARN 而非误报 PAUSE
    验证点：decision=WARN；reason 含 rss
    失败含义：RSS 预警与暂停边界混淆，限流过激或不足
    """
    eco = THRESH["profiles"]["eco"]
    snap = _snap(process_rss_mb=eco["process_rss_pause_mb"] - 1)
    decision, reason = evaluate(snap, THRESH, eco)
    assert decision == Decision.WARN
    assert "rss" in reason.lower()


def test_evaluate_memoryExactlyAtHardStopThreshold_isPause() -> None:
    """覆盖范围：可用内存恰在 hard_stop 边界
    测试对象：evaluate available_memory_gb=1.0
    目的/目标：边界值应按 pause 处理（非 hard_stop 以下才 hard_stop）
    验证点：decision == Decision.PAUSE
    失败含义：边界语义错误，1GB 可用内存决策与合约不符
    """
    snap = _snap(available_memory_gb=1.0)
    decision, _ = evaluate(snap, THRESH)
    assert decision == Decision.PAUSE


def test_evaluate_diskFreeExactlyAtWarnThreshold_isOk() -> None:
    """覆盖范围：磁盘剩余恰在 warn 线
    测试对象：evaluate disk_free_gb=30.0
    目的/目标：等于 warn 阈值时尚未触发 warn，应 OK
    验证点：decision == Decision.OK
    失败含义：边界 off-by-one，30GB 空闲误报 warn
    """
    snap = _snap(disk_free_gb=30.0)
    decision, _ = evaluate(snap, THRESH)
    assert decision == Decision.OK


def test_evaluate_duckdbTempAboveHardStop_returnsHardStop() -> None:
    """覆盖范围：DuckDB 临时文件超 profile 上限 105%
    测试对象：evaluate duckdb_temp_size_gb（eco）
    目的/目标：temp 严重超标应 HARD_STOP
    验证点：decision=HARD_STOP；reason 含 temp
    失败含义：超大 temp 仍继续查询，磁盘可能被写满
    """
    eco = THRESH["profiles"]["eco"]
    temp_max = eco["duckdb_temp_max_gb"]
    snap = _snap(duckdb_temp_size_gb=temp_max * 1.05)
    decision, reason = evaluate(snap, THRESH, eco)
    assert decision == Decision.HARD_STOP
    assert "temp" in reason.lower()


def test_evaluate_duckdbTempAboveMax_returnsPause() -> None:
    """覆盖范围：DuckDB temp 达上限 90% 但未 hard_stop
    测试对象：evaluate duckdb_temp_size_gb（eco）
    目的/目标：接近 temp 上限应 PAUSE
    验证点：decision=PAUSE；reason 含 temp
    失败含义：temp 预警缺失，查询在中等压力下仍全速
    """
    eco = THRESH["profiles"]["eco"]
    temp_max = eco["duckdb_temp_max_gb"]
    snap = _snap(duckdb_temp_size_gb=temp_max * 0.9)
    decision, reason = evaluate(snap, THRESH, eco)
    assert decision == Decision.PAUSE
    assert "temp" in reason.lower()


def test_evaluate_systemDiskUsageAboveHardStop_returnsHardStop() -> None:
    """覆盖范围：系统磁盘使用率超 hard_stop
    测试对象：evaluate system_disk_usage_pct=95
    目的/目标：整机磁盘告急应 HARD_STOP
    验证点：decision=HARD_STOP；reason 含 disk usage
    失败含义：磁盘几乎满仍写库，数据与日志可能损坏
    """
    snap = _snap(system_disk_usage_pct=95.0)
    decision, reason = evaluate(snap, THRESH)
    assert decision == Decision.HARD_STOP
    assert "disk usage" in reason.lower()


def test_formatPauseEvent_includesSentinelAndMetrics() -> None:
    """覆盖范围：format_pause_event 结构化日志行
    测试对象：format_pause_event(Decision.PAUSE, reason, snap, profile)
    目的/目标：暂停事件须含 RESOURCE_GUARD_PAUSED 哨兵与关键指标
    验证点：以 RESOURCE_GUARD_PAUSED 开头；含 available_memory_gb 与 profile=eco
    失败含义：编排层无法解析暂停日志，自动化告警失效
    """
    snap = _snap(
        available_memory_gb=1.5,
        disk_free_gb=15.0,
        process_rss_mb=900.0,
        project_size_gb=2.0,
    )
    msg = format_pause_event(Decision.PAUSE, "available memory below threshold", snap, "eco")
    assert msg.startswith("RESOURCE_GUARD_PAUSED")
    assert "available_memory_gb=1.50" in msg
    assert "profile=eco" in msg


def test_check_okDecision_doesNotWriteGuardLog(monkeypatch, capsys) -> None:
    """覆盖范围：ResourceGuard.check OK 路径副作用
    测试对象：ResourceGuard.check + resource_guard_log
    目的/目标：OK 时不写 DB 日志、不向 stderr 打 PAUSED 哨兵
    验证点：decision=OK；log 0 行；stderr 无 RESOURCE_GUARD_PAUSED
    失败含义：健康检查污染日志与 stderr，运维噪声过大
    """
    guard, con = _memory_guard(monkeypatch)
    decision, _ = guard.check()
    assert decision == Decision.OK
    rows = con.execute("SELECT COUNT(*) FROM resource_guard_log").fetchone()[0]
    assert rows == 0
    assert "RESOURCE_GUARD_PAUSED" not in capsys.readouterr().err


def test_check_lowMemorySnapshot_writesExtendedGuardLogColumns(monkeypatch) -> None:
    """覆盖范围：resource_guard_log 扩展列持久化
    测试对象：ResourceGuard.check 低内存快照
    目的/目标：PAUSE 时须写入 system_memory/disk、cache、duckdb_temp 等扩展列
    验证点：log 行中四列等于注入快照值
    失败含义：审计库缺少扩展指标，事后无法复盘资源状态
    """
    guard, con = _memory_guard(
        monkeypatch,
        available_memory_gb=1.5,
        system_memory_usage_pct=88.0,
        system_disk_usage_pct=80.0,
        cache_size_gb=2.5,
        duckdb_temp_size_gb=1.8,
    )
    guard.check()
    row = con.execute(
        """
        SELECT system_memory_usage_pct, system_disk_usage_pct,
               cache_size_gb, duckdb_temp_size_gb
        FROM resource_guard_log
        """
    ).fetchone()
    assert row[0] == 88.0
    assert row[1] == 80.0
    assert row[2] == 2.5
    assert row[3] == 1.8


def test_check_lowMemorySnapshot_writesGuardLog(monkeypatch, capsys) -> None:
    """覆盖范围：ResourceGuard.check PAUSE 路径
    测试对象：ResourceGuard.check 低可用内存
    目的/目标：PAUSE 须写 1 条 guard_log 并向 stderr 打哨兵
    验证点：decision=PAUSE；log 1 行；stderr 含 RESOURCE_GUARD_PAUSED
    失败含义：暂停无日志无 stderr，编排层不知道被限流
    """
    guard, con = _memory_guard(monkeypatch, available_memory_gb=1.5)
    decision, _ = guard.check()
    assert decision == Decision.PAUSE
    rows = con.execute("SELECT COUNT(*) FROM resource_guard_log").fetchone()[0]
    assert rows == 1
    assert "RESOURCE_GUARD_PAUSED" in capsys.readouterr().err


def test_check_hardStopDecision_writesGuardLog(monkeypatch, capsys) -> None:
    """覆盖范围：ResourceGuard.check HARD_STOP 路径
    测试对象：ResourceGuard.check 极低可用内存
    目的/目标：HARD_STOP 须记 log 且 decision 字段为 HARD_STOP
    验证点：decision=HARD_STOP；log decision=HARD_STOP；stderr 有哨兵
    失败含义：硬停无持久记录，无法审计为何拒绝任务
    """
    guard, con = _memory_guard(monkeypatch, available_memory_gb=0.5)
    decision, _ = guard.check()
    assert decision == Decision.HARD_STOP
    row = con.execute("SELECT decision FROM resource_guard_log").fetchone()
    assert row[0] == "HARD_STOP"
    assert "RESOURCE_GUARD_PAUSED" in capsys.readouterr().err


def test_check_warnDecision_writesGuardLog(monkeypatch, capsys) -> None:
    """覆盖范围：ResourceGuard.check WARN 路径
    测试对象：ResourceGuard.check 内存 warn 区间
    目的/目标：WARN 须写 log 但 stderr 不打 PAUSED 哨兵
    验证点：decision=WARN；log 1 行 decision=WARN；stderr 无 PAUSED
    失败含义：预警不写库或误打暂停哨兵，监控语义混乱
    """
    guard, con = _memory_guard(monkeypatch, available_memory_gb=3.5)
    decision, _ = guard.check()
    assert decision == Decision.WARN
    rows = con.execute("SELECT COUNT(*) FROM resource_guard_log").fetchone()[0]
    assert rows == 1
    row = con.execute("SELECT decision FROM resource_guard_log").fetchone()
    assert row[0] == "WARN"
    assert "RESOURCE_GUARD_PAUSED" not in capsys.readouterr().err


@pytest.mark.slow
def test_snapshot_realCall_returnsFiniteMetrics() -> None:
    """覆盖范围：ResourceGuard.snapshot 真实环境调用
    测试对象：ResourceGuard().snapshot()
    目的/目标：真实 psutil/磁盘扫描不得抛异常且指标为有限非负浮点
    验证点：memory/disk/rss/project_size 均 ≥0 且为有限 float；cache/temp 字段类型正确
    失败含义：生产环境 snapshot 崩溃或返回 NaN，编排前置检查失败
    """
    snap = ResourceGuard().snapshot()
    for field in (
        snap.available_memory_gb,
        snap.disk_free_gb,
        snap.process_rss_mb,
        snap.project_size_gb,
        snap.cache_size_gb,
        snap.duckdb_temp_size_gb,
    ):
        assert isinstance(field, (int, float))
        assert field >= 0
        assert field == field  # NaN guard


def test_resourceSnapshot_negativeValue_raises() -> None:
    """覆盖范围：ResourceSnapshot 构造校验
    测试对象：ResourceSnapshot(-1, ...)
    目的/目标：负的可用内存等非法指标须在构造时拒绝
    验证点：pytest.raises(ValueError, match=available_memory_gb)
    失败含义：非法快照可流入 evaluate，决策不可信
    """
    with pytest.raises(ValueError, match="available_memory_gb"):
        ResourceSnapshot(-1, 1, 1, 1)
