# R3FR-05: Provider Catalog（OpenBB 架构参考）

## 目标

把 provider 元数据升级为 **QMD 机器可读 catalog 契约**（OpenBB 仅 architecture_only）。

## 验收标准（AC）

| ID   | 可验证结果                                                                                               |
| ---- | -------------------------------------------------------------------------------------------------------- |
| AC-1 | `provider_catalog.yaml` 覆盖 registry **25** 源（23 现有 + `qmt_xqshare` + `openbb_provider_reference`） |
| AC-2 | 必填字段 + schema CHECK enum 对齐                                                                        |
| AC-3 | `production_default_candidate` ≠ `production_default_enabled`；外部 proposed 源 production enabled false |
| AC-4 | fred / TDX / QMT / xqshare posture                                                                       |
| AC-5 | 无 OpenBB runtime copy；`test_r3fr05ProviderCatalogClosure`                                              |
| AC-6 | `test_provider_catalog.py` + 相关套件 + **全库 pytest** 绿                                               |
| AC-7 | 两 contract 引用 catalog 路径；`loop_maintain.py --fix` 绿                                               |

## 证据命令

```bash
uv run pytest tests/test_provider_catalog.py tests/test_source_capabilities.py tests/test_reference_adoption_guardrails.py tests/test_source_registry.py -q
uv run pytest -q
uv run python scripts/loop_maintain.py --fix
```

## 协调

- **分支**：`feature/round3fr-provider-catalog`
- **与 R3FR-03**：`source_registry.yaml` 共享锁；本任务合并前须 rebase 协调（playbook §2）
- **与 R3FR-07**：避免并发大改 `reference_adoption_guardrails.yaml`
- **优先级**：P1（R3G 依赖 catalog posture）
