# Privacy Data Flow

## 1. 目的

把用户手动导入文本、Agent 输入、前端本地工具页、证据保存之间的数据流显式化。默认 local-first / local-only，不上传外部服务。

## 2. 数据流模式

| 模式                | 默认持久化 |       进入 Agent log |   进入 evidence_chain |     用户确认 |
| ------------------- | ---------: | -------------------: | --------------------: | -----------: |
| local-only preview  |         否 |                   否 |                    否 |       不需要 |
| save as evidence    |         是 |   可引用 evidence_id |                    是 |         需要 |
| agent context input |    否/临时 | 可摘要但标 untrusted | 否，除非另存 evidence | 需要清晰提示 |

## 3. 必填字段

保存为 evidence 时必须记录：

```text
source_label
provenance_note
redaction_status
retention_policy
created_by
created_at
```

## 4. 禁止

1. 默认上传用户策略或文本。
2. 将用户输入直接写入 clean 表。
3. Agent 把未证据化用户输入当作事实。
4. 用导入文本生成买卖建议。

## 5. 契约

见 `specs/contracts/user_input_privacy_contract.yaml`。
