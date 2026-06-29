# Audit A8 — 证据 · 测试契约 — R3H-08

| 字段                  | 值         |
| --------------------- | ---------- |
| 维                    | A8         |
| plan_protocol_version | 4.1        |
| 日期                  | 2026-06-30 |

## pytest

| 命令                        | 结果                                 |
| --------------------------- | ------------------------------------ |
| 必跑 audit-sandbox basetemp | 30 passed, **3 ERROR**（父目录缺失） |
| 默认 basetemp               | **33 passed**                        |

## §维度裁决

**FAIL**

## 计划内问题

| ID       | P   | 标题                             | 锚点                 | 根因                     | 修复方案                   | 验证            |
| -------- | --- | -------------------------------- | -------------------- | ------------------------ | -------------------------- | --------------- |
| A8-P1-01 | P1  | audit-sandbox basetemp 不可用    | 任务目录             | `.audit-sandbox/` 未创建 | mkdir bootstrap            | 必跑命令 exit 0 |
| A8-P1-02 | P1  | 08B 九源缺 env-gated live 契约测 | WAVE2 AC · slices §5 | 仅 yahoo                 | 每源 parametrized gate 测  | pytest 全绿     |
| A8-P2-01 | P2  | S08-04 ResourceGuard 无测        | slices §6            | AC 无断言                | 补预算守卫测               | 新用例绿        |
| A8-P2-02 | P2  | 08C 无 silent-fallback 负向测    | slices §3            | integration-audit 未落地 | 负向 fallback 测           | pytest          |
| A8-P2-03 | P2  | S08-05 probe→service 未 tracer   | slices §7            | 仅 REHEARSAL 常量        | cross-import 或 defer 文档 | catalog 链接    |

## 计划外发现

| ID       | P   | 标题                         | 锚点                                               | 根因         | 修复方案            | 验证               |
| -------- | --- | ---------------------------- | -------------------------------------------------- | ------------ | ------------------- | ------------------ |
| A8-P2-04 | P2  | env opt-in 测弱断言          | `test_productLiveGate_allowsWhenEnvOptedIn`        | 仅不抛异常   | 断言副作用          | pytest             |
| A8-P2-05 | P2  | 08C reject 未断言 error code | `test_r3h08_08c_productLivePort_rejectsWithoutEnv` | 无 code 断言 | 对齐 BOOT 测        | parametrized       |
| A8-P3-01 | P3  | test_catalog 未链接规范      | `test_catalog.yaml` L905                           | verifies 空  | loop_maintain --fix | check_test_catalog |
