# Grill-me Session — B3V-SYNC (Plan Phase 3)

## Q: 为何不在本分支改 write 模式契约？

**A**：`BATCH_3V_COORDINATOR_PLAYBOOK.md` §2.5 — `write_contract.yaml` + WriteManager 写模式语义 **B3V-OPS 独占**；SYNC crash-window 只读依赖，合并建议 OPS 之后。

## Q: VR-SYNC-001 如何在不违背 ADR-001 前提下关闭？

**A**：ADR-001 刻意将 COMPLETED 放在写提交之后。关闭路径是 **可检测的 WRITING+write_id 状态 + 恢复 transition**（注入测试），而非强制同事务 COMPLETED。若需改 ADR → 3F.4 handoff。

## Q: `test_advA3_016` 与 B3V-SYNC 冲突？

**A**：是。Execute 须将测试目的从「显式 NotImplemented」改为「稳定 deferred 错误」；保留 ADV-A3-016 业务保障（调用方不得误以为已实现）。

## Q: CLI 是否在本任务发布 job types？

**A**：否。任务卡 §4 禁止 CLI 发布；仅契约 + runtime + 测试。
