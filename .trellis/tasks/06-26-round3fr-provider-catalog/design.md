# R3FR-05 技术设计

## 1. 数据模型

### 1.1 Catalog 顶层

```yaml
version: provider_catalog_v1
updated_for: r3fr05_openbb_architecture_reference
rules:
  registry_alignment: every source_registry source_id must appear in exactly one provider entry
  schema_enum_alignment: source_type and license_type must match schema.sql CHECK
providers:
  - provider_id: ...
    source_ids: [...]
```

### 1.2 Provider 分组（25 provider · 1:1 单源为主）

| provider_id               | source_ids                  | status 初值              |
| ------------------------- | --------------------------- | ------------------------ |
| qmt_xtdata                | [qmt_xtdata]                | active                   |
| qmt_xqshare               | [qmt_xqshare]               | proposed_disabled_source |
| baostock                  | [baostock]                  | sandbox_candidate        |
| akshare                   | [akshare]                   | active                   |
| cninfo                    | [cninfo]                    | sandbox_candidate        |
| yahoo_finance             | [yahoo_finance]             | active（catalog SSOT；capability 无显式 status；posture 仍 validation_only + 默认关闭） |
| tdx_pytdx                 | [tdx_pytdx]                 | proposed_disabled_source |
| fred                      | [fred]                      | proposed_disabled_source |
| us_treasury … web_search  | 各单源                      | proposed_disabled_source |
| openbb_provider_reference | [openbb_provider_reference] | proposed_disabled_source |

规则：每个 `source_id` 出现在**恰好一个** provider entry。

### 1.3 状态枚举

| 字段                           | 含义                                                                                                                   |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------- |
| `production_default_candidate` | 未来可作生产默认候选                                                                                                   |
| `production_default_enabled`   | **当前**是否允许生产默认启用（canonical；R3G 文档 `production_default_allowed` 为措辞漂移，读取 catalog 时用 enabled） |
| `enabled_by_default`           | 须 ≤ registry 同名字段（更严允许）                                                                                     |

### 1.4 默认 posture

| 源组                       | enabled_by_default    | production_default_enabled | production_default_candidate |
| -------------------------- | --------------------- | -------------------------- | ---------------------------- |
| baostock, cninfo           | true（对齐 registry） | false                      | true                         |
| akshare                    | true                  | false                      | false                        |
| qmt/tdx/fred/外部 proposed | false                 | false                      | false                        |

### 1.5 catalog ↔ registry 字段映射

| catalog                       | registry                                | 规则                                                             |
| ----------------------------- | --------------------------------------- | ---------------------------------------------------------------- |
| `requires_user_authorization` | `requires_user_setup` / `auth_required` | catalog true 时 registry 须 requires_user_setup 或 auth_required |
| `requires_local_client`       | `requires_user_setup`（broker）         | qmt/tdx 为 true                                                  |
| `enabled_by_default`          | `enabled_by_default`                    | catalog 不得更松                                                 |
| `validation_only`             | `validation_only`                       | 须一致                                                           |

### 1.6 openbb_provider_reference（registry + capability）

- registry：见活卡 §9.2 YAML 模板
- capability：`status: proposed_disabled_source`，`domains: {}` 或空 operations（无 fetch）

## 2. 文件变更

| 文件                                                 | 动作                                |
| ---------------------------------------------------- | ----------------------------------- |
| `specs/datasource_registry/provider_catalog.yaml`    | **新建** SSOT                       |
| `specs/datasource_registry/source_registry.yaml`     | 补 2 行                             |
| `specs/datasource_registry/source_capabilities.yaml` | 补 openbb stub                      |
| `backend/app/datasources/provider_catalog.py`        | loader                              |
| `specs/contracts/source_capability_contract.yaml`    | `provider_catalog_path` 引用        |
| `specs/contracts/datasource_service_contract.yaml`   | catalog 路径引用                    |
| `specs/contracts/reference_adoption_guardrails.yaml` | `required_tests` + R3FR-05 closure  |
| `tests/test_provider_catalog.py`                     | **新建**（见 EXECUTION_INDEX §2）   |
| `tests/test_reference_adoption_guardrails.py`        | `test_r3fr05ProviderCatalogClosure` |
| `tests/test_catalog.yaml`                            | `loop_maintain.py --fix` 登记       |
| `specs/context/authority_graph.yaml`                 | 若 loop 报缺口则 `--fix`            |

## 3. Loader API

```python
def load_provider_catalog() -> dict: ...
def provider_for_source(source_id: str, catalog: dict | None = None) -> dict | None: ...
```

不在 `DataSourceService.fetch` 热路径调用。

## 4. OpenBB（architecture_only）

见 `reference_adoption_guardrails.yaml` → `openbb_provider_architecture`。

## 5. 兼容性

- R3G：`production_default_enabled` 为 canonical；下游读 catalog 时勿用 `production_default_allowed`
- 与 R3FR-03：合并前 rebase `source_registry.yaml`（playbook file lock）

## 6. 回滚

删除 catalog YAML、loader、新测试；还原 registry/capability 两行与 contract 增量。
