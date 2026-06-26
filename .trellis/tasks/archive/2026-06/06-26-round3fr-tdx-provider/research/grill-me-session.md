# Grill-Me Session — R3FR-03 (Phase 3)

## Q1: 能否把 TDX 做成 production primary？

**A:** 禁止。任务卡与 Batch 3F-R 全局 posture 明确 validation-only、disabled-by-default；route 仅 `DISABLED_SOURCE` / `USER_AUTH_REQUIRED` / raw-only pass。

## Q2: 能否直接从 EasyXT 复制 `tdx_provider.py`？

**A:** 禁止 wholesale copy。MIT 允许思路适配；须 `rewrite_required`：无 runtime import、无 auto server scan、无 auto login。归因注释保留。

## Q3: `TdxPytdxProbeFetchPort` 删还是留？

**A:** 留薄兼容层或显式委托新 port，满足 `tdx_live_manual_probe_gate.FORBIDDEN_LIVE_ENTRYPOINTS`（禁止经 interface_probe 默认 live）。不得在旧类继续增长 downloader。

## Q4: caps 用 10 还是任务卡的 3？

**A:** 以任务卡 §5 为准（equity/index max symbols = 3）。gate、port、registry、测试四处对齐；可改测试数值，**不可**改测试目的（仍须证明超 cap 拒绝）。

## Q5: data health 在本任务改吗？

**A:** 不改 `data_health.py` 主体（R3FR-02 已完成）。本任务只保证 TDX raw manifest 形状可供 profile 消费；不新增 health 微切片。

## Q6: 需要新依赖吗？

**A:** 否。`pytdx` 保持 optional；缺包走 `DISABLED_SOURCE`。

## 结论

范围锁定为 **provider port 完整形态**；编排留在 `tdx_manual_probe`；registry 独占 `tdx_pytdx` 行更新。
