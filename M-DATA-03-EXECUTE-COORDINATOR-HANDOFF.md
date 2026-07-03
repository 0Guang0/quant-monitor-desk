# M-DATA-03 Execute 协调者交接（主会话必读）

> **产出：** 2026-07-03（rev 2）· **角色：** 新会话 **主会话 = 协调调度者**（少写码，多派发、合并、门禁）  
> **任务目录：** `.trellis/tasks/m-data-03-tier-a-live/`  
> **集成分支：** `feature/m-data-03-tier-a-live`（`87cb499b` Plan R2 freeze）  
> **全局规则 SSOT（任何违反 = 完成不合格）：** `c:\Users\Guang\Desktop\全局规则.txt`

---

## 0. 用户锁定指令（最高优先级）

### 0.1 持续推进 — 禁止单批后停问

主会话 **不得** 在完成一个批次/切片后停下问用户「是否继续」「要不要下一批」。

**默认行为：** 按 §4 阶段状态机，**当前阶段过关条件满足 → 立即进入下一阶段**（派发下一批 agent 或主会话执行 ACCEPT/CI），直至：

- Execute 全步 `[x]` 且 `validate-execute-handoff` exit 0 → **立即派发 Audit**（A1–A8），或
- Audit FAIL → **立即进入 Repair 关账流程**（无遗留），或
- 命中 §0.2 **唯一允许暂停** 的情形。

**禁止话术：**「批次 1 已完成，需要我继续吗？」「是否派发 F0 agent？」—— 过关即派，无需确认。

### 0.2 唯一允许暂停（block）的情形

| 情形                                                       | 动作                                  |
| ---------------------------------------------------------- | ------------------------------------- |
| `plan-revision-r2.md` §2 AC 语义冲突 / 说不清 scope        | grill-me **真问用户**（非伪 session） |
| GitNexus `impact()` **HIGH/CRITICAL** 且无法 ponytail 收敛 | 停报用户取舍                          |
| 同一切片 **≥4 轮** 仍无法 pytest 绿（已走 DEBUG 链）       | 停报 blocker + 证据                   |
| 需修改用户锁定 AC 或突破阶段外置配额                       | grill-me                              |

**不算暂停：** 批次间 merge、`loop_maintain`、全量 pytest、写 handoff 证据 — 主会话静默做完继续。

### 0.3 本批契约（已预批）

Execute 全阶段 **本批契约 = `plan-revision-r2.md` §2 十条 + `to-issues-slices.md` 各切片 AC**。  
**无需** 每批再问用户开工；仅 §0.2 触发时 grill-me。

---

## 1. 当前状态（一句话）

Plan R2 已冻结、对抗审查 F-01…F-30 已关账；**Execute 未开始**。实现仍缺：证据 manifest、F0 四族无 SKIP、B2 主路径、dispatch 去重、mootdx matrix、R2 契约测试、CI workflow、MCR R4 诚实更新。

**上下文策略：** 子 agent **只加载当前切片相关文件**（见 §12）；主会话维护 §4 状态机，勿把整包 Plan 塞进单次派发。

---

## 2. 主会话职责边界

| 主会话做                                                                | 主会话不做（派给子 agent）                                       |
| ----------------------------------------------------------------------- | ---------------------------------------------------------------- |
| `task.py start`、维护 §4 阶段状态                                       | 各切片 RED/GREEN 实现                                            |
| **过关即派**下一批（§0.1）                                              | 单批完成后停问用户                                               |
| 派发子 agent（**`model: composer-2.5`**，**禁止 `composer-2.5-fast`**） | 子 agent 跳过 §5 全流程                                          |
| 批次 2：**单条消息并行** 派发 F0 + B2 + DISPATCH（最多 3 个 Task）      | 串行一个一个问用户                                               |
| merge 协调（§4.3）；**仅主会话** `loop_maintain` / registry             | 子 agent merge 到集成分支                                        |
| 每 merge：`pytest -q`、`detect_changes()`、更新 §4 状态                 | 子 agent 改 `contract_coverage` waiver（主会话在 EVIDENCE 后关） |
| 批次 3：ACCEPT → CI；handoff 四件套（§11）                              | `finish-work`（Audit PASS 前禁止）                               |
| handoff 绿 → **立即** Audit；Audit FAIL → Repair                        | 为绿改测试目的 / SKIP / 阶段外置滥用                             |

