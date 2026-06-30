# Integration Audit — R3H-06（Plan 5d · doubt-driven-development）

## CLAIM → DOUBT → RECONCILE

| CLAIM                             | DOUBT                           | RECONCILE                                             |
| --------------------------------- | ------------------------------- | ----------------------------------------------------- |
| 单 migration 可闭合三域           | 013 过大难 review               | 先 013 合一；过大则 014 拆 disclosure（brainstorm B） |
| VIEW 够 pilot 兼容                | 用户否决 VIEW                   | **全量**改 `security_bar_1d`；9.7 `rg` 门禁           |
| axis_observation 可接 fred bundle | 列映射不全                      | 9.4 专用 mapper；对照 `ingestion_evidence.py`         |
| upsert 已存在即 G6 闭合           | pilot 仍 append                 | 9.6 强制 promote 路径 write_mode                      |
| 不改 registry 即可 PASS           | 能力字段与表不一致              | 9.2 测 capabilities 列 ⊆ DDL                          |
| Execute 只读三件套够              | cn_announcement 列只在 research | **已并入** INDEX §4 + frozen §6                       |
| Wave 2 可偷改 schema              | 并行 agent                      | frozen §8 + branch 锁                                 |

## 六类检查

| 类   | 状态         | 备注                                                |
| ---- | ------------ | --------------------------------------------------- |
| 契约 | PASS         | schema.sql + capabilities + sandbox contract        |
| 测试 | GAP          | `test_r3h06_clean_schema.py` 尚不存在 — Execute 9.0 |
| 安全 | PASS（设计） | 无 Agent 写；主库 denylist 保持                     |
| 架构 | PASS         | 三域分表；macro 不 duplicate                        |
| 文档 | PASS         | 活卡 + INDEX §4 内联                                |
| 运维 | GAP          | migration 013 rollback 说明 — Execute 9.8 文档段    |

## doc-gap（Plan 期）

- `cn_announcement_clean` 已写入 `specs/schema/schema.sql` — **Execute 9.2 实施**
- `BATCH_3H_TASK_CARD_MANIFEST.md` 未列 R3H-06 — **主会话 merge 时补 manifest 行**（非 Execute 阻塞）

## 对抗性审计（adversarial）

| 检查项                      | 结果                  | 修复                                   |
| --------------------------- | --------------------- | -------------------------------------- |
| B01–B10 BLOCKING            | ✅ fixed              | `research/adversarial-audit-report.md` |
| NB01–NB13                   | ✅ fixed/waived       | 同上                                   |
| implement.jsonl 无 research | 待 generate-manifests | freeze 命令                            |
| validate-plan-freeze        | 待 exit 0             | freeze 命令                            |

## closure

**PASS_WITH_GAPS** — 对抗项已闭环；待 `freeze-task-card` + `validate-plan-freeze` exit 0 后可冻结。

**Phase 5d complete**
