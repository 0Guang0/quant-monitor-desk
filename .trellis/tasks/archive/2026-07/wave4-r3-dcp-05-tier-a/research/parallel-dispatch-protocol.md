# DCP-05 并行 Execute Agent 派发协议（方案 B · merge 负责人 SSOT）

> **模型：** `composer-2.5`（禁止 `composer-2.5-fast`）  
> **铁律：** 与主会话 Execute 流程 **完全一致** + 工程契约全程 + **参考项目实读门禁**

---

## 1. 与主会话一致的 Phase 0 Boot（每个 agent 开工前必做）

| #   | 动作                    | 路径                                                                                                                       |
| --- | ----------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| 0a  | Read 工程契约           | `agent-toolchain.md` · `.cursor/skills/trellis-execute/SKILL.md` · `reference.md` · `principles.md` · `project-global.mdc` |
| 0b  | Read Execution Bundle   | `research/00-EXECUTION-ENTRY.md` §1–§4 · `research/to-issues-slices.md` **本 agent 切片** · `DEBT.plan.md` · ADR-028       |
| 0c  | Read 路由表             | `EXTERNAL-INDEX.md` §A + `implement.jsonl` 每一行                                                                          |
| 0d  | Read 参考采纳 SSOT      | `research/reference-adoption-dcp05.md` + `specs/contracts/reference_adoption_guardrails.yaml`                              |
| 0e  | GitNexus `impact()`     | 本切片将改 symbol；HIGH/CRITICAL 须停报 merge 负责人                                                                       |
| 0f  | `validate-execute-boot` | `python .trellis/scripts/task.py validate-execute-boot .trellis/tasks/wave4-r3-dcp-05-tier-a` exit 0                       |

---

## 2. 参考项目实读门禁（用户追加 · RED 前强制）

**Plan 已给出方案**（`reference-adoption-dcp05.md` + `EXTERNAL-INDEX.md` §D）。执行 agent **不得**仅凭 Plan 摘要写码；须 **对照 L 梯实读 `参考项目/**` 源码\*\*，再写 RED 测试。

### 2.1 全 agent 必读（§D 基线）

| 参考路径                                                  | 等级                            | 执行时对照什么                                                                               |
| --------------------------------------------------------- | ------------------------------- | -------------------------------------------------------------------------------------------- |
| `参考项目/OpenBB/.../fetcher.py` L36–85                   | architecture_only → **L3 对齐** | watermark → query 变换 → port extract → transform → staging → clean；**禁止拷贝 Fetcher 类** |
| `参考项目/EasyXT/.../unified_data_interface.py` L172–244  | **forbidden**                   | sync 路径不得 silent fallback；须负向测或代码审查确认无此模式                                |
| `参考项目/EasyXT/.../auto_data_updater.py` L31–32, L87–97 | **forbidden**                   | 禁止 sys.path / DataManager 进入 sync                                                        |

### 2.2 按 agent 追加实读

| Agent | 切片         | 追加参考实读                                                           | Plan 决策                                                                                             |
| ----- | ------------ | ---------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| **A** | S01, S08     | `auto_data_updater.py` L114–178（L2 概念：交易日/日期窗）              | bar 增量窗 = watermark → `start_date`/`end_date`；仓内模板 `ops/fred_incremental_*` + DCP-01 baostock |
| **B** | S02–S06      | `digital-oracle/.../bis.py` L46–66（**L2**）                           | `startPeriod`/`start_year` 来自 macro watermark；仓内复制 `fred_incremental_run.py`                   |
| **C** | S07, S09–S11 | OpenBB fetcher L3（同上）+ 仓内 `sec_edgar`/`crypto_market` normalizer | metadata/disclosure/crypto clean 列形状对齐仓内 normalizer，fetch 三阶段对齐 OpenBB                   |

### 2.3 落盘证据（每 worktree 一份）

路径：`.trellis/tasks/wave4-r3-dcp-05-tier-a/research/execute-reference-read-evidence-<branch-suffix>.md`

必含字段：

```markdown
## 实读清单

- [ ] 文件路径 · 行号 · L梯 · 本切片采纳/禁止点（一句话）

## 对照 Plan 决策

- reference-adoption-dcp05.md §X → 本切片实现点

## 禁止项自检

- [ ] 无 runtime import 参考项目
- [ ] 无 EasyXT unified_data_interface 式 fallback
```

**RED 测试编写前** 须完成 §2.3；GREEN 后 merge 负责人抽查。

---

## 3. 执行中途（每切片 · 与主会话相同）

```text
实读参考 §2 → impact() → Read /test-driven-development → RED → GREEN → 代码/测试
```

- 五字段 docstring 每个 `test_*`
- ponytail · TDD · GitNexus
- **禁止改：** `clean_write_targets.py` · `incremental_source_registry.py` · `015_*.sql` · `data_commands.py`（S12 主会话）

---

## 4. 方案 B 分支

| Worktree                                 | Branch                  | 切片         | 禁止并发拥有       |
| ---------------------------------------- | ----------------------- | ------------ | ------------------ |
| `../quant-monitor-desk-wt-dcp05-s01-s08` | `feature/dcp05-s01-s08` | S01, S08     | `data_commands.py` |
| `../quant-monitor-desk-wt-dcp05-s02-s06` | `feature/dcp05-s02-s06` | S02–S06      | `data_commands.py` |
| `../quant-monitor-desk-wt-dcp05-s07-s11` | `feature/dcp05-s07-s11` | S07, S09–S11 | `data_commands.py` |

**Base：** `feature/wave4-r3-dcp-05-tier-a`（含 S00 merge）

---

## 5. Agent 收尾（不 commit · 主会话 merge）

```bash
uv run pytest tests/test_<本切片>_*.py -q
uv run python scripts/loop_maintain.py --fix   # 仅当新增测试模块
```

回报：修改文件列表 · 参考实读证据路径 · pytest 输出 · 未解 blocker
