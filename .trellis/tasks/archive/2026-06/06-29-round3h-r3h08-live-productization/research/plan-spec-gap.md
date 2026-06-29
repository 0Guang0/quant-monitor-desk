# Plan Spec Gap — R3H-08

## Intent

24 源 env-gated 产品 live，Tier A/B/C，经 DataSourceService。

## Inputs

- `FetchRequest` + env `QMD_ALLOW_LIVE_FETCH`
- registry `validation_only` / role

## Outputs

- `FetchResult` + tier 路由决策
- raw paths；Tier A/B 可选 staging（本票 bounded）

## Boundaries Always

- Service 金路径 · ResourceGuard · 五字段测 · 全量 pytest

## Boundaries Never

- Rehearsal 冒充产品 · silent fallback · runtime 参考树 · canonical main silent write（Tier B）

## Errors

fail-closed：`LIVE_FETCH_REJECTED` · `USER_AUTH_REQUIRED` · `PRODUCTION_DB_PATH_REJECTED`
