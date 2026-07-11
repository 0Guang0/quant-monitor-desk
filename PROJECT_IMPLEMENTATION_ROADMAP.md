# PROJECT_IMPLEMENTATION_ROADMAP

> **用途：** 阶段外置 / 跨阶段承接的最小 SSOT（与 `docs/quality/待修复清单.md` 配对）。  
> **说明：** 2026-07-12 为闭合「仓库缺 ROADMAP、双登记手续不齐」而建立本最小表；后续阶段继续追加行，勿口头 defer。  
> **非目标：** 本文件不替代 `task_plan` / Gate 规格 / ADR。

## task-01-source-registry · G1-02 启用接缝（承接中）

| 台账 ID | 绑定阶段/任务 | 依赖 | 承接内容 | 关闭条件 |
|---------|---------------|------|----------|----------|
| `T01-F05-A` | G1-02 · **票 06∥07**（4a/4b） | 票 04/05 Execute CLOSED | 旧口径测迁正规 overlay；生产 ESR 消费者清零 | findings F05-A **全部 node-id 绿**；关账证据无 ESR/`__setattr__`；`test:quick` 含 `test_mootdxBarClean_layer5Provenance_matchesSameRunBundle` 绿 |
| `T01-F06` | G1-02 · **票 06**（4a） | 票 05 夹具 | 去掉 `enable_source_route` 对测试副本 `_sources`/`_domain_roles`/`_raw` 内存构造 | 增量路径只靠 overlay+sync；相关测绿 |
| `T01-F07` | G1-02 · **票 06+07 完成后** | 正式入口一律 `con=` | 删除 `plan(con=None)` YAML 内存 `is_enabled` 回落 | 无 con 回落代码路径删除 + 行为测 |
| `T01-ENABLE-FRED-MERGE-001` | Gate 1 · **最迟 G1-08 前** · 票 **10** | 票 06 先拆 FRED 启用撬门 | FRED 编排壳并入通用宏源或新 ADR 废止 | ADR-018 §3 四门槛；见待修复清单 |
| `T01-F03`（余） | G1-02 · 票 **06/07/08** | 04/05 已 CLOSED | 生产路径无 ESR / 强制 platform；bridge 按票 08 处置 | brief §3.1/§6 + inventory 入口全表处置 |

**交叉引用：** `task/task-01-source-registry/findings.md`（F05-A node-id 表）· `docs/quality/待修复清单.md` · `task/task-01-source-registry/HANDOFF.md`
