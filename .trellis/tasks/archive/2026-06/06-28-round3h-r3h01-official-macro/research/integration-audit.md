# Integration Audit — R3H-01（Plan 5d · doubt-driven-development）

## CLAIM → DOUBT → RECONCILE

| CLAIM                        | DOUBT                     | RECONCILE                                                  |
| ---------------------------- | ------------------------- | ---------------------------------------------------------- |
| G10 用 normalizer 可一次闭合 | loader 仍读旧 `date` 字段 | §9.1 测试双形态 round-trip；reader 接受 `observation_date` |
| 迁 fred_port 无回归          | ops 路径大量测试引用      | thin re-export + 渐进删 bridge sidecar                     |
| 六源同卡可一次 merge         | registry 与 R3H-02 冲突   | §9.6 coordinator-only；本卡只改六源行                      |
| replay = READY               | 无 live 也能 READY        | hardening 允许 replay；fred live 为加分                    |
| Layer smoke = R3H-05         | 范围蔓延                  | §9.7 仅 2 测；frozen §8.1 停损 #5                          |
| 主库安全                     | 新测误写 canonical path   | 禁止 WM 测写主库；Tier D INDEX §2.1                        |
| ADR 可偷懒 defer             | 三源不实现                | ADR 须 `docs/adr/` + route DISABLED + release note         |

## 六类检查

| 类   | 状态         | 备注                                                  |
| ---- | ------------ | ----------------------------------------------------- |
| 契约 | PASS         | capabilities + layer5 + guardrails 已映射             |
| 测试 | GAP          | `test_official_macro_adapters` 尚不存在 — Execute 9.0 |
| 安全 | PASS（设计） | 无 Agent 写；SEC identity header；FRED auth           |
| 架构 | PASS         | 单 normalizer；无 official_adapter 大泥球             |
| 文档 | PASS         | 活卡 §2.8/§4.1/§8.1/§9–§15                            |
| 运维 | GAP          | coordinator manifest 模板 — Execute 9.6 填实          |

## doc-gap

- `tests/fixtures/replay/official_macro/fred/` — Execute 9.2 创建
- `tests/fixtures/replay/sec_edgar/` — Execute 9.4 创建
- 六源 coordinator manifest 表 — Execute 9.6 产出 `research/registry-coordinator-manifest.md`

## adversarial

| 攻击面              | 对策                             |
| ------------------- | -------------------------------- |
| bridge sidecar 复活 | §10.1 step 9.1 必证无 sidecar    |
| READY 无 replay     | §10.1 step 9.6 registry 审计     |
| OpenBB 拷贝         | guardrails pytest + §13 red flag |
| 主库 promote 误用   | 不扩 3G promote；§8 forbidden    |

## closure

**PASS_WITH_GAPS** — Plan 冻结可过；Execute 须关闭测试/fixture GAP 与 coordinator manifest GAP。

**Phase 5d complete**
