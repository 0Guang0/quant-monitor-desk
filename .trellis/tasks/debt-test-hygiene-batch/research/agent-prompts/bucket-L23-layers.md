# Agent 派发 — 桶 L23（Layer2 / Layer3 / Lineage）

> **Worktree：** `debt/test-hygiene/bucket-l23-layers` from `master`  
> **Bucket ID：** L23

## Allowed files

```
tests/test_layer2_sensor_loader.py
tests/test_layer3_loader.py
tests/test_layer3_snapshot_builder.py
tests/test_snapshot_lineage_kernel.py
tests/test_layer5_evidence_foundation.py
tests/test_resource_guard.py
```

## 特殊注意

- **Phase B 重点桶**：loader/sensor 测试常慢；Phase A 时记录重复 tmp_path/DB 初始化，便于 Phase B 提 fixture scope（**禁止**删 ResourceGuard/lineage 边界断言）
- `test_resource_guard.py` 在 authority_graph 多处引用：禁止列入 deletion candidates
- `test_layer2_sensor_loader.py` 体量大：ponytail 优先合并重复 staged 路径 setup，不删 ResourceGuard 边界断言

## 验证命令

```powershell
cd C:\Users\Guang\Desktop\quant-monitor-desk
uv run python -m pytest tests/test_layer2_sensor_loader.py tests/test_layer3_loader.py tests/test_layer3_snapshot_builder.py tests/test_snapshot_lineage_kernel.py tests/test_layer5_evidence_foundation.py tests/test_resource_guard.py -q --tb=short
```

## 证据

`.trellis/tasks/debt-test-hygiene-batch/execute-evidence/bucket-L23-*`

## 公共约束

见 `_COMMON.md`。