---

## 3. 权威路径（引用，不复述 AC 条文）

| 用途                             | 路径                                                                            |
| -------------------------------- | ------------------------------------------------------------------------------- |
| 用户 AC（锁定）                  | `.trellis/tasks/m-data-03-tier-a-live/research/plan-revision-r2.md` §2          |
| 切片 AC                          | `.trellis/tasks/m-data-03-tier-a-live/research/to-issues-slices.md`             |
| Execute 路由                     | `.trellis/tasks/m-data-03-tier-a-live/research/00-EXECUTION-ENTRY.md`           |
| 技术规格 / CI / failure artifact | `.trellis/tasks/m-data-03-tier-a-live/research/plan-spec.md`                    |
| 证据契约                         | `specs/contracts/live_tier_a_evidence_v1.yaml`                                  |
| 四族 profile 规则                | `specs/contracts/data_quality_rules.yaml`                                       |
| 并行/文件锁                      | `.trellis/tasks/m-data-03-tier-a-live/research/parallel-dispatch-protocol.md`   |
| 执行索引                         | `.trellis/tasks/m-data-03-tier-a-live/EXECUTION_INDEX.md`                       |
| 包外权威                         | `.trellis/tasks/m-data-03-tier-a-live/research/EXTERNAL-INDEX.md` §A–§E         |
| 活卡（R2 取代后只读）            | `docs/implementation_tasks/M_DATA_03_TIER_A_LIVE/M_DATA_03_TIER_A_LIVE.md` §5.1 |
| ADR                              | `docs/decisions/ADR-034-*.md` · `ADR-027` · `ADR-025` · `ADR-028`               |
| Plan 摘要                        | `M-DATA-03-HANDOFF.md`                                                          |
| Audit 模板                       | `.trellis/tasks/m-data-03-tier-a-live/AUDIT.plan.md`                            |
| 机器路由                         | `.trellis/tasks/m-data-03-tier-a-live/context_pack.json`                        |

---

## 4. 阶段状态机（协调者 SSOT）

### 4.1 阶段与过关条件

| 阶段   | 执行体                  | 过关条件（全部满足才进下一阶段）                                                                                                                                                   |
| ------ | ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **P0** | 主会话                  | `task.py start`；`task.json` → `in_progress`；`validate-plan-freeze` 仍 exit 0                                                                                                     |
| **P1** | 1× Evidence agent       | `S-R2-EVIDENCE` merge；契约测绿；11 `source_bindings`；`loop_maintain --fix` 已跑；**主会话**去掉 `live_tier_a_evidence_v1` 的 contract_coverage **waiver** 并再跑 `loop_maintain` |
| **P2** | 最多 3× agent **并行**  | `S-R2-F0` + `S-R2-B2` + `S-R2-DISPATCH` **均已 merge**；merge 顺序 **F0、B2 任意先后 → DISPATCH 最后**；每 merge 后 `pytest -q` exit 0                                             |
| **P3** | 主会话或 1× Close agent | `S-R2-ACCEPT`：11/11 live `--report`、E2、MCR；`S-R2-CI`：workflow + failure artifact；`plan-revision-r2.md` §2 全条可勾选                                                         |
| **P4** | 主会话                  | §11 handoff 四件套 + `validate-execute-handoff` exit 0                                                                                                                             |
| **P5** | 主会话派发 Audit        | A1–A8 报告 + `audit.report.md`；PASS → 方可 `finish-work`                                                                                                                          |
| **P6** | Repair（若 FAIL）       | `无遗留` 关账 + pytest 绿                                                                                                                                                          |

**P1 完成 → 立即 P2（并行派发，勿停）。P2 完成 → 立即 P3。P3 → P4 → P5 链式推进。**

### 4.2 派发批次表

| 批次 | 阶段 | 子 agent                            | 分支建议                                          |
| ---- | ---- | ----------------------------------- | ------------------------------------------------- |
| 0    | P0   | 主会话                              | `feature/m-data-03-tier-a-live`                   |
| 1    | P1   | **1** Evidence                      | `feature/m-data-03-r2-evidence`                   |
| 2    | P2   | **最多 3 并行**：F0 · B2 · DISPATCH | `feature/m-data-03-r2-f0` · `…-b2` · `…-dispatch` |
| 3    | P3   | 主会话或 1 Close                    | 集成分支                                          |

