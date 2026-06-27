# Grill-Me Session — R3G-01

## Doubt 1: 是否扩 L1 ingest allowlist 完成 R3G-01？

**Reconcile:** 否。活卡 §3 与仓库速记明确：应走 **新 sandbox_clean_write 编排器**；L1 仅 `ENV-E1-DGS10`，扩 allowlist 不是 3G 写入链证明。

## Doubt 2: 能否复用 `staged_pilot.run` 直接当排练？

**Reconcile:** 否。staged_pilot 证 staged 路径且 fred 在 `DISABLED_PILOT_SOURCE_IDS`；R3G-01 需 **authorized fred** + **WriteManager clean 写** + 契约报告字段。须专用 `rehearsal_runner` compose 同门禁。

## Doubt 3: FRED 无用户 artifact 能否 mock 通过？

**Reconcile:** 单元测试可用 mock port；**任何 live fetch 路径** 无 artifact 必须 fail-closed。用户已书面授权排练 — artifact 须落盘 `.audit-sandbox/round3g/fred_user_authorization.yaml`（或 CLI 指定）。

## Doubt 4: 是否证五层全量？

**Reconcile:** 否。3G 证 **写入链** + sandbox 报告；不声称 R6 / production-live。

## Doubt 5: `production_default_allowed` 措辞？

**Reconcile:** 统一 catalog canonical **`production_default_enabled`**；frozen/Plan 禁止旧字段名。

## Doubt 6: 能否并行 R3G-02？

**Reconcile:** Playbook 禁止。R3G-01 先合并证据。

## Doubt 7: rollback 是否真写生产？

**Reconcile:** 仅 sandbox DB dry rollback artifact；`--no-production-mutation` 缺失则 CLI 失败。
