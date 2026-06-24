# Agent 派发 — 桶 DS（DataSource / Adapter / Sync / E2E）

> **Worktree：** `debt/test-hygiene/bucket-ds-sync` from `master`  
> **Bucket ID：** DS

## Allowed files

```
tests/test_datasource_service.py
tests/test_source_registry.py
tests/test_source_route_planner.py
tests/test_source_capabilities.py
tests/test_platform_source_matrix.py
tests/test_r3x_data_source_routing_blockers.py
tests/test_data_adapter_contract.py
tests/test_adapter_skeletons.py
tests/test_sync_orchestrator.py
tests/test_sync_jobs.py
tests/test_sync_pipeline_contract.py
tests/test_sync_migration.py
tests/test_batch_d_orchestration_flow.py
tests/test_vendor_fetch_e2e.py
tests/test_tdx_live_manual_probe_authorization.py
```

可编辑（需 MERGE-C 知悉）：`tests/service_path_support.py`

## 特殊注意

- `test_vendor_fetch_e2e.py`、`test_tdx_live_manual_probe_authorization.py` 可能含 network/live 语义：**禁止**为速度 mock 网络或删 live 用例；保持 `@pytest.mark.network` 与 `--run-network` skip 行为
- `test_r3x_data_source_routing_blockers.py` 在 authority_graph：禁止 deletion
- sync 与 datasource 测试间 helper 重复多：ponytail 优先提取到 **本桶内** 私有 helper（同文件底部），不要新建跨桶 util 文件
- **§1.1：** 注释要求真实 vendor/sync/E2E 路径的用例，Phase B 只能优化 setup/teardown，不得等价替换为 unit mock

## 验证命令

```powershell
cd C:\Users\Guang\Desktop\quant-monitor-desk
uv run python -m pytest tests/test_datasource_service.py tests/test_source_registry.py tests/test_source_route_planner.py tests/test_source_capabilities.py tests/test_platform_source_matrix.py tests/test_r3x_data_source_routing_blockers.py tests/test_data_adapter_contract.py tests/test_adapter_skeletons.py tests/test_sync_orchestrator.py tests/test_sync_jobs.py tests/test_sync_pipeline_contract.py tests/test_sync_migration.py tests/test_batch_d_orchestration_flow.py tests/test_vendor_fetch_e2e.py tests/test_tdx_live_manual_probe_authorization.py -q --tb=short
```

## 证据

`.trellis/tasks/debt-test-hygiene-batch/execute-evidence/bucket-DS-*`

## 公共约束

见 `_COMMON.md`。
