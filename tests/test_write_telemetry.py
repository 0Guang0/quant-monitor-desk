"""WriteManager stderr telemetry tests."""

from __future__ import annotations

import json

import pytest
from backend.app.db.write_telemetry import emit_write_telemetry


def test_emitWriteTelemetry_writesAllowlistedJsonLine(capsys) -> None:
    """覆盖范围：写入成功 stderr 事件
    测试对象：emit_write_telemetry
    目的/目标：脚本可 grep 一行 JSON 获知写入成败与 run_id
    验证点：stderr 一行 JSON；含 event/write_id/run_id；无 error_message
    失败含义：运维只能连库查审计，本地批处理无可机读信号
    """
    emit_write_telemetry(
        {
            "event": "write_completed",
            "run_id": "cli-sync-abc",
            "write_id": "wid-1",
            "job_id": "job-1",
            "status": "SUCCESS",
            "rows_inserted": 2,
            "secret": "must-not-appear",
            "error_message": "also dropped",
        }
    )
    err = capsys.readouterr().err.strip()
    payload = json.loads(err)
    assert payload["event"] == "write_completed"
    assert payload["run_id"] == "cli-sync-abc"
    assert payload["write_id"] == "wid-1"
    assert "secret" not in payload
    assert "error_message" not in payload


def test_emitWriteTelemetry_disabledByEnv(monkeypatch, capsys) -> None:
    """覆盖范围：遥测可关闭
    测试对象：emit_write_telemetry + QMD_WRITE_TELEMETRY=0
    目的/目标：测试套件与安静模式不应污染 stderr
    验证点：stderr 为空
    失败含义：无法在无噪声环境下跑批量测试
    """
    monkeypatch.setenv("QMD_WRITE_TELEMETRY", "0")
    emit_write_telemetry({"event": "write_failed", "run_id": "r1", "write_id": "w1"})
    assert capsys.readouterr().err == ""
