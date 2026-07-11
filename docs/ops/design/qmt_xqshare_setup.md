# QMT xqshare 可选配置

## 1. 定位

`qmt_xqshare` 是拟新增的可选远程 QMT 源。它只在用户明确配置远程 QMT 授权后才可调度。

## 2. 必需配置

```text
XQSHARE_REMOTE_HOST
XQSHARE_REMOTE_PORT
```

未来如需凭证，必须放在 `.env.local` 或用户确认的本地 secret 机制中，不得提交到仓库。

## 3. 禁止

1. 不自动探测远程端口。
2. 不自动登录 QMT。
3. 不处理验证码。
4. 不默认启用。
5. 不 silent fallback 到 qmt_xqshare。

## 4. 路由表现

缺 env 或缺用户授权时，`SourceRoutePlan` 必须返回：

```text
route_status=USER_AUTH_REQUIRED
selected_source_id=null
disabled_reason=missing_xqshare_env_or_user_authorization
```

## 5. 契约

- `specs/contracts/platform_source_matrix.yaml`
- `specs/contracts/source_route_contract.yaml`
- `specs/datasource_registry/source_capabilities.yaml`

## ADR-017 补充

即使管理员覆盖层启用，`qmt_xqshare` 仍必须满足本文件的 env、用户授权和平台矩阵前置条件；
自动 fallback 不得自动设置 env、探测端口或绕过任何前置条件。获准的 fallback 需完整记录来源、
失败原因、RoutePlan 与 `DEGRADED` 标签。
