# Agent 08 — 性能占用与运行速度审计

## 1. 独立角色边界

本 agent 只审计性能占用、运行速度、资源边界、构建体积、生产等价性能验证与未测性能风险。不评价业务完成度、设计一致性或 DB schema 正确性。

## 2. 生产/生产等价边界

真实生产 live source 未执行，原因：`018B_production_live_pilot_gate.md` 与 `production_live_pilot_policy.md` 要求显式用户授权、sandbox-first、raw_only-first、禁止 production clean DB mutation。本 agent 采用生产等价替代：ResourceGuard/route/service/vendor fixture E2E、Batch2.5 production-data gate、frontend production build、full pytest timing、coverage run。残余风险：未暴露真实 vendor 网络延迟、真实数据规模、真实源 schema drift。

## 3. 使用的有效 skill / 工具

| 名称                                    | 用途                                | 执行命令或依据                                                                        | 结果                                                 |
| --------------------------------------- | ----------------------------------- | ------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| performance-optimization skill          | “先测量再优化”与预算审计            | 已加载；审计 build size、test duration、ResourceGuard                                 | 有基础测量，但没有 live/scale benchmark              |
| observability-and-instrumentation skill | 检查性能是否有可观测证据            | 已加载；审计 fetch_log/resource_guard/log evidence 路线                               | Batch2.5 有 evidence，但 live pilot telemetry 未产生 |
| pytest Resource/Service/E2E             | 生产等价关键路径                    | source capabilities/route/service/sync/vendor E2E                                     | exit 0                                               |
| npm build                               | 前端生产构建速度与 bundle size      | `npm run build` in frontend                                                           | build 88ms；JS gzip 60.16 kB                         |
| CodexPro read/search                    | 读取 production smoke 脚本和 policy | `read scripts/production_equivalent_smoke.py`; `read production_live_pilot_policy.md` | 脚本存在但未执行；policy 禁止未授权 live             |

## 4. 执行命令与结果

| 命令                                                                                                                                                                                                    | 结果摘要                                              |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| `pytest tests/test_source_capabilities.py tests/test_source_route_planner.py tests/test_data_cli_contract.py tests/test_sync_orchestrator.py tests/test_sync_jobs.py tests/test_vendor_fetch_e2e.py -q` | exit 0；约 28.8s                                      |
| `pytest -q`                                                                                                                                                                                             | exit 0；约 154.7s；589 collected，1 skip observed     |
| `pytest --cov=backend --cov-fail-under=85 -q`                                                                                                                                                           | exit 0；约 154.3s；coverage 91.31%                    |
| `npm run build` in `frontend`                                                                                                                                                                           | exit 0；Vite build 88ms；JS 190.75 kB / gzip 60.16 kB |
| `pytest tests/test_production_live_pilot_policy.py tests/test_batch25_production_data_gate.py -q`                                                                                                       | exit 0；11 tests passed                               |

未执行：`scripts/production_equivalent_smoke.py`，因为 CodexPro safe bash allowlist 不允许直接运行 Python script。该脚本被读取确认使用 `.audit-sandbox/prod-equiv-smoke` 隔离路径，但未计入已执行性能工具。

## 5. P0/P1/P2/P3

### P0

无。未发现运行测试阶段的资源失控、超时或构建失败。

### P1

| ID        | 问题                                   | 证据                                                   | 影响                                                                  | 当前阶段可修复?         | 修复状态 | 解决方案                                                                                                        |
| --------- | -------------------------------------- | ------------------------------------------------------ | --------------------------------------------------------------------- | ----------------------- | -------- | --------------------------------------------------------------------------------------------------------------- |
| A08-P1-01 | 未执行真实 live/生产等价规模 benchmark | `R3-B2.75-01` DEFERRED；production smoke script 未执行 | 不能确认真实 vendor latency、数据规模、ResourceGuard 在真实负载下表现 | 否；需授权或 full shell | 未修复   | Batch2.75/Batch6 执行 raw-only live pilot 与 production_equivalent_smoke，记录 p50/p95、row cap、guard decision |
| A08-P1-02 | full pytest 约 155s，对快速反馈偏慢    | `pytest -q` durationMs 154670                          | 影响开发/CI 周转，回归成本较高                                        | 是，但用户禁止变更      | 未修复   | 建立 quick/affected/full test tiers；将 slow suites 标注并分层运行                                              |

### P2

| ID        | 问题                                                                        | 证据                                                      | 影响                                               | 当前阶段可修复? | 修复状态 | 解决方案                                                    |
| --------- | --------------------------------------------------------------------------- | --------------------------------------------------------- | -------------------------------------------------- | --------------- | -------- | ----------------------------------------------------------- |
| A08-P2-01 | Layer1 ingestion 文件 1,516 LOC，证据工具 557 LOC，可能增加 import/认知成本 | A2 report                                                 | 性能影响未必大，但会影响执行路径理解与局部测试速度 | 是              | 未修复   | 拆分 evidence tooling，测量 import/test time before/after   |
| A08-P2-02 | 缺少明确性能预算报告文件                                                    | 当前仅有测试时长、build size、historical A6 perf evidence | 性能退化难以作为 release gate                      | 是              | 未修复   | 增加 `performance_limits` 对应的 smoke benchmark 输出与阈值 |

### P3

| ID        | 问题                                 | 影响 | 解决方案                    |
| --------- | ------------------------------------ | ---- | --------------------------- |
| A08-P3-01 | 前端 bundle 当前可接受，但无预算门禁 | 低   | 为 gzip JS/CSS 加 CI budget |

## 6. 评分

**87 / 100 — FAIL**

扣分依据：真实/生产等价规模 benchmark 未执行 -5；full pytest 反馈慢 -3；缺性能预算 gate -3；live telemetry 缺失 -2。

## 7. 达到 95+ 的最小修复清单

1. 在授权/隔离环境执行 Batch2.75 raw-only live pilot 或 `production_equivalent_smoke.py --use-service-path`，保留指标。
2. 建立性能预算：pytest tier 时长、Vite gzip bundle、ResourceGuard threshold、vendor fetch row cap。
3. 标记 slow tests 并提供 quick regression profile。
4. 对 Layer1 ingestion 拆分后测量 import/test time。

## 8. 结论

本维度 **FAIL**。当前性能没有明显爆炸，但真实/生产等价性能证据不足，无法达到 95+。
