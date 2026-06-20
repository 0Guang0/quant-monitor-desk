# 对抗性审计核实与修补记录

> 2026-06-20 · 主会话逐项核实（subagent 超时后等效深度审计）后修补

## Agent 1 上下文项（F1–F16）

| ID  | 发现                                                              | 核实                                                   | 处置                                     |
| --- | ----------------------------------------------------------------- | ------------------------------------------------------ | ---------------------------------------- |
| F1  | `README.md` 未入 implement                                        | 确认；含 docs/specs 非实现边界、Execute 读法           | 已加入 implement + §0.6 + §0.8           |
| F2  | `PENDING_USER_DECISIONS.md` 未入 implement                        | 确认；D-01 uv.lock、D-11 QMT 默认禁用与本批相关        | 已加入 implement + §0.7                  |
| F3  | `runtime_versions.md` 未入 implement                              | 确认；§10 验收命令权威                                 | 已加入 implement + §10 注释              |
| F4  | `docs/ROUND3_HANDOFF.md` 未入 implement                           | DOC-R3-001 直接编辑目标                                | 已加入 implement + ledger                |
| F5  | `UNRESOLVED_ISSUES_REGISTRY.md` 未入 implement                    | BATCH_MAP 八项登记来源                                 | 已加入 implement + ledger                |
| F6  | `RESOLVED_ISSUES_REGISTRY.md` 未入 implement                      | §3.1 允许闭合移入                                      | 已加入 implement                         |
| F7  | GLOBAL\_\* 仅 ledger 声称 inline，MASTER 无实质摘要               | 确认 §0.2 过薄                                         | 已增 §0.7 GLOBAL 摘要                    |
| F8  | `specs/schema/schema.sql` 未入 implement                          | key_tables 表名权威                                    | 已加入 implement                         |
| F9  | `data_sources.md` 未入 implement                                  | evidence.latest_fetch 语义                             | 已加入 implement                         |
| F10 | `016F` 未入 implement                                             | AC-BENCH-1 设计追溯                                    | 已加入 implement                         |
| F11 | 前置 gate 路径未在 AC-PRE 显式                                    | archive routing-service-gate 存在                      | 已补 AC-PRE + implement pointer          |
| F12 | `ROUND_3_MODELING_LAYERS/README.md` 边界未 pointer                | Batch 1 排除 017–023                                   | 已加入 implement                         |
| F13 | `original-plan-trace` 列多文件 summarized 但 MASTER 无对应 inline | 与 F7 同类                                             | §0.7/§0.8/§13 扩充                       |
| F14 | BATCH_MAP §4 Batch 1 共享 docs 部分缺失 manifest                  | data_sources/schema 等已补                             | 其余 ops 模块本批不实现，保留 §0.2 defer |
| F15 | DB 路径：部分旧笔记 `data/quant_monitor.duckdb`                   | `local_file_system.md` 与 registry 均为 `data/duckdb/` | MASTER §9 Tier D 已统一                  |
| F16 | `plan-boot.md` 缺三项新增必读                                     | 确认                                                   | 已更新                                   |
| F17 | E7：`data_sources.md` 1-hop 契约未入 implement                    | validator 报错                                         | 已补 5 条 + validate PASS                |
| F18 | `README.md` 根路径 validator 不识别                               | `_path_exists` 仅查 task_dir                           | 已修 `validate_plan_freeze.py`           |

## Agent 2 协议项（P1–P12）

| ID  | 发现                                         | 核实                     | 处置                                 |
| --- | -------------------------------------------- | ------------------------ | ------------------------------------ |
| P1  | §8.0 RED 用 `test -f` 在 Windows 失败        | 用户环境 win32           | 改为 `uv run python -c` pathlib 检查 |
| P2  | `plan-manifest-audit.md` 仅 stub             | 确认                     | 已扩充                               |
| P3  | `integration-audit.md` PASS 但未覆盖新增必读 | 确认                     | 已更新六类 + doc-gap                 |
| P4  | `audit.jsonl` 仅 3 条                        | A5 无法追溯 registry     | 已扩充                               |
| P5  | `check.jsonl` 仅 2 条且 E14 要求 ⊆ implement | 确认                     | 已对齐 implement                     |
| P6  | §13 归并表缺 DOC/DB/E2E 等八项               | 确认                     | 已补全                               |
| P7  | Tier A 未写 `uv sync --locked`               | runtime_versions §4 要求 | 已补                                 |
| P8  | §8.6 RED 证据列为空                          | 对抗：可跳过 RED         | 已补 Tier B 预检命令                 |
| P9  | AUDIT A5 未列 UNRESOLVED registry            | 确认                     | audit.jsonl + AUDIT §3               |
| P10 | `plan-skill-reads.jsonl` 缺新增必读          | 确认                     | 已追加                               |
| P11 | AC-PRE 未要求 `--locked` 基线                | D-01                     | §8.0 GREEN 已含 `uv sync --locked`   |
| P12 | `plan.freeze.md` 未记录对抗审计轮次          | 流程                     | 已增 §3.7                            |

## 验证

修补后运行：`python .trellis/scripts/task.py validate-plan-freeze <task-dir>` → 须 exit 0。