**开发并行、合并串行：**

```text
EVIDENCE → (F0 ∥ B2) → DISPATCH → ACCEPT → CI
```

- P2：F0/B2/DISPATCH **可同时开工**（三 worktree），但 **merge 必须**：先 F0、B2（顺序任意），**最后 DISPATCH**，再 ACCEPT。
- DISPATCH agent **不得**在 F0/B2 merge 前改 acceptance 集成逻辑（仅 dispatch/matrix）。

### 4.3 每 merge 主会话检查清单

1. 文件锁无冲突（`parallel-dispatch-protocol.md` §6）
2. `uv run python scripts/loop_maintain.py`（**仅主会话**）
3. `uv run pytest -q` exit 0
4. GitNexus `detect_changes()` — 爆炸面符合本切片
5. `EXECUTION_INDEX.md` 对应 R2.x Step → `[x]`
6. 更新 §4 内部状态 → **触发 §0.1 下一阶段**

### 4.4 Worktree 建议命令（P2 并行前）

```bash
git worktree add ../quant-monitor-desk-wt-mdata03-f0 feature/m-data-03-r2-f0
git worktree add ../quant-monitor-desk-wt-mdata03-b2 feature/m-data-03-r2-b2
git worktree add ../quant-monitor-desk-wt-mdata03-dispatch feature/m-data-03-r2-dispatch
```

（分支不存在则 `git branch feature/m-data-03-r2-f0 feature/m-data-03-tier-a-live` 等。）

### 4.5 子 agent Task 硬性参数

```yaml
subagent_type: trellis-implement # 无则 generalPurpose，但 prompt 必须含 §5 全文
model: composer-2.5 # 禁止 composer-2.5-fast
readonly: false
run_in_background: false # 主会话需等回报再 merge；P2 三 agent 可同消息并行 launch
```

**派发 prompt 必含：** §5 全流程 + 本切片 §6 要点 + §12 最小上下文清单 + 「完成后回报 commit hash / 文件列表 / pytest / AC 勾选」。

**禁止**在 prompt 里写「完成后等待用户确认」。

---

## 5. 子 agent 与主会话统一 Execute 全流程（禁止删减）

> 与 `.cursor/skills/trellis-execute/SKILL.md` 完全一致；**任一步跳过 = 不合格**。

### Phase 0 — Boot

| #   | 动作                                                                                                                                       |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| 0-G | Read `c:\Users\Guang\Desktop\全局规则.txt`；本批契约 = Plan R2 §2 + 当前切片 AC                                                            |
| 0a  | `agent-toolchain.md` · `trellis-execute/SKILL.md` · `reference.md` · `principles.md` · `project-global.mdc`                                |
| 0b  | `00-EXECUTION-ENTRY.md` · ENTRY §5.1 全部 `research/*.md` · `EXTERNAL-INDEX.md` §A · `implement.jsonl` 每行 · 当前切片 § · INDEX 当前 Step |
| 0c  | 改 symbol 前 `impact()`；HIGH/CRITICAL → 报主会话                                                                                          |
| 0d  | `uv run python .trellis/scripts/task.py validate-execute-boot .trellis/tasks/m-data-03-tier-a-live`                                        |
| 0e  | ENTRY §5.2 + §5.3 当前切片行                                                                                                               |

### 每切片循环

```text
impact → /test-driven-development + karpathy + testing-guidelines
→ RED（五字段 docstring）→ [DEBUG 链若触发] → GREEN
→ incremental-implementation → SLICE → pytest -q → INDEX/frozen [x]
```

### S-R2-EVIDENCE 专属

- 创建 `required_tests`（contract 与 to-issues 为准）
- `loop_maintain --fix`；manifest 落盘；11 `source_bindings`
- **文件锁：** `scripts/tier_a_live_acceptance.py`（CLI/`--report`）+ `backend/app/ops/tier_a_live_acceptance.py` 中 **manifest 写入**（ACCEPT 阶段再接全管道）

