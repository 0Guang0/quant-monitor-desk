# Agent 派发 — 桶 OPS（Ops / CLI / Config / Security）

> **Worktree：** `debt/test-hygiene/bucket-ops-cli` from `master`  
> **Bucket ID：** OPS

## Allowed files

```
tests/test_ops_db_inspector.py
tests/test_ops_interface_probe.py
tests/test_interface_probe_018c.py
tests/test_data_cli_contract.py
tests/test_config.py
tests/test_config_templates.py
tests/test_dependency_extras_contract.py
tests/test_api_security_contract.py
tests/test_reference_adoption_guardrails.py
```

## 特殊注意

- ops probe 测试多依赖 subprocess/CLI：ponytail 勿删 fail-closed 边界
- `test_ops_db_inspector.py`、`test_ops_interface_probe.py`、`test_interface_probe_018c.py` 在 authority_graph
- `test_api_security_contract.py` 绑定 `specs/contracts/api_security_contract.yaml`

## 验证命令

```powershell
cd C:\Users\Guang\Desktop\quant-monitor-desk
uv run python -m pytest tests/test_ops_db_inspector.py tests/test_ops_interface_probe.py tests/test_interface_probe_018c.py tests/test_data_cli_contract.py tests/test_config.py tests/test_config_templates.py tests/test_dependency_extras_contract.py tests/test_api_security_contract.py tests/test_reference_adoption_guardrails.py -q --tb=short
```

## 证据

`.trellis/tasks/debt-test-hygiene-batch/execute-evidence/bucket-OPS-*`

## 公共约束

见 `_COMMON.md`。
