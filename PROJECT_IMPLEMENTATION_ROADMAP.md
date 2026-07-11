# PROJECT_IMPLEMENTATION_ROADMAP

> **用途：** 阶段外置 / 跨阶段承接的最小 SSOT（与 `docs/quality/待修复清单.md` 配对）。  
> **说明：** 2026-07-12 为闭合「仓库缺 ROADMAP、双登记手续不齐」而建立本最小表；后续阶段继续追加行，勿口头 defer。  
> **非目标：** 本文件不替代 `task_plan` / Gate 规格 / ADR。

## task-01-source-registry · G1-02 启用接缝（承接中）

| 台账 ID                     | 绑定阶段/任务                                                                     | 依赖                                      | 承接内容                                                        | 关闭条件                                                                                                   |
| --------------------------- | --------------------------------------------------------------------------------- | ----------------------------------------- | --------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `T01-F05-A`                 | G1-02 · **票 06∥07**（4a/4b）                                                     | 票 04/05 Execute CLOSED                   | 旧口径测迁正规 overlay；生产 ESR 消费者清零                     | **已满足测债关闭条件（2026-07-12）**：A1–A6 pytest 绿 + `test:quick` exit 0；**≠** G1-02/R4/Execute CLOSED |
| `T01-F06`                   | G1-02 · **仍开放 → 票 08 后夹具零构造切片**                                       | 生产包已清；仅 tests 夹具                 | 去掉 `tests/.../build_sandbox_route_planner` 对测试副本内存构造 | 删内存构造 + 相关测绿；生产已用 `build_activation_route_planner`                                           |
| `T01-F07`                   | G1-02 · **仍开放 → 票 08 后删回落切片**                                           | 正式入口一律 `con=`                       | 删除 `plan(con=None)` YAML 内存 `is_enabled` 回落               | 无 con 回落代码路径删除 + 行为测                                                                           |
| `T01-F08`                   | G1-02 · **票 09 前纠正切片**                                                      | capability 契约                           | RoutePlanner 按 operation 声明闸门                              | 未声明 op 不得 READY + 行为测                                                                              |
| `T01-F09`                   | G1-02 · **代码已改 → 票 09 证据前独立复验**                                       | overlay 例外分支已入 `route_planner.plan` | 独立复现原「overlay 后仍 DISABLED」反证                         | 复验通过后改 findings disposition=已修复；此前不得写已修复                                                 |
| `T01-F10`                   | G1-02 · **管理员写 overlay CLI 前 / 票 09 前置**                                  | sandbox overlay 写入                      | 隔离根 + 已登记能力校验                                         | 非沙箱/未声明能力写入失败 + 行为测                                                                         |
| `T01-F11`                   | G1-02 · **票 09 前纠正切片**（可与 F08 同包）                                     | capability 加载                           | `frequency`/`fields`/`requires_auth` 类型与非空                 | 弱文档拒载 + 行为测                                                                                        |
| `T01-F12`                   | G1-02 · **票 09**                                                                 | 策略遥测                                  | `reason_code` 对齐最终 RoutePlan；补 platform 字段              | 行为测断言最终原因                                                                                         |
| `T01-ENABLE-FRED-MERGE-001` | Gate 1 · **最迟 G1-08 前** · 票 **10**                                            | 票 06 先拆 FRED 启用撬门                  | FRED 编排壳并入通用宏源或新 ADR 废止                            | ADR-018 §3 四门槛；**06/07 不关**                                                                          |
| `T01-F03`（余）             | G1-02 · 票 **08**（4x bridge）；4a/4b 生产 ESR 撬门已清；`enabled_*` 生产定义已删 | 01–07 Execute CLOSED                      | bridge 按票 08 AC 处置                                          | brief §3.1/§6 + inventory；≠ G1-02                                                                         |

**交叉引用：** `task/task-01-source-registry/findings.md`（F05-A node-id 表）· `docs/quality/待修复清单.md` · `task/task-01-source-registry/HANDOFF.md`