### 真网验收（ACCEPT / 子 agent 若需 smoke）

```bash
QMD_ALLOW_LIVE_FETCH=1 DATA_ROOT=.audit-sandbox/m-data-03/<run> \
  uv run python scripts/tier_a_live_acceptance.py --report <path>.json
```

`failure_class` 仅用 contract `failure_class_canonical` 映射表。

---

## 6. 各切片派发要点（粘贴进 Task）

| 切片         | AC 指针                 | 独占路径                                                             | 最小测                                               |
| ------------ | ----------------------- | -------------------------------------------------------------------- | ---------------------------------------------------- |
| **EVIDENCE** | to-issues 表 + contract | `scripts/tier_a_live_acceptance.py`、ops 内 manifest 写入            | `test_live_tier_a_evidence_contract.py`              |
| **F0**       | §2#3；禁 SKIP           | `backend/app/ops/data_health/*`                                      | `test_data_health_*` + harness 无 skip 路径          |
| **B2**       | §2#4                    | `data_quality_validator.py` + acceptance B2 线                       | `test_tier_a_live_b2_acceptance.py`                  |
| **DISPATCH** | §2#6；mootdx matrix     | `tier_a_live_incremental_dispatch.py`、`platform_source_matrix.yaml` | grep 无 bypass + dispatch 测                         |
| **ACCEPT**   | §2 全条                 | 集成 harness；**勿**与未 merge 切片抢文件锁                          | `test_tier_a_live_acceptance_report.py` + 11/11 live |
| **CI**       | §2#7；failure artifact  | `.github/workflows/*tier*a*`                                         | workflow 存在 + plan-spec schema                     |

**ACCEPT 必做：** 更新 `MODULE_COMPLETION_RATING.md`（C3/D1/E1/E2/F0/B2 → R4）；证据 `research/archive/non-plan/execute/r2-tier-a-live-accept-evidence.md`。

---

## 7. 已知实现差距（Execute 必须消掉）

| 项                | 现状                                                                                   |
| ----------------- | -------------------------------------------------------------------------------------- |
| SKIP              | `backend/app/ops/tier_a_live_acceptance.py` 仍有 SKIP                                  |
| B2                | 未接 acceptance 主路径                                                                 |
| mootdx            | 不在 `platform_source_matrix.yaml`                                                     |
| R2 测试           | 三文件未创建                                                                           |
| MCR               | 仍引用 R1 `l4-` 证据                                                                   |
| CI                | tier-a nightly 未建                                                                    |
| contract_coverage | `live_tier_a_evidence_v1` 仍为 **waiver**（EVIDENCE 后主会话关）                       |
| loop_manifest     | `archive/execute/loop_manifest.json` 为 **R1 AC id**（handoff 前须重生成为 R2.1–R2.6） |

---

## 8. 协调者启动清单（P0 一次性）

1. Read 本文件 + `c:\Users\Guang\Desktop\全局规则.txt`
2. `validate-plan-freeze` exit 0（应已过）
3. `task.py start .trellis/tasks/m-data-03-tier-a-live`
4. **立即** P1 派发 Evidence agent（§0.1，勿问）
5. 此后严格 §4 状态机直至 P5 Audit

---

## 9. Suggested skills

### 主会话

| Skill                                                        | 用途                                       |
| ------------------------------------------------------------ | ------------------------------------------ |
| `c:\Users\Guang\Desktop\全局规则.txt`                        | 全程 SSOT                                  |
| `c:\Users\Guang\.claude\skills\context-engineering\SKILL.md` | 派发时 §12 最小上下文；防 context flooding |
| `.cursor/skills/trellis-execute/SKILL.md`                    | Execute 相位                               |
| `agent-toolchain.md`                                         | 条件 skill 路由                            |
| `.cursor/skills/trellis-channel/SKILL.md`                    | 并行 merge                                 |
| `git-workflow-and-versioning`                                | worktree / merge                           |
| `gitnexus-impact-analysis`                                   | merge 前 `detect_changes`                  |
| `agents/audit-boot-v4.1.md`                                  | P5 派发                                    |

### 每个 Execute 子 agent

