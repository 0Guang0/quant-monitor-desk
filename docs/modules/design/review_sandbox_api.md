# Review Sandbox API

## 1. 定位

Review Sandbox 是未来可选的只读策略/规则复盘兼容层。它只允许读取历史数据与记录复盘指标，不允许执行交易、自动登录、外部网络访问或任意导入。

## 2. 可借鉴与不可借鉴

| 来源                 | 可借鉴                         | 禁止                               |
| -------------------- | ------------------------------ | ---------------------------------- |
| JQ2PTrade MiniPTrade | API namespace / lifecycle 思路 | `compile/exec` 用户策略、order API |
| EasyXT               | 模块化边界                     | 真实交易、自动登录                 |
| ptqmt-site           | local-only disclosure          | 上传用户代码                       |

## 3. 权威契约

- `specs/contracts/review_sandbox_contract.yaml`
- `specs/contracts/reference_adoption_guardrails.yaml`
- `specs/contracts/user_input_privacy_contract.yaml`

## 4. 默认执行策略

1. 默认只做 AST 静态扫描。
2. 检测到 order-like API 直接返回 `action_semantics_violation`。
3. 禁止 `os/sys/subprocess/socket/requests` 等访问。
4. 不写 clean 表。
5. 不把复盘结果写成交易建议。

## 5. 验收

```bash
python -m pytest tests/test_review_sandbox_api.py tests/test_reference_adoption_guardrails.py -q
```

## ADR-017 冻结快照边界

Review Sandbox 读取连续监控数据时，冻结快照必须保留来源等级、质量等级、人工复核、RoutePlan 和
恢复替换关系；默认复盘仍读取可信最终库，审计归档区只可经明确审计选择进入，且不得去除风险标签。
