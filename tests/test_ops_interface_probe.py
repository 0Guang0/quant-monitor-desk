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
    """覆盖范围：018C 接口探针与 live pilot 的模块边界
    测试对象：backend.app.ops.interface_probe 源码导入
    目的/目标：探针应共用「库未被改动」的计数逻辑，不得偷偷依赖实盘试点私有代码
    验证点：源码中无 live_pilot 字符串；含 mutation_proof
    失败含义：探针与实盘试点代码缠在一起，边界审计无法证明「只读探测」
    """
    source = inspect.getsource(interface_probe)
    assert "live_pilot" not in source
    assert "mutation_proof" in source


def test_op06_captureNoMutationProofUsesSharedKeyTableCounts(tmp_path: Path) -> None:
    """覆盖范围：单次探针前后的生产库 key 表行数证明
    测试对象：capture_no_mutation_proof、key_table_row_counts
    目的/目标：探测前后关键表行数与数据库文件指纹都不变，才能声称未改动生产库
    验证点：zero_mutation 与 db_hash_unchanged 为真；前后 key_table_counts 相同
    失败含义：探针悄悄改了库，no-mutation 证据不可信
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
    """覆盖范围：TDX 非日线类操作在 018C 有界切片内 defer
    测试对象：run_single_probe（fetch_security_list 目标）
    目的/目标：超出授权范围的操作应标记为延期执行，且不写入沙箱证据
    验证点：status==DEFERRED；failure_reason 含 deferred
    失败含义：未授权操作被当成成功探测，扩大接口探针的攻击面
    """
    target = next(t for t in PROBE_TARGETS if t.operation == "fetch_security_list")
    record = run_single_probe(target, sandbox_root=tmp_path / "unused")

    assert record["status"] == "DEFERRED"
    assert "deferred" in record["failure_reason"].lower()


def test_op06_runSingleProbe_sinaSidecarWritesSandbox(tmp_path: Path) -> None:
    """覆盖范围：Sina sidecar 成功路径写 sandbox raw
    测试对象：run_single_probe + 注入 OkPort
    目的/目标：探测成功时必须把原始响应落到沙箱并记录内容指纹
    验证点：status==SUCCESS；sandbox_path 指向真实文件；content_hash 非空
    失败含义：声称探测成功却无原始证据，接口探针审计链断裂
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
    """覆盖范围：完整 interface_probe 证据流水线落盘
    测试对象：run_interface_probe
    目的/目标：一次完整探测须产出路由、原始响应、决策与无改动四类证据，且数据库文件字节不变
    验证点：四个证据文件存在；mutation_proof.zero_mutation；DB 文件字节前后一致
    失败含义：缺任一证据或库被改写，接口探针无法通过审计签收
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
