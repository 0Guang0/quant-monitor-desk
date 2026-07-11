# Source Capability Registry

## 1. 目的

`SourceRegistry` 负责 source、domain、role 与基础启用状态；管理员启用覆盖层给出当前有效启用状态；`SourceCapabilityRegistry` 负责更细的 operation、field、frequency、incremental/backfill/auth 能力。三者不得混为一层，避免稳定目录被运营状态或能力细节污染。

本设计吸收调研报告中 JQ2PTrade `api_mapping.json` 的 mapping-first 思路，但只用于本项目的数据源能力声明，不用于交易策略转换。

## 2. 权威文件

- `specs/datasource_registry/source_registry.yaml`：source/domain/role/基础启用状态权威；有效启用状态由受控覆盖层与其合成。
- `specs/datasource_registry/source_capabilities.yaml`：source/domain/operation/field 能力权威。
- `specs/contracts/source_capability_contract.yaml`：机器验收规则。

## 3. 核心规则

1. 每个 `source_registry.allowed_domains` 中的 domain 必须存在 capability 声明。
2. Adapter 的 `supported_domains` 必须是 capability registry 子集。
3. Orchestrator 或 DataSourceService 发起 fetch 前必须确认 capability 存在。
4. 未声明 capability 的 operation 不可调度。
5. Capability 不授予 fallback 权限；fallback 必须通过 `SourceRoutePlan` 显式记录。

## 4. 不负责

- 不决定最终主值。
- 不绕过 DataQualityValidator。
- 不启用 QMT / xqshare。
- 不描述交易、下单、自动登录能力。

## 5. 未来实现模块

```text
backend/app/datasources/capability_registry.py
```

建议接口：

```python
class SourceCapabilityRegistry:
    def load(self) -> None: ...
    def assert_source_domain_operation(self, source_id: str, domain: str, operation: str) -> None: ...
    def domains_for_source(self, source_id: str) -> frozenset[str]: ...
```

## 6. 验收

```bash
python -m pytest tests/test_source_capabilities.py tests/test_source_registry.py tests/test_adapter_skeletons.py -q
```

## ADR-017 补充：能力与启用覆盖层边界

`SourceRegistry` 维护基础登记与基础启用，管理员启用覆盖层维护当前有效启用状态；两者的合成结果才是路由可见的有效状态。Capability 仍只回答“是否支持该 source/domain/operation/frequency/auth 组合”，不能因为能力存在而自动获得 fallback 权限。RoutePlan 仅能从同时满足登记、有效启用、能力、授权、平台与领域固定优先级的候选中选择来源，并须把 capability/覆盖层版本写入血缘。
