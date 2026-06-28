# Integration Audit — R3H-02（Plan 5d · doubt-driven-development）

## CLAIM → DOUBT → RECONCILE

| CLAIM                            | DOUBT                       | RECONCILE                                  |
| -------------------------------- | --------------------------- | ------------------------------------------ |
| 双 normalizer 可覆盖五源         | crypto 字段与 OHLCV 混用    | 分 `market_data` / `crypto_market`         |
| yahoo 3G bundle 可直迁           | rehearsal_loader 硬编码路径 | §9.4 新 replay 路径 + 兼容 reader          |
| validation-only 不会被选 primary | route 回归遗漏              | 保留 `test_advR3xRoute001` + §9.3–9.5 负例 |
| replay = READY                   | 无 live 也能 READY          | hardening 允许；AV live 为加分             |
| Layer smoke = R3H-05             | 范围蔓延                    | §9.7 仅 3 测；frozen §8.1 #5               |
| G2 本卡必须闭合                  | EasyXT 日历工作量大         | ponytail 自然日窗；G2 与 R3H-03 协调       |
| 五源同卡可一次 merge             | registry 与 R3H-03 冲突     | §9.6 coordinator-only                      |

## 六类检查

| 类   | 状态         | 备注                                                                               |
| ---- | ------------ | ---------------------------------------------------------------------------------- |
| 契约 | PASS         | capabilities + route + layer5 + resource_limits 已映射                             |
| 测试 | GAP          | `test_market_data_adapters` / `test_crypto_market_adapters` 尚不存在 — Execute 9.0 |
| 安全 | PASS（设计） | 无 crypto 账户 API；AV API key gate                                                |
| 架构 | PASS         | 双 normalizer；无 market_adapter 泥球                                              |
| 文档 | PASS         | 活卡 §1.1–§15                                                                      |
| 运维 | GAP          | coordinator manifest — Execute 9.6 填实                                            |

## doc-gap

- `tests/fixtures/replay/market_data/**` — Execute 9.2–9.4 创建
- `tests/fixtures/replay/crypto_market/**` — Execute 9.5 创建
- 五源 coordinator manifest — Execute 9.6 产出 `execute-evidence/9.6-manifest.md`

## adversarial

| 攻击面                    | 对策                                      |
| ------------------------- | ----------------------------------------- |
| yahoo 升格 primary        | §10.1 step 9.4 + registry validation_only |
| aggregator silent primary | R3X route block + §9.3 stooq 负例         |
| 全期权链扫描              | §7 cap + reject_over_cap                  |
| OpenBB 拷贝               | guardrails pytest + §13                   |
| 主库写入                  | §8 forbidden；Tier D INDEX §2.1           |

## closure

**PASS** — 对抗性审计回补后：Plan 草稿均已 merged 或 INDEX §3 索引；§10.2 攻击面闭包已入 frozen；Execute GAP 仅属 9.0 预期 RED。

**Phase 5d complete · re-audit 2026-06-28**
