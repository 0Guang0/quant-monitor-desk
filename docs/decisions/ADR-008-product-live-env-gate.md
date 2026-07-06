# ADR-008：产品 Live 环境门与 Tier 路由

## 状态

已接受（Plan 冻结）

## 日期

2026-06-29

## 背景

Wave 2 须将**产品 live** 与 **rehearsal（排练/沙箱）** 分离；24 个数据源按 Tier A/B/C 分级。产品侧真网拉数不能靠 ops pilot 脚本默许，须有统一、可测、可审计的门禁。

## 决策

1. **产品 live 门禁：** 须经 `ProductLiveGate` — 同时满足环境变量 `QMD_ALLOW_LIVE_FETCH=1`、`ResourceGuard` 通过、且当前非 rehearsal 模式。
2. **Tier 路由：** `LiveTierRouter.resolve_live_tier(source_id)` 映射 PASS §2.1；**Tier B** 仅允许 pilot / audit-sandbox，不得冒充产品主路径。
3. **拉数门面：** 拉数仅经 `DataSourceService`；**禁止**将 ops pilot 当作产品 SSOT。
4. **禁止静默回退：** EasyXT 式 silent source fallback **禁止**（源失败不得悄悄换源继续写库）。
5. **参考采纳（执行纪律）：** 每个切片 RED 前须阅读并登记 `参考项目/**` 源码（见 `reference-adoption-r3h08.md` §7）；**禁止不参考从零实现**；**禁止** runtime import 参考项目目录。

## 后果

- 新增薄模块：`product_live_gate.py`、`live_tier_router.py`
- 契约测试扩展：`test_production_live_pilot_policy` 及 `test_r3h08_*` 系列（若仍保留）
- reconcile / probe 延后项在 S08-05 闭合

## 绑定切片

S08-BOOT · S08-05

## 与相关 ADR 的关系

- **ADR-006：** 生产 Sync 须显式 `datasource_service=`；与本 ADR「产品拉数仅经 DataSourceService」一致。
- **ADR-015（M-DATA-03）：** Live 验收须在隔离 `DATA_ROOT` 下运行，且依赖 `QMD_ALLOW_LIVE_FETCH=1`（本 ADR 第 1 条）。
