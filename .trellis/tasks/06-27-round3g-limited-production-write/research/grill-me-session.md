# Grill Session — R3G-03（Plan Phase 3）

## 质问与回答

**Q1：用户说「授权进入 R3G-03」，是否等于可以跳过 approval YAML？**  
A：**否**。Plan 授权 ≠ 生产写授权。Execute prod-path 仍须活卡 §6 机器可读 approval + audit 对齐。

**Q2：R3G-02 审计报告 PASS_WITH_FIXES，能否直接 promote？**  
A：**否**。须 `audit_decision.json` 决策枚举为 `PASS_ALLOW_LIMITED_PROD_WRITE` 或 `WARN_*` + 用户 approval；修复项关闭不自动等同决策文件。

**Q3：默认 dry_run 还是真写？**  
A：实现与 CLI **默认 dry_run**；Tier B prod-path 真写须 Coordinator 在 Execute 步进时显式 `--execute`（或等价旗标），且 approval 中 production_db_path 精确匹配。

**Q4：rollback dry-run 要不要真删行？**  
A：**不要**。本任务只证明 affected keys 可识别；真回滚属运维门，不在本切片。

**Q5：能否复用 R3G-01 sandbox DB？**  
A：**否**。promote 目标为 `production_db_path`（approval 指定）；sandbox 仅 R3G-01/02。

**Q6：FRED live fetch？**  
A：仅 approval 中 `live_fetch_authorized: true` + 既有 FRED authorization artifact；默认禁止。

**Q7：最小可交付切片？**  
A：approval_contract → before_proof → rollback_plan schema → entry runner(dry_run) → CLI → 对抗测 → merge。

## 结论

范围锁定为 **promote 门禁链 + 证据 JSON**；不扩源、不 Agent、不参考项目 runtime。
