# Configuration, Secret, Masking, and Rotation Policy

## 1. 目的

修复 QM-AUD-007，并落实用户拍板 D-03：第一版采用 `.env.local` 作为本地 secret 存储方式；OS keyring 后续增强；云密钥服务不进入第一版。

## 2. 已拍板 Secret 存储方式（D-03）

```text
第一版：.env.local + .env.example + .gitignore + 启动检查 + secret scan
后续增强：OS keyring
第一版不采用：云密钥服务
```

## 3. 配置优先级

从高到低：

1. 进程环境变量。
2. 本机 `.env.local`（不得提交）。
3. `.env.example` 默认模板。
4. `configs/*.yaml` 非敏感配置。
5. 代码默认值。

## 4. Secret 文件规则

- 仓库只允许提交 `.env.example`。
- `.env.local`、`.env`、`*.secret`、`*.secret.*`、`*.key`、`credentials.*` 必须写入 `.gitignore`。
- `.env.example` 只能留空占位，不能填真实 key/token/password。
- `QMD_API_TOKEN`、数据源 token、SMTP password、Webhook secret 都属于 secret。
- prod 启动时必须检查必需 secret 是否存在；缺失必须拒绝启动。

## 5. 脱敏规则

日志、异常、报告、Agent 输出中必须 mask：

```text
token
cookie
authorization
password
api_key
secret
邮箱
手机号
本机绝对路径中的用户名片段
```

## 6. Secret Scan 与轮换

CI 必须加入 secret scan。推荐检查范围：

```text
.env.local/.env 是否被提交
常见 API key/token/password 正则
Authorization/Cookie 原文
私钥文件
```

如果 secret 泄露，必须执行：

1. 立即撤销旧 secret。
2. 生成新 secret。
3. 从本地 `.env.local` 替换。
4. 检查 Git 历史是否包含泄露值。
5. 写入 `security_incident_log` 或等价审计记录。

## 7. 轮换规则

| 类型                  | 默认轮换            | 触发轮换                 |
| --------------------- | ------------------- | ------------------------ |
| 本地 API Token        | 90 天               | 泄露、机器迁移、人员变更 |
| 数据源 API Key        | 90 天或按数据商规则 | 泄露、权限变更、额度异常 |
| 本机交易/行情终端凭据 | 用户手动            | 账号变更、机器迁移       |
| 邮件通知凭据          | 90 天               | 通知异常或误发           |

## 8. 测试要求

- `test_envExample_containsNoRealSecrets`
- `test_gitignore_blocksLocalEnvAndKeyFiles`
- `test_configPrecedence_envOverridesYaml`
- `test_prodMissingRequiredSecret_failsStartup`
- `test_logMasking_redactsSecretLikeValues`
- `test_emptyEnvPath_fallsBackToDefault`

## 9. 用户决策补充

D-03 已拍板：第一版使用 `.env.local`。执行角色不得擅自改成 OS keyring 或云密钥服务作为第一版强制依赖。

OS keyring 只作为后续增强项；云密钥服务与本地优先第一版冲突，不纳入第一版实现。
