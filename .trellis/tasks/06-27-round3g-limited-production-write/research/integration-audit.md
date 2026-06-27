# Integration Audit — R3G-03（Plan 5d · doubt-driven-development）

## CLAIM → DOUBT → RECONCILE

| CLAIM                          | DOUBT                       | RECONCILE                                                     |
| ------------------------------ | --------------------------- | ------------------------------------------------------------- |
| 契约已覆盖 r3g03 block_if      | 仅 3+3 静态测，无 runner    | §1 9.4–9.7 要求对抗测；冻结                                   |
| rehearsal_runner 可镜像        | 复制编排→双维护             | ponytail：入口提取共享 `_compose_gates` 或最小镜像+注释天花板 |
| mutation_proof 够 before/after | 缺 target table schema hash | §9.2 补 schema hash 字段测                                    |
| 用户授权=可写生产              | Plan 授权≠§6 YAML           | frozen §0 + grill-me 写死                                     |
| R3G-02 PASS_WITH_FIXES 阻塞    | 决策文件可独立 PASS         | promote 只读 audit_decision.json 枚举                         |

## 六类检查

| 类   | 状态         | 备注                                           |
| ---- | ------------ | ---------------------------------------------- |
| 契约 | PASS         | sandbox_clean_write_contract.yaml r3g03 段齐全 |
| 测试 | GAP          | 须 Execute 扩 PromoteRunner/Cli                |
| 安全 | PASS（设计） | 双锁 approval+audit；默认 dry_run              |
| 架构 | PASS         | 单包 sandbox_clean_write                       |
| 文档 | PASS         | 活卡已加固 §9                                  |
| 运维 | GAP          | Tier B prod-path 须 Coordinator 手册一句       |

## doc-gap

- 缺 `tests/fixtures/sandbox_clean_write/r3g03/` approval/before/rollback 样板 — Execute 9.1 创建
- 缺 promote CLI ops 文档 — 可并入 release note 片段（AC-10）

## adversarial

见 `research/plan-adversarial-audit-main-session.md`

## closure

**PASS_WITH_GAPS** — Plan 冻结可过；Execute 须关闭测试 GAP 与 fixture GAP。
