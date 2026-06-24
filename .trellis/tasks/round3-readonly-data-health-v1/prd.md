# PRD — read-only data health v1 (staged evidence gate)

## 问题

staged pilot 已产出 raw/staging evidence，但缺少机器可读的质量汇总，无法作为 sandbox clean-write rehearsal 的前置 gate。

## 用户

- 协调者 / Execute agent（CLI + JSON）
- 下游 Batch（读取 report 字段，不读口头声称）

## 成功标准

1. 对 v2 evidence 目录一键检查 → JSON + text summary
2. 至少覆盖任务卡 §5.1 所列 rule_id 子集
3. 坏 fixture 可 FAIL；好 evidence 可 PASS/WARN
4. `production_db_mutated: false` / `source_fetch_performed: false` 硬编码为 false 且可测

## 非目标

- production DB 写、source fetch、migration、full market scan、free SQL、前端、自动修复

## 约束

- Wave C playbook §2.2 TDD + ponytail + 五字段测试 docstring
- 全部 agent `composer-2.5`（禁 fast）
