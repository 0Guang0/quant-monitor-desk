"""Ops interface_probe + mutation_proof wiring tests (OP-06)."""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import duckdb
from backend.app.datasources.adapters.fetch_port import FetchPayload, StubFetchPort
from backend.app.db.migrate import apply_migrations
from backend.app.ops import interface_probe
from backend.app.ops.interface_probe import (
    PROBE_TARGETS,
    SIDECAR_SINA_OPERATION,
    capture_no_mutation_proof,
    run_interface_probe,
    run_single_probe,
)
from backend.app.ops.mutation_proof import key_table_row_counts


def _init_db(db_path: Path) -> None:
    con = duckdb.connect(str(db_path))
    apply_migrations(con)
    con.close()


def test_op06_interfaceProbeImportsMutationProofNotLivePilot() -> None:
    """覆盖范围：interface_probe 与 live_pilot 模块边界。

    测试对象：interface_probe 模块导入面。
    目的/目标：probe 经 mutation_proof 共享 key counts，不依赖 live_pilot 私有 API（OP-02/OP-06）。
    """
    source = inspect.getsource(interface_probe)
    assert "live_pilot" not in source
    assert "mutation_proof" in source


def test_op06_captureNoMutationProofUsesSharedKeyTableCounts(tmp_path: Path) -> None:
    """覆盖范围：probe 侧 no-mutation proof 与共享 mutation_proof 接线。

    测试对象：capture_no_mutation_proof / key_table_row_counts。
    目的/目标：探测前后 key table 计数一致且 zero_mutation 为真（OP-06）。
    """
    db = tmp_path / "probe.duckdb"
    _init_db(db)
    before = key_table_row_counts(db)
    proof = capture_no_mutation_proof(db, before_counts=before, before_bytes=db.read_bytes())

    assert proof["zero_mutation"] is True
    assert proof["db_hash_unchanged"] is True
    assert proof["before_key_table_counts"] == before
    assert proof["after_key_table_counts"] == before


def test_op06_runSingleProbe_defersNonDailyTdxOperations(tmp_path: Path) -> None:
    """覆盖范围：018C 有界 slice 内 TDX 非日线操作 defer 路径。

    测试对象：run_single_probe。
    目的/目标：security_list 等操作返回 DEFERRED 且不写 sandbox（OP-06）。
    """
    target = next(t for t in PROBE_TARGETS if t.operation == "fetch_security_list")
    record = run_single_probe(target, sandbox_root=tmp_path / "unused")

    assert record["status"] == "DEFERRED"
    assert "deferred" in record["failure_reason"].lower()


def test_op06_runSingleProbe_sinaSidecarWritesSandbox(tmp_path: Path) -> None:
    """覆盖范围：Sina sidecar 成功探测写 sandbox raw。

    测试对象：run_single_probe + StubFetchPort 注入。
    目的/目标：SUCCESS 记录含 sandbox_path 与 content_hash（OP-06）。
    """
    target = next(t for t in PROBE_TARGETS if t.operation == SIDECAR_SINA_OPERATION)
    sandbox = tmp_path / "sandbox"

    class OkPort:
        def fetch_payload(self, req):
            return FetchPayload(content=b'{"ok":true}', file_type="json", row_count=1)

    record = run_single_probe(target, sandbox_root=sandbox, fetch_port=OkPort())

    assert record["status"] == "SUCCESS"
    assert record["sandbox_path"]
    assert Path(record["sandbox_path"]).is_file()
    assert record["content_hash"]


def test_op06_runInterfaceProbe_writesMutationProofArtifact(tmp_path: Path, monkeypatch) -> None:
    """覆盖范围：run_interface_probe 证据流水线落盘。

    测试对象：run_interface_probe。
    目的/目标：写出 route/raw/decision/no_mutation 四类证据且 mutation_proof.zero_mutation（OP-06）。
    """
    monkeypatch.setattr(
        "backend.app.ops.interface_probe._resolve_fetch_port",
        lambda t: StubFetchPort(payload=b"{}"),
    )
    db = tmp_path / "db.duckdb"
    _init_db(db)
    before_bytes = db.read_bytes()
    ev = tmp_path / "evidence"
    sandbox = tmp_path / "sandbox"

    result = run_interface_probe(evidence_dir=ev, sandbox_root=sandbox, db_path=db)

    assert (ev / "interface_probe_route_matrix.json").is_file()
    assert (ev / "interface_probe_raw_evidence.json").is_file()
    assert (ev / "interface_probe_no_mutation_proof.md").is_file()
    assert (ev / "interface_probe_decision.md").is_file()
    assert result["mutation_proof"]["zero_mutation"] is True
    assert db.read_bytes() == before_bytes
    matrix = json.loads((ev / "interface_probe_route_matrix.json").read_text(encoding="utf-8"))
    assert matrix["routes"]
