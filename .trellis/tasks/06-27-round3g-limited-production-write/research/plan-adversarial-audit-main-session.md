# Plan 对抗性审计 — R3G-03 主会话

> 对照：EXECUTION*INDEX · frozen（待生成）· PROJECT_IMPLEMENTATION_ROADMAP · BATCH_3G*\* · project_map · R3G-01/02 归档

## 审计维度

| #   | 维度             | 结论           | 备注                                               |
| --- | ---------------- | -------------- | -------------------------------------------------- |
| 1   | 目的/范围        | PASS           | 仅 promote 门禁链；不扩源                          |
| 2   | AC/步骤对齐      | PASS           | §0.1 10 AC ↔ §1 9.0–9.8                            |
| 3   | 用户授权语义     | PASS（已澄清） | Plan 授权 ≠ §6 approval YAML                       |
| 4   | R3G-02 前置      | WARN           | 审计报告 PASS_WITH_FIXES；promote 读决策文件非报告 |
| 5   | 索引/manifest    | PASS（修复后） | 见 P-01..P-08                                      |
| 6   | TDD/证据         | PASS           | 每步 RED/GREEN + 9.8 全库                          |
| 7   | 安全 fail-closed | PASS（设计）   | 默认 dry_run；Tier B 隔离                          |
| 8   | 复用/架构        | WARN           | rehearsal_runner 镜像风险 — 见 P-05                |
| 9   | 测试深度         | FAIL→FIX       | 当前仅契约静态测 — Execute 必扩                    |
| 10  | prod-path        | PASS           | Tier B 显式；CI 不真写                             |

## 发现（按优先级）

### P0 — 须在 Execute 前知晓（不阻断 Plan 冻结）

| ID    | 项                      | 证据                                           | 要求                                                         |
| ----- | ----------------------- | ---------------------------------------------- | ------------------------------------------------------------ |
| P0-01 | **无 r3g03 fixture 包** | `tests/fixtures/sandbox_clean_write/` 仅 r3g01 | Execute 9.1 增 approval/audit/before/rollback 最小 YAML/JSON |
| P0-02 | **promote 模块不存在**  | 活卡 §4 路径缺失                               | 符合预期；§1 RED 已写明                                      |

### P1 — Execute 阻断若未修复

| ID    | 项                                        | 证据                               | 要求                                         |
| ----- | ----------------------------------------- | ---------------------------------- | -------------------------------------------- |
| P1-01 | **契约测未覆盖 block_if 全矩阵**          | 活卡 §10 列 10 项；测试仅 3+3 静态 | 9.7 对抗测逐 block_if                        |
| P1-02 | **approval schema 未机器校验**            | 仅文档 §6                          | approval_contract.py + 测                    |
| P1-03 | **rehearse/audit CLI 生产路径**           | R3G-01/02 有拒 DATA_ROOT 测        | promote 须独立测 + 确认未回退 rehearse/audit |
| P1-04 | **block_if 缺 write_manager bypass 专测** | 契约含 bypass；rollback 测未覆盖   | PromoteRunner 合成 bypass 报告               |

### P2 — 计划缺口（已修复或记入 manifest）

| ID    | 项                            | 修复                                                     |
| ----- | ----------------------------- | -------------------------------------------------------- |
| P2-01 | §3 缺 `adversarial_audit.py`  | 已加入 §3                                                |
| P2-02 | §3 缺 R3G-02 execute-evidence | 已加入 §3                                                |
| P2-03 | §3 缺 `rehearsal_plan.py`     | 已加入 §3                                                |
| P2-04 | frozen 未生成                 | freeze-task-card 后闭合                                  |
| P2-05 | **runner 双维护**             | Execute 优先提取共享 gate 函数；否则 ponytail 注释       |
| P2-06 | **after_proof 非目标 range**  | §9.5 测 unchanged row count                              |
| P2-07 | **release note AC-10**        | §2 AC-10 路径待定 — Execute 写片段                       |
| P2-08 | **FRED live_fetch**           | approval 字段 `live_fetch_authorized` — PromoteRunner 测 |

### P3 — 非阻断

| ID    | 项                                                | 备注                                      |
| ----- | ------------------------------------------------- | ----------------------------------------- |
| P3-01 | R3G-02 审计 P0 lineage/synthetic 未在本 Plan 重开 | 不阻塞 promote 契约；Audit A4 可 WARN     |
| P3-02 | `__init__.py` 未导出 promote API                  | ponytail 刻意不导出或 Execute 补          |
| P3-03 | batch map 仍写 MASTER.plan 措辞                   | v4 任务读 EXECUTION_INDEX；历史地图仅追溯 |

## 项目地图倒查（索引遗漏）

见 `research/project-map-omission-check.md`

## 未发现问题（显式）

- Plan 未扩大候选集 beyond baostock/cninfo/fred
- Tier B 与 sandbox rehearse 分离
- `layer1_axes/ingestion.py` 已索引
- Agent 路径未打开

## 状态

**REMEDIATED（Plan 轮）** — manifest/AC/步骤已修补；**测试深度 GAP 留给 Execute**。
