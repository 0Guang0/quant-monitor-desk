# GitNexus Audit 摘要 — Batch B

> **7.pre** · 2026-06-17 Audit 开场 · 主会话刷新

## 索引状态

- Execute 后索引：2605 nodes · 3386 edges · 33 flows（`research/gitnexus-execute-summary.md`）
- Audit 7.pre：`detect_changes({scope:"compare", base_ref:"master"})` · risk **HIGH**（12 changed files · 6 affected processes）
- 变更焦点：`tests/conftest.py` fixtures（`batch_b_registry` / `raw_data_root` / `file_registry_stack`）+ `backend/app/datasources/__init__.py` exports

## query — adapter skeleton 流

**query:** `SkeletonAdapterBase create_adapter adapter fetch`

| 符号 | 路径 | 角色 |
|------|------|------|
| `SkeletonAdapterBase` | `adapters/skeleton_base.py` | SUCCESS raw + FileRegistry + PortError 映射 |
| `create_adapter` | `adapters/__init__.py` | factory · callers = 2 测试 |
| `BaseDataAdapter.fetch` | `base_adapter.py` | 父类 fetch_log 写入 |
| 五 vendor adapter | `adapters/*.py` | 薄子类 |

## context — create_adapter

- **incoming calls:** `test_createAdapter_unknownSource_raises`, `test_createAdapter_defaultFetchPort_success`
- **outgoing:** 无（factory 内联实例化）
- **processes:** 空（skeleton 层尚未接入 orchestrator）

## detect_changes 受影响 processes

| Process | 变更符号 |
|---------|----------|
| File_registry_stack → _file_checksum | `file_registry_stack` |
| Batch_b_registry → _validate_domain_roles | `batch_b_registry` |
| File_registry_stack → Applied_versions | `file_registry_stack` |

## Audit 关注点（AUDIT.plan §2）

1. **F01/F02 偿还：** FileRegistry 对齐 · cninfo EMPTY_RESPONSE（对抗审计 remediation）
2. **无 WriteManager** in adapters/
3. **create_adapter** 仅测试调用 — 无 ghost 生产依赖
4. **audit-sandbox** 独立于 Execute `data/` 路径

## 7.pre complete
