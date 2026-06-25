"""Round 3G R3G-03 limited production clean-write 入口契约门禁。"""

from __future__ import annotations

from tests.contract_gate_support import PROJECT_ROOT, load_yaml

CONTRACT = PROJECT_ROOT / "specs/contracts/sandbox_clean_write_contract.yaml"


def _contract() -> dict:
    return load_yaml(CONTRACT)


def test_r3g03Contract_requiresExplicitUserApproval() -> None:
    """覆盖范围：R3G-03 limited entry 人工审批门
    测试对象：r3g03_limited_entry.explicit_user_approval_required
    目的/目标：有限生产 clean-write 必须显式用户批准，禁止 agent 代签
    验证点：explicit_user_approval_required 为 true
    失败含义：无人工批准门会导致自动化路径误触发生产写
    """
    entry = _contract()["r3g03_limited_entry"]
    assert entry["explicit_user_approval_required"] is True
    assert entry["before_after_proof_required"] is True


def test_r3g03Contract_blocksAgentTriggeredWrite() -> None:
    """覆盖范围：R3G-03 block_if 对 agent 触发写路径的拒绝
    测试对象：r3g03_limited_entry.block_if
    目的/目标：limited entry 必须 fail-closed 拒绝 agent 触发的写路径
    验证点：block_if 含 agent_triggered_write_path
    失败含义：agent 可能绕过 WriteManager 与用户审批链
    """
    block_if = set(_contract()["r3g03_limited_entry"]["block_if"])
    assert "agent_triggered_write_path" in block_if
    assert "cap_expansion" in block_if


def test_r3g03CandidateCaps_boundFredAuthorization() -> None:
    """覆盖范围：R3G-03 candidate_caps 对 FRED 授权与默认禁用
    测试对象：candidate_caps.fred
    目的/目标：宏观序列候选须保持 disabled-by-default 且要求用户授权
    验证点：requires_user_authorization 与 enabled_by_default 符合 registry 语义
    失败含义：FRED 可能在未授权时被 3G 路径误选为默认源
    """
    fred = _contract()["candidate_caps"]["fred"]
    assert fred["requires_user_authorization"] is True
    assert fred["enabled_by_default"] is False
    assert "macro_series" in fred["allowed_domains"]
