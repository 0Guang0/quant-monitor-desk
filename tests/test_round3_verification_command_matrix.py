"""Round 3 验证命令矩阵与门禁测试可发现性。

覆盖范围：docs/ops/verification_commands.md 与 ROUND3 地图是否列出全部 gate 测试模块、
uv pytest 命令，并区分 staged-only 与 production-live、Batch 2.75 网络排除说明。
"""

from __future__ import annotations

from pathlib import Path

from tests.contract_gate_support import PROJECT_ROOT

VERIFICATION_COMMANDS = PROJECT_ROOT / "docs/ops/verification_commands.md"
ROUND3_MAP = PROJECT_ROOT / "ROUND3_BATCH_IMPLEMENTATION_MAP.md"

# Canonical Round 3 gate hygiene commands (PROMPT_05 + staged/live guards).
ROUND3_GATE_COMMANDS: tuple[tuple[str, str, str], ...] = (
    (
        "audit-trace-authority",
        "tests/test_trellis_audit_trace_authority.py",
        "uv run python -m pytest tests/test_trellis_audit_trace_authority.py -q",
    ),
    (
        "audit-registry-alignment",
        "tests/test_round3_audit_registry_alignment.py",
        "uv run python -m pytest tests/test_round3_audit_registry_alignment.py -q",
    ),
    (
        "unresolved-item-coverage",
        "tests/test_unresolved_item_task_coverage.py",
        "uv run python -m pytest tests/test_unresolved_item_task_coverage.py -q",
    ),
    (
        "batch25-staged-not-live",
        "tests/test_batch25_production_data_gate.py",
        "uv run python -m pytest tests/test_batch25_production_data_gate.py -q",
    ),
    (
        "production-live-pilot-policy",
        "tests/test_production_live_pilot_policy.py",
        "uv run python -m pytest tests/test_production_live_pilot_policy.py -q",
    ),
    (
        "batch3-staged-downstream-gate",
        "tests/test_batch3_staged_downstream_gate.py",
        "uv run python -m pytest tests/test_batch3_staged_downstream_gate.py -q",
    ),
    (
        "fred-staged-semantics",
        "tests/test_fred_staged_semantics.py",
        "uv run python -m pytest tests/test_fred_staged_semantics.py -q",
    ),
)

DOC_LINK_CHECK = "uv run python scripts/check_doc_links.py"

# Related Batch 2.75 pilot gate — includes @pytest.mark.network cases; not default CI.
BATCH275_PILOT_GATE_MODULE = "tests/test_batch275_live_pilot_gate.py"


def _read(path: Path) -> str:
    assert path.is_file(), f"missing expected document: {path}"
    return path.read_text(encoding="utf-8")


def test_round3GateTestModules_existOnDisk() -> None:
    """覆盖范围：Round 3 门禁测试模块在仓库里是否真实存在
    测试对象：ROUND3_GATE_COMMANDS 常量列出的各 test_*.py 文件
    目的/目标：运维文档里引用的门禁测试文件不能是死链
    验证点：每个 module 路径在 PROJECT_ROOT 下 is_file()
    失败含义：文档矩阵指向不存在的测试，合并协调人跑不通门禁
    """
    for _gate_id, module, _command in ROUND3_GATE_COMMANDS:
        assert (PROJECT_ROOT / module).is_file(), f"missing gate test module: {module}"


def test_verificationCommandsDoc_listsRound3GateMatrix() -> None:
    """覆盖范围：verification_commands.md 是否列出完整 Round 3 门禁命令矩阵
    测试对象：docs/ops/verification_commands.md
    目的/目标：一处文档能查到全部 gate id、测试模块与 uv pytest 命令
    验证点：含 ## Round 3 gate hygiene、check_doc_links 命令；每个 gate_id/module/command 三元组都在正文
    失败含义：运维找不到标准 pytest 命令，各批次门禁检查会各自为政
    """
    text = _read(VERIFICATION_COMMANDS)
    assert "## Round 3 gate hygiene" in text
    assert DOC_LINK_CHECK in text
    for gate_id, module, command in ROUND3_GATE_COMMANDS:
        assert gate_id in text, f"verification_commands.md missing gate id: {gate_id}"
        assert module in text, f"verification_commands.md missing module: {module}"
        assert command in text, f"verification_commands.md missing command for {gate_id}"


def test_verificationCommandsDoc_distinguishesStagedFromProductionLive() -> None:
    """覆盖范围：verification_commands.md 是否区分 staged-only 与 production-live 两类守卫
    测试对象：docs/ops/verification_commands.md 中的 staged/live 措辞
    目的/目标：读者不会把 staged 证据测试当成已开放线上拉数
    验证点：含 staged-only、production-live、does not open production-live 及四个代表性 test_*.py 文件名
    失败含义：文档混淆 staged 与 live，容易误判 Batch 2.5/2.75/3 数据就绪状态
    """
    text = _read(VERIFICATION_COMMANDS)
    for token in (
        "staged-only",
        "production-live",
        "does not open production-live",
        "test_batch25_production_data_gate.py",
        "test_batch3_staged_downstream_gate.py",
        "test_fred_staged_semantics.py",
        "test_production_live_pilot_policy.py",
    ):
        assert token in text, f"verification_commands.md missing staged/live token: {token}"


def test_verificationCommandsDoc_notesBatch275NetworkExclusion() -> None:
    """覆盖范围：verification_commands.md 对 Batch 2.75 网络测试的 CI 排除说明
    测试对象：docs/ops/verification_commands.md 中 test_batch275_live_pilot_gate.py 条目
    目的/目标：默认 Round 3 CI 不应误跑需外网的 live pilot 用例
    验证点：含 test_batch275_live_pilot_gate.py；正文说明 not default CI（或 not default Round 3 CI）且提到 network
    失败含义：文档未标注网络排除，CI 可能意外拉起外网 live fetch
    """
    text = _read(VERIFICATION_COMMANDS)
    assert BATCH275_PILOT_GATE_MODULE in text
    assert "not default CI" in text or "not default Round 3 CI" in text
    assert "network" in text.lower()


def test_round3BatchMap_pointsToVerificationCommandMatrix() -> None:
    """覆盖范围：ROUND3_BATCH_IMPLEMENTATION_MAP 是否指向 verification_commands 矩阵
    测试对象：ROUND3_BATCH_IMPLEMENTATION_MAP.md
    目的/目标：Batch 地图与运维命令索引互相可发现
    验证点：含 docs/ops/verification_commands.md；含 Round 3 gate hygiene 或 gate hygiene command matrix 措辞
    失败含义：地图缺命令矩阵链接，协调人只能从散落测试文件反查 pytest 命令
    """
    text = _read(ROUND3_MAP)
    assert "docs/ops/verification_commands.md" in text
    assert "Round 3 gate hygiene" in text or "gate hygiene command matrix" in text
