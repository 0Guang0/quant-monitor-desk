# Agent 派发 — 桶 G（Gate / Policy / Round3）

> **派发时机：** 用户确认 DEBT.plan.md 后  
> **Worktree：** `debt/test-hygiene/bucket-g-gate` from `master`  
> **Bucket ID：** G

## 角色

你是 **agent-G**，负责 Round 3 门禁与 policy-contract 类测试的 Phase A 对齐与 ponytail 重构。

## Allowed files（仅可编辑）

```
tests/test_batch3_staged_downstream_gate.py
tests/test_batch25_production_data_gate.py
tests/test_batch275_live_pilot_gate.py
tests/test_production_live_pilot_policy.py
tests/test_fred_staged_semantics.py
tests/test_round3_audit_registry_alignment.py
tests/test_round3_verification_command_matrix.py
tests/test_trellis_audit_trace_authority.py
tests/test_unresolved_item_task_coverage.py
tests/test_global_execution_rules.py
tests/test_staged_pilot.py
tests/test_production_gate.py
tests/test_manifest_protocol.py
```

只读：`tests/contract_gate_support.py`

## 特殊注意

- 本桶 **全部模块在禁止删清单内**；`deletion-candidates.yaml` 应写 `candidates: []`
- `test_batch275_live_pilot_gate.py` 含 `@pytest.mark.network`：**禁止**为性能 mock 掉 live fetch 或删除 network 用例；优化时不要破坏默认 `-m "not network"` 与 `--run-network` 门控
- policy-contract 测试多为读文件/扫字符串；ponytail 重点在**去重复扫描**、合并同类 parametrize，勿削弱断言
- `test_round3_verification_command_matrix.py` 与 `docs/ops/verification_commands.md` 强绑定：改代码时确保矩阵仍覆盖 §3.1 全部 gate 模块

## 验证命令

```powershell
cd C:\Users\Guang\Desktop\quant-monitor-desk
uv run python -m pytest tests/test_batch3_staged_downstream_gate.py tests/test_batch25_production_data_gate.py tests/test_batch275_live_pilot_gate.py tests/test_production_live_pilot_policy.py tests/test_fred_staged_semantics.py tests/test_round3_audit_registry_alignment.py tests/test_round3_verification_command_matrix.py tests/test_trellis_audit_trace_authority.py tests/test_unresolved_item_task_coverage.py tests/test_global_execution_rules.py tests/test_staged_pilot.py tests/test_production_gate.py tests/test_manifest_protocol.py -q --tb=short
```

网络用例子集（可选 smoke，非 merge gate 必须）：

```powershell
uv run python -m pytest tests/test_batch275_live_pilot_gate.py -q -m "not network"
```

## 证据路径

`.trellis/tasks/debt-test-hygiene-batch/execute-evidence/bucket-G-*`

## 公共约束

见同目录 `_COMMON.md`。