`全局规则.txt` · `trellis-execute` + `reference` + `principles` · `/test-driven-development` · `testing-guidelines` · `karpathy-guidelines` · `incremental-implementation` · `source-driven-development`（契约时）· `gitnexus-impact-analysis`

---

## 10. 红线（违反即 FAIL）

1. 未读 `全局规则.txt` 即写码
2. `composer-2.5-fast` 或未走 §5 全流程
3. **单批完成后停问用户是否继续**（§0.1）
4. 改 `plan-revision-r2.md` §2 语义
5. SKIP 过关 / partial F0 宣称 11/11 绿
6. 并行 agent 抢同一文件锁
7. merge 顺序违反 §4.2
8. Audit PASS 前 `finish-work`
9. 为绿改测试目的 / 无 ledger 关账

---

## 11. 漏洞修补 — handoff 机械门（P4 必做）

> **审查发现：** `validate-execute-handoff` / `check_task_evidence` 读 **任务根** `loop_manifest.json`、`evidence_index.json`；`context_pack.required_evidence` 指向 `archive/execute/`。**两处须一致。**

**P4 主会话关账前：**

1. 按 R2 切片重写 `loop_manifest.json`（`acs` id = `R2.1`…`R2.6` 或 INDEX Step id，与 `EXECUTION_INDEX.md` 一致；**勿**沿用 archive 内 R1 `AC-CLI` 等）
2. 生成 `evidence_index.json` 指向真实证据路径（含 `r2-tier-a-live-accept-evidence.md`、report JSON、pytest 摘要）
3. **同步：** 写入任务根 **且** 归档副本 `archive/execute/`（与 `context_pack.json` 一致）
4. `uv run python scripts/check_task_evidence.py`（或 `loop_maintain`）+ `validate-execute-handoff` exit 0
5. **过关 → 立即 P5 Audit**（§0.1）

---

## 12. 子 agent 最小上下文包（context-engineering · 防漂移）

派发时 **只附本表 + §6 行**，勿贴整份 Plan。

| 切片     | 必读文件（除 §5 Boot 公共项外）                                                                                                     |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| EVIDENCE | `live_tier_a_evidence_v1.yaml` · `plan-spec.md` manifest 节 · `scripts/` + `backend/app/ops/tier_a_live_acceptance.py`（Read 后改） |
| F0       | `data_health_cli.md` §5.1.1 · `data_quality_rules.yaml` · contract `source_bindings` F0 列 · `data_health/*`                        |
| B2       | `plan-spec.md` B2 节 · `data_quality_validator.py` · acceptance 现有 B2 钩子                                                        |
| DISPATCH | `gitnexus-summary.md` · `parallel-dispatch-protocol.md` · `tier_a_live_incremental_dispatch.py` · `platform_source_matrix.yaml`     |
| ACCEPT   | `plan-revision-r2.md` §2 · `plan-spec.md` pipeline/`--report` · ADR-034 · 全 harness                                                |
| CI       | `plan-spec.md` CI + `failure_artifact` · contract `failure_artifact`                                                                |

**模式示例：** 找 1 个仓库内已有 incremental e2e（如 `test_fred_macro_incremental_e2e.py`）作风格参照，写入派发 prompt。

---

## 13. 审查缺口清单（rev 2 已纳入上文）

| 缺口                                    | 处置                          |
| --------------------------------------- | ----------------------------- |
| 无持续推进规则                          | §0.1–§0.3                     |
| §8 要求每批 grill 用户                  | 改为 Plan R2 预批 + §0.2 例外 |
| handoff 根目录 vs archive 路径不一致    | §11                           |
| R1 loop_manifest 残留                   | §7、§11                       |
| contract_coverage waiver                | §4.1 P1 过关条件              |
| `scripts/` vs `backend/app/ops/` 双入口 | §5 EVIDENCE、§12              |
| P2 未要求单消息并行派发                 | §2、§4.5                      |
| Audit/Repair 后是否继续                 | §4.1 P5/P6 + §0.1             |
| EXTERNAL-INDEX §E / failure artifact    | §3、§12                       |
| 子 agent 上下文过载                     | §12                           |

---

_Plan commit：`87cb499b`。本文件若未入库，新会话仍以此为准；建议 `git add M-DATA-03-EXECUTE-COORDINATOR-HANDOFF.md` 随集成分支提交。_
